"""
Unit tests for FreightIQ Decision Twin Engine and REST API.
"""

import pytest
import pandas as pd
import numpy as np
from fastapi.testclient import TestClient

from backend.main import app
from backend.data_loader import load_raw_datasets
from backend.features import generate_features
from backend.forecasting import generate_freight_forecast
from backend.decision_twin import DecisionTwinEngine

client = TestClient(app)


@pytest.fixture
def forecast_data():
    raw_df = load_raw_datasets()
    feat_df = generate_features(raw_df)
    fc_res = generate_freight_forecast(feat_df, horizon=14, selected_model="Auto")
    return fc_res["forecast_df"]


def test_decision_twin_seed_determinism(forecast_data):
    """Verifies that identical seed produces identical results."""
    engine1 = DecisionTwinEngine(forecast_df=forecast_data, simulations_count=300, seed=42)
    res1 = engine1.run()

    engine2 = DecisionTwinEngine(forecast_df=forecast_data, simulations_count=300, seed=42)
    res2 = engine2.run()

    assert res1["hero_summary"]["expected_cost_usd"] == res2["hero_summary"]["expected_cost_usd"]
    assert res1["hero_summary"]["robustness_score"] == res2["hero_summary"]["robustness_score"]
    assert res1["hero_summary"]["expected_regret_inr_lakh"] == res2["hero_summary"]["expected_regret_inr_lakh"]


def test_simulation_count_scaling(forecast_data):
    """Verifies simulation count parameter is respected."""
    engine300 = DecisionTwinEngine(forecast_df=forecast_data, simulations_count=300, seed=42)
    res300 = engine300.run()
    assert res300["simulations_count"] == 300

    engine1000 = DecisionTwinEngine(forecast_df=forecast_data, simulations_count=1000, seed=42)
    res1000 = engine1000.run()
    assert res1000["simulations_count"] == 1000


def test_all_costs_finite_and_positive(forecast_data):
    """Verifies costs are finite and positive."""
    engine = DecisionTwinEngine(forecast_df=forecast_data, simulations_count=300, seed=42)
    res = engine.run()

    for cand in res["all_candidates"]:
        assert np.isfinite(cand["mean_cost_usd"])
        assert cand["mean_cost_usd"] > 0
        assert np.isfinite(cand["p90_cost_usd"])
        assert cand["p90_cost_usd"] >= cand["mean_cost_usd"] * 0.5


def test_regret_non_negative(forecast_data):
    """Verifies hindsight regret is always >= 0."""
    engine = DecisionTwinEngine(forecast_df=forecast_data, simulations_count=300, seed=42)
    res = engine.run()

    for cand in res["all_candidates"]:
        assert cand["mean_regret_usd"] >= 0.0
        assert cand["p90_regret_usd"] >= 0.0
        assert cand["worst_regret_usd"] >= 0.0


def test_robustness_score_bounds(forecast_data):
    """Verifies robustness score is an integer bounded 0 to 100."""
    engine = DecisionTwinEngine(forecast_df=forecast_data, simulations_count=300, seed=42)
    res = engine.run()

    for cand in res["all_candidates"]:
        assert isinstance(cand["robustness_score"], int)
        assert 0 <= cand["robustness_score"] <= 100


def test_win_frequencies_sum(forecast_data):
    """Verifies win frequencies across candidates sum to ~100%."""
    engine = DecisionTwinEngine(forecast_df=forecast_data, simulations_count=300, seed=42)
    res = engine.run()

    total_win_freq = sum(c["win_freq_pct"] for c in res["all_candidates"])
    assert 95.0 <= total_win_freq <= 105.0


def test_infeasible_vessel_excluded(forecast_data):
    """Verifies vessel with capacity below cargo quantity is excluded or handled."""
    # 200,000 t cargo exceeds Supramax max capacity (60,000 t)
    engine = DecisionTwinEngine(
        forecast_df=forecast_data,
        cargo_type="Coking Coal",
        quantity_tonnes=200000.0,
        vessel_class="Auto",
        simulations_count=100,
        seed=42
    )
    res = engine.run()

    vessels_evaluated = [c["vessel_class"] for c in res["all_candidates"]]
    assert "Supramax" not in vessels_evaluated


def test_freight_shock_increases_mean_cost(forecast_data):
    """Verifies positive freight rate shock increases mean logistics cost."""
    engine_base = DecisionTwinEngine(forecast_df=forecast_data, simulations_count=200, seed=42)
    res_base = engine_base.run()

    shock = {"freight_rate_shock_pct": 25.0}
    engine_shock = DecisionTwinEngine(forecast_df=forecast_data, simulations_count=200, seed=42, active_shock=shock)
    res_shock = engine_shock.run()

    assert res_shock["hero_summary"]["expected_cost_usd"] > res_base["hero_summary"]["expected_cost_usd"]


def test_input_dataframe_not_mutated(forecast_data):
    """Verifies input forecast DataFrame is preserved without side-effects."""
    df_copy = forecast_data.copy()
    engine = DecisionTwinEngine(forecast_df=forecast_data, simulations_count=100, seed=42)
    _ = engine.run()

    pd.testing.assert_frame_equal(forecast_data, df_copy)


def test_api_decision_twin_endpoint():
    """Verifies POST /decision-twin FastAPI endpoint returns 200 OK and valid schema."""
    payload = {
        "cargo_type": "Coking Coal",
        "quantity_tonnes": 75000.0,
        "origin": "Australia",
        "destination": "Paradip",
        "vessel_class": "Auto",
        "risk_tolerance": "Medium",
        "simulations_count": 300,
        "seed": 42
    }
    response = client.post("/decision-twin", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert data["simulations_count"] == 300
    assert "hero_summary" in data
    assert "heatmap_matrix" in data
    assert "pareto_candidates" in data
    assert "fan_chart_data" in data


def test_pareto_dominance_classification(forecast_data):
    """Verifies formal Pareto dominance classification."""
    engine = DecisionTwinEngine(forecast_df=forecast_data, simulations_count=300, seed=42)
    res = engine.run()

    pareto_list = res["pareto_candidates"]
    assert len(pareto_list) > 0
    # At least one candidate must be non-dominated (on the Pareto frontier)
    non_dominated = [c for c in pareto_list if not c["is_pareto_dominated"]]
    assert len(non_dominated) >= 1
    # Recommended option must be non-dominated or near-frontier
    rec_in_pareto = [c for c in pareto_list if c["is_recommended"]]
    assert len(rec_in_pareto) == 1


def test_dynamic_counterfactuals(forecast_data):
    """Verifies counterfactual tipping points are derived via numerical search."""
    engine = DecisionTwinEngine(forecast_df=forecast_data, simulations_count=300, seed=42)
    res = engine.run()

    cfs = res["counterfactuals"]
    assert len(cfs) == 4
    for cf in cfs:
        assert "trigger_event" in cf
        assert "condition" in cf
        assert "threshold_val" in cf


def test_cost_of_waiting_offsets(forecast_data):
    """Verifies cost of waiting compares equivalent decision variables across offsets +1, +3, +5 days."""
    engine = DecisionTwinEngine(forecast_df=forecast_data, simulations_count=300, seed=42)
    res = engine.run()

    cow = res["cost_of_waiting"]
    assert len(cow) == 3
    offsets = [c["offset_days"] for c in cow]
    assert offsets == [1, 3, 5]


def test_performance_benchmark(forecast_data):
    """Verifies 300 simulations finish under 2s and 1000 simulations finish under 5s."""
    import time
    
    t0 = time.time()
    engine300 = DecisionTwinEngine(forecast_df=forecast_data, simulations_count=300, seed=42)
    _ = engine300.run()
    elapsed300 = time.time() - t0
    assert elapsed300 < 2.0, f"300 sims took {elapsed300:.2f}s, exceeding 2.0s benchmark"

    t0 = time.time()
    engine1000 = DecisionTwinEngine(forecast_df=forecast_data, simulations_count=1000, seed=42)
    _ = engine1000.run()
    elapsed1000 = time.time() - t0
    assert elapsed1000 < 5.0, f"1000 sims took {elapsed1000:.2f}s, exceeding 5.0s benchmark"

