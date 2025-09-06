"""
Main application entry point based on original main.py logic.
"""
import asyncio
import sys
import os
import uuid
from dotenv import load_dotenv
from golem_base_sdk import GolemBaseClient, GolemBaseCreate, Annotation
import logging

# Load environment variables from parent directory if needed
if os.path.exists('../.env'):
    load_dotenv('../.env')
else:
    load_dotenv()

logger = logging.getLogger(__name__)


async def create_client():
    """Create GolemDB client."""
    try:
        private_key = os.getenv('PRIVATE_KEY')
        rpc_url = os.getenv('RPC_URL')
        ws_url = os.getenv('WS_URL')
        
        # Convert hex string to bytes
        private_key_hex = private_key.replace("0x", "")
        private_key_bytes = bytes.fromhex(private_key_hex)
        
        # Create client
        client = await GolemBaseClient.create_rw_client(
            rpc_url=rpc_url,
            ws_url=ws_url,
            private_key=private_key_bytes
        )
        
        print("Connected to Golem DB via ETHWarsaw!")
        
        # Get owner address
        owner_address = client.get_account_address()
        print(f"Connected with address: {owner_address}")
        
        # Get and check client account balance
        balance = await client.http_client().eth.get_balance(owner_address)
        print(f"Client account balance: {balance / 10**18} ETH")
        
        if balance == 0:
            print("Warning: Account balance is 0 ETH. Please acquire test tokens from the faucet.")
        
        return client
        
    except Exception as e:
        print(f"Error during client creation/connection: {e}")
        return None


async def create_entity(client, chunk, chunk_id, batch_id, annotation="TEST2", ttl=100):
    """Create entity for a chunk."""
    try:
        entity = GolemBaseCreate(
            data=chunk,
            ttl=ttl,
            string_annotations=[
                Annotation(key="data_dump", value=annotation),
                Annotation(key="batch_id", value=batch_id),
            ],
            numeric_annotations=[
                Annotation(key="index", value=chunk_id + 1)
            ]
        )
        
        receipt = await client.create_entities([entity])
        return receipt[0].entity_key
        
    except Exception as e:
        print(f"Error creating entity: {e}")
        return None


async def upload_file(client, file_path, annotation="TEST2", ttl=100):
    """Upload file to GolemDB."""
    try:
        chunk_id = 0
        chunk_size = 1024 * 100  # 100KB chunks
        entity_keys = []
        batch_id = str(uuid.uuid4())
        
        with open(file_path, "rb") as file:
            while True:
                file_data = file.read(chunk_size)
                if not file_data:  # End of file reached
                    break
                
                entity_key = await create_entity(client, file_data, chunk_id, batch_id, annotation, ttl)
                if entity_key:
                    entity_keys.append(entity_key)
                    chunk_id += 1
                else:
                    print(f"Failed to upload chunk {chunk_id}")
                    break
        
        await client.disconnect()
        print(f"File upload complete! Total chunks processed: {chunk_id}")
        
        return {
            'batch_id': batch_id,
            'entity_keys': entity_keys,
            'total_chunks': chunk_id
        }
        
    except FileNotFoundError:
        print(f"File {file_path} not found.")
        return None
    except Exception as e:
        print(f"Upload error: {e}")
        return None


async def main():
    """Main function based on original main.py logic."""
    
    # Check command line arguments
    if len(sys.argv) != 2:
        print("wrong arguments")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"File {file_path} not found")
        sys.exit(1)
    
    # Create client and upload
    client = await create_client()
    if not client:
        print("Failed to connect to GolemDB")
        sys.exit(1)
    
    result = await upload_file(client, file_path, "TEST2", 100)
    
    if result:
        return result['entity_keys']
    else:
        print("Upload failed")
        sys.exit(1)


if __name__ == "__main__":
    keys = asyncio.run(main())
    
    for key in keys:
        print("ENTITY KEY:", key)