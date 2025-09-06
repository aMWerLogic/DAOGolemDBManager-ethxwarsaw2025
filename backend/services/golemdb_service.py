"""
Main GolemDB service that combines all functionality.
"""
from typing import List, Optional
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.golemdb_client import GolemDBClientService
from services.data_uploader import DataUploaderService
from services.data_receiver import DataReceiverService
from services.data_searcher import DataSearcherService
from core.interfaces import UploadResult, SearchResult, BatchInfo, BatchMetadata
from core.config import get_config
from core.logging_config import setup_logging
import logging

logger = logging.getLogger(__name__)


class GolemDBService:
    """Main service class that provides all GolemDB functionality."""
    
    def __init__(self):
        self.config = get_config()
        
        # Initialize services
        self.client_service = GolemDBClientService()
        self.uploader = DataUploaderService(self.client_service)
        self.receiver = DataReceiverService(self.client_service)
        self.searcher = DataSearcherService(self.client_service)
        
        # Setup logging
        setup_logging(self.config.log_level, self.config.debug)
    
    async def connect(self, private_key: str = None) -> bool:
        """Connect to GolemDB."""
        try:
            await self.client_service.create_client(private_key)
            logger.info("Successfully connected to GolemDB")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to GolemDB: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from GolemDB."""
        await self.client_service.disconnect()
    
    def is_connected(self) -> bool:
        """Check if connected to GolemDB."""
        return self.client_service.is_connected()
    
    def get_account_address(self) -> str:
        """Get account address."""
        return self.client_service.get_account_address()
    
    async def get_balance(self, address: str = None) -> int:
        """Get account balance."""
        if address is None:
            address = self.get_account_address()
        return await self.client_service.get_balance(address)
    
    # Upload functionality
    async def upload_file(self, file_path: str, annotation: str, btl: int = 100) -> UploadResult:
        """Upload a file to GolemDB."""
        return await self.uploader.upload_file(file_path, annotation, btl)
    
    async def upload_bytes(self, data: bytes, annotation: str, file_name: str = None, 
                          btl: int = 100) -> UploadResult:
        """Upload bytes data to GolemDB."""
        return await self.uploader.upload_bytes(data, annotation, file_name, btl)
    
    # Download functionality
    async def download_by_batch_id(self, batch_id: str) -> bytes:
        """Download and reconstruct file by batch ID."""
        return await self.receiver.download_by_batch_id(batch_id)
    
    async def get_chunk_by_key(self, entity_key: str) -> bytes:
        """Get a single chunk by entity key."""
        return await self.receiver.get_chunk_by_key(entity_key)
    
    async def reconstruct_file(self, entity_keys: List[str]) -> bytes:
        """Reconstruct file from multiple chunks."""
        return await self.receiver.reconstruct_file(entity_keys)
    
    # Search functionality
    async def search_by_annotation(self, key: str, value: str = None) -> List[SearchResult]:
        """Search data by annotation key and optional value."""
        return await self.searcher.search_by_annotation(key, value)
    
    async def search_numeric_range(self, key: str, min_val: int, max_val: int) -> List[SearchResult]:
        """Search by numeric annotation range."""
        return await self.searcher.search_numeric_range(key, min_val, max_val)
    
    async def list_all_batches(self) -> List[BatchInfo]:
        """List all available batches."""
        return await self.searcher.list_all_batches()
    
    async def get_batch_metadata(self, batch_id: str) -> Optional[BatchMetadata]:
        """Get metadata for a specific batch."""
        return await self.searcher.get_batch_metadata(batch_id)
    
    async def search_chunks_by_batch_id(self, batch_id: str) -> List[SearchResult]:
        """Search for all chunks belonging to a batch."""
        return await self.searcher.search_chunks_by_batch_id(batch_id)


# Factory function for easy service creation
async def create_golemdb_service(private_key: str = None) -> GolemDBService:
    """Create and connect GolemDB service."""
    service = GolemDBService()
    
    if await service.connect(private_key):
        return service
    else:
        raise ConnectionError("Failed to create GolemDB service")


# Convenience functions that match the original main.py pattern
async def upload_file_simple(file_path: str, annotation: str = "TEST", 
                           btl: int = 100, private_key: str = None) -> UploadResult:
    """Simple file upload function matching original main.py pattern."""
    service = await create_golemdb_service(private_key)
    
    try:
        result = await service.upload_file(file_path, annotation, btl)
        logger.info(f"Upload complete - Batch ID: {result.batch_id}")
        logger.info(f"Entity keys: {result.entity_keys}")
        return result
    finally:
        await service.disconnect()


async def download_file_simple(batch_id: str, output_path: str = None, 
                             private_key: str = None) -> bytes:
    """Simple file download function."""
    service = await create_golemdb_service(private_key)
    
    try:
        data = await service.download_by_batch_id(batch_id)
        
        if output_path:
            with open(output_path, "wb") as f:
                f.write(data)
            logger.info(f"File saved to: {output_path}")
        
        return data
    finally:
        await service.disconnect()