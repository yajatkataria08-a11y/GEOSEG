"""Tests for pretrained weight expansion (3ch -> 16ch)."""
import pytest
import torch
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.models.channel_expand import expand_first_conv


class TestChannelExpansion:
    """Verify that 3->16 channel expansion preserves variance and shapes."""

    def _make_model(self):
        """Create a minimal model with a 3-channel conv1."""
        import segmentation_models_pytorch as smp
        return smp.Unet(encoder_name='resnet34', encoder_weights='imagenet', in_channels=3, classes=7)

    def test_output_channels(self):
        """After expansion, first conv must accept 16 channels."""
        model = self._make_model()
        expand_first_conv(model, in_channels=16)
        # Find first conv
        first_conv = None
        for m in model.modules():
            if isinstance(m, torch.nn.Conv2d):
                first_conv = m
                break
        assert first_conv is not None
        assert first_conv.in_channels == 16

    def test_forward_pass(self):
        """Model must accept 16-channel input without error."""
        model = self._make_model()
        expand_first_conv(model, in_channels=16)
        model.eval()
        x = torch.rand(1, 16, 64, 64)
        with torch.no_grad():
            out = model(x)
        assert out.shape == (1, 7, 64, 64)

    def test_variance_scaling(self):
        """Expanded weights should have ~(3/16) the variance of original."""
        model = self._make_model()
        # Get original weight variance
        orig_var = None
        for m in model.modules():
            if isinstance(m, torch.nn.Conv2d):
                orig_var = m.weight.data.var().item()
                break
        expand_first_conv(model, in_channels=16)
        new_var = None
        for m in model.modules():
            if isinstance(m, torch.nn.Conv2d):
                new_var = m.weight.data.var().item()
                break
        # New variance should be roughly (3/16)^2 * orig (order of magnitude)
        ratio = new_var / max(orig_var, 1e-10)
        assert ratio < 0.5, f"Variance ratio {ratio} too high — scaling may be wrong"
