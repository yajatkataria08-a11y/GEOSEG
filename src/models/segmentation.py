"""
Segmentation model factory — SMP-based U-Net, U-Net++, DeepLabv3+.

Uses segmentation-models-pytorch (SMP) for battle-tested encoder/decoder
architectures with pretrained ImageNet backbones.
"""

import torch
import torch.nn as nn
import segmentation_models_pytorch as smp

from src.models.channel_expand import expand_first_conv


# Supported SMP architectures
ARCHITECTURES = {
    "unet": smp.Unet,
    "unetplusplus": smp.UnetPlusPlus,
    "deeplabv3plus": smp.DeepLabV3Plus,
    "fpn": smp.FPN,
    "pspnet": smp.PSPNet,
    "linknet": smp.Linknet,
}


def build_segmentation_model(config: dict) -> nn.Module:
    """
    Build a segmentation model from a config dict.

    If `expand_pretrained` is True, builds a 3-channel model first with
    ImageNet weights, then expands the first conv layer to `in_channels`
    using weight replication. This preserves pretrained features.

    Args:
        config: Model config dict with keys:
            - name: Architecture name (unet, unetplusplus, deeplabv3plus, fpn, pspnet, linknet)
            - encoder: Encoder backbone name (e.g., resnet34, resnet50, efficientnet-b0)
            - encoder_weights: Pretrained weights (e.g., 'imagenet', None)
            - in_channels: Number of input channels
            - num_classes: Number of output classes
            - expand_pretrained: (Optional) Whether to expand from 3ch pretrained

    Returns:
        nn.Module: The segmentation model.
    """
    arch_name = config.get("name", "unet").lower()
    encoder = config.get("encoder", "resnet34")
    encoder_weights = config.get("encoder_weights", "imagenet")
    in_channels = config.get("in_channels", 3)
    num_classes = config.get("num_classes", 7)
    expand_pretrained = config.get("expand_pretrained", False)

    if arch_name not in ARCHITECTURES:
        raise ValueError(
            f"Unknown architecture '{arch_name}'. "
            f"Supported: {list(ARCHITECTURES.keys())}"
        )

    arch_class = ARCHITECTURES[arch_name]

    if expand_pretrained and in_channels != 3 and encoder_weights is not None:
        # Strategy: build with 3 channels + ImageNet weights, then expand
        print(f"Building {arch_name} with {encoder} (ImageNet) -> expanding 3 -> {in_channels} channels")

        model = arch_class(
            encoder_name=encoder,
            encoder_weights=encoder_weights,
            in_channels=3,
            classes=num_classes,
        )
        model = expand_first_conv(model, new_in_channels=in_channels)
    else:
        # Standard build — SMP handles channel count natively
        model = arch_class(
            encoder_name=encoder,
            encoder_weights=encoder_weights if in_channels == 3 else None,
            in_channels=in_channels,
            classes=num_classes,
        )

    # Log model info
    params = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Model: {arch_name} | Encoder: {encoder} | "
          f"Channels: {in_channels} -> Classes: {num_classes} | "
          f"Params: {params:,} ({trainable:,} trainable)")

    return model


def build_loss_function(loss_name: str, num_classes: int = 7, ignore_index: int = None, class_weights: torch.Tensor = None):
    """
    Build a loss function by name.

    Args:
        loss_name: One of 'cross_entropy', 'dice', 'dice_ce', 'focal', 'focal_dice', 'tversky_ce'.
        num_classes: Number of classes (for Dice/Focal loss).
        ignore_index: Optional class index to ignore in loss calculation.
        class_weights: Optional per-class loss weight tensor for handling imbalance.

    Returns:
        Loss function (nn.Module or callable).
    """
    import torch

    if loss_name == "cross_entropy":
        return nn.CrossEntropyLoss(
            weight=class_weights,
            ignore_index=ignore_index if ignore_index is not None else -100,
        )

    elif loss_name == "dice":
        return smp.losses.DiceLoss(mode="multiclass", ignore_index=ignore_index)

    elif loss_name == "dice_ce":
        # Combined loss — Dice handles class imbalance, CE provides stable gradients
        dice = smp.losses.DiceLoss(mode="multiclass", ignore_index=ignore_index)
        ce = nn.CrossEntropyLoss(
            weight=class_weights,
            ignore_index=ignore_index if ignore_index is not None else -100,
        )

        class DiceCELoss(nn.Module):
            def __init__(self):
                super().__init__()
                self.dice = dice
                self.ce = ce

            def forward(self, pred, target):
                return self.dice(pred, target) + self.ce(pred, target)

        return DiceCELoss()

    elif loss_name == "focal_dice":
        # Focal + Dice handles hard classes and class imbalance with highest stability
        dice = smp.losses.DiceLoss(mode="multiclass", ignore_index=ignore_index)
        focal = smp.losses.FocalLoss(mode="multiclass", ignore_index=ignore_index, gamma=2.0)
        ce = nn.CrossEntropyLoss(
            weight=class_weights,
            ignore_index=ignore_index if ignore_index is not None else -100,
        )

        class FocalDiceCELoss(nn.Module):
            def __init__(self):
                super().__init__()
                self.dice = dice
                self.focal = focal
                self.ce = ce

            def forward(self, pred, target):
                return self.dice(pred, target) + self.focal(pred, target) + 0.5 * self.ce(pred, target)

        return FocalDiceCELoss()

    elif loss_name == "tversky_ce":
        # Tversky (alpha=0.25, beta=0.75) penalizes False Negatives for minority classes (Rangeland/Water)
        tversky = smp.losses.TverskyLoss(
            mode="multiclass",
            ignore_index=ignore_index,
            alpha=0.25,
            beta=0.75,
        )
        ce = nn.CrossEntropyLoss(
            weight=class_weights,
            ignore_index=ignore_index if ignore_index is not None else -100,
        )

        class TverskyCELoss(nn.Module):
            def __init__(self):
                super().__init__()
                self.tversky = tversky
                self.ce = ce

            def forward(self, pred, target):
                return self.tversky(pred, target) + self.ce(pred, target)

        return TverskyCELoss()

    elif loss_name == "focal":
        return smp.losses.FocalLoss(mode="multiclass", ignore_index=ignore_index, gamma=2.0)

    else:
        raise ValueError(f"Unknown loss function: {loss_name}. "
                         f"Supported: cross_entropy, dice, dice_ce, focal, focal_dice, tversky_ce")
