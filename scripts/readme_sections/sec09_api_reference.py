# -*- coding: utf-8 -*-
"""Section 9: FastAPI Backend Server & Complete REST API Reference."""

def get_section():
    return """# 9. FASTAPI BACKEND SERVER & COMPLETE REST API REFERENCE

The GeoSeg backend is built as an enterprise-grade asynchronous REST API using **FastAPI (Python 3.12 LTS)** and the **Uvicorn** ASGI server. 

---

## 9.1 System Architecture, Middleware & Security Guardrails

### 1. Asynchronous Event-Driven Loop
FastAPI leverages Python's `asyncio` event loop to handle concurrent client requests without blocking. Long-running GPU tasks (e.g., tiled inference or model training) are offloaded to background daemon threads (`threading.Thread`) managed with in-memory thread synchronization locks (`threading.Lock`).

### 2. Cross-Origin Resource Sharing (CORS) Middleware
Configured with permissive headers for local development and proxied via Vite:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 3. Static Assets & Output Mounts
Static directories are mounted safely to serve prediction rasters, super-resolved PNG previews, and AID sample scenes:
- `/static/outputs` $\rightarrow$ `outputs/`
- `/static/sr` $\rightarrow$ `outputs/sr_predictions/`
- `/static/aid` $\rightarrow$ `data/aid/samples/`
- `/` $\rightarrow$ `frontend/dist/` (Mounts compiled React SPA if built)

### 4. Security Whitelist & Input Sanitization Guardrails
- **File Upload Guardrail**: GeoTIFF uploads are checked for valid extensions (`.tif`, `.tiff`) and strictly capped at **100 MB** to prevent denial-of-service (DoS) memory exhaustion.
- **Path Traversal Protection**: All user-supplied filenames and checkpoint paths are passed through `Path(path).resolve()` and validated using `.is_relative_to(allowed_dir)` to prevent directory traversal attacks (e.g. `../../etc/passwd`).

---

## 9.2 Detailed Specification of All REST Endpoints

Below is the exhaustive specification for all 18 REST API endpoints:

```
┌──────┬───────────────────────────────┬─────────────────────────────────────────────────────────────┐
│ Verb │ Path                          │ Purpose                                                     │
├──────┼───────────────────────────────┼─────────────────────────────────────────────────────────────┤
│ GET  │ /api/health                   │ System health check & GPU acceleration discovery            │
│ GET  │ /api                          │ Root API information & discovery index                      │
│ GET  │ /api/sr/paper-metadata        │ Official publication metadata (DOI, PII, authors, modules)  │
│ GET  │ /api/sr/aid-dataset           │ AID 30-class scene metadata, descriptions & sample images   │
│ GET  │ /api/sr/benchmarks            │ Published SOTA comparison table (Tables 3-7)                │
│ POST │ /api/sr/upscale               │ Execute real-time PSISR super-resolution on an aerial scene │
│ POST │ /api/inference/predict        │ Upload a multispectral GeoTIFF and start tiled inference   │
│ GET  │ /api/inference/result/{id}    │ Poll status and get output URLs for an inference job        │
│ GET  │ /api/inference/jobs           │ List all registered inference jobs in memory                │
│ GET  │ /api/results/                 │ Browse all past prediction results and metadata             │
│ GET  │ /api/results/preview/{id}     │ Retrieve a colorized PNG land-cover segmentation mask       │
│ GET  │ /api/results/satellite/{id}   │ Retrieve the optical RGB true-color reference image         │
│ GET  │ /api/results/download/{file}  │ Securely download a full 16-band classified GeoTIFF raster  │
│ GET  │ /api/results/checkpoints      │ Scan and list all saved PyTorch model weights (.pth)        │
│ POST │ /api/training/start           │ Start a multi-epoch neural network training job             │
│ GET  │ /api/training/status          │ Stream live loss, epoch progress, and validation mIoU       │
│ POST │ /api/training/stop            │ Gracefully stop an active training run                      │
│ POST │ /api/aoi/export               │ Export Sentinel-2 L2A tiles via Earth Engine or synthetic   │
│ POST │ /api/cpp-engine/run           │ Run and benchmark the native C++17 OOP geospatial engine    │
└──────┴───────────────────────────────┴─────────────────────────────────────────────────────────────┘
```

---

### Detailed Endpoint Catalog & Curl Examples

#### 1. `GET /api/health`
Checks API server availability and detects whether PyTorch has access to an active NVIDIA CUDA GPU.
- **Request**: `GET http://localhost:8000/api/health`
- **Response (200 OK)**:
```json
{
  "status": "ok",
  "gpu_available": true,
  "gpu_name": "NVIDIA GeForce RTX 5050 Laptop GPU",
  "version": "0.1.0"
}
```
- **Curl**:
```bash
curl -X GET http://localhost:8000/api/health
```

---

#### 2. `GET /api/sr/paper-metadata`
Returns official Elsevier journal publication details, authors, institutions, and architectural modules.
- **Response (200 OK)**:
```json
{
  "title": "Enhanced satellite image resolution with a residual network and correlation filter",
  "journal": "Chemometrics and Intelligent Laboratory Systems (Elsevier)",
  "year": 2025,
  "volume": 256,
  "article_id": "105277",
  "pii": "S0169-7439(24)00217-X",
  "doi": "10.1016/j.chemolab.2024.105277",
  "authors": [
    "Ajay Sharma (VIT Bhopal University)",
    "Bhavana P. Shrivastava (MANIT Bhopal)",
    "Praveen Kumar Tyagi (Poornima Institute, Jaipur)",
    "Ebtasam Ahmad Siddiqui (Poornima Institute, Jaipur)",
    "Rahul Prasad (UPES Dehradun)",
    "Swati Gautam (MANIT Bhopal)",
    "Pranshu Pranjal (VIT Bhopal University)"
  ],
  "loss_function": "loss_CL = w_i * loss_MSE + u_i * loss_SSIM (Equations 4-8)",
  "architectural_modules": [
    "Stage 1: UB1 (512 filters) + 2x Deconvolution",
    "Stage 2: UB2 (256 filters) + 4x Deconvolution",
    "Stage 3: UB3 (128 filters) + 8x Sub-pixel Convolution (PixelShuffle)"
  ]
}
```
- **Curl**:
```bash
curl -X GET http://localhost:8000/api/sr/paper-metadata
```

---

#### 3. `GET /api/sr/aid-dataset`
Returns comprehensive metadata for the 30 AID scene classes along with direct image URLs for all loaded sample scenes.
- **Response (200 OK)**:
```json
{
  "dataset": "AID: Aerial Image Dataset",
  "total_classes": 30,
  "image_resolution": "600x600 pixels",
  "ground_sample_distance": "0.5m to 8m",
  "samples": [
    {
      "id": "aid_airport_01",
      "class_name": "airport",
      "color": "#64748b",
      "description": "Runways, taxiways, and airport terminals with high structural contrast",
      "url": "/static/aid/aid_airport_01.jpg"
    },
    {
      "id": "aid_farmland_01",
      "class_name": "farmland",
      "color": "#eab308",
      "description": "Agricultural crop parcels and irrigation pivots",
      "url": "/static/aid/aid_farmland_01.jpg"
    }
  ]
}
```
- **Curl**:
```bash
curl -X GET http://localhost:8000/api/sr/aid-dataset
```

---

#### 4. `POST /api/sr/upscale`
Executes real-time PSISR super-resolution on an aerial scene using the loaded deep learning weights.
- **Request Body (JSON)**:
```json
{
  "image_id": "aid_farmland_01",
  "scale_factor": 4
}
```
- **Response (200 OK)**:
```json
{
  "status": "success",
  "scale_factor": 4,
  "input_resolution": "48x48 px",
  "output_resolution": "192x192 px",
  "lr_url": "/static/sr/aid_farmland_01_lr.png",
  "sr_url": "/static/sr/aid_farmland_01_sr_4x.png",
  "metrics": {
    "psnr": 31.41,
    "ssim": 0.8275,
    "correlation_efficiency": 99.25,
    "mse": 0.0482
  },
  "model_efficiency": 0.0099,
  "flops": "1.53 GFLOPs",
  "correlation_efficiency_pct": 99.25
}
```
- **Curl**:
```bash
curl -X POST http://localhost:8000/api/sr/upscale \
  -H "Content-Type: application/json" \
  -d '{"image_id": "aid_farmland_01", "scale_factor": 4}'
```

---

#### 5. `POST /api/inference/predict`
Uploads a multispectral GeoTIFF file (`.tif`) and launches background tiled inference using the GeoSeg U-Net model.
- **Content-Type**: `multipart/form-data`
- **Form Parameters**:
  - `file`: The GeoTIFF file binary
  - `tile_size`: `512` (integer)
  - `overlap`: `32` (integer)
  - `use_indices`: `true` (boolean)
  - `checkpoint`: `"checkpoints/psisr/best_model.pth"` (string)
- **Response (200 OK)**:
```json
{
  "id": "e4f8b2a1",
  "status": "pending",
  "input_path": "data/uploads/e4f8b2a1_sentinel2.tif",
  "output_path": "outputs/predictions/e4f8b2a1_prediction.tif",
  "timestamp": "2026-10-08T12:00:00.000000"
}
```
- **Curl**:
```bash
curl -X POST http://localhost:8000/api/inference/predict \
  -F "file=@data/uploads/sample_sentinel2.tif" \
  -F "tile_size=512" \
  -F "overlap=32"
```

---

#### 6. `GET /api/inference/result/{job_id}`
Polls the execution status of a running or completed inference job.
- **Response (200 OK)**:
```json
{
  "id": "e4f8b2a1",
  "status": "completed",
  "input_path": "data/uploads/e4f8b2a1_sentinel2.tif",
  "output_path": "outputs/predictions/e4f8b2a1_prediction.tif",
  "preview_url": "/api/results/preview/e4f8b2a1",
  "elapsed_seconds": 1.84,
  "timestamp": "2026-10-08T12:00:01.840000"
}
```
- **Curl**:
```bash
curl -X GET http://localhost:8000/api/inference/result/e4f8b2a1
```

---

#### 7. `POST /api/cpp-engine/run`
Executes and benchmarks the native C++17 OOP geospatial engine on the host system.
- **Response (200 OK)**:
```json
{
  "success": true,
  "execution_time_ms": 18.4,
  "oop_paradigms": {
    "templates": "Image<T> generic matrix",
    "operator_overload": "+, -, *, / overloaded",
    "inheritance": "BandMathEngine, TileManager",
    "polymorphism": "SpectralIndex virtual factory",
    "abstraction": "ImageProcessor pure virtual",
    "encapsulation": "Strict private memory buffers",
    "raii": "GeoTIFFHandler automated handle cleanup"
  },
  "benchmarks": {
    "spectral_index_speedup": "776x vs pure Python",
    "memory_throughput": "14.2 GB/s SIMD"
  },
  "output_log": "GeoSeg C++ Backend — OOP Demonstration Output..."
}
```
- **Curl**:
```bash
curl -X POST http://localhost:8000/api/cpp-engine/run
```

---
"""
