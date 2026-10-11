"""
Wavelet & High-Frequency Spatial Transforms for Satellite Image Super-Resolution.
Implements:
- 2D Haar Discrete Wavelet Transform (DWT) decomposition (LL, LH, HL, HH sub-bands).
- Inverse 2D Haar DWT (IDWT) reconstruction.
- Sobel Edge Gradient Filter.
- Wavelet Frequency Loss and Edge-Preservation Loss.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


def dwt_haar_2d(x: torch.Tensor) -> torch.Tensor:
    """
    2D Discrete Haar Wavelet Transform (Orthonormal).
    
    Args:
        x: Input tensor of shape (B, C, H, W). H and W must be even.
        
    Returns:
        Tensor of shape (B, 4*C, H/2, W/2) with sub-bands [LL, LH, HL, HH].
    """
    x00 = x[:, :, 0::2, 0::2]
    x01 = x[:, :, 0::2, 1::2]
    x10 = x[:, :, 1::2, 0::2]
    x11 = x[:, :, 1::2, 1::2]
    
    ll = (x00 + x01 + x10 + x11) / 2.0
    lh = (x00 + x01 - x10 - x11) / 2.0
    hl = (x00 - x01 + x10 - x11) / 2.0
    hh = (x00 - x01 - x10 + x11) / 2.0
    
    return torch.cat([ll, lh, hl, hh], dim=1)


def idwt_haar_2d(x: torch.Tensor) -> torch.Tensor:
    """
    Inverse 2D Discrete Haar Wavelet Transform.
    
    Args:
        x: Input tensor of shape (B, 4*C, H/2, W/2).
        
    Returns:
        Reconstructed tensor of shape (B, C, H, W).
    """
    c = x.size(1) // 4
    ll = x[:, 0*c:1*c, :, :]
    lh = x[:, 1*c:2*c, :, :]
    hl = x[:, 2*c:3*c, :, :]
    hh = x[:, 3*c:4*c, :, :]
    
    b, _, h, w = ll.shape
    device = x.device
    dtype = x.dtype
    
    rec = torch.zeros(b, c, h * 2, w * 2, device=device, dtype=dtype)
    rec[:, :, 0::2, 0::2] = (ll + lh + hl + hh) / 2.0
    rec[:, :, 0::2, 1::2] = (ll + lh - hl - hh) / 2.0
    rec[:, :, 1::2, 0::2] = (ll - lh + hl - hh) / 2.0
    rec[:, :, 1::2, 1::2] = (ll - lh - hl + hh) / 2.0
    return rec


class SobelFilter(nn.Module):
    """Sobel Gradient Operator for calculating horizontal and vertical spatial derivatives."""
    def __init__(self, in_channels: int = 3):
        super().__init__()
        self.in_channels = in_channels
        
        kernel_x = torch.tensor([[-1.0, 0.0, 1.0], [-2.0, 0.0, 2.0], [-1.0, 0.0, 1.0]]) / 4.0
        kernel_y = torch.tensor([[-1.0, -2.0, -1.0], [0.0, 0.0, 0.0], [1.0, 2.0, 1.0]]) / 4.0
        
        kernel_x = kernel_x.view(1, 1, 3, 3).repeat(in_channels, 1, 1, 1)
        kernel_y = kernel_y.view(1, 1, 3, 3).repeat(in_channels, 1, 1, 1)
        
        self.register_buffer("kernel_x", kernel_x)
        self.register_buffer("kernel_y", kernel_y)
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        kx = self.kernel_x.to(device=x.device, dtype=x.dtype)
        ky = self.kernel_y.to(device=x.device, dtype=x.dtype)
        gx = F.conv2d(x, kx, padding=1, groups=self.in_channels)
        gy = F.conv2d(x, ky, padding=1, groups=self.in_channels)
        return torch.sqrt(gx ** 2 + gy ** 2 + 1e-6)


class WaveletEdgeLoss(nn.Module):
    """
    Combined Wavelet Frequency & Edge Gradient Loss for Satellite Super-Resolution.
    Penalizes deviations in high-frequency directional sub-bands (LH, HL, HH) and Sobel edges.
    """
    def __init__(self, in_channels: int = 3, lambda_wavelet: float = 0.1, lambda_edge: float = 0.05):
        super().__init__()
        self.lambda_wavelet = lambda_wavelet
        self.lambda_edge = lambda_edge
        self.sobel = SobelFilter(in_channels=in_channels)
        self.l1 = nn.L1Loss()
        
    def forward(self, pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        # High-frequency wavelet sub-bands
        pred_dwt = dwt_haar_2d(pred)
        target_dwt = dwt_haar_2d(target)
        c = pred.size(1)
        # Sub-bands 1*c to 4*c correspond to LH, HL, HH
        loss_wavelet = self.l1(pred_dwt[:, c:], target_dwt[:, c:])
        
        # Sobel spatial edge gradients
        pred_edge = self.sobel(pred)
        target_edge = self.sobel(target)
        loss_edge = self.l1(pred_edge, target_edge)
        
        return self.lambda_wavelet * loss_wavelet + self.lambda_edge * loss_edge
