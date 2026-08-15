# backend/train_model.py
import os
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score

# Ensure models output directory exists
MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(MODELS_DIR, exist_ok=True)

def generate_coastal_dataset(samples=1000):
    """
    Generates synthetic coastal telemetry data for CERI and PPDS models.
    """
    np.random.seed(42)

    # Features for CERI (Coastal Erosion Risk Index)
    wave_height_m = np.random.uniform(0.5, 6.0, samples)           # Wave height in meters
    tidal_range_m = np.random.uniform(0.2, 4.5, samples)           # Tidal range in meters
    coastal_slope_deg = np.random.uniform(1.0, 35.0, samples)       # Coastal slope in degrees
    vegetation_cover_pct = np.random.uniform(5.0, 90.0, samples)    # Bio-shield vegetation %
    sediment_coarseness = np.random.uniform(0.1, 2.0, samples)     # Grain size mm

    # Target: CERI Calculation (0 to 100)
    # Higher wave/tide/slope increase risk; high vegetation/coarse sediment decrease risk
    ceri_target = (
        (wave_height_m * 8.5) + 
        (tidal_range_m * 6.0) + 
        (coastal_slope_deg * 1.2) - 
        (vegetation_cover_pct * 0.45) - 
        (sediment_coarseness * 5.0) + 
        np.random.normal(0, 3, samples)
    )
    ceri_target = np.clip(ceri_target, 0, 100)

    # Features for PPDS (Plastic Pollution Density Score)
    population_density = np.random.uniform(500, 25000, samples)     # People per sq km
    coastal_drain_count = np.random.randint(1, 20, samples)         # Storm drains in 2km radius
    river_proximity_km = np.random.uniform(0.1, 25.0, samples)       # Distance to nearest river mouth
    vessel_density = np.random.uniform(2, 50, samples)               # Ships/boats per day
    monsoon_runoff_idx = np.random.uniform(0.1, 1.0, samples)        # Runoff index

    # Target: PPDS Calculation (0 to 100)
    # Higher pop density, drain count, runoff & vessels increase risk; distance to river decreases risk
    ppds_target = (
        (population_density / 400) + 
        (coastal_drain_count * 2.5) + 
        (vessel_density * 0.6) + 
        (monsoon_runoff_idx * 25.0) - 
        (river_proximity_km * 1.1) + 
        np.random.normal(0, 4, samples)
    )
    ppds_target = np.clip(ppds_target, 0, 100)

    df = pd.DataFrame({
        # CERI Features
        "wave_height_m": wave_height_m,
        "tidal_range_m": tidal_range_m,
        "coastal_slope_deg": coastal_slope_deg,
        "vegetation_cover_pct": vegetation_cover_pct,
        "sediment_coarseness": sediment_coarseness,
        "ceri_target": ceri_target,

        # PPDS Features
        "population_density": population_density,
        "coastal_drain_count": coastal_drain_count,
        "river_proximity_km": river_proximity_km,
        "vessel_density": vessel_density,
        "monsoon_runoff_idx": monsoon_runoff_idx,
        "ppds_target": ppds_target
    })

    return df

def train_ceri_model(df):
    """Trains and exports the CERI Random Forest model."""
    print("Training CERI Model (Coastal Erosion Risk Index)...")
    
    X = df[["wave_height_m", "tidal_range_m", "coastal_slope_deg", "vegetation_cover_pct", "sediment_coarseness"]]
    y = df["ceri_target"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, preds))
    r2 = r2_score(y_test, preds)

    print(f"  └─ CERI Model RMSE: {rmse:.3f}")
    print(f"  └─ CERI Model R² Score: {r2:.3f}")

    model_path = os.path.join(MODELS_DIR, "ceri_model.pkl")
    joblib.dump(model, model_path)
    print(f"  └─ Saved model to {model_path}\n")

def train_ppds_model(df):
    """Trains and exports the PPDS Random Forest model."""
    print("Training PPDS Model (Plastic Pollution Density Score)...")

    X = df[["population_density", "coastal_drain_count", "river_proximity_km", "vessel_density", "monsoon_runoff_idx"]]
    y = df["ppds_target"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, preds))
    r2 = r2_score(y_test, preds)

    print(f"  └─ PPDS Model RMSE: {rmse:.3f}")
    print(f"  └─ PPDS Model R² Score: {r2:.3f}")

    model_path = os.path.join(MODELS_DIR, "ppds_model.pkl")
    joblib.dump(model, model_path)
    print(f"  └─ Saved model to {model_path}\n")

if __name__ == "__main__":
    print("==================================================")
    print("  CoastSentinel AI — Model Training Pipeline      ")
    print("==================================================")
    
    data = generate_coastal_dataset(samples=1500)
    train_ceri_model(data)
    train_ppds_model(data)

    print("✅ All models trained and serialized successfully!")