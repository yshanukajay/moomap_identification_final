from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from app.services.db_manager import db_instance
from app.services.geo_analyzer import analyzer

# --- UPDATED IMPORTS TO MATCH YOUR FILENAMES ---
from app.ai.health_model import health_predictor
from app.ai.battery_model import battery_predictor

router = APIRouter()

# --- Request Model ---
class AnalysisRequest(BaseModel):
    cattle_id: str = Field(..., description="The ID of the cattle (e.g., 'C5')")
    user_id: str = Field(..., description="The User ID (e.g., '95466')")
    voltage: Optional[float] = 4.0
    percent: Optional[float] = 80.0

# --- Response Models ---
class AlertData(BaseModel):
    triggered: bool
    title: str
    message: str
    severity: str

class AIAnalysis(BaseModel):
    health_status: str
    battery_forecast: str

class AnalysisResponse(BaseModel):
    status: str
    is_safe: bool
    cattle_location: Dict[str, float]
    alert: Optional[AlertData] = None
    ai_analysis: AIAnalysis
    detected_objects: List[dict]

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_cattle_position(request: AnalysisRequest):
    
    # 1. Fetch Current Data
    cattle_data = await db_instance.get_cattle_position(request.cattle_id)
    if not cattle_data:
        raise HTTPException(status_code=404, detail="Cattle location not found.")

    polygon_coords = await db_instance.get_relevant_polygon(request.user_id, request.cattle_id)
    if not polygon_coords:
        raise HTTPException(status_code=404, detail="Geofence not found.")

    # 2. Run Geo-Analysis
    geo_result = analyzer.analyze(
        cattle_data['latitude'],
        cattle_data['longitude'],
        polygon_coords
    )

    # 3. AI Analysis
    # Prepare previous location (Simulation for now)
    prev_cattle_data = cattle_data.copy()
    prev_cattle_data['latitude'] -= 0.0001 
    prev_cattle_data['longitude'] -= 0.0001

    # Call the predictors using your file names
    health_status = health_predictor.predict(cattle_data, prev_cattle_data)
    battery_msg = battery_predictor.predict(request.voltage, request.percent)

    # 4. Construct Alert
    alert_payload = None
    if not geo_result["is_safe"]:
        alert_payload = AlertData(
            triggered=True,
            title="⚠️ Geo-Fence Breach!",
            message=f"Cattle {request.cattle_id} is outside the boundary.",
            severity="high"
        )
    elif health_status == "distress":
        alert_payload = AlertData(
            triggered=True,
            title="⚠️ Health Anomaly!",
            message="Unusual movement detected (High speed/Panic).",
            severity="medium"
        )
    else:
        alert_payload = AlertData(
            triggered=False, title="Safe", message="Normal", severity="low"
        )

    return {
        "status": "success",
        "is_safe": geo_result["is_safe"],
        "cattle_location": geo_result["cattle_location"],
        "alert": alert_payload,
        "ai_analysis": {
            "health_status": health_status,
            "battery_forecast": battery_msg
        },
        "detected_objects": geo_result["detected_objects"]
    }

@router.get("/status")
async def api_status():
    return {"status": "API Online", "ai_modules": "Active"}