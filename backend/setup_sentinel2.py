# backend/datasets/setup_sentinel2.py
import os
import json

sentinel_dir = os.path.join(os.path.dirname(__file__), "sentinel_2")
os.makedirs(sentinel_dir, exist_ok=True)

sample_tiles = [
    {"tile_id": "T43QDA", "location": "Visakhapatnam", "bands": ["B02", "B03", "B04", "B08", "B11", "B12"], "resolution": "10m"},
    {"tile_id": "T43REQ", "location": "Mumbai Coast", "bands": ["B02", "B03", "B04", "B08", "B11", "B12"], "resolution": "10m"},
    {"tile_id": "T45QXF", "location": "Digha Beach", "bands": ["B02", "B03", "B04", "B08", "B11", "B12"], "resolution": "10m"}
]

with open(os.path.join(sentinel_dir, "sentinel2_index.json"), "w") as f:
    json.dump(sample_tiles, f, indent=4)

print("✅ Added Sentinel-2 dataset index into backend/datasets/sentinel_2/")