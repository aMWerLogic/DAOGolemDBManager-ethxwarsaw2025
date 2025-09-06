"""
FastAPI routes for the GolemDB interface.
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import List, Optional
from pydantic import BaseModel
import io
import logging

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.golemdb_service import GolemDBService, create_golemdb_service
from core.interfaces import UploadResult, SearchResult, BatchInfo, BatchMetadata

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Dependency to get GolemDB service
async def get_golemdb_service() -> GolemDBService:
    """Dependency to create GolemDB service."""
    try:
        return await create_golemdb_service()
    except Exception as e:
        logger.error(f"Failed to create GolemDB service: {e}")
        raise HTTPException(status_code=500, detail="Failed to connect to GolemDB")


# Pydantic models for API
class UploadResponse(BaseModel):
    batch_id: str
    total_chunks: int
    entity_keys: List[str]
    message: str


class BatchInfoResponse(BaseModel):
    batch_id: str
    annotation: str
    total_chunks: int
    created_at: str
    file_name: Optional[str] = None


class SearchResponse(BaseModel):
    entity_key: str
    annotations: dict


class StatusResponse(BaseModel):
    connected: bool
    address: Optional[str] = None
    balance_eth: Optional[float] = None


# API Routes
@router.get("/status", response_model=StatusResponse)
async def get_status(service: GolemDBService = Depends(get_golemdb_service)):
    """Get connection status and account info."""
    try:
        address = service.get_account_address()
        balance = await service.get_balance(address)
        balance_eth = balance / 10**18
        
        return StatusResponse(
            connected=service.is_connected(),
            address=address,
            balance_eth=balance_eth
        )
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await service.disconnect()


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    annotation: str = Form("API_UPLOAD"),
    btl: int = Form(100),
    service: GolemDBService = Depends(get_golemdb_service)
):
    """Upload a file to GolemDB."""
    try:
        # Read file data
        file_data = await file.read()
        
        logger.info(f"Uploading file: {file.filename} ({len(file_data)} bytes) with annotation: {annotation}")
        
        # Upload to GolemDB
        result = await service.upload_bytes(
            data=file_data,
            annotation=annotation,
            file_name=file.filename,
            btl=btl
        )
        
        return UploadResponse(
            batch_id=result.batch_id,
            total_chunks=result.total_chunks,
            entity_keys=result.entity_keys,
            message=f"Successfully uploaded {file.filename}"
        )
        
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
    finally:
        await service.disconnect()


@router.get("/download/{batch_id}")
async def download_file(
    batch_id: str,
    service: GolemDBService = Depends(get_golemdb_service)
):
    """Download a file by batch ID."""
    try:
        # Download file data
        file_data = await service.download_by_batch_id(batch_id)
        
        # Create streaming response
        file_stream = io.BytesIO(file_data)
        
        return StreamingResponse(
            io.BytesIO(file_data),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename=batch_{batch_id}.dat"}
        )
        
    except Exception as e:
        logger.error(f"Download failed: {e}")
        raise HTTPException(status_code=404, detail=f"Download failed: {str(e)}")
    finally:
        await service.disconnect()


@router.get("/batches", response_model=List[BatchInfoResponse])
async def list_batches(service: GolemDBService = Depends(get_golemdb_service)):
    """List all available batches."""
    try:
        batches = await service.list_all_batches()
        
        return [
            BatchInfoResponse(
                batch_id=batch.batch_id,
                annotation=batch.annotation,
                total_chunks=batch.total_chunks,
                created_at=batch.created_at,
                file_name=batch.file_name
            )
            for batch in batches
        ]
        
    except Exception as e:
        logger.error(f"Failed to list batches: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await service.disconnect()


@router.get("/batch/{batch_id}")
async def get_batch_info(
    batch_id: str,
    service: GolemDBService = Depends(get_golemdb_service)
):
    """Get detailed information about a specific batch."""
    try:
        metadata = await service.get_batch_metadata(batch_id)
        
        if not metadata:
            raise HTTPException(status_code=404, detail="Batch not found")
        
        return {
            "batch_id": metadata.batch_id,
            "entity_keys": metadata.entity_keys,
            "file_name": metadata.file_name,
            "total_chunks": metadata.total_chunks,
            "file_size": metadata.file_size,
            "content_type": metadata.content_type,
            "created_at": metadata.created_at,
            "uploader_address": metadata.uploader_address
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get batch info: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await service.disconnect()


@router.get("/search", response_model=List[SearchResponse])
async def search_by_annotation(
    key: str,
    value: Optional[str] = None,
    service: GolemDBService = Depends(get_golemdb_service)
):
    """Search entities by annotation."""
    try:
        results = await service.search_by_annotation(key, value)
        
        return [
            SearchResponse(
                entity_key=result.entity_key,
                annotations=result.annotations
            )
            for result in results
        ]
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await service.disconnect()


@router.get("/search/numeric")
async def search_numeric_range(
    key: str,
    min_val: int,
    max_val: int,
    service: GolemDBService = Depends(get_golemdb_service)
):
    """Search entities by numeric annotation range."""
    try:
        results = await service.search_numeric_range(key, min_val, max_val)
        
        return [
            SearchResponse(
                entity_key=result.entity_key,
                annotations=result.annotations
            )
            for result in results
        ]
        
    except Exception as e:
        logger.error(f"Numeric search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await service.disconnect()


@router.get("/search/filename/{file_name}")
async def search_by_filename(
    file_name: str,
    service: GolemDBService = Depends(get_golemdb_service)
):
    """Search entities by file name."""
    try:
        results = await service.searcher.search_by_file_name(file_name)
        
        return [
            SearchResponse(
                entity_key=result.entity_key,
                annotations=result.annotations
            )
            for result in results
        ]
        
    except Exception as e:
        logger.error(f"Filename search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await service.disconnect()


@router.get("/search/content-type/{content_type}")
async def search_by_content_type(
    content_type: str,
    service: GolemDBService = Depends(get_golemdb_service)
):
    """Search entities by content type."""
    try:
        results = await service.searcher.search_by_content_type(content_type)
        
        return [
            SearchResponse(
                entity_key=result.entity_key,
                annotations=result.annotations
            )
            for result in results
        ]
        
    except Exception as e:
        logger.error(f"Content type search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await service.disconnect()


@router.get("/annotations")
async def get_all_annotations(service: GolemDBService = Depends(get_golemdb_service)):
    """Get all available annotation keys and their values for discovery."""
    try:
        annotations = await service.searcher.get_all_annotations()
        return annotations
        
    except Exception as e:
        logger.error(f"Failed to get annotations: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await service.disconnect()


@router.get("/chunk/{entity_key}")
async def get_chunk(
    entity_key: str,
    service: GolemDBService = Depends(get_golemdb_service)
):
    """Get a single chunk by entity key."""
    try:
        chunk_data = await service.get_chunk_by_key(entity_key)
        
        return StreamingResponse(
            io.BytesIO(chunk_data),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename=chunk_{entity_key}.dat"}
        )
        
    except Exception as e:
        logger.error(f"Failed to get chunk: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    finally:
        await service.disconnect()