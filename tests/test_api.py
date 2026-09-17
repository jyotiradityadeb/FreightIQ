"""
Unit tests for FastAPI endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["is_demo_data"] is True


def test_market_latest_endpoint():
    response = client.get("/market/latest")
    assert response.status_code == 200
    data = response.json()
    assert "freight_rate" in data
    assert "bdi" in data


def test_forecast_endpoint():
    response = client.post("/forecast", json={"horizon": 14, "model_name": "Auto"})
    assert response.status_code == 200
    data = response.json()
    assert "selected_model" in data
    assert len(data["forecast_records"]) == 14


def test_optimize_endpoint():
    payload = {
        "cargo_type": "Coking Coal",
        "quantity_tonnes": 75000,
        "origin": "Australia",
        "destination": "Paradip",
        "vessel_class": "Auto"
    }
    response = client.post("/optimize", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "recommendation" in data


def test_backtest_endpoint():
    payload = {
        "start_date": "2024-06-01",
        "end_date": "2025-06-01",
        "horizon": 14,
        "step_days": 30,
        "cargo_type": "Coking Coal",
        "quantity_tonnes": 75000,
        "origin": "Australia",
        "destination": "Paradip",
        "vessel_class": "Panamax"
    }
    response = client.post("/backtest", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "simulated_cost_difference_total" in data
