"""
Training API routes — start, stop, and monitor training runs.
"""

import os
import sys
import uuid
import time
import threading
from pathlib import Path

from fastapi import APIRouter, HTTPException

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from api.schemas import (
    TrainingConfig,
    TrainingStartResponse,
    TrainingStatusResponse,
    TrainingMetrics,
    TrainingStatus,
)

router = APIRouter(prefix="/api/training", tags=["training"])

project_root = Path(__file__).resolve().parent.parent.parent
_state_lock = threading.Lock()

# ─── In-memory training state ────────────────────────────────────────────────────
_training_state = {
    "status": TrainingStatus.IDLE,
    "run_id": None,
    "phase": None,
    "current_epoch": 0,
    "total_epochs": 0,
    "best_metric": 0.0,
    "start_time": None,
    "metrics_history": [],
    "latest_metrics": None,
    "thread": None,
    "stop_flag": False,
    "error_message": "",
}


@router.post("/start", response_model=TrainingStartResponse)
async def start_training(config: TrainingConfig):
    """Start a new training run."""
    with _state_lock:
        if _training_state["status"] == TrainingStatus.RUNNING:
            raise HTTPException(
                status_code=409,
                detail="Training is already running. Stop it first.",
            )

    run_id = str(uuid.uuid4())[:8]
    phase = config.phase.value

    # Determine config path
    config_path = config.config_path
    if config_path is None:
        config_map = {
            1: "configs/phase1_eurosat.yaml",
            2: "configs/phase2_deepglobe.yaml",
            3: "configs/phase3_multispectral.yaml",
            4: "configs/phase4_aoi.yaml",
        }
        config_path = config_map.get(phase, "configs/phase1_eurosat.yaml")

    full_config_path = (project_root / config_path).resolve()
    if not full_config_path.exists():
        raise HTTPException(
            status_code=400,
            detail=f"Configuration file not found: '{config_path}'",
        )

    # Update state
    with _state_lock:
        _training_state["status"] = TrainingStatus.RUNNING
        _training_state["run_id"] = run_id
        _training_state["phase"] = phase
        _training_state["current_epoch"] = 0
        _training_state["total_epochs"] = config.epochs or 10
        _training_state["best_metric"] = 0.0
        _training_state["start_time"] = time.time()
        _training_state["metrics_history"] = []
        _training_state["latest_metrics"] = None
        _training_state["stop_flag"] = False
        _training_state["error_message"] = ""

    # Start training in background thread
    def train_background():
        try:
            import subprocess
            import re

            cmd = [
                sys.executable, "-u", "src/train.py",
                "--config", str(config_path),
            ]
            if config.epochs is not None:
                cmd.extend(["--epochs", str(config.epochs)])
            if config.lr is not None:
                cmd.extend(["--lr", str(config.lr)])
            if config.batch_size is not None:
                cmd.extend(["--batch-size", str(config.batch_size)])

            env = {**os.environ, "PYTHONUNBUFFERED": "1"}

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=str(project_root),
                env=env,
            )

            epoch_regex = re.compile(r"Epoch\s*\[(\d+)/(\d+)\]", re.IGNORECASE)
            metric_regex = re.compile(r"(loss|val_acc|mIoU)=([0-9\.]+)", re.IGNORECASE)
            last_lines = []

            for line in iter(process.stdout.readline, ""):
                last_lines.append(line.strip())
                if len(last_lines) > 20:
                    last_lines.pop(0)

                with _state_lock:
                    if _training_state["stop_flag"]:
                        process.terminate()
                        _training_state["status"] = TrainingStatus.STOPPED
                        return

                # Parse epoch logs with robust regex matching
                epoch_match = epoch_regex.search(line)
                if epoch_match:
                    try:
                        curr_ep = int(epoch_match.group(1))
                        tot_ep = int(epoch_match.group(2))

                        metrics_found = dict(metric_regex.findall(line))
                        loss = float(metrics_found.get("loss", 0.0))
                        val_metric = float(metrics_found.get("val_acc", metrics_found.get("mIoU", 0.0)))
                        metric_name = "val_acc" if "val_acc" in metrics_found else ("mIoU" if "mIoU" in metrics_found else "metric")

                        metric_obj = TrainingMetrics(
                            epoch=curr_ep,
                            total_epochs=tot_ep,
                            train_loss=loss,
                            val_metric=val_metric,
                            metric_name=metric_name,
                        )

                        with _state_lock:
                            _training_state["current_epoch"] = curr_ep
                            _training_state["total_epochs"] = tot_ep
                            _training_state["latest_metrics"] = metric_obj
                            _training_state["metrics_history"].append(metric_obj)
                            if val_metric > _training_state["best_metric"]:
                                _training_state["best_metric"] = val_metric
                    except Exception as parse_err:
                        print(f"Telemetry parse error: {parse_err}")

            process.wait()
            with _state_lock:
                if process.returncode == 0:
                    _training_state["status"] = TrainingStatus.COMPLETED
                else:
                    _training_state["status"] = TrainingStatus.FAILED
                    _training_state["error_message"] = "\n".join(last_lines[-5:]) if last_lines else "Process exited with error code"

        except Exception as e:
            with _state_lock:
                _training_state["status"] = TrainingStatus.FAILED
                _training_state["error_message"] = str(e)
            print(f"Training error: {e}")

    thread = threading.Thread(target=train_background, daemon=True)
    thread.start()
    with _state_lock:
        _training_state["thread"] = thread

    return TrainingStartResponse(
        success=True,
        message=f"Training started (Phase {phase}, run={run_id})",
        run_id=run_id,
    )


@router.get("/status", response_model=TrainingStatusResponse)
async def get_training_status():
    """Get current training progress."""
    with _state_lock:
        elapsed = 0.0
        if _training_state["start_time"]:
            elapsed = time.time() - _training_state["start_time"]

        msg = _training_state.get("error_message") or (
            f"Phase {_training_state['phase']} — "
            f"epoch {_training_state['current_epoch']}/{_training_state['total_epochs']}"
            if _training_state["phase"] is not None else "Idle"
        )

        return TrainingStatusResponse(
            status=_training_state["status"],
            phase=_training_state["phase"],
            current_epoch=_training_state["current_epoch"],
            total_epochs=_training_state["total_epochs"],
            metrics=_training_state["latest_metrics"],
            best_metric=_training_state["best_metric"],
            elapsed_seconds=elapsed,
            message=msg,
            history=list(_training_state["metrics_history"]),
        )


@router.post("/stop")
async def stop_training():
    """Stop the current training run."""
    with _state_lock:
        if _training_state["status"] != TrainingStatus.RUNNING:
            raise HTTPException(status_code=400, detail="No training is currently running.")
        _training_state["stop_flag"] = True

    return {"success": True, "message": "Stop signal sent."}
