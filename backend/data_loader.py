"""
FreightIQ Data Loader Module

Loads, validates, cleans, and merges multi-source freight, commodity,
congestion, vessel availability, and risk event CSV datasets.
Supports user custom CSV uploads with schema validation.
"""

import os
import pandas as pd
import numpy as np
from typing import Tuple, List, Optional, Union

REQUIRED_COLUMNS = [
    "date",
    "freight_rate",
    "bdi",
    "capesize_index",
    "panamax_index",
    "iron_ore_price",
    "coking_coal_price",
    "port_congestion_score",
    "avg_waiting_hours",
    "vessel_availability_count",
    "weather_risk_score",
    "event_risk_score"
]

DEFAULT_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def load_raw_datasets(data_dir: str = DEFAULT_DATA_DIR) -> pd.DataFrame:
    """
    Loads all default CSV datasets from data_dir and merges them on 'date'.
    """
    files = {
        "freight": "freight_rates.csv",
        "commodity": "commodity_prices.csv",
        "congestion": "port_congestion.csv",
        "vessels": "vessel_availability.csv",
        "events": "events.csv"
    }

    dfs = []
    for key, filename in files.items():
        filepath = os.path.join(data_dir, filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Required data file missing: {filepath}")
        
        df = pd.read_csv(filepath)
        if "date" not in df.columns:
            raise ValueError(f"CSV {filename} does not contain 'date' column.")
        
        df["date"] = pd.to_datetime(df["date"])
        dfs.append(df)

    # Merge sequentially on date
    merged_df = dfs[0]
    for df in dfs[1:]:
        merged_df = pd.merge(merged_df, df, on="date", how="outer")

    return clean_and_validate_dataframe(merged_df)


def clean_and_validate_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans, deduplicates, handles missing values, and validates modeling dataframe.
    """
    df = df.copy()

    # Ensure date column is datetime
    if not pd.api.types.is_datetime64_any_dtype(df["date"]):
        df["date"] = pd.to_datetime(df["date"])

    # Remove duplicate dates (keep first)
    df = df.drop_duplicates(subset=["date"], keep="first")

    # Sort chronologically
    df = df.sort_values("date").reset_index(drop=True)

    # Forward fill then backward fill missing numeric values
    numeric_cols = [c for c in df.columns if c != "date"]
    df[numeric_cols] = df[numeric_cols].ffill().bfill()

    # If any nulls remain, fill with median or 0
    df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median()).fillna(0.0)

    return df


def validate_user_csv(df: pd.DataFrame) -> Tuple[bool, List[str], pd.DataFrame]:
    """
    Validates user uploaded CSV against expected columns.
    Returns (is_valid, missing_columns, cleaned_dataframe)
    """
    if "date" not in df.columns:
        return False, ["date"], df

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]

    # Clean the df regardless
    cleaned_df = df.copy()
    cleaned_df["date"] = pd.to_datetime(cleaned_df["date"])
    cleaned_df = cleaned_df.drop_duplicates(subset=["date"]).sort_values("date").reset_index(drop=True)

    # Fill any missing required numeric columns with reasonable defaults or 0s
    for col in missing:
        if col in ["freight_rate", "iron_ore_price", "coking_coal_price"]:
            cleaned_df[col] = 20.0 if "rate" in col else 100.0
        elif col in ["bdi", "capesize_index", "panamax_index"]:
            cleaned_df[col] = 1500.0
        else:
            cleaned_df[col] = 0.0

    numeric_cols = [c for c in cleaned_df.columns if c != "date"]
    cleaned_df[numeric_cols] = cleaned_df[numeric_cols].ffill().bfill().fillna(0.0)

    is_valid = len(missing) == 0
    return is_valid, missing, cleaned_df
