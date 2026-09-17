"""
FreightIQ Real-Data Validation Module

Fetches publicly licensed daily weather observations from Open-Meteo
(no API key, CC BY 4.0), caches them locally, and runs held-out train/test
evaluation using the existing SARIMA/naive pipeline.

Hard rules:
  - OFFLINE-SAFE: if fetch fails and no cache exists, return UNAVAILABLE
  - SEPARATION: real and synthetic ValidationResults are never combined
  - Real metrics are computed on a held-out test split of actual observed data
    — never hardcoded

Series choice: max daily wind speed at Paradip port (lat 20.26 N, lon 86.67 E).
This is a relevant proxy for port operations and route risk scoring.
"""

import os
import warnings
from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd

from backend.forecasting import calculate_metrics

# ── Constants ──────────────────────────────────────────────────────────────────

OPEN_METEO_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

DEFAULT_LAT = 20.26          # Paradip, Odisha (East Coast India)
DEFAULT_LON = 86.67
DEFAULT_VARIABLE = "windspeed_10m_max"
DEFAULT_VARIABLE_LABEL = "Max Daily Wind Speed (m/s) — Paradip Port"

_THIS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(_THIS_DIR, "data", "validation")
DEFAULT_CACHE_FILENAME = "openmeteo_paradip_wind.csv"

TEST_DAYS = 30          # held-out test window
MIN_TRAIN_DAYS = 60     # minimum training observations required


# ── Data model ─────────────────────────────────────────────────────────────────

class DataMode(Enum):
    SYNTHETIC = "SYNTHETIC"
    PUBLIC_REAL = "PUBLIC_REAL"
    CONNECTED_REAL = "CONNECTED_REAL"
    MANUAL_REAL = "MANUAL_REAL"


@dataclass
class ValidationResult:
    source_name: str
    source_type: str
    data_mode: DataMode
    start_date: Optional[str]      # ISO date string or None
    end_date: Optional[str]
    n_observations: Optional[int]
    model_name: str
    horizon: int                   # test window in days
    mae: Optional[float]
    rmse: Optional[float]
    mape: Optional[float]
    status: str                    # "OK" | "INSUFFICIENT_DATA" | "UNAVAILABLE" | "SYNTHETIC"
    notes: str = ""
    variable_label: str = ""
    signal_unit: str = "m/s"
    source_unit: str = "m/s"
    requested_model: str = "SARIMA"


# ── Cache helpers ──────────────────────────────────────────────────────────────

def _cache_path(filename: str = DEFAULT_CACHE_FILENAME) -> str:
    return os.path.join(CACHE_DIR, filename)


def _ensure_cache_dir() -> None:
    os.makedirs(CACHE_DIR, exist_ok=True)


# ── Open-Meteo fetch ───────────────────────────────────────────────────────────

def fetch_openmeteo_series(
    lat: float = DEFAULT_LAT,
    lon: float = DEFAULT_LON,
    variable: str = DEFAULT_VARIABLE,
    cache_filename: str = DEFAULT_CACHE_FILENAME,
    force_refresh: bool = False,
    lookback_days: int = 730,
) -> Optional[pd.DataFrame]:
    """
    Returns a DataFrame with columns [date (Timestamp), value (float)],
    or None if data is unavailable (network down, no cache).

    Values are guaranteed to be in m/s. If cached data was stored in km/h
    (mean > 10 m/s for wind), it is automatically converted to m/s (val / 3.6).
    """
    _ensure_cache_dir()
    cache_file = _cache_path(cache_filename)

    def _clean_and_convert_units(df_in: pd.DataFrame) -> pd.DataFrame:
        df_out = df_in.copy()
        # Open-Meteo wind speed in km/h typically has mean > 10. In m/s, mean is ~3-5 m/s.
        if "value" in df_out.columns and len(df_out) > 0 and df_out["value"].mean() > 10.0:
            df_out["value"] = df_out["value"] / 3.6
        return df_out

    if not force_refresh and os.path.exists(cache_file):
        try:
            df = pd.read_csv(cache_file, parse_dates=["date"])
            if len(df) >= MIN_TRAIN_DAYS + TEST_DAYS:
                return _clean_and_convert_units(df)
        except Exception:
            pass  # corrupt cache → try network

    # Attempt live fetch requesting wind_speed_unit="ms" explicitly
    end_dt = date.today() - timedelta(days=5)  # archive lags ~5 days
    start_dt = end_dt - timedelta(days=lookback_days)

    try:
        import requests
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": start_dt.isoformat(),
            "end_date": end_dt.isoformat(),
            "daily": variable,
            "wind_speed_unit": "ms",
            "timezone": "Asia/Kolkata",
        }
        resp = requests.get(OPEN_METEO_ARCHIVE_URL, params=params, timeout=12)
        resp.raise_for_status()
        payload = resp.json()

        times = payload["daily"]["time"]
        vals = payload["daily"][variable]
        df = pd.DataFrame({"date": pd.to_datetime(times), "value": vals})
        df = df.dropna().reset_index(drop=True)

        df.to_csv(cache_file, index=False)
        return _clean_and_convert_units(df)

    except Exception:
        # Network failure or API error → use existing cache (even if short)
        if os.path.exists(cache_file):
            try:
                cached_df = pd.read_csv(cache_file, parse_dates=["date"])
                return _clean_and_convert_units(cached_df)
            except Exception:
                return None
        return None


# ── Real validation runner ─────────────────────────────────────────────────────

def run_real_validation(
    cache_filename: str = DEFAULT_CACHE_FILENAME,
    model_name: str = "SARIMA",
    horizon: int = TEST_DAYS,
    force_refresh: bool = False,
) -> ValidationResult:
    """
    Evaluates `model_name` on a held-out test split of real observed data.

    Train: all observations except last `horizon` days.
    Test:  last `horizon` days.
    Metrics are computed on real test values — never simulated, never hardcoded.
    """
    df = fetch_openmeteo_series(
        cache_filename=cache_filename,
        force_refresh=force_refresh,
    )

    _meta: Dict[str, Any] = dict(
        source_name="Open-Meteo Archive API",
        source_type="Public daily weather observations — CC BY 4.0",
        data_mode=DataMode.PUBLIC_REAL,
        horizon=horizon,
        variable_label=DEFAULT_VARIABLE_LABEL,
        signal_unit="m/s",
        source_unit="m/s",
        requested_model=model_name,
    )

    if df is None or len(df) == 0:
        return ValidationResult(
            **_meta,
            model_name=model_name,
            start_date=None,
            end_date=None,
            n_observations=None,
            mae=None,
            rmse=None,
            mape=None,
            status="UNAVAILABLE",
            notes=(
                "Real-data validation unavailable — "
                "no cached series and network unreachable."
            ),
        )

    series = df["value"].values.astype(float)
    n = len(series)
    start_str = str(df["date"].iloc[0].date())
    end_str = str(df["date"].iloc[-1].date())

    if n < horizon + MIN_TRAIN_DAYS:
        return ValidationResult(
            **_meta,
            model_name=model_name,
            start_date=start_str,
            end_date=end_str,
            n_observations=n,
            mae=None,
            rmse=None,
            mape=None,
            status="INSUFFICIENT_DATA",
            notes=(
                f"Require {horizon + MIN_TRAIN_DAYS} observations for a valid hold-out "
                f"split; have {n}."
            ),
        )

    train = series[:-horizon]
    test = series[-horizon:]

    y_pred, actual_model_used = _predict(model_name, train, horizon)
    metrics = calculate_metrics(test, y_pred)

    return ValidationResult(
        **_meta,
        model_name=actual_model_used,
        start_date=start_str,
        end_date=end_str,
        n_observations=n,
        mae=metrics.get("MAE"),
        rmse=metrics.get("RMSE"),
        mape=metrics.get("MAPE"),
        status=metrics.get("status", "OK"),
        notes=(
            f"Train: {len(train)} obs | Test (held-out): {horizon} obs. "
            f"Series: {DEFAULT_VARIABLE_LABEL} ({actual_model_used})."
        ),
    )


def _predict(model_name: str, train: np.ndarray, horizon: int) -> Tuple[np.ndarray, str]:
    """Runs model on `train`, returns `(horizon_step_forecast, actual_model_name)`."""
    if model_name == "SARIMA":
        try:
            from statsmodels.tsa.statespace.sarimax import SARIMAX
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                m = SARIMAX(
                    train,
                    order=(1, 1, 1),
                    seasonal_order=(1, 0, 0, 7),
                    enforce_stationarity=False,
                    enforce_invertibility=False,
                )
                r = m.fit(disp=False)
                preds = r.forecast(steps=horizon)
                return np.asarray(preds, dtype=float), "SARIMA"
        except Exception:
            pass  # fall through to naive fallback

    # Naive fallback: last value + damped trend
    last = float(train[-1])
    slope = float((train[-1] - train[-14]) / 14.0) if len(train) >= 14 else 0.0
    preds = np.array([last + slope * (h + 1) * 0.5 for h in range(horizon)], dtype=float)
    actual_name = "Naive (SARIMA Fallback)" if model_name == "SARIMA" else "Naive Baseline"
    return preds, actual_name


# ── Synthetic validation wrapper ───────────────────────────────────────────────

def get_synthetic_validation(
    metrics: Dict[str, Any],
    model_name: str = "SARIMA",
    horizon: int = 14,
    n_observations: int = 365,
) -> ValidationResult:
    """
    Wraps existing synthetic-series forecast metrics as a ValidationResult.
    status is "SYNTHETIC" (not "OK") to make the data-mode explicit.
    Never combined with a PUBLIC_REAL ValidationResult.
    """
    ok = metrics.get("status") == "OK"
    return ValidationResult(
        source_name="FreightIQ Synthetic Demo Series",
        source_type="Simulated freight rate time series — not real market data",
        data_mode=DataMode.SYNTHETIC,
        start_date=None,
        end_date=None,
        n_observations=n_observations,
        model_name=model_name,
        horizon=horizon,
        mae=metrics.get("MAE") if ok else None,
        rmse=metrics.get("RMSE") if ok else None,
        mape=metrics.get("MAPE") if ok else None,
        status="SYNTHETIC" if ok else metrics.get("status", "UNAVAILABLE"),
        notes="Metrics on synthetic demo series. Not a real-market accuracy claim.",
        variable_label="Spot freight rate (USD/tonne)",
    )


# ── Real validation chart data ─────────────────────────────────────────────────

def build_validation_chart_data(
    cache_filename: str = DEFAULT_CACHE_FILENAME,
    model_name: str = "SARIMA",
    horizon: int = TEST_DAYS,
) -> Optional[Dict[str, Any]]:
    """
    Returns dict suitable for Plotly chart construction, or None if unavailable.

    Keys:
      dates_train, values_train  — observed training series
      dates_test, values_test    — observed test series (held-out)
      dates_pred, values_pred    — model predictions on test window
      lower_ci, upper_ci         — 1-sigma interval around predictions
      split_date                 — date of train/test boundary
      result                     — ValidationResult with computed metrics
    """
    df = fetch_openmeteo_series(cache_filename=cache_filename)
    if df is None or len(df) < MIN_TRAIN_DAYS + horizon:
        return None

    series = df["value"].values.astype(float)
    dates = df["date"].values

    train_vals = series[:-horizon]
    test_vals = series[-horizon:]
    train_dates = dates[:-horizon]
    test_dates = dates[-horizon:]

    y_pred, _ = _predict(model_name, train_vals, horizon)

    # Naive 1-sigma from recent train std
    sigma = float(np.std(train_vals[-60:])) if len(train_vals) >= 60 else float(np.std(train_vals))
    lower_ci = y_pred - sigma
    upper_ci = y_pred + sigma

    result = run_real_validation(
        cache_filename=cache_filename,
        model_name=model_name,
        horizon=horizon,
    )

    return {
        "dates_train": pd.to_datetime(train_dates),
        "values_train": train_vals,
        "dates_test": pd.to_datetime(test_dates),
        "values_test": test_vals,
        "dates_pred": pd.to_datetime(test_dates),
        "values_pred": y_pred,
        "lower_ci": lower_ci,
        "upper_ci": upper_ci,
        "split_date": pd.to_datetime(test_dates[0]),
        "result": result,
    }
