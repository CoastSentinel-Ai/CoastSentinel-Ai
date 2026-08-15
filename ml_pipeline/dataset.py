# ml_pipeline/dataset.py
import os
import rasterio
import torch
from torch.utils.data import Dataset

class MarineDebrisDataset(Dataset):
    def __init__(self, image_dir, mask_dir):
        self.image_dir = image_dir
        self.mask_dir = mask_dir
        self.images = sorted(os.listdir(image_dir))

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):
        img_name = self.images[idx]
        img_path = os.path.join(self.image_dir, img_name)
        mask_path = os.path.join(self.mask_dir, img_name)

        # Read 5-band Sentinel-2 image using rasterio
        with rasterio.open(img_path) as src:
            image = src.read()  # Shape: (5, H, W)
            
        # Read binary mask (1 for plastic, 0 for background)
        with rasterio.open(mask_path) as src:
            mask = src.read(1)  # Shape: (H, W)

        # Convert to torch tensors and normalize Sentinel-2 reflectance values
        image = torch.tensor(image, dtype=torch.float32) / 10000.0  
        mask = torch.tensor(mask, dtype=torch.float32).unsqueeze(0)  # Shape: (1, H, W)

        return image, mask