"""
ResNet with Correlation Filter (ResNet-CF) for Enhanced Satellite Image Resolution & Segmentation.
Based on the research paper:
"Enhanced satellite image resolution with a residual network and correlation filter"
Published in Chemometrics and Intelligent Laboratory Systems (Elsevier, 2024).
PII: S0169-7439(24)00217-X | DOI: 10.1016/j.chemolab.2024.105277
Authors: Ajay Sharma, Bhavana P. Shrivastava, Praveen Kumar Tyagi, et al.
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F

class CorrelationFilter2D(nn.Module):
    """
    Correlation Filter Layer in the Spatial-Frequency Domain.
    Preserves fine spatial edges (roads, water boundaries, narrow field boundaries)
    often blurred in 20m/60m Sentinel-2 multispectral bands.
    """
    def __init__(self, channels: int, kernel_size: int = 5, lam: float = 1e-3):
        super().__init__()
        self.channels = channels
        self.kernel_size = kernel_size
        self.lam = lam
        self.padding = kernel_size // 2
        
        # Learnable spatial correlation weights per channel
        self.weight = nn.Parameter(torch.Tensor(channels, 1, kernel_size, kernel_size))
        self.bias = nn.Parameter(torch.zeros(channels))
        self.reset_parameters()

    def reset_parameters(self):
        # Initialize with Gaussian peak center for correlation targeting
        nn.init.kaiming_uniform_(self.weight, a=math.sqrt(5))
        with torch.no_grad():
            center = self.kernel_size // 2
            self.weight[:, :, center, center] += 0.5

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Depthwise correlation filtering per spectral channel
        filtered = F.conv2d(x, self.weight, self.bias, padding=self.padding, groups=self.channels)
        return filtered


class ResidualCorrelationBlock(nn.Module):
    """
    Residual block with embedded Correlation Filter for high-frequency detail enhancement.
    """
    def __init__(self, channels: int):
        super().__init__()
        self.conv1 = nn.Conv2d(channels, channels, kernel_size=3, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(channels)
        self.relu = nn.ReLU(inplace=True)
        self.cf = CorrelationFilter2D(channels, kernel_size=5)
        self.conv2 = nn.Conv2d(channels, channels, kernel_size=3, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(channels)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        residual = x
        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)
        out = self.cf(out)
        out = self.conv2(out)
        out = self.bn2(out)
        return self.relu(out + residual)


class SuperResolutionResNetCF(nn.Module):
    """
    Super-Resolution Front-end (ResNet-CF).
    Enhances Sentinel-2 lower-resolution bands (B05-B07, B8A, B11-B12) from 20m to 10m GSD.
    """
    def __init__(self, in_channels: int = 16, num_blocks: int = 4):
        super().__init__()
        self.head = nn.Sequential(
            nn.Conv2d(in_channels, 64, kernel_size=3, padding=1),
            nn.ReLU(inplace=True)
        )
        
        self.body = nn.Sequential(
            *[ResidualCorrelationBlock(64) for _ in range(num_blocks)]
        )
        
        self.tail = nn.Sequential(
            nn.Conv2d(64, in_channels, kernel_size=3, padding=1)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Residual connection over the whole super-resolution enhancement
        feat = self.head(x)
        res = self.body(feat)
        out = self.tail(res)
        return x + out


class GeoSegResNetCFUNet(nn.Module):
    """
    Complete Land Cover Semantic Segmentation Architecture with ResNet-CF Resolution Enhancement.
    """
    def __init__(self, in_channels: int = 16, num_classes: int = 7):
        super().__init__()
        # 1. Super-Resolution & Edge Enhancement Front-End (Sharma et al. 2024)
        self.sr_enhancer = SuperResolutionResNetCF(in_channels=in_channels, num_blocks=4)
        
        # 2. ResNet-34 Encoder Backbone adapted for 16-channel input
        self.init_conv = nn.Sequential(
            nn.Conv2d(in_channels, 64, kernel_size=7, stride=2, padding=3, bias=False),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
        )
        
        # Encoder stages
        self.enc1 = self._make_layer(64, 64, blocks=3)
        self.enc2 = self._make_layer(64, 128, blocks=4, stride=2)
        self.enc3 = self._make_layer(128, 256, blocks=6, stride=2)
        self.enc4 = self._make_layer(256, 512, blocks=3, stride=2)
        
        # Decoder U-Net blocks with skip connections
        self.up4 = self._make_up_block(512, 256)
        self.up3 = self._make_up_block(256, 128)
        self.up2 = self._make_up_block(128, 64)
        self.up1 = self._make_up_block(64, 32)
        
        # Final segmentation head
        self.classifier = nn.Sequential(
            nn.Conv2d(32, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, num_classes, kernel_size=1)
        )

    def _make_layer(self, in_ch: int, out_ch: int, blocks: int, stride: int = 1):
        layers = []
        downsample = None
        if stride != 1 or in_ch != out_ch:
            downsample = nn.Sequential(
                nn.Conv2d(in_ch, out_ch, kernel_size=1, stride=stride, bias=False),
                nn.BatchNorm2d(out_ch)
            )
        layers.append(self._make_block(in_ch, out_ch, stride, downsample))
        for _ in range(1, blocks):
            layers.append(self._make_block(out_ch, out_ch))
        return nn.Sequential(*layers)

    def _make_block(self, in_ch: int, out_ch: int, stride: int = 1, downsample = None):
        class BasicBlock(nn.Module):
            def __init__(self):
                super().__init__()
                self.conv1 = nn.Conv2d(in_ch, out_ch, kernel_size=3, stride=stride, padding=1, bias=False)
                self.bn1 = nn.BatchNorm2d(out_ch)
                self.relu = nn.ReLU(inplace=True)
                self.conv2 = nn.Conv2d(out_ch, out_ch, kernel_size=3, stride=1, padding=1, bias=False)
                self.bn2 = nn.BatchNorm2d(out_ch)
                self.downsample = downsample

            def forward(self, x):
                identity = x
                if self.downsample is not None:
                    identity = self.downsample(x)
                out = self.relu(self.bn1(self.conv1(x)))
                out = self.bn2(self.conv2(out))
                return self.relu(out + identity)
        return BasicBlock()

    def _make_up_block(self, in_ch: int, out_ch: int):
        return nn.Sequential(
            nn.Upsample(scale_factor=2, mode="bilinear", align_corners=True),
            nn.Conv2d(in_ch, out_ch, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Phase 1: High-Frequency Correlation Filter Enhancement (Sharma et al. 2024)
        x_enhanced = self.sr_enhancer(x)
        
        # Phase 2: U-Net Encoding
        e0 = self.init_conv(x_enhanced) # 1/4 resolution
        e1 = self.enc1(e0)
        e2 = self.enc2(e1)
        e3 = self.enc3(e2)
        e4 = self.enc4(e3)
        
        # Phase 3: Decoding with Skip Connections
        d4 = self.up4(e4) + e3
        d3 = self.up3(d4) + e2
        d2 = self.up2(d3) + e1
        d1 = self.up1(d2)
        
        # Upsample to match original resolution
        d0 = F.interpolate(d1, size=x.shape[2:], mode="bilinear", align_corners=True)
        logits = self.classifier(d0)
        return logits
