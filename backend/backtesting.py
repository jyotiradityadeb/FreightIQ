"""
FreightIQ Historical Backtesting & Validation Module

Runs walk-forward historical simulation evaluating FreightIQ's decision recommendations
against a benchmark ("Charter immediately on decision date").

STRICT TERMINOLOGY COMPLIANCE:
- 'historical simulation'
- 'simulated cost difference'
- 'simulated savings/loss'
All results are clearly designated as historical simulations and NOT realized real-world savings.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional

from backend.forecasting import generate_freight_forecast, calculate_metrics, make_insufficient_data_metrics
from backend.optimizer import evaluate_charter_candidate

BACKTEST_DISCLAIMER = (
    "Backtest results are historical simulations and do not guarantee future savings."
)


def run_historical_simulation(
    df: pd.DataFrame,
    start_date: str,
    end_date: str,
    horizon: int = 14,
    step_days: int = 14,
    cargo_type: str = "Coking Coal",
    quantity_tonnes: float = 75000.0,
    origin: str = "Australia",
    destination: str = "Paradip",
    vessel_class: str = "Panamax"
) -> Dict[str, Any]:
    """
    Executes historical walk-forward simulation across historical decision points.
    """
    data = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(data["date"]):
        data["date"] = pd.to_datetime(data["date"])

    data = data.sort_values("date").reset_index(drop=True)

    dt_start = pd.to_datetime(start_date)
    dt_end = pd.to_datetime(end_date)

    # Filter available decision dates
    decision_dates = data[(data["date"] >= dt_start) & (data["date"] <= dt_end)]["date"].tolist()

    # Subsample decision dates according to step_days
    sampled_dates = decision_dates[::step_days]

    if not sampled_dates:
        return {
            "success": False,
            "error": "No historical decision points available in the selected date range.",
            "disclaimer": BACKTEST_DISCLAIMER
        }

    period_results = []
    y_actuals = []
    y_forecasts = []

    for d_point in sampled_dates:
        # 1. Strict train split up to decision date d_point (no future data leakage)
        train_df = data[data["date"] <= d_point]
        if len(train_df) < 30:
            continue

        # 2. Future actual ground truth data for the evaluation window
        future_df = data[(data["date"] > d_point) & (data["date"] <= d_point + pd.Timedelta(days=horizon))]
        if len(future_df) < 3:
            continue

        # 3. Generate Freight Rate Forecast
        fc_res = generate_freight_forecast(train_df, horizon=horizon, selected_model="Auto")
        fc_df = fc_res["forecast_df"]

        # Track forecast accuracy vs actual observed rates
        merged_fc = pd.merge(fc_df, future_df[["date", "freight_rate"]], on="date", how="inner")
        if len(merged_fc) > 0:
            y_forecasts.extend(merged_fc["predicted_freight_rate"].values)
            y_actuals.extend(merged_fc["freight_rate"].values)

        # 4. Benchmark Strategy: Charter immediately on decision date d_point
        row_now = train_df.iloc[-1]
        benchmark_eval = evaluate_charter_candidate(
            charter_date=d_point,
            vessel_class=vessel_class,
            origin=origin,
            destination=destination,
            cargo_type=cargo_type,
            quantity_tonnes=quantity_tonnes,
            freight_rate_forecast=float(row_now["freight_rate"]),
            congestion_score=float(row_now.get("port_congestion_score", 45.0)),
            waiting_hours=float(row_now.get("avg_waiting_hours", 24.0)),
            vessel_avail_count=int(row_now.get("vessel_availability_count", 25)),
            weather_risk=float(row_now.get("weather_risk_score", 3.0)),
            event_risk=float(row_now.get("event_risk_score", 2.0))
        )
        
        # Actual benchmark cost observed historically on d_point
        benchmark_sim_cost = benchmark_eval["total_logistics_cost_usd"]

        # 5. FreightIQ Strategy: Evaluate candidate dates in forecast window
        best_candidate = None
        min_est_cost = float("inf")

        for _, fc_row in fc_df.iterrows():
            cand_date = fc_row["date"]
            # Look up actual historic observed values for cand_date in future_df/data
            historic_row = data[data["date"] == cand_date]
            if len(historic_row) == 0:
                continue

            h_row = historic_row.iloc[0]

            cand_eval = evaluate_charter_candidate(
                charter_date=cand_date,
                vessel_class=vessel_class,
                origin=origin,
                destination=destination,
                cargo_type=cargo_type,
                quantity_tonnes=quantity_tonnes,
                freight_rate_forecast=float(fc_row["predicted_freight_rate"]),
                congestion_score=float(row_now.get("port_congestion_score", 45.0)),
                waiting_hours=float(row_now.get("avg_waiting_hours", 24.0)),
                vessel_avail_count=int(row_now.get("vessel_availability_count", 25)),
                weather_risk=float(row_now.get("weather_risk_score", 3.0)),
                event_risk=float(row_now.get("event_risk_score", 2.0))
            )

            if cand_eval["feasible"] and cand_eval["total_logistics_cost_usd"] < min_est_cost:
                min_est_cost = cand_eval["total_logistics_cost_usd"]

                # Actual realized cost for FreightIQ recommendation based on true historic observation
                actual_rec_eval = evaluate_charter_candidate(
                    charter_date=cand_date,
                    vessel_class=vessel_class,
                    origin=origin,
                    destination=destination,
                    cargo_type=cargo_type,
                    quantity_tonnes=quantity_tonnes,
                    freight_rate_forecast=float(h_row["freight_rate"]),  # Actual true rate
                    congestion_score=float(h_row["port_congestion_score"]),
                    waiting_hours=float(h_row["avg_waiting_hours"]),
                    vessel_avail_count=int(h_row["vessel_availability_count"]),
                    weather_risk=float(h_row["weather_risk_score"]),
                    event_risk=float(h_row["event_risk_score"])
                )
                best_candidate = actual_rec_eval

        if best_candidate is None:
            best_candidate = benchmark_eval

        freightiq_sim_cost = best_candidate["total_logistics_cost_usd"]
        sim_diff = benchmark_sim_cost - freightiq_sim_cost

        period_results.append({
            "decision_date": d_point.strftime("%Y-%m-%d"),
            "recommended_charter_date": best_candidate["charter_date"],
            "benchmark_simulated_cost": benchmark_sim_cost,
            "freightiq_simulated_cost": freightiq_sim_cost,
            "simulated_cost_difference": sim_diff,
            "simulated_savings_status": "Simulated Savings" if sim_diff >= 0 else "Simulated Loss",
            "selected_model": fc_res["selected_model"]
        })

    if not period_results:
        return {
            "success": False,
            "error": "Insufficient history to perform simulation.",
            "disclaimer": BACKTEST_DISCLAIMER
        }

    res_df = pd.DataFrame(period_results)
    
    total_benchmark = float(res_df["benchmark_simulated_cost"].sum())
    total_freightiq = float(res_df["freightiq_simulated_cost"].sum())
    total_sim_diff = total_benchmark - total_freightiq
    pct_sim_diff = (total_sim_diff / total_benchmark * 100.0) if total_benchmark > 0 else 0.0

    wins = int((res_df["simulated_cost_difference"] >= 0).sum())
    total_periods = len(res_df)
    win_rate = round(wins / total_periods * 100.0, 1)

    # Forecast accuracy overall metrics
    if len(y_actuals) > 0:
        forecast_metrics = calculate_metrics(np.array(y_actuals), np.array(y_forecasts))
    else:
        forecast_metrics = make_insufficient_data_metrics(available=0, required=1)

    return {
        "success": True,
        "historical_simulation_title": "FreightIQ vs Benchmark Historical Simulation",
        "benchmark_name": "Charter Immediately on Decision Date",
        "test_periods_count": total_periods,
        "win_count": wins,
        "win_rate_percentage": win_rate,
        "benchmark_simulated_cost_total": round(total_benchmark, 2),
        "freightiq_simulated_cost_total": round(total_freightiq, 2),
        "simulated_cost_difference_total": round(total_sim_diff, 2),
        "simulated_savings_percentage": round(pct_sim_diff, 2),
        "forecast_accuracy_metrics": forecast_metrics,
        "period_results_table": res_df.to_dict(orient="records"),
        "disclaimer": BACKTEST_DISCLAIMER
    }
