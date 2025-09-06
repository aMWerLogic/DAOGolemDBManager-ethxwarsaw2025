from dotenv import load_dotenv
from golem_base_sdk import GolemBaseClient, GenericBytes
import os
class Receiver:
    def __init__(self, file_path=None, keys=[],priv_key = "0x0000000000000000000000000000000000000000000000000000000000000001",RPC_URL="https://ethwarsaw.holesky.golemdb.io/rpc",WS_URL="wss://ethwarsaw.holesky.golemdb.io/rpc/ws"):
        self.file_path = file_path
        self.keys = keys
        self.priv_key = priv_key
        self.RPC_URL = RPC_URL
        self.WS_URL = WS_URL
        self.client = None

    @classmethod
    async def create(cls, file_path=None, keys=[],priv_key = "0x0000000000000000000000000000000000000000000000000000000000000001", RPC_URL="https://ethwarsaw.holesky.golemdb.io/rpc",WS_URL="wss://ethwarsaw.holesky.golemdb.io/rpc/ws"):
        instance = cls(file_path, keys,priv_key, RPC_URL, WS_URL)
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

    async def query_entities(self):
        if os.path.exists(self.file_path):
            os.remove(self.file_path)
        for entity_key in self.keys:
            print(entity_key)
            try:
                result = await self.client.get_storage_value(GenericBytes.from_hex_string(entity_key))
            except Exception as e:
                print(f"Error during get_storage_value (returning None): {e}")
                return None
            with open(self.file_path, "ab") as file:
                file.write(result)
