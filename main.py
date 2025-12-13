from fastapi import FastAPI
from contextlib import asynccontextmanager
from cattle_id_api.app.api import endpoints
from cattle_id_api.app.services.db_manager import db_instance
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows ALL apps to connect (Easiest for development)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],
)

# Add this block immediately after creating 'app'
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows ALL apps to connect (Easiest for development)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],
)

app = FastAPI(
    title="Cattle Identification & Geo-Analysis API",
    version="1.0.0",
)

app.include_router(endpoints.router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Cattle ID API"}




# Lifespan events handles startup and shutdown logic
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to DB
    await db_instance.connect_to_database()
    yield
    # Shutdown: Close DB connection
    await db_instance.close_database_connection()

app = FastAPI(
    title="Cattle Identification & Geo-Analysis API",   
    version="1.0.0",
    lifespan=lifespan 
)

app.include_router(endpoints.router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Cattle ID API"}