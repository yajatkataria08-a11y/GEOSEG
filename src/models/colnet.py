"""
ColNet: Collaborative Network for Super-Resolution and Semantic Segmentation.
Reference:
    "Collaborative Network for Super-Resolution and Semantic Segmentation of Remote Sensing Images",
    IEEE Transactions on Geoscience and Remote Sensing (TGRS).
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Tuple

from src.models.psisr import PSISRNet, CombinedLoss
from src.transforms.wavelet import WaveletEdgeLoss


class CrossTaskAttentionFusion(nn.Module):
    """
    Cross-Task Attention Fusion (CTAF) module.
    Exchanges structural detail from the SR branch and semantic context from the segmentation branch.
    """
    def __init__(self, sr_channels: int = 64, seg_channels: int = 128, fused_dim: int = 128):
        super().__init__()
        self.sr_proj = nn.Sequential(
            nn.Conv2d(sr_channels, fused_dim, 1, bias=False),
            nn.BatchNorm2d(fused_dim),
            nn.ReLU(inplace=True),
        )
        self.seg_proj = nn.Sequential(
            nn.Conv2d(seg_channels, fused_dim, 1, bias=False),
            nn.BatchNorm2d(fused_dim),
            nn.ReLU(inplace=True),
        )
        
        # Cross attention gate
        self.gate = nn.Sequential(
            nn.Conv2d(fused_dim * 2, fused_dim, 3, padding=1, bias=False),
            nn.BatchNorm2d(fused_dim),
            nn.Sigmoid(),
        )
        self.out_conv = nn.Sequential(
            nn.Conv2d(fused_dim, fused_dim, 3, padding=1, bias=False),
            nn.BatchNorm2d(fused_dim),
            nn.ReLU(inplace=True),
        )

    def forward(self, sr_feat: torch.Tensor, seg_feat: torch.Tensor) -> torch.Tensor:
        # Align spatial dimensions if necessary
        if sr_feat.shape[2:] != seg_feat.shape[2:]:
            sr_feat = F.interpolate(sr_feat, size=seg_feat.shape[2:], mode="bilinear", align_corners=False)
            
        f_sr = self.sr_proj(sr_feat)
        f_seg = self.seg_proj(seg_feat)
        
        g = self.gate(torch.cat([f_sr, f_seg], dim=1))
        fused = f_seg * g + f_sr * (1.0 - g)
        return self.out_conv(fused)


class ColNet(nn.Module):
    """
    Collaborative Multi-Task Network for Remote Sensing Super-Resolution & Semantic Segmentation.
    """
    def __init__(
        self,
        in_channels: int = 3,
        num_classes: int = 7,
        sr_base_filters: int = 64,
        scale: int = 8,
    ):
        super().__init__()
        self.scale = scale
        self.in_channels = in_channels
        self.num_classes = num_classes

        # 1. Super-Resolution Branch
        self.sr_branch = PSISRNet(
            in_channels=in_channels,
            out_channels=in_channels,
            base_filters=sr_base_filters,
        )

        # 2. Segmentation Branch (Multi-scale Feature Extractor)
        self.seg_stem = nn.Sequential(
            nn.Conv2d(in_channels, 64, 3, padding=1, bias=False),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 128, 3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
        )

        # 3. Cross-Task Fusion Module
        self.ctaf = CrossTaskAttentionFusion(
            sr_channels=sr_base_filters,
            seg_channels=128,
            fused_dim=128,
        )

        # 4. Dense Segmentation Head
        self.seg_head = nn.Sequential(
            nn.Conv2d(128, 128, 3, padding=1, bias=False),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.Dropout2d(0.1),
            nn.Conv2d(128, num_classes, kernel_size=1),
        )

    def forward(self, x_lr: torch.Tensor) -> Dict[str, torch.Tensor]:
        # SR Forward Pass
        sr_outputs = self.sr_branch(x_lr, scale=self.scale)
        sr_8x = sr_outputs["sr_8x"]
        
        # Deep SR feature maps from cascading blocks
        f0 = self.sr_branch.entry_conv(x_lr)
        f1 = self.sr_branch.deconv_2x(self.sr_branch.ub1_blocks(f0))
        f2 = self.sr_branch.deconv_4x(self.sr_branch.ub2_blocks(f1))
        sr_deep_feat = self.sr_branch.subpixel_8x(self.sr_branch.ub3_blocks(f2))

        # Segmentation Forward Pass on LR/SR features
        seg_feat = self.seg_stem(x_lr)

        # Fuse SR structural details with segmentation semantics
        fused_feat = self.ctaf(sr_deep_feat, seg_feat)

        # Predict Segmentation Mask (at 8x super-resolved target resolution)
        target_size = sr_8x.shape[2:]
        seg_logits = self.seg_head(fused_feat)
        seg_logits = F.interpolate(seg_logits, size=target_size, mode="bilinear", align_corners=False)

        return {
            "sr_2x": sr_outputs["sr_2x"],
            "sr_4x": sr_outputs["sr_4x"],
            "sr_8x": sr_8x,
            "seg_logits": seg_logits,
        }


class JointColNetLoss(nn.Module):
    """
    Unified Multi-Task Joint Loss:
    L_total = L_PSISR(2x, 4x, 8x) + lambda_wavelet * L_Wavelet(8x) + lambda_seg * L_Seg
    """
    def __init__(
        self,
        lambda_sr: float = 1.0,
        lambda_wavelet: float = 0.1,
        lambda_seg: float = 1.0,
        ignore_index: int = -100,
    ):
        super().__init__()
        self.lambda_sr = lambda_sr
        self.lambda_wavelet = lambda_wavelet
        self.lambda_seg = lambda_seg

        self.sr_loss = CombinedLoss()
        self.wavelet_loss = WaveletEdgeLoss(in_channels=3)
        self.ce_loss = nn.CrossEntropyLoss(ignore_index=ignore_index)

    def forward(
        self,
        preds: Dict[str, torch.Tensor],
        targets: Dict[str, torch.Tensor],
    ) -> Tuple[torch.Tensor, Dict[str, float]]:
        # 1. PSISR Multi-Scale Loss
        loss_2x, _, _ = self.sr_loss(preds["sr_2x"], targets["hr_2x"])
        loss_4x, _, _ = self.sr_loss(preds["sr_4x"], targets["hr_4x"])
        loss_8x, _, _ = self.sr_loss(preds["sr_8x"], targets["hr_8x"])
        l_sr = loss_2x + loss_4x + loss_8x

        # 2. Wavelet Edge Loss on 8x SR output
        l_wavelet = self.wavelet_loss(preds["sr_8x"], targets["hr_8x"])

        # 3. Segmentation Loss
        l_seg = torch.tensor(0.0, device=preds["sr_8x"].device)
        if "seg_mask" in targets and targets["seg_mask"] is not None:
            l_seg = self.ce_loss(preds["seg_logits"], targets["seg_mask"])

        total_loss = self.lambda_sr * l_sr + self.lambda_wavelet * l_wavelet + self.lambda_seg * l_seg

        metrics = {
            "loss_total": total_loss.item(),
            "loss_sr": l_sr.item(),
            "loss_wavelet": l_wavelet.item(),
            "loss_seg": l_seg.item(),
        }
        return total_loss, metrics
