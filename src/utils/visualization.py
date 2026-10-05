"""
Visualization utilities for predictions, masks, and spectral indices.

Provides side-by-side comparison of predictions vs ground truth,
mask overlays, colormap generation, and spectral index visualization.
"""

import os
import numpy as np
import torch
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import ListedColormap


# ─── Color Palettes ─────────────────────────────────────────────────────────────

# DeepGlobe 7-class palette (Phase 2)
DEEPGLOBE_PALETTE = np.array([
    [0, 255, 255],     # Urban (cyan)
    [255, 255, 0],     # Agriculture (yellow)
    [255, 0, 255],     # Rangeland (magenta)
    [0, 255, 0],       # Forest (green)
    [0, 0, 255],       # Water (blue)
    [255, 255, 255],   # Barren (white)
    [0, 0, 0],         # Unknown (black)
], dtype=np.uint8)

DEEPGLOBE_CLASSES = [
    "Urban", "Agriculture", "Rangeland",
    "Forest", "Water", "Barren", "Unknown",
]

# SEN12MS 11-class palette
SEN12MS_PALETTE = np.array([
    [0, 0, 0],         # Background
    [0, 255, 0],       # Forest
    [189, 183, 107],   # Shrubland
    [255, 215, 0],     # Savanna
    [210, 180, 140],   # Grassland
    [0, 191, 255],     # Wetlands
    [255, 165, 0],     # Croplands
    [128, 128, 128],   # Urban
    [255, 255, 255],   # Snow/Ice
    [169, 169, 169],   # Barren
    [0, 0, 255],       # Water
], dtype=np.uint8)

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


def create_colormap(num_classes: int, class_names: list = None):
    """
    Generate a categorical colormap for segmentation visualization.

    Args:
        num_classes: Number of classes.
        class_names: Optional class name list.

    Returns:
        Tuple of (colors_array, matplotlib ListedColormap).
    """
    if num_classes <= 7:
        colors = DEEPGLOBE_PALETTE[:num_classes]
        names = class_names or DEEPGLOBE_CLASSES[:num_classes]
    elif num_classes <= 11:
        colors = SEN12MS_PALETTE[:num_classes]
        names = class_names or SEN12MS_CLASSES[:num_classes]
    else:
        # Generate distinct colors using HSV
        hsv_colors = plt.cm.hsv(np.linspace(0, 0.9, num_classes))
        colors = (hsv_colors[:, :3] * 255).astype(np.uint8)
        names = class_names or [f"Class {i}" for i in range(num_classes)]

    cmap = ListedColormap(colors / 255.0)
    return colors, cmap, names


def mask_to_rgb(mask: np.ndarray, palette: np.ndarray) -> np.ndarray:
    """
    Convert a class-index mask to an RGB image using a color palette.

    Args:
        mask: Array of shape (H, W) with integer class indices.
        palette: Array of shape (num_classes, 3) with RGB values.

    Returns:
        RGB array of shape (H, W, 3).
    """
    h, w = mask.shape
    rgb = np.zeros((h, w, 3), dtype=np.uint8)
    for class_idx in range(len(palette)):
        rgb[mask == class_idx] = palette[class_idx]
    return rgb


def plot_prediction(
    image: np.ndarray,
    ground_truth: np.ndarray,
    prediction: np.ndarray,
    class_names: list = None,
    save_path: str = None,
    title: str = None,
):
    """
    Plot a side-by-side comparison: input image | ground truth | prediction.

    Args:
        image: Input image (H, W, 3) or (3, H, W), RGB, [0, 1].
        ground_truth: Ground truth mask (H, W) with class indices.
        prediction: Predicted mask (H, W) with class indices.
        class_names: Optional class name list.
        save_path: Optional file path to save the figure.
        title: Optional figure title.
    """
    if image.ndim == 3 and image.shape[0] <= 13:
        # CHW → HWC, take first 3 channels as RGB proxy
        image = image[:3].transpose(1, 2, 0)

    num_classes = max(ground_truth.max(), prediction.max()) + 1
    colors, cmap, names = create_colormap(num_classes, class_names)

    gt_rgb = mask_to_rgb(ground_truth, colors)
    pred_rgb = mask_to_rgb(prediction, colors)

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    axes[0].imshow(np.clip(image, 0, 1))
    axes[0].set_title("Input Image", fontsize=14)
    axes[0].axis("off")

    axes[1].imshow(gt_rgb)
    axes[1].set_title("Ground Truth", fontsize=14)
    axes[1].axis("off")

    axes[2].imshow(pred_rgb)
    axes[2].set_title("Prediction", fontsize=14)
    axes[2].axis("off")

    # Add legend
    patches = [mpatches.Patch(color=colors[i] / 255.0, label=names[i])
               for i in range(min(len(names), num_classes))]
    fig.legend(handles=patches, loc="lower center", ncol=min(7, len(patches)),
               fontsize=10, framealpha=0.9)

    if title:
        fig.suptitle(title, fontsize=16, fontweight="bold")

    plt.tight_layout()
    plt.subplots_adjust(bottom=0.12)

    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"Saved visualization: {save_path}")

    plt.close(fig)


def overlay_mask(
    image: np.ndarray,
    mask: np.ndarray,
    alpha: float = 0.5,
    palette: np.ndarray = None,
) -> np.ndarray:
    """
    Create a semi-transparent mask overlay on an image.

    Args:
        image: RGB image (H, W, 3), [0, 1] float.
        mask: Class index mask (H, W).
        alpha: Overlay transparency (0=image only, 1=mask only).
        palette: Color palette (num_classes, 3), uint8.

    Returns:
        Blended image (H, W, 3), [0, 1] float.
    """
    if palette is None:
        num_classes = mask.max() + 1
        palette, _, _ = create_colormap(num_classes)

    mask_rgb = mask_to_rgb(mask, palette).astype(np.float32) / 255.0
    blended = (1 - alpha) * image + alpha * mask_rgb
    return np.clip(blended, 0, 1)


def plot_spectral_indices(
    ndvi: np.ndarray,
    ndwi: np.ndarray,
    ndbi: np.ndarray,
    save_path: str = None,
):
    """
    Visualize NDVI, NDWI, NDBI index maps side by side.

    Args:
        ndvi: NDVI array (H, W), values in [-1, 1].
        ndwi: NDWI array (H, W), values in [-1, 1].
        ndbi: NDBI array (H, W), values in [-1, 1].
        save_path: Optional file path to save.
    """
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    im0 = axes[0].imshow(ndvi, cmap="RdYlGn", vmin=-1, vmax=1)
    axes[0].set_title("NDVI (Vegetation)", fontsize=14)
    axes[0].axis("off")
    plt.colorbar(im0, ax=axes[0], fraction=0.046)

    im1 = axes[1].imshow(ndwi, cmap="RdYlBu", vmin=-1, vmax=1)
    axes[1].set_title("NDWI (Water)", fontsize=14)
    axes[1].axis("off")
    plt.colorbar(im1, ax=axes[1], fraction=0.046)

    im2 = axes[2].imshow(ndbi, cmap="RdYlBu_r", vmin=-1, vmax=1)
    axes[2].set_title("NDBI (Built-up)", fontsize=14)
    axes[2].axis("off")
    plt.colorbar(im2, ax=axes[2], fraction=0.046)

    plt.tight_layout()

    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"Saved indices visualization: {save_path}")

    plt.close(fig)


def save_legend(class_names: list, colors: np.ndarray, save_path: str):
    """
    Save a standalone color legend image.

    Args:
        class_names: List of class names.
        colors: Array of shape (num_classes, 3), uint8.
        save_path: File path to save the legend.
    """
    fig, ax = plt.subplots(figsize=(4, len(class_names) * 0.4 + 0.5))
    ax.axis("off")

    patches = [mpatches.Patch(color=colors[i] / 255.0, label=class_names[i])
               for i in range(len(class_names))]
    ax.legend(handles=patches, loc="center", fontsize=12, framealpha=0.9)

    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
