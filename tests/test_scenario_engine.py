"""
FreightIQ Scenario Engine Unit Tests

Tests interactive What-If simulation engine, dataset immutability,
cost responses to market shocks, sensitivity calculation, composite confidence score bounds,
Pydantic validation, and FastAPI /scenario endpoint.
"""

import pytest
import pandas as pd
from fastapi.testclient import TestClient

from backend.data_loader import load_raw_datasets
from backend.features import generate_features
from backend.forecasting import generate_freight_forecast
from backend.schemas import ScenarioRequest, ScenarioShock
from backend.scenario_engine import run_scenario_simulation, build_shocked_forecast_df
from backend.main import app

client = TestClient(app)


@pytest.fixture
def sample_forecast_df():
    raw_df = load_raw_datasets()
    feat_df = generate_features(raw_df)
    fc_res = generate_freight_forecast(feat_df, horizon=14, selected_model="Auto")
    return fc_res["forecast_df"]


def test_zero_shock_matches_baseline(sample_forecast_df):
    """1. Zero shock produces same recommendation as baseline."""
    req = ScenarioRequest(
        cargo_type="Coking Coal",
        quantity_tonnes=75000.0,
        destination="Paradip",
        shock=ScenarioShock()
    )
    res = run_scenario_simulation(sample_forecast_df, req)
    assert res["success"] is True
    assert res["decision_status"] == "Recommendation Unchanged"
    assert res["baseline_recommendation"]["charter_date"] == res["stressed_recommendation"]["charter_date"]
    assert res["baseline_recommendation"]["total_logistics_cost_usd"] == res["stressed_recommendation"]["total_logistics_cost_usd"]


def test_increased_congestion_raises_congestion_cost(sample_forecast_df):
    """2. Increased congestion raises waiting/congestion cost."""
    req_base = ScenarioRequest(destination="Paradip", shock=ScenarioShock(port_congestion_shock_pct=0.0))
    req_shock = ScenarioRequest(destination="Paradip", shock=ScenarioShock(port_congestion_shock_pct=50.0, target_port="Paradip"))
    
    res_base = run_scenario_simulation(sample_forecast_df, req_base)
    res_shock = run_scenario_simulation(sample_forecast_df, req_shock)

    base_cong = res_base["stressed_recommendation"]["congestion_cost_usd"]
    shock_cong = res_shock["stressed_recommendation"]["congestion_cost_usd"]

    assert shock_cong > base_cong


def test_higher_freight_rate_raises_freight_cost(sample_forecast_df):
    """3. Higher freight rate raises freight cost."""
    req_base = ScenarioRequest(shock=ScenarioShock(freight_rate_shock_pct=0.0))
    req_shock = ScenarioRequest(shock=ScenarioShock(freight_rate_shock_pct=20.0))
    
    res_base = run_scenario_simulation(sample_forecast_df, req_base)
    res_shock = run_scenario_simulation(sample_forecast_df, req_shock)

    base_freight = res_base["stressed_recommendation"]["freight_cost_usd"]
    shock_freight = res_shock["stressed_recommendation"]["freight_cost_usd"]

    assert shock_freight > base_freight


def test_vessel_shortage_reduces_availability_count(sample_forecast_df):
    """4. Vessel shortage reduces vessel count and cannot create more vessels."""
    req_unshocked = ScenarioShock(vessel_availability_shock_pct=0.0)
    req_shocked = ScenarioShock(vessel_availability_shock_pct=-50.0)

    unshocked_df = build_shocked_forecast_df(sample_forecast_df, req_unshocked, "Paradip")
    shocked_df = build_shocked_forecast_df(sample_forecast_df, req_shocked, "Paradip")

    orig_count = unshocked_df["vessel_availability_count"].iloc[0]
    new_count = shocked_df["vessel_availability_count"].iloc[0]

    assert new_count < orig_count
    assert new_count >= 0


def test_severe_weather_increases_risk_adjustment(sample_forecast_df):
    """5. Severe weather increases risk adjustment."""
    req_low = ScenarioRequest(shock=ScenarioShock(weather_risk_level="Low"))
    req_sev = ScenarioRequest(shock=ScenarioShock(weather_risk_level="Severe"))

    res_low = run_scenario_simulation(sample_forecast_df, req_low)
    res_sev = run_scenario_simulation(sample_forecast_df, req_sev)

    low_risk = res_low["stressed_recommendation"]["route_risk_penalty_usd"]
    sev_risk = res_sev["stressed_recommendation"]["route_risk_penalty_usd"]

    assert sev_risk > low_risk


def test_scenario_engine_does_not_mutate_input_df(sample_forecast_df):
    """6. Scenario engine does not mutate original input dataset."""
    df_copy = sample_forecast_df.copy(deep=True)

    req = ScenarioRequest(shock=ScenarioShock(freight_rate_shock_pct=25.0, port_congestion_shock_pct=80.0))
    _ = run_scenario_simulation(sample_forecast_df, req)

    pd.testing.assert_frame_equal(sample_forecast_df, df_copy)


def test_scenario_outputs_deterministic(sample_forecast_df):
    """7. Outputs are deterministic for identical input."""
    req = ScenarioRequest(shock=ScenarioShock(freight_rate_shock_pct=15.0, vessel_availability_shock_pct=-20.0))

    res1 = run_scenario_simulation(sample_forecast_df, req)
    res2 = run_scenario_simulation(sample_forecast_df, req)

    assert res1["stressed_recommendation"]["total_logistics_cost_usd"] == res2["stressed_recommendation"]["total_logistics_cost_usd"]
    assert res1["confidence_score"] == res2["confidence_score"]


def test_decision_confidence_bounds(sample_forecast_df):
    """8. Decision confidence score stays bounded between 0 and 100."""
    shocks = [
        ScenarioShock(),
        ScenarioShock(weather_risk_level="Severe", geopolitical_risk_level="Major Disruption", port_congestion_shock_pct=100.0),
        ScenarioShock(freight_rate_shock_pct=-15.0, vessel_availability_shock_pct=30.0)
    ]
    for s in shocks:
        req = ScenarioRequest(shock=s)
        res = run_scenario_simulation(sample_forecast_df, req)
        score = res["confidence_score"]
        assert 0.0 <= score <= 100.0


def test_invalid_shock_ranges_rejected():
    """9. Invalid shock ranges rejected by Pydantic validation."""
    with pytest.raises(ValueError):
        ScenarioShock(freight_rate_shock_pct=500.0)  # Max allowed is +30%

    with pytest.raises(ValueError):
        ScenarioShock(port_congestion_shock_pct=-90.0)  # Min allowed is -50%


def test_api_scenario_endpoint():
    """10. API /scenario responds correctly."""
    payload = {
        "cargo_type": "Coking Coal",
        "quantity_tonnes": 75000.0,
        "origin": "Australia",
        "destination": "Paradip",
        "vessel_class": "Auto",
        "risk_tolerance": "Medium",
        "shock": {
            "freight_rate_shock_pct": 10.0,
            "port_congestion_shock_pct": 25.0,
            "target_port": "Paradip",
            "vessel_availability_shock_pct": -15.0,
            "weather_risk_level": "Moderate",
            "geopolitical_risk_level": "Normal"
        }
    }
    response = client.post("/scenario", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "baseline_recommendation" in data
    assert "stressed_recommendation" in data
    assert "comparison_table" in data
    assert "confidence_score" in data
    assert 0 <= data["confidence_score"] <= 100
    assert data["is_demo_data"] is True
