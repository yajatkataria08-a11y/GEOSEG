# -*- coding: utf-8 -*-
"""Section 6: Multispectral Semantic Land Cover Segmentation (GeoSeg U-Net)."""

def get_section():
    return """# 6. MULTISPECTRAL SEMANTIC LAND COVER SEGMENTATION (GEOSEG U-NET)

While super-resolution sharpens optical imagery, semantic segmentation assigns categorical meaning to every spatial coordinate on planet Earth. This section details the **GeoSeg Multispectral U-Net**, engineered specifically to ingest high-dimensional multi-band satellite rasters.

---

## 6.1 16-Channel Adapted ResNet-34 Encoder Architecture

Standard computer vision backbones (e.g., standard ResNet, EfficientNet, ViT) assume 3-channel RGB image tensors. If one simply discards the remaining 10 Sentinel-2 bands, **76.9% of the satellite's diagnostic spectral data is permanently lost**!

GeoSeg adapts the **ResNet-34** convolutional backbone by replacing its initial convolutional stem:

```
  Standard Computer Vision Stem:
  Input (3 Channels: R, G, B) ───> Conv2d(3, 64, kernel=7, stride=2, padding=3)

  GeoSeg Multispectral Adapted Stem:
  Input (16 Channels: 13 Bands + 3 Indices) ───> Conv2d(16, 64, kernel=7, stride=2, padding=3)
```

### The 16-Channel Tensor Composition

Every input patch fed into GeoSeg U-Net is structured as a 4D tensor $X \in \mathbb{R}^{B \times 16 \times H \times W}$:

```
  Index │ Band / Feature Name  │ Physical Diagnostic Purpose
  ──────┼──────────────────────┼─────────────────────────────────────────────
    0   │ B01: Coastal Aerosol │ Atmospheric scattering reference & turbidity
    1   │ B02: Blue            │ Water body absorption & visual blue
    2   │ B03: Green           │ Vegetation peak reflectance & visual green
    3   │ B04: Red             │ Chlorophyll-a absorption & visual red
    4   │ B05: Red Edge 1      │ Plant cell boundary steep inflection
    5   │ B06: Red Edge 2      │ Canopy nitrogen concentration
    6   │ B07: Red Edge 3      │ Leaf Area Index (LAI) saturation
    7   │ B08: NIR Broad       │ High-resolution canopy biomass reflection
    8   │ B8A: NIR Narrow      │ Atmospheric water-vapor-free infrared
    9   │ B09: Water Vapour    │ Atmospheric column humidity quantification
   10   │ B10: SWIR - Cirrus   │ Sub-visual high-altitude cloud masking
   11   │ B11: SWIR 1          │ Soil moisture, vegetation water content
   12   │ B12: SWIR 2          │ Mineralogy, burn severity, urban reflectance
   13   │ NDVI Feature         │ Normalized Difference Vegetation Index
   14   │ NDWI Feature         │ Normalized Difference Water Index
   15   │ NDBI Feature         │ Normalized Difference Built-Up Index
```

### Weight Adaptation Strategy for Transfer Learning
To leverage ImageNet pretraining weights without destroying pretrained feature detectors:
1. Channels 1, 2, and 3 (B04, B03, B02) are initialized directly from the pretrained Red, Green, and Blue kernel weights.
2. The remaining 13 channels are initialized by copying the channel-averaged RGB weight tensor scaled by a normalization factor $\frac{3}{16}$:
   $$W_{\text{new}}[:, c, :, :] = \frac{1}{3} \sum_{k=0}^2 W_{\text{pretrained}}[:, k, :, :] \cdot \frac{3}{16} \quad (c \ge 3)$$
This guarantees that initial activations do not explode during the first training epoch!

---

## 6.2 Decoder Feature Aggregation & Skip Connections

The GeoSeg U-Net architecture utilizes a symmetric encoder-decoder topology with progressive spatial upsampling and multi-scale skip connections:

```
  Input Tensor: ℝ^{B × 16 × 512 × 512}
       │
       ▼
  [Stem: Conv7x7] ──> ℝ^{B × 64 × 256 × 256} ────── Skip 1 ──────┐
       │                                                         │
       ▼                                                         │
  [ResNet Layer 1] ─> ℝ^{B × 64 × 256 × 256}                     │
       │                                                         │
       ▼                                                         │
  [ResNet Layer 2] ─> ℝ^{B × 128 × 128 × 128} ──── Skip 2 ────┐  │
       │                                                      │  │
       ▼                                                      │  │
  [ResNet Layer 3] ─> ℝ^{B × 256 × 64 × 64} ───── Skip 3 ──┐ │  │
       │                                                   │ │  │
       ▼                                                   │ │  │
  [ResNet Layer 4] ─> ℝ^{B × 512 × 32 × 32} ─── Skip 4 ─┐  │ │  │
       │                                                │  │ │  │
       ▼                                                │  │ │  │
  [Bottleneck: ASPP / Dilated Bridge]                   │  │ │  │
  Output: ℝ^{B × 512 × 32 × 32}                          │  │ │  │
       │                                                │  │ │  │
       ▼                                                │  │ │  │
  [Decoder Block 4: UpConv + Concat] <──────────────────┘  │ │  │
  Output: ℝ^{B × 256 × 64 × 64}                            │ │  │
       │                                                   │ │  │
       ▼                                                   │ │  │
  [Decoder Block 3: UpConv + Concat] <─────────────────────┘ │  │
  Output: ℝ^{B × 128 × 128 × 128}                            │  │
       │                                                     │  │
       ▼                                                     │  │
  [Decoder Block 2: UpConv + Concat] <───────────────────────┘  │
  Output: ℝ^{B × 64 × 256 × 256}                                │
       │                                                        │
       ▼                                                        │
  [Decoder Block 1: UpConv + Concat] <──────────────────────────┘
  Output: ℝ^{B × 64 × 512 × 512}
       │
       ▼
  [Final Head: Conv1x1] ──> Logits: ℝ^{B × 11 × 512 × 512}
```

Every decoder block executes:
1. **Bilinear Upsampling (2×)**: Increases spatial resolution while halving channel depth.
2. **Channel Concatenation with Skip Connection**: Fuses high-level semantic context with low-level spatial boundary localization.
3. **Double 3×3 Convolutional Refinement**: Two consecutive `Conv2d(3x3) -> BatchNorm -> LeakyReLU` passes to eliminate aliasing.

---

## 6.3 Compound Objective Function: Weighted Dice + Cross-Entropy

In remote sensing semantic segmentation, class distributions are notoriously imbalanced. In typical rural scenes, forest and agricultural land might occupy 90% of the pixels, while critical features like roads, rivers, or residential clusters occupy less than 2%. 

A naive network trained solely on Cross-Entropy loss achieves 90% accuracy simply by classifying *every single pixel as forest*, completely failing on infrastructure!

GeoSeg solves this with a **Compound Loss Function**:

$$\mathcal{L}_{\text{total}} = \alpha \cdot \mathcal{L}_{\text{CE}} + \beta \cdot \mathcal{L}_{\text{Dice}} \quad (\alpha = 0.5, \, \beta = 0.5)$$

### 1. Weighted Categorical Cross-Entropy Loss ($\mathcal{L}_{\text{CE}}$)

$$\mathcal{L}_{\text{CE}} = - \frac{1}{N} \sum_{i=1}^N \sum_{c=1}^C w_c \cdot y_{i, c} \cdot \log(\hat{p}_{i, c})$$

where:
- $y_{i, c} \in \{0, 1\}$ is the one-hot ground-truth label for pixel $i$ and class $c$.
- $\hat{p}_{i, c} = \frac{\exp(z_{i, c})}{\sum_{k=1}^C \exp(z_{i, k})}$ is the predicted softmax probability.
- $w_c$ is the inverse-frequency class weight vector:
  $$w_c = \frac{1}{\ln\left( 1.02 + \frac{N_c}{N} \right)}$$
  Rare classes (e.g., wetlands, urban structures) receive high weights, forcing the network to attend to them.

### 2. Multi-Class Soft Dice Loss ($\mathcal{L}_{\text{Dice}}$)

$$\mathcal{L}_{\text{Dice}} = 1 - \frac{1}{C} \sum_{c=1}^C \frac{2 \sum_{i=1}^N \hat{p}_{i, c} \cdot y_{i, c} + \epsilon}{\sum_{i=1}^N \hat{p}_{i, c}^2 + \sum_{i=1}^N y_{i, c}^2 + \epsilon}$$

where $\epsilon = 10^{-6}$ is a Laplace smoothing factor preventing division by zero.

**Why Dice Loss is Critical**:
Dice Loss directly optimizes the overlap ratio (F1 score) between the predicted binary mask and the ground truth. It is mathematically independent of the total number of background pixels, making it immune to extreme class imbalance!

---

## 6.4 Metric Formulations: IoU, mIoU, Dice, Accuracy & Cohen's Kappa

GeoSeg audits every validation epoch using five rigorous geospatial metrics derived from the multi-class confusion matrix:

Let $TP_c, FP_c, FN_c, TN_c$ denote the True Positives, False Positives, False Negatives, and True Negatives for class $c \in \{1, \dots, C\}$ across $N$ total evaluated pixels.

### 1. Class Intersection over Union (IoU / Jaccard Index)
$$\text{IoU}_c = \frac{|\hat{Y}_c \cap Y_c|}{|\hat{Y}_c \cup Y_c|} = \frac{TP_c}{TP_c + FP_c + FN_c}$$

### 2. Mean Intersection over Union (mIoU)
The gold-standard benchmark in semantic segmentation:
$$\text{mIoU} = \frac{1}{C} \sum_{c=1}^C \text{IoU}_c = \frac{1}{C} \sum_{c=1}^C \frac{TP_c}{TP_c + FP_c + FN_c}$$

### 3. F1-Score / Sorensen-Dice Coefficient
$$\text{Dice}_c = \frac{2 \cdot TP_c}{2 \cdot TP_c + FP_c + FN_c}$$

### 4. Overall Pixel Accuracy (OA)
$$\text{OA} = \frac{\sum_{c=1}^C TP_c}{N}$$

### 5. Cohen's Kappa Coefficient ($\kappa$)
Measures agreement between classification output and ground truth, strictly corrected for agreement occurring purely by chance:
$$\kappa = \frac{p_o - p_e}{1 - p_e}$$
where $p_o = \text{OA}$ is the observed accuracy, and $p_e$ is the expected chance agreement:
$$p_e = \sum_{c=1}^C \left( \frac{TP_c + FP_c}{N} \cdot \frac{TP_c + FN_c}{N} \right)$$
A $\kappa > 0.80$ denotes near-perfect agreement in remote sensing classification literature.

---
"""
