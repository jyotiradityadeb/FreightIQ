"""
FreightIQ Route Market & Cross-Page Route Consistency Regression Test Suite
"""

import pytest
import pandas as pd
import numpy as np

from backend.domain.routes import get_calibrated_routes, resolve_route
from backend.route_market import (
    get_route_market_profile,
    get_route_seed,
    generate_all_route_markets,
    get_all_route_market_histories,
    get_route_market_history,
    get_available_route_keys
)
from backend.forecasting import generate_freight_forecast
from backend.optimizer import evaluate_charter_candidate, optimize_charter_timing
from backend.decision_twin import compute_decision_twin_hash, DecisionTwinEngine, get_or_compute_decision_twin
from backend.scenario_engine import build_shocked_forecast_df
from backend.schemas import ScenarioShock
from backend.backtesting import run_historical_simulation
from backend.reporting import generate_charter_decision_pdf
from app.components.charts import plot_forecast_with_ci, apply_industrial_theme
import plotly.graph_objects as go


def test_route_histories_unique_and_correlated():
    """Verify that different route histories are distinct and not byte-identical."""
    r1 = get_route_market_history("AU_HPT -> IN_PDP")
    r2 = get_route_market_history("AU_PHE -> IN_PDP")
    r3 = get_route_market_history("BR_PDM -> IN_GAV")
    r4 = get_route_market_history("ZA_RCB -> IN_HAL")

    assert not r1["freight_rate"].equals(r2["freight_rate"])
    assert not r1["freight_rate"].equals(r3["freight_rate"])
    assert not r3["freight_rate"].equals(r4["freight_rate"])

    corr12 = r1["freight_rate"].corr(r2["freight_rate"])
    assert abs(corr12) < 0.999
    assert corr12 > 0.3  # Shared dry-bulk macro factor maintains positive correlation


def test_deterministic_regeneration():
    """Verify that regenerating route market series produce identical results."""
    s1 = get_route_seed("AU_HPT -> IN_PDP")
    s2 = get_route_seed("AU_HPT -> IN_PDP")
    assert s1 == s2

    h1 = get_route_market_history("AU_HPT -> IN_PDP")
    h2 = get_route_market_history("AU_HPT -> IN_PDP")
    assert h1["freight_rate"].equals(h2["freight_rate"])


def test_canonical_route_ids_resolution():
    """Verify that get_route_market_history resolves canonical route keys and port IDs."""
    keys = get_available_route_keys()
    assert "AU_HPT -> IN_PDP" in keys
    assert "BR_PDM -> IN_PDP" in keys

    h_port = get_route_market_history("AU_HPT -> IN_VTZ")
    assert len(h_port) > 0
    assert "freight_ma_14" in h_port.columns


def test_route_forecast_uses_correct_history():
    """Verify forecasting runs directly on selected route's synthetic history."""
    df_au = get_route_market_history("AU_HPT -> IN_PDP")
    df_br = get_route_market_history("BR_PDM -> IN_PDP")

    fc_au = generate_freight_forecast(df_au, horizon=14, selected_model="Auto")
    fc_br = generate_freight_forecast(df_br, horizon=14, selected_model="Auto")

    mean_au = fc_au["forecast_df"]["predicted_freight_rate"].mean()
    mean_br = fc_br["forecast_df"]["predicted_freight_rate"].mean()

    # Ponta da Madeira (Brazil) rate level is significantly higher than Hay Point (Australia)
    assert mean_br > mean_au + 5.0


def test_decision_twin_hash_includes_route():
    """Verify that Decision Twin hash incorporates route_key and origin/destination ports."""
    ctx1 = {
        "shipment_id": "FIQ-1", "origin": "Hay Point", "origin_port_id": "AU_HPT",
        "destination": "Paradip", "destination_port_id": "IN_PDP",
        "quantity_tonnes": 75000, "cargo_type": "Coking Coal"
    }
    ctx2 = {
        "shipment_id": "FIQ-1", "origin": "Ponta da Madeira", "origin_port_id": "BR_PDM",
        "destination": "Gangavaram", "destination_port_id": "IN_GAV",
        "quantity_tonnes": 75000, "cargo_type": "Iron Ore Fines"
    }

    hash1 = compute_decision_twin_hash(ctx1)
    hash2 = compute_decision_twin_hash(ctx2)

    assert hash1 != hash2


def test_scenario_shock_applies_to_route_baseline():
    """Verify scenario shock applies to selected route baseline."""
    df_route = get_route_market_history("ZA_RCB -> IN_HAL")
    shock = ScenarioShock(freight_rate_shock_pct=20.0, target_port="Haldia")

    df_shocked = build_shocked_forecast_df(df_route, shock, destination="Haldia")
    base_rate = df_route["freight_rate"].iloc[0]
    shocked_rate = df_shocked["predicted_freight_rate"].iloc[0]

    assert abs(shocked_rate - base_rate * 1.20) < 0.01


def test_backtesting_route_integration():
    """Verify walk-forward simulation runs on route-specific synthetic dataset."""
    df_route = get_route_market_history("ID_TBN -> IN_PDP")
    res = run_historical_simulation(
        df=df_route,
        start_date="2024-06-01",
        end_date="2024-09-01",
        horizon=14,
        step_days=14,
        origin="Taboneo",
        destination="Paradip",
        cargo_type="Thermal Coal"
    )

    assert res["success"] is True
    assert res["test_periods_count"] > 0


def test_pdf_report_route_propagation():
    """Verify PDF report generation accepts route-specific recommendation."""
    rec = {
        "shipment_id": "TEST-PDF-001",
        "origin": "Ponta da Madeira",
        "destination": "Paradip",
        "cargo_type": "Iron Ore Fines",
        "quantity_tonnes": 150000.0,
        "recommended_window": "2026-09-25",
        "vessel_class": "Capesize",
        "expected_total_cost_usd": 4200000.0,
        "status": "RECOMMENDATION VALID"
    }
    pdf_bytes = generate_charter_decision_pdf(rec)
    assert pdf_bytes is not None
    assert len(pdf_bytes) > 5000


def test_no_undefined_text_in_charts():
    """Verify that Plotly figures and industrial styling do not emit literal 'undefined' string."""
    df_route = get_route_market_history("AU_HPT -> IN_PDP")
    fc_res = generate_freight_forecast(df_route, horizon=14)

    fig = plot_forecast_with_ci(df_route, fc_res["forecast_df"], title="")
    fig_json = fig.to_json()

    assert "undefined" not in fig_json
    assert "None" not in fig.layout.title.text if fig.layout.title and fig.layout.title.text else True
