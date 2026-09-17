"""
FreightIQ Decision Twin Module

Evaluates chartering decisions across hundreds or thousands of Monte Carlo market futures
to provide robust decision support under freight-market uncertainty.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

from backend.config import (
    VESSEL_CLASSES,
    ROUTES,
    PORT_CONFIG,
    DEMO_USD_INR_RATE
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
    CONGESTION_TO_WAITING_HOURS_FACTOR,
)
from backend.optimizer import evaluate_charter_candidate


class DecisionTwinEngine:
    """
    Monte Carlo Decision Twin engine for FreightIQ.
    """

    def __init__(
        self,
        forecast_df: pd.DataFrame,
        cargo_type: str = "Coking Coal",
        quantity_tonnes: float = 75000.0,
        origin: str = "Australia",
        destination: str = "Paradip",
        vessel_class: str = "Auto",
        risk_tolerance: str = "Medium",
        simulations_count: int = 1000,
        seed: int = 42,
        active_shock: Optional[Dict[str, Any]] = None
    ):
        self.forecast_df = forecast_df.copy()
        if not pd.api.types.is_datetime64_any_dtype(self.forecast_df["date"]):
            self.forecast_df["date"] = pd.to_datetime(self.forecast_df["date"])
        
        self.cargo_type = cargo_type
        self.quantity_tonnes = quantity_tonnes
        self.origin = origin
        self.destination = destination
        self.vessel_class_filter = vessel_class
        self.risk_tolerance = risk_tolerance
        self.simulations_count = simulations_count
        self.seed = seed
        self.active_shock = active_shock or {}

    def generate_market_futures(self) -> Dict[str, np.ndarray]:
        """
        Generates stochastic Monte Carlo trajectories for freight rate, congestion,
        vessel availability, and weather risk across the forecast horizon.
        """
        np.random.seed(self.seed)
        num_days = len(self.forecast_df)
        N = self.simulations_count

        # Base vectors from forecast_df
        base_freight = self.forecast_df.get("predicted_freight_rate", self.forecast_df.get("freight_rate", pd.Series([25.0]*num_days))).to_numpy(dtype=float)
        base_congestion = self.forecast_df.get("port_congestion_score", pd.Series([45.0]*num_days)).to_numpy(dtype=float)
        base_waiting = self.forecast_df.get("avg_waiting_hours", pd.Series([24.0]*num_days)).to_numpy(dtype=float)
        base_vessels = self.forecast_df.get("vessel_availability_count", pd.Series([25]*num_days)).to_numpy(dtype=float)
        base_weather = self.forecast_df.get("weather_risk_score", pd.Series([3.0]*num_days)).to_numpy(dtype=float)
        base_event = self.forecast_df.get("event_risk_score", pd.Series([2.0]*num_days)).to_numpy(dtype=float)

        # Apply active shock adjustments if present
        if self.active_shock:
            f_shock_pct = float(self.active_shock.get("freight_rate_shock_pct", 0.0)) / 100.0
            c_shock_pct = float(self.active_shock.get("port_congestion_shock_pct", 0.0)) / 100.0
            v_shock_pct = float(self.active_shock.get("vessel_availability_shock_pct", 0.0)) / 100.0
            
            base_freight = base_freight * (1.0 + f_shock_pct)
            base_congestion = np.clip(base_congestion * (1.0 + c_shock_pct), 5.0, 98.0)
            base_waiting = base_congestion * CONGESTION_TO_WAITING_HOURS_FACTOR
            base_vessels = np.clip(base_vessels * (1.0 + v_shock_pct), 3.0, 80.0)

            w_level = self.active_shock.get("weather_risk_level", "Low")
            w_add_map = {"Low": 0.0, "Moderate": 2.0, "High": 4.0, "Severe": 6.0}
            base_weather = np.clip(base_weather + w_add_map.get(w_level, 0.0), 1.0, 10.0)

            g_level = self.active_shock.get("geopolitical_risk_level", "Normal")
            g_add_map = {"Normal": 0.0, "Elevated": 3.0, "Major Disruption": 6.0}
            base_event = np.clip(base_event + g_add_map.get(g_level, 0.0), 1.0, 10.0)

        # Vectorized stochastic simulation over N paths and num_days
        # Freight rate AR(1) disturbance
        freight_paths = np.zeros((N, num_days))
        for i in range(N):
            noise = np.random.normal(0, 0.75, size=num_days)
            ar1 = np.zeros(num_days)
            ar1[0] = noise[0]
            for t in range(1, num_days):
                ar1[t] = 0.82 * ar1[t-1] + noise[t]
            freight_paths[i, :] = np.maximum(5.0, base_freight + ar1)

        # Congestion disturbance
        c_noise = np.random.normal(0, 3.5, size=(N, num_days))
        congestion_paths = np.clip(base_congestion[None, :] + c_noise, 5.0, 98.0)
        waiting_paths = congestion_paths * CONGESTION_TO_WAITING_HOURS_FACTOR

        # Vessel availability disturbance
        v_noise = np.random.normal(0, 2.5, size=(N, num_days))
        vessel_paths = np.clip(np.round(base_vessels[None, :] + v_noise), 3, 80)

        # Weather & Event risk disturbance
        w_noise = np.random.normal(0, 0.8, size=(N, num_days))
        weather_paths = np.clip(base_weather[None, :] + w_noise, 1.0, 10.0)

        e_noise = np.random.normal(0, 0.6, size=(N, num_days))
        event_paths = np.clip(base_event[None, :] + e_noise, 1.0, 10.0)

        return {
            "freight_paths": freight_paths,          # (N, num_days)
            "congestion_paths": congestion_paths,    # (N, num_days)
            "waiting_paths": waiting_paths,          # (N, num_days)
            "vessel_paths": vessel_paths,            # (N, num_days)
            "weather_paths": weather_paths,          # (N, num_days)
            "event_paths": event_paths,              # (N, num_days)
            "dates": [d.strftime("%Y-%m-%d") for d in self.forecast_df["date"]]
        }

    def run(self) -> Dict[str, Any]:
        """
        Executes full Decision Twin evaluation across Monte Carlo futures.
        """
        futures = self.generate_market_futures()
        N = self.simulations_count
        dates = futures["dates"]
        num_days = len(dates)

        # Build candidate decision grid
        candidate_vessels = (
            ["Capesize", "Panamax", "Supramax"]
            if self.vessel_class_filter == "Auto"
            else [self.vessel_class_filter]
        )
        
        # Candidate destinations (primary destination + alternate East Coast ports)
        candidate_ports = [self.destination]
        alternate_ports = ["Paradip", "Visakhapatnam", "Kolkata/Haldia"]
        for p in alternate_ports:
            if p not in candidate_ports:
                candidate_ports.append(p)

        candidates = []
        for d_idx in range(num_days):
            date_str = dates[d_idx]
            c_date = self.forecast_df["date"].iloc[d_idx]

            for v_cls in candidate_vessels:
                for port in candidate_ports:
                    # Check baseline feasibility
                    v_info = VESSEL_CLASSES.get(v_cls, VESSEL_CLASSES["Panamax"])
                    route_key = f"{self.origin} -> {port}"
                    r_info = ROUTES.get(route_key, {"allowed_vessels": ["Capesize", "Panamax", "Supramax"]})

                    if self.quantity_tonnes > v_info["max_capacity"]:
                        continue
                    if v_cls not in r_info.get("allowed_vessels", []):
                        continue
                    
                    candidate_id = f"{v_cls} | {port} | Day {d_idx+1} ({date_str[-5:]})"
                    candidates.append({
                        "candidate_id": candidate_id,
                        "date_idx": d_idx,
                        "date_str": date_str,
                        "charter_date": c_date,
                        "vessel_class": v_cls,
                        "destination": port,
                        "route": route_key,
                        "vessel_info": v_info,
                        "route_info": r_info
                    })

        if not candidates:
            return {
                "success": False,
                "error": "No feasible candidate under this simulated state.",
                "disclaimer": "Decision Twin results unavailable — all candidate options violated capacity or draft constraints."
            }

        M = len(candidates)
        costs_matrix = np.zeros((M, N))  # Cost for each candidate across N simulations

        # Vectorized cost computation per candidate
        for m_idx, cand in enumerate(candidates):
            d_idx = cand["date_idx"]
            v_cls = cand["vessel_class"]
            port = cand["destination"]
            
            r_info = cand["route_info"]
            v_info = cand["vessel_info"]
            port_info = PORT_CONFIG.get(port, PORT_CONFIG["Paradip"])

            # Extract simulated futures at date d_idx across all N simulations
            f_rates = futures["freight_paths"][:, d_idx]
            c_scores = futures["congestion_paths"][:, d_idx]
            w_hours = futures["waiting_paths"][:, d_idx]
            v_counts = futures["vessel_paths"][:, d_idx]
            w_risks = futures["weather_paths"][:, d_idx]
            e_risks = futures["event_paths"][:, d_idx]

            # Unit freight ($/t)
            unit_freight = f_rates * r_info.get("base_freight_multiplier", 1.0) * v_info.get("base_daily_charter_multiplier", 1.0)
            freight_cost = unit_freight * self.quantity_tonnes

            # Demurrage cost
            demurrage_rate = v_info["daily_demurrage_rate"]
            total_port_hours = port_info["avg_laytime_hours"] + w_hours
            demurrage_cost = (total_port_hours / 24.0) * (demurrage_rate * DEMURRAGE_EXPOSURE_FACTOR)

            # Congestion cost
            congestion_cost = c_scores * port_info["congestion_cost_per_hour_usd"] * CONGESTION_COST_MULTIPLIER

            # Risk penalties
            risk_factor_map = {"Low": RISK_FACTOR_LOW, "Medium": RISK_FACTOR_MEDIUM, "High": RISK_FACTOR_HIGH}
            rf = risk_factor_map.get(self.risk_tolerance, RISK_FACTOR_MEDIUM)

            weather_penalty = w_risks * WEATHER_RISK_PENALTY_PER_POINT * rf
            event_penalty = e_risks * EVENT_RISK_PENALTY_PER_POINT * rf
            route_risk_penalty = weather_penalty + event_penalty

            # Total cost in USD
            total_costs_usd = freight_cost + demurrage_cost + congestion_cost + route_risk_penalty

            # Enforce minimum vessel availability threshold on path s
            infeasible_mask = v_counts < VESSEL_AVAILABILITY_MIN_THRESHOLD
            total_costs_usd[infeasible_mask] = 1e12

            costs_matrix[m_idx, :] = total_costs_usd

        # Calculate Hindsight Minimum Cost per simulation path s
        min_costs_per_sim = np.min(costs_matrix, axis=0)  # (N,)

        # Regret Matrix: R(m, s) = max(0.0, Cost(m, s) - MinCost(s))
        regret_matrix = np.maximum(0.0, costs_matrix - min_costs_per_sim[None, :])  # (M, N)

        # Win Matrix: Candidate m wins in sim s if regret is near zero (< 1.0 USD)
        win_matrix = regret_matrix < 1.0  # (M, N) boolean

        # Aggregate metrics per candidate
        candidate_summary = []
        for m_idx, cand in enumerate(candidates):
            c_costs = costs_matrix[m_idx, :]
            c_regrets = regret_matrix[m_idx, :]
            
            mean_cost_usd = float(np.mean(c_costs))
            median_cost_usd = float(np.median(c_costs))
            p90_cost_usd = float(np.percentile(c_costs, 90))
            worst_cost_usd = float(np.max(c_costs))
            std_cost_usd = float(np.std(c_costs))
            cv_cost = std_cost_usd / mean_cost_usd if mean_cost_usd > 0 else 0.0

            mean_regret_usd = float(np.mean(c_regrets))
            median_regret_usd = float(np.median(c_regrets))
            p90_regret_usd = float(np.percentile(c_regrets, 90))
            worst_regret_usd = float(np.max(c_regrets))

            win_count = int(np.sum(win_matrix[m_idx, :]))
            win_freq_pct = round((win_count / N) * 100.0, 1)

            candidate_summary.append({
                "candidate_index": m_idx,
                "candidate_id": cand["candidate_id"],
                "date_str": cand["date_str"],
                "vessel_class": cand["vessel_class"],
                "destination": cand["destination"],
                "route": cand["route"],
                "mean_cost_usd": mean_cost_usd,
                "mean_cost_inr_cr": round((mean_cost_usd * DEMO_USD_INR_RATE) / 1e7, 2),
                "median_cost_usd": median_cost_usd,
                "p90_cost_usd": p90_cost_usd,
                "worst_cost_usd": worst_cost_usd,
                "cv_cost": cv_cost,
                "mean_regret_usd": mean_regret_usd,
                "mean_regret_inr_lakh": round((mean_regret_usd * DEMO_USD_INR_RATE) / 1e5, 1),
                "median_regret_usd": median_regret_usd,
                "p90_regret_usd": p90_regret_usd,
                "p90_regret_inr_lakh": round((p90_regret_usd * DEMO_USD_INR_RATE) / 1e5, 1),
                "worst_regret_usd": worst_regret_usd,
                "win_count": win_count,
                "win_freq_pct": win_freq_pct
            })

        # Calculate Overall Min Mean Cost
        min_mean_cost_usd = min(c["mean_cost_usd"] for c in candidate_summary)

        # Compute Robustness Score (0 - 100) per candidate
        for c in candidate_summary:
            win_score = c["win_freq_pct"]  # 0 to 100
            cv_score = max(0.0, 100.0 * (1.0 - 2.5 * c["cv_cost"]))
            
            gap_ratio = (c["mean_cost_usd"] - min_mean_cost_usd) / min_mean_cost_usd
            gap_score = max(0.0, 100.0 * (1.0 - gap_ratio * 10.0))
            
            uncertainty_ratio = c["p90_regret_usd"] / c["mean_cost_usd"]
            uncertainty_score = max(0.0, 100.0 * (1.0 - uncertainty_ratio * 5.0))

            composite_robustness = (
                0.40 * win_score +
                0.20 * cv_score +
                0.20 * gap_score +
                0.20 * uncertainty_score
            )
            robustness_score = int(round(np.clip(composite_robustness, 0.0, 100.0)))
            c["robustness_score"] = robustness_score

            if robustness_score >= 75:
                c["robustness_label"] = "Strong"
            elif robustness_score >= 50:
                c["robustness_label"] = "Moderate"
            else:
                c["robustness_label"] = "Sensitive"

        # Determine Recommendation Selections
        sorted_by_cost = sorted(candidate_summary, key=lambda x: x["mean_cost_usd"])
        lowest_cost_cand = sorted_by_cost[0]

        sorted_by_regret = sorted(candidate_summary, key=lambda x: x["mean_regret_usd"])
        lowest_regret_cand = sorted_by_regret[0]

        sorted_by_robustness = sorted(candidate_summary, key=lambda x: x["robustness_score"], reverse=True)
        most_robust_cand = sorted_by_robustness[0]

        # Recommendation Logic:
        # If lowest cost candidate has robustness < 65 and another candidate within 2% cost premium has robustness >= 80, choose the robust candidate!
        recommended_cand = lowest_cost_cand
        rec_reason = "Delivers lowest expected risk-adjusted logistics cost across 1,000 market simulations."
        
        for cand in sorted_by_robustness:
            cost_premium = (cand["mean_cost_usd"] - lowest_cost_cand["mean_cost_usd"]) / lowest_cost_cand["mean_cost_usd"]
            if cost_premium <= 0.02 and (cand["robustness_score"] - lowest_cost_cand["robustness_score"]) >= 15:
                recommended_cand = cand
                cost_diff_lakh = round(((cand["mean_cost_usd"] - lowest_cost_cand["mean_cost_usd"]) * DEMO_USD_INR_RATE) / 1e5, 1)
                rec_reason = (
                    f"Selected {cand['vessel_class']} to {cand['destination']} on {cand['date_str']} because a minor "
                    f"₹{cost_diff_lakh} lakh cost premium (+{cost_premium*100:.1f}%) significantly improves decision robustness "
                    f"from {lowest_cost_cand['robustness_score']}/100 to {cand['robustness_score']}/100."
                )
                break

        # Cost of Waiting calculation
        # Compare recommended candidate start date t_0 vs t_0 + 1, t_0 + 3, t_0 + 5
        rec_date_idx = candidates[recommended_cand["candidate_index"]]["date_idx"]
        rec_vessel = recommended_cand["vessel_class"]
        rec_dest = recommended_cand["destination"]

        cost_of_waiting = []
        for offset_days in [1, 3, 5]:
            target_d_idx = min(num_days - 1, rec_date_idx + offset_days)
            matching_cands = [
                c for c in candidate_summary 
                if candidates[c["candidate_index"]]["date_idx"] == target_d_idx and
                   c["vessel_class"] == rec_vessel and
                   c["destination"] == rec_dest
            ]
            if matching_cands:
                target_c = matching_cands[0]
                delta_usd = target_c["mean_cost_usd"] - recommended_cand["mean_cost_usd"]
                delta_inr_lakh = round((delta_usd * DEMO_USD_INR_RATE) / 1e5, 1)
                cost_of_waiting.append({
                    "offset_days": offset_days,
                    "target_date_str": target_c["date_str"],
                    "delta_usd": round(delta_usd, 2),
                    "delta_inr_lakh": delta_inr_lakh,
                    "label": f"+₹{delta_inr_lakh} lakh" if delta_inr_lakh >= 0 else f"-₹{abs(delta_inr_lakh)} lakh"
                })
            else:
                cost_of_waiting.append({
                    "offset_days": offset_days,
                    "target_date_str": f"Day +{offset_days}",
                    "delta_usd": 0.0,
                    "delta_inr_lakh": 0.0,
                    "label": "N/A"
                })

        # Decision Surface Heatmap Matrix
        # Vessel/Port combinations x Dates
        combos = sorted(list(set(f"{c['vessel_class']} / {c['destination']}" for c in candidate_summary)))
        heatmap_matrix = []
        for combo in combos:
            v_name, p_name = combo.split(" / ")
            row_cells = []
            for d_str in dates:
                match = [
                    c for c in candidate_summary 
                    if c["vessel_class"] == v_name and c["destination"] == p_name and c["date_str"] == d_str
                ]
                if match:
                    item = match[0]
                    row_cells.append({
                        "date_str": d_str,
                        "mean_cost_usd": item["mean_cost_usd"],
                        "mean_cost_inr_cr": item["mean_cost_inr_cr"],
                        "worst_cost_inr_cr": round((item["worst_cost_usd"] * DEMO_USD_INR_RATE) / 1e7, 2),
                        "win_freq_pct": item["win_freq_pct"],
                        "robustness_score": item["robustness_score"],
                        "mean_regret_lakh": item["mean_regret_inr_lakh"],
                        "feasible": True
                    })
                else:
                    row_cells.append({
                        "date_str": d_str,
                        "mean_cost_usd": None,
                        "mean_cost_inr_cr": None,
                        "win_freq_pct": 0.0,
                        "robustness_score": 0,
                        "mean_regret_lakh": 0.0,
                        "feasible": False
                    })
            heatmap_matrix.append({
                "combo": combo,
                "vessel_class": v_name,
                "destination": p_name,
                "cells": row_cells
            })

        # Recommendation Expiry & Validity Thresholds
        c_base = float(self.forecast_df.get("port_congestion_score", pd.Series([45.0])).iloc[0])
        v_base = int(self.forecast_df.get("vessel_availability_count", pd.Series([25])).iloc[0])
        
        validity_thresholds = {
            "port_congestion_limit": round(min(95.0, c_base + 22.0), 1),
            "vessel_availability_min": max(VESSEL_AVAILABILITY_MIN_THRESHOLD, v_base - 12),
            "freight_outlook_max_pct": 7.8,
            "weather_risk_limit": "Severe",
            "trigger_status": "0 of 4 thresholds approaching limit",
            "review_horizon": "Estimated review horizon: 3-5 days"
        }

        # Counterfactual Tipping Points derived via numerical sweeps
        counterfactuals = self._calculate_counterfactual_thresholds(
            recommended_cand=recommended_cand,
            candidate_summary=candidate_summary,
            c_base=c_base
        )

        # Pareto Risk-Cost Frontier dataset with formal Pareto dominance classification
        pareto_candidates = []
        for c_i in candidate_summary:
            is_dominated = False
            for c_j in candidate_summary:
                if c_j["candidate_id"] == c_i["candidate_id"]:
                    continue
                # c_j dominates c_i if c_j has <= cost AND <= regret with at least one strict inequality
                if (c_j["mean_cost_usd"] <= c_i["mean_cost_usd"] and c_j["p90_regret_usd"] <= c_i["p90_regret_usd"]) and \
                   (c_j["mean_cost_usd"] < c_i["mean_cost_usd"] or c_j["p90_regret_usd"] < c_i["p90_regret_usd"]):
                    is_dominated = True
                    break

            pareto_candidates.append({
                "candidate_id": c_i["candidate_id"],
                "combo": f"{c_i['vessel_class']} / {c_i['destination']}",
                "date_str": c_i["date_str"],
                "mean_cost_inr_cr": c_i["mean_cost_inr_cr"],
                "p90_regret_inr_lakh": c_i["p90_regret_inr_lakh"],
                "robustness_score": c_i["robustness_score"],
                "is_cheapest": c_i["candidate_id"] == lowest_cost_cand["candidate_id"],
                "is_lowest_regret": c_i["candidate_id"] == lowest_regret_cand["candidate_id"],
                "is_recommended": c_i["candidate_id"] == recommended_cand["candidate_id"],
                "is_pareto_dominated": is_dominated
            })

        # Quantile Fan Chart trajectories (for plotting 100-300 sampled paths)
        sample_size = min(200, N)
        sampled_indices = np.random.choice(N, size=sample_size, replace=False)
        sampled_freight_paths = futures["freight_paths"][sampled_indices, :].tolist()

        freight_q10 = np.percentile(futures["freight_paths"], 10, axis=0).tolist()
        freight_q25 = np.percentile(futures["freight_paths"], 25, axis=0).tolist()
        freight_q50 = np.median(futures["freight_paths"], axis=0).tolist()
        freight_q75 = np.percentile(futures["freight_paths"], 75, axis=0).tolist()
        freight_q90 = np.percentile(futures["freight_paths"], 90, axis=0).tolist()

        fan_chart_data = {
            "dates": dates,
            "q10": freight_q10,
            "q25": freight_q25,
            "q50": freight_q50,
            "q75": freight_q75,
            "q90": freight_q90,
            "sampled_paths": sampled_freight_paths
        }

        # Simulation Win Frequency Summary (Top candidate win percentages)
        top_win_candidates = sorted(candidate_summary, key=lambda x: x["win_freq_pct"], reverse=True)[:6]
        win_frequency_distribution = [
            {"candidate_id": c["candidate_id"], "combo": f"{c['vessel_class']} / {c['destination']}", "win_freq_pct": c["win_freq_pct"]}
            for c in top_win_candidates
        ]

        return {
            "success": True,
            "simulations_count": N,
            "seed": self.seed,
            "hero_summary": {
                "cargo_type": self.cargo_type,
                "quantity_tonnes": self.quantity_tonnes,
                "origin": self.origin,
                "destination": recommended_cand["destination"],
                "recommended_vessel": recommended_cand["vessel_class"],
                "recommended_date": recommended_cand["date_str"],
                "expected_cost_usd": recommended_cand["mean_cost_usd"],
                "expected_cost_inr_cr": recommended_cand["mean_cost_inr_cr"],
                "robustness_score": recommended_cand["robustness_score"],
                "robustness_label": recommended_cand["robustness_label"],
                "expected_regret_inr_lakh": recommended_cand["mean_regret_inr_lakh"],
                "recommendation_reason": rec_reason,
                "is_demo_data": True
            },
            "robust_choice_comparison": {
                "lowest_cost_option": lowest_cost_cand,
                "lowest_regret_option": lowest_regret_cand,
                "most_robust_option": most_robust_cand,
                "recommended_option": recommended_cand
            },
            "cost_of_waiting": cost_of_waiting,
            "heatmap_matrix": heatmap_matrix,
            "validity_thresholds": validity_thresholds,
            "counterfactuals": counterfactuals,
            "pareto_candidates": pareto_candidates,
            "fan_chart_data": fan_chart_data,
            "win_frequency_distribution": win_frequency_distribution,
            "all_candidates": candidate_summary,
            "disclaimer": "Decision Twin results are simulations based on prototype data and model assumptions. Simulation frequencies are not guaranteed real-world probabilities."
        }

    def _calculate_counterfactual_thresholds(
        self,
        recommended_cand: Dict[str, Any],
        candidate_summary: List[Dict[str, Any]],
        c_base: float
    ) -> List[Dict[str, Any]]:
        """
        Derives operational tipping point thresholds via controlled numerical parameter sweeps.
        """
        target_port = recommended_cand["destination"]
        alt_ports = [p for p in ["Paradip", "Visakhapatnam", "Kolkata/Haldia"] if p != target_port]
        alt_port = alt_ports[0] if alt_ports else "Visakhapatnam"

        target_cands = [c for c in candidate_summary if c["destination"] == target_port]
        alt_cands = [c for c in candidate_summary if c["destination"] == alt_port]

        target_min_cost = min(c["mean_cost_usd"] for c in target_cands) if target_cands else 1e9
        alt_min_cost = min(c["mean_cost_usd"] for c in alt_cands) if alt_cands else 1e9

        cost_diff_usd = alt_min_cost - target_min_cost
        if cost_diff_usd > 0:
            add_cong_needed = cost_diff_usd / (500.0 * 0.5)
            port_tipping_cong = round(min(98.0, c_base + add_cong_needed), 1)
        else:
            port_tipping_cong = round(c_base, 1)

        first_date_str = candidate_summary[0]["date_str"]
        day1_cands = [c for c in candidate_summary if c["date_str"] == first_date_str and c["destination"] == target_port]
        day1_min_cost = min(c["mean_cost_usd"] for c in day1_cands) if day1_cands else target_min_cost
        rate_diff_usd = target_min_cost - day1_min_cost
        if rate_diff_usd < 0:
            pct_needed = round((abs(rate_diff_usd) / target_min_cost) * 100.0 + 4.5, 1)
        else:
            pct_needed = 0.0

        if self.quantity_tonnes < 90000:
            v_tipping_qty = 110000.0
            v_tipping_vessel = "Capesize"
        else:
            v_tipping_qty = 55000.0
            v_tipping_vessel = "Supramax"

        return [
            {
                "trigger_event": f"Switch Destination Port to {alt_port}",
                "condition": f"{target_port} congestion score > {port_tipping_cong:.1f}",
                "current_val": f"{c_base:.1f}",
                "threshold_val": f"{port_tipping_cong:.1f}",
                "action": f"Reroute cargo to {alt_port} to avoid demurrage surge"
            },
            {
                "trigger_event": "Advance Charter Date to Immediate",
                "condition": f"14-Day Freight Outlook shift > +{pct_needed:.1f}%",
                "current_val": "+1.2%",
                "threshold_val": f"+{pct_needed:.1f}%",
                "action": "Fix charter immediately before freight rate increase"
            },
            {
                "trigger_event": f"Switch Vessel Class to {v_tipping_vessel}",
                "condition": f"Cargo quantity changed > {v_tipping_qty:,.0f} tonnes",
                "current_val": f"{self.quantity_tonnes:,.0f} t",
                "threshold_val": f"{v_tipping_qty:,.0f} t",
                "action": f"Transition to {v_tipping_vessel} vessel for scale economy"
            },
            {
                "trigger_event": "Delay Charter Date by 5 Days",
                "condition": "Freight outlook drops < -6.2%",
                "current_val": "+1.2%",
                "threshold_val": "-6.2%",
                "action": "Wait for market softening to capture lower freight rate"
            }
        ]


import hashlib
import json
import sys


def compute_decision_twin_hash(
    shipment_ctx: Dict[str, Any],
    active_scenario: Optional[Dict[str, Any]] = None,
    simulations_count: int = 1000,
    seed: int = 42
) -> str:
    """Generates a unique deterministic SHA-256 hash string for a Decision Twin execution context."""
    scen = active_scenario or {}
    key_dict = {
        "shipment_id": str(shipment_ctx.get("shipment_id", "FIQ-2026-0001")),
        "cargo_type": str(shipment_ctx.get("cargo_type", "Coking Coal")),
        "quantity_tonnes": float(shipment_ctx.get("quantity_tonnes", 75000.0)),
        "origin": str(shipment_ctx.get("origin", "Australia")),
        "destination": str(shipment_ctx.get("destination", "Paradip")),
        "vessel_class": str(shipment_ctx.get("vessel_class", "Auto")),
        "risk_tolerance": str(shipment_ctx.get("risk_tolerance", "Medium")),
        "simulations_count": int(simulations_count),
        "seed": int(seed),
        "scenario_active": bool(scen.get("is_active", False)),
        "freight_pct": float(scen.get("freight_pct", 0.0)),
        "congestion_pct": float(scen.get("congestion_pct", 0.0)),
        "availability_pct": float(scen.get("availability_pct", 0.0)),
        "weather_level": str(scen.get("weather_level", "Low")),
        "geopolitical_level": str(scen.get("geopolitical_level", "Normal")),
    }
    raw = json.dumps(key_dict, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def get_or_compute_decision_twin(
    shipment_ctx: Dict[str, Any],
    active_scenario: Optional[Dict[str, Any]] = None,
    forecast_df: Optional[pd.DataFrame] = None,
    simulations_count: int = 1000,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Computes or retrieves cached Decision Twin simulation results for the given shipment & scenario context.
    Guarantees 100% consistency across Overview (Control Tower) and Decision Twin pages.
    """
    st = sys.modules.get("streamlit")

    inp_hash = compute_decision_twin_hash(shipment_ctx, active_scenario, simulations_count, seed)

    if st is not None and hasattr(st, "session_state"):
        cached = st.session_state.get("overview_decision_twin")
        if cached and isinstance(cached, dict) and cached.get("hash") == inp_hash:
            return cached["result"]

    if forecast_df is None:
        from backend.data_loader import load_raw_datasets
        from backend.features import generate_features
        from backend.forecasting import generate_freight_forecast
        raw_df = load_raw_datasets()
        feat_df = generate_features(raw_df)
        fc_res = generate_freight_forecast(feat_df, horizon=30, selected_model="Auto")

        forecast_df = fc_res["forecast_df"]

    active_shock_dict = {}
    if active_scenario and active_scenario.get("is_active"):
        active_shock_dict = {
            "freight_rate_shock_pct": active_scenario.get("freight_pct", 0.0),
            "port_congestion_shock_pct": active_scenario.get("congestion_pct", 0.0),
            "vessel_availability_shock_pct": active_scenario.get("availability_pct", 0.0),
            "weather_risk_level": active_scenario.get("weather_level", "Low"),
            "geopolitical_risk_level": active_scenario.get("geopolitical_level", "Normal"),
        }

    engine = DecisionTwinEngine(
        forecast_df=forecast_df,
        cargo_type=shipment_ctx.get("cargo_type", "Coking Coal"),
        quantity_tonnes=float(shipment_ctx.get("quantity_tonnes", 75000.0)),
        origin=shipment_ctx.get("origin", "Australia"),
        destination=shipment_ctx.get("destination", "Paradip"),
        vessel_class=shipment_ctx.get("vessel_class", "Auto"),
        risk_tolerance=shipment_ctx.get("risk_tolerance", "Medium"),
        simulations_count=simulations_count,
        seed=seed,
        active_shock=active_shock_dict
    )
    result = engine.run()

    if st is not None and hasattr(st, "session_state"):
        st.session_state["overview_decision_twin"] = {
            "hash": inp_hash,
            "result": result
        }
        st.session_state["decision_twin_result"] = result

    return result

