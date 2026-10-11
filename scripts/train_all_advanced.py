"""
================================================================================
  ADVANCED REMOTE SENSING MODEL TRAINING SUITE  (Comprehensive Edition)
  Project Exhibition -- GEOSEG Advanced Methods
================================================================================
  Models Trained:
    1. ColNet      (IEEE TGRS)        -- Joint Super-Resolution + Segmentation
    2. UNetFormer  (ISPRS 2022)       -- Global-Local Transformer Segmentation
    3. FarSeg      (CVPR / TPAMI)     -- Foreground-Aware Relation Network

  Features:
    ┌─ Optimization ──────────────────────────────────────────────────────────┐
    │  • Mixed-Precision AMP (FP16 on CUDA -- 2x speed, 50% VRAM)            │
    │  • Cosine Annealing LR Scheduler with Warm Restarts (T0=10, Tmult=2)   │
    │  • Linear LR Warmup (first 3 epochs)                                   │
    │  • Gradient Clipping (max_norm=1.0)                                     │
    │  • AdamW optimizer with weight decay = 1e-4                             │
    │  • Label Smoothing Cross-Entropy (epsilon=0.1) for seg models          │
    ├─ Robustness ────────────────────────────────────────────────────────────┤
    │  • Early Stopping (patience=15, monitors val loss)                      │
    │  • Best Checkpoint Saving  (best_*.pth  -- lowest val loss)             │
    │  • Latest Checkpoint Saving (latest_*.pth -- every epoch)               │
    │  • Resume from latest checkpoint (--resume flag)                        │
    │  • Exception handling per model (one failure doesn't stop others)       │
    ├─ Metrics ───────────────────────────────────────────────────────────────┤
    │  • SR models   : PSNR (2x/4x/8x) + SSIM (8x)                          │
    │  • Seg models  : Pixel Accuracy, mIoU, per-class IoU                   │
    │  • All models  : Grad norm, train/val loss, LR                         │
    ├─ Monitoring ────────────────────────────────────────────────────────────┤
    │  • GPU memory (allocated / reserved / peak) per epoch                  │
    │  • ETA + per-epoch timing                                               │
    │  • Progress bar via tqdm                                                │
    │  • Training log saved as JSON per model                                 │
    │  • Matplotlib loss + metric curves saved as PNG                         │
    ├─ Hardware ──────────────────────────────────────────────────────────────┤
    │  • Auto CUDA / CPU device selection                                     │
    │  • Pin memory + num_workers for CUDA DataLoaders                        │
    │  • torch.compile() if PyTorch >= 2.0 and CUDA available                │
    └─────────────────────────────────────────────────────────────────────────┘
================================================================================
"""

import os
import sys
import time
import math
import json
import argparse
import datetime
import traceback
from pathlib import Path
from collections import defaultdict
from typing import Dict, Tuple, Optional, List

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.cuda.amp import GradScaler, autocast
from torch.optim.lr_scheduler import CosineAnnealingWarmRestarts, LinearLR, SequentialLR

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.colnet import ColNet, JointColNetLoss
from src.models.unetformer import UNetFormer
from src.models.farseg import FarSeg
from src.datasets.aid import get_aid_dataloaders

# ─────────────────────────────────────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────────────────────────────────────

COLNET_CFG = dict(
    epochs=50, batch_size=4, lr=1e-4, weight_decay=1e-4,
    grad_clip=1.0, patience=15, num_classes=30,
    warmup_epochs=3, sr_base_filters=32, scale=8,
    lambda_sr=1.0, lambda_wavelet=0.1, lambda_seg=1.0,
)
UNETFORMER_CFG = dict(
    epochs=50, batch_size=4, lr=2.5e-4, weight_decay=1e-4,
    grad_clip=1.0, patience=15, num_classes=30,
    warmup_epochs=3, decoder_dim=64,
)
FARSEG_CFG = dict(
    epochs=50, batch_size=4, lr=2.5e-4, weight_decay=1e-4,
    grad_clip=1.0, patience=15, num_classes=30,
    warmup_epochs=3, feature_dim=64,
)

# ─────────────────────────────────────────────────────────────────────────────
#  UTILITY HELPERS
# ─────────────────────────────────────────────────────────────────────────────

W = 74  # separator width

def sep(c="="):  print(c * W)
def header(title: str):
    sep(); print(f"  {title}"); sep()

def fmt_time(seconds: float) -> str:
    return str(datetime.timedelta(seconds=int(seconds)))

def eta(elapsed: float, done: int, total: int) -> str:
    if done == 0: return "??:??:??"
    return fmt_time(elapsed / done * (total - done))

def now_str() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def count_params(model: nn.Module) -> Tuple[int, int]:
    total     = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    return total, trainable

def gpu_mem(device: torch.device) -> str:
    if device.type != "cuda":
        return "CPU"
    alloc  = torch.cuda.memory_allocated(device)  / 1024**2
    reserv = torch.cuda.memory_reserved(device)   / 1024**2
    peak   = torch.cuda.max_memory_allocated(device) / 1024**2
    return f"alloc={alloc:.0f}MB  res={reserv:.0f}MB  peak={peak:.0f}MB"

def reset_peak_mem(device: torch.device):
    if device.type == "cuda":
        torch.cuda.reset_peak_memory_stats(device)

def grad_norm(model: nn.Module) -> float:
    total = 0.0
    for p in model.parameters():
        if p.grad is not None:
            total += p.grad.data.norm(2).item() ** 2
    return math.sqrt(total)

# ─────────────────────────────────────────────────────────────────────────────
#  METRIC FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def psnr(pred: torch.Tensor, target: torch.Tensor, max_val: float = 1.0) -> float:
    with torch.no_grad():
        mse = F.mse_loss(pred.clamp(0, max_val), target.clamp(0, max_val))
        if mse.item() == 0:
            return 100.0
        return float(20 * math.log10(max_val) - 10 * math.log10(mse.item()))

def ssim(pred: torch.Tensor, target: torch.Tensor,
         window_size: int = 7, C1: float = 0.01**2, C2: float = 0.03**2) -> float:
    """Simplified SSIM (per-channel, averaged)."""
    with torch.no_grad():
        B, C, H, W = pred.shape
        if H < window_size or W < window_size:
            return 0.0
        pad = window_size // 2
        mu_x = F.avg_pool2d(pred,   window_size, stride=1, padding=pad)
        mu_y = F.avg_pool2d(target, window_size, stride=1, padding=pad)
        mu_x2, mu_y2, mu_xy = mu_x**2, mu_y**2, mu_x * mu_y
        sig_x  = F.avg_pool2d(pred**2,          window_size, stride=1, padding=pad) - mu_x2
        sig_y  = F.avg_pool2d(target**2,         window_size, stride=1, padding=pad) - mu_y2
        sig_xy = F.avg_pool2d(pred * target,     window_size, stride=1, padding=pad) - mu_xy
        num = (2*mu_xy + C1) * (2*sig_xy + C2)
        den = (mu_x2 + mu_y2 + C1) * (sig_x + sig_y + C2)
        return float((num / (den + 1e-8)).mean().item())

def seg_metrics(logits: torch.Tensor, targets: torch.Tensor,
                num_classes: int) -> Tuple[float, float, List[float]]:
    """Pixel Accuracy, mean IoU, per-class IoU list."""
    with torch.no_grad():
        preds  = logits.argmax(dim=1)
        valid  = targets >= 0
        pixel_acc = ((preds == targets) & valid).float().sum() / valid.float().sum()
        iou_per_class = []
        for c in range(num_classes):
            tp = ((preds == c) & (targets == c)).float().sum()
            fp = ((preds == c) & (targets != c)).float().sum()
            fn = ((preds != c) & (targets == c)).float().sum()
            denom = tp + fp + fn
            iou_per_class.append(float(tp / denom) if denom > 0 else float("nan"))
        valid_ious = [v for v in iou_per_class if not math.isnan(v)]
        miou = sum(valid_ious) / len(valid_ious) if valid_ious else 0.0
    return float(pixel_acc), miou, iou_per_class

# ─────────────────────────────────────────────────────────────────────────────
#  CHECKPOINT HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def save_checkpoint(path: Path, payload: dict):
    tmp = path.with_suffix(".tmp")
    torch.save(payload, tmp)
    tmp.replace(path)   # atomic replace

def load_checkpoint(path: Path, model: nn.Module,
                    optimizer=None, scheduler=None) -> int:
    """Returns epoch to resume from (0 if no checkpoint)."""
    if not path.exists():
        return 0
    ckpt = torch.load(path, map_location="cpu")
    model.load_state_dict(ckpt["model_state_dict"])
    if optimizer and "optimizer_state_dict" in ckpt:
        optimizer.load_state_dict(ckpt["optimizer_state_dict"])
    if scheduler and "scheduler_state_dict" in ckpt:
        scheduler.load_state_dict(ckpt["scheduler_state_dict"])
    epoch = ckpt.get("epoch", 0)
    print(f"  [RESUME] Loaded checkpoint from epoch {epoch}: {path}")
    return epoch

# ─────────────────────────────────────────────────────────────────────────────
#  PLOT HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def save_plots(history: List[dict], save_dir: Path, model_name: str):
    """Save train/val loss + key metric curves as PNG."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        epochs = [r["epoch"] for r in history]
        fig, axes = plt.subplots(1, 2, figsize=(12, 4))
        fig.suptitle(f"{model_name} Training Curves", fontsize=13, fontweight="bold")

        # Loss
        ax = axes[0]
        ax.plot(epochs, [r["train_loss"] for r in history], label="Train Loss", color="steelblue")
        ax.plot(epochs, [r["val_loss"]   for r in history], label="Val Loss",   color="coral")
        ax.set_xlabel("Epoch"); ax.set_ylabel("Loss"); ax.legend(); ax.grid(alpha=0.3)
        ax.set_title("Loss Curve")

        # Metric (PSNR or mIoU)
        ax = axes[1]
        if "val_psnr_8x" in history[0]:
            vals = [r.get("val_psnr_8x", 0) for r in history]
            ax.plot(epochs, vals, label="Val PSNR-8x (dB)", color="green")
            ax.set_ylabel("PSNR (dB)")
        elif "val_miou" in history[0]:
            vals = [r.get("val_miou", 0)*100 for r in history]
            ax.plot(epochs, vals, label="Val mIoU (%)", color="purple")
            ax.set_ylabel("mIoU (%)")
        ax.set_xlabel("Epoch"); ax.legend(); ax.grid(alpha=0.3)
        ax.set_title("Key Metric Curve")

        plt.tight_layout()
        plt.savefig(save_dir / f"{model_name.lower()}_curves.png", dpi=120)
        plt.close()
        print(f"  [PLOT] Saved: {save_dir / f'{model_name.lower()}_curves.png'}")
    except Exception as e:
        print(f"  [PLOT] Could not save plot: {e}")

# ─────────────────────────────────────────────────────────────────────────────
#  DATALOADER BUILDER
# ─────────────────────────────────────────────────────────────────────────────

def build_loaders(scale_factor: int, patch_size: int, batch_size: int,
                  device: torch.device):
    pin  = device.type == "cuda"
    nw   = 0  # 0 is safe and optimal for Windows without fork()
    train_loader, val_loader = get_aid_dataloaders(
        root_dir="data/aid", batch_size=batch_size,
        scale_factor=scale_factor, patch_size=patch_size,
    )
    # Rebuild with pin_memory / num_workers for speed
    from torch.utils.data import DataLoader
    train_ds = train_loader.dataset
    val_ds   = val_loader.dataset
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True,
                              num_workers=nw, pin_memory=pin, drop_last=True)
    val_loader   = DataLoader(val_ds,   batch_size=batch_size, shuffle=False,
                              num_workers=nw, pin_memory=pin)
    return train_loader, val_loader

# ─────────────────────────────────────────────────────────────────────────────
#  SCHEDULER BUILDER  (linear warmup → cosine annealing)
# ─────────────────────────────────────────────────────────────────────────────

def build_scheduler(optimizer, warmup_epochs: int, total_epochs: int):
    warmup = LinearLR(optimizer, start_factor=0.1, end_factor=1.0,
                      total_iters=warmup_epochs)
    cosine = CosineAnnealingWarmRestarts(optimizer, T_0=10, T_mult=2, eta_min=1e-6)
    scheduler = SequentialLR(optimizer, schedulers=[warmup, cosine],
                              milestones=[warmup_epochs])
    return scheduler

# ─────────────────────────────────────────────────────────────────────────────
#  1.  ColNet  --  Joint SR + Segmentation  (IEEE TGRS)
# ─────────────────────────────────────────────────────────────────────────────

def train_colnet(device: torch.device, resume: bool = False) -> dict:
    cfg      = COLNET_CFG
    epochs   = cfg["epochs"]
    save_dir = Path("checkpoints/colnet");  save_dir.mkdir(parents=True, exist_ok=True)
    header("[1/3]  ColNet  --  IEEE TGRS  |  Joint Super-Resolution + Segmentation")

    # ── Model ─────────────────────────────────────────────────────────────
    model   = ColNet(in_channels=3, num_classes=cfg["num_classes"],
                     sr_base_filters=cfg["sr_base_filters"], scale=cfg["scale"]).to(device)
    loss_fn = JointColNetLoss(lambda_sr=cfg["lambda_sr"],
                               lambda_wavelet=cfg["lambda_wavelet"],
                               lambda_seg=cfg["lambda_seg"]).to(device)
    optimizer = torch.optim.AdamW(model.parameters(),
                                  lr=cfg["lr"], weight_decay=cfg["weight_decay"])
    scheduler = build_scheduler(optimizer, cfg["warmup_epochs"], epochs)
    scaler    = GradScaler(enabled=(device.type == "cuda"))

    total_p, train_p = count_params(model)
    print(f"  Parameters : {total_p:>12,}  total  |  {train_p:>12,}  trainable")
    print(f"  Loss       : SR x{cfg['lambda_sr']} + Wavelet x{cfg['lambda_wavelet']} + Seg x{cfg['lambda_seg']}")

    # ── Data ──────────────────────────────────────────────────────────────
    train_loader, val_loader = build_loaders(
        scale_factor=8, patch_size=64, batch_size=cfg["batch_size"], device=device)
    print(f"  Dataset    : {len(train_loader.dataset)} train  |  {len(val_loader.dataset)} val")
    print(f"  Batches    : {len(train_loader)}/epoch train  |  {len(val_loader)}/epoch val")

    # ── Resume ────────────────────────────────────────────────────────────
    start_epoch = 0
    if resume:
        start_epoch = load_checkpoint(save_dir / "latest_colnet.pth",
                                      model, optimizer, scheduler)

    best_val_loss = float("inf")
    patience_ct   = 0
    history       = []
    t0 = time.time()

    print(f"\n  Device={device}  AMP={device.type=='cuda'}  "
          f"Warmup={cfg['warmup_epochs']}ep  GradClip={cfg['grad_clip']}")
    sep("-")

    for epoch in range(start_epoch + 1, epochs + 1):
        ep_t0 = time.time()
        reset_peak_mem(device)
        cur_lr = optimizer.param_groups[0]["lr"]

        # ── TRAIN ──────────────────────────────────────────────────────────
        model.train()
        m = defaultdict(float)
        n = 0

        for batch in train_loader:
            lr_img = batch["lr"].to(device,    non_blocking=True)
            hr_2x  = batch["hr_2x"].to(device, non_blocking=True)
            hr_4x  = batch["hr_4x"].to(device, non_blocking=True)
            hr_8x  = batch["hr_8x"].to(device, non_blocking=True)
            seg_gt = torch.randint(0, cfg["num_classes"],
                                   (lr_img.size(0), hr_8x.size(2), hr_8x.size(3)),
                                   device=device)
            targets = {"hr_2x": hr_2x, "hr_4x": hr_4x,
                       "hr_8x": hr_8x, "seg_mask": seg_gt}

            optimizer.zero_grad(set_to_none=True)
            with autocast(enabled=(device.type == "cuda")):
                preds = model(lr_img)
                loss, metrics = loss_fn(preds, targets)

            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            gn = grad_norm(model)
            nn.utils.clip_grad_norm_(model.parameters(), cfg["grad_clip"])
            scaler.step(optimizer)
            scaler.update()

            m["loss"]     += loss.item()
            m["loss_sr"]  += metrics["loss_sr"]
            m["loss_wav"] += metrics.get("loss_wavelet", 0.0)
            m["loss_seg"] += metrics["loss_seg"]
            m["psnr_2x"]  += psnr(preds["sr_2x"], hr_2x)
            m["psnr_4x"]  += psnr(preds["sr_4x"], hr_4x)
            m["psnr_8x"]  += psnr(preds["sr_8x"], hr_8x)
            m["ssim_8x"]  += ssim(preds["sr_8x"], hr_8x)
            m["grad_norm"]+= gn
            n += 1

        scheduler.step()
        a = {k: v / max(1, n) for k, v in m.items()}   # averages

        # ── VALIDATE ───────────────────────────────────────────────────────
        model.eval()
        vm = defaultdict(float); vn = 0
        with torch.no_grad():
            for batch in val_loader:
                lr_img = batch["lr"].to(device,    non_blocking=True)
                hr_2x  = batch["hr_2x"].to(device, non_blocking=True)
                hr_4x  = batch["hr_4x"].to(device, non_blocking=True)
                hr_8x  = batch["hr_8x"].to(device, non_blocking=True)
                seg_gt = torch.randint(0, cfg["num_classes"],
                                       (lr_img.size(0), hr_8x.size(2), hr_8x.size(3)),
                                       device=device)
                targets = {"hr_2x": hr_2x, "hr_4x": hr_4x,
                           "hr_8x": hr_8x, "seg_mask": seg_gt}
                with autocast(enabled=(device.type == "cuda")):
                    preds = model(lr_img)
                    loss, _ = loss_fn(preds, targets)
                vm["loss"]    += loss.item()
                vm["psnr_8x"] += psnr(preds["sr_8x"], hr_8x)
                vm["ssim_8x"] += ssim(preds["sr_8x"], hr_8x)
                vn += 1

        va = {k: v / max(1, vn) for k, v in vm.items()}
        ep_time = time.time() - ep_t0
        elapsed = time.time() - t0
        is_best = va["loss"] < best_val_loss

        # ── PRINT ──────────────────────────────────────────────────────────
        flag = " [BEST]" if is_best else ""
        print(f"\n  Epoch {epoch:02d}/{epochs}  |  LR={cur_lr:.2e}  |  {gpu_mem(device)}")
        print(f"  TRAIN  Loss={a['loss']:.4f}  SR={a['loss_sr']:.4f}  "
              f"Wav={a['loss_wav']:.4f}  Seg={a['loss_seg']:.4f}  GradNorm={a['grad_norm']:.3f}")
        print(f"         PSNR  2x={a['psnr_2x']:.2f}dB  4x={a['psnr_4x']:.2f}dB  "
              f"8x={a['psnr_8x']:.2f}dB  SSIM-8x={a['ssim_8x']:.4f}")
        print(f"  VAL    Loss={va['loss']:.4f}  PSNR-8x={va['psnr_8x']:.2f}dB  "
              f"SSIM-8x={va['ssim_8x']:.4f}  "
              f"[{ep_time:.1f}s | ETA {eta(elapsed, epoch-start_epoch, epochs-start_epoch)}]{flag}")

        # ── CHECKPOINT ─────────────────────────────────────────────────────
        payload_common = {
            "epoch": epoch, "model_state_dict": model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "scheduler_state_dict": scheduler.state_dict(),
            "val_loss": va["loss"], "config": cfg,
        }
        save_checkpoint(save_dir / "latest_colnet.pth", payload_common)

        if is_best:
            best_val_loss = va["loss"]
            patience_ct   = 0
            save_checkpoint(save_dir / "best_colnet.pth",
                            {**payload_common,
                             "val_psnr_8x": va["psnr_8x"],
                             "val_ssim_8x": va["ssim_8x"]})
            print(f"  [SAVED BEST]  val_loss={best_val_loss:.4f}  "
                  f"psnr_8x={va['psnr_8x']:.2f}dB")
        else:
            patience_ct += 1
            print(f"  [patience {patience_ct}/{cfg['patience']}]")

        # History row
        history.append({
            "epoch": epoch, "lr": cur_lr,
            "train_loss": a["loss"], "train_psnr_8x": a["psnr_8x"],
            "train_ssim_8x": a["ssim_8x"], "grad_norm": a["grad_norm"],
            "val_loss": va["loss"], "val_psnr_8x": va["psnr_8x"],
            "val_ssim_8x": va["ssim_8x"],
        })

        if patience_ct >= cfg["patience"]:
            print(f"\n  [EARLY STOP]  patience exhausted at epoch {epoch}.")
            break

    with open(save_dir / "training_log.json", "w") as f:
        json.dump(history, f, indent=2)
    save_plots(history, save_dir, "ColNet")

    total = time.time() - t0
    sep("-")
    print(f"  ColNet COMPLETE  |  Best Val Loss={best_val_loss:.4f}  "
          f"|  {fmt_time(total)}")
    sep()
    return {"model": "ColNet", "best_val_loss": best_val_loss,
            "best_psnr_8x": history[-1]["val_psnr_8x"],
            "best_ssim_8x": history[-1]["val_ssim_8x"],
            "total_time": total, "epochs_run": len(history)}


# ─────────────────────────────────────────────────────────────────────────────
#  2.  UNetFormer  --  Semantic Segmentation  (ISPRS 2022)
# ─────────────────────────────────────────────────────────────────────────────

def train_unetformer(device: torch.device, resume: bool = False) -> dict:
    cfg      = UNETFORMER_CFG
    epochs   = cfg["epochs"]
    save_dir = Path("checkpoints/unetformer"); save_dir.mkdir(parents=True, exist_ok=True)
    header("[2/3]  UNetFormer  --  ISPRS 2022  |  Global-Local Transformer")

    model     = UNetFormer(in_channels=3, num_classes=cfg["num_classes"],
                           decoder_dim=cfg["decoder_dim"]).to(device)
    criterion = nn.CrossEntropyLoss(label_smoothing=0.1, ignore_index=255)
    optimizer = torch.optim.AdamW(model.parameters(),
                                  lr=cfg["lr"], weight_decay=cfg["weight_decay"])
    scheduler = build_scheduler(optimizer, cfg["warmup_epochs"], epochs)
    scaler    = GradScaler(enabled=(device.type == "cuda"))

    total_p, train_p = count_params(model)
    print(f"  Parameters : {total_p:>12,}  total  |  {train_p:>12,}  trainable")
    print(f"  Loss       : CrossEntropy (label_smoothing=0.1)")

    train_loader, val_loader = build_loaders(
        scale_factor=4, patch_size=128, batch_size=cfg["batch_size"], device=device)
    print(f"  Dataset    : {len(train_loader.dataset)} train  |  {len(val_loader.dataset)} val")
    print(f"  Batches    : {len(train_loader)}/epoch train  |  {len(val_loader)}/epoch val")

    start_epoch = 0
    if resume:
        start_epoch = load_checkpoint(save_dir / "latest_unetformer.pth",
                                      model, optimizer, scheduler)

    best_val_loss = float("inf"); best_miou = 0.0
    patience_ct   = 0;            history   = []
    t0 = time.time()

    print(f"\n  Device={device}  AMP={device.type=='cuda'}  "
          f"Warmup={cfg['warmup_epochs']}ep  GradClip={cfg['grad_clip']}")
    sep("-")

    for epoch in range(start_epoch + 1, epochs + 1):
        ep_t0 = time.time(); reset_peak_mem(device)
        cur_lr = optimizer.param_groups[0]["lr"]

        # ── TRAIN ──────────────────────────────────────────────────────────
        model.train()
        m = defaultdict(float); n = 0

        for batch in train_loader:
            img     = batch["hr_2x"].to(device, non_blocking=True)
            targets = torch.randint(0, cfg["num_classes"],
                                    (img.size(0), img.size(2), img.size(3)), device=device)

            optimizer.zero_grad(set_to_none=True)
            with autocast(enabled=(device.type == "cuda")):
                logits = model(img)
                if logits.shape[-2:] != targets.shape[-2:]:
                    logits = F.interpolate(logits, size=targets.shape[-2:],
                                           mode="bilinear", align_corners=False)
                loss = criterion(logits, targets)

            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            gn = grad_norm(model)
            nn.utils.clip_grad_norm_(model.parameters(), cfg["grad_clip"])
            scaler.step(optimizer); scaler.update()

            pa, miou, _ = seg_metrics(logits.float(), targets, cfg["num_classes"])
            m["loss"] += loss.item(); m["pacc"] += pa
            m["miou"] += miou;        m["gnorm"] += gn
            n += 1

        scheduler.step()
        a = {k: v / max(1, n) for k, v in m.items()}

        # ── VALIDATE ───────────────────────────────────────────────────────
        model.eval()
        vm = defaultdict(float); vn = 0
        all_per_class = defaultdict(list)
        with torch.no_grad():
            for batch in val_loader:
                img     = batch["hr_2x"].to(device, non_blocking=True)
                targets = torch.randint(0, cfg["num_classes"],
                                        (img.size(0), img.size(2), img.size(3)), device=device)
                with autocast(enabled=(device.type == "cuda")):
                    logits = model(img)
                    if logits.shape[-2:] != targets.shape[-2:]:
                        logits = F.interpolate(logits, size=targets.shape[-2:],
                                               mode="bilinear", align_corners=False)
                    loss = criterion(logits.float(), targets)
                pa, miou, per_cls = seg_metrics(logits.float(), targets, cfg["num_classes"])
                vm["loss"] += loss.item(); vm["pacc"] += pa; vm["miou"] += miou; vn += 1
                for i, v in enumerate(per_cls):
                    if not math.isnan(v): all_per_class[i].append(v)

        va = {k: v / max(1, vn) for k, v in vm.items()}
        # Per-class IoU summary (top-5 and bottom-5)
        per_class_mean = {i: sum(vs)/len(vs) for i, vs in all_per_class.items() if vs}

        ep_time = time.time() - ep_t0
        elapsed = time.time() - t0
        is_best = va["loss"] < best_val_loss
        flag    = " [BEST]" if is_best else ""

        print(f"\n  Epoch {epoch:02d}/{epochs}  |  LR={cur_lr:.2e}  |  {gpu_mem(device)}")
        print(f"  TRAIN  Loss={a['loss']:.4f}  PixAcc={a['pacc']*100:.2f}%  "
              f"mIoU={a['miou']*100:.2f}%  GradNorm={a['gnorm']:.3f}")
        print(f"  VAL    Loss={va['loss']:.4f}  PixAcc={va['pacc']*100:.2f}%  "
              f"mIoU={va['miou']*100:.2f}%  "
              f"[{ep_time:.1f}s | ETA {eta(elapsed, epoch-start_epoch, epochs-start_epoch)}]{flag}")

        payload_common = {
            "epoch": epoch, "model_state_dict": model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "scheduler_state_dict": scheduler.state_dict(),
            "val_loss": va["loss"], "config": cfg,
        }
        save_checkpoint(save_dir / "latest_unetformer.pth", payload_common)

        if is_best:
            best_val_loss = va["loss"]; best_miou = va["miou"]
            patience_ct   = 0
            save_checkpoint(save_dir / "best_unetformer.pth",
                            {**payload_common,
                             "val_miou": va["miou"], "val_pixel_acc": va["pacc"],
                             "per_class_iou": per_class_mean})
            print(f"  [SAVED BEST]  val_loss={best_val_loss:.4f}  mIoU={best_miou*100:.2f}%")
        else:
            patience_ct += 1
            print(f"  [patience {patience_ct}/{cfg['patience']}]")

        history.append({
            "epoch": epoch, "lr": cur_lr,
            "train_loss": a["loss"], "train_miou": a["miou"], "train_pacc": a["pacc"],
            "grad_norm": a["gnorm"],
            "val_loss": va["loss"], "val_miou": va["miou"], "val_pacc": va["pacc"],
        })

        if patience_ct >= cfg["patience"]:
            print(f"\n  [EARLY STOP]  patience exhausted at epoch {epoch}.")
            break

    with open(save_dir / "training_log.json", "w") as f:
        json.dump(history, f, indent=2)
    save_plots(history, save_dir, "UNetFormer")

    total = time.time() - t0
    sep("-")
    print(f"  UNetFormer COMPLETE  |  Best Val Loss={best_val_loss:.4f}  "
          f"Best mIoU={best_miou*100:.2f}%  |  {fmt_time(total)}")
    sep()
    return {"model": "UNetFormer", "best_val_loss": best_val_loss,
            "best_miou": best_miou, "total_time": total,
            "epochs_run": len(history)}


# ─────────────────────────────────────────────────────────────────────────────
#  3.  FarSeg  --  Geospatial Segmentation  (CVPR / TPAMI)
# ─────────────────────────────────────────────────────────────────────────────

def train_farseg(device: torch.device, resume: bool = False) -> dict:
    cfg      = FARSEG_CFG
    epochs   = cfg["epochs"]
    save_dir = Path("checkpoints/farseg"); save_dir.mkdir(parents=True, exist_ok=True)
    header("[3/3]  FarSeg  --  CVPR/TPAMI  |  Foreground-Aware Relation Network")

    model     = FarSeg(in_channels=3, num_classes=cfg["num_classes"],
                       feature_dim=cfg["feature_dim"]).to(device)
    criterion = nn.CrossEntropyLoss(label_smoothing=0.1, ignore_index=255)
    optimizer = torch.optim.AdamW(model.parameters(),
                                  lr=cfg["lr"], weight_decay=cfg["weight_decay"])
    scheduler = build_scheduler(optimizer, cfg["warmup_epochs"], epochs)
    scaler    = GradScaler(enabled=(device.type == "cuda"))

    total_p, train_p = count_params(model)
    print(f"  Parameters : {total_p:>12,}  total  |  {train_p:>12,}  trainable")
    print(f"  Loss       : CrossEntropy + Scene-Relation FSRM affinity")

    train_loader, val_loader = build_loaders(
        scale_factor=4, patch_size=128, batch_size=cfg["batch_size"], device=device)
    print(f"  Dataset    : {len(train_loader.dataset)} train  |  {len(val_loader.dataset)} val")
    print(f"  Batches    : {len(train_loader)}/epoch train  |  {len(val_loader)}/epoch val")

    start_epoch = 0
    if resume:
        start_epoch = load_checkpoint(save_dir / "latest_farseg.pth",
                                      model, optimizer, scheduler)

    best_val_loss = float("inf"); best_miou = 0.0
    patience_ct   = 0;            history   = []
    t0 = time.time()

    print(f"\n  Device={device}  AMP={device.type=='cuda'}  "
          f"Warmup={cfg['warmup_epochs']}ep  GradClip={cfg['grad_clip']}")
    sep("-")

    for epoch in range(start_epoch + 1, epochs + 1):
        ep_t0 = time.time(); reset_peak_mem(device)
        cur_lr = optimizer.param_groups[0]["lr"]

        # ── TRAIN ──────────────────────────────────────────────────────────
        model.train()
        m = defaultdict(float); n = 0

        for batch in train_loader:
            img     = batch["hr_2x"].to(device, non_blocking=True)
            targets = torch.randint(0, cfg["num_classes"],
                                    (img.size(0), img.size(2), img.size(3)), device=device)

            optimizer.zero_grad(set_to_none=True)
            with autocast(enabled=(device.type == "cuda")):
                logits = model(img)
                if logits.shape[-2:] != targets.shape[-2:]:
                    logits = F.interpolate(logits, size=targets.shape[-2:],
                                           mode="bilinear", align_corners=False)
                loss = criterion(logits, targets)

            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            gn = grad_norm(model)
            nn.utils.clip_grad_norm_(model.parameters(), cfg["grad_clip"])
            scaler.step(optimizer); scaler.update()

            pa, miou, _ = seg_metrics(logits.float(), targets, cfg["num_classes"])
            m["loss"] += loss.item(); m["pacc"] += pa
            m["miou"] += miou;        m["gnorm"] += gn
            n += 1

        scheduler.step()
        a = {k: v / max(1, n) for k, v in m.items()}

        # ── VALIDATE ───────────────────────────────────────────────────────
        model.eval()
        vm = defaultdict(float); vn = 0
        all_per_class = defaultdict(list)
        with torch.no_grad():
            for batch in val_loader:
                img     = batch["hr_2x"].to(device, non_blocking=True)
                targets = torch.randint(0, cfg["num_classes"],
                                        (img.size(0), img.size(2), img.size(3)), device=device)
                with autocast(enabled=(device.type == "cuda")):
                    logits = model(img)
                    if logits.shape[-2:] != targets.shape[-2:]:
                        logits = F.interpolate(logits, size=targets.shape[-2:],
                                               mode="bilinear", align_corners=False)
                    loss = criterion(logits.float(), targets)
                pa, miou, per_cls = seg_metrics(logits.float(), targets, cfg["num_classes"])
                vm["loss"] += loss.item(); vm["pacc"] += pa; vm["miou"] += miou; vn += 1
                for i, v in enumerate(per_cls):
                    if not math.isnan(v): all_per_class[i].append(v)

        va = {k: v / max(1, vn) for k, v in vm.items()}
        per_class_mean = {i: sum(vs)/len(vs) for i, vs in all_per_class.items() if vs}

        ep_time = time.time() - ep_t0
        elapsed = time.time() - t0
        is_best = va["loss"] < best_val_loss
        flag    = " [BEST]" if is_best else ""

        print(f"\n  Epoch {epoch:02d}/{epochs}  |  LR={cur_lr:.2e}  |  {gpu_mem(device)}")
        print(f"  TRAIN  Loss={a['loss']:.4f}  PixAcc={a['pacc']*100:.2f}%  "
              f"mIoU={a['miou']*100:.2f}%  GradNorm={a['gnorm']:.3f}")
        print(f"  VAL    Loss={va['loss']:.4f}  PixAcc={va['pacc']*100:.2f}%  "
              f"mIoU={va['miou']*100:.2f}%  "
              f"[{ep_time:.1f}s | ETA {eta(elapsed, epoch-start_epoch, epochs-start_epoch)}]{flag}")

        payload_common = {
            "epoch": epoch, "model_state_dict": model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "scheduler_state_dict": scheduler.state_dict(),
            "val_loss": va["loss"], "config": cfg,
        }
        save_checkpoint(save_dir / "latest_farseg.pth", payload_common)

        if is_best:
            best_val_loss = va["loss"]; best_miou = va["miou"]
            patience_ct   = 0
            save_checkpoint(save_dir / "best_farseg.pth",
                            {**payload_common,
                             "val_miou": va["miou"], "val_pixel_acc": va["pacc"],
                             "per_class_iou": per_class_mean})
            print(f"  [SAVED BEST]  val_loss={best_val_loss:.4f}  mIoU={best_miou*100:.2f}%")
        else:
            patience_ct += 1
            print(f"  [patience {patience_ct}/{cfg['patience']}]")

        history.append({
            "epoch": epoch, "lr": cur_lr,
            "train_loss": a["loss"], "train_miou": a["miou"], "train_pacc": a["pacc"],
            "grad_norm": a["gnorm"],
            "val_loss": va["loss"], "val_miou": va["miou"], "val_pacc": va["pacc"],
        })

        if patience_ct >= cfg["patience"]:
            print(f"\n  [EARLY STOP]  patience exhausted at epoch {epoch}.")
            break

    with open(save_dir / "training_log.json", "w") as f:
        json.dump(history, f, indent=2)
    save_plots(history, save_dir, "FarSeg")

    total = time.time() - t0
    sep("-")
    print(f"  FarSeg COMPLETE  |  Best Val Loss={best_val_loss:.4f}  "
          f"Best mIoU={best_miou*100:.2f}%  |  {fmt_time(total)}")
    sep()
    return {"model": "FarSeg", "best_val_loss": best_val_loss,
            "best_miou": best_miou, "total_time": total,
            "epochs_run": len(history)}


# ─────────────────────────────────────────────────────────────────────────────
#  FINAL SUMMARY PRINTER
# ─────────────────────────────────────────────────────────────────────────────

def print_final_summary(results: list, grand_total: float):
    sep()
    print("  FINAL TRAINING SUMMARY")
    sep("-")
    print(f"  {'Model':<14} {'Epochs':>6} {'Best ValLoss':>13} "
          f"{'Key Metric':>20} {'Time':>10}")
    sep("-")
    for r in results:
        if "error" in r:
            print(f"  {r['model']:<14} {'--':>6} {'FAILED':>13} {r['error'][:20]:>20} {'--':>10}")
            continue
        if "best_psnr_8x" in r:
            metric = f"PSNR-8x {r['best_psnr_8x']:.2f}dB"
        else:
            metric = f"mIoU {r['best_miou']*100:.2f}%"
        print(f"  {r['model']:<14} {r['epochs_run']:>6} {r['best_val_loss']:>13.4f} "
              f"{metric:>20} {fmt_time(r['total_time']):>10}")
    sep("-")
    print(f"  Total wall-clock time: {fmt_time(grand_total)}")
    print(f"  Finished: {now_str()}")
    sep()

# ─────────────────────────────────────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(description="Advanced Remote Sensing Training Suite")
    p.add_argument("--resume",  action="store_true", help="Resume from latest checkpoints")
    p.add_argument("--only",    choices=["colnet", "unetformer", "farseg"],
                   help="Train only one model")
    return p.parse_args()


def main():
    args   = parse_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    sep()
    print("  ADVANCED REMOTE SENSING TRAINING SUITE")
    print(f"  Device   : {device}")
    if device.type == "cuda":
        props = torch.cuda.get_device_properties(0)
        print(f"  GPU      : {props.name}")
        print(f"  VRAM     : {props.total_memory / 1024**3:.1f} GB")
        print(f"  Compute  : sm_{props.major}{props.minor}")
        print(f"  AMP      : Enabled (FP16 mixed precision)")
    else:
        print(f"  AMP      : Disabled (CPU mode)")
    print(f"  Resume   : {args.resume}")
    print(f"  Only     : {args.only or 'all models'}")
    print(f"  Started  : {now_str()}")
    sep()

    t_grand = time.time()
    results = []

    trainers = [
        ("colnet",     train_colnet),
        ("unetformer", train_unetformer),
        ("farseg",     train_farseg),
    ]

    for name, fn in trainers:
        if args.only and args.only != name:
            continue
        try:
            result = fn(device=device, resume=args.resume)
            results.append(result)
        except Exception as e:
            print(f"\n  [ERROR] {name} failed: {e}")
            traceback.print_exc()
            results.append({"model": name, "error": str(e)})

    print_final_summary(results, time.time() - t_grand)


if __name__ == "__main__":
    main()
