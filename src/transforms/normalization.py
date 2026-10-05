"""
Sentinel-2 normalization utilities.

Sentinel-2 L2A reflectance values are typically 0–10000.
This module centralizes the normalization logic so train and inference
use the same scale — the #1 source of silent bugs in multispectral pipelines.
"""

import torch
import torch.nn as nn
import numpy as np


# Default Sentinel-2 L2A reflectance scale factor
S2_REFLECTANCE_SCALE = 10000.0


def sentinel2_normalize(tensor: torch.Tensor, scale: float = S2_REFLECTANCE_SCALE) -> torch.Tensor:
    """
    Normalize a Sentinel-2 reflectance tensor by dividing by the scale factor.

    Args:
        tensor: Input tensor with raw reflectance values.
        scale: Reflectance scale factor (default 10000 for L2A).

    Returns:
        Normalized tensor in approximately [0, 1] range.
    """
    return tensor.float() / scale


def sentinel2_normalize_numpy(array: np.ndarray, scale: float = S2_REFLECTANCE_SCALE) -> np.ndarray:
    """
    Normalize a Sentinel-2 reflectance numpy array.

    Args:
        array: Input array with raw reflectance values.
        scale: Reflectance scale factor.

    Returns:
        Normalized array in approximately [0, 1] range.
    """
    return array.astype(np.float32) / scale


# NOTE: Legacy utility, kept for reference
def get_normalization_transform(num_channels: int, scale: float = S2_REFLECTANCE_SCALE):
    """
    Create a kornia-compatible normalization transform for Sentinel-2 data.

    Uses mean=0 and std=scale for each channel, which is equivalent to dividing
    by the scale factor. This integrates cleanly with AugmentationSequential.

    Args:
        num_channels: Number of spectral bands.
        scale: Reflectance scale factor.

    Returns:
        kornia.augmentation.Normalize transform.
    """
    import kornia.augmentation as K

    return K.Normalize(
        mean=torch.zeros(num_channels),
        std=torch.full((num_channels,), scale),
    )


class NormalizeModule(nn.Module):
    """
    A simple nn.Module wrapper for reflectance normalization.

    Useful when you want normalization as part of a Sequential pipeline
    rather than a kornia augmentation.
    """

    def __init__(self, scale: float = S2_REFLECTANCE_SCALE):
        super().__init__()
        self.scale = scale

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x.float() / self.scale

    def __repr__(self) -> str:
        return f"NormalizeModule(scale={self.scale})"
