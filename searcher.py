from dotenv import load_dotenv
from golem_base_sdk import GolemBaseClient, GenericBytes
import json
from typing import List, Dict, Optional

class Searcher:
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
            private_key_hex = self.priv_key.replace("0x", "")
            private_key_bytes = bytes.fromhex(private_key_hex)
            client = await GolemBaseClient.create_rw_client(
                rpc_url=self.RPC_URL, ws_url=self.WS_URL, private_key=private_key_bytes
            )
            print("Connected to Golem DB for search!")
            return client
        except Exception as e:
            print(f"Error during client creation: {e}")
            return None

    async def search_by_batch_id(self, batch_id: str) -> Optional[Dict]:
        try:
            entities = await self.client.query_entities(f'type="batch_metadata" && batch_id="{batch_id}"')
            if entities:
                result = entities[0]
                decoded = result.storage_value.decode("utf-8")
                data = json.loads(decoded)
                return {
                    "batch_id": data["batch_id"],
                    "tag": data["tag"],
                    "total_chunks": data["total_chunks"],
                    "entity_keys": data["entity_keys"],
                    "found_by": "batch_id"
                }
            return None
        except Exception as e:
            print(f"Error searching by batch_id: {e}")
            return None

    async def search_by_tag(self, tag: str) -> List[Dict]:
        try:
            entities = await self.client.query_entities(f'type="batch_metadata" && tag="{tag}"')
            results = []
            for entity in entities:
                decoded = entity.storage_value.decode("utf-8")
                data = json.loads(decoded)
                results.append({
                    "batch_id": data["batch_id"],
                    "tag": data["tag"],
                    "total_chunks": data["total_chunks"],
                    "entity_keys": data["entity_keys"],
                    "found_by": "tag"
                })
            return results
        except Exception as e:
            print(f"Error searching by tag: {e}")
            return []

    async def search_by_entity_key(self, entity_key: str) -> Optional[Dict]:
        try:
            entity = await self.client.get_storage_value(GenericBytes.from_hex_string(entity_key))
            if entity:
                result = entity[0]
                decoded = result.storage_value.decode("utf-8")
                data = json.loads(decoded)
                return {
                    "batch_id": data["batch_id"],
                    "tag": data["tag"],
                    "total_chunks": data["total_chunks"],
                    "entity_keys": data["entity_keys"],
                    "found_by": "batch_id"
                }
            return None
        except Exception as e:
            print(f"Error searching by entity_key: {e}")
            return None

    async def search_all_batches(self) -> List[Dict]:
        try:
            entities = await self.client.query_entities('type="batch_metadata"')
            results = []
            for entity in entities:
                decoded = entity.storage_value.decode("utf-8")
                data = json.loads(decoded)
                results.append({
                    "batch_id": data["batch_id"],
                    "tag": data["tag"],
                    "total_chunks": data["total_chunks"],
                    "entity_keys": data["entity_keys"],
                    "found_by": "all"
                })
            return results
        except Exception as e:
            print(f"Error getting all batches: {e}")
            return []

    async def smart_search(self, query: str) -> Dict:
        results = {
            "query": query,
            "results": [],
            "search_methods_used": []
        }
        if len(query) == 36 and query.count('-') == 4:  # UUID format
            result = await self.search_by_batch_id(query)
            if result:
                results["results"].append(result)
                results["search_methods_used"].append("batch_id")
        if query.startswith('0x') and len(query) == 66:
            result = await self.search_by_entity_key(query)
            if result:
                results["results"].append(result)
                results["search_methods_used"].append("entity_key")
        tag_results = await self.search_by_tag(query)
        if tag_results:
            results["results"].extend(tag_results)
            results["search_methods_used"].append("tag")

        return results

    async def disconnect(self):
        if self.client:
            await self.client.disconnect()
