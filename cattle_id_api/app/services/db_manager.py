from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class DBManager:
    def __init__(self):
        self.client = None
        self.db = None

    async def connect_to_database(self):
        try:
            self.client = AsyncIOMotorClient(settings.MONGO_URI)
            self.db = self.client[settings.DB_NAME]
            logger.info("✅ Connected to MongoDB")
        except Exception as e:
            logger.error(f"❌ Could not connect to MongoDB: {e}")
            raise e

    async def close_database_connection(self):
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")

    async def get_cattle_position(self, cattle_id: str):
        """
        Fetches the latest position for a specific cattle ID.
        Assumes the cattle_positions collection uses 'cattleId' or '_id'.
        """
        if self.db is None: raise ConnectionError("Database not initialized")
        
        # We assume there is a separate collection for current cattle locations
        collection = self.db[settings.CATTLE_COLLECTION]
        
        # Try to find by string ID (like "C1") or ObjectId
        # Adjust query based on your actual cattle location document structure
        document = await collection.find_one({
             "$or": [ {"_id": cattle_id}, {"cattleId": cattle_id} ] 
        })
        
        if document:
            return {
                "latitude": document.get("latitude"),
                "longitude": document.get("longitude"),
                "cattle_id": str(document.get("_id"))
            }
        return None

    async def get_relevant_polygon(self, user_id: str, cattle_id: str):
        """
        Finds the correct polygon for a specific User and Cattle.
        It searches the user's geofences to find which one contains this cattle_id.
        """
        if self.db is None: raise ConnectionError("Database not initialized")

        collection = self.db[settings.POLYGON_COLLECTION]

        # 1. Find the User's document
        user_doc = await collection.find_one({"userId": user_id})

        if not user_doc or "geofences" not in user_doc:
            return None

        # 2. Iterate through Geofences to find the one assigned to this Cattle ID
        found_polygon = None
        
        for fence in user_doc["geofences"]:
            # Check if this fence is enabled and contains the cattle_id
            if fence.get("enabled", False) and cattle_id in fence.get("cattleIds", []):
                found_polygon = fence.get("polygon")
                break # Stop after finding the first matching fence
        
        if found_polygon:
            # 3. Convert from [{'lat': x, 'lon': y}, ...] to [[x, y], ...]
            formatted_coords = [ [p["lat"], p["lon"]] for p in found_polygon ]
            return formatted_coords

        return None

db_instance = DBManager()