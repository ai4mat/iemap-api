import motor.motor_asyncio
from server.config import Config
from bson.objectid import ObjectId


c = Config

client = motor.motor_asyncio.AsyncIOMotorClient(c.mongo_uri)
database = client["<yourDB>"]
inventory_collection = database.get_collection("<yourCollection>")


# helpers

def item_helper(item) -> dict:
    return {
        "id": str(item["_id"]),
        "title": item["title"],
        "location": item["location"],
        "project_name": item["project_name"],
        "project_year": item["project_year"],
        "project_url": item["project_url"],
        "objtype": item["objtype"],
        "ID": str(item["ID"])
    }

def object_helper(item) -> dict:
    return {
        "id": str(item["_id"]),
        "metadata": item["metadata"],
        "objectdata": item["objectdata"],
        "storedata": item["storedata"],
    }

## Inventory collection
# Retrieve all items present in the inventory collection
async def retrieve_items():
    items = []
    async for item in inventory_collection.find():
        items.append(item_helper(item))    
    return items

# Retrieve a items with a matching string
async def retrieve_items_fts(string: str) -> dict:
    items = []
    async for item in inventory_collection.find({"$text":{"$search": string}}):
        items.append(item_helper(item))
    return items

# Retrieve a item with a matching ID
async def retrieve_item(id: str) -> dict:
    item = await inventory_collection.find_one({"_id": ObjectId(id)})
    if item:
        return item_helper(item)



