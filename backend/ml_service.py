# backend/ml_service.py
"""
Integration layer between the Flask API and the deep learning pipeline in
ml_pipeline/. Kept separate from app.py so the lightweight CERI/PPDS heuristic
routes don't pay PyTorch's import cost when the deep learning models aren't
being called.
"""
import os
import sys

import torch

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(BACKEND_DIR)
ML_PIPELINE_DIR = os.path.join(REPO_ROOT, "ml_pipeline")
if ML_PIPELINE_DIR not in sys.path:
    sys.path.insert(0, ML_PIPELINE_DIR)

from inference import detect_plastic_hotspots  # noqa: E402
from erosion_model import CoastalErosionCNNLSTM  # noqa: E402

MODELS_DIR = os.path.join(BACKEND_DIR, "models")
UNET_WEIGHTS_PATH = os.path.join(MODELS_DIR, "unet_plastic.pth")
EROSION_WEIGHTS_PATH = os.path.join(MODELS_DIR, "erosion_cnn_lstm.pth")


class ModelNotTrainedError(Exception):
    """Raised when a deep learning model's weight file hasn't been trained/exported yet."""


def run_plastic_detection(image_path):
    """Runs the trained UNet++ model on a Sentinel-2 GeoTIFF tile and returns
    GeoJSON polygons for detected marine plastic."""
    if not os.path.exists(UNET_WEIGHTS_PATH):
        raise ModelNotTrainedError(
            "UNet++ weights not found. Run ml_pipeline/train_unet.py, then copy "
            f"the resulting best_model.pth to {UNET_WEIGHTS_PATH}."
        )
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    return detect_plastic_hotspots(image_path, model_path=UNET_WEIGHTS_PATH)


def run_erosion_prediction(sequence_dir):
    """Runs the trained CNN-LSTM model on a time-ordered sequence of 5-band
    GeoTIFFs for one coastal transect and returns an erosion risk score."""
    if not os.path.exists(EROSION_WEIGHTS_PATH):
        raise ModelNotTrainedError(
            "CNN-LSTM erosion weights not found. Run ml_pipeline/train_erosion.py, "
            f"then copy the resulting erosion_cnn_lstm.pth to {EROSION_WEIGHTS_PATH}."
        )
    if not os.path.isdir(sequence_dir):
        raise FileNotFoundError(f"Sequence directory not found: {sequence_dir}")

    import rasterio  # local import: keeps rasterio optional for routes that don't need it

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = CoastalErosionCNNLSTM(in_channels=5).to(device)
    model.load_state_dict(torch.load(EROSION_WEIGHTS_PATH, map_location=device))
    model.eval()

    image_files = sorted(os.listdir(sequence_dir))
    if not image_files:
        raise FileNotFoundError(f"No image files found in {sequence_dir}")

    tensors = []
    for fname in image_files:
        with rasterio.open(os.path.join(sequence_dir, fname)) as src:
            img = src.read()
        tensors.append(torch.tensor(img, dtype=torch.float32) / 10000.0)

    sequence_tensor = torch.stack(tensors, dim=0).unsqueeze(0).to(device)  # (1, T, C, H, W)

    with torch.no_grad():
        risk_prob = model(sequence_tensor).item()

    if risk_prob >= 0.66:
        risk_level = "High"
    elif risk_prob >= 0.33:
        risk_level = "Moderate"
    else:
        risk_level = "Low"

    return {
        "erosion_risk_probability": round(risk_prob, 4),
        "risk_level": risk_level,
        "frames_used": len(image_files)
    }