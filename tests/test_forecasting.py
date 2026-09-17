"""
Unit tests for forecasting engine module.
"""

import pytest
import pandas as pd
from backend.data_loader import load_raw_datasets
from backend.features import generate_features
from backend.forecasting import generate_freight_forecast, forecast_naive, forecast_sarima


@pytest.fixture
def feature_df():
    raw_df = load_raw_datasets()
    return generate_features(raw_df)


def test_forecast_naive(feature_df):
    fc_df, metrics = forecast_naive(feature_df, horizon=14)
    assert len(fc_df) == 14
    assert "predicted_freight_rate" in fc_df.columns
    assert "lower_ci" in fc_df.columns
    assert "upper_ci" in fc_df.columns
    assert metrics["MAE"] >= 0.0


def test_forecast_sarima(feature_df):
    fc_df, metrics = forecast_sarima(feature_df, horizon=7)
    assert len(fc_df) == 7
    assert "predicted_freight_rate" in fc_df.columns
    assert metrics["RMSE"] >= 0.0


def test_generate_freight_forecast_auto(feature_df):
    res = generate_freight_forecast(feature_df, horizon=14, selected_model="Auto")
    assert "selected_model" in res
    assert "metrics" in res
    assert len(res["forecast_df"]) == 14
    assert res["metrics"]["MAE"] >= 0.0
