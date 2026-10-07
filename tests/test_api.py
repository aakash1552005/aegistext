"""
Unit & Integration Tests for AegisText FastAPI Endpoints
"""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "AegisText API"
    assert data["status"] == "online"


def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["features_registered"] > 0


def test_sanitize_clean_text():
    sample = "This is a clean English sentence."
    response = client.post("/api/v1/sanitize", json={"text": sample})
    assert response.status_code == 200
    data = response.json()
    assert data["sanitized_text"] == sample
    assert not data["tampering_audit"]["adversarial_markers_present"]


def test_sanitize_adversarial_zero_width():
    # Insert zero-width space \u200b
    sample = "This\u200b is an adver\u200csarial hidden text."
    response = client.post("/api/v1/sanitize", json={"text": sample})
    assert response.status_code == 200
    data = response.json()
    assert "\u200b" not in data["sanitized_text"]
    assert data["tampering_audit"]["adversarial_markers_present"]
    assert data["tampering_audit"]["zero_width_count"] >= 2


def test_detection_ai_sample():
    ai_text = (
        "In conclusion, distributed consensus mechanisms represent a pivotal foundation "
        "of modern decentralized architecture. Furthermore, it is crucial to recognize that "
        "latency and fault tolerance must be carefully balanced to achieve optimal throughput."
    )
    response = client.post("/api/v1/detect", json={"text": ai_text, "sanitize_adversarial": True})
    assert response.status_code == 200
    data = response.json()
    assert "classification" in data
    assert "ai_probability" in data
    assert 0.0 <= data["ai_probability"] <= 1.0
    assert data["word_count"] > 10


def test_explain_endpoint():
    sample = (
        "Furthermore, this study clearly demonstrates the vital importance of "
        "interpretability in contemporary biomedical applications. In addition, "
        "deep neural networks require stringent calibration."
    )
    response = client.post("/api/v1/explain", json={"text": sample, "sanitize_adversarial": True})
    assert response.status_code == 200
    data = response.json()
    assert "detection" in data
    assert "feature_attributions" in data
    assert "sentence_heatmap" in data
    assert len(data["sentence_heatmap"]) >= 2
    assert "linguistic_diagnostics" in data


def test_batch_detection():
    texts = [
        "First short sentence for testing detection.",
        "Moreover, advanced machine learning paradigms offer unprecedented opportunities.",
    ]
    response = client.post("/api/v1/batch", json={"texts": texts})
    assert response.status_code == 200
    data = response.json()
    assert data["total_processed"] == 2
    assert len(data["results"]) == 2


def test_metrics_endpoint():
    response = client.get("/api/v1/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "clean_benchmarks" in data


def test_app_ui_endpoint():
    response = client.get("/app")
    assert response.status_code == 200
    assert "AegisText" in response.text
    assert "<!DOCTYPE html>" in response.text

