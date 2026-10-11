"""
Joint Super-Resolution and Semantic Segmentation (ColNet) Training Script.
Trains ColNet end-to-end with multi-task joint loss and wavelet frequency constraints.
"""

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Dict

import torch
import torch.nn as nn
from tqdm import tqdm

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.colnet import ColNet, JointColNetLoss
from src.datasets.aid import get_aid_dataloaders


def parse_args():
    parser = argparse.ArgumentParser(description="Train ColNet Joint SR-Segmentation")
    parser.add_argument("--epochs", type=int, default=10, help="Number of epochs")
    parser.add_argument("--batch-size", type=int, default=4, help="Batch size")
    parser.add_argument("--lr", type=float, default=1e-4, help="Learning rate")
    parser.add_argument("--max-steps", type=int, default=None, help="Max steps per epoch")
    parser.add_argument("--save-dir", type=str, default="checkpoints/colnet", help="Save directory")
    return parser.parse_args()


def main():
    args = parse_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Executing ColNet Joint Training on: {device}")

    save_dir = Path(args.save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)

    # 1. Model & Loss
    model = ColNet(in_channels=3, num_classes=30, sr_base_filters=64, scale=8).to(device)
    loss_fn = JointColNetLoss(lambda_sr=1.0, lambda_wavelet=0.1, lambda_seg=1.0)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)

    # 2. Dataloaders
    train_loader, val_loader = get_aid_dataloaders(
        root_dir="data/aid",
        batch_size=args.batch_size,
        scale_factor=8,
        patch_size=64,
        num_workers=0,
    )
    print(f"ColNet initialized ({sum(p.numel() for p in model.parameters()):,} parameters).")
    print(f"Loaded dataset: {len(train_loader.dataset)} training samples.\n")

    for epoch in range(1, args.epochs + 1):
        model.train()
        epoch_loss = 0.0
        steps = 0

        pbar = tqdm(train_loader, desc=f"ColNet Epoch {epoch}/{args.epochs}", leave=False)
        for batch_idx, batch in enumerate(pbar):
            if args.max_steps and batch_idx >= args.max_steps:
                break

            lr = batch["lr"].to(device)
            targets = {
                "hr_2x": batch["hr_2x"].to(device),
                "hr_4x": batch["hr_4x"].to(device),
                "hr_8x": batch["hr_8x"].to(device),
                # Pseudo segmentation mask mapped to 8x resolution
                "seg_mask": torch.randint(0, 30, (lr.size(0), 512, 512), device=device),
            }

            optimizer.zero_grad()
            preds = model(lr)
            loss, metrics = loss_fn(preds, targets)
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item()
            steps += 1

        avg_loss = epoch_loss / max(1, steps)
        print(f"Epoch {epoch:03d}/{args.epochs:03d} | Total Loss: {avg_loss:.4f} | SR: {metrics['loss_sr']:.4f} | Wavelet: {metrics['loss_wavelet']:.4f} | Seg: {metrics['loss_seg']:.4f}")

    ckpt_path = save_dir / "colnet_model.pth"
    torch.save({"model_state_dict": model.state_dict(), "epochs": args.epochs}, ckpt_path)
    print(f"\n[ColNet Training Complete] Checkpoint saved to: {ckpt_path}")


if __name__ == "__main__":
    main()
