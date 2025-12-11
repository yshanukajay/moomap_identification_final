import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    MONGO_URI: str = os.getenv("MONGO_URI", "mmongodb://admin:A9fT3xPq@213.199.51.193:27017/moomap?authSource=admin")
    DB_NAME: str = os.getenv("DB_NAME", "moomap")
    CATTLE_COLLECTION: str = "dev_2C7A927D7850"
    POLYGON_COLLECTION: str = "dev_2C7A927D7850"
    
settings = Settings()