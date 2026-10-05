# Satellite Land Cover Segmentation — Implementation Plan

This follows the build order you laid out: EuroSAT → real segmentation → multispectral → your own AOI. Each phase is meant to run before you move to the next — don't skip to Phase 3 with a broken Phase 1 pipeline.

---

## 0. Environment Setup

```bash
# conda is easier here because GDAL has painful binary deps
conda create -n geoseg python=3.11 -y
conda activate geoseg

conda install -c conda-forge gdal rasterio -y

pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
pip install torchgeo segmentation-models-pytorch pytorch-lightning torchmetrics
pip install earthengine-api geemap
pip install kornia albumentations tensorboard
```

Sanity check:

```python
import torch, torchgeo, rasterio, segmentation_models_pytorch as smp
print(torch.cuda.is_available())
print(torchgeo.__version__, smp.__version__)
```

---

## Phase 1 — EuroSAT baseline classifier (pipeline validation)

Goal here is **not** accuracy — it's proving the environment, dataloaders, and training loop all work end to end before you add segmentation complexity.

```python
# phase1_eurosat.py
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchgeo.datasets import EuroSAT
from torchgeo.transforms import AugmentationSequential
import kornia.augmentation as K

train_transforms = AugmentationSequential(
    K.RandomHorizontalFlip(p=0.5),
    K.RandomVerticalFlip(p=0.5),
    K.Normalize(mean=torch.zeros(13), std=torch.full((13,), 10000.0)),  # S2 reflectance scale
    data_keys=["image"],
)

train_ds = EuroSAT(root="data/eurosat", split="train", download=True, transforms=train_transforms)
val_ds   = EuroSAT(root="data/eurosat", split="val",   download=True)

train_loader = DataLoader(train_ds, batch_size=64, shuffle=True, num_workers=4)
val_loader   = DataLoader(val_ds,   batch_size=64, shuffle=False, num_workers=4)

class SimpleCNN(nn.Module):
    def __init__(self, in_channels=13, num_classes=10):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(in_channels, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(32, 64, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(64, 128, 3, padding=1), nn.ReLU(), nn.AdaptiveAvgPool2d(1),
        )
        self.fc = nn.Linear(128, num_classes)

    def forward(self, x):
        x = self.net(x)
        return self.fc(x.flatten(1))

model = SimpleCNN().cuda()
opt = torch.optim.Adam(model.parameters(), lr=1e-3)
loss_fn = nn.CrossEntropyLoss()

for epoch in range(10):
    model.train()
    for batch in train_loader:
        x, y = batch["image"].cuda().float(), batch["label"].cuda()
        opt.zero_grad()
        loss = loss_fn(model(x), y)
        loss.backward()
        opt.step()

    model.eval()
    correct, total = 0, 0
    with torch.no_grad():
        for batch in val_loader:
            x, y = batch["image"].cuda().float(), batch["label"].cuda()
            pred = model(x).argmax(1)
            correct += (pred == y).sum().item()
            total += y.size(0)
    print(f"epoch {epoch}  val_acc={correct/total:.3f}")
```

**Exit criteria for Phase 1:** validation accuracy climbing above ~85-90% (EuroSAT is an easy dataset — if you're not there, the bug is in your pipeline, not your model).

---

## Phase 2 — Real segmentation with U-Net

Swap the classification head for pixel-wise prediction. Use `segmentation-models-pytorch` (`smp`) rather than hand-rolling U-Net — it gives you encoder choice, pretrained backbones, and DeepLabv3+ for free.

DeepGlobe (RGB, 7 classes) is the easiest place to prove the segmentation architecture works, since you don't have to deal with multispectral stacking yet. Get the data from Kaggle (`balraj98/deepglobe-land-cover-classification-dataset`) since the original DeepGlobe CVPR18 portal is defunct.

```python
# phase2_unet.py
import segmentation_models_pytorch as smp
import torch, torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import rasterio
import numpy as np
from pathlib import Path

class DeepGlobeDataset(Dataset):
    """Expects paired *_sat.jpg / *_mask.png tiles as downloaded from Kaggle."""
    def __init__(self, root, split="train", tile_size=512):
        self.root = Path(root)
        self.ids = sorted({p.stem.replace("_sat", "") for p in (self.root / split).glob("*_sat.jpg")})
        self.split = split
        self.tile_size = tile_size

    def __len__(self):
        return len(self.ids)

    def __getitem__(self, idx):
        img_id = self.ids[idx]
        img_path = self.root / self.split / f"{img_id}_sat.jpg"
        mask_path = self.root / self.split / f"{img_id}_mask.png"

        with rasterio.open(img_path) as src:
            img = src.read().astype(np.float32) / 255.0  # C,H,W
        with rasterio.open(mask_path) as src:
            mask = src.read(1).astype(np.int64)          # H,W, already class-indexed

        return torch.from_numpy(img), torch.from_numpy(mask)

train_ds = DeepGlobeDataset("data/deepglobe", split="train")
train_loader = DataLoader(train_ds, batch_size=8, shuffle=True, num_workers=4)

model = smp.Unet(
    encoder_name="resnet34",
    encoder_weights="imagenet",   # fine here — 3-channel RGB input
    in_channels=3,
    classes=7,
).cuda()

loss_fn = smp.losses.DiceLoss(mode="multiclass") + nn.CrossEntropyLoss()
opt = torch.optim.AdamW(model.parameters(), lr=3e-4)

for epoch in range(20):
    model.train()
    for imgs, masks in train_loader:
        imgs, masks = imgs.cuda(), masks.cuda()
        opt.zero_grad()
        out = model(imgs)
        loss = loss_fn(out, masks)
        loss.backward()
        opt.step()
    print(f"epoch {epoch} loss={loss.item():.4f}")
```

Track **mean IoU**, not accuracy — accuracy is misleading on segmentation because background/dominant classes dwarf everything else:

```python
from torchmetrics import JaccardIndex

iou_metric = JaccardIndex(task="multiclass", num_classes=7).cuda()

model.eval()
with torch.no_grad():
    for imgs, masks in val_loader:
        imgs, masks = imgs.cuda(), masks.cuda()
        preds = model(imgs).argmax(1)
        iou_metric.update(preds, masks)
print("mIoU:", iou_metric.compute().item())
```

**Exit criteria for Phase 2:** mIoU meaningfully above a naive "predict most common class" baseline, and predicted masks visually resemble the ground truth when plotted.

---

## Phase 3 — Go multispectral (all 13 Sentinel-2 bands + band math)

This is the step that actually earns "multispectral" as a claim. Two changes: (1) the model's first conv layer needs to accept 13 channels instead of 3, (2) you compute spectral indices (NDVI, NDWI, NDBI) as extra channels or at least as sanity-check visualizations.

### 3.1 — Expand a pretrained encoder from 3→N channels

Don't throw away ImageNet pretraining just because you added bands — replicate/average the RGB filters into the new channels so early training isn't starting from scratch:

```python
import torch
import segmentation_models_pytorch as smp

def expand_first_conv(model, new_in_channels=13):
    old_conv = model.encoder.conv1  # resnet-style stem; check attribute name per encoder
    new_conv = torch.nn.Conv2d(
        new_in_channels, old_conv.out_channels,
        kernel_size=old_conv.kernel_size, stride=old_conv.stride,
        padding=old_conv.padding, bias=old_conv.bias is not None,
    )
    with torch.no_grad():
        # tile the pretrained RGB weights across the new channels, then rescale
        mean_weight = old_conv.weight.mean(dim=1, keepdim=True)  # avg over RGB
        new_conv.weight[:] = mean_weight.repeat(1, new_in_channels, 1, 1)
        new_conv.weight *= 3.0 / new_in_channels  # keep activation scale roughly stable
    model.encoder.conv1 = new_conv
    return model

model = smp.Unet(encoder_name="resnet34", encoder_weights="imagenet", in_channels=3, classes=10)
model = expand_first_conv(model, new_in_channels=13)
```

### 3.2 — Band math utilities

Sentinel-2 band order (as delivered by most pipelines, L2A): B01 Coastal, B02 Blue, B03 Green, B04 Red, B05-B07 Red Edge, B08 NIR, B8A Narrow NIR, B09 Water Vapor, B10 Cirrus (often dropped), B11-B12 SWIR.

```python
import numpy as np

def compute_indices(bands: np.ndarray, band_order=("B02","B03","B04","B05","B06","B07","B08","B8A","B09","B10","B11","B12")):
    """bands: array shaped (C, H, W), reflectance scaled 0-1."""
    idx = {name: i for i, name in enumerate(band_order)}
    eps = 1e-6

    red, nir = bands[idx["B04"]] if "B04" in idx else bands[3], bands[idx["B08"]]
    green, swir1 = bands[idx["B03"]], bands[idx["B11"]]

    ndvi = (nir - red) / (nir + red + eps)          # vegetation
    ndwi = (green - nir) / (green + nir + eps)       # water
    ndbi = (swir1 - nir) / (swir1 + nir + eps)        # built-up

    return np.stack([ndvi, ndwi, ndbi], axis=0)

# stack onto the raw bands to get a 16-channel input (13 raw + 3 indices)
def build_input(bands):
    indices = compute_indices(bands)
    return np.concatenate([bands, indices], axis=0)
```

If you add these as extra channels, bump `new_in_channels` in `expand_first_conv` accordingly (13 → 16), and update the dataloader to call `build_input()` before returning tensors.

### 3.3 — Dataloader using SEN12MS/DFC2020 via torchgeo

```python
from torchgeo.datasets import SEN12MS
from torch.utils.data import DataLoader

train_ds = SEN12MS(root="data/sen12ms", split="train", bands=SEN12MS.ALL_BANDS)
train_loader = DataLoader(train_ds, batch_size=8, shuffle=True, num_workers=4)

# torchgeo's SemanticSegmentationTask (Lightning) handles the train/val loop for you
from torchgeo.trainers import SemanticSegmentationTask

task = SemanticSegmentationTask(
    model="unet",
    backbone="resnet34",
    weights=True,
    in_channels=13,
    num_classes=11,           # SEN12MS IGBP simplified scheme
    loss="ce",
    lr=1e-3,
)

import pytorch_lightning as pl
trainer = pl.Trainer(max_epochs=30, accelerator="gpu", devices=1)
trainer.fit(task, train_dataloaders=train_loader)
```

torchgeo's built-in trainers save you from re-writing the boilerplate above by hand once you're past the "does this even work" stage — worth switching to once Phase 2's manual loop is proven.

**Exit criteria for Phase 3:** mIoU improves over the RGB-only Phase 2 run (if it doesn't, check band ordering/normalization first — this is the #1 silent bug in multispectral pipelines), and NDVI/NDWI visualizations look sane over known vegetation/water areas.

---

## Phase 4 — Pull your own AOI and run inference

### 4.1 — Export a Sentinel-2 tile from Google Earth Engine

```python
import ee
ee.Authenticate()
ee.Initialize(project="your-gcp-project")

region = ee.Geometry.Rectangle([76.90, 23.05, 77.10, 23.20])  # example bbox, swap for your AOI

s2 = (
    ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
    .filterBounds(region)
    .filterDate("2025-01-01", "2025-06-01")
    .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 10))
    .median()
    .clip(region)
)

bands = ["B2","B3","B4","B5","B6","B7","B8","B8A","B9","B11","B12"]

task = ee.batch.Export.image.toDrive(
    image=s2.select(bands),
    description="aoi_export",
    folder="s2_exports",
    scale=10,
    region=region,
    fileFormat="GeoTIFF",
    maxPixels=1e9,
)
task.start()
```

(Alternative: manually draw the AOI and download in the [Copernicus Browser](https://browser.dataspace.copernicus.eu/) if you'd rather not deal with GEE auth.)

### 4.2 — Tile a large GeoTIFF for inference

Full AOI tiles are usually far bigger than your model's training patch size, so you tile, predict per-tile, and stitch back.

```python
import rasterio
from rasterio.windows import Window
import numpy as np
import torch

def run_inference_on_tif(model, in_path, out_path, tile_size=512, overlap=32, device="cuda"):
    model.eval()
    with rasterio.open(in_path) as src:
        profile = src.profile.copy()
        H, W = src.height, src.width
        out = np.zeros((H, W), dtype=np.uint8)

        stride = tile_size - overlap
        for y in range(0, H, stride):
            for x in range(0, W, stride):
                win = Window(x, y, min(tile_size, W - x), min(tile_size, H - y))
                tile = src.read(window=win).astype(np.float32) / 10000.0  # S2 reflectance scale

                if tile.shape[1] < tile_size or tile.shape[2] < tile_size:
                    pad = np.zeros((tile.shape[0], tile_size, tile_size), dtype=np.float32)
                    pad[:, :tile.shape[1], :tile.shape[2]] = tile
                    tile = pad

                t = torch.from_numpy(tile).unsqueeze(0).to(device)
                with torch.no_grad():
                    pred = model(t).argmax(1).squeeze(0).cpu().numpy()

                h, w = win.height, win.width
                out[y:y+h, x:x+w] = pred[:h, :w]

    profile.update(count=1, dtype="uint8")
    with rasterio.open(out_path, "w", **profile) as dst:
        dst.write(out, 1)

run_inference_on_tif(model, "data/aoi_export/aoi_export.tif", "outputs/aoi_landcover.tif")
```

Open `aoi_landcover.tif` directly in QGIS with a categorical color ramp to sanity-check it visually against the RGB composite.

---

## Suggested repo structure

```
geoseg/
├── data/                  # raw + downloaded datasets (gitignored)
├── src/
│   ├── datasets/          # dataset wrappers (EuroSAT, SEN12MS, DeepGlobe, custom AOI)
│   ├── models/            # model factory, channel-expansion utils
│   ├── transforms/        # band math, normalization, augmentation
│   ├── train.py
│   └── infer.py           # tiling + stitching for arbitrary GeoTIFFs
├── configs/               # yaml configs per experiment/phase
├── outputs/                # predictions, checkpoints
└── notebooks/             # exploratory / visualization only
```

---

## Practical pitfalls to watch for

- **Band order mismatches** are the single most common silent failure — a model trained on one band ordering will quietly degrade (not crash) on data delivered in a different order. Always assert band order explicitly at the dataloader boundary.
- **Reflectance scaling**: Sentinel-2 L2A values are typically 0–10000 (sometimes 0–65535 depending on processing baseline) — normalize consistently across train/val/inference or your model's activations will be wrong on new data even if metrics looked fine in training.
- **Class imbalance**: bare soil/roads are usually underrepresented relative to vegetation — use Dice loss or focal loss alongside CE, and always evaluate per-class IoU, not just mean IoU, to catch classes that are silently being ignored.
- **Cloud contamination**: median-composite over a date range (as in the GEE snippet) is the cheap fix; for production use, add a proper cloud mask (`QA60` band or `s2cloudless`) before compositing.
- **Train/inference resolution mismatch**: if you train on fixed-size patches but run inference on arbitrarily-sized AOI tiles, use the overlap-and-stitch pattern above rather than a single resize — resizing distorts the effective ground sample distance the model learned on.

---

## Rough timeline

| Phase | Goal | Time (part-time) |
|---|---|---|
| 1 | EuroSAT classifier working | 2-4 days |
| 2 | U-Net segmentation on DeepGlobe/SEN12MS | 1-2 weeks |
| 3 | Multispectral + band math | 1 week |
| 4 | Custom AOI pull + inference | 3-5 days |

Total: roughly a month of part-time work to go from zero to a working custom-AOI segmentation pipeline, assuming no custom labeling is needed yet.
