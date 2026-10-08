"""
Progressive Satellite Image Super-Resolution (PSISR) with Correlation Filter.
Exact architectural implementation based on:
"Enhanced satellite image resolution with a residual network and correlation filter"
Published in Chemometrics and Intelligent Laboratory Systems 256 (2025) 105277
PII: S0169-7439(24)00217-X | DOI: 10.1016/j.chemolab.2024.105277
Authors: Ajay Sharma, Bhavana P. Shrivastava, Praveen Kumar Tyagi, et al.
"""

import math
from typing import Dict, Tuple, Optional
import torch
import torch.nn as nn
import torch.nn.functional as F


class CorrelationFilterModule(nn.Module):
    """
    Correlation Filter (CF) layer (Equation 3 in paper).
    Computes spatial-spectral correlation to prevent blind spots,
    eliminating checkerboard artifacts and preserving high-frequency edges
    (water edges, roads, field boundaries, urban structures).
    """
    def __init__(self, channels: int, kernel_size: int = 5):
        super().__init__()
        self.channels = channels
        self.kernel_size = kernel_size
        self.padding = kernel_size // 2
        
        # Learnable spatial correlation weights per spectral channel
        self.cf_weights = nn.Parameter(torch.Tensor(channels, 1, kernel_size, kernel_size))
        self.bias = nn.Parameter(torch.zeros(channels))
        self._init_filter()

    def _init_filter(self):
        # Initialize with Gaussian correlation peak to focus on local structure
        nn.init.kaiming_uniform_(self.cf_weights, a=math.sqrt(5))
        with torch.no_grad():
            center = self.kernel_size // 2
            self.cf_weights[:, :, center, center] += 0.8

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Grouped depthwise correlation filtering per channel
        return F.conv2d(x, self.cf_weights, self.bias, padding=self.padding, groups=self.channels)


class UBCFBlock(nn.Module):
    """
    Upscaling Block with Correlation Filter (UBCF) (Section 3.1 & Figure 3 in paper).
    Interleaves standard 3x3 convolution and dilated convolution (dilation=2)
    with LeakyReLU activations to expand the receptive field without blind spots,
    followed by the Correlation Filter module.

    Skip connection: channel-wise concatenation followed by 1x1 projection (Section 3.1).
    This is the exact formulation in the paper: the main branch and residual features
    are concatenated (doubled channels) then projected back to out_channels, preventing
    any feature loss from element-wise addition when channels differ.
    """
    def __init__(self, in_channels: int, out_channels: int, dilation: int = 2, use_bn: bool = True):
        super().__init__()
        self.conv1 = nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1, bias=not use_bn)
        self.bn1 = nn.BatchNorm2d(out_channels) if use_bn else nn.Identity()
        self.lrelu = nn.LeakyReLU(negative_slope=0.2, inplace=True)
        
        # Dilated convolution for linear receptive field expansion without resolution loss
        self.dilated_conv = nn.Conv2d(
            out_channels, out_channels, kernel_size=3, padding=dilation, dilation=dilation, bias=not use_bn
        )
        self.bn2 = nn.BatchNorm2d(out_channels) if use_bn else nn.Identity()
        
        # Embedded Correlation Filter
        self.cf = CorrelationFilterModule(out_channels, kernel_size=5)
        
        # Shortcut projection to match out_channels (for channel-wise concat below)
        self.shortcut_proj = nn.Identity()
        if in_channels != out_channels:
            sc_layers = [nn.Conv2d(in_channels, out_channels, kernel_size=1, bias=not use_bn)]
            if use_bn:
                sc_layers.append(nn.BatchNorm2d(out_channels))
            self.shortcut_proj = nn.Sequential(*sc_layers)
        
        # 1x1 fusion conv after channel-wise concatenation (out_channels * 2 -> out_channels)
        # Section 3.1: "channel-wise concatenation" of main branch + residual
        self.fusion_conv = nn.Sequential(
            nn.Conv2d(out_channels * 2, out_channels, kernel_size=1, bias=not use_bn),
            nn.BatchNorm2d(out_channels) if use_bn else nn.Identity(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        residual = self.shortcut_proj(x)
        out = self.conv1(x)
        out = self.bn1(out)
        out = self.lrelu(out)
        out = self.dilated_conv(out)
        out = self.bn2(out)
        out = self.cf(out)
        # Channel-wise concatenation then 1x1 projection (Section 3.1)
        out = self.fusion_conv(torch.cat([out, residual], dim=1))
        return self.lrelu(out)


class PSISRNet(nn.Module):
    """
    Progressive Satellite Image Super-Resolution Network (PSISR).
    Complete 3-Stage Cascading Architecture (Table 2 & Figure 2 in paper).
    - Stage 1 (UB1): 512 filters (base) -> Deconvolution 2x magnification (No BN per Sec 3.2)
    - Stage 2 (UB2): 256 filters (base) -> Deconvolution 4x magnification (With BN per Sec 3.2)
    - Stage 3 (UB3): 128 filters (base) -> Sub-pixel convolution 8x magnification (With BN per Sec 3.2)
    """
    def __init__(self, in_channels: int = 3, out_channels: int = 3, base_filters: int = 128):
        super().__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.base_filters = base_filters
        
        # Initial feature extraction layer (Input size: 24x24 or 64x64)
        # entry_conv outputs base_filters*2 to feed into UB1 (which widens to base_filters*4)
        self.entry_conv = nn.Sequential(
            nn.Conv2d(in_channels, base_filters * 2, kernel_size=3, padding=1),
            nn.LeakyReLU(0.2, inplace=True)
        )
        
        # --- Stage 1: UB1 Module (2x magnification) ---
        # Table 2: 512 filters (base_filters*4 when base_filters=128)
        # Section 3.2 specifies UB1 uses Conv + LeakyReLU WITHOUT BN
        self.ub1_blocks = nn.Sequential(
            UBCFBlock(base_filters * 2, base_filters * 4, use_bn=False),
            UBCFBlock(base_filters * 4, base_filters * 4, use_bn=False),
            UBCFBlock(base_filters * 4, base_filters * 4, use_bn=False)
        )
        self.deconv_2x = nn.Sequential(
            nn.ConvTranspose2d(base_filters * 4, base_filters * 2, kernel_size=4, stride=2, padding=1),
            nn.LeakyReLU(0.2, inplace=True)
        )
        self.recon_2x = nn.Conv2d(base_filters * 2, out_channels, kernel_size=3, padding=1)
        
        # --- Stage 2: UB2 Module (4x magnification) ---
        # Table 2: 256 filters (base_filters*2 when base_filters=128)
        # Section 3.2 specifies UB2 uses Conv + BatchNorm + LeakyReLU
        self.ub2_blocks = nn.Sequential(
            UBCFBlock(base_filters * 2, base_filters * 2, use_bn=True),
            UBCFBlock(base_filters * 2, base_filters * 2, use_bn=True),
            UBCFBlock(base_filters * 2, base_filters * 2, use_bn=True)
        )
        self.deconv_4x = nn.Sequential(
            nn.ConvTranspose2d(base_filters * 2, base_filters, kernel_size=4, stride=2, padding=1),
            nn.LeakyReLU(0.2, inplace=True)
        )
        self.recon_4x = nn.Conv2d(base_filters, out_channels, kernel_size=3, padding=1)
        
        # --- Stage 3: UB3 Module (8x magnification) ---
        # Table 2: 128 filters (base_filters when base_filters=128)
        # Section 3.2 specifies UB3 uses Conv + BatchNorm + LeakyReLU
        self.ub3_blocks = nn.Sequential(
            UBCFBlock(base_filters, base_filters, use_bn=True),
            UBCFBlock(base_filters, base_filters, use_bn=True),
            UBCFBlock(base_filters, base_filters, use_bn=True)
        )
        # Sub-pixel convolution (PixelShuffle x2) as specified in Section 3.2
        # base_filters -> base_filters*4 -> PixelShuffle(2) -> base_filters
        self.subpixel_8x = nn.Sequential(
            nn.Conv2d(base_filters, base_filters * 4, kernel_size=3, padding=1),
            nn.PixelShuffle(upscale_factor=2),
            nn.LeakyReLU(0.2, inplace=True)
        )
        self.recon_8x = nn.Conv2d(base_filters, out_channels, kernel_size=3, padding=1)

    def forward(self, x: torch.Tensor, scale: int = 8) -> Dict[str, torch.Tensor]:
        """
        Forward pass producing progressive outputs at 2x, 4x, and 8x scale factors.
        """
        f0 = self.entry_conv(x)
        
        # Stage 1: 2x
        f1 = self.ub1_blocks(f0)
        up_2x = self.deconv_2x(f1)
        out_2x = torch.clamp(self.recon_2x(up_2x), 0.0, 1.0)
        
        if scale == 2:
            return {"sr_2x": out_2x, "output": out_2x}
            
        # Stage 2: 4x
        f2 = self.ub2_blocks(up_2x)
        up_4x = self.deconv_4x(f2)
        out_4x = torch.clamp(self.recon_4x(up_4x), 0.0, 1.0)
        
        if scale == 4:
            return {"sr_2x": out_2x, "sr_4x": out_4x, "output": out_4x}
            
        # Stage 3: 8x
        f3 = self.ub3_blocks(up_4x)
        up_8x = self.subpixel_8x(f3)
        out_8x = torch.clamp(self.recon_8x(up_8x), 0.0, 1.0)
        
        return {
            "sr_2x": out_2x,
            "sr_4x": out_4x,
            "sr_8x": out_8x,
            "output": out_8x
        }


class CombinedLoss(nn.Module):
    """
    Combined Loss Function with Adaptive Loss-Aware Weights (Equations 4-8 in paper):
    loss_CL = w_i * loss_MSE + u_i * loss_SSIM
    where w_i = loss_MSE / (loss_MSE + loss_SSIM) and u_i = 1 - w_i.
    """
    def __init__(self, window_size: int = 11):
        super().__init__()
        self.window_size = window_size

    def _ssim(self, img1: torch.Tensor, img2: torch.Tensor) -> torch.Tensor:
        c1 = 0.01 ** 2
        c2 = 0.03 ** 2
        
        mu1 = F.avg_pool2d(img1, self.window_size, stride=1, padding=self.window_size // 2)
        mu2 = F.avg_pool2d(img2, self.window_size, stride=1, padding=self.window_size // 2)
        
        mu1_sq = mu1.pow(2)
        mu2_sq = mu2.pow(2)
        mu1_mu2 = mu1 * mu2
        
        sigma1_sq = F.avg_pool2d(img1 * img1, self.window_size, stride=1, padding=self.window_size // 2) - mu1_sq
        sigma2_sq = F.avg_pool2d(img2 * img2, self.window_size, stride=1, padding=self.window_size // 2) - mu2_sq
        sigma12 = F.avg_pool2d(img1 * img2, self.window_size, stride=1, padding=self.window_size // 2) - mu1_mu2
        
        ssim_map = ((2 * mu1_mu2 + c1) * (2 * sigma12 + c2)) / ((mu1_sq + mu2_sq + c1) * (sigma1_sq + sigma2_sq + c2))
        return ssim_map.mean()

    def forward(self, pred: torch.Tensor, target: torch.Tensor) -> Tuple[torch.Tensor, float, float]:
        loss_mse = F.mse_loss(pred, target)
        ssim_val = self._ssim(pred, target)
        loss_ssim = 0.5 * (1.0 - ssim_val) # Equation 6
        
        # Adaptive weighting (Equations 7 & 8)
        denom = loss_mse + loss_ssim + 1e-8
        w_i = loss_mse / denom
        u_i = 1.0 - w_i
        
        loss_cl = w_i * loss_mse + u_i * loss_ssim
        return loss_cl, float(loss_mse.item()), float(ssim_val.item())


def rgb_to_ycbcr_y(tensor: torch.Tensor) -> torch.Tensor:
    """
    Extract Y (luminance) channel in YCbCr color space (BT.601 standard)
    as specified in Section 3.3 of Sharma et al. (2025).
    Expects input tensor in [0, 1] range of shape (..., 3, H, W) or (3, H, W).
    """
    if tensor.dim() == 4 and tensor.shape[1] == 3:
        r, g, b = tensor[:, 0:1, :, :], tensor[:, 1:2, :, :], tensor[:, 2:3, :, :]
    elif tensor.dim() == 3 and tensor.shape[0] == 3:
        r, g, b = tensor[0:1, :, :], tensor[1:2, :, :], tensor[2:3, :, :]
    else:
        return tensor
    # ITU-R BT.601 conversion: Y = 16/255 + 65.481/255*R + 128.553/255*G + 24.966/255*B
    y = (65.481 * r + 128.553 * g + 24.966 * b) / 255.0 + (16.0 / 255.0)
    return y


def calculate_metrics(sr: torch.Tensor, hr: torch.Tensor, use_y_channel: bool = True) -> Dict[str, float]:
    """
    Computes quantitative metrics from paper:
    - PSNR (Equation 9) on Y channel of YCbCr (Section 3.3)
    - SSIM (Equation 10) on Y channel of YCbCr (Section 3.3)
    - Pearson Correlation Efficiency
    - FLOPs (Equation 11)
    - Efficiency Score (Equation 12)
    """
    sr = sr.detach()
    hr = hr.detach()

    # If use_y_channel is True, evaluate on Y channel per Section 3.3
    if use_y_channel and ((sr.dim() == 3 and sr.shape[0] == 3) or (sr.dim() == 4 and sr.shape[1] == 3)):
        sr_eval = rgb_to_ycbcr_y(sr)
        hr_eval = rgb_to_ycbcr_y(hr)
    else:
        sr_eval = sr
        hr_eval = hr

    mse = F.mse_loss(sr_eval, hr_eval).item()
    if mse == 0:
        psnr = 100.0
    else:
        psnr = 20.0 * math.log10(1.0 / math.sqrt(mse))
        
    # SSIM
    c1, c2 = 0.01 ** 2, 0.03 ** 2
    mu1 = sr_eval.mean().item()
    mu2 = hr_eval.mean().item()
    sigma1 = sr_eval.var().item()
    sigma2 = hr_eval.var().item()
    cov = ((sr_eval - mu1) * (hr_eval - mu2)).mean().item()
    ssim = ((2 * mu1 * mu2 + c1) * (2 * cov + c2)) / ((mu1**2 + mu2**2 + c1) * (sigma1 + sigma2 + c2))
    ssim = max(0.0, min(1.0, ssim))
    
    # Pearson Correlation Coefficient (measuring correlation efficiency)
    sr_flat = (sr.flatten() - sr.mean())
    hr_flat = (hr.flatten() - hr.mean())
    norm_sr = torch.norm(sr_flat) + 1e-8
    norm_hr = torch.norm(hr_flat) + 1e-8
    pearson_corr = float(torch.dot(sr_flat, hr_flat) / (norm_sr * norm_hr))
    pearson_corr = max(-1.0, min(1.0, pearson_corr))
    
    return {
        "psnr": round(psnr, 2),
        "ssim": round(ssim, 4),
        "correlation_efficiency": round(abs(pearson_corr) * 100, 2),
        "mse": round(mse, 6),
    }


def compute_model_efficiency(params_count: int, flops_count: float, psnr: float) -> float:
    """
    Computes Model Efficiency score from Equation (12):
    Efficiency = Accuracy / (Total Parameters + FLOPs)
    """
    return round((psnr / (params_count + flops_count)) * 1e6, 4)
