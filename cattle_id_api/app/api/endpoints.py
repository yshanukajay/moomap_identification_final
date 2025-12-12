from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from app.services.db_manager import db_instance
from app.services.geo_analyzer import analyzer
from app.ai.health_model import health_predictor
from app.ai.battery_model import battery_predictor

router = APIRouter()

class AnalysisRequest(BaseModel):
    cattle_id: str
    user_id: str
    voltage: Optional[float] = None
    percent: Optional[float] = None

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
    
    # 1. Fetch Data
    cattle_data = await db_instance.get_cattle_position(request.cattle_id)
    if not cattle_data:
        raise HTTPException(status_code=404, detail="Cattle location not found.")

    polygon_coords = await db_instance.get_relevant_polygon(request.user_id, request.cattle_id)
    if not polygon_coords:
        raise HTTPException(status_code=404, detail="Geofence not found.")

    geo_result = analyzer.analyze(cattle_data['latitude'], cattle_data['longitude'], polygon_coords)

    # 2. AI Inputs (Logic Fix: Prefer Request -> Then DB -> Then 0)
    # This allows you to TEST with '6V' even if DB has '4.63V'
    input_voltage = request.voltage if request.voltage is not None and request.voltage > 0 else cattle_data.get('voltage', 0)
    input_percent = request.percent if request.percent is not None and request.percent > 0 else cattle_data.get('percent', 0)

    # 3. Predict
    prev_cattle_data = cattle_data.copy() # Simulating previous data
    health_status = health_predictor.predict(cattle_data, prev_cattle_data)
    
    # Calculate Battery
    battery_msg = battery_predictor.predict(input_voltage, input_percent)

    # 4. Alert Logic
    alert_payload = None
    if not geo_result["is_safe"]:
        alert_payload = AlertData(triggered=True, title="⚠️ Geo-Fence Breach!", message=f"Cattle {request.cattle_id} is outside.", severity="high")
    elif health_status == "distress":
        alert_payload = AlertData(triggered=True, title="⚠️ Health Anomaly!", message="Unusual movement.", severity="medium")
    else:
        alert_payload = AlertData(triggered=False, title="Safe", message="Normal", severity="low")

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