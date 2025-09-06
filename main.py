import asyncio
import os
from dotenv import load_dotenv
from golem_base_sdk import GolemBaseClient
from golem_base_sdk import GolemBaseCreate, Annotation
from uploader import Uploader
import sys
from receiver import Receiver

if len(sys.argv) != 3:
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

async def upload():
    uploader = await Uploader.create(sys.argv[1],1000,"golemTEST",PRIVATE_KEY)
    keys, batch_id = await uploader.upload_file()
    return keys, batch_id

async def receive(batch_id):
    receiver = await Receiver.create(sys.argv[2],batch_id,PRIVATE_KEY)
    await receiver.query_entities()

if __name__ == "__main__":

    keys, batch_id  = asyncio.run(upload())
    for key in keys:
        print("ENTITY KEY:", key)
    asyncio.run(receive(batch_id))



    
    