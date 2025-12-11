import joblib
import pandas as pd
import os

MODEL_PATH = "app/ai/models/battery_model.pkl"

class BatteryPredictor:
    def __init__(self):
        self.model = None
        if os.path.exists(MODEL_PATH):
            self.model = joblib.load(MODEL_PATH)

    def predict(self, voltage, percent):
        if not self.model: return "Unknown"
        try:
            # Predict hours left
            hours = self.model.predict(pd.DataFrame([[voltage, percent]], columns=['voltage', 'percent']))[0]
            return f"{max(0, round(hours, 1))} hours remaining"
        except:
            return "Unknown"

battery_predictor = BatteryPredictor()