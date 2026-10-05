"""Tests for the native C++ pybind11 module."""
import pytest
import numpy as np
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    import geoseg_cpp
    HAS_CPP = True
except ImportError:
    HAS_CPP = False


@pytest.mark.skipif(not HAS_CPP, reason="geoseg_cpp not compiled")
class TestBandMathEngine:
    """Test C++ BandMathEngine via pybind11."""

    def _make_engine(self):
        return geoseg_cpp.BandMathEngine(
            ['B01','B02','B03','B04','B05','B06','B07','B08','B8A','B09','B10','B11','B12']
        )

    def test_ndvi_shape(self):
        engine = self._make_engine()
        data = np.random.rand(13, 64, 64).astype(np.float32)
        ndvi = engine.compute_ndvi(data)
        assert ndvi.shape == (1, 64, 64)

    def test_ndvi_range(self):
        engine = self._make_engine()
        data = np.random.rand(13, 32, 32).astype(np.float32)
        ndvi = engine.compute_ndvi(data)
        assert np.all(ndvi >= -1.0) and np.all(ndvi <= 1.0)

    def test_ndvi_vegetation(self):
        """High NIR(B08), low Red(B04) => positive NDVI."""
        engine = self._make_engine()
        data = np.full((13, 4, 4), 0.1, dtype=np.float32)
        data[3, :, :] = 0.03   # B04 = Red
        data[7, :, :] = 0.50   # B08 = NIR
        ndvi = engine.compute_ndvi(data)
        assert np.all(ndvi > 0.8)

    def test_multispectral_build(self):
        """13-channel input -> 16-channel output."""
        engine = self._make_engine()
        data = np.random.rand(13, 32, 32).astype(np.float32)
        full = engine.build_multispectral_input(data)
        assert full.shape[0] == 16
        assert full.shape[1] == 32 and full.shape[2] == 32

    def test_no_nan(self):
        engine = self._make_engine()
        data = np.zeros((13, 8, 8), dtype=np.float32)
        ndvi = engine.compute_ndvi(data)
        assert not np.any(np.isnan(ndvi))


@pytest.mark.skipif(not HAS_CPP, reason="geoseg_cpp not compiled")
class TestTileManager:
    def test_tile_count(self):
        tm = geoseg_cpp.TileManager(512, 32)
        count = tm.get_tile_count(2048, 2048)
        assert count > 0
        assert count == 25

    def test_params(self):
        tm = geoseg_cpp.TileManager(256, 16)
        assert tm.get_tile_size() == 256
        assert tm.get_overlap() == 16
        assert tm.get_stride() == 240


@pytest.mark.skipif(not HAS_CPP, reason="geoseg_cpp not compiled")
class TestBoundingBox:
    def test_contains(self):
        bbox = geoseg_cpp.BoundingBox(77.0, 23.0, 78.0, 24.0)
        assert bbox.contains(77.5, 23.5)
        assert not bbox.contains(80.0, 23.5)

    def test_width_height(self):
        bbox = geoseg_cpp.BoundingBox(10.0, 20.0, 15.0, 25.0)
        assert bbox.width() == pytest.approx(5.0)
        assert bbox.height() == pytest.approx(5.0)
