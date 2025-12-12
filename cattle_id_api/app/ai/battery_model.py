import joblib
import numpy as np
import os
from sklearn.linear_model import LinearRegression

class BatteryPredictor:
    def __init__(self):
        # Set the path to look for the file in the SAME folder as this script
        self.model_path = os.path.join(os.path.dirname(__file__), "battery_model.pkl")
        self.model = self._load_or_train()

    def _load_or_train(self):
        """Checks for the file. If missing, TRAINS a new one automatically."""
        
        # 1. Try to Load Existing File
        if os.path.exists(self.model_path):
            try:
                loaded_model = joblib.load(self.model_path)
                print(f"✅ Battery AI Model Loaded successfully.")
                return loaded_model
            except Exception as e:
                print(f"⚠️ Old model corrupted. Re-training new one...")

        # 2. If Missing or Broken -> Train NEW Model instantly
        print("⚙️ Model missing. Training a new AI model now...")
        
        # Simple training data (Voltage/Percent -> Hours)
        X_train = np.array([
            [4.2, 100], [4.0, 80], [3.8, 60], [3.7, 50], [3.5, 20]
        ])
        y_train = np.array([48, 38, 28, 24, 9]) # Hours remaining

        # Train
        new_model = LinearRegression()
        new_model.fit(X_train, y_train)

        # Save it so we have it for next time
        joblib.dump(new_model, self.model_path)
        print(f"✅ New AI Model Created & Saved at: {self.model_path}")
        
        return new_model

    def predict(self, voltage, percent):
        # Use the AI Model
        if self.model:
            try:
                features = np.array([[voltage, percent]])
                prediction = self.model.predict(features)[0]
                return f"{round(prediction, 1)} hours remaining"
            except Exception:
                pass # Fail silently to math fallback if calculation errs
        
        # Math Fallback (Just in case)
        return f"{percent * 0.5} hours remaining (Estimated)"

# Create the instance
battery_predictor = BatteryPredictor()