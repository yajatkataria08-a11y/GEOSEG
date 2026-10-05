"""Tests for spectral index computation (NDVI, NDWI, NDBI)."""
import pytest
import numpy as np
import torch
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.transforms.band_math import compute_indices, build_multispectral_input_torch, DEFAULT_BAND_ORDER


# compute_indices returns ndarray of shape (3, H, W): [0]=NDVI, [1]=NDWI, [2]=NDBI


class TestNDVI:
    """Test NDVI computation against known physical values."""

    def test_dense_vegetation(self):
        """Dense forest: NIR~0.50, Red~0.03 => NDVI ~ +0.89"""
        bands = np.zeros((13, 4, 4), dtype=np.float32)
        bands[3, :, :] = 0.03   # B04 (Red)
        bands[7, :, :] = 0.50   # B08 (NIR)
        result = compute_indices(bands, DEFAULT_BAND_ORDER)
        ndvi = result[0]
        assert ndvi.shape == (4, 4)
        assert np.all(ndvi > 0.85) and np.all(ndvi < 0.95)

    def test_open_water(self):
        """Water: NIR~0.01, Red~0.05 => NDVI ~ -0.67"""
        bands = np.zeros((13, 4, 4), dtype=np.float32)
        bands[3, :, :] = 0.05
        bands[7, :, :] = 0.01
        result = compute_indices(bands, DEFAULT_BAND_ORDER)
        ndvi = result[0]
        assert np.all(ndvi < -0.5)

    def test_bare_soil(self):
        """Bare soil: NIR~0.25, Red~0.20 => NDVI ~ +0.11"""
        bands = np.zeros((13, 4, 4), dtype=np.float32)
        bands[3, :, :] = 0.20
        bands[7, :, :] = 0.25
        result = compute_indices(bands, DEFAULT_BAND_ORDER)
        ndvi = result[0]
        assert np.all(ndvi > 0.05) and np.all(ndvi < 0.20)

    def test_ndvi_range(self):
        """NDVI must always be in [-1, +1]."""
        bands = np.random.rand(13, 32, 32).astype(np.float32)
        result = compute_indices(bands, DEFAULT_BAND_ORDER)
        assert np.all(result[0] >= -1.0) and np.all(result[0] <= 1.0)


class TestNDWI:
    """Test NDWI computation."""

    def test_water_positive(self):
        """Water bodies should have positive NDWI."""
        bands = np.zeros((13, 4, 4), dtype=np.float32)
        bands[2, :, :] = 0.12   # B03 (Green)
        bands[7, :, :] = 0.01   # B08 (NIR)
        result = compute_indices(bands, DEFAULT_BAND_ORDER)
        assert np.all(result[1] > 0.5)

    def test_vegetation_negative(self):
        """Dense vegetation should have negative NDWI."""
        bands = np.zeros((13, 4, 4), dtype=np.float32)
        bands[2, :, :] = 0.06
        bands[7, :, :] = 0.45
        result = compute_indices(bands, DEFAULT_BAND_ORDER)
        assert np.all(result[1] < -0.5)


class TestNDBI:
    """Test NDBI computation."""

    def test_urban_positive(self):
        """Urban areas (high SWIR1, low NIR) should have positive NDBI."""
        bands = np.zeros((13, 4, 4), dtype=np.float32)
        bands[7, :, :] = 0.22   # B08 (NIR)
        bands[11, :, :] = 0.35  # B11 (SWIR1)
        result = compute_indices(bands, DEFAULT_BAND_ORDER)
        assert np.all(result[2] > 0.1)


class TestEpsilonSafety:
    """Test numerical stability with zero-value inputs."""

    def test_zero_denominator(self):
        """All-zero bands should NOT produce NaN."""
        bands = np.zeros((13, 4, 4), dtype=np.float32)
        result = compute_indices(bands, DEFAULT_BAND_ORDER)
        assert not np.any(np.isnan(result[0]))  # NDVI
        assert not np.any(np.isnan(result[1]))  # NDWI
        assert not np.any(np.isnan(result[2]))  # NDBI


class TestMultispectralTorch:
    """Test PyTorch GPU-compatible multispectral tensor builder."""

    def test_output_shape(self):
        """13ch input -> 16ch output (appends NDVI, NDWI, NDBI)."""
        x = torch.rand(2, 13, 64, 64)
        out = build_multispectral_input_torch(x, DEFAULT_BAND_ORDER)
        assert out.shape == (2, 16, 64, 64)

    def test_no_nan(self):
        """Output tensor must contain no NaN values."""
        x = torch.rand(1, 13, 32, 32)
        out = build_multispectral_input_torch(x, DEFAULT_BAND_ORDER)
        assert not torch.any(torch.isnan(out))

    def test_original_bands_preserved(self):
        """First 13 channels of output must equal the input."""
        x = torch.rand(1, 13, 16, 16)
        out = build_multispectral_input_torch(x, DEFAULT_BAND_ORDER)
        assert torch.allclose(out[:, :13, :, :], x)
