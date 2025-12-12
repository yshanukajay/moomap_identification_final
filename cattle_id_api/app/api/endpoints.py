from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List, Dict
import httpx 
import math # <--- Needed to fix the Error

from app.services.db_manager import db_instance
from app.services.geo_analyzer import analyzer
from app.ai.health_model import health_predictor
from app.ai.battery_model import battery_predictor

router = APIRouter()

# ==========================================
# 👇 PASTE YOUR WEBHOOK URL HERE 👇
# ==========================================
WEBHOOK_URL = "https://webhook.site/4e525158-f183-40a9-adf6-60f4a5a815ba" 
# (I copied the one from your logs, but double check it!)

# --- Models ---
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

# --- 🧹 THE SANITIZER FUNCTION (Fixes the Crash) ---
def clean_data(data):
    """
    Recursively scans data. If it finds 'NaN' (Not a Number), 
    it replaces it with 0.0 so JSON doesn't crash.
    """
    if isinstance(data, dict):
        return {k: clean_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_data(i) for i in data]
    elif isinstance(data, float):
        # If the number is broken (NaN or Infinite), make it 0
        if math.isnan(data) or math.isinf(data):
            return 0.0
    return data

# --- WEBHOOK FUNCTION ---
async def send_emergency_alert(cattle_id: str, location: dict, ai_data: dict, objects: list):
    
    # 1. Build Payload
    raw_payload = {
        "event": "GEOFENCE_BREACH",
        "severity": "HIGH",
        "message": "⚠️ Cattle is OUTSIDE the safe zone!",
        "cattle_id": cattle_id,
        "location": location,
        "ai_analysis": ai_data,
        "nearby_objects": objects
    }

    # 2. Sanitize Payload (Remove NaNs)
    safe_payload = clean_data(raw_payload)
    
    # 3. Send
    async with httpx.AsyncClient() as client:
        try:
            print(f"🚀 Sending Full Data Alert to Webhook...")
            await client.post(WEBHOOK_URL, json=safe_payload)
            print("✅ Webhook Sent Successfully!")
        except Exception as e:
            print(f"⚠️ Failed to send webhook: {e}")

# --- API Endpoint ---
@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_cattle_position(request: AnalysisRequest):
    
    # Fetch Data
    cattle_data = await db_instance.get_cattle_position(request.cattle_id)
    if not cattle_data:
        raise HTTPException(status_code=404, detail="Cattle location not found.")

    polygon_coords = await db_instance.get_relevant_polygon(request.user_id, request.cattle_id)
    if not polygon_coords:
        raise HTTPException(status_code=404, detail="Geofence not found.")

    geo_result = analyzer.analyze(cattle_data['latitude'], cattle_data['longitude'], polygon_coords)

    # AI Inputs
    input_voltage = request.voltage if request.voltage is not None and request.voltage > 0 else cattle_data.get('voltage', 0)
    input_percent = request.percent if request.percent is not None and request.percent > 0 else cattle_data.get('percent', 0)

    prev_cattle_data = cattle_data.copy()
    health_status = health_predictor.predict(cattle_data, prev_cattle_data)
    battery_msg = battery_predictor.predict(input_voltage, input_percent)

    # Alert Logic
    alert_payload = None
    
    if not geo_result["is_safe"]:
        alert_payload = AlertData(triggered=True, title="⚠️ Geo-Fence Breach!", message=f"Cattle {request.cattle_id} is outside.", severity="high")
        
        # 🔥 Trigger Webhook (With Sanitizer)
        await send_emergency_alert(
            cattle_id=request.cattle_id, 
            location=geo_result["cattle_location"],
            ai_data={"health": health_status, "battery": battery_msg},
            objects=geo_result["detected_objects"]
        )
        
    elif health_status == "distress":
        alert_payload = AlertData(triggered=True, title="⚠️ Health Anomaly!", message="Unusual movement.", severity="medium")
        
        # Trigger Webhook
        await send_emergency_alert(
            cattle_id=request.cattle_id, 
            location=geo_result["cattle_location"],
            ai_data={"health": health_status, "battery": battery_msg},
            objects=geo_result["detected_objects"]
        )

    else:
        alert_payload = AlertData(triggered=False, title="Safe", message="Normal", severity="low")

    # Sanitize the final response too, just in case
    final_response = {
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
    
    return clean_data(final_response)  