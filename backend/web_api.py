"""Route-aware endpoints for the Netlify web client; the Python engines stay authoritative."""
from datetime import date
from functools import lru_cache
import json
from typing import Literal

import pandas as pd
from fastapi import APIRouter, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import Response
from pydantic import Field

from backend.schemas import OptimizeRequest, ScenarioShock, ScenarioRequest
from backend.domain.routes import get_calibrated_routes
from backend.domain.vessels import get_all_vessel_classes
from backend.route_market import get_route_market_history
from backend.forecasting import generate_freight_forecast, HAS_PROPHET
from backend.optimizer import optimize_charter_timing
from backend.config_model import get_decision_params_registry

router = APIRouter(prefix="/web", tags=["Netlify client"])


def clean(value):
    """Normalize scientific values, including NaN, to strict JSON."""
    if isinstance(value, pd.DataFrame):
        return json.loads(value.to_json(orient="records", date_format="iso"))
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(v) for v in value]
    if hasattr(value, "tolist"):
        return clean(value.tolist())
    if isinstance(value, float) and not __import__("math").isfinite(value):
        return None
    return jsonable_encoder(value)


def history(route_key):
    if route_key not in {r["route_key"] for r in get_calibrated_routes()}:
        raise HTTPException(422, "Choose a calibrated route from the route selector.")
    return get_route_market_history(route_key)


@lru_cache(maxsize=64)
def forecast(route_key, horizon, model):
    return generate_freight_forecast(history(route_key), horizon=horizon, selected_model=model)


class WebRequest(OptimizeRequest):
    route_key: str = "AU_HPT -> IN_PDP"
    horizon: int = Field(14, ge=7, le=30)
    model_name: Literal["Auto", "SARIMA", "Naive Baseline", "Prophet"] = "Auto"
    vessel_class: Literal["Auto", "Capesize", "Panamax", "Supramax"] = "Auto"
    risk_tolerance: Literal["Low", "Medium", "High"] = "Medium"
    cargo_type: Literal["Coking Coal", "Iron Ore"] = "Coking Coal"
    simulations_count: int = Field(1000, ge=50, le=5000)
    arena_simulations_count: int = Field(250, ge=50, le=500)
    seed: int = 42
    uncertainty_scale: float = Field(1.0, ge=0.25, le=2.0)
    shock: ScenarioShock = Field(default_factory=ScenarioShock)
    start_date: date = date(2026, 1, 1)
    end_date: date = date(2026, 6, 30)
    step_days: int = Field(14, ge=7, le=30)
    demurrage_rate: float | None = Field(None, ge=0, le=1000000)


@router.get("/catalog")
def catalog():
    return clean({"routes": get_calibrated_routes(), "parameters": get_decision_params_registry(),
                  "data_mode": "DEMO / SYNTHETIC", "usd_inr": 84,
                  "vessel_speeds_knots": {name: vessel.speed_knots for name, vessel in get_all_vessel_classes().items()},
                  "prophet_available": HAS_PROPHET})


@router.get("/data")
def dataset(route_key: str = "AU_HPT -> IN_PDP"):
    df = history(route_key)
    numeric = df.select_dtypes(include="number")
    return clean({"records": df, "correlation": numeric.corr().reset_index(),
                  "quality": {"rows": len(df), "duplicate_dates": int(df.date.duplicated().sum()),
                              "missing_values": df.isna().sum().to_dict()},
                  "is_demo_data": True})


@router.post("/{action}")
def calculate(action: str, req: WebRequest):
    if action not in {"forecast", "optimize", "scenario", "decision-twin", "strategy-arena", "arena-report", "control-tower",
                      "backtest", "sensitivity", "report"}:
        raise HTTPException(404, "Unknown calculation")
    df = history(req.route_key)
    origin, destination = req.route_key.split(" -> ")
    common = dict(cargo_type=req.cargo_type, quantity_tonnes=req.quantity_tonnes,
                  origin=origin, destination=destination, vessel_class=req.vessel_class,
                  risk_tolerance=req.risk_tolerance)
    if action == "backtest":
        from backend.backtesting import run_historical_simulation
        if req.start_date >= req.end_date:
            raise HTTPException(422, "Backtest start must precede end.")
        if req.start_date < df.date.min().date() or req.end_date > df.date.max().date():
            raise HTTPException(422, "Backtest dates must be inside the dataset period.")
        common.pop("risk_tolerance")
        # The existing backtest evaluates a fixed Panamax, not the optimizer's
        # "Auto" selector. Passing Auto produces an infeasible candidate.
        common["vessel_class"] = "Panamax"
        result = run_historical_simulation(df, start_date=str(req.start_date), end_date=str(req.end_date),
                                          horizon=req.horizon, step_days=req.step_days, **common)
    else:
        fc = forecast(req.route_key, req.horizon, req.model_name)
        frame = fc["forecast_df"].copy(deep=True)
        if action == "forecast":
            return clean({**fc, "route_key": req.route_key, "is_demo_data": True})
        # The univariate freight forecast has no operational regressors. Carry the
        # latest route-specific synthetic observation forward as an explicit
        # assumption instead of silently using generic optimizer fallbacks.
        context_fields = ("port_congestion_score", "avg_waiting_hours", "vessel_availability_count",
                          "weather_risk_score", "event_risk_score")
        latest_context = df.iloc[-1]
        for field in context_fields:
            if field not in frame and field in df:
                frame[field] = latest_context[field]
        try:
            earliest = pd.Timestamp(req.earliest_date) if req.earliest_date else frame.date.min()
            latest = pd.Timestamp(req.latest_date) if req.latest_date else frame.date.max()
            if earliest > latest or earliest > frame.date.max() or latest < frame.date.min():
                raise ValueError()
        except (ValueError, TypeError):
            raise HTTPException(422, "Charter dates must overlap the forecast period, with start before end.")
        if action in {"optimize", "report", "sensitivity"}:
            args = dict(forecast_df=frame, **common, earliest_date=req.earliest_date,
                        latest_date=req.latest_date, demurrage_rate=req.demurrage_rate)
            if action == "sensitivity":
                from backend.sensitivity import run_sensitivity_analysis
                args.pop("vessel_class")  # Existing sensitivity engine compares automatic vessel choice.
                result = run_sensitivity_analysis(**args)
            else:
                result = optimize_charter_timing(**args)
                if action == "report" and result.get("success"):
                    from backend.backtesting import run_historical_simulation
                    from backend.decision_twin import DecisionTwinEngine
                    from backend.reporting import generate_charter_decision_pdf
                    from backend.scenario_engine import run_scenario_simulation
                    from backend.validation import run_real_validation

                    twin = DecisionTwinEngine(
                        frame, **common, simulations_count=req.simulations_count,
                        seed=req.seed, active_shock=req.shock.model_dump(),
                    ).run()
                    scenario = run_scenario_simulation(
                        frame, ScenarioRequest(**common, shock=req.shock,
                                               earliest_date=req.earliest_date,
                                               latest_date=req.latest_date),
                    )
                    # A short, explicit walk-forward period keeps the downloadable
                    # report responsive while using actual held-out demo history.
                    backtest_end = df.date.max() - pd.Timedelta(days=req.horizon)
                    backtest_start = max(df.date.min() + pd.Timedelta(days=60),
                                         backtest_end - pd.Timedelta(days=60))
                    backtest = run_historical_simulation(
                        df, start_date=str(backtest_start.date()),
                        end_date=str(backtest_end.date()), horizon=req.horizon,
                        step_days=30, cargo_type=req.cargo_type,
                        quantity_tonnes=req.quantity_tonnes, origin=origin,
                        destination=destination,
                        vessel_class=result["best_option"]["vessel_class"],
                    )
                    if not all(part.get("success") for part in (twin, scenario, backtest)):
                        raise HTTPException(422, "Report analyses could not be completed for this shipment.")
                    recommendation = {**result["recommendation"],
                                      "all_evaluated_candidates": result["all_evaluated_candidates"][:4]}
                    pdf = generate_charter_decision_pdf(
                        recommendation,
                        market_outlook={"model": fc["selected_model"], "horizon": req.horizon},
                        decision_twin_result=twin, scenario_result=scenario,
                        backtest_metrics=backtest, synthetic_validation=fc["metrics"],
                        real_validation=run_real_validation(), data_mode="DEMO / SYNTHETIC",
                    )
                    return Response(pdf,
                                    media_type="application/pdf",
                                    headers={"Content-Disposition": 'attachment; filename="FreightIQ-decision.pdf"'})
        elif action == "scenario":
            from backend.scenario_engine import run_scenario_simulation
            result = run_scenario_simulation(frame, ScenarioRequest(**common, shock=req.shock,
                         earliest_date=req.earliest_date, latest_date=req.latest_date))
        elif action in {"strategy-arena", "arena-report"}:
            from backend.scenario_engine import build_shocked_forecast_df
            from backend.strategy_arena import compare_strategies
            shock = req.shock
            active = (shock.freight_rate_shock_pct != 0 or shock.port_congestion_shock_pct != 0
                      or shock.vessel_availability_shock_pct != 0 or shock.demurrage_rate_shock_pct != 0
                      or shock.weather_risk_level != "Low" or shock.geopolitical_risk_level != "Normal")
            arena_frame = build_shocked_forecast_df(frame, shock, destination) if active else frame
            try:
                result = compare_strategies(
                    arena_frame, df, **common, earliest_date=req.earliest_date,
                    latest_date=req.latest_date, demurrage_rate=req.demurrage_rate,
                    simulations_count=req.arena_simulations_count, seed=req.seed,
                    uncertainty_scale=req.uncertainty_scale, model_name=fc["selected_model"],
                    route_key=req.route_key, demurrage_shock_pct=shock.demurrage_rate_shock_pct,
                )
            except ValueError as error:
                raise HTTPException(422, str(error)) from error
            result["active_shock"] = shock.model_dump() if active else None
            if action == "arena-report":
                from backend.reporting import generate_strategy_arena_pdf
                return Response(generate_strategy_arena_pdf(result), media_type="application/pdf",
                                headers={"Content-Disposition": 'attachment; filename="FreightIQ-strategy-arena.pdf"'})
        elif action == "decision-twin":
            from backend.decision_twin import DecisionTwinEngine
            result = DecisionTwinEngine(frame, **common, simulations_count=req.simulations_count,
                                        seed=req.seed, active_shock=req.shock.model_dump()).run()
        else:
            from backend.disruption_engine import evaluate_control_tower_state
            result = evaluate_control_tower_state(frame, **common, shock_override=req.shock)
    if result.get("success") is False:
        raise HTTPException(422, result.get("error", "No feasible result for these inputs."))
    payload = {**result, "route_key": req.route_key, "is_demo_data": True}
    if action != "backtest":
        payload["operational_context"] = {
            "method": "last synthetic route observation carried forward",
            "observation_date": str(df.date.max().date()),
        }
    return clean(payload)


@router.get("/validation")
def validation():
    from backend.validation import run_real_validation
    return clean(run_real_validation())
