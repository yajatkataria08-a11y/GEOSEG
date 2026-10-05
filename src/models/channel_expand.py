"""
Pretrained encoder channel expansion — 3ch RGB → N-ch multispectral.

When going from 3-channel (ImageNet pretrained) to 13+ channels (Sentinel-2),
we don't want to throw away pretrained features. Instead, we replicate the
averaged RGB filter weights across the new channels and rescale to maintain
roughly the same activation magnitude.
"""

import torch
import torch.nn as nn


def expand_first_conv(model: nn.Module, new_in_channels: int = 13) -> nn.Module:
    """
    Expand the first convolutional layer of a pretrained encoder from 3 to N channels.

    Strategy:
        1. Average the 3 pretrained RGB filter weights → single-channel filter
        2. Tile this average filter across all new_in_channels
        3. Rescale by 3/new_in_channels to keep activation magnitudes stable

    This works because the average RGB filter captures a reasonable "generic"
    spatial feature detector, and the model will learn band-specific adjustments
    during fine-tuning.

    Args:
        model: A segmentation model (SMP) with a pretrained encoder.
        new_in_channels: Target number of input channels (e.g., 13 for S2, 16 for S2+indices).

    Returns:
        The model with its first conv layer expanded.
    """
    # Find the first conv layer — handle different encoder architectures
    old_conv = _find_first_conv(model)

    if old_conv is None:
        raise ValueError(
            "Could not find the first Conv2d layer in the encoder. "
            "This utility supports ResNet, EfficientNet, and similar architectures."
        )

    if old_conv.in_channels == new_in_channels:
        print(f"First conv already has {new_in_channels} channels, skipping expansion.")
        return model

    if old_conv.in_channels != 3:
        raise ValueError(
            f"Expected first conv to have 3 input channels (RGB), "
            f"but found {old_conv.in_channels}. Cannot expand."
        )

    # Build new conv with same spatial params but different input channels
    new_conv = nn.Conv2d(
        in_channels=new_in_channels,
        out_channels=old_conv.out_channels,
        kernel_size=old_conv.kernel_size,
        stride=old_conv.stride,
        padding=old_conv.padding,
        dilation=old_conv.dilation,
        groups=old_conv.groups,
        bias=old_conv.bias is not None,
        padding_mode=old_conv.padding_mode,
    )

    with torch.no_grad():
        # Average the 3 RGB filters → (out_channels, 1, kH, kW)
        mean_weight = old_conv.weight.mean(dim=1, keepdim=True)

        # Tile across all new input channels → (out_channels, new_in_channels, kH, kW)
        new_conv.weight[:] = mean_weight.repeat(1, new_in_channels, 1, 1)

        # Rescale to maintain activation magnitude
        # Original: 3 channels × weight → activation
        # New: N channels × (weight × 3/N) → same activation magnitude
        new_conv.weight *= 3.0 / new_in_channels

        # Copy bias if it exists
        if old_conv.bias is not None:
            new_conv.bias[:] = old_conv.bias

    # Replace the old conv with the new one
    _replace_first_conv(model, new_conv)

    print(f"Expanded first conv: 3 -> {new_in_channels} channels "
          f"(weights rescaled by {3.0/new_in_channels:.4f})")

    return model


def _find_first_conv(model: nn.Module) -> nn.Conv2d:
    """
    Find the first Conv2d layer in the encoder.

    Handles multiple encoder architectures:
    - ResNet: encoder.conv1
    - EfficientNet: encoder._conv_stem or encoder.features[0][0]
    - Generic: first Conv2d found via recursive search
    """
    encoder = getattr(model, "encoder", model)

    # ResNet-style: encoder.conv1
    if hasattr(encoder, "conv1") and isinstance(encoder.conv1, nn.Conv2d):
        return encoder.conv1

    # EfficientNet-style: encoder._conv_stem
    if hasattr(encoder, "_conv_stem") and isinstance(encoder._conv_stem, nn.Conv2d):
        return encoder._conv_stem

    # Generic fallback: find first Conv2d in the model tree
    for module in encoder.modules():
        if isinstance(module, nn.Conv2d):
            return module

    return None


def _replace_first_conv(model: nn.Module, new_conv: nn.Conv2d):
    """
    Replace the first Conv2d layer in the encoder with a new one.

    Mirrors the detection logic in _find_first_conv.
    """
    encoder = getattr(model, "encoder", model)

    if hasattr(encoder, "conv1") and isinstance(encoder.conv1, nn.Conv2d):
        encoder.conv1 = new_conv
        return

    if hasattr(encoder, "_conv_stem") and isinstance(encoder._conv_stem, nn.Conv2d):
        encoder._conv_stem = new_conv
        return

    # Generic fallback — replace first Conv2d found
    for name, module in encoder.named_modules():
        if isinstance(module, nn.Conv2d):
            # Navigate to the parent and replace the attribute
            parts = name.split(".")
            parent = encoder
            for part in parts[:-1]:
                parent = parent[int(part)] if part.isdigit() else getattr(parent, part)
            setattr(parent, parts[-1], new_conv)
            return

    raise ValueError("Could not replace the first Conv2d layer.")
