"""
Configuration management for the DAO GolemDB system.
"""
import os
from typing import Optional
from dataclasses import dataclass
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class GolemDBConfig:
    """Configuration for GolemDB connection."""
    private_key: str
    rpc_url: str
    ws_url: str
    chain_id: Optional[int] = None
    
    # Default test configuration for ETHWarsaw
    DEFAULT_PRIVATE_KEY = "0x4c0883a69102937d6231471b5dbb6204fe5129617082792ae468d01a3f362318"
    DEFAULT_RPC_URL = "https://ethwarsaw.holesky.golemdb.io/rpc"
    DEFAULT_WS_URL = "wss://ethwarsaw.holesky.golemdb.io/rpc/ws"
    DEFAULT_CHAIN_ID = 60138453033


@dataclass
class AppConfig:
    """Main application configuration."""
    golemdb: GolemDBConfig
    debug: bool = False
    log_level: str = "INFO"
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    chunk_size: int = 100 * 1024  # 100KB
    
    @classmethod
    def from_env(cls) -> 'AppConfig':
        """Create configuration from environment variables."""
        
        # GolemDB configuration
        private_key = os.getenv('PRIVATE_KEY', GolemDBConfig.DEFAULT_PRIVATE_KEY)
        rpc_url = os.getenv('RPC_URL', GolemDBConfig.DEFAULT_RPC_URL)
        ws_url = os.getenv('WS_URL', GolemDBConfig.DEFAULT_WS_URL)
        chain_id = int(os.getenv('CHAIN_ID', GolemDBConfig.DEFAULT_CHAIN_ID))
        
        golemdb_config = GolemDBConfig(
            private_key=private_key,
            rpc_url=rpc_url,
            ws_url=ws_url,
            chain_id=chain_id
        )
        
        # Application configuration
        debug = os.getenv('DEBUG', 'false').lower() == 'true'
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        max_file_size = int(os.getenv('MAX_FILE_SIZE', 100 * 1024 * 1024))
        chunk_size = int(os.getenv('CHUNK_SIZE', 100 * 1024))
        
        config = cls(
            golemdb=golemdb_config,
            debug=debug,
            log_level=log_level,
            max_file_size=max_file_size,
            chunk_size=chunk_size
        )
        
        # Log configuration warnings
        if private_key == GolemDBConfig.DEFAULT_PRIVATE_KEY:
            logger.warning("Using default test private key. Set PRIVATE_KEY environment variable for production.")
        
        if rpc_url == GolemDBConfig.DEFAULT_RPC_URL:
            logger.info("Using default ETHWarsaw RPC URL.")
            
        return config
    
    def validate(self) -> bool:
        """Validate configuration."""
        if not self.golemdb.private_key:
            logger.error("Private key is required")
            return False
            
        if not self.golemdb.rpc_url:
            logger.error("RPC URL is required")
            return False
            
        if not self.golemdb.ws_url:
            logger.error("WebSocket URL is required")
            return False
            
        if self.chunk_size <= 0:
            logger.error("Chunk size must be positive")
            return False
            
        if self.max_file_size <= 0:
            logger.error("Max file size must be positive")
            return False
            
        return True


# Global configuration instance
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = AppConfig.from_env()
        if not _config.validate():
            raise ValueError("Invalid configuration")
    return _config


def reload_config() -> AppConfig:
    """Reload configuration from environment."""
    global _config
    _config = None
    return get_config()