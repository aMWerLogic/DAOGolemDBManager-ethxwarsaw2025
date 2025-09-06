"""
Data searcher service implementation.
"""
from typing import List, Optional, Dict, Any
# GolemDB SDK imports handled in methods
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.interfaces import IDataSearcher, SearchResult, BatchInfo, BatchMetadata
from core.exceptions import SearchError, ConnectionError
from services.golemdb_client import GolemDBClientService
import logging

logger = logging.getLogger(__name__)


class DataSearcherService(IDataSearcher):
    """Implementation of data search functionality."""
    
    def __init__(self, client_service: GolemDBClientService):
        self.client_service = client_service
    
    async def search_by_annotation(self, key: str, value: str = None) -> List[SearchResult]:
        """Search data by annotation key and optional value using owner entities."""
        if not self.client_service.is_connected():
            raise ConnectionError("GolemDB client not connected")
        
        try:
            # Get all entities owned by current user
            owner_address = self.client_service.get_account_address()
            entity_keys = await self.client_service.client.get_entities_of_owner(owner_address)
            
            logger.debug(f"Found {len(entity_keys)} entities for owner {owner_address}")
            
            # Filter entities by annotation
            search_results = []
            for entity_key in entity_keys:
                try:
                    metadata = await self.client_service.client.get_entity_metadata(entity_key)
                    annotations = {}
                    
                    # Extract string annotations
                    for annotation in metadata.string_annotations:
                        annotations[annotation.key] = annotation.value
                    
                    # Extract numeric annotations  
                    for annotation in metadata.numeric_annotations:
                        annotations[annotation.key] = annotation.value
                    
                    # Check if this entity matches our search criteria
                    if key in annotations:
                        if value is None or annotations[key] == value:
                            search_results.append(SearchResult(
                                entity_key=str(entity_key).replace('GenericBytes(', '').replace(')', ''),
                                annotations=annotations
                            ))
                            logger.debug(f"Match found: {entity_key} with {key}={annotations[key]}")
                
                except Exception as e:
                    logger.warning(f"Failed to get metadata for entity {entity_key}: {e}")
                    continue
            
            logger.info(f"Search completed: found {len(search_results)} entities for annotation {key}={value or 'any'}")
            
            # Log summary of found annotations for debugging
            if search_results:
                annotation_keys = set()
                for result in search_results:
                    annotation_keys.update(result.annotations.keys())
                logger.debug(f"Available annotation keys in results: {sorted(annotation_keys)}")
            
            return search_results
            
        except Exception as e:
            logger.error(f"Error searching by annotation {key}={value}: {e}")
            raise SearchError(f"Failed to search by annotation: {e}")
    
    async def search_numeric_range(self, key: str, min_val: int, max_val: int) -> List[SearchResult]:
        """Search by numeric annotation range."""
        if not self.client_service.is_connected():
            raise ConnectionError("GolemDB client not connected")
        
        try:
            # Build range query
            query = f'{key} >= {min_val} && {key} <= {max_val}'
            
            # Execute query
            results = await self.client_service.client.query_entities(query)
            
            search_results = []
            for result in results:
                annotations = {}
                
                # Extract annotations
                if hasattr(result, 'string_annotations'):
                    for annotation in result.string_annotations:
                        annotations[annotation.key] = annotation.value
                
                if hasattr(result, 'numeric_annotations'):
                    for annotation in result.numeric_annotations:
                        annotations[annotation.key] = annotation.value
                
                search_results.append(SearchResult(
                    entity_key=result.entity_key,
                    annotations=annotations
                ))
            
            logger.info(f"Found {len(search_results)} entities for {key} in range [{min_val}, {max_val}]")
            return search_results
            
        except Exception as e:
            logger.error(f"Error searching numeric range {key} [{min_val}, {max_val}]: {e}")
            raise SearchError(f"Failed to search numeric range: {e}")
    
    async def list_all_batches(self) -> List[BatchInfo]:
        """List all available batches by searching for batch metadata entities first, then fallback to chunks."""
        try:
            # First try to find batch metadata entities
            metadata_results = await self.search_by_annotation("type", "batch_metadata")
            
            batches = {}
            
            # Process batch metadata entities if found
            for result in metadata_results:
                batch_id = result.annotations.get('batch_id')
                if batch_id:
                    batches[batch_id] = BatchInfo(
                        batch_id=batch_id,
                        annotation=result.annotations.get('annotation', 'Unknown'),
                        total_chunks=result.annotations.get('total_chunks', 0),
                        created_at=result.annotations.get('created_at', 'Unknown'),
                        file_name=result.annotations.get('file_name')
                    )
            
            logger.info(f"Found {len(batches)} batches from metadata entities")
            
            # Fallback: search for chunk entities with data_dump annotation
            if not batches:
                logger.info("No batch metadata found, searching chunks directly...")
                # Try different approaches to find chunks
                search_results = []
                try:
                    search_results = await self.search_by_annotation("data_dump")
                except Exception as e:
                    logger.warning(f"Failed to search by data_dump: {e}")
                    # Try searching by batch_id instead
                    try:
                        search_results = await self.search_by_annotation("batch_id")
                    except Exception as e2:
                        logger.warning(f"Failed to search by batch_id: {e2}")
                        search_results = []
                
                # Group by batch_id and get unique batches
                for result in search_results:
                    batch_id = result.annotations.get('batch_id')
                    data_dump = result.annotations.get('data_dump')
                    file_name = result.annotations.get('file_name')
                    
                    if batch_id and batch_id not in batches:
                        batches[batch_id] = BatchInfo(
                            batch_id=batch_id,
                            annotation=data_dump or 'Unknown',
                            total_chunks=0,
                            created_at='Unknown',
                            file_name=file_name
                        )
                    
                    if batch_id:
                        batches[batch_id].total_chunks += 1
                
                logger.info(f"Found {len(batches)} batches from chunk analysis")
            
            batch_list = list(batches.values())
            logger.info(f"Total unique batches found: {len(batch_list)}")
            
            # Log batch details for debugging
            for batch in batch_list:
                logger.debug(f"Batch {batch.batch_id}: {batch.total_chunks} chunks, annotation: {batch.annotation}")
            
            return batch_list
            
        except Exception as e:
            logger.error(f"Error listing batches: {e}")
            raise SearchError(f"Failed to list batches: {e}")
    
    async def get_batch_metadata(self, batch_id: str) -> Optional[BatchMetadata]:
        """Get metadata for a specific batch, preferring batch metadata entities."""
        try:
            # First try to find batch metadata entity
            metadata_query_results = await self.search_by_annotation("batch_id", batch_id)
            
            # Look for batch metadata entity specifically
            metadata_entity = None
            for result in metadata_query_results:
                if result.annotations.get('type') == 'batch_metadata':
                    metadata_entity = result
                    break
            
            if metadata_entity:
                # Extract metadata from batch metadata entity
                logger.info(f"Found batch metadata entity for batch {batch_id}")
                
                # Get the metadata JSON from the entity
                try:
                    import json
                    metadata_data = await self.client_service.client.get_entity(metadata_entity.entity_key)
                    metadata_json = json.loads(metadata_data.decode('utf-8'))
                    
                    return BatchMetadata(
                        batch_id=batch_id,
                        entity_keys=metadata_json.get('entity_keys', []),
                        file_name=metadata_json.get('file_name', 'Unknown'),
                        total_chunks=metadata_json.get('total_chunks', 0),
                        file_size=metadata_json.get('file_size', 0),
                        content_type=metadata_json.get('content_type', 'application/octet-stream'),
                        created_at=metadata_json.get('created_at', 'Unknown'),
                        uploader_address=metadata_json.get('uploader_address', 'Unknown')
                    )
                    
                except Exception as e:
                    logger.warning(f"Failed to parse batch metadata JSON: {e}, falling back to chunk analysis")
            
            # Fallback: search for chunks in this batch
            logger.info(f"No batch metadata entity found for {batch_id}, analyzing chunks...")
            chunk_results = [r for r in metadata_query_results if r.annotations.get('type') != 'batch_metadata']
            
            if not chunk_results:
                logger.warning(f"No chunks found for batch_id: {batch_id}")
                return None
            
            # Extract metadata from chunks
            first_chunk = chunk_results[0]
            annotation = first_chunk.annotations.get('data_dump', 'Unknown')
            file_name = first_chunk.annotations.get('file_name', 'Unknown')
            content_type = first_chunk.annotations.get('content_type', 'application/octet-stream')
            
            # Collect all chunk entity keys and calculate total size
            entity_keys = []
            total_size = 0
            
            for result in chunk_results:
                entity_keys.append(result.entity_key)
                chunk_size = result.annotations.get('chunk_size', 0)
                if isinstance(chunk_size, (int, float)):
                    total_size += int(chunk_size)
            
            # Sort entity keys by index to maintain order
            def get_index(result):
                return result.annotations.get('index', 0)
            
            sorted_chunks = sorted(chunk_results, key=get_index)
            entity_keys = [chunk.entity_key for chunk in sorted_chunks]
            
            metadata = BatchMetadata(
                batch_id=batch_id,
                entity_keys=entity_keys,
                file_name=file_name,
                total_chunks=len(chunk_results),
                file_size=total_size,
                content_type=content_type,
                created_at='Unknown',  # Would need timestamp annotation
                uploader_address='Unknown'  # Would need uploader annotation
            )
            
            logger.info(f"Reconstructed metadata for batch {batch_id}: {len(entity_keys)} chunks, {total_size} bytes")
            return metadata
            
        except Exception as e:
            logger.error(f"Error getting batch metadata for {batch_id}: {e}")
            raise SearchError(f"Failed to get batch metadata: {e}")
    
    async def search_chunks_by_batch_id(self, batch_id: str) -> List[SearchResult]:
        """Search for all chunks belonging to a batch."""
        return await self.search_by_annotation("batch_id", batch_id)
    
    async def search_by_file_name(self, file_name: str) -> List[SearchResult]:
        """Search entities by file name."""
        logger.info(f"Searching for entities with file_name: {file_name}")
        return await self.search_by_annotation("file_name", file_name)
    
    async def search_by_content_type(self, content_type: str) -> List[SearchResult]:
        """Search entities by content type."""
        logger.info(f"Searching for entities with content_type: {content_type}")
        return await self.search_by_annotation("content_type", content_type)
    
    async def search_by_uploader(self, uploader_address: str) -> List[SearchResult]:
        """Search entities by uploader address."""
        logger.info(f"Searching for entities uploaded by: {uploader_address}")
        return await self.search_by_annotation("uploader", uploader_address)
    
    async def get_all_annotations(self) -> Dict[str, List[str]]:
        """Get all available annotation keys and their unique values for discovery."""
        try:
            # Search for all entities with any data_dump annotation
            all_results = await self.search_by_annotation("data_dump")
            
            annotations_map = {}
            
            for result in all_results:
                for key, value in result.annotations.items():
                    if key not in annotations_map:
                        annotations_map[key] = set()
                    annotations_map[key].add(str(value))
            
            # Convert sets to sorted lists
            for key in annotations_map:
                annotations_map[key] = sorted(list(annotations_map[key]))
            
            logger.info(f"Found {len(annotations_map)} unique annotation keys")
            return annotations_map
            
        except Exception as e:
            logger.error(f"Error getting all annotations: {e}")
            raise SearchError(f"Failed to get annotations: {e}")
    
    async def create_batch_metadata(self, batch_info: dict) -> str:
        """Create batch metadata entity and return its key."""
        # This method is implemented in DataUploader, but we can add it here for completeness
        raise NotImplementedError("Batch metadata creation should be done via DataUploader service")