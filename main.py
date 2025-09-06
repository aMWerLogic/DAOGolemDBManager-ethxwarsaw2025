import asyncio
import os
from dotenv import load_dotenv
from golem_base_sdk import GolemBaseClient
from golem_base_sdk import GolemBaseCreate, Annotation
from uploader import Uploader
import sys

if len(sys.argv) != 2:
    print("wrong arguments")
    exit(1)

# Load environment variables
load_dotenv()
# Configuration
PRIVATE_KEY = os.getenv(
    "PRIVATE_KEY", "0x0000000000000000000000000000000000000000000000000000000000000001"
)
RPC_URL = os.getenv("RPC_URL", "https://ethwarsaw.holesky.golemdb.io/rpc")
WS_URL = os.getenv("WS_URL", "wss://ethwarsaw.holesky.golemdb.io/rpc/ws")



async def main():
    uploader = await Uploader.create(sys.argv[1],100,"TEST2",PRIVATE_KEY)
    keys = await uploader.upload_file()
    return keys

if __name__ == "__main__":
    keys  = asyncio.run(main())
    
    
    for key in keys:
        print("ENTITY KEY:", key)
    #asyncio.run(create_first_entity())