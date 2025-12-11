import joblib
import pandas as pd
import os
from geopy.distance import geodesic

MODEL_PATH = "app/ai/models/health_model.pkl"

class HealthPredictor:
    def __init__(self):
        self.model = None
        if os.path.exists(MODEL_PATH):
            self.model = joblib.load(MODEL_PATH)

    def predict(self, curr_doc, prev_doc):
        if not self.model: return "AI Loading..."
        try:
            # Derive Speed from Lat/Lon
            p1 = (prev_doc["latitude"], prev_doc["longitude"])
            p2 = (curr_doc["latitude"], curr_doc["longitude"])
            
            # Assuming ~10s interval if live data doesn't have timestamp
            # Ideally, pass timestamps to this function for accuracy
            speed = geodesic(p1, p2).meters / 10.0 
            
            # Predict using Speed only
            return self.model.predict(pd.DataFrame([[speed]], columns=['speed']))[0]
        except:
            return "Unknown"

health_predictor = HealthPredictor()