# -*- coding: utf-8 -*-
"""Section 10: Frontend UI/UX Architecture & Component System."""

def get_section():
    return """# 10. FRONTEND UI/UX ARCHITECTURE & COMPONENT SYSTEM

The GeoSeg user interface was conceived as a high-technology **Earth Observation Cockpit**. Built using **React 18, TypeScript, Vite 5, Tailwind CSS v4, and Framer Motion**, the application marries publication-grade scientific rigor with intuitive, 60fps interactive visual storytelling.

---

## 10.1 React 18, Vite 5, Tailwind CSS v4 & Framer Motion Stack

```
  ┌─────────────────────────────────────────────────────────────────────────────┐
  │                            FRONTEND TECH STACK                              │
  ├─────────────────────────────────────────────────────────────────────────────┤
  │ Core UI Framework:     React 18.3 (Concurrent Mode, Fiber Reconciler)      │
  │ Language:              TypeScript 5.6 (Strict Type Safety, Zero Any)       │
  │ Bundler / Dev Server:  Vite 5.4 (Rollup Engine, Lightning Hot Module Reload)│
  │ Styling Engine:        Tailwind CSS v4 (Oxide Rust-Powered Engine)         │
  │ Animation Subsystem:   Framer Motion 11 (Hardware-Accelerated Physics)     │
  │ GIS Mapping:           Leaflet 1.9 + React-Leaflet                         │
  │ Vector Iconography:    Lucide React (Feather Icon Derivatives)             │
  │ Texture Rendering:     HTML5 Canvas 2D Orthographic Texture Mapping        │
  └─────────────────────────────────────────────────────────────────────────────┘
```

### The Vite Reverse-Proxy Configuration
In `frontend/vite.config.ts`, Vite is configured to reverse-proxy all API traffic directly to the FastAPI backend running on port 8000:
```typescript
export default defineConfig({
  plugins: [react()],
  server: {
    host: '127.0.0.1',
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/static': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
});
```
This guarantees that all network calls from the browser hit `/api/*` and `/static/*` locally without triggering browser Cross-Origin Resource Sharing (CORS) security blocks!

---

## 10.2 Interactive 3D Earth Globe with NASA Blue Marble Texture

A centerpiece of the user experience is the custom-built **3D Earth Globe** located in `frontend/src/components/common/EarthGlobe.tsx`. Rather than importing heavy multi-megabyte 3D engine libraries (e.g., Three.js), GeoSeg implements a lightweight, high-performance **HTML5 Canvas 2D Orthographic Projection Engine**:

```
                              [ NASA Blue Marble JPG Texture ]
                                             │
                                             ▼
                                  [ Canvas 2D Context ]
                                             │
                             ┌───────────────┴───────────────┐
                             │  Orthographic Spherical Math  │
                             │  - Radius: 175px (Scaled)     │
                             │  - Dynamic Yaw Rotation (λ)   │
                             │  - Clamped Pitch Tilt (φ)     │
                             └───────────────┬───────────────┘
                                             │
                                             ▼
                             [ Dual Elliptical Orbit Rings ]
                             - Orbit 1: Cyan Sentinel-2A Dot
                             - Orbit 2: Purple Sat Dot
                                             │
                                             ▼
                                 [ 3 Geodetic Target Pins ]
                                 - Pin 1: Sentinel-2A Polar
                                 - Pin 2: Bhopal AOI (23°N, 77°E)
                                 - Pin 3: California AOI (34°N, 118°W)
```

### Key Engineering Features of the Earth Globe:
1. **Photorealistic NASA Texture**: Maps authentic NASA *Blue Marble: Next Generation* optical imagery onto the sphere.
2. **Smooth 60fps Continuous Auto-Rotation**: An optimized `requestAnimationFrame` loop continuously increments longitude rotation.
3. **Pointer Drag-to-Rotate Physics**:
   - Horizontal drag updates longitude yaw angle smoothly.
   - Vertical drag updates latitude pitch tilt, strictly clamped between **$-28^\circ$ and $+28^\circ$** to prevent inverted pole disorientation.
4. **Mouse Wheel Zoom**: Lets evaluators zoom the globe between **$0.85\times$ and $1.35\times$ magnification**.
5. **Two Animated Orbit Rings**: Slanted elliptical orbital trajectories with pulsing satellite dots orbiting the globe in real time.
6. **Three Interactive Geodetic Target Pins**:
   - *Sentinel-2A Orbit Node*
   - *Bhopal Upper Lake Basin AOI* ($23.25^\circ\text{N}, 77.375^\circ\text{E}$)
   - *California Central Valley AOI* ($34.025^\circ\text{N}, 118.325^\circ\text{W}$)
7. **Floating Controls Dock**: Quick buttons to toggle auto-rotation, zoom in, zoom out, or reset the globe to its prime meridian orientation.

---

## 10.3 Component-by-Component Architectural Inspection

```
┌────────────────────────┬──────────────────────┬────────────────────────────────────────────────────────┐
│ Component File         │ Subsystem            │ Primary Role & Interactive Behavior                    │
├────────────────────────┼──────────────────────┼────────────────────────────────────────────────────────┤
│ CosmicBackground.tsx   │ Visual Atmosphere    │ 60fps dynamic starfield canvas with drifting nebulae.  │
│ EarthGlobe.tsx         │ 3D Visualization     │ Orthographic NASA globe with interactive drag & orbits.│
│ Navbar.tsx             │ Global Navigation    │ Top bar with glowing active tab pill & CUDA badge.     │
│ SystemDrawer.tsx       │ Telemetry & Health   │ Slide-out diagnostics drawer with live GPU & API stats.│
│ PredictionViewer.tsx   │ Raster Inspection    │ Zoomable canvas viewer for classified GeoTIFF outputs. │
│ RasterMapViewer.tsx    │ Side-by-Side GIS     │ Synchronized split view (True Color vs Classified Mask)│
│ SpectralIndices.tsx    │ Spectral Analytics   │ RGB composite vs NDVI false-color heatmap viewer.      │
│ FileUpload.tsx         │ Data Ingestion       │ Drag-and-drop GeoTIFF upload box with size validation. │
│ AOIMap.tsx             │ Leaflet GIS Selector │ Multi-provider map with bounding-box rectangle drawer. │
│ MapControls.tsx        │ GIS Layer Switching  │ Toggle between Google, ISRO Bhuvan, Esri, OSM, NDVI.   │
│ TrainingProgress.tsx   │ Training Telemetry   │ Real-time SVG convergence curves for loss & mIoU.      │
│ PhaseTracker.tsx       │ Project Milestones   │ Visual 4-phase progress pipeline stepper.              │
│ Button.tsx             │ Design System        │ Glow-accent, glassmorphic, and secondary CTA buttons.  │
│ Card.tsx               │ Design System        │ Glassmorphic container with cyan border highlights.    │
│ Badge.tsx              │ Design System        │ Pill badges with pulsating status indicators.          │
└────────────────────────┴──────────────────────┴────────────────────────────────────────────────────────┘
```

---

## 10.4 Page-by-Page Feature Matrix & Interaction Flows

### 1. `Home.tsx` (Mission Command & Walkthrough)
- **Hero Banner**: Engaging title typography with glowing cyan gradients.
- **3D Globe Display**: Seamlessly embedded alongside the hero section.
- **Three-Step Guided Workflow**:
  - *Step 1: Choose an Area* $\rightarrow$ Links to Map Explorer.
  - *Step 2: Let it Learn* $\rightarrow$ Links to Training Matrix.
  - *Step 3: See Your Results* $\rightarrow$ Links to Land Cover Results.
- **Interactive Carousel**: Step-by-step educational cards with previous/next navigation buttons.

### 2. `SuperResolution.tsx` (PSISR Progressive 8× Magnification)
- **Elsevier Publication Badge**: Displays official PII, DOI, and journal citations.
- **Scale Selector**: Toggle between $2\times$, $4\times$, and $8\times$ magnification.
- **Interactive Split Slider**: A smooth cursor-following comparison slider dividing low-resolution input and super-resolved UBCF output.
- **Live Quantitative Metrics Card**: Displays live PSNR (dB), SSIM, Pearson Correlation Efficiency (%), and FLOPs.
- **Mathematical Formulations Card**: Displays Equations 3, 7, 8, and 12 directly from Sharma et al. (2025).
- **AID 30-Scene Benchmark Catalog**: Responsive grid displaying all 30 scene categories loaded from the backend API. Clicking any card runs live progressive super-resolution on that scene!
- **SOTA Comparison Table**: Full benchmark matrix comparing Bicubic, SRCNN, VDSR, RDN, RCAN, Swin2-MoSE, MambaFormer, and PSISR.

### 3. `MapView.tsx` (Interactive Satellite Explorer)
- **Multi-Provider Tile Switching**:
  1. *Google Satellite*: Global high-resolution optical imagery.
  2. *ISRO Bhuvan*: National Remote Sensing Centre (NRSC India) WMS raster layer.
  3. *Esri World Imagery*: Maxar Earthstar optical composites.
  4. *OpenStreetMap (Carto)*: Global vector road and urban grid.
  5. *Sentinel-2 False-Color NDVI*: Synthetic photosynthetic canopy heatmap.
- **Quick Location Presets**: Instant fly-to navigation for Bhopal Upper Lake, Delhi NCR, Kerala Backwaters, Sundarbans Mangroves, Amazon Rainforest, Midwest Agricultural Belt, Los Angeles, and Tokyo Bay.
- **Bounding Box Drawing Tool**: Click and drag on the map to define a custom geographic coordinate box (`west, south, east, north`) for export.

### 4. `Inference.tsx` (Multispectral Prediction Engine)
- **GeoTIFF Drag-and-Drop**: Upload custom Sentinel-2 L2A tiles.
- **Model Checkpoint Selector**: Select between ResNet-CF (Super-Res), ResNet-34 MS (16-Channel), DeepGlobe RGB, or EuroSAT.
- **Configurable Sliding Window**: Adjust tile size ($512$), overlap ($32\text{ px}$), and spectral indices toggle.
- **Interactive Results Panel**: Renders classified output with land class percentage distribution chart.

### 5. `Training.tsx` (Deep Learning Training Monitor)
- **Phase Selector**: Configure hyperparameters for Phase 1 (EuroSAT), Phase 2 (DeepGlobe), Phase 3 (Multispectral), or Phase 4 (PSISR Super-Res).
- **Live Streamed SVG Convergence Curves**: Plots loss reduction and mIoU gains dynamically across epochs.
- **Per-Class IoU Breakdown**: Displays real-time IoU performance for all 11 land categories.

### 6. `Results.tsx` (Historical Prediction Catalog)
- **Demonstration Showcase**: Pre-loaded classified scenes for Bhopal Upper Lake, Los Angeles, Fresno, and Sacramento Delta.
- **Synchronized Dual-Map Inspection**: Compare optical satellite photo side-by-side with the colored segmentation mask.
- **GeoTIFF Download Manager**: One-click download of full-precision classified `.tif` rasters.

### 7. `CppDemo.tsx` (Native C++17 Terminal)
- **Interactive Execution Console**: Execute the compiled `geoseg_backend.exe` binary directly from the web browser.
- **Live Terminal Telemetry**: Displays the full execution log verifying all seven OOP concepts and SIMD throughput timings.

---
"""
