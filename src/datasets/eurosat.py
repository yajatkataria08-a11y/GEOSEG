"""
EuroSAT dataset wrapper.

Wraps torchgeo's EuroSAT dataset with proper transforms, normalization,
and train/val DataLoader construction.

EuroSAT: 27,000 labeled Sentinel-2 image patches (64×64, 13 bands, 10 classes).
"""

import torch
from torch.utils.data import DataLoader
from torchgeo.datasets import EuroSAT

from src.transforms.augmentations import get_train_augmentations, get_val_augmentations


# EuroSAT class names for reference
EUROSAT_CLASSES = [
    "AnnualCrop",
    "Forest",
    "HerbaceousVegetation",
    "Highway",
    "Industrial",
    "Pasture",
    "PermanentCrop",
    "Residential",
    "River",
    "SeaLake",
]


def get_eurosat_dataloaders(
    root: str = "data/eurosat",
    download: bool = True,
    batch_size: int = 64,
    num_workers: int = 0,
    num_channels: int = 13,
    scale: float = 10000.0,
):
    """
    Create train and validation DataLoaders for EuroSAT.

    Args:
        root: Path to dataset root directory.
        download: Whether to download the dataset if not present.
        batch_size: Batch size for both loaders.
        num_workers: Number of dataloader workers (0 recommended on Windows).
        num_channels: Number of spectral bands (13 for full Sentinel-2).
        scale: Reflectance scale factor for normalization.

    Returns:
        Tuple of (train_loader, val_loader).
    """
    train_transforms = get_train_augmentations(num_channels=num_channels, scale=scale)
    val_transforms = get_val_augmentations(num_channels=num_channels, scale=scale)

    train_ds = EuroSAT(
        root=root,
        split="train",
        download=download,
        transforms=train_transforms,
    )
    val_ds = EuroSAT(
        root=root,
        split="val",
        download=download,
        transforms=val_transforms,
    )

    train_loader = DataLoader(
        train_ds,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=False,
        drop_last=True,
    )
    val_loader = DataLoader(
        val_ds,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=False,
    )

    return train_loader, val_loader
