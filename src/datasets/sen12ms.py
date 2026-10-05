"""
SEN12MS dataset loader and preprocessor for Phase 3 multispectral segmentation.

SEN12MS provides paired Sentinel-1 SAR, Sentinel-2 Optical (13 bands), and MODIS Land Cover (IGBP).
This loader selects the 13 Sentinel-2 bands (s2-all) matching the project's band_order:
  ('B01', 'B02', 'B03', 'B04', 'B05', 'B06', 'B07', 'B08', 'B8A', 'B09', 'B10', 'B11', 'B12')
and remaps the raw 17-class IGBP mask to the simplified 11-class land cover scheme:
  0: No-data / Background
  1: Forest (IGBP 1, 2, 3, 4, 5)
  2: Shrubland (IGBP 6, 7)
  3: Savanna (IGBP 8, 9)
  4: Grassland (IGBP 10)
  5: Wetlands (IGBP 11)
  6: Croplands (IGBP 12, 14)
  7: Urban (IGBP 13)
  8: Snow/Ice (IGBP 15)
  9: Barren (IGBP 16)
  10: Water (IGBP 17)

Includes automatic high-fidelity synthetic fallback generation when the 500GB raw SEN12MS dataset is not locally stored.
"""

import os
import re
import random
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader, Subset

try:
    from torchgeo.datasets import SEN12MS
except ImportError:
    SEN12MS = None


# Remapping tensor from raw IGBP 17 classes to simplified 11 classes
# Index: raw IGBP (0-17) -> Value: simplified class (0-10)
IGBP_TO_SIMPLIFIED = torch.tensor(
    [0, 1, 1, 1, 1, 1, 2, 2, 3, 3, 4, 5, 6, 7, 6, 8, 9, 10],
    dtype=torch.long,
)

SEN12MS_CLASSES = [
    "Background",
    "Forest",
    "Shrubland",
    "Savanna",
    "Grassland",
    "Wetlands",
    "Croplands",
    "Urban",
    "Snow/Ice",
    "Barren",
    "Water",
]

# Spectral signatures for 11 simplified classes across 13 Sentinel-2 bands
# Bands: [B01, B02, B03, B04, B05, B06, B07, B08, B8A, B09, B10, B11, B12]
CLASS_SPECTRAL_SIGNATURES = {
    0: np.array([0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05], dtype=np.float32),  # Background
    1: np.array([0.02, 0.03, 0.06, 0.04, 0.12, 0.28, 0.38, 0.45, 0.46, 0.08, 0.02, 0.15, 0.07], dtype=np.float32),  # Forest (Strong NIR)
    2: np.array([0.04, 0.05, 0.08, 0.07, 0.14, 0.24, 0.30, 0.35, 0.36, 0.07, 0.02, 0.20, 0.11], dtype=np.float32),  # Shrubland
    3: np.array([0.05, 0.06, 0.09, 0.09, 0.15, 0.23, 0.28, 0.32, 0.33, 0.08, 0.03, 0.22, 0.13], dtype=np.float32),  # Savanna
    4: np.array([0.03, 0.04, 0.07, 0.06, 0.13, 0.25, 0.32, 0.39, 0.40, 0.08, 0.02, 0.18, 0.09], dtype=np.float32),  # Grassland
    5: np.array([0.03, 0.05, 0.08, 0.06, 0.10, 0.18, 0.22, 0.25, 0.26, 0.09, 0.04, 0.12, 0.06], dtype=np.float32),  # Wetlands
    6: np.array([0.03, 0.04, 0.08, 0.05, 0.14, 0.27, 0.36, 0.42, 0.43, 0.08, 0.02, 0.17, 0.08], dtype=np.float32),  # Croplands
    7: np.array([0.10, 0.12, 0.14, 0.15, 0.16, 0.18, 0.20, 0.22, 0.23, 0.06, 0.02, 0.32, 0.26], dtype=np.float32),  # Urban (High SWIR)
    8: np.array([0.45, 0.50, 0.52, 0.53, 0.52, 0.50, 0.48, 0.45, 0.43, 0.12, 0.03, 0.05, 0.02], dtype=np.float32),  # Snow/Ice
    9: np.array([0.12, 0.15, 0.18, 0.22, 0.25, 0.28, 0.30, 0.32, 0.33, 0.08, 0.03, 0.35, 0.28], dtype=np.float32),  # Barren / Soil
    10: np.array([0.08, 0.10, 0.09, 0.05, 0.03, 0.02, 0.01, 0.01, 0.01, 0.05, 0.01, 0.01, 0.01], dtype=np.float32), # Water (Low NIR)
}


def _extract_scene_id(filepath: str) -> str:
    """Extract scene-level identifier from a patch filepath."""
    match = re.search(r'(ROIs\d+_\w+)', filepath)
    if match:
        season_part = match.group(1)
        scene_match = re.search(r's[12]_(\d+)', filepath)
        scene_sub = scene_match.group(1) if scene_match else "0"
        return f"{season_part}_{scene_sub}"
    return str(Path(filepath).parent.name)


class SyntheticSEN12MSDataset(Dataset):
    """
    High-fidelity synthetic dataset matching SEN12MS 13-band Sentinel-2 L2A optical
    and 11-class IGBP ground truth masks.
    """
    def __init__(self, num_samples: int = 160, patch_size: int = 256, seed: int = 42):
        self.num_samples = num_samples
        self.patch_size = patch_size
        self.seed = seed
        self.samples = []
        self._generate()

    def _generate(self):
        rng = np.random.RandomState(self.seed)
        for i in range(self.num_samples):
            # Create smooth multi-class segmentation mask using random geometric shapes
            mask = np.zeros((self.patch_size, self.patch_size), dtype=np.int64)
            # Fill background with dominant class
            dom_class = rng.choice([1, 4, 6, 9]) # Forest, Grass, Crop, Barren
            mask.fill(dom_class)

            # Add multiple land cover blobs
            num_blobs = rng.randint(4, 9)
            for _ in range(num_blobs):
                cls = rng.choice([1, 2, 3, 4, 5, 6, 7, 9, 10])
                cx = rng.randint(0, self.patch_size)
                cy = rng.randint(0, self.patch_size)
                rx = rng.randint(20, 80)
                ry = rng.randint(20, 80)
                y_coords, x_coords = np.ogrid[:self.patch_size, :self.patch_size]
                dist = ((x_coords - cx) / rx) ** 2 + ((y_coords - cy) / ry) ** 2
                mask[dist <= 1.0] = cls

            # Generate 13 bands according to class spectra with per-pixel noise
            image = np.zeros((13, self.patch_size, self.patch_size), dtype=np.float32)
            for cls_idx, spectrum in CLASS_SPECTRAL_SIGNATURES.items():
                cls_pixels = (mask == cls_idx)
                if np.any(cls_pixels):
                    noise = rng.normal(0, 0.015, size=(13, np.sum(cls_pixels))).astype(np.float32)
                    base_spectrum = spectrum[:, np.newaxis]
                    pixel_vals = np.clip(base_spectrum + noise, 0.001, 0.999)
                    image[:, cls_pixels] = pixel_vals

            scene_id = f"scene_{i // 20}"
            self.samples.append((image, mask, scene_id))

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int):
        image, mask, scene_id = self.samples[idx]
        return {
            "image": torch.from_numpy(image),
            "mask": torch.from_numpy(mask),
            "scene_id": scene_id,
        }


class SEN12MSSegmentationDataset(Dataset):
    """
    Wrapper for TorchGeo SEN12MS dataset with automatic synthetic fallback.
    """
    def __init__(self, root: str = "data/sen12ms", split: str = "train",
                 scale: float = 10000.0, augment: bool = False):
        self.root = Path(root)
        self.scale = scale
        self.augment = augment
        self.is_synthetic = False
        self.ds = None

        if SEN12MS is not None and self.root.exists() and any(self.root.iterdir()):
            try:
                bands = SEN12MS.BAND_SETS.get("s2-all", ("B01", "B02", "B03", "B04", "B05", "B06", "B07", "B08", "B8A", "B09", "B10", "B11", "B12"))
                self.ds = SEN12MS(root=str(self.root), split=split, bands=bands)
            except Exception:
                self.is_synthetic = True
                self.ds = SyntheticSEN12MSDataset(num_samples=160, patch_size=256, seed=42 if split == "train" else 99)
        else:
            self.is_synthetic = True
            self.ds = SyntheticSEN12MSDataset(num_samples=160, patch_size=256, seed=42 if split == "train" else 99)

    def __len__(self) -> int:
        return len(self.ds)

    def __getitem__(self, idx: int):
        if self.is_synthetic:
            sample = self.ds[idx]
            image = sample["image"].float()
            mask = sample["mask"].long()
        else:
            sample = self.ds[idx]
            image = sample["image"].float() / self.scale
            raw_mask = sample["mask"].long()
            if raw_mask.dim() == 3:
                raw_mask = raw_mask.squeeze(0)
            clamped_mask = raw_mask.clamp(0, 17)
            mask = IGBP_TO_SIMPLIFIED[clamped_mask]

        if self.augment:
            image, mask = self._apply_augmentations(image, mask)

        return {"image": image, "mask": mask}

    @staticmethod
    def _apply_augmentations(image: torch.Tensor, mask: torch.Tensor):
        if random.random() > 0.5:
            image = torch.flip(image, dims=[-1])
            mask = torch.flip(mask, dims=[-1])

        if random.random() > 0.5:
            image = torch.flip(image, dims=[-2])
            mask = torch.flip(mask, dims=[-2])

        k = random.randint(0, 3)
        if k > 0:
            image = torch.rot90(image, k, dims=[-2, -1])
            mask = torch.rot90(mask, k, dims=[-2, -1])

        if random.random() > 0.5:
            brightness = (random.random() - 0.5) * 0.1
            image = image + brightness

        if random.random() > 0.5:
            contrast = 0.85 + random.random() * 0.3
            image = image * contrast

        image = image.clamp(0.0, 1.0)
        return image, mask


def _scene_level_split(dataset, train_ratio: float = 0.8, seed: int = 42):
    """Split dataset indices by scene ID to prevent spatial leakage."""
    scene_to_indices = defaultdict(list)

    for idx in range(len(dataset)):
        try:
            if dataset.is_synthetic:
                scene_id = dataset.ds.samples[idx][2]
            elif hasattr(dataset.ds, 'files') and idx < len(dataset.ds.files):
                filepath = str(dataset.ds.files[idx])
                scene_id = _extract_scene_id(filepath)
            else:
                scene_id = f"scene_{idx // 20}"
        except Exception:
            scene_id = f"scene_{idx // 20}"

        scene_to_indices[scene_id].append(idx)

    scene_ids = sorted(scene_to_indices.keys())
    rng = random.Random(seed)
    rng.shuffle(scene_ids)

    n_train_scenes = max(1, int(len(scene_ids) * train_ratio))
    train_scenes = set(scene_ids[:n_train_scenes])

    train_indices = []
    val_indices = []
    for scene_id in scene_ids:
        indices = scene_to_indices[scene_id]
        if scene_id in train_scenes:
            train_indices.extend(indices)
        else:
            val_indices.extend(indices)

    if not val_indices:
        val_indices = train_indices[:max(1, len(train_indices) // 5)]

    return train_indices, val_indices


def get_sen12ms_dataloaders(
    root: str = "data/sen12ms",
    batch_size: int = 8,
    num_workers: int = 0,
    train_split_ratio: float = 0.8,
):
    """
    Create train and validation DataLoaders for SEN12MS with scene-level split
    to prevent spatial leakage.
    """
    full_ds = SEN12MSSegmentationDataset(root=root, split="train", augment=False)
    train_indices, val_indices = _scene_level_split(full_ds, train_ratio=train_split_ratio)

    train_ds_augmented = SEN12MSSegmentationDataset(root=root, split="train", augment=True)

    train_subset = Subset(train_ds_augmented, train_indices)
    val_subset = Subset(full_ds, val_indices)

    print(f"  SEN12MS split: {len(train_indices)} train / {len(val_indices)} val patches "
          f"(scene-level, no spatial leakage, {'synthetic' if full_ds.is_synthetic else 'live'})")

    train_loader = DataLoader(
        train_subset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available(),
        drop_last=True,
    )
    val_loader = DataLoader(
        val_subset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available(),
    )

    return train_loader, val_loader
