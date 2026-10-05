"""
Inference API routes — upload GeoTIFF, run prediction, download result.
"""

import os
import sys
import uuid
import time
import shutil
import threading
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from api.schemas import InferenceRequest, InferenceResult, InferenceStatus

router = APIRouter(prefix="/api/inference", tags=["inference"])

# In-memory job store
_inference_jobs: dict = {}

UPLOAD_DIR = "data/uploads"
OUTPUT_DIR = "outputs/predictions"


@router.post("/predict", response_model=InferenceResult)
async def run_inference(
    file: UploadFile = File(...),
    tile_size: int = 512,
    overlap: int = 32,
    use_indices: bool = True,
    checkpoint: str = "outputs/checkpoints/phase3/best_model.pth",
):
    """
    Upload a GeoTIFF and run segmentation inference safely.
    Returns immediately with a job ID. Poll /result/{id} for status.
    """
    # 1. Sanitize file name & validate extension
    raw_filename = Path(file.filename).name
    if not (raw_filename.lower().endswith(".tif") or raw_filename.lower().endswith(".tiff")):
        raise HTTPException(status_code=400, detail="Invalid file type. Only GeoTIFF (.tif, .tiff) files are accepted.")

    # 2. Checkpoint path security whitelist validation
    project_root = Path(__file__).resolve().parent.parent.parent
    allowed_checkpoint_dir = (project_root / "outputs" / "checkpoints").resolve()
    target_ckpt = (project_root / checkpoint).resolve()

    if not target_ckpt.is_relative_to(allowed_checkpoint_dir):
        raise HTTPException(status_code=400, detail="Forbidden: Checkpoint must reside within outputs/checkpoints/")

    if not target_ckpt.is_file():
        raise HTTPException(status_code=400, detail=f"Checkpoint file not found: {checkpoint}")

    job_id = str(uuid.uuid4())[:8]

    # 3. Save uploaded file safely
    os.makedirs(os.path.join(str(project_root), UPLOAD_DIR), exist_ok=True)
    os.makedirs(os.path.join(str(project_root), OUTPUT_DIR), exist_ok=True)

    safe_input_name = f"{job_id}_{raw_filename}"
    input_path = os.path.join(str(project_root), UPLOAD_DIR, safe_input_name)

    # Read and check size
    file_content = await file.read()
    if len(file_content) > 100 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 100MB.")

    with open(input_path, "wb") as f:
        f.write(file_content)

    output_path = os.path.join(str(project_root), OUTPUT_DIR, f"{job_id}_prediction.tif")

    # Create job entry
    job = InferenceResult(
        id=job_id,
        status=InferenceStatus.PENDING,
        input_path=os.path.relpath(input_path, str(project_root)),
        output_path=os.path.relpath(output_path, str(project_root)),
        timestamp=datetime.now(),
    )
    _inference_jobs[job_id] = job

    # Run inference in background using safe subprocess execution (sys.argv)
    def run_background():
        try:
            _inference_jobs[job_id].status = InferenceStatus.PROCESSING
            start_time = time.time()

            import subprocess
            cmd = [
                sys.executable,
                "src/infer.py",
                "--input", input_path,
                "--output", output_path,
                "--checkpoint", str(target_ckpt),
                "--tile-size", str(tile_size),
                "--overlap", str(overlap),
                "--device", "cuda" if __import__("torch").cuda.is_available() else "cpu",
            ]
            if use_indices:
                cmd.append("--use-indices")

            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(project_root),
            )

            elapsed = time.time() - start_time

            if process.returncode == 0:
                _inference_jobs[job_id].status = InferenceStatus.COMPLETED
                _inference_jobs[job_id].elapsed_seconds = round(elapsed, 2)
                _inference_jobs[job_id].preview_url = f"/api/results/preview/{job_id}"
            else:
                _inference_jobs[job_id].status = InferenceStatus.FAILED
                print(f"Inference error output: {process.stderr}")

        except Exception as e:
            _inference_jobs[job_id].status = InferenceStatus.FAILED
            print(f"Inference worker exception: {e}")

    thread = threading.Thread(target=run_background, daemon=True)
    thread.start()

    return job


@router.get("/result/{job_id}", response_model=InferenceResult)
async def get_inference_result(job_id: str):
    """Get the status/result of an inference job."""
    if job_id not in _inference_jobs:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    return _inference_jobs[job_id]


@router.get("/jobs")
async def list_inference_jobs():
    """List all inference jobs."""
    return {
        "jobs": list(_inference_jobs.values()),
        "total": len(_inference_jobs),
    }
