from dotenv import load_dotenv
from golem_base_sdk import GolemBaseClient, GenericBytes
import os
import json
class Receiver:
    def __init__(self, file_path=None,batch_id=None,priv_key = "0x0000000000000000000000000000000000000000000000000000000000000001",RPC_URL="https://ethwarsaw.holesky.golemdb.io/rpc",WS_URL="wss://ethwarsaw.holesky.golemdb.io/rpc/ws"):
        self.file_path = file_path
        self.batch_id = batch_id
        self.priv_key = priv_key
        self.RPC_URL = RPC_URL
        self.WS_URL = WS_URL
        self.client = None

    @classmethod
    async def create(cls, file_path=None,batch_id=None,priv_key = "0x0000000000000000000000000000000000000000000000000000000000000001", RPC_URL="https://ethwarsaw.holesky.golemdb.io/rpc",WS_URL="wss://ethwarsaw.holesky.golemdb.io/rpc/ws"):
        instance = cls(file_path,batch_id,priv_key, RPC_URL, WS_URL)
        instance.client = await instance.create_client()
        return instance


    async def create_client(self):
        try:
            private_key_hex = self.priv_key.replace("0x", "")
            private_key_bytes = bytes.fromhex(private_key_hex)
            client = await GolemBaseClient.create_rw_client(
                rpc_url=self.RPC_URL, ws_url=self.WS_URL, private_key=private_key_bytes
            )
            print("Connected to Golem DB via ETHWarsaw!")
            owner_address = client.get_account_address()
            print(f"Connected with address: {owner_address}")
            balance = await client.http_client().eth.get_balance(owner_address)
            print(f"Client account balance: {balance / 10**18} ETH")
            if balance == 0:
                print("Warning: Account balance is 0 ETH. Please acquire test tokens from the faucet.")
            return client
        except Exception as e:
            print(f"Error during client creation/connection (returning None): {e}")
            return None

    async def query_entities(self):
        if os.path.exists(self.file_path):
            os.remove(self.file_path)
        keys = await self.query_entity_for_keys()
        for entity_key in keys:
            print(entity_key)
            try:
                result = await self.client.get_storage_value(GenericBytes.from_hex_string(entity_key))
            except Exception as e:
                print(f"Error during get_storage_value (returning None): {e}")
                return None
            with open(self.file_path, "ab") as file:
                file.write(result)

    async def query_entity_for_keys(self):
        entities = await self.client.query_entities(f'type="batch_metadata" && batch_id="{self.batch_id}"')
        len_of_entities = len(entities)
        if len_of_entities > 1:
            print("Warning, more than 1 entity with same batch_id found!")
        keys = []
        index_dict = {}
        for result in entities:
            entity_key = result.entity_key
            decoded = result.storage_value.decode("utf-8")
            try:
                data = json.loads(decoded)
                print(f"Entity: {entity_key}, Decoded JSON data {data}")
                index_dict[data["index"]] = data["entity_keys"]
            except (json.JSONDecodeError, ValueError):
                print(f"Entity: {entity_key}, Decoded data {decoded}")
                return -1
        for idx in sorted(index_dict.keys()):
            keys.extend(index_dict[idx])
        return keys
