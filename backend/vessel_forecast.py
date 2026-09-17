"""
FreightIQ Vessel Availability Forecast Module

Provides lightweight time-series forecast for regional vessel availability count,
trend indicator (Increasing / Stable / Decreasing), and confidence score.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any


def forecast_vessel_availability(df: pd.DataFrame, horizon: int = 14) -> Dict[str, Any]:
    """
    Lightweight vessel availability forecast using rolling average and trend projection.
    """
    if "vessel_availability_count" not in df.columns:
        # Fallback default
        return {
            "expected_availability_count": 25,
            "trend": "Stable",
            "confidence_score": "Moderate",
            "forecast_df": pd.DataFrame()
        }

    counts = df["vessel_availability_count"].values
    dates = df["date"]
    
    recent_7_ma = float(np.mean(counts[-7:]))
    older_7_ma = float(np.mean(counts[-14:-7])) if len(counts) >= 14 else recent_7_ma

    delta = recent_7_ma - older_7_ma
    if delta > 1.5:
        trend = "Increasing"
    elif delta < -1.5:
        trend = "Decreasing"
    else:
        trend = "Stable"

    # Future dates
    future_dates = pd.date_range(start=dates.iloc[-1] + pd.Timedelta(days=1), periods=horizon, freq="D")
    
    # Project with slight mean reversion to recent_7_ma
    projected = np.zeros(horizon)
    for h in range(horizon):
        projected[h] = max(5, int(round(recent_7_ma + (delta * 0.1 * h))))

    fc_df = pd.DataFrame({
        "date": future_dates,
        "expected_vessel_count": projected.astype(int),
        "trend": trend
    })

    # Simple confidence indicator based on historical variance
    vol = float(np.std(counts[-14:])) if len(counts) >= 14 else 2.0
    if vol < 2.0:
        confidence = "High"
    elif vol < 5.0:
        confidence = "Moderate"
    else:
        confidence = "Low"

    return {
        "expected_availability_count": int(round(projected[0])),
        "avg_horizon_availability": int(round(np.mean(projected))),
        "trend": trend,
        "confidence_score": confidence,
        "forecast_df": fc_df
    }
