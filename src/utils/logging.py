"""
Training logger — TensorBoard + console output.

Centralizes all logging so train.py stays clean.
"""

import os
from datetime import datetime

import torch


class TrainLogger:
    """
    Unified logger for training metrics and visualizations.

    Writes scalars and images to TensorBoard and prints formatted
    summaries to console.

    Args:
        log_dir: Directory for TensorBoard event files.
        experiment_name: Optional name for the experiment run.
    """

    def __init__(self, log_dir: str, experiment_name: str = None):
        os.makedirs(log_dir, exist_ok=True)

        # Lazy import — tensorboard may not be installed in minimal setups
        from torch.utils.tensorboard import SummaryWriter

        if experiment_name:
            log_dir = os.path.join(log_dir, experiment_name)

        self.writer = SummaryWriter(log_dir=log_dir)
        self.log_dir = log_dir
        self.start_time = datetime.now()

        print(f"TensorBoard logs: {log_dir}")
        print(f"  → Run: tensorboard --logdir {log_dir}")

    def log_scalar(self, tag: str, value: float, step: int):
        """Log a scalar value to TensorBoard."""
        self.writer.add_scalar(tag, value, step)

    def log_scalars(self, main_tag: str, tag_scalar_dict: dict, step: int):
        """Log multiple related scalars (e.g., per-class IoU)."""
        self.writer.add_scalars(main_tag, tag_scalar_dict, step)

    def log_image(self, tag: str, image: torch.Tensor, step: int):
        """
        Log an image tensor to TensorBoard.

        Args:
            tag: Image tag/name.
            image: Tensor of shape (C, H, W) with values in [0, 1].
            step: Global step.
        """
        self.writer.add_image(tag, image, step)

    def log_epoch(
        self,
        epoch: int,
        total_epochs: int,
        train_loss: float,
        val_metric: float,
        metric_name: str = "val_acc",
        extra: dict = None,
    ):
        """
        Log and print an epoch summary.

        Args:
            epoch: Current epoch (0-indexed).
            total_epochs: Total number of epochs.
            train_loss: Average training loss for the epoch.
            val_metric: Validation metric value.
            metric_name: Name of the validation metric.
            extra: Optional dict of additional metrics to log.
        """
        elapsed = datetime.now() - self.start_time

        # TensorBoard
        self.log_scalar("train/loss", train_loss, epoch)
        self.log_scalar(f"val/{metric_name}", val_metric, epoch)

        if extra:
            for key, value in extra.items():
                self.log_scalar(key, value, epoch)

        # Console
        extra_str = ""
        if extra:
            extra_str = "  " + "  ".join(f"{k}={v:.4f}" for k, v in extra.items())

        print(
            f"  Epoch [{epoch + 1}/{total_epochs}]  "
            f"loss={train_loss:.4f}  "
            f"{metric_name}={val_metric:.4f}"
            f"{extra_str}  "
            f"[{elapsed}]"
        )

    def log_lr(self, lr: float, step: int):
        """Log learning rate."""
        self.log_scalar("train/lr", lr, step)

    def close(self):
        """Flush and close the TensorBoard writer."""
        self.writer.flush()
        self.writer.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
