"""
Google Earth Engine — Sentinel-2 AOI Export Script.

Exports a cloud-free median composite of Sentinel-2 L2A imagery
for a specified area of interest and date range.

Usage:
    python scripts/export_aoi.py --config configs/phase4_aoi.yaml

Prerequisites:
    - Google Earth Engine account (earthengine.google.com)
    - GCP project with Earth Engine API enabled
    - Run `earthengine authenticate` once

Alternative:
    Manually download from the Copernicus Browser:
    https://browser.dataspace.copernicus.eu/
"""

import argparse
import os
import sys
import yaml

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load_config(config_path: str) -> dict:
    """Load YAML config."""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser(description="Export Sentinel-2 AOI via Google Earth Engine")
    parser.add_argument("--config", type=str, required=True, help="Path to YAML config file")
    args = parser.parse_args()

    config = load_config(args.config)
    aoi_config = config["aoi_export"]

    # ─── Authenticate & Initialize ───────────────────────────────────────────
    try:
        import ee
    except ImportError:
        print("ERROR: earthengine-api not installed.")
        print("Install with: pip install earthengine-api")
        print("\nAlternative: download manually from Copernicus Browser:")
        print("  https://browser.dataspace.copernicus.eu/")
        sys.exit(1)

    print("Authenticating with Google Earth Engine...")
    try:
        ee.Authenticate()
    except Exception as e:
        print(f"Authentication failed: {e}")
        print("Run 'earthengine authenticate' in your terminal first.")
        sys.exit(1)

    gcp_project = aoi_config.get("gcp_project", "your-gcp-project")
    if gcp_project == "your-gcp-project":
        print("\n⚠  WARNING: Using placeholder GCP project name.")
        print("  Edit configs/phase4_aoi.yaml → aoi_export.gcp_project")
        print("  with your actual GCP project ID.\n")

    ee.Initialize(project=gcp_project)
    print("Earth Engine initialized.")

    # ─── Define AOI ──────────────────────────────────────────────────────────
    region_coords = aoi_config["region"]  # [west, south, east, north]
    region = ee.Geometry.Rectangle(region_coords)

    date_range = aoi_config["date_range"]
    max_cloud = aoi_config.get("max_cloud_pct", 10)

    print(f"\nAOI: [{region_coords[0]:.4f}, {region_coords[1]:.4f}] → "
          f"[{region_coords[2]:.4f}, {region_coords[3]:.4f}]")
    print(f"Date range: {date_range[0]} → {date_range[1]}")
    print(f"Max cloud %: {max_cloud}")

    # ─── Build Sentinel-2 Composite ──────────────────────────────────────────
    s2 = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(region)
        .filterDate(date_range[0], date_range[1])
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", max_cloud))
        .median()
        .clip(region)
    )

    # Count available scenes
    scene_count = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(region)
        .filterDate(date_range[0], date_range[1])
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", max_cloud))
        .size()
        .getInfo()
    )
    print(f"Scenes matched: {scene_count}")

    if scene_count == 0:
        print("\n⚠  No scenes found! Try:")
        print("  - Expanding the date range")
        print("  - Increasing max_cloud_pct")
        print("  - Checking the AOI coordinates")
        sys.exit(1)

    # ─── Select Bands ────────────────────────────────────────────────────────
    # Band names in GEE use different naming than our pipeline
    infer_config = config.get("inference", {})
    band_order = infer_config.get("band_order", [
        "B02", "B03", "B04", "B05", "B06", "B07", "B08", "B8A", "B09", "B11", "B12"
    ])

    # GEE uses B2, B3, etc. (no leading zero for some bands)
    # Convert our format to GEE format
    gee_bands = []
    for band in band_order:
        # GEE naming: B2, B3, B4, ..., B8A, B9, B11, B12
        gee_name = band.replace("B0", "B")  # B02 → B2, B03 → B3, etc.
        if band == "B8A":
            gee_name = "B8A"  # Special case — already correct
        gee_bands.append(gee_name)

    print(f"Bands: {gee_bands}")

    # ─── Export to Drive ─────────────────────────────────────────────────────
    export_folder = aoi_config.get("export_folder", "s2_exports")
    scale = aoi_config.get("scale", 10)

    task = ee.batch.Export.image.toDrive(
        image=s2.select(gee_bands),
        description="aoi_sentinel2_export",
        folder=export_folder,
        scale=scale,
        region=region,
        fileFormat="GeoTIFF",
        maxPixels=1e9,
    )
    task.start()

    print(f"\n✓ Export task started!")
    print(f"  Destination: Google Drive/{export_folder}/")
    print(f"  Scale: {scale}m/pixel")
    print(f"  Format: GeoTIFF")
    print(f"\nMonitor progress at: https://code.earthengine.google.com/tasks")
    print(f"\nOnce complete, download the GeoTIFF from Drive and place it at:")
    print(f"  {infer_config.get('input_tif', 'data/aoi_export/aoi_export.tif')}")
    print(f"\nThen run inference:")
    print(f"  python src/infer.py --config {args.config}")


if __name__ == "__main__":
    main()
