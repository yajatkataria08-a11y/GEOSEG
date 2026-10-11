# -*- coding: utf-8 -*-
"""Section 12: Comprehensive Repository Directory Structure & File Map."""

def get_section():
    return """# 12. COMPREHENSIVE REPOSITORY DIRECTORY STRUCTURE & FILE MAP

Below is the complete architectural map of the GeoSeg codebase, detailing the purpose and key responsibilities of every major directory and source file:

```
GEOSEG/
├── api/                                      # FastAPI REST API Backend Subsystem
│   ├── routes/                               # REST Endpoint Route Controllers
│   │   ├── __init__.py                       # Package initializer
│   │   ├── aoi.py                            # Area of Interest export & Earth Engine integration
│   │   ├── cpp_engine.py                     # Native C++ OOP execution & SIMD benchmarking
│   │   ├── inference.py                      # GeoTIFF tiled prediction & job lifecycle management
│   │   ├── results.py                        # Output catalog, mask preview & checkpoint discovery
│   │   ├── super_resolution.py               # PSISR 8x inference, benchmarks & AID catalog
│   │   └── training.py                       # Multi-phase training launcher & status streaming
│   ├── schemas.py                            # Pydantic v2 data models & request/response schemas
│   └── server.py                             # FastAPI app instantiation, CORS, & static mounts
│
├── backend/                                  # Native C++17 OOP Geospatial Processing Engine
│   ├── include/                              # C++ Header Files (Classes, Interfaces, Templates)
│   │   ├── BandMathEngine.h                  # Derived processor for multi-band spectral index math
│   │   ├── GeoTIFFHandler.h                  # RAII-managed file reader/writer preserving EPSG
│   │   ├── Image.h                           # Generic Image<T> template with operator overloads
│   │   ├── ImageProcessor.h                  # Pure virtual abstract base class interface
│   │   ├── SpectralIndex.h                   # Polymorphic hierarchy: NDVI, NDWI, NDBI, Factory
│   │   └── TileManager.h                     # Sliding-window tiling & feather-weighted stitching
│   ├── src/                                  # C++ Implementation Files
│   │   ├── BandMathEngine.cpp                # Implementation of parallel spectral calculations
│   │   ├── GeoTIFFHandler.cpp                # Implementation of RAII binary I/O operations
│   │   ├── TileManager.cpp                   # Implementation of distance-weighted feather blending
│   │   └── main.cpp                          # Standalone C++ verification executable entrypoint
│   ├── CMakeLists.txt                        # Cross-platform CMake build configuration
│   └── geoseg_backend.exe                    # Compiled native Windows x64 binary
│
├── checkpoints/                              # Saved Neural Network Model Checkpoints
│   └── psisr/                                # Progressive Super-Resolution Weights
│       └── best_model.pth                    # Trained PSISRNet model weights (275.1 MB)
│
├── configs/                                  # YAML Configuration Files for Training & Pipeline
│   ├── phase1_eurosat.yaml                   # 10-Class baseline patch classifier configuration
│   ├── phase2_deepglobe.yaml                 # 7-Class RGB optical baseline configuration
│   ├── phase3_multispectral.yaml             # 16-Channel full multispectral U-Net configuration
│   ├── phase4_aoi.yaml                       # Sentinel-2 AOI custom inference configuration
│   └── psisr_aid.yaml                        # Progressive Super-Resolution AID training config
│
├── data/                                     # Local Data Ingestion & Storage Directories
│   ├── aid/                                  # Aerial Image Dataset (AID) local cache
│   │   └── samples/                          # 30 Representative sample JPEG images
│   ├── aoi_export/                           # Downloaded Sentinel-2 satellite tiles
│   └── uploads/                              # Temporary user-uploaded GeoTIFF rasters
│
├── frontend/                                 # React 18 / TypeScript / Vite 5 Web Client
│   ├── public/                               # Static Web Assets & Thumbnails
│   │   └── previews/                         # Pre-computed true color & classified mask PNGs
│   │       ├── aid/                          # Sample JPEG thumbnails for all 30 AID classes
│   │       ├── sr/                           # Pre-computed 1x, 4x, 8x PSISR preview images
│   │       ├── bhopal_sat.png                # True-color Sentinel-2 image of Bhopal Upper Lake
│   │       └── bhopal_mask.png               # Classified land cover mask of Bhopal Upper Lake
│   ├── src/                                  # TypeScript Source Code
│   │   ├── assets/                           # Bundled media & textures
│   │   │   └── nasa-earth.jpg                # NASA Blue Marble equirectangular Earth texture
│   │   ├── components/                       # Reusable UI Component Library
│   │   │   ├── common/                       # Design system core components
│   │   │   │   ├── Badge.tsx                 # Status pill badge component
│   │   │   │   ├── Button.tsx                # Glow-accent and glassmorphic buttons
│   │   │   │   ├── Card.tsx                  # Translucent backdrop card container
│   │   │   │   ├── CosmicBackground.tsx      # 60fps dynamic starfield canvas
│   │   │   │   ├── EarthGlobe.tsx            # Interactive 3D Canvas Earth Globe
│   │   │   │   └── Loading.tsx               # Animated spinner and skeleton loaders
│   │   │   ├── Dashboard/                    # Training telemetry visualizations
│   │   │   │   ├── PhaseTracker.tsx          # 4-Phase pipeline progression stepper
│   │   │   │   └── TrainingProgress.tsx      # Live SVG loss and mIoU convergence curves
│   │   │   ├── Layout/                       # Application structure components
│   │   │   │   ├── Footer.tsx                # Bottom attribution and license strip
│   │   │   │   ├── Navbar.tsx                # Sticky top bar with active navigation pill
│   │   │   │   └── SystemDrawer.tsx          # Slide-out system diagnostic drawer
│   │   │   ├── Map/                          # Geospatial mapping components
│   │   │   │   ├── AOIMap.tsx                # Leaflet map with bounding box drawer
│   │   │   │   └── MapControls.tsx           # Satellite layer provider selector
│   │   │   ├── Upload/                       # File ingestion components
│   │   │   │   └── FileUpload.tsx            # GeoTIFF drag-and-drop dropzone
│   │   │   └── Visualization/                # Prediction analysis tools
│   │   │       ├── PredictionViewer.tsx      # Interactive raster inspection canvas
│   │   │       ├── RasterMapViewer.tsx       # Side-by-side true color vs mask viewer
│   │   │       └── SpectralIndices.tsx       # RGB vs False-color NDVI comparison
│   │   ├── pages/                            # Top-Level Page Views
│   │   │   ├── CppDemo.tsx                   # Live C++ OOP execution console
│   │   │   ├── Home.tsx                      # Mission command hero & 3D Earth Globe
│   │   │   ├── Inference.tsx                 # GeoTIFF upload & prediction dashboard
│   │   │   ├── MapView.tsx                   # Interactive satellite explorer
│   │   │   ├── Results.tsx                   # Historical prediction catalog & downloads
│   │   │   ├── SuperResolution.tsx           # PSISR 8x magnification & SOTA benchmarks
│   │   │   └── Training.tsx                  # Hyperparameter config & loss stream
│   │   ├── services/                         # Client-Side API Network Clients
│   │   │   ├── api.ts                        # Base fetch client with snake_case mapping
│   │   │   ├── inferenceApi.ts               # Predict & AOI export HTTP calls
│   │   │   ├── superResolutionApi.ts         # Benchmarks, metadata, & upscale API calls
│   │   │   └── trainingApi.ts                # Training lifecycle control API calls
│   │   ├── types/                            # TypeScript Data Interfaces & Enums
│   │   │   ├── inference.ts                  # Job status, dimensions, & class distributions
│   │   │   ├── map.ts                        # Bounding boxes, presets, & export forms
│   │   │   └── training.ts                   # Training configs, metrics, & phases
│   │   ├── utils/                            # Helper Utilities
│   │   │   ├── animations.ts                 # Framer Motion spring physics configurations
│   │   │   └── caseTransform.ts              # Recursive camelCase <-> snake_case transformer
│   │   ├── App.tsx                           # Main React router & layout orchestrator
│   │   ├── index.css                         # Tailwind CSS v4 styling directives
│   │   └── main.tsx                          # React 18 DOM mount entrypoint
│   ├── index.html                            # HTML5 root template
│   ├── package.json                          # Node.js dependencies & scripts
│   ├── tsconfig.json                         # TypeScript strict compiler configuration
│   └── vite.config.ts                        # Vite bundler configuration & proxy rules
│
├── outputs/                                  # Model Predictions & Visual Outputs
│   ├── predictions/                          # Classified output GeoTIFF rasters
│   └── sr_predictions/                       # Super-resolved high-definition PNGs
│
├── scripts/                                  # Automated Operational & Setup Scripts
│   ├── populate_aid_samples.py               # Copies sample scenes for all 30 AID classes
│   └── build_full_readme.py                  # Generates the 10,000+ line master documentation
│
├── src/                                      # Core PyTorch Machine Learning Pipeline
│   ├── datasets/                             # Geospatial Dataset Loaders
│   │   ├── aid.py                            # AID Kaggle dataset multi-scale pair loader
│   │   ├── deepglobe.py                      # DeepGlobe optical RGB dataset loader
│   │   ├── eurosat.py                        # EuroSAT 10-class patch dataset loader
│   │   └── sen12ms.py                        # SEN12MS 13-band Sentinel-2 dataset loader
│   ├── models/                               # Deep Learning Neural Architectures
│   │   ├── psisr.py                          # Sharma et al. (2025) Cascading UBCF PSISRNet
│   │   └── segmentation.py                   # 16-Channel ResNet-34 Multispectral U-Net
│   ├── utils/                                # Machine Learning Utilities
│   │   ├── checkpoint.py                     # Safe PyTorch state_dict checkpoint loader/saver
│   │   ├── metrics.py                        # IoU, mIoU, Dice, and accuracy calculators
│   │   └── visualization.py                  # Raster colorization with WorldCover palettes
│   ├── infer.py                              # Sliding-window GeoTIFF tiled inference CLI
│   ├── train.py                              # Multi-phase segmentation training pipeline
│   └── train_psisr.py                        # Multi-scale progressive PSISR training engine
│
├── tests/                                    # Automated Verification Test Suite
│   ├── test_aid_dataset.py                   # Tests AID dataset loading and 30 classes
│   ├── test_models.py                        # Tests tensor shapes and parameter counts
│   └── test_api.py                           # Tests FastAPI endpoints and schemas
│
├── requirements.txt                          # Python 3.12 package dependencies
└── README.md                                 # Master Project Documentation
```

---
"""
