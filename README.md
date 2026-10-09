<p align="center"><img src="asset/hero.svg" alt="GeoSeg" width="100%"></p>

<p align="center">
<img src="https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white">
<img src="https://img.shields.io/badge/PyTorch-2.5-EE4C2C?style=flat-square&logo=pytorch&logoColor=white">
<img src="https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white">
<img src="https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black">
<img src="https://img.shields.io/badge/Tailwind-v4-06B6D4?style=flat-square&logo=tailwindcss&logoColor=white">
<img src="https://img.shields.io/badge/C%2B%2B-17-00599C?style=flat-square&logo=c%2B%2B&logoColor=white">
<img src="https://img.shields.io/badge/Sentinel--2-13%20bands-003247?style=flat-square">
<img src="https://img.shields.io/badge/License-MIT-yellow?style=flat-square">
</p>

---

## 🧭 Overview

**GeoSeg** is a full-stack Earth Observation platform: multispectral **super-resolution** (PSISRNet, 2× / 4× / 8×), **16-channel land-cover segmentation** (ResNet-34 U-Net), a **C++17 SIMD** geospatial engine, and an interactive **FastAPI + React** cockpit.

PSISRNet is an implementation of
> Sharma et al., *Enhanced satellite image resolution with a residual network and correlation filter*, Chemometrics and Intelligent Laboratory Systems **256** (2025) 105277 · [DOI 10.1016/j.chemolab.2024.105277](https://doi.org/10.1016/j.chemolab.2024.105277)

---

## 📊 At a Glance

<p align="center"><img src="asset/stats.svg" alt="Stats" width="100%"></p>

---

## 🏗️ Architecture

<p align="center"><img src="asset/architecture.svg" alt="Architecture" width="100%"></p>

| Layer | What it does |
| --- | --- |
| 🖥️ **Frontend** | Canvas Earth globe, split-slider super-resolution viewer, Leaflet map explorer, GeoTIFF inference UI, live training curves |
| ⚙️ **Backend** | 18 async REST endpoints, background training and inference jobs, path-traversal and upload-size guards |
| 🤖 **ML core** | PSISRNet, 16-channel U-Net, Dice + CE loss, AMP FP16 training |
| ⚡ **Native engine** | `Image<T>` templates, operator overloading, polymorphic spectral indices, RAII GeoTIFF I/O, AVX2 + OpenMP |

---

## 🧠 PSISRNet Pipeline

<p align="center"><img src="asset/pipeline.svg" alt="PSISRNet pipeline" width="100%"></p>

- **Cascading UBCF blocks** (2× → 4× → 8×) instead of one 8× leap.
- **Dilation rates 1, 2, 4** to avoid gridding blind spots.
- **Pearson correlation filter** inside each block, concat + 1×1 fusion instead of residual addition.
- **PixelShuffle** at the last stage to suppress checkerboard artifacts.
- **Adaptive loss** `L = w·MSE + u·(1−SSIM)` with `w = MSE / (MSE + L_SSIM)`.

---

## 🛰️ Spectral Input

<p align="center"><img src="asset/bands.svg" alt="Sentinel-2 bands" width="100%"></p>

The segmentation U-Net takes **16 channels**: all 13 Sentinel-2 L2A bands plus **NDVI**, **NDWI** and **NDBI**, and predicts 11 land-cover classes.

| Index | Formula |
| --- | --- |
| NDVI | (B08 − B04) / (B08 + B04) |
| NDWI | (B03 − B08) / (B03 + B08) |
| NDBI | (B11 − B08) / (B11 + B08) |

---

## 📈 Benchmarks (published)

<p align="center"><img src="asset/benchmark.svg" alt="Benchmark" width="100%"></p>

| Model | Params | 2× PSNR / SSIM | 4× PSNR / SSIM | 8× PSNR / SSIM |
| --- | --- | --- | --- | --- |
| Bicubic | – | 31.42 / 0.8841 | 26.15 / 0.7320 | 22.84 / 0.6120 |
| RCAN | 15.6 M | 35.12 / 0.9415 | 29.62 / 0.8350 | 25.80 / 0.7250 |
| MambaFormer | 11.2 M | 35.45 / 0.9458 | 29.98 / 0.8435 | 26.18 / 0.7380 |
| **PSISR (paper)** | 21.89 M | **38.47 / 0.9592** | **31.41 / 0.8275** | **27.03 / 0.6458** |

> Numbers above come from the paper's tables. At 4× and 8× the paper's own SSIM for PSISR is *lower* than MambaFormer's, so the "dominates every metric" framing does not hold.

### Reproduction status

| Item | Status |
| --- | --- |
| Paper results | Published, **not reproduced** here |
| Local training run | 3 epochs on AID, loss 1.2523 → 1.1664, PSNR ≈ 6 dB (not converged) |
| Full 300-epoch run | Not yet run, so no converged checkpoint metrics are claimed |

---

## 🌍 Dataset

<p align="center"><img src="asset/aid.svg" alt="AID classes" width="100%"></p>

---

## 🚀 Quick Start

```bash
git clone https://github.com/yajatkataria08-a11y/GEOSEG.git
cd GEOSEG
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python scripts/populate_aid_samples.py
python -m uvicorn api.server:app --host 127.0.0.1 --port 8000
```

```bash
cd frontend && npm install && npm run dev      # http://127.0.0.1:5173
```

```bash
cd backend
g++ -std=c++17 -O3 -mavx2 -mfma -fopenmp -Iinclude \
    src/main.cpp src/BandMathEngine.cpp src/TileManager.cpp src/GeoTIFFHandler.cpp \
    -o geoseg_backend
```

---

## 📡 API Reference

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/health` | Health and GPU discovery |
| `GET` | `/api/sr/paper-metadata` | Paper metadata |
| `GET` | `/api/sr/aid-dataset` | 30-class AID catalog |
| `GET` | `/api/sr/benchmarks` | Published comparison table |
| `POST` | `/api/sr/upscale` | Run PSISR on a scene |
| `POST` | `/api/inference/predict` | Upload GeoTIFF, start tiled inference |
| `GET` | `/api/inference/result/{id}` | Poll job status |
| `GET` | `/api/results/` | Browse results |
| `POST` | `/api/training/start` | Start training |
| `GET` | `/api/training/status` | Live loss / mIoU |
| `POST` | `/api/aoi/export` | Export Sentinel-2 AOI |
| `POST` | `/api/cpp-engine/run` | Run native engine benchmark |

Interactive docs at `http://127.0.0.1:8000/docs`.

---

## 📁 Structure

```
GEOSEG/
├── api/        FastAPI routes and schemas
├── backend/    C++17 engine (Image<T>, BandMath, TileManager, GeoTIFFHandler)
├── src/        PyTorch models, datasets, train / infer
├── frontend/   React 18 + Vite + Tailwind v4
├── configs/    YAML training configs
├── scripts/    Setup and data helpers
├── tests/      pytest suite
└── asset/      README graphics
```

---

## 🧪 Tests

```bash
pytest tests/ -v
```

---

## 📚 Citation

```bibtex
@article{sharma2025enhanced,
  title   = {Enhanced satellite image resolution with a residual network and correlation filter},
  author  = {Sharma, Ajay and Shrivastava, Bhavana P. and Tyagi, Praveen Kumar and Siddiqui, Ebtasam Ahmad and Prasad, Rahul and Gautam, Swati and Pranjal, Pranshu},
  journal = {Chemometrics and Intelligent Laboratory Systems},
  volume  = {256}, pages = {105277}, year = {2025},
  doi     = {10.1016/j.chemolab.2024.105277}
}
```

---

<p align="center"><b>MIT License</b> · Built on open Sentinel-2 and AID data</p>
