"""
FreightIQ Feature Engineering Module

Generates time, lag, rolling statistical, market momentum, correlation,
congestion trend, vessel availability change, and risk indicator features.
"""

import numpy as np
import pandas as pd


def generate_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Takes cleaned merged DataFrame and computes engineering features.
    """
    data = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(data["date"]):
        data["date"] = pd.to_datetime(data["date"])

    data = data.sort_values("date").reset_index(drop=True)

    # 1. Time Features
    data["day"] = data["date"].dt.day
    data["week"] = data["date"].dt.isocalendar().week.astype(int)
    data["month"] = data["date"].dt.month
    data["quarter"] = data["date"].dt.quarter
    data["year"] = data["date"].dt.year
    data["month_sin"] = np.sin(2 * np.pi * data["month"] / 12.0)
    data["month_cos"] = np.cos(2 * np.pi * data["month"] / 12.0)

    # 2. Lag Features for Freight Rate
    if "freight_rate" in data.columns:
        data["freight_rate_lag_1"] = data["freight_rate"].shift(1)
        data["freight_rate_lag_7"] = data["freight_rate"].shift(7)
        data["freight_rate_lag_14"] = data["freight_rate"].shift(14)
        data["freight_rate_lag_30"] = data["freight_rate"].shift(30)

        # 3. Rolling Features for Freight Rate
        data["freight_ma_7"] = data["freight_rate"].rolling(window=7, min_periods=1).mean()
        data["freight_ma_14"] = data["freight_rate"].rolling(window=14, min_periods=1).mean()
        data["freight_ma_30"] = data["freight_rate"].rolling(window=30, min_periods=1).mean()
        data["freight_volatility_14"] = data["freight_rate"].rolling(window=14, min_periods=1).std().fillna(0.0)

        # Freight Momentum
        data["freight_momentum_7"] = data["freight_rate"] - data["freight_rate_lag_7"]

    # 4. Market & Commodity Features
    if "iron_ore_price" in data.columns:
        data["iron_ore_return_7"] = data["iron_ore_price"].pct_change(7).fillna(0.0)
    if "coking_coal_price" in data.columns:
        data["coking_coal_return_7"] = data["coking_coal_price"].pct_change(7).fillna(0.0)

    if "freight_rate" in data.columns and "iron_ore_price" in data.columns:
        data["freight_iron_ore_corr_30"] = (
            data["freight_rate"]
            .rolling(window=30, min_periods=7)
            .corr(data["iron_ore_price"])
            .fillna(0.0)
        )

    # 5. Congestion Features
    if "port_congestion_score" in data.columns:
        data["congestion_trend_7"] = data["port_congestion_score"] - data["port_congestion_score"].shift(7)
        data["congestion_ma_7"] = data["port_congestion_score"].rolling(window=7, min_periods=1).mean()

    # 6. Vessel Availability Features
    if "vessel_availability_count" in data.columns:
        data["vessel_avail_change_7"] = data["vessel_availability_count"] - data["vessel_availability_count"].shift(7)
        data["vessel_avail_ma_7"] = data["vessel_availability_count"].rolling(window=7, min_periods=1).mean()

    # Fill any NaNs from shifting with ffill and 0.0 (no backward filling to prevent future data leakage)
    feature_cols = [c for c in data.columns if c != "date"]
    data[feature_cols] = data[feature_cols].ffill().fillna(0.0)

    return data
