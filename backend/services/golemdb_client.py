"""
GolemDB client service implementation.
"""
import asyncio
from typing import Optional
from golem_base_sdk import GolemBaseClient
import sys
import os
import time
import random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.interfaces import IGolemDBClient
from core.config import get_config
from core.exceptions import ConnectionError, InsufficientBalanceError
import logging

logger = logging.getLogger(__name__)


class GolemDBClientService(IGolemDBClient):
    """Implementation of GolemDB client management."""
    
    def __init__(self):
        self.client: Optional[GolemBaseClient] = None
        self.config = get_config()
    
    async def create_client(self, private_key: str = None, max_retries: int = 3) -> GolemBaseClient:
        """Create and return a GolemDB client with retry logic."""
        priv_key = private_key or self.config.golemdb.private_key
        
        for attempt in range(max_retries + 1):
            try:
                # Convert hex string to bytes
                private_key_hex = priv_key.replace("0x", "")
                private_key_bytes = bytes.fromhex(private_key_hex)
                
                # Create client
                self.client = await GolemBaseClient.create_rw_client(
                    rpc_url=self.config.golemdb.rpc_url,
                    ws_url=self.config.golemdb.ws_url,
                    private_key=private_key_bytes
                )
                
                logger.info("Connected to Golem DB via ETHWarsaw!")
                
                # Get owner address
                owner_address = self.client.get_account_address()
                logger.info(f"Connected with address: {owner_address}")
                
                # Get and check client account balance
                balance = await self.client.http_client().eth.get_balance(owner_address)
                balance_eth = balance / 10**18
                logger.info(f"Client account balance: {balance_eth} ETH")
                
                if balance == 0:
                    logger.warning("Account balance is 0 ETH. Please acquire test tokens from the faucet.")
                    raise InsufficientBalanceError("Account balance is 0 ETH")
                
                return self.client
                
            except InsufficientBalanceError:
                # Don't retry for insufficient balance
                raise
            except Exception as e:
                if attempt == max_retries:
                    logger.error(f"Failed to create GolemDB client after {max_retries + 1} attempts: {e}")
                    raise ConnectionError(f"Failed to create GolemDB client: {e}")
                
                # Calculate exponential backoff with jitter
                delay = (2 ** attempt) + random.uniform(0, 1)
                logger.warning(f"Connection attempt {attempt + 1} failed: {e}. Retrying in {delay:.2f} seconds...")
                await asyncio.sleep(delay)
    
    async def get_balance(self, address: str, max_retries: int = 2) -> int:
        """Get account balance with retry logic."""
        if not self.client:
            raise ConnectionError("Client not initialized")
        
        for attempt in range(max_retries + 1):
            try:
                balance = await self.client.http_client().eth.get_balance(address)
                return balance
            except Exception as e:
                if attempt == max_retries:
                    logger.error(f"Failed to get balance for {address} after {max_retries + 1} attempts: {e}")
                    raise ConnectionError(f"Failed to get balance: {e}")
                
                # Shorter delay for balance checks
                delay = (1.5 ** attempt) + random.uniform(0, 0.5)
                logger.warning(f"Balance check attempt {attempt + 1} failed: {e}. Retrying in {delay:.2f} seconds...")
                await asyncio.sleep(delay)
    
    def get_account_address(self) -> str:
        """Get account address."""
        if not self.client:
            raise ConnectionError("Client not initialized")
        
        return self.client.get_account_address()
    
    async def disconnect(self):
        """Disconnect the client."""
        if self.client:
            await self.client.disconnect()
            self.client = None
            logger.info("Disconnected from GolemDB")
    
    def is_connected(self) -> bool:
        """Check if client is connected."""
        return self.client is not None