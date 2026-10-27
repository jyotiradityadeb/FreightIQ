"""Traceable strategy comparison on one shared set of synthetic futures.

The existing charter optimizer and cost evaluator remain authoritative. Sampled
frequencies describe this configured synthetic experiment, not real-world odds.
"""

from __future__ import annotations

from datetime import datetime, timezone
import math
from typing import Any

import numpy as np
import pandas as pd

from backend.config import DEMO_USD_INR_RATE
from backend.config_model import DEMURRAGE_EXPOSURE_FACTOR
from backend.optimizer import evaluate_charter_candidate, optimize_charter_timing


def _sigma(values: pd.Series, floor: float, ceiling: float) -> float:
    numeric = pd.to_numeric(values, errors="coerce").dropna()
    if len(numeric) < 3:
        return floor
    return float(np.clip(numeric.tail(90).diff().dropna().std(), floor, ceiling))


def _identity(candidate: dict[str, Any]) -> tuple[str, str]:
    return candidate["charter_date"], candidate["vessel_class"]


def _evaluate_samples(
    candidate: dict[str, Any], row: pd.Series, draws: np.ndarray, sigmas: dict[str, float],
    *, cargo_type: str, quantity_tonnes: float, origin: str, destination: str,
    risk_tolerance: str, demurrage_rate: float | None, uncertainty_scale: float,
    cost_factor_overrides: dict[str, float] | None,
) -> np.ndarray:
    values = np.full(len(draws), np.nan)
    for index, (rate_z, congestion_z, wait_z, availability_z, weather_z, event_z) in enumerate(draws):
        freight = max(0.01, float(row["predicted_freight_rate"]) + rate_z * sigmas["freight"] * uncertainty_scale)
        congestion = float(np.clip(float(row["port_congestion_score"]) + congestion_z * sigmas["congestion"] * uncertainty_scale, 0, 100))
        waiting = max(0.0, float(row["avg_waiting_hours"]) + wait_z * sigmas["waiting"] * uncertainty_scale)
        vessels = max(0, round(float(row["vessel_availability_count"]) + availability_z * sigmas["availability"] * uncertainty_scale))
        weather = float(np.clip(float(row["weather_risk_score"]) + weather_z * sigmas["weather"] * uncertainty_scale, 0, 10))
        event = float(np.clip(float(row["event_risk_score"]) + event_z * sigmas["event"] * uncertainty_scale, 0, 10))
        evaluated = evaluate_charter_candidate(
            charter_date=pd.Timestamp(candidate["charter_date"]), vessel_class=candidate["vessel_class"],
            origin=origin, destination=destination, cargo_type=cargo_type,
            quantity_tonnes=quantity_tonnes, freight_rate_forecast=freight,
            congestion_score=congestion, waiting_hours=waiting, vessel_avail_count=vessels,
            weather_risk=weather, event_risk=event, demurrage_rate_override=demurrage_rate,
            risk_tolerance=risk_tolerance, cost_factor_overrides=cost_factor_overrides,
        )
        if evaluated["feasible"]:
            values[index] = evaluated["total_logistics_cost_usd"]
    return values


def _cvar90(costs: np.ndarray) -> float:
    cutoff = np.percentile(costs, 90)
    return float(np.mean(costs[costs >= cutoff]))


def _date_rate_counterfactual(frame: pd.DataFrame, best: dict[str, Any], args: dict[str, Any]) -> dict[str, Any]:
    """Find a selected-date freight increase that changes the optimizer's date."""
    date = best["charter_date"]
    mask = frame["date"].dt.strftime("%Y-%m-%d") == date
    if not mask.any():
        return {"status": "unavailable", "reason": "Selected date is absent from the forecast frame."}
    base_rate = float(frame.loc[mask, "predicted_freight_rate"].iloc[0])

    def evaluate(pct: float) -> dict[str, Any]:
        revised = frame.copy(deep=True)
        revised.loc[mask, "predicted_freight_rate"] = base_rate * (1 + pct / 100)
        return optimize_charter_timing(forecast_df=revised, **args)

    high_result = evaluate(50.0)
    if not high_result["success"] or high_result["best_option"]["charter_date"] == date:
        return {"status": "not_found_within_range", "tested_max_pct": 50,
                "reason": "No different charter date became optimal with up to a 50% increase in the selected date's freight rate."}
    low, high = 0.0, 50.0
    for _ in range(20):
        middle = (low + high) / 2
        result = evaluate(middle)
        if result["success"] and result["best_option"]["charter_date"] != date:
            high = middle
        else:
            low = middle
    # Round upward to the displayed 0.01% step and verify that the reported
    # percentage itself changes the selected charter date.
    displayed = math.ceil(high * 100 - 1e-10) / 100
    displayed_result = evaluate(displayed)
    while displayed < 50 and (
        not displayed_result["success"] or displayed_result["best_option"]["charter_date"] == date
    ):
        displayed = round(displayed + 0.01, 2)
        displayed_result = evaluate(displayed)
    if not displayed_result["success"] or displayed_result["best_option"]["charter_date"] == date:
        return {"status": "not_found_within_range", "tested_max_pct": 50,
                "reason": "No different charter date became optimal at the displayed 0.01% step."}
    return {"status": "threshold_found", "freight_increase_pct": displayed,
            "base_rate_usd_per_tonne": round(base_rate, 2),
            "new_date": displayed_result["best_option"]["charter_date"],
            "new_vessel": displayed_result["best_option"]["vessel_class"],
            "interpretation": "Increase applies only to the selected charter date; every other model input stays fixed."}


def compare_strategies(
    forecast_df: pd.DataFrame, history_df: pd.DataFrame, *, cargo_type: str,
    quantity_tonnes: float, origin: str, destination: str, vessel_class: str = "Auto",
    risk_tolerance: str = "Medium", earliest_date: str | None = None,
    latest_date: str | None = None, demurrage_rate: float | None = None,
    simulations_count: int = 250, seed: int = 42, uncertainty_scale: float = 1.0,
    model_name: str = "Auto", route_key: str = "", demurrage_shock_pct: float = 0.0,
) -> dict[str, Any]:
    if not 50 <= simulations_count <= 500:
        raise ValueError("simulations_count must be between 50 and 500")
    if not 0.25 <= uncertainty_scale <= 2.0:
        raise ValueError("uncertainty_scale must be between 0.25 and 2.0")
    frame = forecast_df.copy(deep=True)
    frame["date"] = pd.to_datetime(frame["date"])
    required = ["predicted_freight_rate", "port_congestion_score", "avg_waiting_hours",
                "vessel_availability_count", "weather_risk_score", "event_risk_score"]
    if frame.empty or any(field not in frame or frame[field].isna().any() for field in required):
        raise ValueError("Forecast frame lacks complete operational inputs")
    overrides = ({"demurrage_factor": DEMURRAGE_EXPOSURE_FACTOR * (1 + demurrage_shock_pct / 100)}
                 if demurrage_shock_pct else None)
    args = dict(cargo_type=cargo_type, quantity_tonnes=quantity_tonnes, origin=origin,
                destination=destination, vessel_class=vessel_class, risk_tolerance=risk_tolerance,
                earliest_date=earliest_date, latest_date=latest_date, demurrage_rate=demurrage_rate,
                cost_factor_overrides=overrides)
    optimization = optimize_charter_timing(forecast_df=frame, **args)
    if not optimization["success"]:
        raise ValueError(optimization.get("error", "No feasible charter strategies"))
    candidates = optimization["all_evaluated_candidates"]
    best = optimization["best_option"]
    earliest_day = min(item["charter_date"] for item in candidates)
    early = next(item for item in candidates if item["charter_date"] == earliest_day)
    later_dates = sorted({item["charter_date"] for item in candidates if item["charter_date"] > earliest_day})
    target_later = next((day for day in later_dates if (pd.Timestamp(day) - pd.Timestamp(earliest_day)).days >= 7),
                        later_dates[-1] if later_dates else earliest_day)
    deferred = next(item for item in candidates if item["charter_date"] == target_later)
    shortlist = {_identity(item): item for item in [best, early, deferred]}
    for item in candidates:
        shortlist.setdefault(_identity(item), item)
        if len(shortlist) >= 10:
            break
    options = list(shortlist.values())
    by_date = {date.strftime("%Y-%m-%d"): row for date, row in frame.set_index("date").iterrows()}
    sigmas = {
        "freight": _sigma(history_df["freight_rate"], 0.25, 3.0),
        "congestion": _sigma(history_df["port_congestion_score"], 1.0, 12.0),
        "waiting": _sigma(history_df["avg_waiting_hours"], 0.5, 8.0),
        "availability": _sigma(history_df["vessel_availability_count"], 1.0, 6.0),
        "weather": _sigma(history_df["weather_risk_score"], 0.25, 2.0),
        "event": _sigma(history_df["event_risk_score"], 0.2, 1.5),
    }
    draws = np.random.default_rng(seed).standard_normal((simulations_count, 6))
    sampled = {}
    for item in options:
        sampled[_identity(item)] = _evaluate_samples(
            item, by_date[item["charter_date"]], draws, sigmas,
            cargo_type=cargo_type, quantity_tonnes=quantity_tonnes, origin=origin,
            destination=destination, risk_tolerance=risk_tolerance,
            demurrage_rate=demurrage_rate, uncertainty_scale=uncertainty_scale,
            cost_factor_overrides=overrides,
        )
    common_shortlist = np.logical_and.reduce([np.isfinite(values) for values in sampled.values()])
    if common_shortlist.sum() < max(20, simulations_count // 2):
        raise ValueError("Too few common feasible futures for a fair strategy comparison")
    risk = min(options, key=lambda item: (_cvar90(sampled[_identity(item)][common_shortlist]),
                                          item["total_logistics_cost_usd"], _identity(item)))
    policies = [("early", "Early charter", early), ("forecast", "Forecast window", best),
                ("deferred", "Deferred benchmark", deferred),
                ("downside", "Downside-aware", risk)]
    final_mask = np.logical_and.reduce([np.isfinite(sampled[_identity(item)]) for _, _, item in policies])
    n_common = int(final_mask.sum())
    if n_common < 20:
        raise ValueError("Too few common feasible futures for final strategy comparison")
    compared = np.array([sampled[_identity(item)][final_mask] for _, _, item in policies])
    winners = np.min(compared, axis=0)
    strategies = []
    for index, (policy, label, item) in enumerate(policies):
        values = compared[index]
        mean = float(np.mean(values))
        p90 = float(np.percentile(values, 90))
        cvar = _cvar90(values)
        win_share = float(np.mean(np.isclose(values, winners, atol=0.01, rtol=0)) * 100)
        strategies.append({
            "id": policy, "label": label, "charter_date": item["charter_date"],
            "vessel_class": item["vessel_class"], "baseline_cost_usd": item["total_logistics_cost_usd"],
            "freight_cost_usd": item["freight_cost_usd"], "demurrage_cost_usd": item["demurrage_cost_usd"],
            "congestion_cost_usd": item["congestion_cost_usd"], "risk_cost_usd": item["route_risk_penalty_usd"],
            "mean_cost_usd": round(mean, 2), "median_cost_usd": round(float(np.median(values)), 2),
            "p90_cost_usd": round(p90, 2), "cvar90_cost_usd": round(cvar, 2),
            "win_share_pct": round(win_share, 1),
            "feasible_futures_pct": round(float(np.mean(np.isfinite(sampled[_identity(item)])) * 100), 1),
            "cost_samples_inr_cr": np.round(values * DEMO_USD_INR_RATE / 1e7, 4).tolist(),
        })
    for strategy in strategies:
        strategy["pareto_efficient"] = not any(
            other is not strategy
            and other["mean_cost_usd"] <= strategy["mean_cost_usd"]
            and other["cvar90_cost_usd"] <= strategy["cvar90_cost_usd"]
            and (other["mean_cost_usd"] < strategy["mean_cost_usd"]
                 or other["cvar90_cost_usd"] < strategy["cvar90_cost_usd"])
            for other in strategies
        )
    lowest_mean = min(strategies, key=lambda item: (item["mean_cost_usd"], item["id"]))["id"]
    lowest_downside = min(strategies, key=lambda item: (item["cvar90_cost_usd"], item["id"]))["id"]
    most_stable = max(strategies, key=lambda item: (item["win_share_pct"], -item["mean_cost_usd"]))["id"]
    savings = early["total_logistics_cost_usd"] - best["total_logistics_cost_usd"]
    components = [
        ("Freight", "freight_cost_usd"), ("Demurrage", "demurrage_cost_usd"),
        ("Port / congestion", "congestion_cost_usd"), ("Weather / event model penalty", "route_risk_penalty_usd"),
    ]
    evidence = [{"driver": label, "selected_usd": best[key], "earliest_usd": early[key],
                 "delta_vs_earliest_usd": round(best[key] - early[key], 2)} for label, key in components]
    return {
        "success": True, "route_key": route_key, "model_name": model_name,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "data_mode": "SYNTHETIC / MODELLED", "currency_rate_inr_per_usd": DEMO_USD_INR_RATE,
        "sample_count": simulations_count, "common_feasible_samples": n_common,
        "seed": seed, "uncertainty_scale": uncertainty_scale,
        "demurrage_shock_pct": demurrage_shock_pct,
        "uncertainty_sigma": sigmas,
        "uncertainty_method": "Independent normal shocks; scale from last 90 synthetic daily changes, bounded by documented floors/caps. Shared draws across all strategies. Not calibrated real-world probabilities.",
        "selection_scope": f"Downside-aware policy selected from {len(options)} feasible candidate actions, including earliest and deferred benchmarks.",
        "strategies": strategies,
        "winners": {"lowest_mean": lowest_mean, "lowest_downside": lowest_downside,
                    "most_simulated_wins": most_stable},
        "selected_action": {"charter_date": best["charter_date"], "vessel_class": best["vessel_class"],
                            "cost_usd": best["total_logistics_cost_usd"]},
        "earliest_action": {"charter_date": early["charter_date"], "vessel_class": early["vessel_class"],
                            "cost_usd": early["total_logistics_cost_usd"]},
        "deferred_action": {"charter_date": deferred["charter_date"], "vessel_class": deferred["vessel_class"],
                            "cost_usd": deferred["total_logistics_cost_usd"]},
        "modelled_savings_vs_earliest_usd": round(savings, 2),
        "modelled_cost_of_waiting_usd": round(deferred["total_logistics_cost_usd"] - best["total_logistics_cost_usd"], 2),
        "cost_evidence": evidence,
        "counterfactual": _date_rate_counterfactual(frame, best, args),
        "history_start": str(pd.to_datetime(history_df["date"]).min().date()),
        "history_end": str(pd.to_datetime(history_df["date"]).max().date()),
        "forecast_start": str(frame["date"].min().date()),
        "forecast_end": str(frame["date"].max().date()),
    }
