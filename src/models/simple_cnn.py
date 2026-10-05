"""
SimpleCNN — Lightweight classifier for pipeline validation (Phase 1).

This is NOT meant to be a good model. Its purpose is to prove that
the environment, dataloaders, and training loop all work end-to-end
before adding segmentation complexity.
"""

import torch
import torch.nn as nn


class SimpleCNN(nn.Module):
    """
    A minimal 3-block CNN for multi-band satellite image classification.

    Architecture:
        Conv2d(in, 32) → ReLU → MaxPool2d(2)
        Conv2d(32, 64) → ReLU → MaxPool2d(2)
        Conv2d(64, 128) → ReLU → AdaptiveAvgPool2d(1)
        Linear(128, num_classes)

    Args:
        in_channels: Number of input spectral bands (default 13 for Sentinel-2).
        num_classes: Number of output classes (default 10 for EuroSAT).
    """

    def __init__(self, in_channels: int = 13, num_classes: int = 10):
        super().__init__()
        self.in_channels = in_channels
        self.num_classes = num_classes

        self.features = nn.Sequential(
            # Block 1: 13 → 32 channels
            nn.Conv2d(in_channels, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),

            # Block 2: 32 → 64 channels
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),

            # Block 3: 64 → 128 channels
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d(1),
        )

        self.classifier = nn.Sequential(
            nn.Dropout(p=0.3),
            nn.Linear(128, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.

        Args:
            x: Input tensor of shape (B, C, H, W).

        Returns:
            Logits tensor of shape (B, num_classes).
        """
        x = self.features(x)
        x = x.flatten(1)  # (B, 128)
        x = self.classifier(x)
        return x

    def __repr__(self) -> str:
        params = sum(p.numel() for p in self.parameters())
        return (
            f"SimpleCNN(in_channels={self.in_channels}, "
            f"num_classes={self.num_classes}, "
            f"params={params:,})"
        )
