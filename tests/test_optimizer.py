"""
Unit tests for charter-timing optimizer module.
"""

import pytest
import pandas as pd
from backend.data_loader import load_raw_datasets
from backend.features import generate_features
from backend.forecasting import generate_freight_forecast
from backend.optimizer import optimize_charter_timing, evaluate_charter_candidate


@pytest.fixture
def forecast_df():
    raw_df = load_raw_datasets()
    feat_df = generate_features(raw_df)
    fc_res = generate_freight_forecast(feat_df, horizon=14, selected_model="Auto")
    return fc_res["forecast_df"]


def test_optimizer_constraints_and_window(forecast_df):
    earliest = forecast_df["date"].iloc[1].strftime("%Y-%m-%d")
    latest = forecast_df["date"].iloc[5].strftime("%Y-%m-%d")

    res = optimize_charter_timing(
        forecast_df=forecast_df,
        cargo_type="Coking Coal",
        quantity_tonnes=75000.0,
        origin="Australia",
        destination="Paradip",
        earliest_date=earliest,
        latest_date=latest,
        vessel_class="Panamax"
    )

    assert res["success"] is True
    rec_date = res["recommendation"]["recommended_charter_date"]
    
    # Verify recommended date lies within window [earliest, latest]
    assert earliest <= rec_date <= latest

    # Verify vessel capacity constraint
    assert res["recommendation"]["recommended_vessel"] == "Panamax"

    # Verify total cost is finite and positive
    cost = res["recommendation"]["expected_total_logistics_cost_usd"]
    assert cost > 0.0
    assert cost < 1e9


def test_optimizer_determinism(forecast_df):
    """Verify that identical inputs produce identical deterministic recommendations."""
    res1 = optimize_charter_timing(
        forecast_df=forecast_df,
        cargo_type="Iron Ore",
        quantity_tonnes=150000.0,
        origin="Australia",
        destination="Visakhapatnam",
        vessel_class="Auto"
    )

    res2 = optimize_charter_timing(
        forecast_df=forecast_df,
        cargo_type="Iron Ore",
        quantity_tonnes=150000.0,
        origin="Australia",
        destination="Visakhapatnam",
        vessel_class="Auto"
    )

    assert res1["recommendation"]["recommended_charter_date"] == res2["recommendation"]["recommended_charter_date"]
    assert res1["recommendation"]["recommended_vessel"] == res2["recommendation"]["recommended_vessel"]
    assert res1["recommendation"]["expected_total_logistics_cost_usd"] == res2["recommendation"]["expected_total_logistics_cost_usd"]


def test_optimizer_sensitivity(forecast_df):
    """Verify that optimizer recommendations change logically for different cargo size and port constraints."""
    # 1. Panamax size (75k tonnes) -> Auto chooses Panamax
    res_panamax = optimize_charter_timing(
        forecast_df=forecast_df,
        cargo_type="Coking Coal",
        quantity_tonnes=75000.0,
        origin="Australia",
        destination="Paradip",
        vessel_class="Auto"
    )
    assert res_panamax["recommendation"]["recommended_vessel"] == "Panamax"

    # 2. Capesize size (160k tonnes) -> Auto chooses Capesize
    res_cape = optimize_charter_timing(
        forecast_df=forecast_df,
        cargo_type="Iron Ore",
        quantity_tonnes=160000.0,
        origin="Australia",
        destination="Visakhapatnam",
        vessel_class="Auto"
    )
    assert res_cape["recommendation"]["recommended_vessel"] == "Capesize"

    # 3. Capesize to Haldia -> Infeasible (Capesize exceeds Haldia draft limits)
    res_haldia = optimize_charter_timing(
        forecast_df=forecast_df,
        cargo_type="Iron Ore",
        quantity_tonnes=160000.0,
        origin="Australia",
        destination="Kolkata/Haldia",
        vessel_class="Auto"
    )
    assert res_haldia["success"] is False
    assert "infeasibility_reasons" in res_haldia
