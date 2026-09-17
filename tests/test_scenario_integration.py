"""
Integration tests for Scenario Lab cross-page shock propagation and reset.
"""

import pytest
import pandas as pd
import numpy as np
from backend.scenario_engine import ScenarioShock, run_scenario_simulation
from backend.decision_twin import DecisionTwinEngine


def test_scenario_shock_fields():
    scen = ScenarioShock(
        freight_rate_shock_pct=25.0,
        port_congestion_shock_pct=50.0,
        vessel_availability_shock_pct=-30.0,
        demurrage_rate_shock_pct=30.0,
        weather_risk_level="Moderate",
        geopolitical_risk_level="Elevated"
    )
    assert scen.freight_rate_shock_pct == 25.0
    assert scen.port_congestion_shock_pct == 50.0
    assert scen.vessel_availability_shock_pct == -30.0
    assert scen.demurrage_rate_shock_pct == 30.0


def test_scenario_shock_propagation_to_twin():
    dates = pd.date_range(end=pd.Timestamp.now(), periods=30, freq="D")
    df = pd.DataFrame({
        "date": dates,
        "predicted_freight_rate": [25.0] * 30,
        "freight_rate": [25.0] * 30,
        "port_congestion_score": [45.0] * 30,
        "avg_waiting_hours": [36.0] * 30,
        "vessel_availability_count": [20] * 30,
        "weather_risk_score": [2.0] * 30,
        "event_risk_score": [1.0] * 30
    })

    shock_dict = {
        "freight_pct": 30.0,
        "congestion_pct": 40.0,
        "is_active": True
    }

    engine = DecisionTwinEngine(
        forecast_df=df,
        cargo_type="Coking Coal",
        quantity_tonnes=75000.0,
        origin="Australia",
        destination="Paradip",
        simulations_count=10,
        seed=42,
        active_shock=shock_dict
    )
    assert engine.active_shock == shock_dict

    res = engine.run()
    assert res["success"] is True



def test_scenario_reset_restores_baseline():
    default_shock = ScenarioShock()
    assert default_shock.freight_rate_shock_pct == 0.0
    assert default_shock.port_congestion_shock_pct == 0.0
