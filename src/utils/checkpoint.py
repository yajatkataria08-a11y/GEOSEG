"""
Checkpoint utilities — save and load model state.

Tracks the best model by a configurable metric and auto-saves both
'latest' and 'best' checkpoints.
"""

import os
from pathlib import Path

import torch


def save_checkpoint(
    model: torch.nn.Module,
    optimizer: torch.optim.Optimizer,
    epoch: int,
    metrics: dict,
    path: str,
    scheduler=None,
):
    """
    Save a training checkpoint.

    Args:
        model: The model to save.
        optimizer: The optimizer state.
        epoch: Current epoch number.
        metrics: Dict of metric values (e.g., {"val_acc": 0.92, "train_loss": 0.15}).
        path: File path to save the checkpoint.
        scheduler: Optional LR scheduler state.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)

    checkpoint = {
        "epoch": epoch,
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "metrics": metrics,
    }

    if scheduler is not None:
        checkpoint["scheduler_state_dict"] = scheduler.state_dict()

    torch.save(checkpoint, path)


def load_checkpoint(
    path: str,
    model: torch.nn.Module,
    optimizer: torch.optim.Optimizer = None,
    scheduler=None,
    device: str = "cuda",
) -> dict:
    """
    Load a training checkpoint.

    Args:
        path: Path to the checkpoint file.
        model: Model to load weights into.
        optimizer: Optional optimizer to restore state.
        scheduler: Optional LR scheduler to restore state.
        device: Device to map tensors to.

    Returns:
        Dict with 'epoch' and 'metrics' from the checkpoint.
    """
    try:
        checkpoint = torch.load(path, map_location=device, weights_only=True)
    except Exception:
        checkpoint = torch.load(path, map_location=device, weights_only=False)

    try:
        model.load_state_dict(checkpoint["model_state_dict"])
    except RuntimeError as e:
        raise RuntimeError(
            f"Checkpoint architecture mismatch while loading '{path}'.\n"
            f"Error details: {e}\n"
            f"Hint: Ensure the model config (architecture, in_channels, num_classes) "
            f"matches the architecture used when creating this checkpoint."
        ) from e

    if optimizer is not None and "optimizer_state_dict" in checkpoint:
        optimizer.load_state_dict(checkpoint["optimizer_state_dict"])

    if scheduler is not None and "scheduler_state_dict" in checkpoint:
        scheduler.load_state_dict(checkpoint["scheduler_state_dict"])

    return {
        "epoch": checkpoint.get("epoch", 0),
        "metrics": checkpoint.get("metrics", {}),
    }


class BestModelTracker:
    """
    Tracks the best model checkpoint by a specified metric.

    Automatically saves the best model when the tracked metric improves.

    Args:
        checkpoint_dir: Directory to save checkpoints.
        metric_name: Name of the metric to track (e.g., "val_acc", "mIoU").
        mode: "max" if higher is better, "min" if lower is better.
    """

    def __init__(self, checkpoint_dir: str, metric_name: str = "val_metric", mode: str = "max", patience: int = None):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.metric_name = metric_name
        self.mode = mode
        self.patience = patience
        self.num_bad_epochs = 0

        self.best_value = float("-inf") if mode == "max" else float("inf")
        self.best_epoch = -1

    def update(
        self,
        model: torch.nn.Module,
        optimizer: torch.optim.Optimizer,
        epoch: int,
        metric_value: float,
        metrics: dict = None,
        scheduler=None,
    ) -> bool:
        """
        Check if current metric is the best so far, and save if so.
        Also always saves the 'latest' checkpoint.
        """
        if metrics is None:
            metrics = {self.metric_name: metric_value}

        # Always save latest
        save_checkpoint(
            model, optimizer, epoch, metrics,
            str(self.checkpoint_dir / "latest.pth"),
            scheduler=scheduler,
        )

        # Check if new best
        is_best = False
        if self.mode == "max" and metric_value > self.best_value:
            is_best = True
        elif self.mode == "min" and metric_value < self.best_value:
            is_best = True

        if is_best:
            self.best_value = metric_value
            self.best_epoch = epoch
            self.num_bad_epochs = 0
            save_checkpoint(
                model, optimizer, epoch, metrics,
                str(self.checkpoint_dir / "best_model.pth"),
                scheduler=scheduler,
            )
            print(f"  [*] New best {self.metric_name}={metric_value:.4f} (epoch {epoch + 1})")
        else:
            self.num_bad_epochs += 1

        return is_best

    def should_stop(self) -> bool:
        """Check if early stopping criteria is met."""
        if self.patience is not None and self.num_bad_epochs >= self.patience:
            print(f"  [!] Early stopping triggered: no improvement for {self.patience} epochs.")
            return True
        return False

