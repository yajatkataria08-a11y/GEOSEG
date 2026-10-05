"""Smoke tests for the FastAPI endpoints."""
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi.testclient import TestClient
from api.server import app

client = TestClient(app)


class TestHealth:
    def test_health_ok(self):
        r = client.get('/api/health')
        assert r.status_code == 200
        data = r.json()
        assert data['status'] == 'ok'


class TestTraining:
    def test_status_idle(self):
        r = client.get('/api/training/status')
        assert r.status_code == 200
        data = r.json()
        assert data['status'] in ('idle', 'running', 'completed', 'failed')


class TestResults:
    def test_list_results(self):
        r = client.get('/api/results/')
        assert r.status_code == 200
        data = r.json()
        assert 'results' in data
        assert 'total' in data

    def test_checkpoints(self):
        r = client.get('/api/results/checkpoints')
        assert r.status_code == 200


class TestCppEngine:
    def test_run(self):
        r = client.post('/api/cpp-engine/run')
        assert r.status_code == 200
        data = r.json()
        assert 'success' in data
        assert 'benchmarks' in data


class TestAOI:
    def test_invalid_bbox(self):
        r = client.post('/api/aoi/export', json={
            'west': 80.0, 'south': 23.0, 'east': 70.0, 'north': 24.0,
            'start_date': '2025-01-01', 'end_date': '2025-06-01'
        })
        assert r.status_code == 400

    def test_invalid_date(self):
        r = client.post('/api/aoi/export', json={
            'west': 77.0, 'south': 23.0, 'east': 78.0, 'north': 24.0,
            'start_date': '2025-06-01', 'end_date': '2025-01-01'
        })
        assert r.status_code == 400

    def test_synthetic_export(self):
        """Valid export should succeed and honestly flag is_synthetic."""
        r = client.post('/api/aoi/export', json={
            'west': 77.0, 'south': 23.0, 'east': 77.5, 'north': 23.5,
            'start_date': '2025-01-01', 'end_date': '2025-06-01'
        })
        assert r.status_code == 200
        data = r.json()
        assert data['success'] is True
        assert data['is_synthetic'] is True
        assert '[SYNTHETIC]' in data['message']
