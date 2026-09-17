"""
Tests for backend/validation.py — real-data validation path.

Covers:
  - ValidationResult dataclass fields
  - DataMode enum values
  - Synthetic validation wrapper
  - Real validation with a fixture-injected DataFrame
  - Offline fallback (no network, no cache)
  - Separation: SYNTHETIC and PUBLIC_REAL results must never share status "OK"
"""

import os
import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch

from backend.validation import (
    DataMode,
    ValidationResult,
    get_synthetic_validation,
    run_real_validation,
    fetch_openmeteo_series,
    build_validation_chart_data,
    TEST_DAYS,
    MIN_TRAIN_DAYS,
    DEFAULT_CACHE_FILENAME,
)


# ── DataMode enum ──────────────────────────────────────────────────────────────

def test_datamode_enum_has_required_values():
    assert DataMode.SYNTHETIC.value == "SYNTHETIC"
    assert DataMode.PUBLIC_REAL.value == "PUBLIC_REAL"
    assert DataMode.CONNECTED_REAL.value == "CONNECTED_REAL"
    assert DataMode.MANUAL_REAL.value == "MANUAL_REAL"


# ── ValidationResult dataclass ────────────────────────────────────────────────

def _make_result(**overrides) -> ValidationResult:
    defaults = dict(
        source_name="Test Source",
        source_type="test",
        data_mode=DataMode.SYNTHETIC,
        start_date="2026-01-01",
        end_date="2026-09-01",
        n_observations=365,
        model_name="SARIMA",
        horizon=14,
        mae=1.23,
        rmse=1.50,
        mape=5.2,
        status="OK",
        notes="test notes",
        variable_label="test variable",
    )
    defaults.update(overrides)
    return ValidationResult(**defaults)


def test_validation_result_has_required_fields():
    r = _make_result()
    assert hasattr(r, "source_name")
    assert hasattr(r, "source_type")
    assert hasattr(r, "data_mode")
    assert hasattr(r, "start_date")
    assert hasattr(r, "end_date")
    assert hasattr(r, "n_observations")
    assert hasattr(r, "model_name")
    assert hasattr(r, "horizon")
    assert hasattr(r, "mae")
    assert hasattr(r, "rmse")
    assert hasattr(r, "mape")
    assert hasattr(r, "status")
    assert hasattr(r, "notes")
    assert hasattr(r, "variable_label")


def test_validation_result_none_metrics_allowed():
    r = _make_result(mae=None, rmse=None, mape=None, status="UNAVAILABLE")
    assert r.mae is None
    assert r.rmse is None
    assert r.mape is None


def test_validation_result_data_mode_is_datamode_enum():
    r = _make_result(data_mode=DataMode.PUBLIC_REAL)
    assert isinstance(r.data_mode, DataMode)
    assert r.data_mode == DataMode.PUBLIC_REAL


# ── Synthetic validation wrapper ──────────────────────────────────────────────

def test_get_synthetic_validation_ok_metrics():
    metrics = {"status": "OK", "MAE": 2.5, "RMSE": 3.1, "MAPE": 4.2}
    result = get_synthetic_validation(metrics, model_name="SARIMA", horizon=14)
    assert result.data_mode == DataMode.SYNTHETIC
    assert result.status == "SYNTHETIC"
    assert result.mae == 2.5
    assert result.rmse == 3.1
    assert result.mape == 4.2
    assert result.model_name == "SARIMA"
    assert result.horizon == 14


def test_get_synthetic_validation_insufficient_data():
    metrics = {
        "status": "INSUFFICIENT_DATA",
        "MAE": None,
        "RMSE": None,
        "MAPE": None,
        "minimum_required_observations": 45,
        "available_observations": 10,
    }
    result = get_synthetic_validation(metrics)
    assert result.data_mode == DataMode.SYNTHETIC
    assert result.status == "INSUFFICIENT_DATA"
    assert result.mae is None


def test_synthetic_and_real_results_have_different_data_mode():
    """Separation test: synthetic and real results must carry distinct data_mode values."""
    syn = get_synthetic_validation({"status": "OK", "MAE": 1.0, "RMSE": 1.2, "MAPE": 3.0})
    real = _make_result(data_mode=DataMode.PUBLIC_REAL, status="OK")
    assert syn.data_mode != real.data_mode
    assert syn.data_mode == DataMode.SYNTHETIC
    assert real.data_mode == DataMode.PUBLIC_REAL


# ── Real validation with fixture-injected DataFrame ───────────────────────────

def _make_fixture_df(n: int = 200) -> pd.DataFrame:
    """Generates a synthetic 'real' series with realistic wind speed values."""
    rng = np.random.default_rng(42)
    dates = pd.date_range(end="2026-09-10", periods=n, freq="D")
    values = 5.0 + 2.0 * np.sin(np.linspace(0, 4 * np.pi, n)) + rng.normal(0, 0.5, n)
    values = np.clip(values, 0.5, 25.0)
    return pd.DataFrame({"date": dates, "value": values})


def test_run_real_validation_with_fixture(tmp_path):
    """With a valid cached fixture, run_real_validation must return status OK."""
    fixture_df = _make_fixture_df(n=MIN_TRAIN_DAYS + TEST_DAYS + 10)
    cache_file = tmp_path / DEFAULT_CACHE_FILENAME
    fixture_df.to_csv(cache_file, index=False)

    with patch("backend.validation.CACHE_DIR", str(tmp_path)):
        result = run_real_validation(cache_filename=DEFAULT_CACHE_FILENAME, model_name="Naive")

    assert result.status == "OK"
    assert result.data_mode == DataMode.PUBLIC_REAL
    assert result.mae is not None and result.mae >= 0.0
    assert result.rmse is not None and result.rmse >= 0.0
    assert result.mape is not None and result.mape >= 0.0
    assert result.n_observations == len(fixture_df)
    assert result.horizon == TEST_DAYS


def test_run_real_validation_metrics_are_positive(tmp_path):
    """MAE, RMSE, MAPE must all be non-negative on a valid fixture."""
    fixture_df = _make_fixture_df(n=150)
    cache_file = tmp_path / DEFAULT_CACHE_FILENAME
    fixture_df.to_csv(cache_file, index=False)

    with patch("backend.validation.CACHE_DIR", str(tmp_path)):
        result = run_real_validation(model_name="Naive")

    if result.status == "OK":
        assert result.mae >= 0.0
        assert result.rmse >= result.mae - 1e-9  # RMSE >= MAE always
        assert result.mape >= 0.0


def test_run_real_validation_insufficient_data(tmp_path):
    """A series shorter than MIN_TRAIN_DAYS + TEST_DAYS must return INSUFFICIENT_DATA."""
    import requests

    fixture_df = _make_fixture_df(n=20)  # too short
    cache_file = tmp_path / DEFAULT_CACHE_FILENAME
    fixture_df.to_csv(cache_file, index=False)

    # Block network so the short cache is the only available data source
    with (
        patch("backend.validation.CACHE_DIR", str(tmp_path)),
        patch("requests.get", side_effect=requests.exceptions.ConnectionError("down")),
    ):
        result = run_real_validation(model_name="Naive")

    assert result.status == "INSUFFICIENT_DATA"
    assert result.mae is None
    assert result.rmse is None


# ── Offline fallback ──────────────────────────────────────────────────────────

def test_run_real_validation_offline_no_cache(tmp_path):
    """No cache + network failure must return UNAVAILABLE, not raise."""
    import requests

    def _raise(*args, **kwargs):
        raise requests.exceptions.ConnectionError("Network unreachable")

    with (
        patch("backend.validation.CACHE_DIR", str(tmp_path)),
        patch("requests.get", side_effect=_raise),
    ):
        result = run_real_validation()

    assert result.status == "UNAVAILABLE"
    assert result.mae is None
    assert "unavailable" in result.notes.lower()


def test_fetch_openmeteo_series_returns_none_on_failure(tmp_path):
    """fetch_openmeteo_series must return None when network is down and no cache exists."""
    import requests

    with (
        patch("backend.validation.CACHE_DIR", str(tmp_path)),
        patch("requests.get", side_effect=requests.exceptions.ConnectionError("down")),
    ):
        result = fetch_openmeteo_series(cache_filename=DEFAULT_CACHE_FILENAME)

    assert result is None


# ── Separation enforcement ────────────────────────────────────────────────────

def test_synthetic_validation_status_is_never_ok():
    """
    Synthetic ValidationResult.status must be "SYNTHETIC", not "OK",
    so callers cannot accidentally treat it as real-data validated.
    """
    metrics = {"status": "OK", "MAE": 1.0, "RMSE": 1.2, "MAPE": 3.0}
    result = get_synthetic_validation(metrics)
    assert result.status != "OK", (
        "Synthetic ValidationResult must use status='SYNTHETIC', never 'OK'"
    )


def test_real_validation_status_is_never_synthetic(tmp_path):
    """Real ValidationResult.status must never be 'SYNTHETIC'."""
    fixture_df = _make_fixture_df(n=MIN_TRAIN_DAYS + TEST_DAYS + 10)
    cache_file = tmp_path / DEFAULT_CACHE_FILENAME
    fixture_df.to_csv(cache_file, index=False)

    with patch("backend.validation.CACHE_DIR", str(tmp_path)):
        result = run_real_validation(model_name="Naive")

    assert result.status != "SYNTHETIC", (
        "Real ValidationResult must never carry status='SYNTHETIC'"
    )


# ── build_validation_chart_data ───────────────────────────────────────────────

def test_build_validation_chart_data_structure(tmp_path):
    """Returns dict with required keys when data is available."""
    fixture_df = _make_fixture_df(n=MIN_TRAIN_DAYS + TEST_DAYS + 20)
    cache_file = tmp_path / DEFAULT_CACHE_FILENAME
    fixture_df.to_csv(cache_file, index=False)

    with patch("backend.validation.CACHE_DIR", str(tmp_path)):
        chart = build_validation_chart_data(model_name="Naive", horizon=TEST_DAYS)

    assert chart is not None
    for key in ("dates_train", "values_train", "dates_test", "values_test",
                "dates_pred", "values_pred", "lower_ci", "upper_ci",
                "split_date", "result"):
        assert key in chart, f"Chart data missing key '{key}'"

    assert len(chart["dates_test"]) == TEST_DAYS
    assert len(chart["values_pred"]) == TEST_DAYS
    assert isinstance(chart["result"], ValidationResult)


def test_build_validation_chart_data_returns_none_without_data(tmp_path):
    """Returns None when no data is available."""
    import requests

    with (
        patch("backend.validation.CACHE_DIR", str(tmp_path)),
        patch("requests.get", side_effect=requests.exceptions.ConnectionError("down")),
    ):
        chart = build_validation_chart_data(model_name="Naive")

    assert chart is None
