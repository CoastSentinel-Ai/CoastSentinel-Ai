# backend/fastapi_app.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import random
import uvicorn

app = FastAPI(
    title="CoastSentinel AI Public Trend API",
    description="Public endpoints for Coastal Erosion Risk Index (CERI) & Plastic Pollution Density Scores (PPDS)",
    version="1.0.0"
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ErosionPredictionRequest(BaseModel):
    zone_id: str
    historical_months: int = 6

@app.get("/")
def read_root():
    return {"service": "CoastSentinel FastAPI Public Analytics", "status": "active"}

# 1. Public Trend API (Used by Analytics Dashboard)
@app.get("/api/v1/public/trends")
def get_public_coastal_trends():
    """
    Returns time-series trend data comparing CERI (Erosion) and PPDS (Plastic Density)
    """
    return {
        "dates": ["Jul 1", "Jul 8", "Jul 15", "Jul 22", "Jul 29"],
        "metrics": {
            "ceri_erosion_score": [82, 78, 74, 71, 74],
            "plastic_density_ppds": [45, 42, 38, 35, 35],
            "composite_health_index": [63.5, 60.0, 56.0, 53.0, 54.5]
        },
        "zones_monitored": ["vizag-rk-beach", "kakinada-coast", "alappuzha-beach"]
    }

# 2. CNN-LSTM Erosion Risk Prediction Endpoint
@app.post("/api/v1/public/erosion/predict")
def predict_erosion_risk(payload: ErosionPredictionRequest):
    """
    Simulates CNN-LSTM sequential image evaluation for shoreline recession prediction
    """
    predicted_recession_meters = round(random.uniform(2.1, 5.8), 2)
    ceri_score = int(70 + (predicted_recession_meters * 4))
    
    return {
        "zone_id": payload.zone_id,
        "ceri_score": min(ceri_score, 99),
        "risk_level": "High" if ceri_score > 75 else "Moderate",
        "predicted_shoreline_recession_m": predicted_recession_meters,
        "confidence": 0.89,
        "model_architecture": "ResNet50-CNN-LSTM Temporal Model"
    }

if __name__ == "__main__":
    uvicorn.run("fastapi_app:app", host="0.0.0.0", port=8000, reload=True)