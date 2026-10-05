"""
Pydantic schemas for the REST API.

Defines request/response models for training, inference, and results.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from enum import Enum
from datetime import datetime


# ─── Enums ───────────────────────────────────────────────────────────────────────

class Phase(int, Enum):
    EUROSAT = 1
    DEEPGLOBE = 2
    MULTISPECTRAL = 3
    AOI = 4


class TrainingStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


class InferenceStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ─── Training Schemas ────────────────────────────────────────────────────────────

class TrainingConfig(BaseModel):
    """Configuration for starting a training run."""
    phase: Phase = Field(..., description="Training phase (1-4)")
    config_path: Optional[str] = Field(None, description="Path to YAML config file")
    epochs: Optional[int] = Field(None, description="Override number of epochs")
    lr: Optional[float] = Field(None, description="Override learning rate")
    batch_size: Optional[int] = Field(None, description="Override batch size")


class TrainingMetrics(BaseModel):
    """Metrics from a single training epoch."""
    epoch: int
    total_epochs: int
    train_loss: float
    val_metric: float
    metric_name: str = "accuracy"
    per_class_iou: Optional[Dict[str, float]] = None
    lr: float = 0.0


class TrainingStatusResponse(BaseModel):
    """Current training status."""
    status: TrainingStatus
    phase: Optional[Phase] = None
    current_epoch: int = 0
    total_epochs: int = 0
    metrics: Optional[TrainingMetrics] = None
    best_metric: float = 0.0
    elapsed_seconds: float = 0.0
    message: str = ""
    history: List[TrainingMetrics] = []


class TrainingStartResponse(BaseModel):
    """Response when starting a training run."""
    success: bool
    message: str
    run_id: Optional[str] = None


# ─── Inference Schemas ───────────────────────────────────────────────────────────

class InferenceRequest(BaseModel):
    """Request to run inference on a GeoTIFF."""
    model_checkpoint: str = Field(
        "outputs/checkpoints/phase3/best_model.pth",
        description="Path to the model checkpoint",
    )
    tile_size: int = Field(512, description="Inference tile size")
    overlap: int = Field(32, description="Tile overlap in pixels")
    use_indices: bool = Field(True, description="Append spectral indices")


class InferenceResult(BaseModel):
    """Result of an inference run."""
    id: str
    status: InferenceStatus
    input_path: str
    output_path: Optional[str] = None
    class_distribution: Optional[Dict[str, float]] = None
    preview_url: Optional[str] = None
    timestamp: datetime
    elapsed_seconds: float = 0.0


# ─── Results Schemas ─────────────────────────────────────────────────────────────

class ResultSummary(BaseModel):
    """Summary of a past prediction result."""
    id: str
    input_filename: str
    output_filename: str
    phase: Phase
    metric_value: float
    timestamp: datetime
    preview_url: Optional[str] = None
    location_name: Optional[str] = None
    file_size_bytes: Optional[int] = None
    classes: Optional[List[Dict[str, Any]]] = None
    satellite_url: Optional[str] = None


class ResultListResponse(BaseModel):
    """List of all past results."""
    results: List[ResultSummary]
    total: int


# ─── AOI Export Schemas ──────────────────────────────────────────────────────────

class AOIExportRequest(BaseModel):
    """Request to export Sentinel-2 data for an AOI."""
    west: float = Field(..., description="Western longitude")
    south: float = Field(..., description="Southern latitude")
    east: float = Field(..., description="Eastern longitude")
    north: float = Field(..., description="Northern latitude")
    start_date: str = Field("2025-01-01", description="Start date (YYYY-MM-DD)")
    end_date: str = Field("2025-06-01", description="End date (YYYY-MM-DD)")
    max_cloud_pct: int = Field(10, description="Max cloud cover percentage")
    scale: int = Field(10, description="Resolution in meters")


class AOIExportResponse(BaseModel):
    """Response from an AOI export request."""
    success: bool
    message: str
    task_id: Optional[str] = None
    is_synthetic: bool = False


# ─── Health ──────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    """API health check response."""
    status: str = "ok"
    gpu_available: bool = False
    gpu_name: Optional[str] = None
    version: str = "0.1.0"


# ─── C++ Engine ──────────────────────────────────────────────────────────────────

class CppEngineRunResponse(BaseModel):
    """Response from running native C++ engine benchmarks."""
    success: bool
    execution_time_ms: float
    oop_paradigms: Dict[str, str]
    benchmarks: Dict[str, Any]
    output_log: str
