"""
AOI Export API route — export Sentinel-2 satellite imagery for a given bounding box.
"""

import os
import sys
import uuid
from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, HTTPException

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from api.schemas import AOIExportRequest, AOIExportResponse

router = APIRouter(prefix="/api/aoi", tags=["aoi"])

EXPORT_DIR = "data/aoi_export"


@router.post("/export", response_model=AOIExportResponse)
async def export_aoi(request: AOIExportRequest):
    """
    Export Sentinel-2 L2A multispectral imagery for an Area of Interest (AOI).
    """
    if request.west >= request.east or request.south >= request.north:
        raise HTTPException(
            status_code=400,
            detail="Invalid bounding box: west must be < east and south must be < north.",
        )
    if not (-180 <= request.west <= 180 and -180 <= request.east <= 180):
        raise HTTPException(
            status_code=400,
            detail="Longitude must be between -180 and 180.",
        )
    if not (-90 <= request.south <= 90 and -90 <= request.north <= 90):
        raise HTTPException(
            status_code=400,
            detail="Latitude must be between -90 and 90.",
        )
    if request.start_date >= request.end_date:
        raise HTTPException(
            status_code=400,
            detail="start_date must be before end_date.",
        )

    task_id = str(uuid.uuid4())[:8]
    project_root = Path(__file__).resolve().parent.parent.parent
    export_folder = project_root / EXPORT_DIR
    export_folder.mkdir(parents=True, exist_ok=True)
    target_tif = export_folder / f"aoi_{task_id}.tif"

    # Try Google Earth Engine first if authenticated
    gee_success = False
    try:
        import ee
        ee.Initialize()
        region = ee.Geometry.Rectangle([request.west, request.south, request.east, request.north])
        s2 = (
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(region)
            .filterDate(request.start_date, request.end_date)
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", request.max_cloud_pct))
            .median()
            .clip(region)
        )
        task = ee.batch.Export.image.toDrive(
            image=s2.select(["B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B8A", "B9", "B11", "B12"]),
            description=f"aoi_export_{task_id}",
            folder="s2_exports",
            scale=request.scale,
            region=region,
            fileFormat="GeoTIFF",
        )
        task.start()
        gee_success = True
        return AOIExportResponse(
            success=True,
            message=f"Google Earth Engine export started (Task ID: {task.id}). Output will appear in Google Drive.",
            task_id=task.id,
            is_synthetic=False,
        )
    except Exception as e:
        # Fallback to local geospatial Sentinel-2 synthetic scene generator
        try:
            import numpy as np
            import rasterio
            from rasterio.transform import from_bounds

            # Generate synthetic 13-band Sentinel-2 GeoTIFF for the selected AOI
            height, width = 512, 512
            transform = from_bounds(request.west, request.south, request.east, request.north, width, height)
            
            # Synthetic 13 bands (reflectance 0-10000 matching Sentinel-2 L2A full bandset)
            data = np.random.randint(200, 4000, size=(13, height, width), dtype=np.uint16)
            
            with rasterio.open(
                str(target_tif),
                "w",
                driver="GTiff",
                height=height,
                width=width,
                count=13,
                dtype=data.dtype,
                crs="EPSG:4326",
                transform=transform,
            ) as dst:
                dst.write(data)

            # Copy to default aoi_export.tif
            default_tif = export_folder / "aoi_export.tif"
            import shutil
            shutil.copyfile(str(target_tif), str(default_tif))

            return AOIExportResponse(
                success=True,
                message=f"[SYNTHETIC] Demo Sentinel-2 scene generated (GEE not authenticated). File: {target_tif.name} for [{request.west:.2f}, {request.south:.2f}, {request.east:.2f}, {request.north:.2f}].",
                task_id=task_id,
                is_synthetic=True,
            )
        except Exception as local_err:
            raise HTTPException(
                status_code=500,
                detail=f"AOI Export failed: {local_err}",
            )
