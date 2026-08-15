# ml_pipeline/train_unet.py
import torch
import torch.nn as nn
import segmentation_models_pytorch as smp
from torch.utils.data import DataLoader
from dataset import MarineDebrisDataset

# 1. Initialize Dataset and DataLoader
train_dataset = MarineDebrisDataset(
    image_dir="datasets/marida/images",
    mask_dir="datasets/marida/masks"
)
train_loader = DataLoader(train_dataset, batch_size=4, shuffle=True)

# 2. Setup Device and UNet++ Model Architecture
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = smp.UnetPlusPlus(
    encoder_name="resnet50",
    encoder_weights="imagenet",
    in_channels=5,                  # B2, B3, B4, B8, B11 bands
    classes=1,                      # Binary classification: plastic vs background
    activation=None
).to(device)

# 3. Define Focal Loss Class
class FocalLoss(nn.Module):
    def __init__(self, alpha=0.25, gamma=2.0):
        super(FocalLoss, self).__init__()
        self.alpha = alpha
        self.gamma = gamma

    def forward(self, inputs, targets):
        bce_loss = nn.functional.binary_cross_entropy_with_logits(inputs, targets, reduction='none')
        pt = torch.exp(-bce_loss)
        focal_loss = self.alpha * (1 - pt) ** self.gamma * bce_loss
        return focal_loss.mean()

criterion = FocalLoss(alpha=0.25, gamma=2.0)
optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)

# 4. Model Training Loop
num_epochs = 10
print(f"Starting training on device: {device}")

for epoch in range(num_epochs):
    model.train()
    epoch_loss = 0
    
    for images, masks in train_loader:
        images = images.to(device)
        masks = masks.to(device)
        
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, masks)
        
        loss.backward()
        optimizer.step()
        
        epoch_loss += loss.item()
        
    print(f"Epoch [{epoch+1}/{num_epochs}], Loss: {epoch_loss/len(train_loader):.4f}")

# 5. Save Trained Model Weights
torch.save(model.state_dict(), "best_model.pth")
print("Training complete! Model weights successfully saved to best_model.pth")