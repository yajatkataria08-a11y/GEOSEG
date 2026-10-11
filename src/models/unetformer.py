"""
UNetFormer: A UNet-like Transformer for Efficient Semantic Segmentation of Remote Sensing Imagery.
Reference:
    Wang et al., "UNetFormer: A UNet-like Transformer for Efficient Semantic Segmentation
    of Remote Sensing Urban Scene Imagery", ISPRS Journal of Photogrammetry and Remote Sensing, 2022.
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Tuple, Optional


class ConvBNReLU(nn.Sequential):
    def __init__(self, in_ch, out_ch, kernel_size=3, stride=1, padding=1, dilation=1, groups=1):
        super().__init__(
            nn.Conv2d(in_ch, out_ch, kernel_size, stride, padding, dilation, groups, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
        )


class GlobalLocalAttention(nn.Module):
    """
    Global-Local Transformer Attention Block (GLTA).
    Captures both fine-grained local high-frequency textures and long-range geospatial dependencies.
    """
    def __init__(self, dim: int, num_heads: int = 4, sr_ratio: int = 2):
        super().__init__()
        self.dim = dim
        self.num_heads = num_heads
        self.head_dim = dim // num_heads
        self.scale = self.head_dim ** -0.5
        self.sr_ratio = sr_ratio

        # Local branch (Depthwise Conv)
        self.local_conv = nn.Sequential(
            nn.Conv2d(dim, dim, kernel_size=3, padding=1, groups=dim, bias=False),
            nn.BatchNorm2d(dim),
            nn.GELU(),
        )

        # Global branch (Spatial Reduction Attention)
        self.q = nn.Linear(dim, dim, bias=False)
        self.kv = nn.Linear(dim, dim * 2, bias=False)
        self.proj = nn.Linear(dim, dim)

        if sr_ratio > 1:
            self.sr = nn.Sequential(
                nn.Conv2d(dim, dim, kernel_size=sr_ratio, stride=sr_ratio, bias=False),
                nn.BatchNorm2d(dim),
            )
            self.norm = nn.LayerNorm(dim)
        else:
            self.sr = None
            self.norm = None

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        b, c, h, w = x.shape
        # Local branch
        x_local = self.local_conv(x)

        # Global branch
        x_flat = x.flatten(2).transpose(1, 2)  # (B, N, C)
        q = self.q(x_flat).reshape(b, h * w, self.num_heads, self.head_dim).permute(0, 2, 1, 3)

        if self.sr is not None:
            x_sr = self.sr(x).flatten(2).transpose(1, 2)
            x_sr = self.norm(x_sr)
            kv = self.kv(x_sr).reshape(b, -1, 2, self.num_heads, self.head_dim).permute(2, 0, 3, 1, 4)
        else:
            kv = self.kv(x_flat).reshape(b, -1, 2, self.num_heads, self.head_dim).permute(2, 0, 3, 1, 4)

        k, v = kv[0], kv[1]

        attn = (q @ k.transpose(-2, -1)) * self.scale
        attn = attn.softmax(dim=-1)

        global_out = (attn @ v).transpose(1, 2).reshape(b, h * w, c)
        global_out = self.proj(global_out).transpose(1, 2).reshape(b, c, h, w)

        return x + x_local + global_out


class GLTB(nn.Module):
    """Global-Local Transformer Block with Feed-Forward Network."""
    def __init__(self, dim: int, num_heads: int = 4, sr_ratio: int = 2, mlp_ratio: float = 2.0):
        super().__init__()
        self.norm1 = nn.BatchNorm2d(dim)
        self.attn = GlobalLocalAttention(dim, num_heads=num_heads, sr_ratio=sr_ratio)
        self.norm2 = nn.BatchNorm2d(dim)
        
        hidden_dim = int(dim * mlp_ratio)
        self.ffn = nn.Sequential(
            nn.Conv2d(dim, hidden_dim, 1, bias=False),
            nn.BatchNorm2d(hidden_dim),
            nn.GELU(),
            nn.Conv2d(hidden_dim, dim, 1, bias=False),
            nn.BatchNorm2d(dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x + self.attn(self.norm1(x))
        x = x + self.ffn(self.norm2(x))
        return x


class UNetFormerDecoder(nn.Module):
    """Hierarchical decoder with GLTB transformer blocks and skip fusion."""
    def __init__(self, encoder_channels: List[int] = [64, 128, 256, 512], decoder_dim: int = 128):
        super().__init__()
        c1, c2, c3, c4 = encoder_channels

        self.lat_c4 = ConvBNReLU(c4, decoder_dim, 1, padding=0)
        self.lat_c3 = ConvBNReLU(c3, decoder_dim, 1, padding=0)
        self.lat_c2 = ConvBNReLU(c2, decoder_dim, 1, padding=0)
        self.lat_c1 = ConvBNReLU(c1, decoder_dim, 1, padding=0)

        self.gltb4 = GLTB(decoder_dim, num_heads=4, sr_ratio=1)
        self.gltb3 = GLTB(decoder_dim, num_heads=4, sr_ratio=2)
        self.gltb2 = GLTB(decoder_dim, num_heads=4, sr_ratio=2)
        self.gltb1 = GLTB(decoder_dim, num_heads=4, sr_ratio=4)

        self.fuse3 = ConvBNReLU(decoder_dim * 2, decoder_dim, 3, padding=1)
        self.fuse2 = ConvBNReLU(decoder_dim * 2, decoder_dim, 3, padding=1)
        self.fuse1 = ConvBNReLU(decoder_dim * 2, decoder_dim, 3, padding=1)

    def forward(self, feats: List[torch.Tensor]) -> torch.Tensor:
        c1, c2, c3, c4 = feats

        p4 = self.gltb4(self.lat_c4(c4))

        p4_up = F.interpolate(p4, size=c3.shape[2:], mode="bilinear", align_corners=False)
        p3 = self.fuse3(torch.cat([p4_up, self.lat_c3(c3)], dim=1))
        p3 = self.gltb3(p3)

        p3_up = F.interpolate(p3, size=c2.shape[2:], mode="bilinear", align_corners=False)
        p2 = self.fuse2(torch.cat([p3_up, self.lat_c2(c2)], dim=1))
        p2 = self.gltb2(p2)

        p2_up = F.interpolate(p2, size=c1.shape[2:], mode="bilinear", align_corners=False)
        p1 = self.fuse1(torch.cat([p2_up, self.lat_c1(c1)], dim=1))
        p1 = self.gltb1(p1)

        return p1


class UNetFormer(nn.Module):
    """
    UNetFormer model for Satellite Scene Land Cover Segmentation.
    
    Args:
        in_channels: Number of input bands (3 for RGB, 13 for Sentinel-2, 16 for Multispectral + Indices).
        num_classes: Number of semantic output classes.
        decoder_dim: Feature dimension of Transformer blocks.
    """
    def __init__(self, in_channels: int = 3, num_classes: int = 7, decoder_dim: int = 128):
        super().__init__()
        self.in_channels = in_channels
        self.num_classes = num_classes

        # ResNet-style Encoder
        self.stem = nn.Sequential(
            nn.Conv2d(in_channels, 64, kernel_size=7, stride=2, padding=3, bias=False),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
        )
        self.maxpool = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)

        # Stage 1: 64 ch
        self.layer1 = nn.Sequential(
            ConvBNReLU(64, 64),
            ConvBNReLU(64, 64),
        )
        # Stage 2: 128 ch
        self.layer2 = nn.Sequential(
            ConvBNReLU(64, 128, stride=2),
            ConvBNReLU(128, 128),
        )
        # Stage 3: 256 ch
        self.layer3 = nn.Sequential(
            ConvBNReLU(128, 256, stride=2),
            ConvBNReLU(256, 256),
        )
        # Stage 4: 512 ch
        self.layer4 = nn.Sequential(
            ConvBNReLU(256, 512, stride=2),
            ConvBNReLU(512, 512),
        )

        self.decoder = UNetFormerDecoder(
            encoder_channels=[64, 128, 256, 512],
            decoder_dim=decoder_dim,
        )

        self.head = nn.Sequential(
            ConvBNReLU(decoder_dim, decoder_dim, 3, padding=1),
            nn.Dropout2d(0.1),
            nn.Conv2d(decoder_dim, num_classes, kernel_size=1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        input_size = x.shape[2:]

        # Encoder forward
        x0 = self.stem(x)         # 1/2
        c1 = self.layer1(x0)       # 1/2
        c2 = self.layer2(c1)       # 1/4
        c3 = self.layer3(c2)       # 1/8
        c4 = self.layer4(c3)       # 1/16

        # Decoder forward
        feat = self.decoder([c1, c2, c3, c4])  # 1/2

        # Segmentation Head & Upsample to original input size
        out = self.head(feat)
        out = F.interpolate(out, size=input_size, mode="bilinear", align_corners=False)
        return out
