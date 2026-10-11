# -*- coding: utf-8 -*-
"""Section 4: Academic Literature Review & Theoretical Foundations."""

def get_section():
    return """# 4. ACADEMIC LITERATURE REVIEW & THEORETICAL FOUNDATIONS

The field of Single Image Super-Resolution (SISR) has undergone a decade of intense theoretical and algorithmic revolution, transitioning from classical interpolation to deep convolutional networks, attention mechanisms, vision transformers, state-space models, and correlation-filtered progressive architectures.

---

## 4.1 Evolution of Image Super-Resolution in Remote Sensing

Super-Resolution (SR) is an inherently **ill-posed inverse problem**. For any given low-resolution (LR) image $I_{LR}$, there exist infinitely many candidate high-resolution (HR) ground-truth images $I_{HR}$ that could have produced that observation through the forward degradation model:

$$I_{LR} = (I_{HR} * k) \\downarrow_s + \\, n$$

where:
- $*$ denotes spatial convolution.
- $k$ represents the optical system Point Spread Function (PSF) and atmospheric blur kernel.
- $\\downarrow_s$ denotes spatial downsampling by scale factor $s \\in \\{2, 4, 8\\}$.
- $n$ represents additive sensor noise (Poisson shot noise and Gaussian thermal read noise).

Below is the chronological evolution of SISR architectures from 2014 through 2025:

```
  2014: SRCNN (Dong et al.) ──────────> First 3-layer CNN (Patch Extraction -> Non-linear -> Recon)
          │
  2016: ESPCN (Shi et al.) ───────────> Sub-pixel convolution (PixelShuffle)
          │
  2016: VDSR (Kim et al.) ────────────> 20-layer deep network with global residual learning
          │
  2017: EDSR (Lim et al.) ────────────> Removed BatchNorm to preserve high-frequency dynamic range
          │
  2018: RDN (Zhang et al.) ───────────> Residual Dense Network: Contiguous feature reuse
          │
  2018: RCAN (Zhang et al.) ──────────> Residual Channel Attention: 400+ layers with CA blocks
          │
  2021: SwinIR (Liang et al.) ────────> Shifted Window Self-Attention Vision Transformer
          │
  2024: Swin2-MoSE ───────────────────> Mixture-of-Experts Sparse Transformer for Satellite Imagery
          │
  2024: MambaFormer ──────────────────> Selective State-Space Sequence Modeling for Long Horizons
          │
  2025: PSISR (Sharma et al.) ────────> PROPOSED: Cascading UBCF with Pearson Correlation Filtering
```

### Detailed Chronological Architectural Profiles

#### 1. Classical Bicubic Interpolation (Baseline)
- **Year**: Decades-old numerical analysis benchmark.
- **Mechanism**: Estimates unobserved sub-pixel coordinates by calculating a weighted average of the nearest $4 \\times 4$ ($16$) pixels using third-order polynomial cubic spline convolution kernels:
  $$W(x) = \\begin{cases} (a+2)|x|^3 - (a+3)|x|^2 + 1 & \\text{for } |x| \\le 1 \\\\ a|x|^3 - 5a|x|^2 + 8a|x| - 4a & \\text{for } 1 < |x| < 2 \\\\ 0 & \\text{otherwise} \\end{cases}$$
  *(typically $a = -0.5$)*
- **Fatal Flaw in Satellite Domain**: Smooths out all high-frequency boundary edges. Cannot recover lost spatial frequency information beyond the Nyquist limit; blurs mixed pixels irreversibly.

#### 2. SRCNN (Dong et al., ECCV 2014 / IEEE TPAMI 2015)
- **Architecture**: A compact 3-layer convolutional network:
  1. Patch extraction and representation: $\\text{Conv}(9 \\times 9, c=64) + \\text{ReLU}$
  2. Non-linear mapping: $\\text{Conv}(1 \\times 1, c=32) + \\text{ReLU}$
  3. High-resolution reconstruction: $\\text{Conv}(5 \\times 5, c=1)$
- **Limitation**: Operates in pre-upscaled bicubic space, causing massive computational overhead ($O(s^2)$ FLOPs). Receptive field is extremely small ($13 \\times 13$), failing to capture extended geospatial features.

#### 3. ESPCN (Shi et al., CVPR 2016)
- **Breakthrough**: Introduced **Sub-Pixel Convolution (PixelShuffle)**. Extracted features entirely in the low-resolution LR domain, performing spatial expansion only in the final layer by reshaping feature channel dimensions.
- **Impact on PSISR**: Adopted directly in PSISR's Stage 3 (UB3) to eliminate checkerboard artifacts!

#### 4. VDSR (Kim et al., CVPR 2016)
- **Architecture**: Deep 20-layer VGG-style network using small $3 \\times 3$ filters and **Global Residual Learning**:
  $$I_{SR} = I_{LR\\_bicubic} + \\mathcal{F}(I_{LR\\_bicubic})$$
- **Breakthrough**: Allowed deep training without gradient degradation by using high learning rates ($10^{-1}$) and adaptive gradient clipping ($[-0.4, 0.4]$).

#### 5. RCAN (Zhang et al., ECCV 2018)
- **Architecture**: Residual Channel Attention Networks. Over 400 convolutional layers organized into Residual Groups (RG) containing Residual Channel Attention Blocks (RCAB).
- **Mechanism**: Calculates global average pooling across spatial dimensions to derive a channel descriptor vector, followed by a two-layer multi-layer perceptron (MLP) with gating to weight channel importance:
  $$s = \\sigma(W_2 \\cdot \\delta(W_1 \\cdot z))$$
- **Limitation in Remote Sensing**: Very high parameter footprint ($15.6\\text{M}$ params) and heavy GPU memory demands. Focuses on natural photo contrast rather than ground-truth spectral correlation.

#### 6. Swin2-MoSE & MambaFormer (2024 SOTA Benchmarks)
- **Swin2-MoSE**: Combines Swin Transformer shifted-window cross-attention with Mixture-of-Experts routing for satellite feature extraction.
- **MambaFormer**: Replaces quadratic self-attention ($O(N^2)$) with linear state-space models ($O(N)$) using hardware-aware parallel scans.
- **Performance**: Achieved $35.34 \\text{ dB}$ (Swin2-MoSE) and $35.45 \\text{ dB}$ (MambaFormer) at 2× magnification on AID benchmarks.

---

## 4.2 Why Classical & Natural Image SR Models Fail on Earth Imagery

When state-of-the-art natural computer vision models are transferred directly to satellite remote sensing, they suffer severe degradation due to four fundamental domain discrepancies:

```
┌───────────────────────────────────────┬────────────────────────────────────────────────────────────────────────┐
│ Challenge in Satellite Remote Sensing │ Why Standard CV Super-Resolution Models Fail                           │
├───────────────────────────────────────┼────────────────────────────────────────────────────────────────────────┤
│ 1. Receptive Field Blind Spots        │ Standard 3×3 convolutions have localized receptive fields. Long linear │
│                                       │ features (highways, runways, rivers) lose structural continuity.       │
├───────────────────────────────────────┼────────────────────────────────────────────────────────────────────────┤
│ 2. Checkerboard Deconvolution Noise   │ Transposed convolutions insert non-uniform stride overlaps, creating   │
│                                       │ periodic high-frequency grid artifacts across smooth terrain.          │
├───────────────────────────────────────┼────────────────────────────────────────────────────────────────────────┤
│ 3. Category Information Loss          │ Natural models optimize for perceptual sharpness (L1 / L2 / VGG loss), │
│                                       │ which alters pixel reflectances, causing downstream classifiers to     │
│                                       │ misidentify crop species or confuse wetlands with open water.          │
├───────────────────────────────────────┼────────────────────────────────────────────────────────────────────────┤
│ 4. Mixed-Pixel (Mixel) Blurring       │ Satellite pixels average multiple distinct ground materials. Standard  │
│                                       │ models hallucinate sharp textures instead of resolving physical        │
│                                       │ constituent reflectance boundaries.                                    │
└───────────────────────────────────────┴────────────────────────────────────────────────────────────────────────┘
```

---

## 4.3 The Sharma et al. (2025) Breakthrough in Chemometrics

In January 2025, a landmark paper appeared in **Chemometrics and Intelligent Laboratory Systems** (Elsevier, Volume 256, Article 105277):

```
  ┌──────────────────────────────────────────────────────────────────────────────────────────────────────────┐
  │ TITLE:   Enhanced satellite image resolution with a residual network and correlation filter              │
  │ JOURNAL: Chemometrics and Intelligent Laboratory Systems, Volume 256 (2025) 105277                      │
  │ DOI:     10.1016/j.chemolab.2024.105277                                                                  │
  │ PII:     S0169-7439(24)00217-X                                                                           │
  │ AUTHORS: Ajay Sharma (VIT Bhopal University), Bhavana P. Shrivastava (MANIT Bhopal),                     │
  │          Praveen Kumar Tyagi, Ebtasam Ahmad Siddiqui, Rahul Prasad, Swati Gautam, Pranshu Pranjal        │
  └──────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### The Four Pillar Contributions of Sharma et al.:

1. **Cascading Three-Stage Architecture**:
   Instead of a single giant network or independent models for each scale factor, PSISRNet creates a progressive cascading pipeline where Stage 1 ($2\\times$) feeds into Stage 2 ($4\\times$), which feeds into Stage 3 ($8\\times$). Features learned at lower magnification directly inform and constrain higher magnification stages!

2. **The UBCF (Upscaling Block with Correlation Filter) Module**:
   Combines multi-rate dilated convolutions ($r = 1, 2, 4$) with a specialized **Correlation Filter (CF)**. The correlation filter evaluates the spatial correlation between reconstructed and ground-truth features, preventing the formation of blind spots while preserving spectral identity.

3. **Loss-Aware Adaptive Combined Loss ($L_{CL}$)**:
   A dynamic objective function that continuously computes the ratio between Mean Squared Error ($L_{MSE}$) and Structural Similarity ($L_{SSIM}$):
   $$L_{CL} = w_i \\cdot L_{MSE} + u_i \\cdot L_{SSIM}$$
   The weights $w_i$ and $u_i$ adapt automatically at every training step, ensuring the model never over-optimizes for blurry pixel averages at the expense of structural edges.

4. **Rigorous Empirical Verification on Satellite Benchmarks**:
   Evaluated extensively across three major remote sensing benchmarks:
   - **AID (Aerial Image Dataset)**: 10,000 images across 30 diverse scene categories.
   - **WHU-RS19**: High-resolution 19-class remote sensing benchmark.
   - **Test30**: Standardized evaluation benchmark for remote sensing super-resolution.

The published results demonstrated that PSISR achieves a **+0.40 dB PSNR gain** over Swin2-MoSE and MambaFormer, while maintaining an unprecedented **99.25% ground-truth spectral correlation efficiency**!

---
"""
