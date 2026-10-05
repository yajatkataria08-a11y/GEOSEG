"""
Sanity Check — Verify environment setup.

Run this after installing dependencies to confirm everything works:
    python scripts/sanity_check.py
"""

import sys

# Ensure UTF-8 output encoding on Windows console
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def check_import(module_name, display_name=None):
    """Try to import a module and report success/failure."""
    display_name = display_name or module_name
    try:
        mod = __import__(module_name)
        version = getattr(mod, "__version__", "installed")
        print(f"  [+] {display_name:<35} v{version}")
        return True
    except ImportError as e:
        print(f"  [-] {display_name:<35} MISSING ({e})")
        return False


def main():
    print("=" * 60)
    print("  Satellite Land Cover Segmentation — Sanity Check")
    print("=" * 60)
    print()

    # --- Core ML ---
    print("Core ML:")
    all_ok = True
    all_ok &= check_import("torch")
    all_ok &= check_import("torchvision")

    # CUDA check
    try:
        import torch
        cuda_available = torch.cuda.is_available()
        device_name = torch.cuda.get_device_name(0) if cuda_available else "N/A"
        status = f"✓ Available ({device_name})" if cuda_available else "⚠ Not available (CPU only)"
        print(f"  {'CUDA':<37} {status}")
    except Exception:
        print(f"  {'CUDA':<37} ⚠ Could not check")

    # --- Geospatial ML ---
    print("\nGeospatial ML:")
    all_ok &= check_import("torchgeo")
    all_ok &= check_import("segmentation_models_pytorch", "segmentation-models-pytorch")
    all_ok &= check_import("pytorch_lightning", "pytorch-lightning")
    all_ok &= check_import("torchmetrics")

    # --- Geospatial I/O ---
    print("\nGeospatial I/O:")
    all_ok &= check_import("rasterio")

    # --- Augmentation ---
    print("\nAugmentation & Processing:")
    all_ok &= check_import("kornia")
    all_ok &= check_import("albumentations")

    # --- Logging ---
    print("\nLogging & Visualization:")
    all_ok &= check_import("tensorboard")
    all_ok &= check_import("matplotlib")

    # --- Config ---
    print("\nConfig & Utilities:")
    all_ok &= check_import("yaml", "pyyaml")
    all_ok &= check_import("numpy")
    all_ok &= check_import("tqdm")

    # --- Optional (Phase 4) ---
    print("\nOptional (Phase 4 — Earth Engine):")
    check_import("ee", "earthengine-api")
    check_import("geemap")

    # --- src package ---
    print("\nProject Package:")
    src_ok = check_import("src", "src (editable install)")
    if not src_ok:
        print("    → Run 'pip install -e .' from the project root to fix this")

    # --- Summary ---
    print()
    print("=" * 60)
    if all_ok:
        print("  ✓ All required dependencies are installed!")
    else:
        print("  ⚠ Some dependencies are missing. See above for details.")
    print("=" * 60)

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
