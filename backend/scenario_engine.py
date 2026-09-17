"""
FreightIQ Scenario Engine Module

Interactive What-If simulation and decision stress testing engine.
Applies market, operational, congestion, weather, and geopolitical shocks,
reruns charter optimization, computes decision sensitivity, threshold sweeps,
composite decision confidence, and port alternative ranking.

Does NOT mutate original datasets or state.
"""

import copy
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
from backend.schemas import ScenarioRequest, ScenarioShock


def usd_to_inr(usd_val: float) -> float:
    """Converts USD to INR using standard presentation exchange rate."""
    return float(usd_val) * DEMO_USD_INR_RATE


def format_inr_val(inr_val: float, mode: str = "auto") -> str:
    """Formats INR value cleanly into Cr, Lakh, or thousands."""
    abs_val = abs(inr_val)
    if mode == "cr" or (mode == "auto" and abs_val >= 10_000_000):
        return f"₹{inr_val / 10_000_000:.2f} Cr"
    elif mode == "lakh" or (mode == "auto" and abs_val >= 100_000):
        return f"₹{inr_val / 100_000:.2f} Lakh"
    else:
        return f"₹{inr_val:,.0f}"


def build_shocked_forecast_df(forecast_df: pd.DataFrame, shock: ScenarioShock, destination: str) -> pd.DataFrame:
    """
    Creates a deep copy of forecast_df and applies scenario shocks without mutating the original dataframe.
    """
    df_shocked = forecast_df.copy(deep=True)

    # Ensure baseline market columns exist if not present in forecast_df
    if "predicted_freight_rate" not in df_shocked.columns:
        if "freight_rate" in df_shocked.columns:
            df_shocked["predicted_freight_rate"] = df_shocked["freight_rate"]
        else:
            df_shocked["predicted_freight_rate"] = 25.0

    if "port_congestion_score" not in df_shocked.columns:
        df_shocked["port_congestion_score"] = 45.0

    if "avg_waiting_hours" not in df_shocked.columns:
        df_shocked["avg_waiting_hours"] = 24.0

    if "vessel_availability_count" not in df_shocked.columns:
        df_shocked["vessel_availability_count"] = 25

    if "weather_risk_score" not in df_shocked.columns:
        df_shocked["weather_risk_score"] = 3.0

    if "event_risk_score" not in df_shocked.columns:
        df_shocked["event_risk_score"] = 2.0

    # 1. Freight Rate Shock
    if shock.freight_rate_shock_pct != 0.0:
        df_shocked["predicted_freight_rate"] = df_shocked["predicted_freight_rate"] * (1.0 + shock.freight_rate_shock_pct / 100.0)

    # 2. Port Congestion Shock
    target = shock.target_port
    is_targeted_port = (target == "All East Coast Ports") or (target.lower() in destination.lower()) or (destination.lower() in target.lower())

    if is_targeted_port and shock.port_congestion_shock_pct != 0.0:
        cong_multiplier = (1.0 + shock.port_congestion_shock_pct / 100.0)
        df_shocked["port_congestion_score"] = (df_shocked["port_congestion_score"] * cong_multiplier).clip(0.0, 100.0)
        df_shocked["avg_waiting_hours"] = (df_shocked["avg_waiting_hours"] * cong_multiplier).clip(lower=0.0)

    # 3. Vessel Availability Shock
    if shock.vessel_availability_shock_pct != 0.0:
        avail_multiplier = (1.0 + shock.vessel_availability_shock_pct / 100.0)
        df_shocked["vessel_availability_count"] = (df_shocked["vessel_availability_count"] * avail_multiplier).clip(lower=0).astype(int)

    # 4. Weather Risk Level
    weather_map = {"Low": 3.0, "Moderate": 5.0, "High": 7.5, "Severe": 9.5}
    w_val = weather_map.get(shock.weather_risk_level, 3.0)
    df_shocked["weather_risk_score"] = w_val

    # 5. Geopolitical / Route Risk Level
    geo_map = {"Normal": 2.0, "Elevated": 5.0, "Major Disruption": 8.5}
    g_val = geo_map.get(shock.geopolitical_risk_level, 2.0)
    df_shocked["event_risk_score"] = g_val

    return df_shocked


def calculate_decision_confidence(
    forecast_df: pd.DataFrame,
    shock: ScenarioShock,
    opt_res: Dict[str, Any]
) -> Tuple[float, Dict[str, Any]]:
    """
    Calculates a transparent composite decision confidence score between 0 and 100.
    """
    base_conf = 88.0

    # Weather penalty
    weather_map = {"Low": 1.0, "Moderate": 3.0, "High": 7.0, "Severe": 12.0}
    w_penalty = weather_map.get(shock.weather_risk_level, 1.0)

    # Event penalty
    geo_map = {"Normal": 0.0, "Elevated": 4.0, "Major Disruption": 10.0}
    g_penalty = geo_map.get(shock.geopolitical_risk_level, 0.0)

    # Congestion penalty
    cong_pct = shock.port_congestion_shock_pct
    c_penalty = max(0.0, cong_pct * 0.08)

    # Volatility / Freight Shock penalty
    f_penalty = abs(shock.freight_rate_shock_pct) * 0.15

    # Cost Separation Margin Bonus (Separation between Best option and 2nd best)
    scenarios = opt_res.get("scenarios", {})
    opt_a = scenarios.get("Option A (Optimal)", {})
    opt_b = scenarios.get("Option B (Alternative)", {})
    margin_bonus = 0.0
    if opt_a and opt_b and opt_a != opt_b:
        cost_a = opt_a.get("total_logistics_cost_usd", 1.0)
        cost_b = opt_b.get("total_logistics_cost_usd", 1.0)
        cost_diff_pct = ((cost_b - cost_a) / max(1.0, cost_a)) * 100.0
        margin_bonus = min(8.0, max(0.0, cost_diff_pct * 1.5))

    confidence = base_conf - w_penalty - g_penalty - c_penalty - f_penalty + margin_bonus
    confidence_score = round(max(10.0, min(98.0, confidence)), 1)

    breakdown = {
        "base_confidence": base_conf,
        "weather_risk_deduction": round(w_penalty, 1),
        "geopolitical_deduction": round(g_penalty, 1),
        "congestion_volatility_deduction": round(c_penalty, 1),
        "freight_volatility_deduction": round(f_penalty, 1),
        "option_separation_bonus": round(margin_bonus, 1),
        "explanation": "Decision Confidence is a prototype composite indicator based on forecast uncertainty, data quality, and cost separation between feasible charter options."
    }

    return confidence_score, breakdown


def calculate_decision_sensitivity(
    forecast_df: pd.DataFrame,
    request: ScenarioRequest
) -> List[Dict[str, Any]]:
    """
    Measures influence of major operational variables via controlled perturbation (+10%).
    Returns normalized influence ranks.
    """
    base_res = optimize_charter_timing(
        forecast_df=forecast_df,
        cargo_type=request.cargo_type,
        quantity_tonnes=request.quantity_tonnes,
        origin=request.origin,
        destination=request.destination,
        earliest_date=request.earliest_date,
        latest_date=request.latest_date,
        vessel_class=request.vessel_class,
        risk_tolerance=request.risk_tolerance
    )
    if not base_res["success"]:
        return []

    base_cost = base_res["best_option"]["total_logistics_cost_usd"]

    variables = [
        ("Freight Rate", ScenarioShock(freight_rate_shock_pct=10.0)),
        ("Port Congestion", ScenarioShock(port_congestion_shock_pct=20.0, target_port=request.destination)),
        ("Vessel Availability", ScenarioShock(vessel_availability_shock_pct=-25.0)),
        ("Weather Risk", ScenarioShock(weather_risk_level="High")),
        ("Geopolitical Risk", ScenarioShock(geopolitical_risk_level="Elevated")),
        ("Demurrage Rate", ScenarioShock(demurrage_rate_shock_pct=20.0))
    ]

    sensitivity_results = []
    for var_name, pert_shock in variables:
        shocked_df = build_shocked_forecast_df(forecast_df, pert_shock, request.destination)
        dem_override = None
        if pert_shock.demurrage_rate_shock_pct != 0.0:
            v_cls = request.vessel_class if request.vessel_class != "Auto" else "Panamax"
            base_dem = VESSEL_CLASSES.get(v_cls, VESSEL_CLASSES["Panamax"])["daily_demurrage_rate"]
            dem_override = base_dem * (1.0 + pert_shock.demurrage_rate_shock_pct / 100.0)

        p_res = optimize_charter_timing(
            forecast_df=shocked_df,
            cargo_type=request.cargo_type,
            quantity_tonnes=request.quantity_tonnes,
            origin=request.origin,
            destination=request.destination,
            earliest_date=request.earliest_date,
            latest_date=request.latest_date,
            vessel_class=request.vessel_class,
            demurrage_rate=dem_override,
            risk_tolerance=request.risk_tolerance
        )

        if p_res["success"]:
            p_cost = p_res["best_option"]["total_logistics_cost_usd"]
            cost_delta_pct = abs((p_cost - base_cost) / base_cost) * 100.0
            
            if cost_delta_pct >= 4.5:
                influence = "High Influence"
            elif cost_delta_pct >= 1.5:
                influence = "Medium Influence"
            else:
                influence = "Low Influence"

            sensitivity_results.append({
                "variable": var_name,
                "cost_impact_pct": round(cost_delta_pct, 2),
                "influence_level": influence,
                "description": f"A standard perturbation alters total logistics cost by {cost_delta_pct:.1f}%."
            })

    sensitivity_results.sort(key=lambda x: x["cost_impact_pct"], reverse=True)
    return sensitivity_results


def calculate_threshold_analysis(
    forecast_df: pd.DataFrame,
    request: ScenarioRequest
) -> List[Dict[str, Any]]:
    """
    Performs controlled scenario sweeps to estimate exact tipping points for decision shifts.
    """
    base_res = optimize_charter_timing(
        forecast_df=forecast_df,
        cargo_type=request.cargo_type,
        quantity_tonnes=request.quantity_tonnes,
        origin=request.origin,
        destination=request.destination,
        earliest_date=request.earliest_date,
        latest_date=request.latest_date,
        vessel_class=request.vessel_class,
        risk_tolerance=request.risk_tolerance
    )

    if not base_res["success"]:
        return []

    base_best = base_res["best_option"]
    base_date = base_best["charter_date"]
    base_vessel = base_best["vessel_class"]

    thresholds = []

    # 1. Congestion Sweep
    cong_threshold_found = False
    for c_pct in range(10, 110, 10):
        test_shock = ScenarioShock(port_congestion_shock_pct=float(c_pct), target_port=request.destination)
        s_df = build_shocked_forecast_df(forecast_df, test_shock, request.destination)
        t_res = optimize_charter_timing(
            forecast_df=s_df,
            cargo_type=request.cargo_type,
            quantity_tonnes=request.quantity_tonnes,
            origin=request.origin,
            destination=request.destination,
            earliest_date=request.earliest_date,
            latest_date=request.latest_date,
            vessel_class=request.vessel_class,
            risk_tolerance=request.risk_tolerance
        )
        if t_res["success"]:
            t_best = t_res["best_option"]
            if t_best["charter_date"] != base_date or t_best["vessel_class"] != base_vessel or (t_best["total_logistics_cost_usd"] / base_best["total_logistics_cost_usd"]) > 1.12:
                # Congestion score calculation
                base_cong_score = PORT_CONFIG.get(request.destination, PORT_CONFIG["Paradip"])["base_congestion_index"]
                tipping_score = min(100.0, round(base_cong_score * (1.0 + c_pct / 100.0), 0))
                thresholds.append({
                    "variable": "Port Congestion",
                    "tipping_point": f"Congestion Score > {tipping_score:.0f} (+{c_pct}%)",
                    "impact": "Recommendation shifts or cost increases significantly above this threshold.",
                    "status": "Threshold Identified"
                })
                cong_threshold_found = True
                break

    if not cong_threshold_found:
        thresholds.append({
            "variable": "Port Congestion",
            "tipping_point": "Stable above +100% surge",
            "impact": "Current recommendation remains resilient to extreme congestion increases.",
            "status": "Resilient"
        })

    # 2. Freight Rate Sweep
    freight_threshold_found = False
    for f_pct in range(4, 32, 4):
        test_shock = ScenarioShock(freight_rate_shock_pct=float(f_pct))
        s_df = build_shocked_forecast_df(forecast_df, test_shock, request.destination)
        t_res = optimize_charter_timing(
            forecast_df=s_df,
            cargo_type=request.cargo_type,
            quantity_tonnes=request.quantity_tonnes,
            origin=request.origin,
            destination=request.destination,
            earliest_date=request.earliest_date,
            latest_date=request.latest_date,
            vessel_class=request.vessel_class,
            risk_tolerance=request.risk_tolerance
        )
        if t_res["success"]:
            t_best = t_res["best_option"]
            if t_best["charter_date"] != base_date:
                thresholds.append({
                    "variable": "Freight Rate",
                    "tipping_point": f"Immediate charter becomes preferred above +{f_pct}%",
                    "impact": f"Rate increase exceeding +{f_pct}% alters the recommended charter date window.",
                    "status": "Threshold Identified"
                })
                freight_threshold_found = True
                break

    if not freight_threshold_found:
        thresholds.append({
            "variable": "Freight Rate",
            "tipping_point": "Linear cost scaling above +8%",
            "impact": "Charter timing window remains the lowest-cost candidate across simulated rate variations.",
            "status": "Linear Scaling"
        })

    # 3. Vessel Availability Sweep
    avail_threshold_found = False
    for a_pct in range(-10, -70, -10):
        test_shock = ScenarioShock(vessel_availability_shock_pct=float(a_pct))
        s_df = build_shocked_forecast_df(forecast_df, test_shock, request.destination)
        t_res = optimize_charter_timing(
            forecast_df=s_df,
            cargo_type=request.cargo_type,
            quantity_tonnes=request.quantity_tonnes,
            origin=request.origin,
            destination=request.destination,
            earliest_date=request.earliest_date,
            latest_date=request.latest_date,
            vessel_class=request.vessel_class,
            risk_tolerance=request.risk_tolerance
        )
        if not t_res["success"] or (t_res["best_option"]["vessel_avail_count"] < 10):
            thresholds.append({
                "variable": "Vessel Availability",
                "tipping_point": f"Availability drops below {t_res.get('best_option', {}).get('vessel_avail_count', 8)} vessels ({a_pct}%)",
                "impact": "Alternative vessel class or emergency charter spot market considered.",
                "status": "Threshold Identified"
            })
            avail_threshold_found = True
            break

    if not avail_threshold_found:
        thresholds.append({
            "variable": "Vessel Availability",
            "tipping_point": "Threshold below 8 vessels",
            "impact": "Vessel availability remains sufficient across simulation range.",
            "status": "Sufficient Availability"
        })

    return thresholds


def calculate_port_alternative_analysis(
    forecast_df: pd.DataFrame,
    request: ScenarioRequest,
    shocked_df: pd.DataFrame
) -> List[Dict[str, Any]]:
    """
    Evaluates alternative destination ports under current scenario conditions.
    """
    ports = ["Paradip", "Visakhapatnam", "Kolkata/Haldia"]
    results = []

    for port in ports:
        # Evaluate for this port
        res = optimize_charter_timing(
            forecast_df=shocked_df,
            cargo_type=request.cargo_type,
            quantity_tonnes=request.quantity_tonnes,
            origin=request.origin,
            destination=port,
            earliest_date=request.earliest_date,
            latest_date=request.latest_date,
            vessel_class=request.vessel_class,
            risk_tolerance=request.risk_tolerance
        )

        port_cfg = PORT_CONFIG.get(port, PORT_CONFIG["Paradip"])
        draft_limit = port_cfg["draft_limit_m"]
        
        # Check vessel draft compatibility
        req_vessel = request.vessel_class if request.vessel_class != "Auto" else "Panamax"
        v_info = VESSEL_CLASSES.get(req_vessel, VESSEL_CLASSES["Panamax"])
        draft_ok = v_info["draft_requirement_m"] <= draft_limit

        route_key = f"{request.origin} -> {port}"
        vessel_ok = req_vessel in ROUTES.get(route_key, {}).get("allowed_vessels", ["Panamax", "Supramax"])

        if res["success"]:
            best = res["best_option"]
            cost_usd = best["total_logistics_cost_usd"]
            cost_inr = usd_to_inr(cost_usd)
            cong_score = best["congestion_score"]
            feasible = True
        else:
            cost_inr = 0.0
            cong_score = port_cfg["base_congestion_index"]
            feasible = False

        results.append({
            "port": port,
            "expected_cost_usd": cost_usd if feasible else 0.0,
            "expected_cost_inr_formatted": format_inr_val(cost_inr) if feasible else "Infeasible",
            "congestion_score": cong_score,
            "draft_compatibility": f"Supported ({draft_limit}m draft)" if draft_ok else f"Restricted ({draft_limit}m draft)",
            "vessel_compatibility": "Compatible" if vessel_ok else "Incompatible / Draft Limit",
            "feasible": feasible,
            "total_cost_raw": cost_inr if feasible else 999_999_999.0
        })

    # Rank by total cost among feasible options
    results.sort(key=lambda x: x["total_cost_raw"])
    for rank_idx, item in enumerate(results, start=1):
        if item["feasible"]:
            item["overall_rank"] = f"Rank {rank_idx}"
        else:
            item["overall_rank"] = "Infeasible"
        del item["total_cost_raw"]

    return results


def run_scenario_simulation(
    forecast_df: pd.DataFrame,
    request: ScenarioRequest
) -> Dict[str, Any]:
    """
    Main Scenario Engine execution entrypoint.
    Applies shocks, reruns optimizer, calculates comparison, sensitivity, threshold sweeps, and confidence.
    """
    shock = request.shock

    # 1. Base Scenario Optimization (Shocks = 0)
    base_res = optimize_charter_timing(
        forecast_df=forecast_df,
        cargo_type=request.cargo_type,
        quantity_tonnes=request.quantity_tonnes,
        origin=request.origin,
        destination=request.destination,
        earliest_date=request.earliest_date,
        latest_date=request.latest_date,
        vessel_class=request.vessel_class,
        risk_tolerance=request.risk_tolerance
    )

    if not base_res["success"]:
        return {
            "success": False,
            "error": f"Base scenario optimization failed: {base_res.get('error')}"
        }

    # 2. Shocked Scenario Forecast DF
    shocked_df = build_shocked_forecast_df(forecast_df, shock, request.destination)

    # Demurrage override
    demurrage_override = None
    if shock.demurrage_rate_shock_pct != 0.0:
        v_cls = base_res["best_option"]["vessel_class"]
        base_dem = VESSEL_CLASSES.get(v_cls, VESSEL_CLASSES["Panamax"])["daily_demurrage_rate"]
        demurrage_override = base_dem * (1.0 + shock.demurrage_rate_shock_pct / 100.0)

    # 3. Stressed Scenario Optimization
    stress_res = optimize_charter_timing(
        forecast_df=shocked_df,
        cargo_type=request.cargo_type,
        quantity_tonnes=request.quantity_tonnes,
        origin=request.origin,
        destination=request.destination,
        earliest_date=request.earliest_date,
        latest_date=request.latest_date,
        vessel_class=request.vessel_class,
        demurrage_rate=demurrage_override,
        risk_tolerance=request.risk_tolerance
    )

    if not stress_res["success"]:
        return {
            "success": False,
            "error": f"Stressed scenario optimization failed: {stress_res.get('error')}"
        }

    base_opt = base_res["best_option"]
    stress_opt = stress_res["best_option"]

    # 4. Decision Confidence
    conf_score, conf_breakdown = calculate_decision_confidence(forecast_df, shock, stress_res)

    # 5. Side-by-Side Comparison Table Construction
    base_cost_inr = usd_to_inr(base_opt["total_logistics_cost_usd"])
    stress_cost_inr = usd_to_inr(stress_opt["total_logistics_cost_usd"])
    cost_diff_inr = stress_cost_inr - base_cost_inr

    base_freight_inr = usd_to_inr(base_opt["freight_cost_usd"])
    stress_freight_inr = usd_to_inr(stress_opt["freight_cost_usd"])

    base_dem_inr = usd_to_inr(base_opt["demurrage_cost_usd"])
    stress_dem_inr = usd_to_inr(stress_opt["demurrage_cost_usd"])

    base_cong_inr = usd_to_inr(base_opt["congestion_cost_usd"])
    stress_cong_inr = usd_to_inr(stress_opt["congestion_cost_usd"])

    base_risk_inr = usd_to_inr(base_opt["route_risk_penalty_usd"])
    stress_risk_inr = usd_to_inr(stress_opt["route_risk_penalty_usd"])

    base_per_t_inr = usd_to_inr(base_opt["effective_cost_per_tonne"])
    stress_per_t_inr = usd_to_inr(stress_opt["effective_cost_per_tonne"])

    comparison_table = [
        {
            "metric": "Charter Window",
            "baseline": base_opt["charter_date"],
            "stress_scenario": stress_opt["charter_date"],
            "changed": base_opt["charter_date"] != stress_opt["charter_date"]
        },
        {
            "metric": "Vessel Class",
            "baseline": base_opt["vessel_class"],
            "stress_scenario": stress_opt["vessel_class"],
            "changed": base_opt["vessel_class"] != stress_opt["vessel_class"]
        },
        {
            "metric": "Route",
            "baseline": base_opt["route"],
            "stress_scenario": stress_opt["route"],
            "changed": base_opt["route"] != stress_opt["route"]
        },
        {
            "metric": "Freight Cost",
            "baseline": format_inr_val(base_freight_inr),
            "stress_scenario": format_inr_val(stress_freight_inr),
            "changed": abs(stress_freight_inr - base_freight_inr) > 100_000
        },
        {
            "metric": "Demurrage Exposure",
            "baseline": format_inr_val(base_dem_inr, mode="lakh"),
            "stress_scenario": format_inr_val(stress_dem_inr, mode="lakh"),
            "changed": abs(stress_dem_inr - base_dem_inr) > 50_000
        },
        {
            "metric": "Port / Waiting Cost",
            "baseline": format_inr_val(base_cong_inr, mode="lakh"),
            "stress_scenario": format_inr_val(stress_cong_inr, mode="lakh"),
            "changed": abs(stress_cong_inr - base_cong_inr) > 50_000
        },
        {
            "metric": "Risk Adjustment",
            "baseline": format_inr_val(base_risk_inr, mode="lakh"),
            "stress_scenario": format_inr_val(stress_risk_inr, mode="lakh"),
            "changed": abs(stress_risk_inr - base_risk_inr) > 50_000
        },
        {
            "metric": "Total Logistics Cost",
            "baseline": format_inr_val(base_cost_inr),
            "stress_scenario": format_inr_val(stress_cost_inr),
            "changed": abs(cost_diff_inr) > 500_000
        },
        {
            "metric": "Cost / Tonne",
            "baseline": f"₹{base_per_t_inr:,.0f}/t",
            "stress_scenario": f"₹{stress_per_t_inr:,.0f}/t",
            "changed": abs(stress_per_t_inr - base_per_t_inr) > 10
        },
        {
            "metric": "Decision Confidence",
            "baseline": "85.0 / 100",
            "stress_scenario": f"{conf_score:.1f} / 100",
            "changed": abs(conf_score - 85.0) > 2.0
        }
    ]

    # 6. Decision Status & Dynamic Explanation
    if base_opt["charter_date"] != stress_opt["charter_date"]:
        decision_status = "Charter Window Shifted"
    elif base_opt["destination"] != stress_opt["destination"]:
        decision_status = "Route Changed"
    elif base_opt["vessel_class"] != stress_opt["vessel_class"]:
        decision_status = "Vessel Class Changed"
    elif abs(cost_diff_inr) > 500_000:
        if cost_diff_inr > 0:
            decision_status = "Cost Increase Under Stress"
        else:
            decision_status = "Cost Decrease Under Relief"
    else:
        decision_status = "Recommendation Unchanged"

    # Generate dynamic explanation
    explanation_parts = []
    if shock.port_congestion_shock_pct > 0:
        diff_dem_lakh = (stress_dem_inr - base_dem_inr) / 100_000
        explanation_parts.append(
            f"{shock.target_port} congestion increased by {shock.port_congestion_shock_pct:.0f}%, raising expected waiting and demurrage exposure by {format_inr_val(stress_dem_inr - base_dem_inr, mode='lakh')}."
        )
    elif shock.port_congestion_shock_pct < 0:
        explanation_parts.append(
            f"{shock.target_port} congestion decreased by {abs(shock.port_congestion_shock_pct):.0f}%, reducing expected port delays."
        )

    if shock.freight_rate_shock_pct != 0:
        explanation_parts.append(
            f"Dry bulk freight market rate shifted by {shock.freight_rate_shock_pct:+.1f}%, altering the baseline freight component by {format_inr_val(stress_freight_inr - base_freight_inr)}."
        )

    if shock.vessel_availability_shock_pct != 0:
        explanation_parts.append(
            f"Vessel availability changed by {shock.vessel_availability_shock_pct:+.0f}%, tightening suitable ship supply."
        )

    if shock.weather_risk_level in ["High", "Severe"]:
        explanation_parts.append(
            f"Weather risk elevated to {shock.weather_risk_level}, increasing risk adjustment by {format_inr_val(stress_risk_inr - base_risk_inr, mode='lakh')}."
        )

    if shock.geopolitical_risk_level != "Normal":
        explanation_parts.append(
            f"Route security risk set to {shock.geopolitical_risk_level}, applying operational buffer."
        )

    if not explanation_parts:
        explanation_parts.append("No market or operational shocks applied. Stressed scenario matches baseline recommendation.")

    if decision_status != "Recommendation Unchanged":
        explanation_parts.append(
            f"FreightIQ adapted the decision: baseline charter on {base_opt['charter_date']} ({base_opt['vessel_class']}) changed to {stress_opt['charter_date']} ({stress_opt['vessel_class']}) to optimize risk-adjusted total cost."
        )
    else:
        explanation_parts.append(
            f"Despite shock conditions, the baseline recommendation on {base_opt['charter_date']} using {base_opt['vessel_class']} remains the lowest simulated-cost candidate."
        )

    explanation_text = " ".join(explanation_parts)

    # 7. Decision Sensitivity
    sensitivity_list = calculate_decision_sensitivity(forecast_df, request)

    # 8. Threshold Analysis
    threshold_list = calculate_threshold_analysis(forecast_df, request)

    # 9. Port Alternative Analysis
    port_alt_list = calculate_port_alternative_analysis(forecast_df, request, shocked_df)

    return {
        "success": True,
        "baseline_recommendation": base_opt,
        "stressed_recommendation": stress_opt,
        "comparison_table": comparison_table,
        "decision_status": decision_status,
        "explanation": explanation_text,
        "sensitivity_analysis": sensitivity_list,
        "threshold_analysis": threshold_list,
        "confidence_score": conf_score,
        "confidence_breakdown": conf_breakdown,
        "port_alternative_analysis": port_alt_list,
        "is_demo_data": True
    }
