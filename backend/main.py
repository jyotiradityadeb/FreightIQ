"""
FreightIQ FastAPI Application Server

Exposes RESTful endpoints for health status, market data, freight rate forecasting,
charter timing optimization, historical backtesting, and custom CSV upload.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io

from backend.config import APP_TITLE, DEMO_BANNER_TEXT, DISCLAIMER_TEXT
from backend.data_loader import load_raw_datasets, validate_user_csv
from backend.features import generate_features
from backend.forecasting import generate_freight_forecast
from backend.optimizer import optimize_charter_timing
from backend.backtesting import run_historical_simulation
from backend.scenario_engine import run_scenario_simulation
from backend.disruption_engine import evaluate_control_tower_state
from backend.decision_twin import DecisionTwinEngine
from backend.schemas import (
    HealthResponse,
    MarketLatestResponse,
    ForecastRequest,
    ForecastResponse,
    OptimizeRequest,
    OptimizeResponse,
    BacktestRequest,
    BacktestResponse,
    ScenarioRequest,
    ScenarioResponse,
    ControlTowerResponse,
    DecisionTwinRequest,
    DecisionTwinResponse
)

app = FastAPI(
    title="FreightIQ API",
    description="API for Freight Rate Forecasting & Vessel Chartering Optimizer",
    version="1.0.0"
)

# Enable CORS for Streamlit / Frontend interaction
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def get_health():
    """Health check endpoint."""
    return HealthResponse(
        status="ok",
        app_title=APP_TITLE,
        is_demo_data=True,
        message="FreightIQ FastAPI engine running successfully."
    )


@app.get("/market/latest", response_model=MarketLatestResponse)
def get_market_latest():
    """Returns the most recent market observations."""
    try:
        raw_df = load_raw_datasets()
        latest = raw_df.iloc[-1]
        return MarketLatestResponse(
            latest_date=latest["date"].strftime("%Y-%m-%d"),
            freight_rate=float(latest["freight_rate"]),
            bdi=float(latest["bdi"]),
            capesize_index=float(latest["capesize_index"]),
            panamax_index=float(latest["panamax_index"]),
            iron_ore_price=float(latest["iron_ore_price"]),
            coking_coal_price=float(latest["coking_coal_price"]),
            port_congestion_score=float(latest["port_congestion_score"]),
            avg_waiting_hours=float(latest["avg_waiting_hours"]),
            vessel_availability_count=int(latest["vessel_availability_count"]),
            weather_risk_score=float(latest["weather_risk_score"]),
            event_risk_score=float(latest["event_risk_score"]),
            is_demo_data=True
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/forecast", response_model=ForecastResponse)
def post_forecast(req: ForecastRequest):
    """Generates freight rate forecasts for 7, 14, or 30 day horizons."""
    try:
        raw_df = load_raw_datasets()
        feat_df = generate_features(raw_df)
        res = generate_freight_forecast(feat_df, horizon=req.horizon, selected_model=req.model_name)
        
        fc_records = res["forecast_df"].copy()
        fc_records["date"] = fc_records["date"].dt.strftime("%Y-%m-%d")
        
        return ForecastResponse(
            selected_model=res["selected_model"],
            metrics=res["metrics"],
            selection_reason=res["selection_reason"],
            forecast_records=fc_records.to_dict(orient="records"),
            comparison_table=res["comparison_table"],
            is_demo_data=True
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/optimize", response_model=OptimizeResponse)
def post_optimize(req: OptimizeRequest):
    """Calculates optimal charter date and vessel class minimizing total expected logistics cost."""
    try:
        raw_df = load_raw_datasets()
        feat_df = generate_features(raw_df)
        fc_res = generate_freight_forecast(feat_df, horizon=30, selected_model="Auto")
        
        opt_res = optimize_charter_timing(
            forecast_df=fc_res["forecast_df"],
            cargo_type=req.cargo_type,
            quantity_tonnes=req.quantity_tonnes,
            origin=req.origin,
            destination=req.destination,
            earliest_date=req.earliest_date,
            latest_date=req.latest_date,
            vessel_class=req.vessel_class,
            demurrage_rate=req.demurrage_rate,
            risk_tolerance=req.risk_tolerance
        )

        if not opt_res["success"]:
            raise HTTPException(status_code=400, detail=opt_res.get("error", "Optimization infeasible"))

        return OptimizeResponse(
            success=True,
            recommendation=opt_res["recommendation"],
            best_option=opt_res["best_option"],
            scenarios=opt_res["scenarios"],
            is_demo_data=True
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/backtest", response_model=BacktestResponse)
def post_backtest(req: BacktestRequest):
    """Runs historical simulation walk-forward backtest."""
    try:
        raw_df = load_raw_datasets()
        res = run_historical_simulation(
            df=raw_df,
            start_date=req.start_date,
            end_date=req.end_date,
            horizon=req.horizon,
            step_days=req.step_days,
            cargo_type=req.cargo_type,
            quantity_tonnes=req.quantity_tonnes,
            origin=req.origin,
            destination=req.destination,
            vessel_class=req.vessel_class
        )

        if not res["success"]:
            raise HTTPException(status_code=400, detail=res.get("error", "Backtest execution failed"))

        return BacktestResponse(
            success=True,
            historical_simulation_title=res["historical_simulation_title"],
            benchmark_name=res["benchmark_name"],
            test_periods_count=res["test_periods_count"],
            win_count=res["win_count"],
            win_rate_percentage=res["win_rate_percentage"],
            benchmark_simulated_cost_total=res["benchmark_simulated_cost_total"],
            freightiq_simulated_cost_total=res["freightiq_simulated_cost_total"],
            simulated_cost_difference_total=res["simulated_cost_difference_total"],
            simulated_savings_percentage=res["simulated_savings_percentage"],
            forecast_accuracy_metrics=res["forecast_accuracy_metrics"],
            period_results_table=res["period_results_table"],
            disclaimer=res["disclaimer"],
            is_demo_data=True
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/scenario", response_model=ScenarioResponse)
def post_scenario(req: ScenarioRequest):
    """Runs interactive What-If scenario simulation & stress test."""
    try:
        raw_df = load_raw_datasets()
        feat_df = generate_features(raw_df)
        fc_res = generate_freight_forecast(feat_df, horizon=30, selected_model="Auto")
        
        sim_res = run_scenario_simulation(
            forecast_df=fc_res["forecast_df"],
            request=req
        )

        if not sim_res["success"]:
            raise HTTPException(status_code=400, detail=sim_res.get("error", "Scenario simulation failed"))

        return ScenarioResponse(
            success=True,
            baseline_recommendation=sim_res["baseline_recommendation"],
            stressed_recommendation=sim_res["stressed_recommendation"],
            comparison_table=sim_res["comparison_table"],
            decision_status=sim_res["decision_status"],
            explanation=sim_res["explanation"],
            sensitivity_analysis=sim_res["sensitivity_analysis"],
            threshold_analysis=sim_res["threshold_analysis"],
            confidence_score=sim_res["confidence_score"],
            confidence_breakdown=sim_res["confidence_breakdown"],
            port_alternative_analysis=sim_res["port_alternative_analysis"],
            is_demo_data=True
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/control-tower", response_model=ControlTowerResponse)
def get_control_tower():
    """Returns real-time Control Tower disruption status, active alerts, and decision stability."""
    try:
        raw_df = load_raw_datasets()
        feat_df = generate_features(raw_df)
        fc_res = generate_freight_forecast(feat_df, horizon=30, selected_model="Auto")

        ct_res = evaluate_control_tower_state(forecast_df=fc_res["forecast_df"])

        if not ct_res["success"]:
            raise HTTPException(status_code=500, detail=ct_res.get("error", "Control Tower evaluation failed"))

        return ControlTowerResponse(
            success=True,
            current_recommendation=ct_res["current_recommendation"],
            signal_states=ct_res["signal_states"],
            active_alerts=ct_res["active_alerts"],
            port_status=ct_res["port_status"],
            route_status=ct_res["route_status"],
            decision_stability=ct_res["decision_stability"],
            market_stress_index=ct_res["market_stress_index"],
            recommended_action=ct_res["recommended_action"],
            event_log_summary=ct_res["event_log_summary"],
            disruption_simulated=ct_res["disruption_simulated"],
            is_demo_data=True
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/decision-twin", response_model=DecisionTwinResponse)
def post_decision_twin(req: DecisionTwinRequest):
    """Executes Monte Carlo Decision Twin simulation across market futures."""
    try:
        raw_df = load_raw_datasets()
        feat_df = generate_features(raw_df)
        fc_res = generate_freight_forecast(feat_df, horizon=14, selected_model="Auto")

        active_shock_dict = req.shock.model_dump() if req.shock else None

        dt_engine = DecisionTwinEngine(
            forecast_df=fc_res["forecast_df"],
            cargo_type=req.cargo_type,
            quantity_tonnes=req.quantity_tonnes,
            origin=req.origin,
            destination=req.destination,
            vessel_class=req.vessel_class,
            risk_tolerance=req.risk_tolerance,
            simulations_count=req.simulations_count,
            seed=req.seed,
            active_shock=active_shock_dict
        )

        dt_res = dt_engine.run()

        if not dt_res["success"]:
            raise HTTPException(status_code=500, detail="Decision Twin execution failed.")

        return DecisionTwinResponse(
            success=True,
            simulations_count=dt_res["simulations_count"],
            seed=dt_res["seed"],
            hero_summary=dt_res["hero_summary"],
            robust_choice_comparison=dt_res["robust_choice_comparison"],
            cost_of_waiting=dt_res["cost_of_waiting"],
            heatmap_matrix=dt_res["heatmap_matrix"],
            validity_thresholds=dt_res["validity_thresholds"],
            counterfactuals=dt_res["counterfactuals"],
            pareto_candidates=dt_res["pareto_candidates"],
            fan_chart_data=dt_res["fan_chart_data"],
            win_frequency_distribution=dt_res["win_frequency_distribution"],
            all_candidates=dt_res["all_candidates"],
            disclaimer=dt_res["disclaimer"],
            is_demo_data=True
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/data/upload")
async def upload_csv(file: UploadFile = File(...)):
    """Validates user uploaded CSV dataset."""
    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        is_valid, missing_cols, cleaned_df = validate_user_csv(df)

        return {
            "filename": file.filename,
            "is_valid": is_valid,
            "missing_columns": missing_cols,
            "rows_count": len(cleaned_df),
            "columns": list(cleaned_df.columns),
            "sample_data": cleaned_df.head(5).to_dict(orient="records")
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process CSV file: {str(e)}")
