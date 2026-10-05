"""
Spectral index computation — NDVI, NDWI, NDBI.

These normalized difference indices are computed from Sentinel-2 bands
and can be used as extra input channels to improve segmentation.

IMPORTANT: Band order must be explicitly specified to prevent silent
mismatches — the #1 bug in multispectral pipelines.
"""

import numpy as np
import torch


# Default Sentinel-2 L2A band order (13 bands, as delivered by most pipelines)
# B01 (Coastal) is often excluded because its 60m resolution doesn't match the others
DEFAULT_BAND_ORDER = (
    "B01",   # Coastal   (60m)
    "B02",   # Blue      (10m)
    "B03",   # Green     (10m)
    "B04",   # Red       (10m)
    "B05",   # Red Edge 1 (20m)
    "B06",   # Red Edge 2 (20m)
    "B07",   # Red Edge 3 (20m)
    "B08",   # NIR       (10m)
    "B8A",   # Narrow NIR (20m)
    "B09",   # Water Vap  (60m)
    "B10",   # Cirrus    (60m, often dropped)
    "B11",   # SWIR 1    (20m)
    "B12",   # SWIR 2    (20m)
)

# Index names for reference
INDEX_NAMES = ["NDVI", "NDWI", "NDBI"]


def compute_indices(
    bands: np.ndarray,
    band_order: tuple = DEFAULT_BAND_ORDER,
    eps: float = 1e-6,
) -> np.ndarray:
    """
    Compute spectral indices from Sentinel-2 bands.

    Indices:
        NDVI = (NIR - Red) / (NIR + Red + ε)     → vegetation vigor
        NDWI = (Green - NIR) / (Green + NIR + ε)  → water bodies
        NDBI = (SWIR1 - NIR) / (SWIR1 + NIR + ε)  → built-up areas

    Args:
        bands: Array of shape (C, H, W), reflectance scaled to ~[0, 1].
        band_order: Tuple of band names matching the channel dimension.
        eps: Small value to avoid division by zero.

    Returns:
        Array of shape (3, H, W) containing [NDVI, NDWI, NDBI].
    """
    idx = {name: i for i, name in enumerate(band_order)}

    # Validate required bands exist
    required = {"B03", "B04", "B08", "B11"}
    missing = required - set(band_order)
    if missing:
        raise ValueError(
            f"Missing required bands for index computation: {missing}. "
            f"Available bands: {list(band_order)}"
        )

    red = bands[idx["B04"]]      # Red
    green = bands[idx["B03"]]    # Green
    nir = bands[idx["B08"]]      # Near Infrared
    swir1 = bands[idx["B11"]]    # Short-Wave Infrared 1

    # Normalized Difference Vegetation Index
    ndvi = (nir - red) / (nir + red + eps)

    # Normalized Difference Water Index
    ndwi = (green - nir) / (green + nir + eps)

    # Normalized Difference Built-up Index
    ndbi = (swir1 - nir) / (swir1 + nir + eps)

    return np.stack([ndvi, ndwi, ndbi], axis=0).astype(np.float32)


def compute_indices_torch(
    bands: torch.Tensor,
    band_order: tuple = DEFAULT_BAND_ORDER,
    eps: float = 1e-6,
) -> torch.Tensor:
    """
    Compute spectral indices from Sentinel-2 bands (PyTorch version).

    Same as compute_indices but operates on torch tensors for GPU compatibility.

    Args:
        bands: Tensor of shape (B, C, H, W) or (C, H, W).
        band_order: Tuple of band names matching the channel dimension.
        eps: Small value to avoid division by zero.

    Returns:
        Tensor of shape (B, 3, H, W) or (3, H, W) containing [NDVI, NDWI, NDBI].
    """
    idx = {name: i for i, name in enumerate(band_order)}

    has_batch = bands.dim() == 4
    if not has_batch:
        bands = bands.unsqueeze(0)

    red = bands[:, idx["B04"]]
    green = bands[:, idx["B03"]]
    nir = bands[:, idx["B08"]]
    swir1 = bands[:, idx["B11"]]

    ndvi = (nir - red) / (nir + red + eps)
    ndwi = (green - nir) / (green + nir + eps)
    ndbi = (swir1 - nir) / (swir1 + nir + eps)

    indices = torch.stack([ndvi, ndwi, ndbi], dim=1)

    if not has_batch:
        indices = indices.squeeze(0)

    return indices


def build_multispectral_input(
    bands: np.ndarray,
    band_order: tuple = DEFAULT_BAND_ORDER,
) -> np.ndarray:
    """
    Build a full multispectral input by concatenating raw bands + spectral indices.

    Example: 13 raw Sentinel-2 bands + 3 indices = 16-channel input.

    Args:
        bands: Array of shape (C, H, W), reflectance scaled to ~[0, 1].
        band_order: Tuple of band names matching the channel dimension.

    Returns:
        Array of shape (C+3, H, W) with indices appended.
    """
    indices = compute_indices(bands, band_order)
    return np.concatenate([bands, indices], axis=0)


def build_multispectral_input_torch(
    bands: torch.Tensor,
    band_order: tuple = DEFAULT_BAND_ORDER,
) -> torch.Tensor:
    """
    Build a full multispectral input (PyTorch version).

    Args:
        bands: Tensor of shape (B, C, H, W) or (C, H, W).
        band_order: Tuple of band names matching the channel dimension.

    Returns:
        Tensor of shape (B, C+3, H, W) or (C+3, H, W) with indices appended.
    """
    indices = compute_indices_torch(bands, band_order)
    dim = 1 if bands.dim() == 4 else 0
    return torch.cat([bands, indices], dim=dim)
