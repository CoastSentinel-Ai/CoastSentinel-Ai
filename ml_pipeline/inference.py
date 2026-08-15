# ml_pipeline/inference.py
import torch
import rasterio
from rasterio.features import shapes
import segmentation_models_pytorch as smp
import json

def detect_plastic_hotspots(image_path, model_path="best_model.pth", threshold=0.5):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    # 1. Load trained UNet++ Model
    model = smp.UnetPlusPlus(
        encoder_name="resnet50",
        encoder_weights=None,
        in_channels=5,
        classes=1
    ).to(device)
    
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()

    # 2. Load Satellite GeoTIFF
    with rasterio.open(image_path) as src:
        image = src.read()  # (5, H, W)
        transform = src.transform
        crs = src.crs

    # Preprocess & Inference
    input_tensor = torch.tensor(image, dtype=torch.float32).unsqueeze(0) / 10000.0
    input_tensor = input_tensor.to(device)

    with torch.no_grad():
        output = model(input_tensor)
        probs = torch.sigmoid(output).squeeze().cpu().numpy()

    # Binary mask creation based on threshold
    binary_mask = (probs > threshold).astype('uint8')

    # 3. Vectorize raster mask into GeoJSON polygons
    results = []
    for geom, val in shapes(binary_mask, mask=(binary_mask == 1), transform=transform):
        results.append({
            "type": "Feature",
            "geometry": geom,
            "properties": {
                "class": "marine_plastic",
                "confidence": float(probs[binary_mask == 1].mean() if (binary_mask == 1).any() else 0.0)
            }
        })

    geojson_output = {
        "type": "FeatureCollection",
        "crs": {"type": "name", "properties": {"name": str(crs)}},
        "features": results
    }

    return geojson_output

if __name__ == "__main__":
    # Example usage
    geojson_data = detect_plastic_hotspots("datasets/sentinel_2/sample_tile.tif")
    with open("detected_pollution.geojson", "w") as f:
        json.dump(geojson_data, f)
    print("Successfully generated detected_pollution.geojson")