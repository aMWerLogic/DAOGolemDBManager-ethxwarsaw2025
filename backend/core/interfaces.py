"""
Core interfaces for the DAO GolemDB system.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class UploadResult:
    """Result of a file upload operation."""
    batch_id: str
    entity_keys: List[str]
    total_chunks: int


@dataclass
class SearchResult:
    """Result of a search operation."""
    entity_key: str
    annotations: Dict[str, Any]


@dataclass
class BatchInfo:
    """Information about a batch."""
    batch_id: str
    annotation: str
    total_chunks: int
    created_at: str
    file_name: Optional[str] = None


@dataclass
class BatchMetadata:
    """Detailed metadata for a batch."""
    batch_id: str
    entity_keys: List[str]
    file_name: str
    total_chunks: int
    file_size: int
    content_type: str
    created_at: str
    uploader_address: str


class IGolemDBClient(ABC):
    """Interface for GolemDB client management."""
    
    @abstractmethod
    async def create_client(self, private_key: str):
        """Create and return a GolemDB client."""
        pass
    
    @abstractmethod
    async def get_balance(self, address: str) -> int:
        """Get account balance."""
        pass
    
    @abstractmethod
    def get_account_address(self) -> str:
        """Get account address."""
        pass


class IDataUploader(ABC):
    """Interface for data uploading functionality."""
    
    @abstractmethod
    async def upload_file(self, file_path: str, annotation: str, btl: int = 100) -> UploadResult:
        """Upload a file to GolemDB."""
        pass
    
    @abstractmethod
    async def upload_bytes(self, data: bytes, annotation: str, file_name: str = None, btl: int = 100) -> UploadResult:
        """Upload bytes data to GolemDB."""
        pass
    
    @abstractmethod
    async def create_batch_metadata(self, batch_id: str, entity_keys: List[str], 
                                  file_name: str, file_size: int, content_type: str,
                                  annotation: str, btl: int = 100) -> str:
        """Create batch metadata entity and return its key."""
        pass


class IDataReceiver(ABC):
    """Interface for data retrieval functionality."""
    
    @abstractmethod
    async def download_by_batch_id(self, batch_id: str) -> bytes:
        """Download and reconstruct file by batch ID."""
        pass
    
    @abstractmethod
    async def get_chunk_by_key(self, entity_key: str) -> bytes:
        """Get a single chunk by entity key."""
        pass
    
    @abstractmethod
    async def reconstruct_file(self, entity_keys: List[str]) -> bytes:
        """Reconstruct file from multiple chunks."""
        pass


class IDataSearcher(ABC):
    """Interface for data search functionality."""
    
    @abstractmethod
    async def search_by_annotation(self, key: str, value: str = None) -> List[SearchResult]:
        """Search data by annotation key and optional value."""
        pass
    
    @abstractmethod
    async def get_batch_metadata(self, batch_id: str) -> Optional[BatchMetadata]:
        """Get metadata for a specific batch."""
        pass
    
    @abstractmethod
    async def list_all_batches(self) -> List[BatchInfo]:
        """List all available batches."""
        pass
    
    @abstractmethod
    async def search_chunks_by_batch_id(self, batch_id: str) -> List[SearchResult]:
        """Search for all chunks belonging to a batch."""
        pass
    
    @abstractmethod
    async def search_numeric_range(self, key: str, min_val: int, max_val: int) -> List[SearchResult]:
        """Search by numeric annotation range."""
        pass
    
    @abstractmethod
    async def create_batch_metadata(self, batch_info: dict) -> str:
        """Create batch metadata entity and return its key."""
        pass
    
    @abstractmethod
    async def search_by_file_name(self, file_name: str) -> List[SearchResult]:
        """Search entities by file name."""
        pass
    
    @abstractmethod
    async def search_by_content_type(self, content_type: str) -> List[SearchResult]:
        """Search entities by content type."""
        pass
    
    @abstractmethod
    async def search_by_uploader(self, uploader_address: str) -> List[SearchResult]:
        """Search entities by uploader address."""
        pass
    
    @abstractmethod
    async def get_all_annotations(self) -> Dict[str, List[str]]:
        """Get all available annotation keys and their unique values."""
        pass