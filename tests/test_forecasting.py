"""
Unit tests for forecasting engine module.
"""

import pytest
import numpy as np
import pandas as pd
from backend.data_loader import load_raw_datasets
from backend.features import generate_features
from backend.forecasting import (
    generate_freight_forecast,
    forecast_naive,
    forecast_sarima,
    make_insufficient_data_metrics,
)


@pytest.fixture
def feature_df():
    raw_df = load_raw_datasets()
    return generate_features(raw_df)


def _short_df(n_rows: int) -> pd.DataFrame:
    """Builds a minimal n-row DataFrame that matches the expected schema."""
    dates = pd.date_range("2026-01-01", periods=n_rows, freq="D")
    rates = np.linspace(25.0, 30.0, n_rows)
    df = pd.DataFrame({"date": dates, "freight_rate": rates})
    for col in ["bdi", "capesize_index", "panamax_index", "iron_ore_price",
                "coking_coal_price", "port_congestion_score", "avg_waiting_hours",
                "vessel_availability_count", "weather_risk_score", "event_risk_score"]:
        df[col] = 1.0
    return df


# ---------------------------------------------------------------------------
# Existing tests — still pass with real data; assertions widened where needed
# ---------------------------------------------------------------------------

def test_forecast_naive_full_data(feature_df):
    fc_df, metrics = forecast_naive(feature_df, horizon=14)
    assert len(fc_df) == 14
    assert "predicted_freight_rate" in fc_df.columns
    assert "lower_ci" in fc_df.columns
    assert "upper_ci" in fc_df.columns
    # Full demo data (974 rows) has enough observations; must return OK metrics
    assert metrics["status"] == "OK"
    assert metrics["MAE"] is not None
    assert metrics["MAE"] >= 0.0


def test_forecast_sarima_full_data(feature_df):
    fc_df, metrics = forecast_sarima(feature_df, horizon=7)
    assert len(fc_df) == 7
    assert "predicted_freight_rate" in fc_df.columns
    # Full demo data must return OK metrics
    assert metrics["status"] == "OK"
    assert metrics["RMSE"] is not None
    assert metrics["RMSE"] >= 0.0


def test_generate_freight_forecast_auto_full_data(feature_df):
    res = generate_freight_forecast(feature_df, horizon=14, selected_model="Auto")
    assert "selected_model" in res
    assert "metrics" in res
    assert len(res["forecast_df"]) == 14
    # Full data must yield real numeric metrics
    assert res["metrics"]["status"] == "OK"
    assert res["metrics"]["MAE"] is not None
    assert res["metrics"]["MAE"] >= 0.0


# ---------------------------------------------------------------------------
# Stability test — normal demo data must still auto-select the same model
# ---------------------------------------------------------------------------

def test_auto_selection_stable_on_full_data(feature_df):
    """Auto-selection on 974-row demo data must pick Naive Baseline with a valid OK metric.

    Batch E note: latent-factor generator produces MAE≈0.63 (was 0.326 on v1 data).
    The specific value shifts with data changes; the range [0.1, 1.0] captures both.
    """
    res = generate_freight_forecast(feature_df, horizon=14, selected_model="Auto")
    assert res["selected_model"] == "Naive Baseline", (
        f"Auto-selection changed: expected 'Naive Baseline', got '{res['selected_model']}'"
    )
    assert res["metrics"]["status"] == "OK"
    # MAE range covers both v1 (0.326) and v2 (0.634) data generations
    assert 0.1 <= res["metrics"]["MAE"] <= 1.0


# ---------------------------------------------------------------------------
# INSUFFICIENT_DATA tests — short series must never return invented numbers
# ---------------------------------------------------------------------------

FAKE_NUMBERS = {1.2, 1.5, 5.0, 1.1, 1.4, 4.8, 0.0}


def test_naive_insufficient_data():
    """forecast_naive on a very short series must return INSUFFICIENT_DATA, not fake zeros."""
    short = _short_df(10)  # 10 rows < horizon(14)+1 = 15 required
    fc_df, metrics = forecast_naive(short, horizon=14)
    # Forecast itself can still be produced
    assert len(fc_df) == 14
    # Metrics must be INSUFFICIENT_DATA
    assert metrics["status"] == "INSUFFICIENT_DATA", f"Got status={metrics['status']}"
    assert metrics["MAE"] is None
    assert metrics["RMSE"] is None
    assert metrics["MAPE"] is None
    assert "minimum_required_observations" in metrics
    assert "available_observations" in metrics
    assert metrics["available_observations"] == 10
    # No fake fallback number should appear
    for v in [metrics["MAE"], metrics["RMSE"], metrics["MAPE"]]:
        assert v not in FAKE_NUMBERS, f"Fake fallback number {v} found in metrics"


def test_sarima_insufficient_data():
    """forecast_sarima with too few rows for a holdout fold must return INSUFFICIENT_DATA."""
    # horizon=14 requires train_len > 30, so need > 44 rows; 40 is insufficient
    short = _short_df(40)
    fc_df, metrics = forecast_sarima(short, horizon=14)
    assert len(fc_df) == 14
    assert metrics["status"] == "INSUFFICIENT_DATA", f"Got status={metrics['status']}"
    assert metrics["MAE"] is None
    assert metrics["RMSE"] is None
    assert metrics["MAPE"] is None
    for v in [metrics["MAE"], metrics["RMSE"], metrics["MAPE"]]:
        assert v not in FAKE_NUMBERS, f"Fake fallback number {v} found in metrics"


def test_auto_selection_excludes_insufficient_data_from_ranking():
    """When only Naive can produce metrics (others INSUFFICIENT_DATA), auto picks Naive."""
    # 20 rows: Naive needs >14 (OK), SARIMA needs >44 (INSUFFICIENT_DATA)
    short = _short_df(20)
    res = generate_freight_forecast(short, horizon=14, selected_model="Auto")
    # Naive is the only eligible candidate; must be selected
    assert res["selected_model"] == "Naive Baseline"
    assert res["metrics"]["status"] == "OK"
    assert res["metrics"]["MAE"] is not None


def test_all_insufficient_data_fallback():
    """When every model has INSUFFICIENT_DATA, generator falls back to Naive Baseline."""
    # 10 rows: even Naive needs >14, so all INSUFFICIENT_DATA
    tiny = _short_df(10)
    res = generate_freight_forecast(tiny, horizon=14, selected_model="Auto")
    assert res["selected_model"] == "Naive Baseline"
    # Chosen model metrics will also be INSUFFICIENT_DATA
    assert res["metrics"]["status"] == "INSUFFICIENT_DATA"
    assert res["metrics"]["MAE"] is None


def test_make_insufficient_data_metrics_helper():
    m = make_insufficient_data_metrics(available=5, required=30)
    assert m["status"] == "INSUFFICIENT_DATA"
    assert m["MAE"] is None
    assert m["RMSE"] is None
    assert m["MAPE"] is None
    assert m["available_observations"] == 5
    assert m["minimum_required_observations"] == 30
