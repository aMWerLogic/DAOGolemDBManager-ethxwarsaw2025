import asyncio
import os
from dotenv import load_dotenv
from golem_base_sdk import GolemBaseClient
from golem_base_sdk import GolemBaseSearch, SearchFilter
from typing import List, Optional, Dict, Any
import uuid

class Receiver:
    def __init__(self, priv_key="0x0000000000000000000000000000000000000000000000000000000000000001", 
                 RPC_URL="https://ethwarsaw.holesky.golemdb.io/rpc", 
                 WS_URL="wss://ethwarsaw.holesky.golemdb.io/rpc/ws"):
        self.priv_key = priv_key
        self.RPC_URL = RPC_URL
        self.WS_URL = WS_URL
        self.client = None

    @classmethod
    async def create(cls, priv_key="0x0000000000000000000000000000000000000000000000000000000000000001",
                     RPC_URL="https://ethwarsaw.holesky.golemdb.io/rpc",
                     WS_URL="wss://ethwarsaw.holesky.golemdb.io/rpc/ws"):
        instance = cls(priv_key, RPC_URL, WS_URL)
        instance.client = await instance.create_client()
        return instance

    async def create_client(self):
        try:
            # Convert hex string to bytes
            private_key_hex = self.priv_key.replace("0x", "")
            private_key_bytes = bytes.fromhex(private_key_hex)
            # Create client
            client = await GolemBaseClient.create_rw_client(
                rpc_url=self.RPC_URL, ws_url=self.WS_URL, private_key=private_key_bytes
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
        # in case of an exception/error just return None
        except Exception as e:
            print(f"Error during client creation/connection (returning None): {e}")
            return None

    async def search_by_batch_id(self, batch_id: str) -> List[Dict[str, Any]]:
        """Search for all chunks belonging to a specific batch ID."""
        if not isinstance(self.client, GolemBaseClient):
            print("Problem with client init")
            return []

        try:
            # Create search filter for batch_id
            search = GolemBaseSearch(
                filters=[
                    SearchFilter(key="batch_id", value=batch_id)
                ]
            )
            
            # Execute search
            results = await self.client.search_entities(search)
            
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
            
            print(f"Found {len(chunks)} chunks for batch_id: {batch_id}")
            return chunks
            
        except Exception as e:
            print(f"Error searching for batch_id {batch_id}: {e}")
            return []

    async def get_entity_data(self, entity_key: str) -> Optional[bytes]:
        """Retrieve data for a specific entity key."""
        if not isinstance(self.client, GolemBaseClient):
            print("Problem with client init")
            return None

        try:
            # Get entity data
            entity = await self.client.get_entity(entity_key)
            if entity and hasattr(entity, 'data'):
                return entity.data
            else:
                print(f"No data found for entity key: {entity_key}")
                return None
                
        except Exception as e:
            print(f"Error retrieving entity {entity_key}: {e}")
            return None

    async def download_by_batch_id(self, batch_id: str, output_path: str = None) -> Optional[bytes]:
        """Download and reconstruct file by batch ID."""
        try:
            # Search for all chunks in the batch
            chunks = await self.search_by_batch_id(batch_id)
            
            if not chunks:
                print(f"No chunks found for batch_id: {batch_id}")
                return None
            
            print(f"Reconstructing file from {len(chunks)} chunks...")
            
            # Retrieve and combine all chunk data
            file_data = b""
            for i, chunk in enumerate(chunks):
                entity_key = chunk['entity_key']
                chunk_data = await self.get_entity_data(entity_key)
                
                if chunk_data is None:
                    print(f"Failed to retrieve chunk {i+1}/{len(chunks)} (entity: {entity_key})")
                    return None
                
                file_data += chunk_data
                print(f"Retrieved chunk {i+1}/{len(chunks)} ({len(chunk_data)} bytes)")
            
            print(f"File reconstruction complete! Total size: {len(file_data)} bytes")
            
            # Save to file if output path provided
            if output_path:
                with open(output_path, "wb") as f:
                    f.write(file_data)
                print(f"File saved to: {output_path}")
            
            return file_data
            
        except Exception as e:
            print(f"Error downloading batch {batch_id}: {e}")
            return None
        finally:
            if self.client:
                await self.client.disconnect()

    async def search_by_annotation(self, key: str, value: str = None) -> List[Dict[str, Any]]:
        """Search entities by annotation key and optional value."""
        if not isinstance(self.client, GolemBaseClient):
            print("Problem with client init")
            return []

        try:
            # Create search filter
            search_filter = SearchFilter(key=key)
            if value:
                search_filter.value = value
            
            search = GolemBaseSearch(filters=[search_filter])
            
            # Execute search
            results = await self.client.search_entities(search)
            
            # Convert results to list of dictionaries
            entities = []
            for result in results:
                entity_info = {
                    'entity_key': result.entity_key,
                    'annotations': {},
                    'numeric_annotations': {}
                }
                
                # Extract annotations
                if hasattr(result, 'string_annotations'):
                    for annotation in result.string_annotations:
                        entity_info['annotations'][annotation.key] = annotation.value
                
                if hasattr(result, 'numeric_annotations'):
                    for annotation in result.numeric_annotations:
                        entity_info['numeric_annotations'][annotation.key] = annotation.value
                
                entities.append(entity_info)
            
            print(f"Found {len(entities)} entities for annotation {key}={value}")
            return entities
            
        except Exception as e:
            print(f"Error searching by annotation {key}={value}: {e}")
            return []

    async def list_all_batches(self) -> List[Dict[str, Any]]:
        """List all available batches by searching for data_dump annotation."""
        try:
            # Search for all entities with data_dump annotation
            entities = await self.search_by_annotation("data_dump")
            
            # Group by batch_id and get unique batches
            batches = {}
            for entity in entities:
                batch_id = entity['annotations'].get('batch_id')
                data_dump = entity['annotations'].get('data_dump')
                
                if batch_id and batch_id not in batches:
                    batches[batch_id] = {
                        'batch_id': batch_id,
                        'annotation': data_dump,
                        'chunk_count': 0
                    }
                
                if batch_id:
                    batches[batch_id]['chunk_count'] += 1
            
            batch_list = list(batches.values())
            print(f"Found {len(batch_list)} unique batches")
            return batch_list
            
        except Exception as e:
            print(f"Error listing batches: {e}")
            return []

    async def get_batch_info(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific batch."""
        try:
            chunks = await self.search_by_batch_id(batch_id)
            
            if not chunks:
                return None
            
            # Calculate total size and get metadata
            total_size = 0
            annotation = chunks[0]['annotations'].get('data_dump', 'Unknown')
            
            for chunk in chunks:
                # We can't get the actual chunk size without downloading,
                # so we'll estimate or mark as unknown
                pass
            
            batch_info = {
                'batch_id': batch_id,
                'annotation': annotation,
                'total_chunks': len(chunks),
                'estimated_size': 'Unknown (requires download to calculate)',
                'chunks': chunks
            }
            
            return batch_info
            
        except Exception as e:
            print(f"Error getting batch info for {batch_id}: {e}")
            return None

# Example usage functions
async def main():
    """Example usage of the Receiver class."""
    
    # Create receiver instance
    receiver = await Receiver.create()
    
    if receiver.client is None:
        print("Failed to create receiver client")
        return
    
    try:
        # List all available batches
        print("\n=== Listing all batches ===")
        batches = await receiver.list_all_batches()
        for batch in batches:
            print(f"Batch ID: {batch['batch_id']}")
            print(f"Annotation: {batch['annotation']}")
            print(f"Chunks: {batch['chunk_count']}")
            print("-" * 40)
        
        # If batches exist, download the first one
        if batches:
            batch_id = batches[0]['batch_id']
            print(f"\n=== Downloading batch: {batch_id} ===")
            
            # Download and save file
            output_file = f"downloaded_{batch_id}.dat"
            file_data = await receiver.download_by_batch_id(batch_id, output_file)
            
            if file_data:
                print(f"Successfully downloaded {len(file_data)} bytes")
            else:
                print("Download failed")
        
    except Exception as e:
        print(f"Error in main: {e}")
    
    finally:
        if receiver.client:
            await receiver.client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())