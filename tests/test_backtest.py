"""
Unit tests for historical simulation backtest module.
"""

import pytest
from backend.data_loader import load_raw_datasets
from backend.backtesting import run_historical_simulation, BACKTEST_DISCLAIMER


def test_run_historical_simulation():
    raw_df = load_raw_datasets()
    start_d = raw_df["date"].iloc[100].strftime("%Y-%m-%d")
    end_d = raw_df["date"].iloc[300].strftime("%Y-%m-%d")

    res = run_historical_simulation(
        df=raw_df,
        start_date=start_d,
        end_date=end_d,
        horizon=14,
        step_days=30,
        cargo_type="Coking Coal",
        quantity_tonnes=75000.0,
        origin="Australia",
        destination="Paradip",
        vessel_class="Panamax"
    )

    assert res["success"] is True
    assert res["test_periods_count"] > 0
    assert "simulated_cost_difference_total" in res
    assert "win_rate_percentage" in res
    assert res["disclaimer"] == BACKTEST_DISCLAIMER
