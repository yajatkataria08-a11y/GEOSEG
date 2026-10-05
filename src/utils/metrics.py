"""
Metrics trackers for classification and segmentation.

Wraps torchmetrics for a clean .update() / .compute() / .reset() interface.
Always track per-class IoU for segmentation — mean IoU alone hides classes
that are being silently ignored due to class imbalance.
"""

import torch
from torchmetrics import JaccardIndex, Accuracy


class AccuracyTracker:
    """
    Running accuracy tracker for classification tasks (Phase 1).

    Tracks correct/total counts across batches within an epoch,
    then resets for the next epoch.
    """

    def __init__(self):
        self.correct = 0
        self.total = 0

    def update(self, preds: torch.Tensor, targets: torch.Tensor):
        """
        Update with a batch of predictions and targets.

        Args:
            preds: Model output logits of shape (B, C) or class indices (B,).
            targets: Ground truth class indices of shape (B,).
        """
        if preds.dim() > 1:
            preds = preds.argmax(dim=1)
        self.correct += (preds == targets).sum().item()
        self.total += targets.size(0)

    def compute(self) -> float:
        """Compute accuracy over all accumulated batches."""
        if self.total == 0:
            return 0.0
        return self.correct / self.total

    def reset(self):
        """Reset counters for a new epoch."""
        self.correct = 0
        self.total = 0


class IoUTracker:
    """
    Mean IoU tracker for segmentation tasks (Phase 2+).

    Wraps torchmetrics.JaccardIndex and provides both mean and per-class IoU.
    Per-class IoU is essential for catching classes silently ignored by the model
    due to class imbalance.

    Args:
        num_classes: Number of segmentation classes.
        device: Device to run metric computation on.
        ignore_index: Optional class index to ignore in computation (e.g. 6 for Unknown).
    """

    def __init__(self, num_classes: int, device: str = "cuda", ignore_index: int = None):
        self.num_classes = num_classes
        self.device = device
        self.ignore_index = ignore_index

        # Mean IoU
        self.mean_iou = JaccardIndex(
            task="multiclass",
            num_classes=num_classes,
            ignore_index=ignore_index,
            average="macro",
        ).to(device)

        # Per-class IoU
        self.per_class_iou = JaccardIndex(
            task="multiclass",
            num_classes=num_classes,
            ignore_index=ignore_index,
            average="none",
        ).to(device)

    def update(self, preds: torch.Tensor, targets: torch.Tensor):
        """
        Update with a batch of predictions and targets.

        Args:
            preds: Model output logits (B, C, H, W) or class indices (B, H, W).
            targets: Ground truth class indices (B, H, W).
        """
        if preds.dim() == 4:
            preds = preds.argmax(dim=1)
        self.mean_iou.update(preds, targets)
        self.per_class_iou.update(preds, targets)

    def compute(self) -> float:
        """Compute mean IoU over all accumulated batches."""
        return self.mean_iou.compute().item()

    def compute_per_class(self) -> torch.Tensor:
        """Compute per-class IoU. Returns tensor of shape (num_classes,)."""
        return self.per_class_iou.compute()

    def reset(self):
        """Reset for a new epoch."""
        self.mean_iou.reset()
        self.per_class_iou.reset()

    def summary(self, class_names: list = None) -> str:
        """
        Generate a human-readable per-class IoU summary.

        Args:
            class_names: Optional list of class names.

        Returns:
            Formatted string with per-class and mean IoU.
        """
        per_class = self.compute_per_class()
        mean = self.compute()

        lines = []
        for i, iou_val in enumerate(per_class):
            name = class_names[i] if class_names and i < len(class_names) else f"Class {i}"
            lines.append(f"  {name:<25} IoU={iou_val:.4f}")
        lines.append(f"  {'Mean IoU':<25} {mean:.4f}")

        return "\n".join(lines)
