"""
Tests for the decision-model parameter registry (config/decision_model.yaml + loader).
Verifies: provenance fields present, sensitivity bounds valid, values match baseline,
and that the optimizer reads from config rather than hardcoding.
"""

import pytest
import inspect
import importlib
import backend.optimizer as opt_module
import backend.decision_twin as dt_module
from backend.config_model import (
    _PARAMS,
    get_decision_params_registry,
    DEMURRAGE_EXPOSURE_FACTOR,
    CONGESTION_COST_MULTIPLIER,
    VESSEL_AVAILABILITY_MIN_THRESHOLD,
    RISK_FACTOR_LOW,
    RISK_FACTOR_MEDIUM,
    RISK_FACTOR_HIGH,
    WEATHER_RISK_PENALTY_PER_POINT,
    EVENT_RISK_PENALTY_PER_POINT,
    AVAILABILITY_SHORTAGE_PENALTY_PER_VESSEL,
    FREIGHT_TREND_THRESHOLD,
    CONGESTION_TO_WAITING_HOURS_FACTOR,
)

REQUIRED_FIELDS = {"value", "unit", "classification", "source", "note", "sensitivity_range", "editable"}
VALID_CLASSIFICATIONS = {
    "OBSERVED",
    "DERIVED",
    "LITERATURE_INFORMED",
    "CONFIGURED_ASSUMPTION",
    "DEMO_ONLY_ASSUMPTION",
}


# ── Provenance completeness ───────────────────────────────────────────────────

def test_every_parameter_has_required_fields():
    for name, meta in _PARAMS.items():
        missing = REQUIRED_FIELDS - set(meta.keys())
        assert not missing, f"Parameter '{name}' is missing fields: {missing}"


def test_every_classification_is_valid():
    for name, meta in _PARAMS.items():
        cls = meta.get("classification", "")
        assert cls in VALID_CLASSIFICATIONS, (
            f"Parameter '{name}' has unknown classification '{cls}'"
        )


def test_every_sensitivity_range_has_min_max():
    for name, meta in _PARAMS.items():
        sr = meta.get("sensitivity_range", {})
        assert "min" in sr and "max" in sr, (
            f"Parameter '{name}' sensitivity_range missing min/max"
        )


def test_sensitivity_range_bounds_contain_value():
    for name, meta in _PARAMS.items():
        sr = meta["sensitivity_range"]
        v = meta["value"]
        lo, hi = sr["min"], sr["max"]
        assert lo <= v <= hi, (
            f"Parameter '{name}' value {v} is outside sensitivity_range [{lo}, {hi}]"
        )


# ── Named constant values match YAML ─────────────────────────────────────────

def test_named_constants_match_yaml():
    assert DEMURRAGE_EXPOSURE_FACTOR    == _PARAMS["demurrage_exposure_factor"]["value"]
    assert CONGESTION_COST_MULTIPLIER   == _PARAMS["congestion_cost_multiplier"]["value"]
    assert VESSEL_AVAILABILITY_MIN_THRESHOLD == int(_PARAMS["vessel_availability_min_threshold"]["value"])
    assert RISK_FACTOR_LOW              == _PARAMS["risk_factor_low_tolerance"]["value"]
    assert RISK_FACTOR_MEDIUM           == _PARAMS["risk_factor_medium_tolerance"]["value"]
    assert RISK_FACTOR_HIGH             == _PARAMS["risk_factor_high_tolerance"]["value"]
    assert WEATHER_RISK_PENALTY_PER_POINT == _PARAMS["weather_risk_penalty_per_point"]["value"]
    assert EVENT_RISK_PENALTY_PER_POINT   == _PARAMS["event_risk_penalty_per_point"]["value"]
    assert FREIGHT_TREND_THRESHOLD        == _PARAMS["freight_trend_detection_threshold"]["value"]
    assert CONGESTION_TO_WAITING_HOURS_FACTOR == _PARAMS["congestion_to_waiting_hours_factor"]["value"]


# ── Baseline regression: values reproduce the pre-refactor numbers ─────────────

def test_baseline_constant_values():
    assert DEMURRAGE_EXPOSURE_FACTOR == 0.15
    assert CONGESTION_COST_MULTIPLIER == 0.5
    assert VESSEL_AVAILABILITY_MIN_THRESHOLD == 8
    assert RISK_FACTOR_LOW == 1.5
    assert RISK_FACTOR_MEDIUM == 1.0
    assert RISK_FACTOR_HIGH == 0.5
    assert WEATHER_RISK_PENALTY_PER_POINT == 1200.0
    assert EVENT_RISK_PENALTY_PER_POINT == 1800.0
    assert AVAILABILITY_SHORTAGE_PENALTY_PER_VESSEL == 2500.0
    assert FREIGHT_TREND_THRESHOLD == 0.5
    assert CONGESTION_TO_WAITING_HOURS_FACTOR == 0.55


# ── Optimizer reads constants from config_model, not inline ──────────────────

def test_optimizer_uses_config_demurrage_factor():
    src = inspect.getsource(opt_module.evaluate_charter_candidate)
    assert "DEMURRAGE_EXPOSURE_FACTOR" in src, (
        "evaluate_charter_candidate must reference DEMURRAGE_EXPOSURE_FACTOR from config_model"
    )
    assert "* 0.15" not in src, (
        "evaluate_charter_candidate must not hardcode 0.15 — use DEMURRAGE_EXPOSURE_FACTOR"
    )


def test_optimizer_uses_config_congestion_multiplier():
    src = inspect.getsource(opt_module.evaluate_charter_candidate)
    assert "CONGESTION_COST_MULTIPLIER" in src
    assert "* 0.5" not in src, (
        "evaluate_charter_candidate must not hardcode 0.5 — use CONGESTION_COST_MULTIPLIER"
    )


def test_optimizer_uses_config_risk_factors():
    src = inspect.getsource(opt_module.evaluate_charter_candidate)
    assert "RISK_FACTOR_LOW" in src
    assert "RISK_FACTOR_HIGH" in src
    assert "1.5" not in src or "RISK_FACTOR_LOW" in src  # 1.5 only appears as constant ref


def test_optimizer_uses_config_vessel_threshold():
    src = inspect.getsource(opt_module.evaluate_charter_candidate)
    assert "VESSEL_AVAILABILITY_MIN_THRESHOLD" in src
    assert "< 8" not in src, (
        "evaluate_charter_candidate must not hardcode 8 — use VESSEL_AVAILABILITY_MIN_THRESHOLD"
    )


def test_decision_twin_uses_config_constants():
    src = inspect.getsource(dt_module.DecisionTwinEngine)
    assert "DEMURRAGE_EXPOSURE_FACTOR" in src
    assert "CONGESTION_COST_MULTIPLIER" in src
    assert "CONGESTION_TO_WAITING_HOURS_FACTOR" in src


# ── Registry display function ─────────────────────────────────────────────────

def test_registry_returns_list_with_all_parameters():
    reg = get_decision_params_registry()
    assert isinstance(reg, list)
    assert len(reg) == len(_PARAMS)
    param_names = {r["parameter"] for r in reg}
    assert "demurrage_exposure_factor" in param_names
    assert "weather_risk_penalty_per_point" in param_names


def test_registry_rows_have_required_display_fields():
    reg = get_decision_params_registry()
    for row in reg:
        for field in ("parameter", "value", "unit", "classification", "source",
                      "note", "sensitivity_min", "sensitivity_max", "editable"):
            assert field in row, f"Registry row missing field '{field}'"


# ── Pulp not imported ─────────────────────────────────────────────────────────

def test_optimizer_does_not_import_pulp():
    src = inspect.getsource(opt_module)
    assert "import pulp" not in src, (
        "optimizer.py must not import pulp — enumeration is used, not LP"
    )
