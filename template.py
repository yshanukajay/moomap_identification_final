import os

PROJECT_NAME = "cattle_id_api"

# --- File Contents ---

REQUIREMENTS_CONTENT = """
fastapi
uvicorn[standard]
pydantic
motor
shapely
geopandas
osmnx
python-dotenv
"""

MAIN_PY_CONTENT = """
from fastapi import FastAPI
from app.api import endpoints

app = FastAPI(
    title="Cattle Identification & Geo-Analysis API",
    version="1.0.0",
)

app.include_router(endpoints.router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Cattle ID API"}
"""

ENDPOINTS_PY_CONTENT = """
from fastapi import APIRouter

router = APIRouter()

@router.get("/status")
async def api_status():
    return {"status": "API is running"}
"""

CONFIG_PY_CONTENT = """
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    DB_NAME: str = os.getenv("DB_NAME", "cattle_db")
    CATTLE_COLLECTION: str = "cattle_positions"
    POLYGON_COLLECTION: str = "farm_polygons"
    
settings = Settings()
"""

# --- Creation Logic ---

def create_project():
    print(f"--- Creating {PROJECT_NAME} ---")

    # 1. Create Root Directory
    if not os.path.exists(PROJECT_NAME):
        os.makedirs(PROJECT_NAME)
        print(f"Created root: {PROJECT_NAME}")

    # 2. Define and Create Subdirectories
    directories = [
        "app",
        "app/api",
        "app/core",
        "app/services",
        "data"
    ]

    for d in directories:
        dir_path = os.path.join(PROJECT_NAME, d)
        os.makedirs(dir_path, exist_ok=True)
        print(f"Created dir:  {dir_path}")

    # 3. Define and Create Files
    files = {
        ".env": "MONGO_URI=mongodb://localhost:27017/\nDB_NAME=cattle_db",
        "requirements.txt": REQUIREMENTS_CONTENT,
        "main.py": MAIN_PY_CONTENT,
        "app/__init__.py": "",
        "app/api/__init__.py": "",
        "app/api/endpoints.py": ENDPOINTS_PY_CONTENT,
        "app/core/__init__.py": "",
        "app/core/config.py": CONFIG_PY_CONTENT,
        "app/services/__init__.py": "",
        "app/services/db_manager.py": "# Database logic goes here",
        "app/services/geo_analyzer.py": "# Geospatial logic goes here",
        "data/sample_polygon.geojson": ""
    }

    for file_path, content in files.items():
        # Handle file paths correctly across OS (Windows/Linux)
        full_path = os.path.join(PROJECT_NAME, *file_path.split("/"))
        
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"Created file: {full_path}")

    print("\n--- Setup Complete! ---")
    print(f"1. cd {PROJECT_NAME}")
    print("2. pip install -r requirements.txt")
    print("3. uvicorn main:app --reload")

if __name__ == "__main__":
    create_project()