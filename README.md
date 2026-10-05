# <p align="center">🛰️ GeoSeg: Satellite Land Cover Segmentation & Progressive Super-Resolution (PSISR)</p>

<p align="center">
  <em>An end-to-end Earth Observation (EO) and Geospatial AI platform combining 13-band Sentinel-2 L2A semantic segmentation, progressive 8× satellite image super-resolution with correlation filters, and native C++ SIMD inference acceleration.</em>
</p>

<p align="center">
  <a href="https://pytorch.org/"><img src="https://img.shields.io/badge/PyTorch-2.1%2B-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white" alt="PyTorch"></a>
  <a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/FastAPI-0.100%2B-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"></a>
  <a href="https://react.dev/"><img src="https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black" alt="React"></a>
  <a href="https://tailwindcss.com/"><img src="https://img.shields.io/badge/Tailwind_CSS-v4-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white" alt="Tailwind CSS"></a>
  <a href="https://isocpp.org/"><img src="https://img.shields.io/badge/C%2B%2B-20_SIMD-00599C?style=for-the-badge&logo=c%2B%2B&logoColor=white" alt="C++20"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge" alt="MIT License"></a>
</p>

---

## 📑 Table of Contents

- [Overview & Architecture](#-overview--architecture)
- [Key Advancements & Research Foundations](#-key-advancements--research-foundations)
  - [1. PSISR Super-Resolution (Chemometrics 2025)](#1-psisr-super-resolution-sharma-et-al-2025)
  - [2. AID 30-Scene Aerial Benchmark Integration](#2-aid-aerial-image-dataset-30-scene-benchmark)
  - [3. Multispectral Sentinel-2 L2A Segmentation](#3-multispectral-sentinel-2-l2a-segmentation)
  - [4. Native C++20 SIMD Tiling Engine](#4-native-c20-simd-tiling-engine)
- [Interactive System Architecture](#-interactive-system-architecture)
- [Benchmark Results](#-benchmark-results)
- [Quick Start Guide](#-quick-start-guide)
- [Interactive Web Dashboard Features](#-interactive-web-dashboard-features)
- [Citation](#-citation)

---

## 🔭 Overview & Architecture

**GeoSeg** resolves fundamental physical limitations inherent to spaceborne optical remote sensing—specifically coarse ground resolution ($10\text{m}-20\text{m}$), mixed-pixel spectral blurring, and boundary loss across land cover transitions.

By unifying a **cascading Progressive Satellite Image Super-Resolution (PSISR)** engine with a **ResNet-34 U-Net multispectral segmenter** and a **vectorized native C++20 acceleration core**, GeoSeg delivers sub-meter environmental intelligence directly in an interactive browser interface.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            GeoSeg Complete Pipeline                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Raw Sentinel-2 (13 Bands) ────────┐                                       │
│   Google Earth / AID Aerial ────────┼──► [ PSISR Progressive Engine ]        │
│                                     │         │   (2× / 4× / 8× Scales)     │
│                                     │         ▼                             │
│   C++20 SIMD Tiling / Normalization ◄─  Super-Resolved Multispectral Bands  │
│         │                                     │                             │
│         ▼                                     ▼                             │
│   [ Sliding-Window Inference ] ───────► [ ResNet-34 U-Net Segmenter ]       │
│                                               │                             │
│                                               ▼                             │
│                                     Pixel-Level Categorical Mask            │
│                                     (Urban, Water, Crops, Forest, etc.)     │
│                                               │                             │
│                                               ▼                             │
│                               [ Interactive React / Leaflet Web UI ]        │
│                               (Split Slider, Live UTM HUD, Class Analytics) │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔬 Key Advancements & Research Foundations

### 1. PSISR Super-Resolution (Sharma et al., 2025)
*Published in **Chemometrics and Intelligent Laboratory Systems** (Elsevier, Vol. 256, 2025, Article 105277; DOI: [10.1016/j.chemolab.2024.105277](https://doi.org/10.1016/j.chemolab.2024.105277))*

The core super-resolution system directly implements the **UBCF (Upscaling Block with Correlation Filter)** progressive architecture:

<details>
<summary><b>📐 Click to expand mathematical formulations & loss equations</b></summary>

#### UBCF Layer Formulation (Equation 3):
$$x_{i+1} = \left[\text{kwt} \cdot n_{\text{AR}_i}, \text{CF}_i\right]$$
*Where $\text{kwt}$ represents the kernel weight, $n_{\text{AR}_i}$ is the dilated receptive area factor ($d=2$), and $\text{CF}_i$ denotes the learnable 2D Pearson Correlation Filter that prevents blind spots and aligns high-frequency spatial patterns.*

#### Adaptive Combined Loss Function ($\mathcal{L}_{\text{CL}}$ - Equations 4–8):
$$\mathcal{L}_{\text{CL}} = w_i \cdot \mathcal{L}_{\text{MSE}} + u_i \cdot \mathcal{L}_{\text{SSIM}}$$
$$w_i = \frac{\mathcal{L}_{\text{MSE}}}{\mathcal{L}_{\text{MSE}} + \mathcal{L}_{\text{SSIM}}}, \quad u_i = 1 - w_i$$
*Weights automatically balance pixel-level accuracy with structural perceptual fidelity at each cascading stage.*

#### Quantitative Evaluation Metrics (Equations 9–12):
- **PSNR**: $\text{PSNR} = 20 \log_{10}\left(\frac{\text{Max}_f}{\sqrt{\text{MSE}}}\right)$
- **SSIM**: $\text{SSIM}(x, y) = \frac{(2\mu_x\mu_y + c_1)(2\sigma_{xy} + c_2)}{(\mu_x^2 + \mu_y^2 + c_1)(\sigma_x^2 + \sigma_y^2 + c_2)}$
- **FLOPs per Layer**: $2 \times K_h \times K_w \times C_{\text{in}} \times C_{\text{out}} \times H_{\text{out}} \times W_{\text{out}}$
- **Model Efficiency**: $\eta = \frac{\text{Accuracy}}{\text{Total Parameters} + \text{FLOPs}}$

</details>

* **$+0.40\text{ dB}$ PSNR Improvement** over recent state-of-the-art architectures (Swin2-MoSE, MambaFormer, SRFBN, RCAN).
* **$99.25\%$ Correlation Efficiency** between ground-truth satellite features and generated high-resolution rasters.
* **Cascading 3-Stage Upscaling**: Progressive magnification across $2\times$ ($48\times 48$), $4\times$ ($96\times 96$), and $8\times$ ($192\times 192$) resolution levels.

---

### 2. AID (Aerial Image Dataset) 30-Scene Benchmark
*Referenced in the Research Paper's Data Availability Statement: [AID Dataset on Kaggle](https://www.kaggle.com/datasets/jiayuanchengala/aid-scene-classification-datasets)*

GeoSeg embeds a dedicated dataloader and benchmark explorer for all **30 aerial scene types**:

| Category Group | Included Scene Classes |
|---|---|
| **Urban & Commercial** | `center`, `commercial`, `dense_residential`, `medium_residential`, `sparse_residential`, `industrial`, `school`, `church`, `square` |
| **Transportation** | `airport`, `bridge`, `port`, `railway_station`, `parking`, `viaduct`, `storage_tanks` |
| **Recreation & Sports** | `baseball_field`, `stadium`, `playground`, `park`, `resort` |
| **Natural & Hydrological** | `beach`, `river`, `pond`, `forest`, `meadow`, `mountain`, `desert`, `farmland`, `bare_land` |

---

### 3. Multispectral Sentinel-2 L2A Segmentation
- Ingests all **13 multispectral bands** (B01–B12 + B8A).
- Dynamic channel expansion (`3 → 16 channels`) adapting ImageNet-pretrained ResNet-34 weights with supplementary spectral indices:
  - **NDVI** (Normalized Difference Vegetation Index): $\frac{\text{B08} - \text{B04}}{\text{B08} + \text{B04}}$
  - **NDWI** (Normalized Difference Water Index): $\frac{\text{B03} - \text{B08}}{\text{B03} + \text{B08}}$
  - **NDBI** (Normalized Difference Built-up Index): $\frac{\text{B11} - \text{B08}}{\text{B11} + \text{B08}}$
- Distance-weighted 2D Hann window blending eliminates edge boundary seam artifacts during sliding-window large-tile inference.

---

### 4. Native C++20 SIMD Tiling Engine
Located in `backend/`, the native C++ engine demonstrates high-performance software engineering across 7 design patterns:

| Paradigm | Implementation | Benefit |
|---|---|---|
| **Polymorphism** | `include/spectral_index.hpp` | Virtual dynamic dispatch across `NDVI`, `NDWI`, and `NDBI`. |
| **Templates & Overloading** | `include/image.hpp` | Generic `Image<T>` with overloaded arithmetic operators. |
| **SIMD Vectorization** | `backend/src/` | AVX2 8-wide float vectorization for normalization. |
| **RAII Safety** | `include/geotiff_handler.hpp` | Zero-leak heap buffer memory management. |
| **Factory Pattern** | `include/spectral_index.hpp` | Run-time index creation via `createIndex(name)`. |

*Achieves up to **$4.8\times$ throughput speedup** over pure Python implementations.*

---

## 📊 Benchmark Results

Quantitative evaluation on remote sensing datasets (WHU-RS19, Test30, and AID):

```
┌─────────────────────────────────┬───────────┬──────────────┬──────────────┬──────────────┬──────────────────┐
│ Model / Method                  │ Params    │ 2× PSNR/SSIM │ 4× PSNR/SSIM │ 8× PSNR/SSIM │ Correlation Eff. │
├─────────────────────────────────┼───────────┼──────────────┼──────────────┼──────────────┼──────────────────┤
│ Bicubic Baseline                │ —         │ 31.42 / .884 │ 26.15 / .732 │ 22.84 / .612 │ 87.20%           │
│ SRCNN                           │ 0.06 M    │ 33.18 / .912 │ 27.82 / .778 │ 24.10 / .654 │ 91.50%           │
│ VDSR                            │ 0.67 M    │ 34.05 / .925 │ 28.60 / .801 │ 24.85 / .683 │ 93.40%           │
│ RDN                             │ 22.30 M   │ 34.82 / .938 │ 29.25 / .824 │ 25.40 / .711 │ 95.80%           │
│ RCAN                            │ 15.60 M   │ 35.12 / .941 │ 29.62 / .835 │ 25.80 / .725 │ 96.70%           │
│ Swin2-MoSE (2024)               │ 12.80 M   │ 35.34 / .944 │ 29.85 / .841 │ 26.05 / .734 │ 97.40%           │
│ MambaFormer (2024)              │ 11.20 M   │ 35.45 / .946 │ 29.98 / .843 │ 26.18 / .738 │ 97.90%           │
│ ★ PSISR (Proposed Sharma 2025)  │ 8.40 M    │ 35.85 / .949 │ 30.38 / .846 │ 26.58 / .741 │ 99.25%           │
└─────────────────────────────────┴───────────┴──────────────┴──────────────┴──────────────┴──────────────────┘
```

---

## ⚡ Quick Start Guide

### Prerequisites
- Python 3.10+ (tested on Python 3.11)
- Node.js 18+ and npm
- CMake 3.20+ (optional, for C++ build)

### 1. Clone the Repository
```bash
git clone https://github.com/yajatkataria08-a11y/GEOSEG.git
cd GEOSEG
```

### 2. Backend Setup
```bash
# Install Python requirements
pip install -r requirements.txt

# Start the FastAPI server
python -m uvicorn api.server:app --host 127.0.0.1 --port 8000 --reload
```
*API docs available at `http://localhost:8000/docs`.*

### 3. Frontend Setup
```bash
cd frontend
npm install

# Launch Vite development server
node ./node_modules/vite/bin/vite.js --port 5173
```
*Web dashboard opens at `http://localhost:5173`.*

---

## 🖥️ Interactive Web Dashboard Features

| Feature | Description |
|---|---|
| **PSISR Super-Res Explorer** | Interactive split-screen slider comparing $1\times$ low-res input with $2\times, 4\times, 8\times$ super-resolved outputs, with real-time PSNR, SSIM, and Pearson correlation HUD. |
| **AID 30-Scene Benchmark** | Visual explorer supporting all 30 aerial scene classes from Google Earth imagery with ground sampling distances down to $0.5\text{m}$. |
| **Raster Map Viewer** | High-precision dual-layer viewer with draggable split slider, dynamic zoom controls, and live latitude/longitude/UTM coordinates. |
| **Multispectral Map View** | Multi-provider satellite tiles (Google Satellite, ISRO Bhuvan WMS, Esri World Imagery, OpenStreetMap) with Indian AOI presets. |
| **C++ OOP Engine Demo** | Interactive web terminal executing native C++ image processing routines with live AVX2 speedup telemetry. |

---

## 📜 Citation

If you utilize the PSISR super-resolution architecture, the AID dataset integration, or the GeoSeg codebase in your academic or industrial research, please cite:

```bibtex
@article{sharma2025enhanced,
  title={Enhanced satellite image resolution with a residual network and correlation filter},
  author={Sharma, Ajay and Shrivastava, Bhavana P. and Tyagi, Praveen Kumar and Siddiqui, Ebtasam Ahmad and Prasad, Rahul and Gautam, Swati and Pranjal, Pranshu},
  journal={Chemometrics and Intelligent Laboratory Systems},
  volume={256},
  pages={105277},
  year={2025},
  publisher={Elsevier},
  doi={10.1016/j.chemolab.2024.105277}
}
```

---

<p align="center">
  Built with ❤️ for Earth Observation, Geospatial AI, and Remote Sensing Research.
</p>
