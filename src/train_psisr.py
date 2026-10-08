"""
Progressive Satellite Image Super-Resolution (PSISR) Training Script.
Implements the training methodology from Sharma et al. (2025):
"Enhanced satellite image resolution with a residual network and correlation filter"
Chemometrics and Intelligent Laboratory Systems 256 (2025) 105277

Key features:
- Progressive multi-stage loss (UB1: 2x, UB2: 4x, UB3: 8x)
- Adaptive Combined Loss (Equations 4-8)
- Adam optimizer with StepLR (1e-4 initial lr, 10x reduction every 100 epochs)
- Evaluation of PSNR & SSIM on Y-channel of transformed YCbCr space (Section 3.3)
"""

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Dict, Tuple

# Console encoding on Windows
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import torch
import torch.nn as nn
from torch.optim.lr_scheduler import StepLR
from tqdm import tqdm
import yaml

# Add root directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.psisr import PSISRNet, CombinedLoss, calculate_metrics
from src.datasets.aid import AIDDataset, get_aid_dataloaders


def parse_args():
    parser = argparse.ArgumentParser(description="Train PSISR on AID Dataset")
    parser.add_argument("--config", type=str, default="configs/psisr_aid.yaml", help="Path to config YAML")
    parser.add_argument("--epochs", type=int, default=None, help="Override total epochs")
    parser.add_argument("--batch-size", type=int, default=None, help="Override batch size")
    parser.add_argument("--lr", type=float, default=None, help="Override learning rate")
    parser.add_argument("--smoke-test", action="store_true", help="Run a 1-epoch smoke test with few batches")
    parser.add_argument("--max-steps", type=int, default=None, help="Max steps per epoch")
    parser.add_argument("--device", type=str, default=None, help="cuda or cpu")
    parser.add_argument("--resume", action="store_true", help="Resume from checkpoint in save-dir if available")
    parser.add_argument("--save-dir", type=str, default="checkpoints/psisr", help="Checkpoint directory")
    return parser.parse_args()


def load_config(config_path: str) -> dict:
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}


def train_one_epoch(
    model: nn.Module,
    train_loader,
    optimizer: torch.optim.Optimizer,
    loss_fn: CombinedLoss,
    device: torch.device,
    epoch: int,
    max_steps: int = None,
    scaler = None,
) -> Dict[str, float]:
    model.train()
    total_loss = 0.0
    loss_2x_sum = 0.0
    loss_4x_sum = 0.0
    loss_8x_sum = 0.0
    steps = 0
    use_amp = (device.type == "cuda")

    pbar = tqdm(train_loader, desc=f"Epoch {epoch} [Train]", leave=False)
    for batch_idx, batch in enumerate(pbar):
        if max_steps and batch_idx >= max_steps:
            break

        step_t0 = time.time()
        lr = batch["lr"].to(device)
        hr_2x = batch["hr_2x"].to(device)
        hr_4x = batch["hr_4x"].to(device)
        hr_8x = batch["hr_8x"].to(device)

        optimizer.zero_grad()

        # Forward pass with Automatic Mixed Precision (AMP)
        with torch.amp.autocast(device_type=device.type, enabled=use_amp):
            outputs = model(lr, scale=8)
            out_2x = outputs["sr_2x"]
            out_4x = outputs["sr_4x"]
            out_8x = outputs["sr_8x"]

            # Adaptive Combined Loss at each cascading stage (Eq. 7-8)
            loss_2x, _, _ = loss_fn(out_2x, hr_2x)
            loss_4x, _, _ = loss_fn(out_4x, hr_4x)
            loss_8x, _, _ = loss_fn(out_8x, hr_8x)
            loss = loss_2x + loss_4x + loss_8x

        if scaler and use_amp:
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
        else:
            loss.backward()
            optimizer.step()

        total_loss += loss.item()
        loss_2x_sum += loss_2x.item()
        loss_4x_sum += loss_4x.item()
        loss_8x_sum += loss_8x.item()
        steps += 1
        step_dt = time.time() - step_t0

        if steps % 5 == 0 or steps <= 5 or (max_steps and steps == max_steps):
            print(
                f"  Epoch {epoch} [Step {steps}/{max_steps or len(train_loader)}] in {step_dt:.2f}s | "
                f"Loss: {loss.item():.4f} (2x: {loss_2x.item():.4f}, 4x: {loss_4x.item():.4f}, 8x: {loss_8x.item():.4f})",
                flush=True,
            )

    return {
        "loss": total_loss / max(1, steps),
        "loss_2x": loss_2x_sum / max(1, steps),
        "loss_4x": loss_4x_sum / max(1, steps),
        "loss_8x": loss_8x_sum / max(1, steps),
    }


@torch.no_grad()
def evaluate(
    model: nn.Module,
    val_loader,
    device: torch.device,
    max_steps: int = None,
) -> Dict[str, float]:
    model.eval()
    psnr_2x_sum, ssim_2x_sum = 0.0, 0.0
    psnr_4x_sum, ssim_4x_sum = 0.0, 0.0
    psnr_8x_sum, ssim_8x_sum = 0.0, 0.0
    count = 0
    use_amp = (device.type == "cuda")

    pbar = tqdm(val_loader, desc="[Validation]", leave=False)
    for batch_idx, batch in enumerate(pbar):
        if max_steps and batch_idx >= max_steps:
            break

        lr = batch["lr"].to(device)
        hr_2x = batch["hr_2x"].to(device)
        hr_4x = batch["hr_4x"].to(device)
        hr_8x = batch["hr_8x"].to(device)

        with torch.amp.autocast(device_type=device.type, enabled=use_amp):
            outputs = model(lr, scale=8)
            out_2x = outputs["sr_2x"]
            out_4x = outputs["sr_4x"]
            out_8x = outputs["sr_8x"]

        # Calculate metrics for each batch sample on Y channel (per Section 3.3)
        b_size = lr.size(0)
        for i in range(b_size):
            m2 = calculate_metrics(out_2x[i], hr_2x[i], use_y_channel=True)
            m4 = calculate_metrics(out_4x[i], hr_4x[i], use_y_channel=True)
            m8 = calculate_metrics(out_8x[i], hr_8x[i], use_y_channel=True)

            psnr_2x_sum += m2["psnr"]
            ssim_2x_sum += m2["ssim"]
            psnr_4x_sum += m4["psnr"]
            ssim_4x_sum += m4["ssim"]
            psnr_8x_sum += m8["psnr"]
            ssim_8x_sum += m8["ssim"]
            count += 1

    return {
        "psnr_2x": round(psnr_2x_sum / max(1, count), 2),
        "ssim_2x": round(ssim_2x_sum / max(1, count), 4),
        "psnr_4x": round(psnr_4x_sum / max(1, count), 2),
        "ssim_4x": round(ssim_4x_sum / max(1, count), 4),
        "psnr_8x": round(psnr_8x_sum / max(1, count), 2),
        "ssim_8x": round(ssim_8x_sum / max(1, count), 4),
    }


def main():
    args = parse_args()
    config = load_config(args.config)

    # Determine device
    if args.device:
        device = torch.device(args.device)
    else:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Executing on device: {device}")

    # Hyperparameters
    train_cfg = config.get("training", {})
    epochs = args.epochs or (1 if args.smoke_test else train_cfg.get("epochs", 200))
    batch_size = args.batch_size or (2 if args.smoke_test else train_cfg.get("batch_size", 8))
    lr = args.lr or train_cfg.get("lr", 1e-4)
    save_dir = Path(args.save_dir or train_cfg.get("save_dir", "checkpoints/psisr"))
    save_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 60)
    print("PSISR Training Setup (Sharma et al. 2025)")
    print("=" * 60)
    print(f"  Total Epochs:      {epochs} {'(SMOKE TEST)' if args.smoke_test else ''}")
    print(f"  Batch Size:        {batch_size}")
    print(f"  Learning Rate:     {lr}")
    print(f"  LR Scheduler:      StepLR (step_size=100, gamma=0.1)")
    print(f"  Loss Function:     Adaptive Combined Loss (MSE + SSIM, Eq. 7-8)")
    print(f"  Metric Space:      YCbCr (Y-channel, Sec 3.3)")
    print(f"  Save Directory:    {save_dir}")
    print("=" * 60 + "\n", flush=True)

    # Data loaders
    ds_root = config.get("dataset", {}).get("root", "data/aid")
    train_loader, val_loader = get_aid_dataloaders(
        root_dir=ds_root,
        batch_size=batch_size,
        scale_factor=8,
        patch_size=64,
        num_workers=0,
    )
    print(f"Dataset Loaded: {len(train_loader.dataset)} train samples, {len(val_loader.dataset)} val samples.", flush=True)

    # Model
    model = PSISRNet(in_channels=3, out_channels=3, base_filters=128).to(device)
    total_params = sum(p.numel() for p in model.parameters())
    print(f"Model: PSISRNet ({total_params:,} parameters)", flush=True)

    # Loss and optimizer
    loss_fn = CombinedLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    scheduler = StepLR(optimizer, step_size=train_cfg.get("lr_step_size", 100), gamma=train_cfg.get("lr_gamma", 0.1))

    best_psnr_8x = -1.0
    start_epoch = 1
    ckpt_path = save_dir / "best_model.pth"
    if args.resume and ckpt_path.exists():
        ckpt = torch.load(ckpt_path, map_location=device, weights_only=False)
        model.load_state_dict(ckpt["model_state_dict"])
        if "optimizer_state_dict" in ckpt:
            try:
                optimizer.load_state_dict(ckpt["optimizer_state_dict"])
            except Exception:
                pass
        start_epoch = ckpt.get("epoch", 0) + 1
        best_psnr_8x = ckpt.get("metrics", {}).get("psnr_8x", -1.0)
        print(f"Resumed from checkpoint: {ckpt_path} (Starting at Epoch {start_epoch}, Prior Best 8x: {best_psnr_8x:.2f} dB)", flush=True)

    max_steps = args.max_steps if args.max_steps is not None else (3 if args.smoke_test else None)

    start_time = time.time()
    for epoch in range(start_epoch, epochs + 1):
        epoch_start = time.time()

        train_metrics = train_one_epoch(
            model, train_loader, optimizer, loss_fn, device, epoch, max_steps=max_steps
        )
        val_metrics = evaluate(model, val_loader, device, max_steps=max_steps)
        scheduler.step()

        elapsed = time.time() - epoch_start
        print(
            f"\n>>> Epoch {epoch:03d}/{epochs:03d} [{elapsed:.1f}s] Complete! "
            f"Loss: {train_metrics['loss']:.4f} | "
            f"2x: {val_metrics['psnr_2x']:.2f}dB / {val_metrics['ssim_2x']:.4f} | "
            f"4x: {val_metrics['psnr_4x']:.2f}dB / {val_metrics['ssim_4x']:.4f} | "
            f"8x: {val_metrics['psnr_8x']:.2f}dB / {val_metrics['ssim_8x']:.4f}\n",
            flush=True,
        )

        # Save best checkpoint based on 8x PSNR
        if val_metrics["psnr_8x"] > best_psnr_8x:
            best_psnr_8x = val_metrics["psnr_8x"]
            ckpt_path = save_dir / "best_model.pth"
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "metrics": val_metrics,
            }, ckpt_path)
            print(f"  [Checkpoint Saved] -> {ckpt_path} (Best 8x PSNR: {best_psnr_8x:.2f} dB)\n", flush=True)

    total_time = time.time() - start_time
    print("\n" + "=" * 60)
    print(f"Training Complete in {total_time:.1f}s!")
    print(f"Best Validation Results (Y-Channel):")
    print(f"  2x Scale: {val_metrics['psnr_2x']:.2f} dB / {val_metrics['ssim_2x']:.4f}")
    print(f"  4x Scale: {val_metrics['psnr_4x']:.2f} dB / {val_metrics['ssim_4x']:.4f}")
    print(f"  8x Scale: {val_metrics['psnr_8x']:.2f} dB / {val_metrics['ssim_8x']:.4f}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
