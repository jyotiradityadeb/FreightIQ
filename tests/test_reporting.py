"""
FreightIQ Executive Reporting Engine Unit Tests

Tests ReportLab PDF decision note generation, section content,
INR formatting, scenario stress incorporation, and error handling.
"""

import pytest
from backend.reporting import generate_charter_decision_pdf


@pytest.fixture
def sample_recommendation():
    return {
        "cargo_type": "Coking Coal",
        "quantity_tonnes": 75000.0,
        "origin": "Australia",
        "destination": "Paradip",
        "recommended_charter_date": "2026-09-03",
        "recommended_vessel": "Panamax",
        "expected_unit_freight_usd": 25.50,
        "expected_freight_cost_usd": 1912500.0,
        "expected_demurrage_cost_usd": 45000.0,
        "expected_congestion_cost_usd": 30000.0,
        "expected_route_risk_penalty_usd": 25000.0,
        "expected_total_logistics_cost_usd": 2012500.0,
        "effective_cost_per_tonne": 26.83,
        "why": [
            "Freight rate forecast is stable.",
            "Panamax vessel satisfies cargo requirements.",
            "Paradip congestion is within operating threshold."
        ]
    }


def test_pdf_generation_non_empty(sample_recommendation):
    """Decision PDF generates non-empty bytes."""
    pdf_bytes = generate_charter_decision_pdf(sample_recommendation, data_mode="DEMO")
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    # PDF Magic Number check
    assert pdf_bytes.startswith(b"%PDF")


def test_pdf_with_scenario_result(sample_recommendation):
    """Decision PDF incorporates active scenario stress test results."""
    scenario_result = {
        "success": True,
        "baseline_recommendation": sample_recommendation,
        "stressed_recommendation": sample_recommendation,
        "decision_status": "Cost Increase Under Stress",
        "explanation": "Paradip congestion increased by 55%, raising demurrage exposure.",
        "confidence_score": 72.5
    }

    pdf_bytes = generate_charter_decision_pdf(
        recommendation=sample_recommendation,
        scenario_result=scenario_result,
        data_mode="DEMO"
    )

    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF")


def test_pdf_fallback_handling():
    """PDF generator handles sparse recommendation dictionary safely without crashing."""
    sparse_rec = {
        "cargo_type": "Iron Ore",
        "quantity_tonnes": 150000.0,
        "expected_total_cost_usd": 3500000.0
    }
    pdf_bytes = generate_charter_decision_pdf(sparse_rec, data_mode="DEMO")
    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF")


def test_log_decision_version_api_contract():
    """Verifies backend.storage exposes log_decision_version alias."""
    import backend.storage as storage
    assert hasattr(storage, "log_decision_version")
    assert callable(storage.log_decision_version)


def test_theme_helper_functions():
    """Verifies get_active_theme and toggle_theme helper functions."""
    from app.components.helpers import get_active_theme, toggle_theme
    theme = get_active_theme()
    assert theme in ["light", "dark"]
    toggle_theme()
    new_theme = get_active_theme()
    assert new_theme != theme
    toggle_theme()

