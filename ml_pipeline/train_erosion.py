# ml_pipeline/train_erosion.py
"""
Trains the CNN-LSTM erosion risk model defined in erosion_model.py.

Each entry in `sequence_dirs` must be a folder of chronologically-ordered,
5-band GeoTIFFs (same B2/B3/B4/B8/B11 bands as the plastic pipeline) covering
one coastal transect over time. `target_labels` marks each sequence 1 (high
erosion risk) or 0 (stable), derived from the INCOIS 34-year shoreline dataset.

This file is a placeholder training loop with example paths/labels — swap in
your real INCOIS-derived transect sequences and labels before training.
"""
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from erosion_dataset import CoastalTimeSeriesDataset
from erosion_model import CoastalErosionCNNLSTM

# 1. Define labeled coastal transect sequences
sequence_dirs = [
    "datasets/incois/transect_001",
    "datasets/incois/transect_002",
    # ... one entry per labeled transect
]
target_labels = [1, 0]  # 1 = high erosion risk, 0 = stable — replace with real labels

train_dataset = CoastalTimeSeriesDataset(sequence_dirs, target_labels)
train_loader = DataLoader(train_dataset, batch_size=2, shuffle=True)

# 2. Setup Device and Model
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = CoastalErosionCNNLSTM(in_channels=5).to(device)

# 3. Loss and Optimizer (binary risk classification — model ends in Sigmoid)
criterion = nn.BCELoss()
optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)

# 4. Training Loop
num_epochs = 15
print(f"Starting erosion model training on device: {device}")

for epoch in range(num_epochs):
    model.train()
    epoch_loss = 0

    for sequences, labels in train_loader:
        sequences = sequences.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()
        outputs = model(sequences)
        loss = criterion(outputs, labels)

        loss.backward()
        optimizer.step()

        epoch_loss += loss.item()

    print(f"Epoch [{epoch+1}/{num_epochs}], Loss: {epoch_loss/len(train_loader):.4f}")

# 5. Save Trained Model Weights
torch.save(model.state_dict(), "erosion_cnn_lstm.pth")
print("Training complete! Model weights saved to erosion_cnn_lstm.pth")