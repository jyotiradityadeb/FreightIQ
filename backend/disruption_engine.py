"""
FreightIQ Disruption Engine & Control Tower Intelligence Module

Ingests market signals, port congestion, vessel availability, weather/event risk,
classifies signal severity, calculates Market Stress Index, Decision Stability Score,
triggers rule-based active alerts, detects recommendation changes, and generates
operational action guidance.

Does NOT mutate original datasets or state.
"""

import datetime
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple

from backend.config import (
    DEMO_USD_INR_RATE,
    VESSEL_CLASSES,
    ROUTES,
    PORT_CONFIG,
)
from backend.optimizer import optimize_charter_timing
from backend.scenario_engine import build_shocked_forecast_df, usd_to_inr, format_inr_val
from backend.schemas import ScenarioShock, ScenarioRequest


def classify_signal_severity(signal_name: str, value: float) -> Tuple[str, int]:
    """
    Classifies signal value into operational severity band:
    0 = Normal, 1 = Watch, 2 = Elevated, 3 = Disrupted.
    """
    if signal_name == "port_congestion":
        if value < 50.0:
            return "Normal", 0
        elif value < 65.0:
            return "Watch", 1
        elif value < 80.0:
            return "Elevated", 2
        else:
            return "Disrupted", 3

    elif signal_name == "vessel_availability":
        if value > 20:
            return "Normal", 0
        elif value >= 12:
            return "Watch", 1
        elif value >= 6:
            return "Elevated", 2
        else:
            return "Disrupted", 3

    elif signal_name == "forecast_change":
        abs_val = abs(value)
        if abs_val < 3.0:
            return "Normal", 0
        elif abs_val < 7.0:
            return "Watch", 1
        elif abs_val < 12.0:
            return "Elevated", 2
        else:
            return "Disrupted", 3

    elif signal_name in ["weather_risk", "route_risk"]:
        if value <= 3.0:
            return "Normal", 0
        elif value <= 5.5:
            return "Watch", 1
        elif value <= 7.9:
            return "Elevated", 2
        else:
            return "Disrupted", 3

    return "Normal", 0


def calculate_market_stress_index(
    forecast_change_pct: float,
    port_congestion_score: float,
    vessel_avail_count: int,
    weather_risk_score: float,
    event_risk_score: float
) -> Dict[str, Any]:
    """
    Calculates deterministic Freight Market Stress Index (0-100).
    """
    freight_pressure = min(30.0, max(0.0, abs(forecast_change_pct) * 2.0))
    port_pressure = min(35.0, max(0.0, (port_congestion_score - 35.0) * 0.55))
    vessel_pressure = min(20.0, max(0.0, (25.0 - float(vessel_avail_count)) * 1.0))
    risk_pressure = min(15.0, max(0.0, (weather_risk_score + event_risk_score) * 1.2))

    total_score = min(100.0, max(0.0, freight_pressure + port_pressure + vessel_pressure + risk_pressure))
    round_score = round(total_score, 1)

    if round_score < 30.0:
        state = "Normal"
    elif round_score < 55.0:
        state = "Watch"
    elif round_score < 75.0:
        state = "Elevated"
    else:
        state = "Disrupted"

    return {
        "score": round_score,
        "state": state,
        "breakdown": {
            "freight_pressure": round(freight_pressure, 1),
            "port_pressure": round(port_pressure, 1),
            "vessel_pressure": round(vessel_pressure, 1),
            "risk_pressure": round(risk_pressure, 1)
        }
    }


def calculate_decision_stability(
    market_stress_score: float,
    congestion_score: float,
    weather_risk_score: float,
    event_risk_score: float,
    recommendation_changed: bool = False
) -> Dict[str, Any]:
    """
    Calculates deterministic Decision Stability Indicator (0-100).
    """
    base_stability = 100.0
    stress_penalty = market_stress_score * 0.50
    congestion_penalty = max(0.0, (congestion_score - 45.0) * 0.25)
    risk_penalty = (weather_risk_score + event_risk_score) * 1.5
    change_penalty = 15.0 if recommendation_changed else 0.0

    raw_score = base_stability - stress_penalty - congestion_penalty - risk_penalty - change_penalty
    stability_score = round(max(0.0, min(100.0, raw_score)), 1)

    if stability_score >= 80.0:
        interpretation = "Stable"
    elif stability_score >= 60.0:
        interpretation = "Monitor"
    elif stability_score >= 40.0:
        interpretation = "Unstable"
    else:
        interpretation = "Review Required"

    return {
        "score": stability_score,
        "interpretation": interpretation,
        "formula_description": "Decision Stability is a prototype composite indicator derived from market stress index, port congestion volatility, weather/route risk pressure, and recommendation change state."
    }


def generate_active_alerts(
    signal_states: Dict[str, Any],
    port_congestion_score: float,
    vessel_avail_count: int,
    forecast_change_pct: float,
    destination: str
) -> List[Dict[str, Any]]:
    """
    Generates rule-based active alerts for Control Tower.
    """
    alerts = []
    now_str = datetime.datetime.now().strftime("%H:%M")

    # 1. Port Congestion Alert
    if port_congestion_score >= 65.0:
        sev = "HIGH" if port_congestion_score >= 80.0 else "MEDIUM"
        alerts.append({
            "severity": sev,
            "signal": f"{destination} Port Congestion Surge",
            "timestamp": now_str,
            "operational_impact": f"Congestion score ({port_congestion_score:.0f}/100) increases expected laytime and demurrage risk.",
            "recommended_action": "Review Visakhapatnam alternative or adjust charter window"
        })

    # 2. Freight Forecast Alert
    if abs(forecast_change_pct) >= 6.0:
        sev = "HIGH" if abs(forecast_change_pct) >= 12.0 else "MEDIUM"
        direction = "upward" if forecast_change_pct > 0 else "downward"
        alerts.append({
            "severity": sev,
            "signal": "Freight Rate Forecast Shift",
            "timestamp": now_str,
            "operational_impact": f"14-day rate forecast indicates {forecast_change_pct:+.1f}% {direction} price pressure.",
            "recommended_action": "Advance charter execution to lock rate" if forecast_change_pct > 0 else "Hold charter date to capture softening rates"
        })

    # 3. Vessel Availability Alert
    if vessel_avail_count <= 12:
        sev = "HIGH" if vessel_avail_count < 6 else "MEDIUM"
        alerts.append({
            "severity": sev,
            "signal": "Vessel Supply Tightening",
            "timestamp": now_str,
            "operational_impact": f"Panamax availability count dropped to {vessel_avail_count} suitable ships.",
            "recommended_action": "Secure vessel commitment early or inspect Supramax fallback"
        })

    # Default low priority alert if no high/medium alerts active
    if not alerts:
        alerts.append({
            "severity": "LOW",
            "signal": "Normal Operations",
            "timestamp": now_str,
            "operational_impact": "Freight rates, port congestion, and vessel supply remain within standard operating bands.",
            "recommended_action": "No action required — maintain current charter schedule"
        })

    return alerts


def evaluate_control_tower_state(
    forecast_df: pd.DataFrame,
    cargo_type: str = "Coking Coal",
    quantity_tonnes: float = 75000.0,
    origin: str = "Australia",
    destination: str = "Paradip",
    vessel_class: str = "Auto",
    risk_tolerance: str = "Medium",
    shock_override: Optional[ScenarioShock] = None
) -> Dict[str, Any]:
    """
    Main evaluation pipeline for Control Tower state.
    Computes baseline vs active state, disruption alerts, stress index, decision stability, and recommendations.
    """
    shock = shock_override if shock_override is not None else ScenarioShock()

    # 1. Baseline Optimization (Shocks = 0)
    base_res = optimize_charter_timing(
        forecast_df=forecast_df,
        cargo_type=cargo_type,
        quantity_tonnes=quantity_tonnes,
        origin=origin,
        destination=destination,
        vessel_class=vessel_class,
        risk_tolerance=risk_tolerance
    )

    if not base_res["success"]:
        return {"success": False, "error": f"Base optimizer failed: {base_res.get('error')}"}

    # 2. Apply Shocks to build Active State
    active_df = build_shocked_forecast_df(forecast_df, shock, destination)

    dem_override = None
    if shock.demurrage_rate_shock_pct != 0.0:
        base_v = base_res["best_option"]["vessel_class"]
        base_dem = VESSEL_CLASSES.get(base_v, VESSEL_CLASSES["Panamax"])["daily_demurrage_rate"]
        dem_override = base_dem * (1.0 + shock.demurrage_rate_shock_pct / 100.0)

    active_res = optimize_charter_timing(
        forecast_df=active_df,
        cargo_type=cargo_type,
        quantity_tonnes=quantity_tonnes,
        origin=origin,
        destination=destination,
        vessel_class=vessel_class,
        demurrage_rate=dem_override,
        risk_tolerance=risk_tolerance
    )

    if not active_res["success"]:
        return {"success": False, "error": f"Active state optimizer failed: {active_res.get('error')}"}

    base_opt = base_res["best_option"]
    active_opt = active_res["best_option"]

    # Calculate active signal values
    latest_row = active_df.iloc[-1] if len(active_df) > 0 else forecast_df.iloc[-1]
    
    first_rate = active_df["predicted_freight_rate"].iloc[0] if "predicted_freight_rate" in active_df.columns else 25.0
    last_rate = active_df["predicted_freight_rate"].iloc[-1] if "predicted_freight_rate" in active_df.columns else 25.0
    forecast_change_pct = ((last_rate - first_rate) / max(1.0, first_rate)) * 100.0

    port_cong = float(latest_row.get("port_congestion_score", 45.0))
    waiting_h = float(latest_row.get("avg_waiting_hours", 24.0))
    vessel_cnt = int(latest_row.get("vessel_availability_count", 25))
    weather_score = float(latest_row.get("weather_risk_score", 3.0))
    event_score = float(latest_row.get("event_risk_score", 2.0))

    # Signal Classifications
    freight_status, freight_sev = classify_signal_severity("forecast_change", forecast_change_pct)
    port_status_str, port_sev = classify_signal_severity("port_congestion", port_cong)
    vessel_status_str, vessel_sev = classify_signal_severity("vessel_availability", vessel_cnt)
    weather_status_str, weather_sev = classify_signal_severity("weather_risk", weather_score)

    signal_states = {
        "freight_market": {
            "status": freight_status,
            "severity": freight_sev,
            "signal_value": f"{forecast_change_pct:+.1f}% 14d forecast",
            "trend": "Upward" if forecast_change_pct > 0 else "Softening",
            "impact": "High" if freight_sev >= 2 else ("Medium" if freight_sev == 1 else "Low")
        },
        "port_congestion": {
            "status": port_status_str,
            "severity": port_sev,
            "signal_value": f"{port_cong:.0f} / 100",
            "waiting_hours": f"{waiting_h:.0f} h",
            "trend": "Elevated" if port_cong > 60 else "Stable",
            "impact": "High" if port_sev >= 2 else ("Medium" if port_sev == 1 else "Low")
        },
        "vessel_availability": {
            "status": vessel_status_str,
            "severity": vessel_sev,
            "signal_value": f"{vessel_cnt} vessels available",
            "trend": "Tightening" if vessel_cnt <= 15 else "Adequate",
            "impact": "High" if vessel_sev >= 2 else ("Medium" if vessel_sev == 1 else "Low")
        },
        "route_weather_risk": {
            "status": weather_status_str,
            "severity": weather_sev,
            "signal_value": f"Risk Score {weather_score + event_score:.1f} / 20",
            "trend": "Moderate Risk" if weather_score > 4 else "Low Risk",
            "impact": "High" if weather_sev >= 2 else ("Medium" if weather_sev == 1 else "Low")
        }
    }

    # Market Stress Index
    stress_idx = calculate_market_stress_index(
        forecast_change_pct=forecast_change_pct,
        port_congestion_score=port_cong,
        vessel_avail_count=vessel_cnt,
        weather_risk_score=weather_score,
        event_risk_score=event_score
    )

    # Recommendation Change Detector
    rec_changed = (
        (base_opt["charter_date"] != active_opt["charter_date"]) or
        (base_opt["destination"] != active_opt["destination"]) or
        (base_opt["vessel_class"] != active_opt["vessel_class"])
    )

    if rec_changed:
        rec_status_str = "RECOMMENDATION CHANGED"
    elif max(freight_sev, port_sev, vessel_sev, weather_sev) >= 2:
        rec_status_str = "REVIEW REQUIRED"
    else:
        rec_status_str = "RECOMMENDATION VALID"

    # Decision Stability Score
    stability_idx = calculate_decision_stability(
        market_stress_score=stress_idx["score"],
        congestion_score=port_cong,
        weather_risk_score=weather_score,
        event_risk_score=event_score,
        recommendation_changed=rec_changed
    )

    # Active Alerts
    alerts = generate_active_alerts(
        signal_states=signal_states,
        port_congestion_score=port_cong,
        vessel_avail_count=vessel_cnt,
        forecast_change_pct=forecast_change_pct,
        destination=destination
    )

    # Operational Action Guidance
    if rec_changed:
        action_text = f"Update charter recommendation to {active_opt['vessel_class']} on {active_opt['charter_date']}."
        action_why = [
            f"Market disruption altered cost balance: previous charter date ({base_opt['charter_date']}) is no longer the lowest-cost candidate.",
            f"Port congestion / risk adjustment at {destination} increased exposure by {format_inr_val(usd_to_inr(active_opt['total_logistics_cost_usd'] - base_opt['total_logistics_cost_usd']), mode='lakh')}.",
            f"Selected candidate minimizes total expected logistics cost at {format_inr_val(usd_to_inr(active_opt['total_logistics_cost_usd']))}."
        ]
        action_alt = f"Review Visakhapatnam if {destination} congestion exceeds threshold."
    elif port_sev >= 2:
        action_text = "Advance charter timing or inspect Visakhapatnam port alternative."
        action_why = [
            f"Elevated port congestion at {destination} ({port_cong:.0f}/100) increases demurrage exposure.",
            "Vessel supply remains sufficient to execute charter early.",
            "Current route remains feasible but risk buffer is reduced."
        ]
        action_alt = "Review Visakhapatnam alternative discharge berth."
    else:
        action_text = f"Maintain current charter execution window ({active_opt['charter_date']})."
        action_why = [
            "Freight rate forecasts remain stable across the decision window.",
            "Port congestion and waiting times are within normal operating tolerances.",
            f"Panamax vessel availability ({vessel_cnt} ships) is sufficient."
        ]
        action_alt = "No alternative required — maintain standard procurement plan."

    # India East Coast Port Status Table
    ports_eval = []
    for p_name in ["Paradip", "Visakhapatnam", "Kolkata/Haldia"]:
        p_cfg = PORT_CONFIG.get(p_name, PORT_CONFIG["Paradip"])
        is_dest = (p_name.lower() in destination.lower()) or (destination.lower() in p_name.lower())
        p_cong = (port_cong + (15.0 if p_name == "Kolkata/Haldia" else (-10.0 if p_name == "Visakhapatnam" else 0.0))) if is_dest else p_cfg["base_congestion_index"]
        p_cong = max(0.0, min(100.0, p_cong))
        p_wait = p_cfg["avg_laytime_hours"] * (p_cong / 50.0)

        p_status_str, _ = classify_signal_severity("port_congestion", p_cong)
        
        ports_eval.append({
            "port": p_name,
            "congestion_score": f"{p_cong:.0f}/100",
            "waiting_time": f"{p_wait:.0f} h",
            "draft_status": f"Compatible ({p_cfg['draft_limit_m']}m)" if p_cfg['draft_limit_m'] >= 14.0 else f"Restricted ({p_cfg['draft_limit_m']}m)",
            "risk_state": p_status_str,
            "recommendation_impact": "High" if p_cong > 65 else ("Medium" if p_cong > 50 else "Low")
        })

    # Route Intelligence Table
    routes_eval = []
    for r_key, r_info in ROUTES.items():
        r_dest = r_info["destination"]
        r_dist = r_info["distance_nm"]
        is_match = (r_info["origin"] == origin and r_dest == destination)
        
        r_weather = (weather_score + (1.5 if is_match else 0.0))
        r_weather = min(10.0, r_weather)

        r_status, _ = classify_signal_severity("weather_risk", r_weather)

        routes_eval.append({
            "route": r_key,
            "distance_nm": f"{r_dist:,} nm",
            "vessel_compatibility": "Capesize/Panamax/Supramax" if "Capesize" in r_info["allowed_vessels"] else "Panamax/Supramax",
            "weather_risk": f"{r_weather:.1f} / 10",
            "route_risk": "Low" if r_weather < 4.0 else "Elevated",
            "port_risk": "Elevated" if (r_dest == destination and port_cong > 65) else "Normal",
            "overall_status": r_status
        })

    # Synthetic Event Stream Log
    now_dt = datetime.datetime.now()
    event_log = [
        {
            "timestamp": (now_dt - datetime.timedelta(minutes=15)).strftime("%H:%M"),
            "event": f"{destination} congestion score updated ({port_cong:.0f}/100)",
            "severity": port_status_str,
            "impact": "High" if port_sev >= 2 else "Low"
        },
        {
            "timestamp": (now_dt - datetime.timedelta(minutes=35)).strftime("%H:%M"),
            "event": f"Panamax vessel availability updated ({vessel_cnt} ships available)",
            "severity": vessel_status_str,
            "impact": "Medium" if vessel_sev >= 2 else "Low"
        },
        {
            "timestamp": (now_dt - datetime.timedelta(minutes=55)).strftime("%H:%M"),
            "event": f"14-day freight rate outlook calculated ({forecast_change_pct:+.1f}%)",
            "severity": freight_status,
            "impact": "Medium"
        },
        {
            "timestamp": (now_dt - datetime.timedelta(minutes=80)).strftime("%H:%M"),
            "event": f"Charter recommendation status evaluated: {rec_status_str}",
            "severity": "Watch" if rec_changed else "Normal",
            "impact": "High" if rec_changed else "Low"
        }
    ]

    cost_inr = usd_to_inr(active_opt["total_logistics_cost_usd"])

    curr_rec = {
        "cargo_type": cargo_type,
        "quantity_tonnes": quantity_tonnes,
        "origin": origin,
        "destination": destination,
        "recommended_window": active_opt["charter_date"],
        "vessel_class": active_opt["vessel_class"],
        "expected_total_cost_usd": active_opt["total_logistics_cost_usd"],
        "expected_total_cost_inr_formatted": format_inr_val(cost_inr),
        "decision_confidence": active_opt.get("confidence_score", 78.0),
        "status": rec_status_str
    }

    return {
        "success": True,
        "current_recommendation": curr_rec,
        "signal_states": signal_states,
        "active_alerts": alerts,
        "port_status": ports_eval,
        "route_status": routes_eval,
        "decision_stability": stability_idx,
        "market_stress_index": stress_idx,
        "recommended_action": {
            "action": action_text,
            "why": action_why,
            "alternative": action_alt
        },
        "event_log_summary": event_log,
        "disruption_simulated": (shock_override is not None and shock_override != ScenarioShock()),
        "is_demo_data": True
    }
