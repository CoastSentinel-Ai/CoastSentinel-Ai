# ml_pipeline/erosion_dataset.py
import os
import rasterio
import torch
from torch.utils.data import Dataset

class CoastalTimeSeriesDataset(Dataset):
    def __init__(self, sequence_dirs, target_labels):
        """
        sequence_dirs: list of folders, each containing chronological multi-band TIFFs
        target_labels: list of float labels (0 for stable coastline, 1 for high erosion risk)
        """
        self.sequence_dirs = sequence_dirs
        self.labels = target_labels

    def __len__(self):
        return len(self.sequence_dirs)

    def __getitem__(self, idx):
        folder = self.sequence_dirs[idx]
        image_files = sorted(os.listdir(folder))
        
        sequence_tensors = []
        for img_file in image_files:
            img_path = os.path.join(folder, img_file)
            with rasterio.open(img_path) as src:
                img = src.read()  # Shape: (5, H, W)
            tensor_img = torch.tensor(img, dtype=torch.float32) / 10000.0
            sequence_tensors.append(tensor_img)
            
        # Stack into temporal sequence tensor: (TimeSteps, Channels, Height, Width)
        sequence_tensor = torch.stack(sequence_tensors, dim=0)
        label = torch.tensor([self.labels[idx]], dtype=torch.float32)
        
        return sequence_tensor, label