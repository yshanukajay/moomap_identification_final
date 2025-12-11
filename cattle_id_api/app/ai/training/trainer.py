import pandas as pd
import joblib
import asyncio
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LinearRegression
from app.services.db_manager import db_instance
from geopy.distance import geodesic

HEALTH_MODEL_PATH = "app/ai/models/health_model.pkl"
BATTERY_MODEL_PATH = "app/ai/models/battery_model.pkl"

async def train_models():
    print("--- 🚀 Starting AI Training (Fixed) ---")
    await db_instance.connect_to_database()
    
    # 1. Fetch Data
    collection = db_instance.db["dummy_data_CSV_labeled"]
    cursor = collection.find({})
    data = await cursor.to_list(length=10000)
    
    if not data:
        print("❌ No data found.")
        return

    df_raw = pd.DataFrame(data)

    # --- THE FIX IS HERE ---
    # We extract 'ts_ms' from the battery object and make it a real column
    print("Extracting timestamps...")
    try:
        df_raw['ts_ms'] = df_raw['battery'].apply(lambda x: x.get('ts_ms'))
    except Exception as e:
        print(f"❌ Error extracting timestamps: {e}")
        return

    # Now we can safely sort
    health_rows = []
    battery_rows = []

    for device_id, group in df_raw.groupby("device_id"):
        # Sort by the new extracted column
        group = group.sort_values("ts_ms")
        max_time = group["ts_ms"].max()
        
        for i in range(len(group)):
            curr = group.iloc[i]
            
            # --- BATTERY LOGIC ---
            time_left_ms = max_time - curr["ts_ms"]
            hours_left = time_left_ms / (1000 * 60 * 60)
            
            try:
                # Extract voltage/percent safely
                volts = curr["battery"]["voltage"]
                perc = curr["battery"]["percent"]
                
                # Only train if we have valid time left
                if hours_left >= 0:
                    battery_rows.append({
                        "voltage": volts,
                        "percent": perc,
                        "hours_left": hours_left
                    })
            except: pass

            # --- HEALTH LOGIC ---
            if i > 0:
                prev = group.iloc[i-1]
                try:
                    p1 = (prev["gps"]["lat"], prev["gps"]["lon"])
                    p2 = (curr["gps"]["lat"], curr["gps"]["lon"])
                    
                    dist = geodesic(p1, p2).meters
                    time_diff = (curr["ts_ms"] - prev["ts_ms"]) / 1000.0
                    
                    speed = dist / time_diff if time_diff > 0 else 0
                    
                    health_rows.append({
                        "speed": speed,
                        "label": curr["label"]
                    })
                except: pass

    # TRAIN HEALTH
    df_health = pd.DataFrame(health_rows)
    if not df_health.empty:
        clf = RandomForestClassifier(n_estimators=100)
        clf.fit(df_health[['speed']], df_health['label'])
        joblib.dump(clf, HEALTH_MODEL_PATH)
        print(f"✅ Health Model Saved ({len(df_health)} records)")

    # TRAIN BATTERY
    df_batt = pd.DataFrame(battery_rows)
    if not df_batt.empty:
        reg = LinearRegression()
        reg.fit(df_batt[['voltage', 'percent']], df_batt['hours_left'])
        joblib.dump(reg, BATTERY_MODEL_PATH)
        print(f"✅ Battery Model Saved ({len(df_batt)} records)")
        
    await db_instance.close_database_connection()
    print("--- Training Complete ---")

if __name__ == "__main__":
    asyncio.run(train_models())