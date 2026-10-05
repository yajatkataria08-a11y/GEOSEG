"""
Unified training script — config-driven, supports all 4 phases.

Usage:
    python src/train.py --config configs/phase1_eurosat.yaml
    python src/train.py --config configs/phase2_deepglobe.yaml
    python src/train.py --config configs/phase3_multispectral.yaml

The YAML config determines which dataset, model, loss, and metrics to use.
"""

import argparse
import os
import random
import sys

# Ensure UTF-8 output encoding on Windows console
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import numpy as np
import torch
import torch.nn as nn
from torch.optim.lr_scheduler import CosineAnnealingLR
import yaml
from tqdm import tqdm

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.metrics import AccuracyTracker, IoUTracker
from src.utils.logging import TrainLogger
from src.utils.checkpoint import BestModelTracker


def set_seed(seed: int = 42):
    """Set global random seed for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    print(f"  Global seed set to {seed}")


def load_config(config_path: str) -> dict:
    """Load and return a YAML config file."""
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    print(f"Loaded config: {config_path}")
    print(f"  Phase: {config.get('phase', 'unknown')}")
    return config


def get_device() -> torch.device:
    """Get the best available device."""
    if torch.cuda.is_available():
        device = torch.device("cuda")
        print(f"Using GPU: {torch.cuda.get_device_name(0)}")
    else:
        device = torch.device("cpu")
        print("Using CPU (no GPU available)")
    return device


# ─── Dataset Loaders ─────────────────────────────────────────────────────────────

def build_dataloaders(config: dict):
    """
    Build train/val dataloaders based on config.

    Returns:
        Tuple of (train_loader, val_loader).
    """
    ds_config = config["dataset"]
    train_config = config["training"]
    ds_name = ds_config["name"]

    if ds_name == "eurosat":
        from src.datasets.eurosat import get_eurosat_dataloaders
        return get_eurosat_dataloaders(
            root=ds_config.get("root", "data/eurosat"),
            download=ds_config.get("download", True),
            batch_size=train_config.get("batch_size", 64),
            num_workers=train_config.get("num_workers", 4),
        )

    elif ds_name == "deepglobe":
        from src.datasets.deepglobe import get_deepglobe_dataloaders
        return get_deepglobe_dataloaders(
            root=ds_config.get("root", "data/deepglobe"),
            batch_size=train_config.get("batch_size", 8),
            num_workers=train_config.get("num_workers", 4),
            tile_size=ds_config.get("tile_size", 512),
        )

    elif ds_name == "sen12ms":
        # Phase 3: SEN12MS multispectral segmentation loader
        from src.datasets.sen12ms import get_sen12ms_dataloaders
        return get_sen12ms_dataloaders(
            root=ds_config.get("root", "data/sen12ms"),
            batch_size=train_config.get("batch_size", 8),
            num_workers=train_config.get("num_workers", 0),
        )

    else:
        raise ValueError(f"Unknown dataset: {ds_name}")


# ─── Model Builder ───────────────────────────────────────────────────────────────

def build_model(config: dict, device: torch.device) -> nn.Module:
    """
    Build a model based on config.

    Phase 1: SimpleCNN classifier
    Phase 2+: SMP segmentation model
    """
    model_config = config["model"]
    model_name = model_config["name"]

    if model_name == "simple_cnn":
        from src.models.simple_cnn import SimpleCNN
        model = SimpleCNN(
            in_channels=model_config.get("in_channels", 13),
            num_classes=model_config.get("num_classes", 10),
        )
    else:
        from src.models.segmentation import build_segmentation_model
        model = build_segmentation_model(model_config)

    model = model.to(device)
    return model


# ─── Optimizer & Scheduler ───────────────────────────────────────────────────────

def build_optimizer(model: nn.Module, config: dict):
    """Build optimizer from config."""
    train_config = config["training"]
    lr = train_config.get("lr", 1e-3)
    opt_name = train_config.get("optimizer", "adam").lower()

    if opt_name == "adam":
        return torch.optim.Adam(model.parameters(), lr=lr)
    elif opt_name == "adamw":
        return torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    elif opt_name == "sgd":
        return torch.optim.SGD(model.parameters(), lr=lr, momentum=0.9, weight_decay=1e-4)
    else:
        raise ValueError(f"Unknown optimizer: {opt_name}")


def build_scheduler(optimizer, config: dict, total_epochs: int = None):
    """Build LR scheduler from config (optional)."""
    train_config = config["training"]
    sched_name = train_config.get("scheduler", None)
    epochs = total_epochs if total_epochs is not None else train_config.get("epochs", 15)

    if sched_name is None:
        return None
    elif sched_name == "cosine":
        return CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-6)
    else:
        raise ValueError(f"Unknown scheduler: {sched_name}")


def build_loss(config: dict, device: torch.device = None):
    """Build loss function from config."""
    loss_name = config["training"].get("loss", "cross_entropy")

    if config.get("phase", 1) == 1:
        # Phase 1: always CrossEntropy for classification
        return nn.CrossEntropyLoss()
    else:
        from src.models.segmentation import build_loss_function
        ds_name = config.get("dataset", {}).get("name")
        ignore_idx = config.get("dataset", {}).get("ignore_index", 6 if ds_name == "deepglobe" else None)

        # Balanced class weights for DeepGlobe (Urban, Agri, Rangeland, Forest, Water, Barren, Unknown)
        class_weights = None
        if ds_name == "deepglobe":
            weights = torch.tensor([2.0, 0.5, 6.0, 1.8, 4.5, 2.0, 0.0], dtype=torch.float32)
            if device is not None:
                weights = weights.to(device)
            class_weights = weights

        return build_loss_function(
            loss_name,
            num_classes=config["model"].get("num_classes", 7),
            ignore_index=ignore_idx,
            class_weights=class_weights,
        )


# ─── Training Loops ──────────────────────────────────────────────────────────────
from src.transforms.band_math import build_multispectral_input_torch


def train_one_epoch_classification(model, loader, optimizer, loss_fn, device, config=None, scaler=None, grad_accum_steps=1):
    """Phase 1: Classification training loop."""
    model.train()
    total_loss = 0
    num_batches = 0
    use_amp = scaler is not None and scaler.is_enabled() and device.type == "cuda"
    use_indices = config.get("dataset", {}).get("use_indices", False) if config else False
    band_order = tuple(config.get("dataset", {}).get("band_order", [])) if config else ()

    optimizer.zero_grad()
    for batch_idx, batch in enumerate(tqdm(loader, desc="  Train", leave=False)):
        images = batch["image"].to(device).float()
        labels = batch["label"].to(device)

        if use_indices and band_order:
            images = build_multispectral_input_torch(images, band_order)

        with torch.amp.autocast(device_type=device.type, enabled=use_amp):
            outputs = model(images)
            loss = loss_fn(outputs, labels)
            if grad_accum_steps > 1:
                loss = loss / grad_accum_steps

        if use_amp:
            scaler.scale(loss).backward()
            if (batch_idx + 1) % grad_accum_steps == 0 or (batch_idx + 1) == len(loader):
                scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                scaler.step(optimizer)
                scaler.update()
                optimizer.zero_grad()
        else:
            loss.backward()
            if (batch_idx + 1) % grad_accum_steps == 0 or (batch_idx + 1) == len(loader):
                torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                optimizer.step()
                optimizer.zero_grad()

        total_loss += loss.item() * (grad_accum_steps if grad_accum_steps > 1 else 1)
        num_batches += 1

    return total_loss / max(num_batches, 1)


def validate_classification(model, loader, metric, device, config=None):
    """Phase 1: Classification validation."""
    model.eval()
    metric.reset()
    use_indices = config.get("dataset", {}).get("use_indices", False) if config else False
    band_order = tuple(config.get("dataset", {}).get("band_order", [])) if config else ()

    with torch.no_grad():
        for batch in tqdm(loader, desc="  Val", leave=False):
            images = batch["image"].to(device).float()
            labels = batch["label"].to(device)

            if use_indices and band_order:
                images = build_multispectral_input_torch(images, band_order)

            outputs = model(images)
            metric.update(outputs, labels)

    return metric.compute()


def train_one_epoch_segmentation(model, loader, optimizer, loss_fn, device, config=None, scaler=None, grad_accum_steps=1):
    """Phase 2+: Segmentation training loop with AMP support."""
    model.train()
    total_loss = 0
    num_batches = 0
    use_amp = scaler is not None and scaler.is_enabled() and device.type == "cuda"

    use_indices = config.get("dataset", {}).get("use_indices", False) if config else False
    band_order = tuple(config.get("dataset", {}).get("band_order", [])) if config else ()

    optimizer.zero_grad()
    for batch_idx, batch in enumerate(tqdm(loader, desc="  Train", leave=False)):
        # Handle different dataset formats
        if isinstance(batch, dict):
            # torchgeo format (SEN12MS)
            images = batch["image"].to(device).float()
            masks = batch["mask"].to(device).long()
            if use_indices and band_order:
                images = build_multispectral_input_torch(images, band_order)
        else:
            # Tuple format (DeepGlobe)
            images, masks = batch
            images = images.to(device).float()
            masks = masks.to(device).long()

        with torch.amp.autocast(device_type=device.type, enabled=use_amp):
            outputs = model(images)
            loss = loss_fn(outputs, masks)
            if grad_accum_steps > 1:
                loss = loss / grad_accum_steps

        if use_amp:
            scaler.scale(loss).backward()
            if (batch_idx + 1) % grad_accum_steps == 0 or (batch_idx + 1) == len(loader):
                scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                scaler.step(optimizer)
                scaler.update()
                optimizer.zero_grad()
        else:
            loss.backward()
            if (batch_idx + 1) % grad_accum_steps == 0 or (batch_idx + 1) == len(loader):
                torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                optimizer.step()
                optimizer.zero_grad()

        total_loss += loss.item() * (grad_accum_steps if grad_accum_steps > 1 else 1)
        num_batches += 1

    return total_loss / max(num_batches, 1)


def validate_segmentation(model, loader, metric, device, config=None):
    """Phase 2+: Segmentation validation."""
    model.eval()
    metric.reset()

    use_indices = config.get("dataset", {}).get("use_indices", False) if config else False
    band_order = tuple(config.get("dataset", {}).get("band_order", [])) if config else ()

    with torch.no_grad():
        for batch in tqdm(loader, desc="  Val", leave=False):
            if isinstance(batch, dict):
                images = batch["image"].to(device).float()
                masks = batch["mask"].to(device).long()
                if use_indices and band_order:
                    images = build_multispectral_input_torch(images, band_order)
            else:
                images, masks = batch
                images = images.to(device).float()
                masks = masks.to(device).long()

            outputs = model(images)
            metric.update(outputs, masks)

    return metric.compute()


# ─── Main ────────────────────────────────────────────────────────────────────────

def validate_config(config: dict):
    """Upfront validation of config to catch mismatches early."""
    model_cfg = config.get("model", {})
    ds_cfg = config.get("dataset", {})

    in_channels = model_cfg.get("in_channels")
    band_order = ds_cfg.get("band_order", [])
    use_indices = ds_cfg.get("use_indices", False)

    if in_channels is not None and band_order:
        expected = len(band_order) + (3 if use_indices else 0)
        assert in_channels == expected, (
            f"Config mismatch: model.in_channels={in_channels} but "
            f"len(band_order)={len(band_order)} + indices={'3' if use_indices else '0'} = {expected}. "
            f"Check your YAML config."
        )

    num_classes = model_cfg.get("num_classes")
    ds_name = ds_cfg.get("name")
    expected_classes = {"eurosat": 10, "deepglobe": 7, "sen12ms": 11}
    if num_classes is not None and ds_name in expected_classes:
        assert num_classes == expected_classes[ds_name], (
            f"Config mismatch: model.num_classes={num_classes} but "
            f"dataset '{ds_name}' expects {expected_classes[ds_name]} classes."
        )


def main():
    parser = argparse.ArgumentParser(description="GeoSeg Training")
    parser.add_argument("--config", type=str, required=True, help="Path to YAML config file")
    parser.add_argument("--resume", type=str, default=None, help="Path to checkpoint to resume from")
    parser.add_argument("--epochs", type=int, default=None, help="Override number of epochs")
    parser.add_argument("--lr", type=float, default=None, help="Override learning rate")
    parser.add_argument("--batch-size", type=int, default=None, help="Override batch size")
    args = parser.parse_args()

    # Load config
    config = load_config(args.config)
    phase = config.get("phase", 1)
    train_cfg = config.get("training", {})

    # Apply CLI overrides if provided
    if args.epochs is not None:
        train_cfg["epochs"] = args.epochs
    if args.lr is not None:
        train_cfg["lr"] = args.lr
    if args.batch_size is not None:
        train_cfg["batch_size"] = args.batch_size

    epochs = train_cfg.get("epochs", 10)
    use_amp = train_cfg.get("amp", False)
    grad_accum_steps = train_cfg.get("gradient_accumulation_steps", 1)
    patience = train_cfg.get("early_stopping_patience", None)
    seed = train_cfg.get("seed", 42)

    # Global seeding for reproducibility
    set_seed(seed)

    # Upfront config validation
    validate_config(config)

    # Setup
    device = get_device()
    model = build_model(config, device)
    optimizer = build_optimizer(model, config)
    loss_fn = build_loss(config, device=device)

    # Resume from checkpoint if specified
    start_epoch = 0
    ckpt_info = None
    if args.resume:
        from src.utils.checkpoint import load_checkpoint
        ckpt_info = load_checkpoint(args.resume, model, optimizer, device=str(device))
        start_epoch = ckpt_info["epoch"] + 1
        print(f"Resumed from epoch {start_epoch}")

    total_epochs = (start_epoch + epochs) if args.resume else epochs
    scheduler = build_scheduler(optimizer, config, total_epochs=total_epochs)

    # Restore scheduler state from checkpoint on resume
    if args.resume and scheduler is not None:
        ckpt = torch.load(args.resume, map_location=str(device), weights_only=False)
        if "scheduler_state_dict" in ckpt:
            scheduler.load_state_dict(ckpt["scheduler_state_dict"])
            print(f"  Restored scheduler state from checkpoint")

    # Scaler for AMP (PyTorch 2.0+ API)
    scaler = torch.amp.GradScaler(device.type, enabled=use_amp and device.type == "cuda")

    # Build dataloaders
    train_loader, val_loader = build_dataloaders(config)

    # Metrics & logging
    output_config = config["output"]
    logger = TrainLogger(
        log_dir=output_config.get("log_dir", "outputs/tensorboard"),
        experiment_name=f"phase{phase}",
    )

    is_classification = config["model"].get("name") == "simple_cnn" or config.get("dataset", {}).get("name") == "eurosat"

    if is_classification:
        metric = AccuracyTracker()
        metric_name = "val_acc"
        tracker = BestModelTracker(
            output_config.get("checkpoint_dir", "outputs/checkpoints"),
            metric_name="val_acc",
            mode="max",
            patience=patience,
        )
    else:
        num_classes = config["model"].get("num_classes", 7)
        ignore_idx = config.get("dataset", {}).get("ignore_index", 6 if config.get("dataset", {}).get("name") == "deepglobe" else None)
        metric = IoUTracker(num_classes=num_classes, device=str(device), ignore_index=ignore_idx)
        metric_name = "mIoU"
        tracker = BestModelTracker(
            output_config.get("checkpoint_dir", "outputs/checkpoints"),
            metric_name="mIoU",
            mode="max",
            patience=patience,
        )

    # Seed BestModelTracker from checkpoint so we don't overwrite a better best_model.pth
    if args.resume and ckpt_info is not None:
        resumed_metrics = ckpt_info.get("metrics", {})
        if metric_name in resumed_metrics:
            tracker.best_value = resumed_metrics[metric_name]
            tracker.best_epoch = ckpt_info["epoch"]
            print(f"  Restored best {metric_name}={tracker.best_value:.4f} from checkpoint (epoch {tracker.best_epoch + 1})")

    # ─── Training Loop ───────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  Phase {phase} Training — Epochs {start_epoch+1} to {total_epochs} (AMP: {use_amp}, GradAccum: {grad_accum_steps})")
    print(f"{'='*60}\n")

    for epoch in range(start_epoch, total_epochs):
        # Train
        if is_classification:
            train_loss = train_one_epoch_classification(
                model, train_loader, optimizer, loss_fn, device, config=config,
                scaler=scaler, grad_accum_steps=grad_accum_steps,
            )
            val_metric = validate_classification(
                model, val_loader, metric, device, config=config,
            )
        else:
            train_loss = train_one_epoch_segmentation(
                model, train_loader, optimizer, loss_fn, device, config=config,
                scaler=scaler, grad_accum_steps=grad_accum_steps,
            )
            val_metric = validate_segmentation(
                model, val_loader, metric, device, config=config,
            )

        # Log
        extra = {}
        if scheduler is not None:
            extra["train/lr"] = scheduler.get_last_lr()[0]

        if not is_classification:
            per_class = metric.compute_per_class()
            for idx, c_iou in enumerate(per_class):
                extra[f"val_iou/class_{idx}"] = c_iou.item()

        logger.log_epoch(epoch, total_epochs, train_loss, val_metric, metric_name, extra)

        # Checkpoint
        tracker.update(
            model, optimizer, epoch, val_metric,
            metrics={"train_loss": train_loss, metric_name: val_metric},
            scheduler=scheduler,
        )

        # Step scheduler
        if scheduler is not None:
            scheduler.step()

        # Per-class IoU summary for segmentation (every 5 epochs)
        if not is_classification and (epoch + 1) % 5 == 0:
            print(f"\n  Per-class IoU (epoch {epoch + 1}):")
            print(metric.summary())
            print()

        # Early stopping
        if tracker.should_stop():
            break

    # ─── Training Complete ───────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  Training complete!")
    print(f"  Best {metric_name}: {tracker.best_value:.4f} (epoch {tracker.best_epoch + 1})")
    print(f"  Checkpoints: {output_config.get('checkpoint_dir')}")
    print(f"{'='*60}")

    logger.close()


if __name__ == "__main__":
    main()
