import joblib
import numpy as np
import os

class BatteryPredictor:
    def __init__(self):
        self.model = None
        # Path to your model
        model_path = os.path.join(os.path.dirname(__file__), "battery_model.pkl")
        try:
            if os.path.exists(model_path):
                self.model = joblib.load(model_path)
                print("✅ Battery AI Model Loaded")
            else:
                print("⚠️ Battery Model not found. Using Math Fallback.")
        except Exception as e:
            print(f"⚠️ Battery Model Error: {e}. Using Math Fallback.")
            self.model = None

    def predict(self, voltage, percent):
        # 1. AI PREDICTION (If model works)
        if self.model:
            try:
                # Prepare input [voltage, percent]
                features = np.array([[voltage, percent]])
                prediction = self.model.predict(features)[0]
                return f"{round(prediction, 1)} hours remaining"
            except Exception as e:
                print(f"⚠️ Prediction failed: {e}")
        
        # 2. MATH FALLBACK (If AI fails)
        # Simple logic: Assume 1% battery = 0.5 hours of life
        estimated_hours = percent * 0.5 
        return f"{estimated_hours} hours remaining (Estimated)"

battery_predictor = BatteryPredictor()