import asyncio
import os
from dotenv import load_dotenv
from golem_base_sdk import GolemBaseClient
from golem_base_sdk import GolemBaseCreate, Annotation
import uuid
import json

#TODO: annotation must not exceed 10KB
class Uploader:
    def __init__(self, file_path=None, time=None, annotation=None, priv_key = "0x0000000000000000000000000000000000000000000000000000000000000001",RPC_URL="https://ethwarsaw.holesky.golemdb.io/rpc",WS_URL="wss://ethwarsaw.holesky.golemdb.io/rpc/ws"):
        self.file_path = file_path
        self.time = time
        self.annotation = annotation
        self.priv_key = priv_key
        self.RPC_URL = RPC_URL
        self.WS_URL = WS_URL
        self.client = None

    @classmethod
    async def create(cls, file_path=None, time=None, annotation=None, priv_key = "0x0000000000000000000000000000000000000000000000000000000000000001",RPC_URL="https://ethwarsaw.holesky.golemdb.io/rpc",WS_URL="wss://ethwarsaw.holesky.golemdb.io/rpc/ws"):
        instance = cls(file_path, time, annotation, priv_key, RPC_URL, WS_URL)
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


    async def create_entity(self, chunk, chunk_id, batch_id):
        #client = await self.create_client()
        if isinstance(self.client, GolemBaseClient):
            # Create entity
            entity = GolemBaseCreate(
                data=chunk,
                btl=self.time,
                string_annotations=[
                    Annotation(key="data_dump", value=self.annotation),
                    Annotation(key="batch_id", value=batch_id),
                ],
                numeric_annotations=[
                    Annotation(key="index", value=chunk_id+1)
                ]
            )
            receipt = await self.client.create_entities([entity])
            return receipt[0].entity_key
        else:
            print("Problem with client init")
            return -1

    async def create_entity_for_keys(self, keys, batch_id, id, index):
        if isinstance(self.client, GolemBaseClient):
            entity = GolemBaseCreate(
                data=json.dumps({
                "batch_id": batch_id,
                "entity_keys": keys,
                "tag": self.annotation, #usefull for search engine
                "total_chunks": id,
                "index": index,
            }),
            btl=self.time,
            string_annotations=[
                Annotation(key="type", value="batch_metadata"),
                Annotation(key="batch_id", value=batch_id),
            ],
            numeric_annotations=[
                ]
            )
            receipt = await self.client.create_entities([entity])
            return receipt[0].entity_key
        else:
            print("Problem with client init")
            return -1

    async def upload_file(self):
        id = 0
        chunk_size = 1024 * 100 #100KB
        entity_keys = []
        batch_id = str(uuid.uuid4())
        try:
            with open(self.file_path, "rb") as file:
                while True:
                    file_data = file.read(chunk_size)
                    if not file_data:  #End of file reached
                        break
                    entity_key = await self.create_entity(file_data,id,batch_id)
                    print(entity_key)
                    entity_keys.append(entity_key.as_hex_string())
                    id += 1
                print(f"File upload complete! Total chunks processed: {id}")
            
            #Check if entity_keys array exceeds 100KB
            keys_json = json.dumps(entity_keys)
            keys_size = len(keys_json.encode('utf-8'))
            index = 1
            if keys_size <= 100 * 1024: #TEST with lower values
                batch_key = await self.create_entity_for_keys(entity_keys, batch_id, id, index)
                print("batch_key:", batch_key)
            else:
                for i in range(0, len(entity_keys), 1000): # test with 3
                    sub_batch = entity_keys[i:i + 1000] # test with 3
                    print(f"Uploading keys {i} to {i+len(sub_batch)-1}")
                    await self.create_entity_for_keys(sub_batch, batch_id, id, index)
                    index+=1
            await self.client.disconnect()  
            return entity_keys, batch_id
        except FileNotFoundError:
            print(f"File {self.file_path} not found.")
            return -1
