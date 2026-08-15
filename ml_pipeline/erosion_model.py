# ml_pipeline/erosion_model.py
import torch
import torch.nn as nn

class CoastalErosionCNNLSTM(nn.Module):
    def __init__(self, in_channels=5):
        super(CoastalErosionCNNLSTM, self).__init__()
        
        # Spatial Feature Extractor (CNN)
        self.cnn = nn.Sequential(
            nn.Conv2d(in_channels, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),
            
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),
            
            nn.AdaptiveAvgPool2d((4, 4))  # Compresses spatial maps to a fixed (64, 4, 4) grid
        )
        
        # Temporal Dependency Engine (LSTM)
        self.lstm = nn.LSTM(
            input_size=64 * 4 * 4,
            hidden_size=128,
            num_layers=2,
            batch_first=True,
            dropout=0.2
        )
        
        # Erosion Risk Prediction Head
        self.fc = nn.Sequential(
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 1),  # Outputs probability score of severe erosion
            nn.Sigmoid()
        )

    def forward(self, x):
        # Input shape: (BatchSize, TimeSteps, Channels, Height, Width)
        batch_size, time_steps, C, H, W = x.size()
        
        # Flatten time and batch dimensions to pass images through the CNN
        c_in = x.view(batch_size * time_steps, C, H, W)
        c_out = self.cnn(c_in)  # Output: (Batch * Time, 64, 4, 4)
        
        feature_dim = 64 * 4 * 4
        r_in = c_out.view(batch_size, time_steps, feature_dim)
        
        # Pass sequential features through LSTM
        lstm_out, _ = self.lstm(r_in)  # Output: (Batch, Time, 128)
        
        # Use the final time step's hidden state to predict erosion probability
        out = self.fc(lstm_out[:, -1, :])
        return out