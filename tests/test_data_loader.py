"""
Unit tests for data loading, cleaning, and schema validation.
"""

import pytest
import pandas as pd
import numpy as np
from backend.data_loader import load_raw_datasets, clean_and_validate_dataframe, validate_user_csv, REQUIRED_COLUMNS


def test_load_raw_datasets():
    df = load_raw_datasets()
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 500
    for col in REQUIRED_COLUMNS:
        assert col in df.columns, f"Missing required column: {col}"
    assert df["date"].is_monotonic_increasing


def test_clean_and_validate_dataframe():
    sample_df = pd.DataFrame({
        "date": ["2024-01-01", "2024-01-01", "2024-01-02"],
        "freight_rate": [20.0, 20.0, np.nan],
        "bdi": [1500, 1500, 1510]
    })
    cleaned = clean_and_validate_dataframe(sample_df)
    assert len(cleaned) == 2  # duplicate date removed
    assert cleaned["freight_rate"].isnull().sum() == 0  # nan filled


def test_validate_user_csv():
    valid_df = pd.DataFrame({col: [1.0] for col in REQUIRED_COLUMNS})
    valid_df["date"] = ["2024-01-01"]
    
    is_valid, missing, clean = validate_user_csv(valid_df)
    assert is_valid is True
    assert len(missing) == 0

    invalid_df = pd.DataFrame({"date": ["2024-01-01"], "freight_rate": [20.0]})
    is_valid_inv, missing_inv, clean_inv = validate_user_csv(invalid_df)
    assert is_valid_inv is False
    assert len(missing_inv) > 0
    assert "bdi" in missing_inv
