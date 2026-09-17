"""
Regression test for Decision Twin robustness score consistency across Overview and Decision Twin pages.
"""

import pytest
import pandas as pd
from backend.decision_twin import (
    DecisionTwinEngine,
    get_or_compute_decision_twin,
    compute_decision_twin_hash
)


def test_overview_and_decision_twin_page_robustness_consistency():
    dates = pd.date_range(end=pd.Timestamp.now(), periods=30, freq="D")
    forecast_df = pd.DataFrame({
        "date": dates,
        "predicted_freight_rate": [25.0] * 30,
        "freight_rate": [25.0] * 30,
        "port_congestion_score": [45.0] * 30,
        "avg_waiting_hours": [36.0] * 30,
        "vessel_availability_count": [20] * 30,
        "weather_risk_score": [2.0] * 30,
        "event_risk_score": [1.0] * 30
    })

    shipment_ctx = {
        "shipment_id": "FIQ-2026-TEST",
        "cargo_type": "Coking Coal",
        "quantity_tonnes": 75000.0,
        "origin": "Australia",
        "destination": "Paradip",
        "vessel_class": "Auto",
        "risk_tolerance": "Medium"
    }

    active_scenario = {
        "is_active": True,
        "scenario_name": "Port Congestion Surge",
        "freight_pct": 10.0,
        "congestion_pct": 50.0,
        "availability_pct": -20.0,
        "weather_level": "Low",
        "geopolitical_level": "Normal"
    }

    # 1. Directly execute DecisionTwinEngine (simulating raw backend run)
    active_shock_dict = {
        "freight_rate_shock_pct": 10.0,
        "port_congestion_shock_pct": 50.0,
        "vessel_availability_shock_pct": -20.0,
        "weather_risk_level": "Low",
        "geopolitical_risk_level": "Normal"
    }
    raw_engine = DecisionTwinEngine(
        forecast_df=forecast_df,
        cargo_type="Coking Coal",
        quantity_tonnes=75000.0,
        origin="Australia",
        destination="Paradip",
        vessel_class="Auto",
        risk_tolerance="Medium",
        simulations_count=1000,
        seed=42,
        active_shock=active_shock_dict
    )
    raw_result = raw_engine.run()

    # 2. Execute get_or_compute_decision_twin (simulating Overview call)
    overview_result = get_or_compute_decision_twin(
        shipment_ctx=shipment_ctx,
        active_scenario=active_scenario,
        forecast_df=forecast_df,
        simulations_count=1000,
        seed=42
    )

    # 3. Execute get_or_compute_decision_twin (simulating Decision Twin page call)
    dt_page_result = get_or_compute_decision_twin(
        shipment_ctx=shipment_ctx,
        active_scenario=active_scenario,
        forecast_df=forecast_df,
        simulations_count=1000,
        seed=42
    )

    # Verify score equality across all 3
    raw_score = raw_result["hero_summary"]["robustness_score"]
    overview_score = overview_result["hero_summary"]["robustness_score"]
    dt_page_score = dt_page_result["hero_summary"]["robustness_score"]

    assert overview_score == raw_score, f"Overview score ({overview_score}) does not match raw score ({raw_score})"
    assert dt_page_score == raw_score, f"Decision Twin page score ({dt_page_score}) does not match raw score ({raw_score})"


def test_scenario_reset_restores_baseline_hash():
    shipment_ctx = {
        "shipment_id": "FIQ-2026-TEST",
        "cargo_type": "Coking Coal",
        "quantity_tonnes": 75000.0,
        "origin": "Australia",
        "destination": "Paradip",
    }
    scen_active = {"is_active": True, "freight_pct": 25.0}
    scen_inactive = {"is_active": False, "freight_pct": 0.0}

    hash_active = compute_decision_twin_hash(shipment_ctx, scen_active)
    hash_inactive = compute_decision_twin_hash(shipment_ctx, scen_inactive)
    hash_default = compute_decision_twin_hash(shipment_ctx, {})

    assert hash_active != hash_inactive
    assert hash_inactive == hash_default
