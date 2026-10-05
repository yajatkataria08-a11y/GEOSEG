"""
Data augmentations for satellite imagery.

Uses kornia and torch.nn for robust batch and dictionary augmentations.
"""

import torch
import torch.nn as nn
import kornia.augmentation as K


class SampleTransform(nn.Module):
    """
    Transforms dictionary samples from TorchGeo datasets (e.g. EuroSAT, SEN12MS).
    Applies spatial augmentation on training split and Sentinel-2 reflectance scaling.
    
    WARNING: This class only augments images, not masks. Do NOT use for segmentation 
    datasets where masks need spatial augmentations.
    """

    def __init__(self, num_channels: int = 13, is_train: bool = True, scale: float = 10000.0):
        super().__init__()
        self.num_channels = num_channels
        self.is_train = is_train
        self.scale = scale

        if is_train:
            self.aug = nn.Sequential(
                K.RandomHorizontalFlip(p=0.5),
                K.RandomVerticalFlip(p=0.5),
                K.RandomRotation(degrees=90.0, p=0.3),
            )
        else:
            self.aug = nn.Identity()

    def forward(self, sample):
        if isinstance(sample, dict):
            # TorchGeo sample dictionary
            img = sample["image"].float() / self.scale
            if self.is_train:
                if img.dim() == 3:
                    # (C, H, W) -> (1, C, H, W)
                    img = self.aug(img.unsqueeze(0)).squeeze(0)
                else:
                    img = self.aug(img)
            sample["image"] = img
            return sample
        elif isinstance(sample, torch.Tensor):
            img = sample.float() / self.scale
            if self.is_train:
                if img.dim() == 3:
                    img = self.aug(img.unsqueeze(0)).squeeze(0)
                else:
                    img = self.aug(img)
            return img
        return sample


def get_train_augmentations(num_channels: int = 13, include_normalize: bool = True, scale: float = 10000.0):
    """Build training augmentations for satellite datasets."""
    return SampleTransform(num_channels=num_channels, is_train=True, scale=scale)


def get_val_augmentations(num_channels: int = 13, scale: float = 10000.0):
    """Build validation transforms (normalize only, no spatial augmentation)."""
    return SampleTransform(num_channels=num_channels, is_train=False, scale=scale)
