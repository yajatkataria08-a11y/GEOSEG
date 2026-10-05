"""
FastAPI Backend Server for GeoSeg.

Provides REST API endpoints for:
- Model training & progress monitoring
- Sliding-window multispectral inference
- Prediction results & checkpoint management
- Sentinel-2 AOI export integration
- Native C++ OOP processing engine execution
"""

import os
import sys
from pathlib import Path

# Ensure UTF-8 output encoding on Windows console
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.schemas import HealthResponse
from api.routes.training import router as training_router
from api.routes.inference import router as inference_router
from api.routes.results import router as results_router
from api.routes.aoi import router as aoi_router
from api.routes.cpp_engine import router as cpp_engine_router

# ─── App ─────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="GeoSeg API",
    description="Satellite Land Cover Segmentation — REST API",
    version="0.1.0",
)

# ─── CORS (allow React dev server) ───────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",    # Vite dev server
        "http://localhost:3000",    # Fallback
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from api.routes.super_resolution import router as super_resolution_router

# ─── Static outputs serving ──────────────────────────────────────────────────────

project_root = Path(__file__).resolve().parent.parent
os.makedirs(str(project_root / "outputs" / "predictions"), exist_ok=True)
os.makedirs(str(project_root / "outputs" / "sr_predictions"), exist_ok=True)
os.makedirs(str(project_root / "data" / "aid" / "samples"), exist_ok=True)

app.mount("/static/outputs", StaticFiles(directory=str(project_root / "outputs")), name="outputs")
app.mount("/static/sr", StaticFiles(directory=str(project_root / "outputs" / "sr_predictions")), name="sr_outputs")
app.mount("/static/aid", StaticFiles(directory=str(project_root / "data" / "aid" / "samples")), name="aid_samples")

# ─── API Routes ──────────────────────────────────────────────────────────────────

app.include_router(training_router)
app.include_router(inference_router)
app.include_router(results_router)
app.include_router(aoi_router)
app.include_router(cpp_engine_router)
app.include_router(super_resolution_router)


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """API health check — reports GPU availability."""
    gpu_available = False
    gpu_name = None

    try:
        import torch
        gpu_available = torch.cuda.is_available()
        if gpu_available:
            gpu_name = torch.cuda.get_device_name(0)
    except Exception:
        pass

    return HealthResponse(
        status="ok",
        gpu_available=gpu_available,
        gpu_name=gpu_name,
    )


@app.get("/api")
async def api_root():
    """Root endpoint — API info."""
    return {
        "name": "GeoSeg API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/api/health",
    }


# ─── Frontend SPA Mount (must be last to allow API routes precedence) ────────────

frontend_dist = project_root / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
