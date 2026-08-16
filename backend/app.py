# backend/app.py

# load_dotenv() MUST run before database/alerts/ml_service are imported below —
# alerts.py reads TWILIO_* and SMTP_* from the environment at import time, so
# if .env hasn't been loaded yet, those values are locked in as None forever
# for this process, no matter how many times you restart afterwards.
from dotenv import load_dotenv
load_dotenv()

import os
import joblib
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS

# Import local database and alert modules
import database
import alerts
import ml_service

app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing for frontend fetch calls

# -------------------------------------------------------------------
# Model Loading Configuration
# -------------------------------------------------------------------
BASE_DIR = os.path.dirname(__file__)
CERI_MODEL_PATH = os.path.join(BASE_DIR, "models", "ceri_model.pkl")
PPDS_MODEL_PATH = os.path.join(BASE_DIR, "models", "ppds_model.pkl")

ceri_model = None
ppds_model = None

def load_ml_models():
    """Loads pre-trained CERI and PPDS models into memory on server start."""
    global ceri_model, ppds_model
    try:
        if os.path.exists(CERI_MODEL_PATH) and os.path.exists(PPDS_MODEL_PATH):
            ceri_model = joblib.load(CERI_MODEL_PATH)
            ppds_model = joblib.load(PPDS_MODEL_PATH)
            print("  └─ ✅ Trained ML models loaded into memory successfully.")
        else:
            print("  └─ ⚠️  ML model files missing in /models! Run train_model.py first.")
    except Exception as e:
        print(f"  └─ ❌ Error loading ML models: {e}")

# Initialize Database and Load Models on Startup
database.init_db()
load_ml_models()

# -------------------------------------------------------------------
# API Routes
# -------------------------------------------------------------------

@app.route('/api/health', methods=['GET'])
def health_check():
    """System status check including database & model readiness."""
    return jsonify({
        "status": "active",
        "database": "connected",
        "models_loaded": (ceri_model is not None and ppds_model is not None)
    }), 200


@app.route('/api/v1/predict', methods=['POST'])
def predict_coastal_health():
    """
    ML Inference Endpoint.
    Receives coastal telemetry payload and returns computed CERI and PPDS scores.
    """
    if ceri_model is None or ppds_model is None:
        return jsonify({
            "error": "ML models are not loaded on server. Please execute train_model.py."
        }), 500

    data = request.get_json() or {}

    try:
        # Extract features for CERI (with realistic defaults if omitted)
        wave_height = float(data.get('wave_height_m', 2.5))
        tidal_range = float(data.get('tidal_range_m', 1.8))
        slope = float(data.get('coastal_slope_deg', 12.0))
        veg_cover = float(data.get('vegetation_cover_pct', 35.0))
        sediment = float(data.get('sediment_coarseness', 0.8))

        # Extract features for PPDS
        pop_density = float(data.get('population_density', 8500))
        drains = int(data.get('coastal_drain_count', 8))
        river_dist = float(data.get('river_proximity_km', 4.2))
        vessels = float(data.get('vessel_density', 15.0))
        monsoon_idx = float(data.get('monsoon_runoff_idx', 0.5))

        # Array formatting for Random Forest Regressors
        ceri_features = np.array([[wave_height, tidal_range, slope, veg_cover, sediment]])
        ppds_features = np.array([[pop_density, drains, river_dist, vessels, monsoon_idx]])

        # Execute Inference
        raw_ceri = float(ceri_model.predict(ceri_features)[0])
        raw_ppds = float(ppds_model.predict(ppds_features)[0])

        ceri_score = round(np.clip(raw_ceri, 0, 100), 2)
        ppds_score = round(np.clip(raw_ppds, 0, 100), 2)

        # Derived metrics
        shoreline_retreat_m = round(ceri_score * 0.08, 2)  # Estimated annual retreat rate
        overall_risk = round((ceri_score * 0.55) + (ppds_score * 0.45), 2)

        if overall_risk >= 75:
            threat_level = "CRITICAL"
        elif overall_risk >= 45:
            threat_level = "MODERATE"
        else:
            threat_level = "STABLE"

        return jsonify({
            "status": "success",
            "location": data.get("location_name", "Custom Coordinates"),
            "predictions": {
                "ceri_score": ceri_score,
                "ppds_score": ppds_score,
                "overall_risk_score": overall_risk,
                "shoreline_retreat_m": shoreline_retreat_m,
                "threat_level": threat_level
            }
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route('/api/register_ngo', methods=['POST'])
def register_ngo():
    """Inserts NGO registration entries into SQLite."""
    data = request.get_json() or {}
    name = data.get('name')
    email = data.get('email')
    phone = data.get('phone')
    region = data.get('focus_area')  # coastal focus area maps to the 'region' column

    if not name or not email or not phone or not region:
        return jsonify({"error": "Missing required fields: name, email, phone, focus_area"}), 400

    result = database.add_ngo(name, email, phone, region)
    if not result["success"]:
        return jsonify({"status": "error", "message": result["error"]}), 409

    return jsonify({"status": "success", "id": result["id"]}), 201


@app.route('/api/report_issue', methods=['POST'])
def report_issue():
    """Logs public citizen reports into SQLite."""
    data = request.get_json() or {}
    report_type = data.get('type')
    location = data.get('location')
    description = data.get('description')

    if not location or not description:
        return jsonify({"error": "Missing required fields: location, description"}), 400

    record_id = database.add_report(report_type, location, description)
    return jsonify({"status": "success", "id": record_id}), 201


@app.route('/api/trigger_alert', methods=['POST'])
def trigger_alert():
    """Triggers external Twilio SMS emergency alerts."""
    data = request.get_json() or {}
    location = data.get('location', 'Unknown Region')
    threat_level = data.get('threat_level', 'CRITICAL')

    result = alerts.send_emergency_sms(location, threat_level)
    return jsonify(result), 200


@app.route('/api/v1/detect_plastic', methods=['POST'])
def detect_plastic():
    """
    Runs the trained UNet++ segmentation model on a Sentinel-2 GeoTIFF tile and
    returns GeoJSON polygons for detected marine plastic. Newly detected
    hotspots are also persisted so they appear on future dashboard loads.
    """
    data = request.get_json() or {}
    image_path = data.get('image_path')
    if not image_path:
        return jsonify({"error": "image_path is required"}), 400

    try:
        geojson = ml_service.run_plastic_detection(image_path)
    except ml_service.ModelNotTrainedError as e:
        return jsonify({"status": "error", "message": str(e)}), 503
    except FileNotFoundError as e:
        return jsonify({"status": "error", "message": str(e)}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

    inserted = database.record_detections(geojson)

    return jsonify({
        "status": "success",
        "detections_stored": inserted,
        "geojson": geojson
    }), 200


@app.route('/api/v1/predict_erosion', methods=['POST'])
def predict_erosion():
    """
    Runs the trained CNN-LSTM model on a time-ordered sequence of coastal
    imagery for one transect and returns an erosion risk score.
    """
    data = request.get_json() or {}
    sequence_dir = data.get('sequence_dir')
    if not sequence_dir:
        return jsonify({"error": "sequence_dir is required"}), 400

    try:
        result = ml_service.run_erosion_prediction(sequence_dir)
    except ml_service.ModelNotTrainedError as e:
        return jsonify({"status": "error", "message": str(e)}), 503
    except FileNotFoundError as e:
        return jsonify({"status": "error", "message": str(e)}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

    return jsonify({"status": "success", **result}), 200


if __name__ == '__main__':
    print("==================================================")
    print("  Starting CoastSentinel AI Backend Server        ")
    print("==================================================")
    app.run(host='0.0.0.0', port=5000, debug=True)