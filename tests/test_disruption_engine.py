"""
FreightIQ Disruption Engine & Control Tower Unit Tests

Tests operational signal classification, Market Stress Index, Decision Stability score,
active alert triggers, recommendation change detector, dataset non-mutation,
determinism, reset behavior, and FastAPI /control-tower endpoint.
"""

import pytest
import pandas as pd
from fastapi.testclient import TestClient

from backend.data_loader import load_raw_datasets
from backend.features import generate_features
from backend.forecasting import generate_freight_forecast
from backend.schemas import ScenarioShock
from backend.disruption_engine import (
    classify_signal_severity,
    calculate_market_stress_index,
    calculate_decision_stability,
    generate_active_alerts,
    evaluate_control_tower_state
)
from backend.main import app

client = TestClient(app)


@pytest.fixture
def sample_forecast_df():
    raw_df = load_raw_datasets()
    feat_df = generate_features(raw_df)
    fc_res = generate_freight_forecast(feat_df, horizon=14, selected_model="Auto")
    return fc_res["forecast_df"]


def test_normal_inputs_produce_normal_or_watch_states():
    """1. Normal inputs produce Normal / Watch states correctly."""
    status, sev = classify_signal_severity("port_congestion", 45.0)
    assert status == "Normal"
    assert sev == 0

    status_w, sev_w = classify_signal_severity("port_congestion", 55.0)
    assert status_w == "Watch"
    assert sev_w == 1


def test_high_congestion_triggers_elevated_or_disrupted():
    """2. High congestion triggers Elevated / Disrupted."""
    status_el, sev_el = classify_signal_severity("port_congestion", 72.0)
    assert status_el == "Elevated"
    assert sev_el == 2

    status_dis, sev_dis = classify_signal_severity("port_congestion", 88.0)
    assert status_dis == "Disrupted"
    assert sev_dis == 3


def test_low_vessel_availability_increases_severity():
    """3. Low vessel availability increases severity."""
    status_norm, sev_norm = classify_signal_severity("vessel_availability", 25)
    assert status_norm == "Normal"
    assert sev_norm == 0

    status_low, sev_low = classify_signal_severity("vessel_availability", 5)
    assert status_low == "Disrupted"
    assert sev_low == 3


def test_freight_spike_increases_market_stress():
    """4. Freight spike increases market stress score."""
    stress_base = calculate_market_stress_index(
        forecast_change_pct=1.0,
        port_congestion_score=40.0,
        vessel_avail_count=25,
        weather_risk_score=2.0,
        event_risk_score=1.0
    )
    stress_spike = calculate_market_stress_index(
        forecast_change_pct=15.0,
        port_congestion_score=40.0,
        vessel_avail_count=25,
        weather_risk_score=2.0,
        event_risk_score=1.0
    )
    assert stress_spike["score"] > stress_base["score"]


def test_route_risk_contributes_to_market_stress():
    """5. Route risk contributes to market stress."""
    stress_low = calculate_market_stress_index(
        forecast_change_pct=0.0,
        port_congestion_score=40.0,
        vessel_avail_count=25,
        weather_risk_score=2.0,
        event_risk_score=1.0
    )
    stress_high = calculate_market_stress_index(
        forecast_change_pct=0.0,
        port_congestion_score=40.0,
        vessel_avail_count=25,
        weather_risk_score=8.0,
        event_risk_score=7.0
    )
    assert stress_high["score"] > stress_low["score"]


def test_severe_combined_stress_triggers_active_alerts():
    """6. Severe combined stress triggers active alerts."""
    signals = {
        "port_congestion": {"severity": 2},
        "freight_market": {"severity": 2},
        "vessel_availability": {"severity": 2},
        "route_weather_risk": {"severity": 1}
    }
    alerts = generate_active_alerts(
        signal_states=signals,
        port_congestion_score=78.0,
        vessel_avail_count=8,
        forecast_change_pct=10.0,
        destination="Paradip"
    )
    assert len(alerts) > 0
    severities = [a["severity"] for a in alerts]
    assert "HIGH" in severities or "MEDIUM" in severities


def test_reset_returns_baseline_state(sample_forecast_df):
    """7. Reset returns baseline state."""
    ct_base = evaluate_control_tower_state(sample_forecast_df, shock_override=None)
    assert ct_base["success"] is True
    assert ct_base["current_recommendation"]["status"] == "RECOMMENDATION VALID"
    assert ct_base["disruption_simulated"] is False


def test_recommendation_change_detector(sample_forecast_df):
    """8. Recommendation change detector works under disruption shock."""
    disruption_shock = ScenarioShock(
        freight_rate_shock_pct=12.0,
        port_congestion_shock_pct=60.0,
        target_port="Paradip",
        vessel_availability_shock_pct=-35.0,
        weather_risk_level="High"
    )
    ct_disrupted = evaluate_control_tower_state(sample_forecast_df, shock_override=disruption_shock)
    assert ct_disrupted["success"] is True
    assert ct_disrupted["current_recommendation"]["status"] in ["RECOMMENDATION CHANGED", "REVIEW REQUIRED"]
    assert ct_disrupted["disruption_simulated"] is True


def test_decision_stability_bounds():
    """9. Decision stability stays between 0 and 100."""
    st1 = calculate_decision_stability(market_stress_score=10.0, congestion_score=35.0, weather_risk_score=2.0, event_risk_score=1.0)
    st2 = calculate_decision_stability(market_stress_score=90.0, congestion_score=90.0, weather_risk_score=9.0, event_risk_score=8.0, recommendation_changed=True)

    assert 0.0 <= st1["score"] <= 100.0
    assert 0.0 <= st2["score"] <= 100.0
    assert st1["score"] > st2["score"]


def test_market_stress_index_bounds():
    """10. Market stress index stays between 0 and 100."""
    idx1 = calculate_market_stress_index(0.0, 30.0, 30, 1.0, 1.0)
    idx2 = calculate_market_stress_index(30.0, 100.0, 0, 10.0, 10.0)

    assert 0.0 <= idx1["score"] <= 100.0
    assert 0.0 <= idx2["score"] <= 100.0
    assert idx2["score"] > idx1["score"]


def test_disruption_engine_determinism(sample_forecast_df):
    """11. Outputs are deterministic for identical input."""
    ct1 = evaluate_control_tower_state(sample_forecast_df)
    ct2 = evaluate_control_tower_state(sample_forecast_df)

    assert ct1["market_stress_index"]["score"] == ct2["market_stress_index"]["score"]
    assert ct1["decision_stability"]["score"] == ct2["decision_stability"]["score"]


def test_disruption_engine_does_not_mutate_df(sample_forecast_df):
    """12. Disruption engine does not mutate original input dataset."""
    df_copy = sample_forecast_df.copy(deep=True)
    disruption_shock = ScenarioShock(port_congestion_shock_pct=80.0, vessel_availability_shock_pct=-50.0)
    _ = evaluate_control_tower_state(sample_forecast_df, shock_override=disruption_shock)

    pd.testing.assert_frame_equal(sample_forecast_df, df_copy)


def test_api_control_tower_endpoint():
    """13. API /control-tower endpoint responds correctly."""
    response = client.get("/control-tower")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "current_recommendation" in data
    assert "signal_states" in data
    assert "active_alerts" in data
    assert "market_stress_index" in data
    assert "decision_stability" in data
    assert data["is_demo_data"] is True
