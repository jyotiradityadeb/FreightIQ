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
    risk_tolerance: str = "Medium",
    cost_factor_overrides: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Evaluates exact logistics cost for a specific candidate (date, vessel_class, route).

    cost_factor_overrides is an optional dict accepted by the sensitivity engine to
    substitute specific cost factors without mutating global config.  Recognised keys:
      "demurrage_factor", "congestion_multiplier", "weather_penalty", "event_penalty"
    Any key absent from the dict falls back to the config_model constant.
    """
def _normalize_location_alias(name: str) -> str:
    """Normalizes common display name aliases to canonical config names."""
    if not name:
        return name
    name_clean = name.strip()
    alias_map = {
        "Haldia": "Kolkata/Haldia",
        "Kolkata": "Kolkata/Haldia",
        "Vizag": "Visakhapatnam",
        "Paradeep": "Paradip",
    }
    return alias_map.get(name_clean, name_clean)


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
    risk_tolerance: str = "Medium",
    cost_factor_overrides: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Evaluates exact logistics cost for a specific candidate (date, vessel_class, route).

    cost_factor_overrides is an optional dict accepted by the sensitivity engine to
    substitute specific cost factors without mutating global config.  Recognised keys:
      "demurrage_factor", "congestion_multiplier", "weather_penalty", "event_penalty"
    Any key absent from the dict falls back to the config_model constant.
    """
    norm_origin = _normalize_location_alias(origin)
    norm_dest = _normalize_location_alias(destination)
    route_key = f"{norm_origin} -> {norm_dest}"

    # Use canonical route resolver
    from backend.domain.routes import resolve_route
    from backend.domain.ports import get_port_by_id
    route_res = resolve_route(origin, destination)

    if not route_res.is_calibrated:
        return {
            "feasible": False,
            "infeasibility_reason": f"UNSUPPORTED_ROUTE: Route '{origin}' → '{destination}' is CATALOG ONLY — optimization unavailable ({route_res.message})."
        }

    if vessel_class not in VESSEL_CLASSES:
        return {
            "feasible": False,
            "infeasibility_reason": f"UNSUPPORTED_VESSEL: Vessel class '{vessel_class}' is not recognized."
        }

    dest_port = get_port_by_id(destination) or get_port_by_id(norm_dest)
    port_info = PORT_CONFIG.get(norm_dest, {
        "base_congestion_index": 50.0,
        "avg_laytime_hours": 48.0,
        "congestion_cost_per_hour_usd": 700.0,
        "draft_limit_m": dest_port.max_draft_m if dest_port else 18.0
    })

    vessel_info = VESSEL_CLASSES[vessel_class]

    # 1. Capacity Feasibility Check
    if quantity_tonnes > vessel_info["max_capacity"]:
        return {
            "feasible": False,
            "infeasibility_reason": f"Cargo quantity ({quantity_tonnes:,}t) exceeds max capacity of {vessel_class} ({vessel_info['max_capacity']:,}t)."
        }

    # 2. Port Route & Draft Compatibility Check
    v_draft = vessel_info.get("draft_requirement_m", 0.0)
    p_draft_limit = dest_port.max_draft_m if dest_port else port_info.get("draft_limit_m", 99.0)
    if v_draft > p_draft_limit:
        return {
            "feasible": False,
            "infeasibility_reason": f"UNSUPPORTED_DRAFT: {vessel_class} draft ({v_draft}m) exceeds {dest_port.port_name if dest_port else norm_dest} max allowed draft limit ({p_draft_limit}m)."
        }

    allowed_vessels = route_res.allowed_vessel_classes
    if vessel_class not in allowed_vessels:
        return {
            "feasible": False,
            "infeasibility_reason": f"{vessel_class} is not compatible with route constraints for {norm_dest}."
        }

    # 3. Minimum Availability Check
    if vessel_avail_count < VESSEL_AVAILABILITY_MIN_THRESHOLD:
        return {
            "feasible": False,
            "infeasibility_reason": f"Insufficient vessel availability ({vessel_avail_count} ships available, min threshold is {VESSEL_AVAILABILITY_MIN_THRESHOLD})."
        }

    # Calculate Costs
    unit_freight = (
        freight_rate_forecast
        * route_res.base_freight_multiplier
        * vessel_info["base_daily_charter_multiplier"]
    )
    freight_cost = unit_freight * quantity_tonnes

    _ov = cost_factor_overrides or {}
    eff_demurrage_factor = _ov.get("demurrage_factor", DEMURRAGE_EXPOSURE_FACTOR)
    eff_congestion_mult = _ov.get("congestion_multiplier", CONGESTION_COST_MULTIPLIER)
    eff_weather_penalty = _ov.get("weather_penalty", WEATHER_RISK_PENALTY_PER_POINT)
    eff_event_penalty = _ov.get("event_penalty", EVENT_RISK_PENALTY_PER_POINT)

    demurrage_rate = demurrage_rate_override if demurrage_rate_override is not None else vessel_info["daily_demurrage_rate"]
    laytime_hours = port_info["avg_laytime_hours"]
    total_port_hours = laytime_hours + waiting_hours
    demurrage_cost = (total_port_hours / 24.0) * (demurrage_rate * eff_demurrage_factor)

    congestion_cost = congestion_score * port_info["congestion_cost_per_hour_usd"] * eff_congestion_mult

    risk_factor_map = {"Low": RISK_FACTOR_LOW, "Medium": RISK_FACTOR_MEDIUM, "High": RISK_FACTOR_HIGH}
    risk_factor = risk_factor_map.get(risk_tolerance, RISK_FACTOR_MEDIUM)

    weather_penalty = weather_risk * eff_weather_penalty * risk_factor
    event_penalty = event_risk * eff_event_penalty * risk_factor
    route_risk_penalty = weather_penalty + event_penalty

    total_cost = freight_cost + demurrage_cost + congestion_cost + route_risk_penalty

    return {
        "feasible": True,
        "infeasibility_reason": None,
        "charter_date": charter_date.strftime("%Y-%m-%d"),
        "vessel_class": vessel_class,
        "route": route_key,
        "origin": norm_origin,
        "destination": norm_dest,
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
    risk_tolerance: str = "Medium",
    cost_factor_overrides: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Evaluates all candidate dates and vessel options within decision window,
    selects deterministic minimum total logistics cost candidate, and generates
    rule-based explainability text.
    """
    df_eval = forecast_df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df_eval["date"]):
        df_eval["date"] = pd.to_datetime(df_eval["date"])

    if earliest_date:
        df_eval = df_eval[df_eval["date"] >= pd.to_datetime(earliest_date)]
    if latest_date:
        df_eval = df_eval[df_eval["date"] <= pd.to_datetime(latest_date)]

    if len(df_eval) == 0:
        df_eval = forecast_df.copy()

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
                risk_tolerance=risk_tolerance,
                cost_factor_overrides=cost_factor_overrides,
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
    
    # Option B: Alternative candidate with 2nd best cost
    option_b = candidates[1] if len(candidates) > 1 else best_option
    
    # Option C: Earliest date feasible candidate
    earliest_candidates = sorted(candidates, key=lambda x: x["charter_date"])
    option_c = earliest_candidates[0]

    # Rule-Based Explainability Generation
    rec_date_dt = pd.to_datetime(best_option["charter_date"])
    earliest_date_str = earliest_candidates[0]["charter_date"]
    earliest_dt = pd.to_datetime(earliest_date_str)
    days_from_start = (rec_date_dt - earliest_dt).days

    if days_from_start == 0:
        action_text = f"Charter on earliest window date ({best_option['charter_date']})"
    else:
        action_text = f"Charter on optimal date ({best_option['charter_date']}) — {days_from_start} days after window opens"

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
        f"port congestion and demurrage exposure at {best_option['destination']} are minimized on {best_option['charter_date']}.",
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

    explainability = generate_candidate_explainability(best_option, candidates)

    return {
        "success": True,
        "recommendation": recommendation_card,
        "best_option": best_option,
        "scenarios": {
            "Option A (Optimal)": option_a,
            "Option B (Alternative)": option_b,
            "Option C (Earliest Date)": option_c
        },
        "all_evaluated_candidates": candidates,
        "explainability": explainability,
    }


def generate_candidate_explainability(
    best_option: Dict[str, Any],
    all_candidates: List[Dict[str, Any]],
    top_n: int = 3,
) -> Dict[str, Any]:
    """
    Generates per-candidate explainability from actual computed cost fields.
    No generic boilerplate — all figures are pulled from the candidates list.
    """
    best_total = best_option["total_logistics_cost_usd"]

    cost_fractions = {
        "freight": best_option["freight_cost_usd"] / best_total if best_total else 0,
        "demurrage": best_option["demurrage_cost_usd"] / best_total if best_total else 0,
        "congestion": best_option["congestion_cost_usd"] / best_total if best_total else 0,
        "risk": best_option["route_risk_penalty_usd"] / best_total if best_total else 0,
    }
    dominant_component = max(cost_fractions, key=cost_fractions.get)
    component_labels = {
        "freight": "freight cost",
        "demurrage": "demurrage exposure",
        "congestion": "congestion charge",
        "risk": "route risk penalty",
    }

    dominant_field = "route_risk_penalty_usd" if dominant_component == "risk" else f"{dominant_component}_cost_usd"

    winner_reasons = [
        f"Lowest risk-adjusted total logistics cost among all feasible candidates "
        f"(${best_total:,.0f} total; ${best_option['effective_cost_per_tonne']:.2f}/t).",
        f"Capacity feasible: {best_option['vessel_class']} handles {best_option['quantity_tonnes']:,.0f} t "
        f"within vessel max capacity.",
        f"Dominant cost driver is {component_labels[dominant_component]} "
        f"(${best_option[dominant_field]:,.0f}, "
        f"{cost_fractions[dominant_component]*100:.1f}% of total).",
        f"Port waiting exposure: {best_option['waiting_hours']:.1f} h at charter date "
        f"(congestion score {best_option['congestion_score']:.0f}/100).",
    ]

    # Why top alternatives lost
    alternatives = [c for c in all_candidates if c is not best_option][:top_n]
    alt_explanations = []
    for alt in alternatives:
        delta = alt["total_logistics_cost_usd"] - best_total
        reasons = []
        if alt["freight_cost_usd"] > best_option["freight_cost_usd"] + 1:
            reasons.append(
                f"freight cost ${alt['freight_cost_usd']:,.0f} vs ${best_option['freight_cost_usd']:,.0f} "
                f"(+${alt['freight_cost_usd'] - best_option['freight_cost_usd']:,.0f})"
            )
        if alt["demurrage_cost_usd"] > best_option["demurrage_cost_usd"] + 1:
            reasons.append(
                f"demurrage ${alt['demurrage_cost_usd']:,.0f} vs ${best_option['demurrage_cost_usd']:,.0f} "
                f"(+${alt['demurrage_cost_usd'] - best_option['demurrage_cost_usd']:,.0f})"
            )
        if alt["congestion_cost_usd"] > best_option["congestion_cost_usd"] + 1:
            reasons.append(
                f"congestion ${alt['congestion_cost_usd']:,.0f} vs ${best_option['congestion_cost_usd']:,.0f} "
                f"(+${alt['congestion_cost_usd'] - best_option['congestion_cost_usd']:,.0f})"
            )
        if alt["route_risk_penalty_usd"] > best_option["route_risk_penalty_usd"] + 1:
            reasons.append(
                f"risk adjustment ${alt['route_risk_penalty_usd']:,.0f} vs "
                f"${best_option['route_risk_penalty_usd']:,.0f}"
            )
        if not reasons:
            reasons.append("marginally higher total cost due to combined factor accumulation")

        alt_explanations.append({
            "candidate": f"{alt['vessel_class']} on {alt['charter_date']}",
            "total_cost_usd": alt["total_logistics_cost_usd"],
            "delta_vs_winner_usd": round(delta, 2),
            "loss_reasons": reasons,
        })

    return {
        "winner": {
            "candidate": f"{best_option['vessel_class']} on {best_option['charter_date']}",
            "total_cost_usd": best_total,
            "cost_breakdown_usd": {
                "freight": best_option["freight_cost_usd"],
                "demurrage": best_option["demurrage_cost_usd"],
                "congestion": best_option["congestion_cost_usd"],
                "risk_penalty": best_option["route_risk_penalty_usd"],
            },
            "why_won": winner_reasons,
        },
        "alternatives": alt_explanations,
    }
