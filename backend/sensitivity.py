"""
FreightIQ Assumption Sensitivity Engine

Perturbs each key cost-model assumption individually (holding others at baseline),
re-runs the optimizer, and computes a stability summary over all tested settings.

Stability definition:
    fraction of perturbed settings in which BOTH the recommended vessel AND the
    recommended charter date are identical to the baseline recommendation.
"""

from typing import Any, Dict, List, Optional

import pandas as pd

from backend.config_model import (
    DEMURRAGE_EXPOSURE_FACTOR,
    CONGESTION_COST_MULTIPLIER,
    WEATHER_RISK_PENALTY_PER_POINT,
    EVENT_RISK_PENALTY_PER_POINT,
)
from backend.optimizer import optimize_charter_timing

# Perturbation levels applied to each parameter (fractional, e.g. -0.30 = −30%)
PERTURBATION_LEVELS = [-0.30, -0.15, 0.0, 0.15, 0.30]

# Parameters subject to sensitivity sweep
_PARAM_SPECS = [
    {
        "key": "demurrage_exposure_factor",
        "label": "Demurrage Exposure Factor",
        "baseline": DEMURRAGE_EXPOSURE_FACTOR,
        "override_key": "demurrage_factor",
        "unit": "dimensionless",
    },
    {
        "key": "congestion_cost_multiplier",
        "label": "Congestion Cost Multiplier",
        "baseline": CONGESTION_COST_MULTIPLIER,
        "override_key": "congestion_multiplier",
        "unit": "dimensionless",
    },
    {
        "key": "weather_risk_penalty_per_point",
        "label": "Weather Risk Penalty",
        "baseline": WEATHER_RISK_PENALTY_PER_POINT,
        "override_key": "weather_penalty",
        "unit": "USD/pt",
    },
    {
        "key": "event_risk_penalty_per_point",
        "label": "Event Risk Penalty",
        "baseline": EVENT_RISK_PENALTY_PER_POINT,
        "override_key": "event_penalty",
        "unit": "USD/pt",
    },
]


def run_sensitivity_analysis(
    forecast_df: pd.DataFrame,
    cargo_type: str = "Coking Coal",
    quantity_tonnes: float = 75000.0,
    origin: str = "Australia",
    destination: str = "Paradip",
    risk_tolerance: str = "Medium",
    demurrage_rate: Optional[float] = None,
    earliest_date: Optional[str] = None,
    latest_date: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Runs the optimizer once per (parameter, perturbation_level) combination.
    Returns per-assumption results and an overall stability summary.

    The baseline (0% perturbation on every parameter) is included in each
    parameter's sweep; its recommendation is the reference for stability counting.
    Non-mutating: global config constants are never modified.
    """

    # --- Baseline run ---
    baseline_res = optimize_charter_timing(
        forecast_df=forecast_df,
        cargo_type=cargo_type,
        quantity_tonnes=quantity_tonnes,
        origin=origin,
        destination=destination,
        risk_tolerance=risk_tolerance,
        demurrage_rate=demurrage_rate,
        earliest_date=earliest_date,
        latest_date=latest_date,
    )

    if not baseline_res["success"]:
        return {"success": False, "error": "Baseline optimizer run failed."}

    baseline_vessel = baseline_res["recommendation"]["recommended_vessel"]
    baseline_date = baseline_res["recommendation"]["recommended_charter_date"]
    baseline_cost = baseline_res["recommendation"]["expected_total_logistics_cost_usd"]

    # --- Per-parameter sweeps ---
    param_results: List[Dict[str, Any]] = []
    total_settings = 0
    stable_count = 0

    for spec in _PARAM_SPECS:
        levels: List[Dict[str, Any]] = []
        param_stable = 0

        for pct in PERTURBATION_LEVELS:
            perturbed_value = round(spec["baseline"] * (1.0 + pct), 6)

            run_res = optimize_charter_timing(
                forecast_df=forecast_df,
                cargo_type=cargo_type,
                quantity_tonnes=quantity_tonnes,
                origin=origin,
                destination=destination,
                risk_tolerance=risk_tolerance,
                demurrage_rate=demurrage_rate,
                earliest_date=earliest_date,
                latest_date=latest_date,
                cost_factor_overrides={spec["override_key"]: perturbed_value},
            )

            if run_res["success"]:
                run_vessel = run_res["recommendation"]["recommended_vessel"]
                run_date = run_res["recommendation"]["recommended_charter_date"]
                run_cost = run_res["recommendation"]["expected_total_logistics_cost_usd"]
                rec_held = (run_vessel == baseline_vessel) and (run_date == baseline_date)
            else:
                run_vessel = None
                run_date = None
                run_cost = None
                rec_held = False

            if pct != 0.0:  # exclude baseline-level from stability count (trivially stable)
                total_settings += 1
                if rec_held:
                    stable_count += 1
                    param_stable += 1

            # Detect flip threshold: first level where recommendation changes
            flip_threshold = None
            if not rec_held and pct != 0.0:
                flip_threshold = f"{pct:+.0%}"

            levels.append({
                "perturbation_pct": pct * 100,
                "perturbed_value": perturbed_value,
                "recommended_vessel": run_vessel,
                "recommended_date": run_date,
                "total_cost_usd": run_cost,
                "recommendation_held": rec_held,
                "flip_threshold": flip_threshold,
            })

        # Find the lowest-magnitude flip (if any)
        flips = [lv for lv in levels if not lv["recommendation_held"] and lv["perturbation_pct"] != 0]
        first_flip = None
        if flips:
            flips_sorted = sorted(flips, key=lambda x: abs(x["perturbation_pct"]))
            first_flip = flips_sorted[0]["flip_threshold"]

        non_baseline_count = len(PERTURBATION_LEVELS) - 1  # 4 levels per param
        param_results.append({
            "parameter_key": spec["key"],
            "parameter_label": spec["label"],
            "baseline_value": spec["baseline"],
            "unit": spec["unit"],
            "levels": levels,
            "stable_count": param_stable,
            "tested_count": non_baseline_count,
            "stability_fraction": param_stable / non_baseline_count if non_baseline_count else 1.0,
            "holds_across_range": param_stable == non_baseline_count,
            "first_flip_at": first_flip,
        })

    # --- Overall stability ---
    overall_stability = stable_count / total_settings if total_settings > 0 else 1.0
    stable_desc = (
        f"{baseline_vessel} on {baseline_date} held in {stable_count} of "
        f"{total_settings} perturbed settings ({overall_stability*100:.0f}%)"
    )

    return {
        "success": True,
        "baseline_vessel": baseline_vessel,
        "baseline_date": baseline_date,
        "baseline_cost_usd": baseline_cost,
        "param_results": param_results,
        "overall_stability_fraction": overall_stability,
        "stable_count": stable_count,
        "total_settings": total_settings,
        "stability_summary": stable_desc,
        "data_label": "computed on synthetic demo series — not real-market robustness",
    }
