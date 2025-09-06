"""
Data receiver service implementation based on existing receiver.py logic.
"""
from typing import List, Optional, Dict, Any
# GolemDB SDK imports handled in methods
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.interfaces import IDataReceiver, SearchResult, BatchInfo, BatchMetadata
from core.exceptions import DownloadError, EntityNotFoundError, ConnectionError
from services.golemdb_client import GolemDBClientService
import logging

logger = logging.getLogger(__name__)


class DataReceiverService(IDataReceiver):
    """Implementation of data retrieval functionality."""
    
    def __init__(self, client_service: GolemDBClientService):
        self.client_service = client_service
    
    async def get_chunk_by_key(self, entity_key: str) -> bytes:
        """Get a single chunk by entity key."""
        if not self.client_service.is_connected():
            raise ConnectionError("GolemDB client not connected")
        
        try:
            # Convert string entity_key back to GenericBytes if needed
            if isinstance(entity_key, str):
                # Find the actual GenericBytes object from owner entities
                owner_address = self.client_service.get_account_address()
                owner_entities = await self.client_service.client.get_entities_of_owner(owner_address)
                
                # Find matching entity
                target_entity = None
                for entity in owner_entities:
                    entity_hex = str(entity).replace('GenericBytes(', '').replace(')', '')
                    if entity_hex == entity_key or entity_key in entity_hex:
                        target_entity = entity
                        break
                
                if not target_entity:
                    raise EntityNotFoundError(f"Entity {entity_key} not found in owner entities")
                
                entity_key = target_entity
            
            # Use get_storage_value instead of get_entity
            data = await self.client_service.client.get_storage_value(entity_key)
            
            if data:
                logger.debug(f"Retrieved chunk {entity_key} ({len(data)} bytes)")
                return data
            else:
                raise EntityNotFoundError(f"No data found for entity key: {entity_key}")
                
        except Exception as e:
            logger.error(f"Error retrieving entity {entity_key}: {e}")
            raise DownloadError(f"Failed to get chunk: {e}")
    
    async def search_chunks_by_batch_id(self, batch_id: str) -> List[Dict[str, Any]]:
        """Search for all chunks belonging to a batch ID."""
        if not self.client_service.is_connected():
            raise ConnectionError("GolemDB client not connected")
        
        try:
            # Query entities by batch_id annotation
            query = f'batch_id = "{batch_id}"'
            results = await self.client_service.client.query_entities(query)
            
            # Convert results to list of dictionaries with entity info
            chunks = []
            for result in results:
                chunk_info = {
                    'entity_key': result.entity_key,
                    'annotations': {},
                    'numeric_annotations': {}
                }
                
                # Extract annotations
                if hasattr(result, 'string_annotations'):
                    for annotation in result.string_annotations:
                        chunk_info['annotations'][annotation.key] = annotation.value
                
                if hasattr(result, 'numeric_annotations'):
                    for annotation in result.numeric_annotations:
                        chunk_info['numeric_annotations'][annotation.key] = annotation.value
                
                chunks.append(chunk_info)
            
            # Sort chunks by index to maintain order
            chunks.sort(key=lambda x: x['numeric_annotations'].get('index', 0))
            
            logger.info(f"Found {len(chunks)} chunks for batch_id: {batch_id}")
            return chunks
            
        except Exception as e:
            logger.error(f"Error searching for batch_id {batch_id}: {e}")
            raise DownloadError(f"Failed to search chunks: {e}")
    
    async def reconstruct_file(self, entity_keys: List[str]) -> bytes:
        """Reconstruct file from multiple chunks."""
        try:
            file_data = b""
            
            for i, entity_key in enumerate(entity_keys):
                chunk_data = await self.get_chunk_by_key(entity_key)
                file_data += chunk_data
                logger.debug(f"Retrieved chunk {i+1}/{len(entity_keys)} ({len(chunk_data)} bytes)")
            
            logger.info(f"File reconstruction complete! Total size: {len(file_data)} bytes")
            return file_data
            
        except Exception as e:
            logger.error(f"Error reconstructing file: {e}")
            raise DownloadError(f"Failed to reconstruct file: {e}")
    
    async def download_by_batch_id(self, batch_id: str) -> bytes:
        """Download and reconstruct file by batch ID."""
        try:
            # Search for all chunks in the batch
            chunks = await self.search_chunks_by_batch_id(batch_id)
            
            if not chunks:
                raise EntityNotFoundError(f"No chunks found for batch_id: {batch_id}")
            
            logger.info(f"Reconstructing file from {len(chunks)} chunks...")
            
            # Extract entity keys in order
            entity_keys = [chunk['entity_key'] for chunk in chunks]
            
            # Reconstruct file
            return await self.reconstruct_file(entity_keys)
            
        except Exception as e:
            logger.error(f"Error downloading batch {batch_id}: {e}")
            raise DownloadError(f"Failed to download batch: {e}")