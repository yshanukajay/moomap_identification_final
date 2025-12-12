import joblib
import pandas as pd
from sklearn.linear_model import LinearRegression
import os

print("--- 🧠 Training Battery AI Model ---")

# 1. Create simple training data (Voltage/Percent -> Hours Left)
data = {
    'voltage': [4.2, 4.1, 4.0, 3.9, 3.8, 3.7, 3.6, 3.5],
    'percent': [100, 90, 80, 70, 60, 50, 40, 20],
    'hours_left': [48, 43, 38, 33, 28, 24, 19, 9]  # Example lifespan
}
df = pd.DataFrame(data)

# 2. Train the Model
X = df[['voltage', 'percent']]
y = df['hours_left']
model = LinearRegression()
model.fit(X, y)

# 3. Save the file to the correct folder (app/ai/)
save_path = os.path.join("app", "ai", "battery_model.pkl")
os.makedirs(os.path.dirname(save_path), exist_ok=True)

joblib.dump(model, save_path)
print(f"✅ Success! Model saved to: {save_path}")
print("--- You can now restart the server ---")