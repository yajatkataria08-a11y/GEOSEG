# -*- coding: utf-8 -*-
"""Section 11: Step-by-Step Reproduction Cookbook: From Scratch to Production."""

def get_section():
    return """# 11. STEP-BY-STEP REPRODUCTION COOKBOOK: FROM SCRATCH TO PRODUCTION

This chapter provides a complete, foolproof, ground-up guide for recreating, building, training, and running the entire GeoSeg platform on a clean machine.

---

## 11.1 Hardware Specifications & OS Compatibility

GeoSeg is engineered to run seamlessly across all major operating systems:

```
┌──────────────────┬─────────────────────────────────────┬─────────────────────────────────────┐
│ Component        │ Minimum Requirements (Demo / CPU)   │ Recommended Production Setup (GPU) │
├──────────────────┼─────────────────────────────────────┼─────────────────────────────────────┤
│ Operating System │ Windows 10/11 64-bit, Ubuntu 22.04+ │ Windows 11 64-bit, Ubuntu 22.04 LTS │
│ Processor (CPU)  │ 4-Core Intel Core i5 / AMD Ryzen 5  │ 8+ Core Intel Core i7/i9 or Ryzen 7 │
│ Memory (RAM)     │ 8 GB DDR4                           │ 16 GB - 32 GB DDR4/DDR5             │
│ Storage          │ 10 GB Free SSD Space                │ 50 GB NVMe M.2 SSD Space            │
│ Graphics (GPU)   │ Integrated Graphics (CPU fallback)  │ NVIDIA GeForce RTX 3060 / 4060 /    │
│                  │                                     │ 5050 / A100 (4 GB+ VRAM, CUDA 12+)  │
│ C++ Compiler     │ GCC 9+ / Clang 10+ / MSVC 2019+     │ GCC 12+ (MinGW-w64 on Windows)      │
│ Node.js Runtime  │ Node.js 18.x LTS                    │ Node.js 20.x or 22.x LTS            │
│ Python Runtime   │ Python 3.11                         │ Python 3.12 LTS                     │
└──────────────────┴─────────────────────────────────────┴─────────────────────────────────────┘
```

---

## 11.2 Step 1: Environment Provisioning & Toolchains

### On Windows (PowerShell):
Open PowerShell as Administrator and verify installed toolchains:
```powershell
# 1. Verify Git
git --version

# 2. Verify Python 3.12
python --version

# 3. Verify Node.js & npm
node -v
npm -v

# 4. Verify C++ Compiler (g++ via MinGW or MSVC cl.exe)
g++ --version
```

If toolchains are missing:
```powershell
# Install Node.js via winget
winget install OpenJS.NodeJS.LTS

# Install Python 3.12 via winget
winget install Python.Python.3.12

# Install MinGW-w64 C++ compiler via winget
winget install BrechtSanders.MinGW-w64
```

### On Linux (Ubuntu / Debian):
```bash
sudo apt update && sudo apt install -y \
    build-essential \
    cmake \
    git \
    python3.12 \
    python3.12-venv \
    python3-pip \
    libgdal-dev \
    nodejs \
    npm
```

---

## 11.3 Step 2: Repository Setup & Virtual Environment

Clone the repository and initialize the Python virtual environment:

```bash
# 1. Clone the repository
git clone https://github.com/yajatkataria08-a11y/GEOSEG.git
cd GEOSEG

# 2. Create an isolated Python 3.12 virtual environment
python -m venv .venv

# 3. Activate the virtual environment
# On Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# On Linux / macOS:
source .venv/bin/activate

# 4. Upgrade pip and build tools
python -m pip install --upgrade pip setuptools wheel
```

### Install Core Python Dependencies
```bash
# Install core requirements
pip install -r requirements.txt
```

### Configure PyTorch with GPU Acceleration (Optional)
If your workstation has an NVIDIA GPU:
```bash
# Install PyTorch with CUDA 12.1 support
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121 --force-reinstall
```
Verify GPU discovery:
```bash
python -c "import torch; print('CUDA Available:', torch.cuda.is_available()); print('Device:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
```

---

## 11.4 Step 3: AID Dataset Ingestion & Automated Sample Setup

GeoSeg utilizes the 10,000-image Aerial Image Dataset (AID). You can download it directly via Kagglehub or download our pre-populated sample pack:

```bash
# Ingest AID dataset using kagglehub (Python)
python -c "import kagglehub; path = kagglehub.dataset_download('jiayuanchengala/aid-scene-classification-datasets'); print('Downloaded to:', path)"
```

### Run Automated Sample Population
To copy representative sample scenes for all 30 classes into `data/aid/samples/` and `frontend/public/previews/aid/`:
```bash
python scripts/populate_aid_samples.py
```
This guarantees that the web UI immediately has live image assets for all 30 scene categories!

---

## 11.5 Step 4: Compiling the Native C++ OOP Engine

Compile the C++17 backend into an executable binary using standard `g++` or CMake:

### Method A: Direct Compilation with g++ (Recommended on Windows/MinGW & Linux)
```bash
cd backend

# Compile the standalone OOP demonstration binary
g++ -std=c++17 -O3 -mavx2 -mfma -fopenmp \
    -Iinclude \
    src/main.cpp \
    src/BandMathEngine.cpp \
    src/TileManager.cpp \
    src/GeoTIFFHandler.cpp \
    -o geoseg_backend.exe

# Return to project root
cd ..
```

### Method B: Build with CMake
```bash
cd backend
mkdir -p build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . --config Release
cd ../..
```

### Test the Compiled C++ Binary
```bash
# On Windows:
.\backend\geoseg_backend.exe

# On Linux:
./backend/geoseg_backend
```
You should see the clean terminal output validating all seven OOP paradigms and execution timings!

---

## 11.6 Step 5: Launching the FastAPI Backend Server

Launch the Uvicorn ASGI server hosting the REST API:

```bash
# From the project root with .venv active:
python -m uvicorn api.server:app --host 127.0.0.1 --port 8000 --reload
```

Verify that the backend is healthy by opening your browser or running curl:
```bash
curl http://127.0.0.1:8000/api/health
```
Expected output:
```json
{"status":"ok","gpu_available":true,"gpu_name":"...","version":"0.1.0"}
```
You can also view the interactive Swagger documentation at `http://127.0.0.1:8000/docs`.

---

## 11.7 Step 6: Launching the React Vite Frontend Application

Open a second terminal window to launch the frontend web application:

```bash
# Navigate to the frontend directory
cd frontend

# 1. Install Node.js dependencies
npm install

# 2. Launch the Vite development server
npm run dev -- --host 127.0.0.1 --port 5173
```

Open your browser to:
👉 **`http://localhost:5173`**

You are now in the GeoSeg Mission Cockpit!
- Click **"PSISR Super-Res"** to test 8× magnification on any of the 30 AID scenes.
- Click **"home"** to spin the 3D NASA Earth Globe.
- Click **"projects"** to explore satellite tiles on Google, Bhuvan, and Esri maps.
- Click **"developers"** to execute the C++ engine live in your browser!

---

## 11.8 Step 7: Full-Stack Verification & Automated Testing Suite

To run the automated Python test suite verifying dataset loaders, model architectures, metrics, and API routes:

```bash
# Run pytest from project root
pytest tests/ -v
```
Expected result: **30 passed tests** verifying model tensor shapes, skip connection dimensionality, and metric calculations!

---

## 11.9 Step 8: Production Single-Server Bundling (Optional)

If you wish to deploy GeoSeg as a single production server (where FastAPI serves the compiled React application directly without needing a separate `npm run dev` process):

```bash
# 1. Compile the React frontend into static HTML/JS/CSS assets
cd frontend
npm run build
cd ..

# 2. Verify that frontend/dist/ exists
# FastAPI automatically detects frontend/dist and mounts it as the root static handler!

# 3. Launch FastAPI in production mode
python -m uvicorn api.server:app --host 0.0.0.0 --port 8000
```
Now navigating to `http://localhost:8000/` serves the complete React web application directly from the FastAPI server!

---

## 11.10 Troubleshooting Matrix & Common Pitfall Mitigations

```
┌───────────────────────────────────────────────┬────────────────────────────────────────────────────────────────────────┐
│ Issue / Error Message                         │ Cause & Definitive Fix                                                 │
├───────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────┤
│ "CUDA error: out of memory"                   │ GPU VRAM exhausted. In configs/psisr_aid.yaml, reduce batch_size from  │
│                                               │ 8 to 4 or 2, or enable gradient accumulation.                          │
├───────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────┤
│ "C++ binary is not compiled" on CppDemo page  │ geoseg_backend.exe missing from backend/. Run the g++ compilation      │
│                                               │ command in Section 11.5 to create the executable.                      │
├───────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────┤
│ "Cannot find module 'leaflet'" in frontend    │ Node dependencies not installed. Run `cd frontend && npm install`.    │
├───────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────┤
│ "Port 8000 is already in use"                 │ An existing Uvicorn server is running. Kill it using:                  │
│                                               │ PowerShell: `Stop-Process -Name python -Force`                         │
│                                               │ Linux: `fuser -k 8000/tcp`                                             │
├───────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────┤
│ "Forbidden: Checkpoint must reside within..."  │ Path traversal security guard triggered. Ensure checkpoints are placed │
│                                               │ inside `checkpoints/` or `outputs/checkpoints/`.                       │
└───────────────────────────────────────────────┴────────────────────────────────────────────────────────────────────────┘
```

---
"""
