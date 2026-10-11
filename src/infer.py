"""
Inference engine — tile, predict, and stitch for arbitrary GeoTIFFs.

Takes a trained model and a large GeoTIFF, runs tiled inference,
and writes a classified GeoTIFF preserving the original CRS and transform.

Usage:
    python src/infer.py --config configs/phase4_aoi.yaml
"""

import argparse
import os
import sys

import numpy as np
import torch
import yaml
from tqdm import tqdm

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import rasterio
    from rasterio.windows import Window
except ImportError:
    raise ImportError("rasterio required: conda install -c conda-forge rasterio")


def load_config(config_path: str) -> dict:
    """Load YAML config."""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)





def create_feather_weights(tile_size: int, overlap: int) -> np.ndarray:
    """Generate a 2D linear feather weight matrix for seamless tile stitching."""
    if overlap <= 0:
        return np.ones((tile_size, tile_size), dtype=np.float32)
    wx = np.ones(tile_size, dtype=np.float32)
    wy = np.ones(tile_size, dtype=np.float32)
    ramp = np.linspace(0.05, 1.0, overlap, dtype=np.float32)
    wx[:overlap] = ramp
    wx[-overlap:] = ramp[::-1]
    wy[:overlap] = ramp
    wy[-overlap:] = ramp[::-1]
    return np.outer(wy, wx)


def run_inference_on_tif(
    model: torch.nn.Module,
    in_path: str,
    out_path: str,
    tile_size: int = 512,
    overlap: int = 32,
    batch_size: int = 4,
    device: str = "cuda",
    reflectance_scale: float = 10000.0,
    use_indices: bool = False,
    band_order: tuple = None,
    num_classes: int = 11,
):
    """
    Run tiled inference on a large GeoTIFF with distance-weighted overlap blending.
    """
    model.eval()
    stride = tile_size - overlap if overlap < tile_size else tile_size

    with rasterio.open(in_path) as src:
        profile = src.profile.copy()
        H, W = src.height, src.width
        num_bands = src.count

        print(f"Input: {in_path}")
        print(f"  Size: {W}×{H} ({num_bands} bands)")

        # Accumulator arrays for seamless blending
        accum_probs = np.zeros((num_classes, H, W), dtype=np.float32)
        accum_weights = np.zeros((H, W), dtype=np.float32)
        tile_weights = create_feather_weights(tile_size, overlap)

        # Build tile grid
        tiles = []
        for y in range(0, H, stride):
            for x in range(0, W, stride):
                tile_h = min(tile_size, H - y)
                tile_w = min(tile_size, W - x)
                tiles.append((x, y, tile_w, tile_h))

        print(f"  Tiles: {len(tiles)} ({tile_size}×{tile_size}, overlap={overlap})")

        # Process tiles in batches
        for batch_start in tqdm(range(0, len(tiles), batch_size), desc="Inference"):
            batch_tiles = tiles[batch_start:batch_start + batch_size]
            batch_tensors = []
            batch_meta = []

            for x, y, tw, th in batch_tiles:
                win = Window(x, y, tw, th)
                tile = src.read(window=win).astype(np.float32) / reflectance_scale

                # Pad if needed
                if tile.shape[1] < tile_size or tile.shape[2] < tile_size:
                    padded = np.zeros((tile.shape[0], tile_size, tile_size), dtype=np.float32)
                    padded[:, :tile.shape[1], :tile.shape[2]] = tile
                    tile = padded

                batch_tensors.append(torch.from_numpy(tile))
                batch_meta.append((x, y, tw, th))

            # Stack into batch
            batch_input = torch.stack(batch_tensors).to(device)

            # Optionally append spectral indices
            if use_indices and band_order:
                from src.transforms.band_math import build_multispectral_input_torch
                batch_input = build_multispectral_input_torch(batch_input, tuple(band_order))

            # Inference with softmax probabilities for blending
            with torch.no_grad():
                logits = model(batch_input)
                probs = torch.softmax(logits, dim=1).cpu().numpy()

            # Blend predictions into canvas
            for i, (x, y, tw, th) in enumerate(batch_meta):
                w_sub = tile_weights[:th, :tw]
                accum_probs[:, y:y + th, x:x + tw] += probs[i, :, :th, :tw] * w_sub[None, ...]
                accum_weights[y:y + th, x:x + tw] += w_sub

    # Normalize accumulated probabilities and compute argmax
    valid_mask = accum_weights > 0
    accum_weights = np.maximum(accum_weights, 1e-6)
    out = (accum_probs / accum_weights[None, ...]).argmax(axis=0).astype(np.uint8)
    out[~valid_mask] = 255  # nodata

    # Write output GeoTIFF
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    profile.update(count=1, dtype="uint8", nodata=255)

    with rasterio.open(out_path, "w", **profile) as dst:
        dst.write(out, 1)

    print(f"\nOutput: {out_path}")
    print(f"  Classes found: {np.unique(out[out != 255])}")


def main():
    parser = argparse.ArgumentParser(description="GeoSeg Inference")
    parser.add_argument("--config", type=str, default=None, help="Path to YAML config file")
    parser.add_argument("--checkpoint", type=str, default=None, help="Path to model checkpoint")
    parser.add_argument("--input", type=str, default=None, help="Path to input GeoTIFF")
    parser.add_argument("--output", type=str, default=None, help="Path to output classified GeoTIFF")
    parser.add_argument("--tile-size", type=int, default=512, help="Tile size (px)")
    parser.add_argument("--overlap", type=int, default=32, help="Tile overlap stride (px)")
    parser.add_argument("--batch-size", type=int, default=4, help="Inference batch size")
    parser.add_argument("--device", type=str, default=None, help="Device (cuda or cpu)")
    parser.add_argument("--use-indices", action="store_true", help="Append computed spectral indices")
    parser.add_argument("--num-classes", type=int, default=11, help="Number of segmentation classes")
    args = parser.parse_args()

    if args.config:
        config = load_config(args.config)
        infer_config = config.get("inference", {})
        model_config = config.get("model", {"name": "unet", "encoder": "resnet34", "in_channels": 16 if infer_config.get("use_indices", False) else 13, "num_classes": 11})
        in_path = args.input or infer_config.get("input_tif")
        out_path = args.output or infer_config.get("output_tif")
        ckpt_path = args.checkpoint or infer_config.get("model_checkpoint")
        tile_size = args.tile_size if args.tile_size != 512 else infer_config.get("tile_size", 512)
        overlap = args.overlap if args.overlap != 32 else infer_config.get("overlap", 32)
        batch_size = args.batch_size if args.batch_size != 4 else infer_config.get("batch_size", 4)
        use_indices = args.use_indices or infer_config.get("use_indices", False)
        band_order = infer_config.get("band_order", ["B01", "B02", "B03", "B04", "B05", "B06", "B07", "B08", "B8A", "B09", "B10", "B11", "B12"])
        num_classes = model_config.get("num_classes", 11)
        device_str = args.device or infer_config.get("device", "cuda" if torch.cuda.is_available() else "cpu")
    else:
        if not args.input or not args.output:
            parser.error("Either --config or both --input and --output are required.")
        in_path = args.input
        out_path = args.output
        ckpt_path = args.checkpoint or "outputs/checkpoints/phase3/best_model.pth"
        tile_size = args.tile_size
        overlap = args.overlap
        batch_size = args.batch_size
        use_indices = args.use_indices
        band_order = ["B01", "B02", "B03", "B04", "B05", "B06", "B07", "B08", "B8A", "B09", "B10", "B11", "B12"]
        num_classes = args.num_classes
        device_str = args.device or ("cuda" if torch.cuda.is_available() else "cpu")
        model_config = {
            "name": "unet",
            "encoder": "resnet34",
            "in_channels": 16 if use_indices else 13,
            "num_classes": num_classes,
        }

    device = torch.device(device_str if (device_str == "cpu" or torch.cuda.is_available()) else "cpu")
    print(f"Device: {device}")

    # Build and load model
    from src.models.segmentation import build_segmentation_model
    from src.utils.checkpoint import load_checkpoint

    model = build_segmentation_model(model_config).to(device)
    if ckpt_path and os.path.exists(ckpt_path):
        load_checkpoint(ckpt_path, model, device=str(device))
        print(f"Loaded checkpoint: {ckpt_path}")
    else:
        print(f"[Notice] Checkpoint '{ckpt_path}' not found on disk. Initializing model for inference demonstration.")


    model.eval()

    run_inference_on_tif(
        model=model,
        in_path=in_path,
        out_path=out_path,
        tile_size=tile_size,
        overlap=overlap,
        batch_size=batch_size,
        device=str(device),
        use_indices=use_indices,
        band_order=band_order,
        num_classes=num_classes,
    )

    print("\n[OK] Inference complete. Output saved.")


if __name__ == "__main__":
    main()
