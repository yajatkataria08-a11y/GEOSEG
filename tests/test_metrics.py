"""Tests for multi-class evaluation metrics."""
import pytest
import torch
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils.metrics import IoUTracker, AccuracyTracker


class TestAccuracyTracker:
    """Test classification accuracy tracker."""

    def test_perfect_accuracy(self):
        tracker = AccuracyTracker()
        preds = torch.tensor([0, 1, 2, 3, 4])
        labels = torch.tensor([0, 1, 2, 3, 4])
        tracker.update(preds, labels)
        assert tracker.compute() == pytest.approx(1.0)

    def test_zero_accuracy(self):
        tracker = AccuracyTracker()
        preds = torch.tensor([0, 0, 0, 0])
        labels = torch.tensor([1, 2, 3, 4])
        tracker.update(preds, labels)
        assert tracker.compute() == pytest.approx(0.0)

    def test_partial_accuracy(self):
        tracker = AccuracyTracker()
        preds = torch.tensor([0, 1, 0, 1])
        labels = torch.tensor([0, 1, 1, 0])
        tracker.update(preds, labels)
        assert tracker.compute() == pytest.approx(0.5)

    def test_reset(self):
        tracker = AccuracyTracker()
        preds = torch.tensor([0, 1, 2])
        labels = torch.tensor([0, 1, 2])
        tracker.update(preds, labels)
        tracker.reset()
        assert tracker.compute() == 0.0


class TestIoUTracker:
    """Test IoU (Jaccard Index) tracker."""

    def test_perfect_iou(self):
        tracker = IoUTracker(num_classes=3, device="cpu")
        preds = torch.tensor([0, 1, 2, 0, 1, 2])
        labels = torch.tensor([0, 1, 2, 0, 1, 2])
        tracker.update(preds, labels)
        miou = tracker.compute()
        assert miou == pytest.approx(1.0, abs=0.01)

    def test_iou_range(self):
        """mIoU must always be in [0, 1]."""
        tracker = IoUTracker(num_classes=5, device="cpu")
        preds = torch.randint(0, 5, (100,))
        labels = torch.randint(0, 5, (100,))
        tracker.update(preds, labels)
        miou = tracker.compute()
        assert 0.0 <= miou <= 1.0

    def test_per_class_iou(self):
        """Per-class IoU should return num_classes values."""
        tracker = IoUTracker(num_classes=4, device="cpu")
        preds = torch.tensor([0, 1, 2, 3, 0, 1])
        labels = torch.tensor([0, 1, 2, 3, 0, 1])
        tracker.update(preds, labels)
        per_class = tracker.compute_per_class()
        assert per_class.shape == (4,)
        assert torch.all(per_class == 1.0)

    def test_reset(self):
        tracker = IoUTracker(num_classes=3, device="cpu")
        preds = torch.tensor([0, 1, 2])
        labels = torch.tensor([0, 1, 2])
        tracker.update(preds, labels)
        assert tracker.compute() == pytest.approx(1.0, abs=0.01)
        tracker.reset()
        # After reset, provide completely mismatched predictions
        preds2 = torch.tensor([0, 1, 2])
        labels2 = torch.tensor([1, 2, 0])
        tracker.update(preds2, labels2)
        assert tracker.compute() == pytest.approx(0.0, abs=0.01)
