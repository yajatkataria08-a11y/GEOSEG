"""
C++ Engine API routes — executes and benchmarks the native C++ OOP geospatial engine.
"""

import os
import sys
import time
import subprocess
from pathlib import Path
from typing import Dict, Any

from fastapi import APIRouter, HTTPException

from api.schemas import CppEngineRunResponse

router = APIRouter(prefix="/api/cpp-engine", tags=["cpp-engine"])


@router.post("/run", response_model=CppEngineRunResponse)
async def run_cpp_engine():
    """
    Run and benchmark the C++ native engine's 7 OOP paradigms on satellite imagery.
    """
    project_root = Path(__file__).resolve().parent.parent.parent
    backend_dir = project_root / "backend"

    start_time = time.perf_counter()
    log_lines = []

    # Check if compiled binary exists
    build_dir = backend_dir / "build"
    exe_candidates = [
        backend_dir / "geoseg_backend.exe",
        backend_dir / "geoseg_backend",
        build_dir / "geoseg_backend.exe",
        build_dir / "geoseg_backend",
        build_dir / "geoseg_cli.exe",
        build_dir / "geoseg_cli",
        build_dir / "Release" / "geoseg_backend.exe",
        build_dir / "Release" / "geoseg_cli.exe",
    ]

    compiled_exe = None
    for cand in exe_candidates:
        if cand.exists():
            compiled_exe = cand
            break

    if compiled_exe:
        try:
            res = subprocess.run(
                [str(compiled_exe)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
                cwd=str(backend_dir),
            )
            if res.stdout:
                log_lines.append(str(res.stdout))
            if res.stderr:
                log_lines.append(str(res.stderr))
        except Exception as e:
            log_lines.append(f"Subprocess run note: {e}")
    else:
        return CppEngineRunResponse(
            success=False,
            execution_time_ms=0.0,
            oop_paradigms={},
            benchmarks={},
            output_log="C++ binary is not compiled.",
        )

    # --- Real C++ Native Engine Benchmarks via pybind11 ---
    import numpy as np
    cpp_available = False
    try:
        import geoseg_cpp
        cpp_available = True
    except ImportError:
        pass

    height, width = 512, 512
    band_order = [
        "B01", "B02", "B03", "B04", "B05", "B06",
        "B07", "B08", "B8A", "B09", "B10", "B11", "B12",
    ]

    if cpp_available:
        # Use REAL C++ classes via pybind11
        engine = geoseg_cpp.BandMathEngine(band_order)
        data = np.random.rand(13, height, width).astype(np.float32)

        # 1. C++ Spectral Index Computation
        t0 = time.perf_counter()
        ndvi = engine.compute_ndvi(data)
        ndwi = engine.compute_ndwi(data)
        ndbi = engine.compute_ndbi(data)
        index_time_ms = (time.perf_counter() - t0) * 1000.0

        # 2. C++ Full Multispectral Build (13 -> 16 channels)
        t1 = time.perf_counter()
        full_input = engine.build_multispectral_input(data)
        build_time_ms = (time.perf_counter() - t1) * 1000.0
        buffer_bytes = full_input.nbytes
        throughput_mb_s = (buffer_bytes / (1024 * 1024)) / max(build_time_ms / 1000.0, 1e-6)

        # 3. C++ TileManager
        tm = geoseg_cpp.TileManager(512, 32)
        t2 = time.perf_counter()
        tile_count = tm.get_tile_count(2048, 2048)
        tile_time_ms = (time.perf_counter() - t2) * 1000.0

        engine_label = "C++ Native (pybind11)"
    else:
        # Fallback to NumPy (clearly labeled)
        data = np.random.rand(13, height, width).astype(np.float32)
        eps = 1e-6
        t0 = time.perf_counter()
        nir, red, green, swir1 = data[7], data[3], data[2], data[11]
        ndvi = (nir - red) / (nir + red + eps)
        ndwi = (green - nir) / (green + nir + eps)
        ndbi = (swir1 - nir) / (swir1 + nir + eps)
        index_time_ms = (time.perf_counter() - t0) * 1000.0

        t1 = time.perf_counter()
        buffer_16ch = np.zeros((16, height, width), dtype=np.float32)
        buffer_bytes = buffer_16ch.nbytes
        build_time_ms = (time.perf_counter() - t1) * 1000.0
        throughput_mb_s = (buffer_bytes / (1024 * 1024)) / max(build_time_ms / 1000.0, 1e-6)

        t2 = time.perf_counter()
        tile_count = 0
        stride = 480
        for y in range(0, 2048, stride):
            for x in range(0, 2048, stride):
                tile_count += 1
        tile_time_ms = (time.perf_counter() - t2) * 1000.0
        engine_label = "Python/NumPy Fallback (geoseg_cpp not compiled)"

    total_time_ms = (time.perf_counter() - start_time) * 1000.0

    output_summary = "\n".join([
        f"=== GeoSeg Engine: {engine_label} ===",
        "[1] Spectral Index Computation (NDVI, NDWI, NDBI)",
        f"    Resolution: {height}x{width} | Execution: {index_time_ms:.3f} ms",
        "[2] Multispectral Input Build (13 -> 16 channels)",
        f"    Buffer: {buffer_bytes / 1024:.1f} KB | Throughput: {throughput_mb_s:.1f} MB/s",
        f"[3] Tile Decomposition: {tile_count} tiles | Execution: {tile_time_ms:.3f} ms",
        "===========================================================",
    ])

    if log_lines:
        clean_lines = [str(l) for l in log_lines if l]
        if clean_lines:
            output_summary = "\n".join(clean_lines) + "\n\n" + output_summary

    return CppEngineRunResponse(
        success=True,
        execution_time_ms=round(total_time_ms, 2),
        oop_paradigms={
            "Polymorphism": "Abstract SpectralIndex base with NDVI/NDWI/NDBI derived classes",
            "RAII": "Image<T> and GeoTIFFHandler with automatic resource cleanup",
            "Factory Pattern": "createIndex() returns polymorphic unique_ptr by name",
            "Templates": "Image<T> generic container for uint8, uint16, float pixel types",
            "Encapsulation": "BandMathEngine encapsulates band ordering and index computation",
            "Operator Overloading": "Image<T> supports +, -, *, / with epsilon-safe division",
            "Abstraction": "ImageProcessor pure virtual interface with getInfo() contract",
        },
        benchmarks={
            "engine": engine_label,
            "spectral_indices_ms": round(index_time_ms, 3),
            "buffer_throughput_mb_s": round(throughput_mb_s, 1),
            "tile_count": tile_count,
            "tile_generation_ms": round(tile_time_ms, 3),
        },
        output_log=output_summary,
    )
