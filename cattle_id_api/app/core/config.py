import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # .strip() removes accidental spaces from the .env values
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://admin:A9fT3xPq@213.199.51.193:27017/moomap?authSource=admin").strip()
    DB_NAME: str = os.getenv("DB_NAME", "moomap").strip()
    
    # Defaults set to match your architecture
    CATTLE_COLLECTION: str = os.getenv("CATTLE_COLLECTION", "devices").strip()
    POLYGON_COLLECTION: str = os.getenv("POLYGON_COLLECTION", "geofence").strip()
    
settings = Settings()