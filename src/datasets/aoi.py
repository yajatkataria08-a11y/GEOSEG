"""
AOI Tile Dataset — Sliding-window tile reader for large GeoTIFFs.

Used during inference (Phase 4) to tile large satellite images into
model-sized patches, with configurable overlap for better edge quality.
"""

import numpy as np
import torch
from torch.utils.data import Dataset

try:
    import rasterio
    from rasterio.windows import Window
except ImportError:
    raise ImportError("rasterio is required for AOI inference. Install via: conda install -c conda-forge rasterio")


class AOITileDataset(Dataset):
    """
    Sliding-window tile dataset for large GeoTIFF files.

    Reads a large raster and yields overlapping tiles for batched inference.
    Each tile includes metadata needed for stitching predictions back together.

    Args:
        tif_path: Path to the input GeoTIFF.
        tile_size: Size of each square tile (pixels).
        overlap: Overlap between adjacent tiles (pixels).
        normalize_scale: Reflectance scale factor (divide raw values by this).
        transform: Optional callable applied to each tile tensor.
    """

    def __init__(
        self,
        tif_path: str,
        tile_size: int = 512,
        overlap: int = 32,
        normalize_scale: float = 10000.0,
        transform=None,
    ):
        self.tif_path = tif_path
        self.tile_size = tile_size
        self.overlap = overlap
        self.normalize_scale = normalize_scale
        self.transform = transform
        self.stride = tile_size - overlap

        # Read raster metadata without loading all data
        with rasterio.open(tif_path) as src:
            self.height = src.height
            self.width = src.width
            self.num_bands = src.count
            self.profile = src.profile.copy()
            self.crs = src.crs
            self.raster_transform = src.transform

        # Precompute tile grid
        self.tiles = []
        for y in range(0, self.height, self.stride):
            for x in range(0, self.width, self.stride):
                tile_h = min(self.tile_size, self.height - y)
                tile_w = min(self.tile_size, self.width - x)
                self.tiles.append({
                    "x": x,
                    "y": y,
                    "width": tile_w,
                    "height": tile_h,
                })

        print(f"AOITileDataset: {tif_path}")
        print(f"  Raster: {self.width}×{self.height} ({self.num_bands} bands)")
        print(f"  Tiles: {len(self.tiles)} ({tile_size}×{tile_size}, overlap={overlap})")

    def __len__(self) -> int:
        return len(self.tiles)

    def __getitem__(self, idx: int):
        """
        Read and return a single tile.

        Returns:
            Tuple of:
                - tile_tensor: (C, tile_size, tile_size) float tensor, zero-padded if edge tile
                - tile_meta: dict with x, y, width, height for stitching
        """
        meta = self.tiles[idx]
        window = Window(meta["x"], meta["y"], meta["width"], meta["height"])

        with rasterio.open(self.tif_path) as src:
            tile = src.read(window=window).astype(np.float32)

        # Normalize reflectance
        tile = tile / self.normalize_scale

        # Zero-pad if edge tile is smaller than tile_size
        if tile.shape[1] < self.tile_size or tile.shape[2] < self.tile_size:
            padded = np.zeros(
                (tile.shape[0], self.tile_size, self.tile_size),
                dtype=np.float32,
            )
            padded[:, :tile.shape[1], :tile.shape[2]] = tile
            tile = padded

        tile_tensor = torch.from_numpy(tile)

        if self.transform is not None:
            tile_tensor = self.transform(tile_tensor)

        return tile_tensor, meta

    def get_profile(self) -> dict:
        """Get rasterio profile for writing output GeoTIFF."""
        return self.profile
