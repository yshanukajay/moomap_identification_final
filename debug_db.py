import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

# 1. Load your settings
load_dotenv()
uri = os.getenv("MONGO_URI")
db_name = os.getenv("DB_NAME")
coll_name = os.getenv("CATTLE_COLLECTION")

async def test_connection():
    print(f"--- 🕵️ DEBUGGING DATABASE ---")
    print(f"1. URI: {uri[:20]}...") 
    print(f"2. Database: '{db_name}'")
    print(f"3. Target Collection: '{coll_name}'") # Check if this matches your Compass name!

    client = AsyncIOMotorClient(uri)
    db = client[db_name]
    collection = db[coll_name]

    # 4. Check if collection is empty
    count = await collection.count_documents({})
    print(f"4. Total Documents in '{coll_name}': {count}")

    if count == 0:
        print("❌ ERROR: Collection is EMPTY. Check the name in .env file!")
        return

    # 5. List all IDs to see what is actually there
    print("\n5. Listing first 5 IDs found in DB:")
    cursor = collection.find({}, {"_id": 1}).limit(5)
    async for doc in cursor:
        print(f"   -> Found ID: '{doc['_id']}' (Type: {type(doc['_id'])})")

    # 6. Try to find your specific ID
    target_id = "7454927D7850"
    print(f"\n6. Searching for specific ID: '{target_id}'...")
    found = await collection.find_one({"_id": target_id})
    
    if found:
        print("✅ SUCCESS! Document found.")
        print(found)
    else:
        print("❌ FAILURE: ID not found. Check for spaces or typos.")

    client.close()

if __name__ == "__main__":
    asyncio.run(test_connection())