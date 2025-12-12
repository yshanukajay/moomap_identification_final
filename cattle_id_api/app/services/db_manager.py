from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
import logging

class DBManager:
    def __init__(self):
        self.client = None
        self.db = None

    async def connect_to_database(self):
        self.client = AsyncIOMotorClient(settings.MONGO_URI)
        self.db = self.client[settings.DB_NAME]
        print(f"✅ Connected to DB: {settings.DB_NAME}")

    async def close_database_connection(self):
        if self.client: self.client.close()

    async def get_cattle_position(self, cattle_id: str):
        if self.db is None: return None
        
        # 1. Search in the correct collection (devices)
        collection = self.db[settings.CATTLE_COLLECTION] 
        document = await collection.find_one({"_id": cattle_id})
        
        # 2. Extract Data (Handling 'meta' structure)
        if document:
            # Check inside 'meta' first (Primary Source)
            if "meta" in document and "gps" in document["meta"]:
                meta = document["meta"]
                return {
                    "latitude": float(meta["gps"].get("lat", 0)),
                    "longitude": float(meta["gps"].get("lon", 0)),
                    "cattle_id": document.get("_id"),
                    "voltage": meta.get("battery", {}).get("voltage", 0),
                    "percent": meta.get("battery", {}).get("percent", 0)
                }
            
            # Check Root level (Fallback)
            elif "gps" in document:
                return {
                    "latitude": float(document["gps"].get("lat", 0)),
                    "longitude": float(document["gps"].get("lon", 0)),
                    "cattle_id": document.get("_id"),
                    "voltage": document.get("battery", {}).get("voltage", 0),
                    "percent": document.get("battery", {}).get("percent", 0)
                }

        return None

    async def get_relevant_polygon(self, user_id: str, cattle_id: str):
        # 1. Search in the correct collection (geofences)
        collection = self.db[settings.POLYGON_COLLECTION]
        user_doc = await collection.find_one({"userId": user_id})

        if not user_doc or "geofences" not in user_doc: return None

        for fence in user_doc["geofences"]:
            if fence.get("enabled") and cattle_id in fence.get("cattleIds", []):
                raw_polygon = fence.get("polygon", [])
                
                # 3. ROBUST FIX: Convert all points to Floats (handles "quotes")
                clean_polygon = []
                for p in raw_polygon:
                    try:
                        lat = float(p["lat"])
                        lon = float(p["lon"])
                        clean_polygon.append([lat, lon])
                    except (ValueError, TypeError):
                        continue # Skip bad points
                
                return clean_polygon
        return None

db_instance = DBManager()