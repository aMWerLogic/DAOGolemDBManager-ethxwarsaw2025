## Functionalities:
1. Upload data dump to golemdb
2. Download data dump from golemdb
3. Search for data dumps 


## Collecting file:
Keys of data dump entities are stored in a special entity containing json:

{
    "batch_id": batch_id,
    "entity_keys": keys,
    "tag": self.annotation,
    "total_chunks": id
}

From this entity keys for all chunks are retrieved for a given data dump.

## Search engine:

Client can find arbitrary data dump with searching by batch_id (uuid4), tag or key.