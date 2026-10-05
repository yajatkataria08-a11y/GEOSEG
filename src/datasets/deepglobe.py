"""
DeepGlobe Land Cover Classification Dataset.

Expects the Kaggle download structure:
    data/deepglobe/
    ├── train/
    │   ├── 12345_sat.jpg    (satellite image)
    │   └── 12345_mask.png   (class-indexed mask)
    ├── valid/
    └── test/

Download from: https://www.kaggle.com/datasets/balraj98/deepglobe-land-cover-classification-dataset
"""

import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from pathlib import Path

try:
    import rasterio
except ImportError:
    rasterio = None

from PIL import Image


# DeepGlobe 7-class color mapping (RGB → class index)
# Used for converting color-coded masks to class indices
DEEPGLOBE_COLOR_MAP = {
    (0, 255, 255):   0,  # Urban land
    (255, 255, 0):   1,  # Agriculture land
    (255, 0, 255):   2,  # Rangeland
    (0, 255, 0):     3,  # Forest land
    (0, 0, 255):     4,  # Water
    (255, 255, 255): 5,  # Barren land
    (0, 0, 0):       6,  # Unknown
}

DEEPGLOBE_CLASSES = [
    "Urban",
    "Agriculture",
    "Rangeland",
    "Forest",
    "Water",
    "Barren",
    "Unknown",
]


def _rgb_mask_to_class_index(mask_rgb: np.ndarray) -> np.ndarray:
    """
    Convert an RGB-coded mask to class indices.

    Args:
        mask_rgb: RGB mask array of shape (H, W, 3).

    Returns:
        Class index array of shape (H, W) with values 0–6.
    """
    h, w, _ = mask_rgb.shape
    class_mask = np.full((h, w), 6, dtype=np.int64)  # Default to 'Unknown'

    for color, class_idx in DEEPGLOBE_COLOR_MAP.items():
        match = np.all(mask_rgb == np.array(color), axis=-1)
        class_mask[match] = class_idx

    return class_mask


class DeepGlobeDataset(Dataset):
    """
    DeepGlobe Land Cover Classification dataset.

    Reads paired satellite images and segmentation masks from the
    Kaggle download format.

    Args:
        root: Root directory containing train/valid/test subdirectories.
        split: One of 'train', 'valid', 'test'.
        tile_size: Crop size (512x512) for training and evaluation.
        is_train: Whether this is for training (random crop) or validation (center crop).
        ids: Optional explicit list of image IDs.
    """

    def __init__(
        self,
        root: str,
        split: str = "train",
        tile_size: int = 512,
        is_train: bool = True,
        ids: list = None,
    ):
        self.root = Path(root)
        self.split = split
        self.tile_size = tile_size
        self.is_train = is_train

        split_dir = self.root / split
        if not split_dir.exists():
            raise FileNotFoundError(
                f"Split directory not found: {split_dir}\n"
                f"Download the dataset from Kaggle and extract to {root}"
            )

        if ids is not None:
            self.ids = ids
        else:
            # Find all images that have a corresponding mask
            self.ids = sorted([
                p.stem.replace("_sat", "")
                for p in split_dir.glob("*_sat.jpg")
                if (split_dir / f"{p.stem.replace('_sat', '')}_mask.png").exists()
            ])

        if len(self.ids) == 0:
            raise FileNotFoundError(
                f"No matching *_sat.jpg and *_mask.png pairs found in {split_dir}."
            )

        print(f"DeepGlobe [{split}{' (train)' if is_train else ' (val)'}]: {len(self.ids)} images")

    def __len__(self) -> int:
        return len(self.ids)

    def __getitem__(self, idx: int):
        """
        Load a satellite image and its class-indexed mask.

        Returns:
            Tuple of (image_tensor[3, H, W], mask_tensor[H, W]).
        """
        img_id = self.ids[idx]
        img_path = self.root / self.split / f"{img_id}_sat.jpg"
        mask_path = self.root / self.split / f"{img_id}_mask.png"

        # Load image and mask
        img_pil = Image.open(img_path).convert("RGB")
        mask_pil = Image.open(mask_path).convert("RGB")
        ts = self.tile_size
        W, H = img_pil.size

        if self.is_train and np.random.rand() > 0.4 and W >= ts and H >= ts:
            # 60% chance: Native-resolution crop with Rangeland-targeted mining
            best_x, best_y = np.random.randint(0, W - ts + 1), np.random.randint(0, H - ts + 1)
            # Try a few candidate windows to prioritize rangeland/minority boundaries
            for _ in range(4):
                cand_x = np.random.randint(0, W - ts + 1)
                cand_y = np.random.randint(0, H - ts + 1)
                cand_mask = mask_pil.crop((cand_x, cand_y, cand_x + ts, cand_y + ts))
                m_arr = np.array(cand_mask)
                # Check if candidate contains Rangeland (magenta: R>200, G<100, B>200) or Water (B>200, R<100)
                is_rangeland = (m_arr[:, :, 0] > 200) & (m_arr[:, :, 1] < 100) & (m_arr[:, :, 2] > 200)
                if is_rangeland.sum() > 500:
                    best_x, best_y = cand_x, cand_y
                    break

            img_pil = img_pil.crop((best_x, best_y, best_x + ts, best_y + ts))
            mask_pil = mask_pil.crop((best_x, best_y, best_x + ts, best_y + ts))
        else:
            # Full-scene contextual resize
            img_pil = img_pil.resize((ts, ts), Image.BILINEAR)
            mask_pil = mask_pil.resize((ts, ts), Image.NEAREST)

        img = np.array(img_pil).astype(np.float32)
        mask_rgb = np.array(mask_pil)

        # Data Augmentations (Rotation, Flips & Color perturbation)
        if self.is_train:
            # Random horizontal flip
            if np.random.rand() > 0.5:
                img = np.fliplr(img)
                mask_rgb = np.fliplr(mask_rgb)
            # Random vertical flip
            if np.random.rand() > 0.5:
                img = np.flipud(img)
                mask_rgb = np.flipud(mask_rgb)
            # Random 90-degree rotations (0, 90, 180, 270)
            k = np.random.randint(0, 4)
            if k > 0:
                img = np.rot90(img, k)
                mask_rgb = np.rot90(mask_rgb, k)
            # Mild brightness/contrast jitter to prevent color-memorization
            if np.random.rand() > 0.5:
                contrast_factor = np.random.uniform(0.85, 1.15)
                brightness_delta = np.random.uniform(-15.0, 15.0)
                img = np.clip(img * contrast_factor + brightness_delta, 0.0, 255.0)

        # ImageNet normalization for pretrained ResNet-34 encoder
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        img_norm = (img / 255.0 - mean) / std
        img_norm = img_norm.transpose(2, 0, 1)  # HWC -> CHW

        # Convert RGB mask to class index (0-6)
        mask = _rgb_mask_to_class_index(mask_rgb)

        img_tensor = torch.from_numpy(np.ascontiguousarray(img_norm))
        mask_tensor = torch.from_numpy(np.ascontiguousarray(mask))

        return img_tensor, mask_tensor


def get_deepglobe_dataloaders(
    root: str = "data/deepglobe",
    batch_size: int = 8,
    num_workers: int = 0,
    tile_size: int = 512,
):
    """
    Create train and validation DataLoaders for DeepGlobe.

    Args:
        root: Path to DeepGlobe dataset root.
        batch_size: Batch size.
        num_workers: Number of DataLoader workers.
        tile_size: Tile crop size (default 512).

    Returns:
        Tuple of (train_loader, val_loader).
    """
    val_dir = Path(root) / "valid"
    has_valid_masks = any(val_dir.glob("*_mask.png")) if val_dir.exists() else False

    if has_valid_masks:
        train_ds = DeepGlobeDataset(root, split="train", tile_size=tile_size, is_train=True)
        val_ds = DeepGlobeDataset(root, split="valid", tile_size=tile_size, is_train=False)
    else:
        # Get all labeled image IDs from train/
        train_dir = Path(root) / "train"
        all_ids = sorted([
            p.stem.replace("_sat", "")
            for p in train_dir.glob("*_sat.jpg")
            if (train_dir / f"{p.stem.replace('_sat', '')}_mask.png").exists()
        ])

        # 80/20 train/val split with fixed random seed
        np.random.seed(42)
        shuffled = np.random.permutation(all_ids).tolist()
        split_idx = int(0.8 * len(shuffled))

        train_ids = shuffled[:split_idx]
        val_ids = shuffled[split_idx:]

        train_ds = DeepGlobeDataset(root, split="train", tile_size=tile_size, is_train=True, ids=train_ids)
        val_ds = DeepGlobeDataset(root, split="train", tile_size=tile_size, is_train=False, ids=val_ids)

    train_loader = DataLoader(
        train_ds,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available(),
        drop_last=True,
    )
    val_loader = DataLoader(
        val_ds,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available(),
    )

    return train_loader, val_loader
