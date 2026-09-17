"""
Batch E — Leakage-free generator tests (phase 26).

Three layers of assurance:

  STRUCTURAL — source inspection: the assignment expressions for bdi_raw,
    capesize_raw, panamax_raw, iron_raw, coal_raw, and avail_raw must not
    contain the string "freight_rate".  A reference there would mean the
    observed series is a direct function of the forecast target.

  STATISTICAL — on the generated CSVs: no series should be a near-identity
    of freight_rate.  Threshold: |Pearson r| < 0.97.  BDI / capesize / panamax
    are expected to be moderately correlated (~0.80) via shared demand/supply
    latents; iron_ore and coking_coal should be nearly uncorrelated (~0.10–0.20).

  DETERMINISM — two calls to generate_demo_dataset() with the same seed must
    produce byte-identical CSVs.
"""

import inspect
import os
import re
import tempfile

import numpy as np
import pandas as pd
import pytest

from data.generate_demo_data import generate_demo_dataset


# ── Helper: extract an assignment block from function source ──────────────────

def _get_assignment_block(source: str, var_name: str) -> str:
    """
    Returns the text of the assignment `{var_name} = (...)` in *source*,
    following matching parentheses to capture multi-line expressions.
    Returns empty string if not found.
    """
    lines = source.split("\n")
    result = []
    in_block = False
    depth = 0

    for line in lines:
        stripped = line.strip()
        # Detect start: `var_name =` or `var_name=` at the beginning of the stripped line
        if re.match(rf"^{re.escape(var_name)}\s*=\s*", stripped):
            in_block = True
            depth = stripped.count("(") - stripped.count(")")
            result.append(stripped)
            if depth <= 0:
                break
            continue

        if in_block:
            result.append(stripped)
            depth += stripped.count("(") - stripped.count(")")
            if depth <= 0:
                break

    return "\n".join(result)


# ── STRUCTURAL TESTS ──────────────────────────────────────────────────────────

_SRC = inspect.getsource(generate_demo_dataset)

# Mapping: raw variable name → final series name (for error messages)
_SERIES_VARS = {
    "bdi_raw": "bdi",
    "capesize_raw": "capesize_index",
    "panamax_raw": "panamax_index",
    "iron_raw": "iron_ore_price",
    "coal_raw": "coking_coal_price",
    "avail_raw": "vessel_availability_count",
}


@pytest.mark.parametrize("raw_var,series_name", list(_SERIES_VARS.items()))
def test_structural_no_freight_leakage(raw_var, series_name):
    """Assignment block for {raw_var} must not reference 'freight_rate'."""
    block = _get_assignment_block(_SRC, raw_var)
    assert block, f"Could not find assignment for '{raw_var}' in generator source"
    assert "freight_rate" not in block, (
        f"'{series_name}' ({raw_var}) references 'freight_rate' — synthetic leakage detected.\n"
        f"Block:\n{block[:400]}"
    )


def test_structural_freight_rate_defined_once_in_observed_section():
    """
    After the LATENT FACTORS section, 'freight_rate' should only appear in
    its own assignment (fr_raw / freight_rate =) and in non-assignment contexts
    (sanity print, CSV write, comments).  It must NOT appear in the RHS of any
    other series assignment.
    """
    # Extract the OBSERVED SERIES section
    obs_marker = "# ── OBSERVED SERIES"
    sanity_marker = "# ── SANITY CHECK"
    obs_start = _SRC.find(obs_marker)
    sanity_start = _SRC.find(sanity_marker)
    assert obs_start != -1, "OBSERVED SERIES section marker not found"
    assert sanity_start != -1, "SANITY CHECK section marker not found"

    observed_section = _SRC[obs_start:sanity_start]

    # Split into lines; skip lines that belong to fr_raw / freight_rate assignment
    lines = observed_section.split("\n")
    violations = []
    in_freight_def = False
    fr_depth = 0

    for line in lines:
        stripped = line.strip()
        # Track the fr_raw / freight_rate assignment block
        if re.match(r"^fr_raw\s*=", stripped) or re.match(r"^freight_rate\s*=", stripped):
            in_freight_def = True
            fr_depth = stripped.count("(") - stripped.count(")")
            continue
        if in_freight_def:
            fr_depth += stripped.count("(") - stripped.count(")")
            if fr_depth <= 0:
                in_freight_def = False
            continue

        # Any other line that assigns something and references freight_rate is a violation
        if "=" in stripped and "freight_rate" in stripped and not stripped.startswith("#"):
            violations.append(stripped)

    assert not violations, (
        "The following lines in the OBSERVED SERIES section reference 'freight_rate' "
        "outside its own definition block:\n" + "\n".join(violations)
    )


# ── STATISTICAL TESTS ─────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def generated_data():
    """Load the generated CSVs (already on disk from the last generator run)."""
    freight_df = pd.read_csv("data/freight_rates.csv")
    commodity_df = pd.read_csv("data/commodity_prices.csv")
    return freight_df, commodity_df


LEAKAGE_THRESHOLD = 0.97  # correlation above this is near-identity: suspect leakage


@pytest.mark.parametrize("col,expected_r_range", [
    ("bdi",            (0.50, LEAKAGE_THRESHOLD)),   # shared latents → moderate-high
    ("capesize_index", (0.50, LEAKAGE_THRESHOLD)),
    ("panamax_index",  (0.50, LEAKAGE_THRESHOLD)),
])
def test_bdi_indices_not_near_identity_of_freight(generated_data, col, expected_r_range):
    """
    BDI and vessel-class indices must be moderately correlated with freight_rate
    (shared demand/supply latents) but strictly below the leakage threshold.
    """
    freight_df, _ = generated_data
    r = float(np.corrcoef(freight_df["freight_rate"], freight_df[col])[0, 1])
    lo, hi = expected_r_range
    print(f"\n  Pearson r(freight_rate, {col}) = {r:.4f}  [expected {lo:.2f}–{hi:.2f}]")
    assert abs(r) < hi, (
        f"r(freight_rate, {col}) = {r:.4f} ≥ {hi} — near-identity suggests leakage. "
        "BDI/indices should be moderately correlated, not a scaled copy."
    )
    assert abs(r) >= lo, (
        f"r(freight_rate, {col}) = {r:.4f} < {lo} — unexpectedly low; shared latents "
        "should produce moderate positive correlation."
    )


@pytest.mark.parametrize("col,max_abs_r", [
    ("iron_ore_price",    0.40),   # independent latents; only noise correlation expected
    ("coking_coal_price", 0.40),
])
def test_commodity_prices_not_correlated_with_freight(generated_data, col, max_abs_r):
    """
    Iron ore and coking coal must have LOW correlation with freight_rate.
    They use commodity/macro latents; freight uses demand/supply/bunker/port latents.
    """
    freight_df, commodity_df = generated_data
    merged = freight_df[["date", "freight_rate"]].merge(commodity_df[["date", col]], on="date")
    r = float(np.corrcoef(merged["freight_rate"], merged[col])[0, 1])
    print(f"\n  Pearson r(freight_rate, {col}) = {r:.4f}  [expected |r| < {max_abs_r}]")
    assert abs(r) < max_abs_r, (
        f"r(freight_rate, {col}) = {r:.4f} ≥ {max_abs_r} — "
        f"commodity price appears correlated with freight target; check for leakage."
    )


def test_vessel_availability_not_correlated_with_freight(generated_data):
    """
    Vessel availability must NOT be tightly correlated with freight_rate.
    Old generator: avail depended directly on freight_rate.
    New generator: avail uses supply + demand latents only.
    """
    freight_df, _ = generated_data
    vessel_df = pd.read_csv("data/vessel_availability.csv")
    merged = freight_df[["date", "freight_rate"]].merge(vessel_df, on="date")
    r = float(np.corrcoef(merged["freight_rate"], merged["vessel_availability_count"])[0, 1])
    print(f"\n  Pearson r(freight_rate, vessel_availability_count) = {r:.4f}")
    # The old formula gave r ≈ -0.80 (direct linear dependence via -0.5*freight_rate)
    # The new formula should give a moderate or weak correlation via shared demand latent
    assert abs(r) < 0.90, (
        f"r(freight_rate, vessel_availability_count) = {r:.4f} ≥ 0.90 — "
        "vessel availability still appears tightly coupled to freight_rate."
    )


def test_all_series_within_sane_ranges():
    """Generated series must stay within documented UI-safe clip ranges."""
    freight_df  = pd.read_csv("data/freight_rates.csv")
    commodity   = pd.read_csv("data/commodity_prices.csv")
    congestion  = pd.read_csv("data/port_congestion.csv")
    vessels     = pd.read_csv("data/vessel_availability.csv")
    events      = pd.read_csv("data/events.csv")

    assert freight_df["freight_rate"].between(12.0, 48.0).all(),   "freight_rate out of range"
    assert freight_df["bdi"].between(200.0, 4000.0).all(),          "bdi out of range"
    assert freight_df["capesize_index"].between(400.0, 8000.0).all(),"capesize out of range"
    assert freight_df["panamax_index"].between(300.0, 3500.0).all(), "panamax out of range"
    assert commodity["iron_ore_price"].between(50.0, 250.0).all(),  "iron_ore out of range"
    assert commodity["coking_coal_price"].between(100.0, 500.0).all(),"coking_coal out of range"
    assert congestion["port_congestion_score"].between(10.0, 100.0).all(),"congestion out of range"
    assert congestion["avg_waiting_hours"].between(5.0, 100.0).all(), "waiting hours out of range"
    assert vessels["vessel_availability_count"].between(5, 65).all(), "vessel avail out of range"
    assert events["weather_risk_score"].between(0.0, 10.0).all(),    "weather risk out of range"
    assert events["event_risk_score"].between(0.0, 10.0).all(),      "event risk out of range"


# ── DETERMINISM TEST ──────────────────────────────────────────────────────────

def test_generator_is_deterministic(tmp_path):
    """Two generator runs with the same seed produce identical freight_rates.csv."""
    import shutil, sys

    orig_dir = os.getcwd()
    # Run 1: generate into a temp location by patching the cwd
    run1_dir = tmp_path / "run1"
    run2_dir = tmp_path / "run2"
    run1_dir.mkdir()
    run2_dir.mkdir()

    def _run(dest):
        # Copy the project data dir structure, then generate
        os.chdir(dest)
        os.makedirs("data", exist_ok=True)
        # Import fresh to avoid cached state
        import importlib
        import data.generate_demo_data as _mod
        importlib.reload(_mod)
        _mod.generate_demo_dataset()
        df = pd.read_csv("data/freight_rates.csv")
        os.chdir(orig_dir)
        return df

    df1 = _run(run1_dir)
    df2 = _run(run2_dir)

    pd.testing.assert_frame_equal(df1, df2, check_exact=True,
                                  obj="freight_rates.csv must be byte-identical across two runs")
