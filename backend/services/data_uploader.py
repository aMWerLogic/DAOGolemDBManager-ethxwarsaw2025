"""
Data uploader service implementation based on existing uploader.py logic.
Enhanced with file type support, metadata, and batch metadata creation.
"""
import uuid
import json
import mimetypes
from datetime import datetime
from typing import List, Optional
from pathlib import Path
from golem_base_sdk import GolemBaseCreate, Annotation
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.interfaces import IDataUploader, UploadResult
from core.config import get_config
from core.exceptions import UploadError, ConnectionError
from services.golemdb_client import GolemDBClientService
import logging

logger = logging.getLogger(__name__)


class DataUploaderService(IDataUploader):
    """Implementation of data uploading functionality."""
    
    def __init__(self, client_service: GolemDBClientService):
        self.client_service = client_service
        self.config = get_config()
    
    async def create_entity(self, chunk: bytes, chunk_id: int, batch_id: str, 
                          annotation: str, file_name: str = None, content_type: str = None,
                          total_chunks: int = None, btl: int = 100) -> str:
        """Create a single entity for a chunk of data with enhanced metadata."""
        if not self.client_service.is_connected():
            raise ConnectionError("GolemDB client not connected")
        
        try:
            # Build string annotations
            string_annotations = [
                Annotation(key="data_dump", value=annotation),
                Annotation(key="batch_id", value=batch_id),
            ]
            
            # Add optional metadata
            if file_name:
                string_annotations.append(Annotation(key="file_name", value=file_name))
            if content_type:
                string_annotations.append(Annotation(key="content_type", value=content_type))
            
            # Add expiration date
            from datetime import timedelta
            expiration_date = (datetime.utcnow() + timedelta(seconds=btl)).isoformat()
            string_annotations.append(Annotation(key="expiration_date", value=expiration_date))
            
            # Build numeric annotations
            numeric_annotations = [
                Annotation(key="index", value=chunk_id + 1),
                Annotation(key="chunk_size", value=len(chunk))
            ]
            
            if total_chunks:
                numeric_annotations.append(Annotation(key="total_chunks", value=total_chunks))
            
            # Create entity with enhanced annotations
            entity = GolemBaseCreate(
                data=chunk,
                ttl=btl,  # GolemDB SDK uses 'ttl' parameter
                string_annotations=string_annotations,
                numeric_annotations=numeric_annotations
            )
            
            # Create entity and get receipt
            receipt = await self.client_service.client.create_entities([entity])
            entity_key = receipt[0].entity_key
            
            logger.debug(f"Created entity {entity_key} for chunk {chunk_id + 1} ({len(chunk)} bytes)")
            return entity_key
            
        except Exception as e:
            logger.error(f"Error creating entity for chunk {chunk_id}: {e}")
            raise UploadError(f"Failed to create entity: {e}")
    
    async def create_batch_metadata(self, batch_id: str, entity_keys: List[str], 
                                  file_name: str, file_size: int, content_type: str,
                                  annotation: str, btl: int = 100) -> str:
        """Create batch metadata entity in GolemDB."""
        if not self.client_service.is_connected():
            raise ConnectionError("GolemDB client not connected")
        
        try:
            uploader_address = self.client_service.get_account_address()
            created_at = datetime.utcnow().isoformat()
            
            # Calculate expiration date based on BTL (assuming 1 block = 1 second for simplicity)
            from datetime import timedelta
            expiration_date = (datetime.utcnow() + timedelta(seconds=btl)).isoformat()
            
            # Create metadata dictionary
            metadata = {
                "batch_id": batch_id,
                "entity_keys": entity_keys,
                "file_name": file_name,
                "total_chunks": len(entity_keys),
                "file_size": file_size,
                "content_type": content_type,
                "created_at": created_at,
                "expiration_date": expiration_date,
                "btl_blocks": btl,
                "uploader_address": uploader_address,
                "annotation": annotation
            }
            
            # Convert to JSON bytes
            metadata_json = json.dumps(metadata, indent=2)
            metadata_bytes = metadata_json.encode('utf-8')
            
            # Create metadata entity
            metadata_entity = GolemBaseCreate(
                data=metadata_bytes,
                ttl=btl,  # GolemDB SDK uses 'ttl' parameter
                string_annotations=[
                    Annotation(key="type", value="batch_metadata"),
                    Annotation(key="batch_id", value=batch_id),
                    Annotation(key="uploader", value=uploader_address),
                    Annotation(key="file_name", value=file_name),
                    Annotation(key="annotation", value=annotation)
                ],
                numeric_annotations=[
                    Annotation(key="total_chunks", value=len(entity_keys)),
                    Annotation(key="file_size", value=file_size)
                ]
            )
            
            # Create metadata entity
            receipt = await self.client_service.client.create_entities([metadata_entity])
            metadata_key = receipt[0].entity_key
            
            logger.info(f"Created batch metadata entity {metadata_key} for batch {batch_id}")
            return metadata_key
            
        except Exception as e:
            logger.error(f"Error creating batch metadata for {batch_id}: {e}")
            raise UploadError(f"Failed to create batch metadata: {e}")
    
    async def upload_file(self, file_path: str, annotation: str, btl: int = 100) -> UploadResult:
        """Upload a file to GolemDB with enhanced metadata support."""
        try:
            # Validate file exists and get metadata
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                raise FileNotFoundError(f"File {file_path} not found")
            
            file_name = file_path_obj.name
            file_size = file_path_obj.stat().st_size
            content_type, _ = mimetypes.guess_type(file_path)
            content_type = content_type or "application/octet-stream"
            
            # Validate file size
            if file_size > self.config.max_file_size:
                raise UploadError(f"File size {file_size} exceeds maximum {self.config.max_file_size}")
            
            chunk_id = 0
            chunk_size = self.config.chunk_size
            entity_keys = []
            batch_id = str(uuid.uuid4())
            
            logger.info(f"Starting upload of {file_path} ({file_size} bytes, {content_type}) with batch_id: {batch_id}")
            
            # Calculate total chunks for progress tracking
            total_chunks = (file_size + chunk_size - 1) // chunk_size
            
            with open(file_path, "rb") as file:
                while True:
                    file_data = file.read(chunk_size)
                    if not file_data:  # End of file reached
                        break
                    
                    entity_key = await self.create_entity(
                        chunk=file_data,
                        chunk_id=chunk_id,
                        batch_id=batch_id,
                        annotation=annotation,
                        file_name=file_name,
                        content_type=content_type,
                        total_chunks=total_chunks,
                        btl=btl
                    )
                    entity_keys.append(entity_key)
                    chunk_id += 1
                    
                    logger.debug(f"Uploaded chunk {chunk_id}/{total_chunks} ({len(file_data)} bytes)")
            
            logger.info(f"File upload complete! Total chunks processed: {chunk_id}")
            
            # Create batch metadata entity
            try:
                metadata_key = await self.create_batch_metadata(
                    batch_id=batch_id,
                    entity_keys=entity_keys,
                    file_name=file_name,
                    file_size=file_size,
                    content_type=content_type,
                    annotation=annotation,
                    btl=btl
                )
                logger.info(f"Created batch metadata: {metadata_key}")
            except Exception as e:
                logger.warning(f"Failed to create batch metadata (upload still successful): {e}")
            
            return UploadResult(
                batch_id=batch_id,
                entity_keys=[str(key).replace('GenericBytes(', '').replace(')', '') for key in entity_keys],  # Convert GenericBytes to clean hex string
                total_chunks=chunk_id
            )
            
        except FileNotFoundError:
            error_msg = f"File {file_path} not found"
            logger.error(error_msg)
            raise UploadError(error_msg)
        except UploadError:
            # Re-raise UploadError as-is
            raise
        except Exception as e:
            logger.error(f"Unexpected error uploading file {file_path}: {e}")
            raise UploadError(f"Failed to upload file: {e}")
    
    async def upload_bytes(self, data: bytes, annotation: str, file_name: str = None, 
                          btl: int = 100) -> UploadResult:
        """Upload bytes data to GolemDB with enhanced metadata support."""
        try:
            # Validate data size
            data_size = len(data)
            if data_size > self.config.max_file_size:
                raise UploadError(f"Data size {data_size} exceeds maximum {self.config.max_file_size}")
            
            # Determine content type from file name if provided
            content_type = "application/octet-stream"
            if file_name:
                content_type, _ = mimetypes.guess_type(file_name)
                content_type = content_type or "application/octet-stream"
            
            chunk_id = 0
            chunk_size = self.config.chunk_size
            entity_keys = []
            batch_id = str(uuid.uuid4())
            
            logger.info(f"Starting upload of {data_size} bytes ({content_type}) with batch_id: {batch_id}")
            
            # Calculate total chunks for progress tracking
            total_chunks = (data_size + chunk_size - 1) // chunk_size
            
            # Process data in chunks
            offset = 0
            while offset < data_size:
                chunk_data = data[offset:offset + chunk_size]
                
                entity_key = await self.create_entity(
                    chunk=chunk_data,
                    chunk_id=chunk_id,
                    batch_id=batch_id,
                    annotation=annotation,
                    file_name=file_name,
                    content_type=content_type,
                    total_chunks=total_chunks,
                    btl=btl
                )
                entity_keys.append(entity_key)
                chunk_id += 1
                offset += chunk_size
                
                logger.debug(f"Uploaded chunk {chunk_id}/{total_chunks} ({len(chunk_data)} bytes)")
            
            logger.info(f"Bytes upload complete! Total chunks processed: {chunk_id}")
            
            # Create batch metadata entity
            try:
                metadata_key = await self.create_batch_metadata(
                    batch_id=batch_id,
                    entity_keys=entity_keys,
                    file_name=file_name or f"data_{batch_id[:8]}",
                    file_size=data_size,
                    content_type=content_type,
                    annotation=annotation,
                    btl=btl
                )
                logger.info(f"Created batch metadata: {metadata_key}")
            except Exception as e:
                logger.warning(f"Failed to create batch metadata (upload still successful): {e}")
            
            return UploadResult(
                batch_id=batch_id,
                entity_keys=[str(key).replace('GenericBytes(', '').replace(')', '') for key in entity_keys],  # Convert GenericBytes to clean hex string
                total_chunks=chunk_id
            )
            
        except UploadError:
            # Re-raise UploadError as-is
            raise
        except Exception as e:
            logger.error(f"Unexpected error uploading bytes data: {e}")
            raise UploadError(f"Failed to upload bytes: {e}")