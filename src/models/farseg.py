"""
FarSeg: Foreground-Aware Relation Network for Geospatial Object Segmentation.
Reference:
    Zheng et al., "Foreground-Aware Relation Network for Geospatial Object Segmentation
    in High Spatial Resolution Remote Sensing Imagery", CVPR 2020 / IEEE TPAMI 2023.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List


class SceneRelation(nn.Module):
    """
    Foreground-Scene Relation Module (FSRM).
    Relates local spatial features with global scene context to suppress false positives.
    """
    def __init__(self, in_channels: int, scene_channels: int = 256):
        super().__init__()
        self.in_channels = in_channels
        self.scene_channels = scene_channels

        # Global scene embedding
        self.scene_encoder = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),
            nn.Conv2d(in_channels, scene_channels, 1, bias=False),
            nn.BatchNorm2d(scene_channels),
            nn.ReLU(inplace=True),
        )

        # Relational transform
        self.psi = nn.Conv2d(in_channels, scene_channels, 1, bias=False)
        self.phi = nn.Conv2d(scene_channels, scene_channels, 1, bias=False)
        self.gamma = nn.Sequential(
            nn.Conv2d(scene_channels, in_channels, 1, bias=False),
            nn.BatchNorm2d(in_channels),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        b, c, h, w = x.shape
        # Global scene vector: (B, scene_channels, 1, 1)
        scene = self.scene_encoder(x)

        # Spatial query & scene key
        q = self.psi(x).view(b, self.scene_channels, -1)  # (B, S, N)
        k = self.phi(scene).view(b, self.scene_channels, 1)  # (B, S, 1)

        # Relation affinity: (B, 1, N)
        affinity = (q * k).sum(dim=1, keepdim=True) / (self.scene_channels ** 0.5)
        affinity = torch.sigmoid(affinity).view(b, 1, h, w)

        # Feature re-weighting
        out = x * affinity
        return out + self.gamma(scene.expand(-1, -1, h, w))


class AsymmetricFPN(nn.Module):
    """Asymmetric Feature Pyramid Network decoder for high-resolution geospatial features."""
    def __init__(self, in_channels_list: List[int], out_channels: int = 128):
        super().__init__()
        self.lateral_convs = nn.ModuleList([
            nn.Conv2d(c, out_channels, 1, bias=False) for c in in_channels_list
        ])
        self.fpn_convs = nn.ModuleList([
            nn.Sequential(
                nn.Conv2d(out_channels, out_channels, 3, padding=1, bias=False),
                nn.BatchNorm2d(out_channels),
                nn.ReLU(inplace=True),
            ) for _ in in_channels_list
        ])

    def forward(self, feats: List[torch.Tensor]) -> torch.Tensor:
        # Top-down pathway
        laterals = [l_conv(f) for l_conv, f in zip(self.lateral_convs, feats)]
        
        for i in range(len(laterals) - 1, 0, -1):
            prev_shape = laterals[i - 1].shape[2:]
            laterals[i - 1] = laterals[i - 1] + F.interpolate(laterals[i], size=prev_shape, mode="bilinear", align_corners=False)
            
        fpn_outs = [f_conv(lat) for f_conv, lat in zip(self.fpn_convs, laterals)]
        
        # Merge all scales to the highest spatial resolution (P2)
        base_size = fpn_outs[0].shape[2:]
        merged = fpn_outs[0]
        for p in fpn_outs[1:]:
            merged = merged + F.interpolate(p, size=base_size, mode="bilinear", align_corners=False)
            
        return merged


class FarSeg(nn.Module):
    """
    FarSeg: Foreground-Aware Relation Network for Geospatial Segmentation.
    """
    def __init__(self, in_channels: int = 3, num_classes: int = 7, feature_dim: int = 128):
        super().__init__()
        self.in_channels = in_channels
        self.num_classes = num_classes

        # ResNet Backbone
        self.stem = nn.Sequential(
            nn.Conv2d(in_channels, 64, kernel_size=7, stride=2, padding=3, bias=False),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
        )
        self.maxpool = nn.MaxPool2d(3, stride=2, padding=1)

        self.layer1 = nn.Sequential(
            nn.Conv2d(64, 64, 3, padding=1, bias=False), nn.BatchNorm2d(64), nn.ReLU(inplace=True),
            nn.Conv2d(64, 64, 3, padding=1, bias=False), nn.BatchNorm2d(64), nn.ReLU(inplace=True)
        )
        self.layer2 = nn.Sequential(
            nn.Conv2d(64, 128, 3, stride=2, padding=1, bias=False), nn.BatchNorm2d(128), nn.ReLU(inplace=True),
            nn.Conv2d(128, 128, 3, padding=1, bias=False), nn.BatchNorm2d(128), nn.ReLU(inplace=True)
        )
        self.layer3 = nn.Sequential(
            nn.Conv2d(128, 256, 3, stride=2, padding=1, bias=False), nn.BatchNorm2d(256), nn.ReLU(inplace=True),
            nn.Conv2d(256, 256, 3, padding=1, bias=False), nn.BatchNorm2d(256), nn.ReLU(inplace=True)
        )
        self.layer4 = nn.Sequential(
            nn.Conv2d(256, 512, 3, stride=2, padding=1, bias=False), nn.BatchNorm2d(512), nn.ReLU(inplace=True),
            nn.Conv2d(512, 512, 3, padding=1, bias=False), nn.BatchNorm2d(512), nn.ReLU(inplace=True)
        )

        self.asym_fpn = AsymmetricFPN(in_channels_list=[64, 128, 256, 512], out_channels=feature_dim)
        self.fsrm = SceneRelation(in_channels=feature_dim, scene_channels=feature_dim)
        
        self.classifier = nn.Sequential(
            nn.Conv2d(feature_dim, feature_dim, 3, padding=1, bias=False),
            nn.BatchNorm2d(feature_dim),
            nn.ReLU(inplace=True),
            nn.Dropout2d(0.1),
            nn.Conv2d(feature_dim, num_classes, kernel_size=1)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        input_size = x.shape[2:]

        x0 = self.stem(x)
        c1 = self.layer1(x0)
        c2 = self.layer2(c1)
        c3 = self.layer3(c2)
        c4 = self.layer4(c3)

        fpn_feat = self.asym_fpn([c1, c2, c3, c4])
        rel_feat = self.fsrm(fpn_feat)

        out = self.classifier(rel_feat)
        out = F.interpolate(out, size=input_size, mode="bilinear", align_corners=False)
        return out
