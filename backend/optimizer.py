"""
FreightIQ Charter-Timing Optimizer Module

Constraint-aware exhaustive candidate evaluation engine for charter date, vessel
selection, and route evaluation minimising total expected logistics cost:
    Expected Total Logistics Cost = Freight Cost + Demurrage Cost + Congestion Cost + Route Risk Penalty

Enumeration is appropriate here: the candidate space is small (O(dates × 3 vessel classes)),
deterministic, and fully auditable — no LP solver is needed or used.

Outputs deterministic recommendations with rule-based explanations.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

from backend.config import (
    VESSEL_CLASSES,
    ROUTES,
    CARGO_TYPES,
    PORT_CONFIG,
)
from backend.config_model import (
    DEMURRAGE_EXPOSURE_FACTOR,
    CONGESTION_COST_MULTIPLIER,
    VESSEL_AVAILABILITY_MIN_THRESHOLD,
    RISK_FACTOR_LOW,
    RISK_FACTOR_MEDIUM,
    RISK_FACTOR_HIGH,
    WEATHER_RISK_PENALTY_PER_POINT,
    EVENT_RISK_PENALTY_PER_POINT,
    FREIGHT_TREND_THRESHOLD,
)


def evaluate_charter_candidate(
    charter_date: pd.Timestamp,
    vessel_class: str,
    origin: str,
    destination: str,
    cargo_type: str,
    quantity_tonnes: float,
    freight_rate_forecast: float,
    congestion_score: float,
    waiting_hours: float,
    vessel_avail_count: int,
    weather_risk: float,
    event_risk: float,
    demurrage_rate_override: Optional[float] = None,
    risk_tolerance: str = "Medium"
) -> Dict[str, Any]:
    """
    Evaluates exact logistics cost for a specific candidate (date, vessel_class, route).
    """
    route_key = f"{origin} -> {destination}"
    route_info = ROUTES.get(route_key, {
        "base_transit_days": 12,
        "base_freight_multiplier": 1.0,
        "allowed_vessels": ["Capesize", "Panamax", "Supramax"]
    })

    vessel_info = VESSEL_CLASSES.get(vessel_class, VESSEL_CLASSES["Panamax"])
    port_info = PORT_CONFIG.get(destination, PORT_CONFIG["Paradip"])

    # 1. Capacity Feasibility Check
    capacity = vessel_info["default_capacity"]
    if quantity_tonnes > vessel_info["max_capacity"]:
        return {"feasible": False, "infeasibility_reason": f"Cargo quantity ({quantity_tonnes:,}t) exceeds max capacity of {vessel_class} ({vessel_info['max_capacity']:,}t)."}

    # 2. Port Draft / Vessel Feasibility Check
    if vessel_class not in route_info.get("allowed_vessels", []):
        return {"feasible": False, "infeasibility_reason": f"{vessel_class} is not compatible with port draft or route constraints for {destination}."}

    # 3. Minimum Availability Check
    if vessel_avail_count < VESSEL_AVAILABILITY_MIN_THRESHOLD:
        return {"feasible": False, "infeasibility_reason": f"Insufficient vessel availability ({vessel_avail_count} ships available, min threshold is {VESSEL_AVAILABILITY_MIN_THRESHOLD})."}

    # Calculate Costs
    # Base Freight Cost ($/tonne * tonnes * multipliers)
    unit_freight = (
        freight_rate_forecast
        * route_info["base_freight_multiplier"]
        * vessel_info["base_daily_charter_multiplier"]
    )
    freight_cost = unit_freight * quantity_tonnes

    # Demurrage Cost
    demurrage_rate = demurrage_rate_override if demurrage_rate_override is not None else vessel_info["daily_demurrage_rate"]
    laytime_hours = port_info["avg_laytime_hours"]
    total_port_hours = laytime_hours + waiting_hours
    demurrage_cost = (total_port_hours / 24.0) * (demurrage_rate * DEMURRAGE_EXPOSURE_FACTOR)

    # Congestion Cost
    congestion_cost = congestion_score * port_info["congestion_cost_per_hour_usd"] * CONGESTION_COST_MULTIPLIER

    # Risk Penalty Factor based on user tolerance
    risk_factor_map = {"Low": RISK_FACTOR_LOW, "Medium": RISK_FACTOR_MEDIUM, "High": RISK_FACTOR_HIGH}
    risk_factor = risk_factor_map.get(risk_tolerance, RISK_FACTOR_MEDIUM)

    weather_penalty = weather_risk * WEATHER_RISK_PENALTY_PER_POINT * risk_factor
    event_penalty = event_risk * EVENT_RISK_PENALTY_PER_POINT * risk_factor
    route_risk_penalty = weather_penalty + event_penalty

    total_cost = freight_cost + demurrage_cost + congestion_cost + route_risk_penalty

    return {
        "feasible": True,
        "infeasibility_reason": None,
        "charter_date": charter_date.strftime("%Y-%m-%d"),
        "vessel_class": vessel_class,
        "route": route_key,
        "origin": origin,
        "destination": destination,
        "cargo_type": cargo_type,
        "quantity_tonnes": quantity_tonnes,
        "unit_freight_usd_per_tonne": round(unit_freight, 2),
        "freight_cost_usd": round(freight_cost, 2),
        "demurrage_cost_usd": round(demurrage_cost, 2),
        "congestion_cost_usd": round(congestion_cost, 2),
        "route_risk_penalty_usd": round(route_risk_penalty, 2),
        "total_logistics_cost_usd": round(total_cost, 2),
        "effective_cost_per_tonne": round(total_cost / quantity_tonnes, 2),
        "forecast_freight_base": round(freight_rate_forecast, 2),
        "congestion_score": round(congestion_score, 1),
        "waiting_hours": round(waiting_hours, 1),
        "vessel_avail_count": int(vessel_avail_count)
    }


def optimize_charter_timing(
    forecast_df: pd.DataFrame,
    cargo_type: str = "Coking Coal",
    quantity_tonnes: float = 75000.0,
    origin: str = "Australia",
    destination: str = "Paradip",
    earliest_date: Optional[str] = None,
    latest_date: Optional[str] = None,
    vessel_class: str = "Auto",
    demurrage_rate: Optional[float] = None,
    risk_tolerance: str = "Medium"
) -> Dict[str, Any]:
    """
    Evaluates all candidate dates and vessel options within decision window,
    selects deterministic minimum total logistics cost candidate, and generates
    rule-based explainability text.
    """
    # Filter forecast dates within decision window
    df_eval = forecast_df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df_eval["date"]):
        df_eval["date"] = pd.to_datetime(df_eval["date"])

    if earliest_date:
        df_eval = df_eval[df_eval["date"] >= pd.to_datetime(earliest_date)]
    if latest_date:
        df_eval = df_eval[df_eval["date"] <= pd.to_datetime(latest_date)]

    if len(df_eval) == 0:
        df_eval = forecast_df.copy()  # fallback to full horizon

    candidate_vessels = (
        ["Capesize", "Panamax", "Supramax"]
        if vessel_class == "Auto"
        else [vessel_class]
    )

    candidates = []
    infeasible_reasons = []

    for _, row in df_eval.iterrows():
        c_date = row["date"]
        f_rate = float(row.get("predicted_freight_rate", row.get("freight_rate", 25.0)))
        c_score = float(row.get("port_congestion_score", 45.0))
        w_hours = float(row.get("avg_waiting_hours", 24.0))
        v_count = int(row.get("vessel_availability_count", row.get("expected_vessel_count", 25)))
        w_risk = float(row.get("weather_risk_score", 3.0))
        e_risk = float(row.get("event_risk_score", 2.0))

        for v_cls in candidate_vessels:
            res = evaluate_charter_candidate(
                charter_date=c_date,
                vessel_class=v_cls,
                origin=origin,
                destination=destination,
                cargo_type=cargo_type,
                quantity_tonnes=quantity_tonnes,
                freight_rate_forecast=f_rate,
                congestion_score=c_score,
                waiting_hours=w_hours,
                vessel_avail_count=v_count,
                weather_risk=w_risk,
                event_risk=e_risk,
                demurrage_rate_override=demurrage_rate,
                risk_tolerance=risk_tolerance
            )
            if res["feasible"]:
                candidates.append(res)
            else:
                infeasible_reasons.append(res["infeasibility_reason"])

    if not candidates:
        return {
            "success": False,
            "error": "No feasible charter option found.",
            "infeasibility_reasons": list(set(infeasible_reasons))
        }

    # Sort deterministically by total_logistics_cost_usd, then date, then vessel_class
    candidates.sort(key=lambda x: (x["total_logistics_cost_usd"], x["charter_date"], x["vessel_class"]))

    best_option = candidates[0]

    # Generate Alternative Scenarios (Options A, B, C)
    option_a = best_option
    
    # Option B: Alternative vessel or date with 2nd best cost
    option_b = candidates[1] if len(candidates) > 1 else best_option
    
    # Option C: Earliest date candidate
    earliest_candidates = sorted(candidates, key=lambda x: x["charter_date"])
    option_c = earliest_candidates[0]

    # Rule-Based Explainability Generation
    rec_date_dt = pd.to_datetime(best_option["charter_date"])
    earliest_dt = pd.to_datetime(candidates[0]["charter_date"])
    days_from_start = (rec_date_dt - earliest_dt).days

    if days_from_start == 0:
        action_text = "Charter immediately on earliest window date"
    else:
        action_text = f"Charter within the next {days_from_start} to {days_from_start + 2} days"

    # Freight trend rationale
    first_rate = df_eval["predicted_freight_rate"].iloc[0] if "predicted_freight_rate" in df_eval.columns else 25.0
    last_rate = df_eval["predicted_freight_rate"].iloc[-1] if "predicted_freight_rate" in df_eval.columns else 25.0
    if last_rate > first_rate + FREIGHT_TREND_THRESHOLD:
        freight_trend = "Upward trend expected (rising rates)"
        trend_reason = "freight rates are forecast to rise after the recommended window"
    elif last_rate < first_rate - FREIGHT_TREND_THRESHOLD:
        freight_trend = "Downward trend expected (softening rates)"
        trend_reason = "freight rates are expected to soften towards the end of window"
    else:
        freight_trend = "Stable rates"
        trend_reason = "freight rates remain flat across the evaluation window"

    why_reasons = [
        f"{trend_reason}.",
        f"selected {best_option['vessel_class']} vessel provides the best-fit capacity for {quantity_tonnes:,} tonnes of {cargo_type}.",
        f"port congestion and demurrage exposure at {destination} are minimized on {best_option['charter_date']}.",
        f"total estimated logistics cost (${best_option['total_logistics_cost_usd']:,.2f}) is lower than alternative charter dates."
    ]

    recommendation_card = {
        "recommended_charter_date": best_option["charter_date"],
        "recommended_vessel": best_option["vessel_class"],
        "route": best_option["route"],
        "origin": best_option["origin"],
        "destination": best_option["destination"],
        "cargo_type": cargo_type,
        "quantity_tonnes": quantity_tonnes,
        "expected_unit_freight_usd": best_option["unit_freight_usd_per_tonne"],
        "expected_freight_cost_usd": best_option["freight_cost_usd"],
        "expected_demurrage_cost_usd": best_option["demurrage_cost_usd"],
        "expected_congestion_cost_usd": best_option["congestion_cost_usd"],
        "expected_route_risk_penalty_usd": best_option["route_risk_penalty_usd"],
        "expected_total_logistics_cost_usd": best_option["total_logistics_cost_usd"],
        "effective_cost_per_tonne": best_option["effective_cost_per_tonne"],
        "freight_trend": freight_trend,
        "decision": action_text,
        "why": why_reasons,
        "disclaimer": "Prototype decision-support estimate — not a commercial charter commitment."
    }

    return {
        "success": True,
        "recommendation": recommendation_card,
        "best_option": best_option,
        "scenarios": {
            "Option A (Optimal)": option_a,
            "Option B (Alternative)": option_b,
            "Option C (Earliest Date)": option_c
        },
        "all_evaluated_candidates": candidates
    }
