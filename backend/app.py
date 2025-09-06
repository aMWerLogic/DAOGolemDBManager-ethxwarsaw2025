"""
FastAPI application for GolemDB interface.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

# Import handling for running as script
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.routes import router
from core.config import get_config
from core.logging_config import setup_logging

# Setup configuration and logging
config = get_config()
setup_logging(config.log_level, config.debug)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="DAO GolemDB Interface",
    description="A decentralized interface for DAO organizations to interact with GolemDB",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware - allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "DAO GolemDB Interface API",
        "version": "0.1.0",
        "docs": "/docs",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "dao-golemdb-interface"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    
    # Run the application
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Always reload for development
        log_level=config.log_level.lower()
    )