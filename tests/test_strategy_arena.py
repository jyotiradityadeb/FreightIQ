"""Decision Arena comparisons stay reproducible and route shocks reach the model."""

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.scenario_engine import build_shocked_forecast_df
from backend.schemas import ScenarioShock


client = TestClient(app)


def test_arena_uses_shared_futures_and_preserves_cost_arithmetic():
    body = {"route_key": "AU_GLT -> IN_PDP", "arena_simulations_count": 50, "seed": 9}
    response = client.post("/web/strategy-arena", json=body)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["route_key"] == body["route_key"]
    assert result["sample_count"] == 50
    assert result["common_feasible_samples"] >= 20
    assert {item["id"] for item in result["strategies"]} == {"early", "forecast", "deferred", "downside"}
    assert all(len(item["cost_samples_inr_cr"]) == result["common_feasible_samples"] for item in result["strategies"])
    assert sum(item["delta_vs_earliest_usd"] for item in result["cost_evidence"]) == pytest.approx(
        -result["modelled_savings_vs_earliest_usd"], abs=0.05
    )
    rerun = client.post("/web/strategy-arena", json=body).json()
    assert [x["cost_samples_inr_cr"] for x in result["strategies"]] == [
        x["cost_samples_inr_cr"] for x in rerun["strategies"]
    ]


def test_route_port_shock_changes_congestion_without_erasing_other_signals():
    frame = pd.DataFrame({"predicted_freight_rate": [20.0], "port_congestion_score": [40.0],
                          "avg_waiting_hours": [10.0], "vessel_availability_count": [25],
                          "weather_risk_score": [4.0], "event_risk_score": [3.0]})
    shock = ScenarioShock(port_congestion_shock_pct=50, target_port="Paradip")
    revised = build_shocked_forecast_df(frame, shock, "IN_PDP")
    assert revised.loc[0, "port_congestion_score"] == 60.0
    assert revised.loc[0, "avg_waiting_hours"] == 15.0
    assert revised.loc[0, "weather_risk_score"] == 4.0
    assert revised.loc[0, "event_risk_score"] == 3.0
    assert frame.loc[0, "port_congestion_score"] == 40.0


def test_arena_rejects_invalid_simulation_count():
    response = client.post("/web/strategy-arena", json={"arena_simulations_count": 10})
    assert response.status_code == 422


def test_backtest_does_not_claim_forecast_context_was_carried_forward():
    response = client.post("/web/backtest", json={
        "route_key": "AU_GLT -> IN_PDP", "start_date": "2026-01-01",
        "end_date": "2026-02-01", "step_days": 30,
    })
    assert response.status_code == 200, response.text
    assert "operational_context" not in response.json()


def test_unshocked_scenario_keeps_same_confidence_on_selected_route():
    response = client.post("/web/scenario", json={"route_key": "AU_GLT -> IN_PDP"})
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["route_key"] == "AU_GLT -> IN_PDP"
    confidence = next(row for row in result["comparison_table"] if row["metric"] == "Decision Confidence")
    assert confidence["baseline"] == confidence["stress_scenario"]
    assert not confidence["changed"]
    assert "Despite shock conditions" not in result["explanation"]


def test_demurrage_scenario_explains_computed_exposure():
    response = client.post("/web/scenario", json={
        "route_key": "AU_GLT -> IN_PDP", "shock": {"demurrage_rate_shock_pct": 30}
    })
    assert response.status_code == 200, response.text
    result = response.json()
    assert "Configured demurrage rate change: +30%" in result["explanation"]
    assert result["stressed_recommendation"]["demurrage_cost_usd"] > result["baseline_recommendation"]["demurrage_cost_usd"]


def test_arena_pdf_exports_same_decision_evidence():
    response = client.post("/web/arena-report", json={"arena_simulations_count": 50})
    assert response.status_code == 200, response.text
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF-")
    from pypdf import PdfReader
    import io
    content = "\n".join(page.extract_text() for page in PdfReader(io.BytesIO(response.content)).pages)
    assert "Decision Arena" in content
    assert "CVaR90" in content
    assert "SYNTHETIC / MODELLED" in content
    assert "USD" not in content
    assert "$" not in content


def test_reported_freight_break_even_actually_changes_charter_date():
    from backend.web_api import forecast, history
    from backend.optimizer import optimize_charter_timing

    route = "AU_HPT -> IN_PDP"
    result = client.post("/web/strategy-arena", json={
        "route_key": route, "arena_simulations_count": 50
    }).json()
    counter = result["counterfactual"]
    assert counter["status"] == "threshold_found"
    history_df = history(route)
    frame = forecast(route, 14, "Auto")["forecast_df"].copy(deep=True)
    for field in ("port_congestion_score", "avg_waiting_hours", "vessel_availability_count",
                  "weather_risk_score", "event_risk_score"):
        frame[field] = history_df.iloc[-1][field]
    selected_date = result["selected_action"]["charter_date"]
    selected_row = frame.date.dt.strftime("%Y-%m-%d") == selected_date

    def selected_after(increase_pct):
        revised = frame.copy(deep=True)
        revised.loc[selected_row, "predicted_freight_rate"] *= 1 + increase_pct / 100
        return optimize_charter_timing(
            revised, cargo_type="Coking Coal", quantity_tonnes=75000,
            origin="AU_HPT", destination="IN_PDP"
        )["best_option"]["charter_date"]

    assert selected_after(counter["freight_increase_pct"]) == counter["new_date"]
    assert selected_after(counter["freight_increase_pct"] - 0.01) == selected_date
