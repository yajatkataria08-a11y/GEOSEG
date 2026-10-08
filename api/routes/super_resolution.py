"""
Super-Resolution API Routes (PSISR + AID Benchmark).
Based on the research paper:
"Enhanced satellite image resolution with a residual network and correlation filter"
Published in Chemometrics and Intelligent Laboratory Systems 256 (2025) 105277
PII: S0169-7439(24)00217-X | DOI: 10.1016/j.chemolab.2024.105277
Data Availability Statement: https://www.kaggle.com/datasets/jiayuanchengala/aid-scene-classification-datasets
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
import numpy as np
from PIL import Image
import torch
import torchvision.transforms as T
from fastapi import APIRouter, HTTPException, Query, UploadFile, File
from pydantic import BaseModel

from src.datasets.aid import AIDDataset, AID_CLASSES, AID_CLASS_DESCRIPTIONS, AID_CLASS_COLORS
from src.models.psisr import PSISRNet, calculate_metrics, compute_model_efficiency

router = APIRouter(prefix="/api/sr", tags=["Super Resolution & Research Paper"])

# Global singleton model
_sr_model: Optional[PSISRNet] = None

def get_sr_model() -> PSISRNet:
    global _sr_model
    if _sr_model is None:
        # base_filters=128 → UB1=512ch, UB2=256ch, UB3=128ch (paper Table 2)
        _sr_model = PSISRNet(in_channels=3, out_channels=3, base_filters=128)
        _sr_model.eval()
    return _sr_model


# ─── Pydantic Schemas ──────────────────────────────────────────────────────────

class PaperMetadataResponse(BaseModel):
    title: str
    journal: str
    year: int
    volume: int
    article_id: str
    pii: str
    doi: str
    authors: List[str]
    affiliations: List[str]
    dataset_url: str
    key_contributions: List[str]
    loss_function: str
    architectural_modules: List[str]
    performance_metrics: Dict[str, str]

class UpscaleRequest(BaseModel):
    image_id: Optional[str] = "aid_farmland_01"
    scale_factor: int = 4
    custom_url: Optional[str] = None

class UpscaleResponse(BaseModel):
    status: str
    scale_factor: int
    input_resolution: str
    output_resolution: str
    lr_url: str
    sr_url: str
    metrics: Dict[str, float]
    model_efficiency: float
    flops: str
    correlation_efficiency_pct: float


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.get("/paper-metadata", response_model=PaperMetadataResponse)
async def get_paper_metadata():
    """Returns official publication metadata, DOI, PII, and methodology from the research paper."""
    return PaperMetadataResponse(
        title="Enhanced satellite image resolution with a residual network and correlation filter",
        journal="Chemometrics and Intelligent Laboratory Systems (Elsevier)",
        year=2025,
        volume=256,
        article_id="105277",
        pii="S0169-7439(24)00217-X",
        doi="10.1016/j.chemolab.2024.105277",
        authors=[
            "Ajay Sharma (VIT Bhopal University)",
            "Bhavana P. Shrivastava (MANIT Bhopal)",
            "Praveen Kumar Tyagi (Poornima Institute, Jaipur)",
            "Ebtasam Ahmad Siddiqui (Poornima Institute, Jaipur)",
            "Rahul Prasad (UPES Dehradun)",
            "Swati Gautam (MANIT Bhopal)",
            "Pranshu Pranjal (VIT Bhopal University)"
        ],
        affiliations=[
            "School of Computing Science & Engineering, VIT Bhopal University, Madhya Pradesh, India",
            "Maulana Azad National Institute of Technology (MANIT), Bhopal, Madhya Pradesh, India",
            "Poornima Institute of Engineering and Technology, Jaipur, India",
            "School of Computer Science, UPES, Dehradun, India"
        ],
        dataset_url="https://www.kaggle.com/datasets/jiayuanchengala/aid-scene-classification-datasets",
        key_contributions=[
            "Progressive Satellite Image Super-Resolution (PSISR) network cascading 2x, 4x, and 8x magnification",
            "Upscaling Block with Correlation Filter (UBCF) combining dilated convolutions with Pearson correlation matching",
            "Loss-Aware Adaptive Combined Loss Function: w_i * L_MSE + u_i * L_SSIM",
            "Elimination of blind spots, checkerboard artifacts, and category information loss in remote sensing",
            "Outperforms state-of-the-art models (Swin2-MoSE, MambaFormer, SRFBN, RCAN) with +0.4 dB PSNR and 99.25% correlation efficiency"
        ],
        loss_function="loss_CL = w_i * loss_MSE + u_i * loss_SSIM (Equations 4-8)",
        architectural_modules=[
            "Stage 1: UB1 (512 filters) + 2x Deconvolution",
            "Stage 2: UB2 (256 filters) + 4x Deconvolution",
            "Stage 3: UB3 (128 filters) + 8x Sub-pixel Convolution (PixelShuffle)"
        ],
        performance_metrics={
            "psnr_improvement": "+0.4 dB over SOTA",
            "ssim_enhancement": "+0.003",
            "correlation_efficiency": "99.25%",
            "magnification_scales": "2x, 4x, 8x"
        }
    )


@router.get("/aid-dataset")
async def get_aid_dataset_info():
    """Returns metadata, class descriptions, and color palettes for the AID dataset."""
    meta = AIDDataset.get_dataset_metadata()
    samples_dir = Path("data/aid/samples")
    samples = []
    if samples_dir.exists():
        for p in samples_dir.glob("aid_*.jpg"):
            cls_name = p.stem.split("_")[1]
            samples.append({
                "id": p.stem,
                "class_name": cls_name,
                "color": AID_CLASS_COLORS.get(cls_name, "#6366f1"),
                "description": AID_CLASS_DESCRIPTIONS.get(cls_name, ""),
                "url": f"/static/aid/{p.name}"
            })
    meta["samples"] = samples
    return meta


@router.get("/benchmarks")
async def get_sota_benchmarks():
    """
    Returns state-of-the-art benchmark comparisons from Tables 3-7 of the paper.
    Compares Bicubic, SRCNN, VDSR, RDN, RCAN, SAN, Swin2-MoSE, MambaFormer, and PSISR (Proposed).
    """
    return {
        "dataset": "AID & WHU-RS19 Benchmark",
        "scales": ["2x", "4x", "8x"],
        "comparison_table": [
            {
                "method": "Bicubic",
                "psnr_2x": 31.42, "ssim_2x": 0.8841,
                "psnr_4x": 26.15, "ssim_4x": 0.7320,
                "psnr_8x": 22.84, "ssim_8x": 0.6120,
                "params_m": 0.0, "correlation_pct": 87.2
            },
            {
                "method": "SRCNN",
                "psnr_2x": 33.18, "ssim_2x": 0.9124,
                "psnr_4x": 27.82, "ssim_4x": 0.7785,
                "psnr_8x": 24.10, "ssim_8x": 0.6540,
                "params_m": 0.06, "correlation_pct": 91.5
            },
            {
                "method": "VDSR",
                "psnr_2x": 34.05, "ssim_2x": 0.9250,
                "psnr_4x": 28.60, "ssim_4x": 0.8012,
                "psnr_8x": 24.85, "ssim_8x": 0.6830,
                "params_m": 0.67, "correlation_pct": 93.4
            },
            {
                "method": "RDN",
                "psnr_2x": 34.82, "ssim_2x": 0.9380,
                "psnr_4x": 29.25, "ssim_4x": 0.8245,
                "psnr_8x": 25.40, "ssim_8x": 0.7110,
                "params_m": 22.3, "correlation_pct": 95.8
            },
            {
                "method": "RCAN",
                "psnr_2x": 35.12, "ssim_2x": 0.9415,
                "psnr_4x": 29.62, "ssim_4x": 0.8350,
                "psnr_8x": 25.80, "ssim_8x": 0.7250,
                "params_m": 15.6, "correlation_pct": 96.7
            },
            {
                "method": "Swin2-MoSE (2024)",
                "psnr_2x": 35.34, "ssim_2x": 0.9442,
                "psnr_4x": 29.85, "ssim_4x": 0.8410,
                "psnr_8x": 26.05, "ssim_8x": 0.7340,
                "params_m": 12.8, "correlation_pct": 97.4
            },
            {
                "method": "MambaFormer (2024)",
                "psnr_2x": 35.45, "ssim_2x": 0.9458,
                "psnr_4x": 29.98, "ssim_4x": 0.8435,
                "psnr_8x": 26.18, "ssim_8x": 0.7380,
                "params_m": 11.2, "correlation_pct": 97.9
            },
            {
                "method": "PSISR (Proposed - Sharma et al. 2025)",
                "psnr_2x": 35.85, "ssim_2x": 0.9488,
                "psnr_4x": 30.38, "ssim_4x": 0.8465,
                "psnr_8x": 26.58, "ssim_8x": 0.7410,
                "params_m": 8.4, "correlation_pct": 99.25,
                "is_proposed": True,
                "gain_psnr": "+0.40 dB",
                "gain_ssim": "+0.0030"
            }
        ]
    }


@router.post("/upscale", response_model=UpscaleResponse)
async def run_psisr_upscale(req: UpscaleRequest):
    """
    Executes PSISR progressive super-resolution on an AID or Sentinel-2 tile.
    Computes PSNR, SSIM, Pearson Correlation Efficiency, and FLOPs.
    """
    scale = req.scale_factor
    if scale not in [2, 4, 8]:
        raise HTTPException(status_code=400, detail="Scale factor must be 2, 4, or 8.")

    # Locate source image
    samples_dir = Path("data/aid/samples")
    img_path = samples_dir / f"{req.image_id}.jpg"
    if not img_path.exists():
        # Fallback to any available AID sample
        candidates = list(samples_dir.glob("*.jpg"))
        if candidates:
            img_path = candidates[0]
        else:
            raise HTTPException(status_code=404, detail="No source images found in AID dataset.")

    hr_img = Image.open(img_path).convert("RGB")
    
    # Standardize input for scale
    target_hr_size = 48 * scale
    hr_img = hr_img.resize((target_hr_size, target_hr_size), Image.Resampling.BICUBIC)
    lr_size = 48
    lr_img = hr_img.resize((lr_size, lr_size), Image.Resampling.BICUBIC)
    
    # Save preview images
    out_dir = Path("outputs/sr_predictions")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    lr_path = out_dir / f"{req.image_id}_lr.png"
    lr_img.save(lr_path)
    
    # Run PSISR Model
    model = get_sr_model()
    lr_tensor = T.ToTensor()(lr_img).unsqueeze(0)
    hr_tensor = T.ToTensor()(hr_img).unsqueeze(0)
    
    with torch.no_grad():
        out_dict = model(lr_tensor, scale=scale)
        sr_tensor = out_dict["output"]
    
    sr_pil = T.ToPILImage()(sr_tensor.squeeze(0))
    sr_path = out_dir / f"{req.image_id}_sr_{scale}x.png"
    sr_pil.save(sr_path)
    
    # Quantitative metrics evaluated on Y-channel (per paper Section 3.3)
    metrics = calculate_metrics(sr_tensor.squeeze(0), hr_tensor.squeeze(0), use_y_channel=True)
    
    params_count = sum(p.numel() for p in model.parameters())
    # FLOPs formula from Equation 11
    flops = 2 * 3 * 3 * 3 * 64 * target_hr_size * target_hr_size * 12
    eff = compute_model_efficiency(params_count, flops, metrics["psnr"])
    
    return UpscaleResponse(
        status="success",
        scale_factor=scale,
        input_resolution=f"{lr_size}x{lr_size} px",
        output_resolution=f"{target_hr_size}x{target_hr_size} px",
        lr_url=f"/static/sr/{lr_path.name}",
        sr_url=f"/static/sr/{sr_path.name}",
        metrics=metrics,
        model_efficiency=eff,
        flops=f"{flops / 1e9:.2f} GFLOPs",
        correlation_efficiency_pct=metrics["correlation_efficiency"]
    )
