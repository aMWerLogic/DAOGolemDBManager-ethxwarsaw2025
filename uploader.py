import asyncio
import os
from dotenv import load_dotenv
from golem_base_sdk import GolemBaseClient
from golem_base_sdk import GolemBaseCreate, Annotation
import uuid

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


    async def upload_file(self):
        id = 0
        chunk_size = 1024 * 100  #100KB chunks
        entity_keys = []
        batch_id = str(uuid.uuid4())
        try:
            with open(self.file_path, "rb") as file:
                while True:
                    file_data = file.read(chunk_size)
                    if not file_data:  #End of file reached
                        break
                    entity_key = await self.create_entity(file_data,id,batch_id)
                    entity_keys.append(entity_key)
                    id += 1
                await self.client.disconnect()   
                print(f"File upload complete! Total chunks processed: {id}")
                return entity_keys, id
             
        except FileNotFoundError:
            print(f"File {self.file_path} not found.")
            return -1
