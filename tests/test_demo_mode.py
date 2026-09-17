"""
FreightIQ Demo Mode & Reset Unit Tests

Tests SIH demo mode state initialization, dataset loading, and demo state reset behavior.
"""

import pytest
import os
from backend.data_loader import load_raw_datasets
from backend.features import generate_features
from backend.forecasting import generate_freight_forecast
from backend.optimizer import optimize_charter_timing
from backend.disruption_engine import evaluate_control_tower_state
from backend.schemas import ScenarioShock


def test_demo_dataset_loading():
    """Demo datasets load cleanly with fixed reproducible seed."""
    df = load_raw_datasets()
    assert len(df) >= 365
    assert "freight_rate" in df.columns
    assert "port_congestion_score" in df.columns
    assert "vessel_availability_count" in df.columns


def test_demo_reset_behavior():
    """Reset clears disruption overrides and restores baseline valid recommendation."""
    raw_df = load_raw_datasets()
    feat_df = generate_features(raw_df)
    fc_res = generate_freight_forecast(feat_df, horizon=14, selected_model="Auto")

    # Evaluate under disruption shock
    disruption_shock = ScenarioShock(port_congestion_shock_pct=75.0, vessel_availability_shock_pct=-40.0)
    ct_disrupted = evaluate_control_tower_state(fc_res["forecast_df"], shock_override=disruption_shock)
    assert ct_disrupted["disruption_simulated"] is True

    # Evaluate under reset (shock = None)
    ct_reset = evaluate_control_tower_state(fc_res["forecast_df"], shock_override=None)
    assert ct_reset["disruption_simulated"] is False
    assert ct_reset["current_recommendation"]["status"] == "RECOMMENDATION VALID"
    assert ct_reset["market_stress_index"]["state"] in ["Normal", "Watch"]
