"""
Unit tests for FreightIQ PDF Reporting & Truthfulness
"""

import io
import pytest
from backend.reporting import generate_charter_decision_pdf, format_pdf_inr_val


def test_format_pdf_inr_val_truthfulness():
    assert format_pdf_inr_val(None) == "N/A"
    assert format_pdf_inr_val(0.0) == "INR 0"
    assert "Lakh" in format_pdf_inr_val(1_800_000.0)
    assert "Cr" in format_pdf_inr_val(185_800_000.0)


def test_pdf_truthfulness_when_results_none():
    rec = {
        "shipment_id": "TEST-001",
        "cargo_type": "Coking Coal",
        "quantity_tonnes": 75000.0,
        "origin": "Australia",
        "destination": "Paradip",
        "recommended_vessel": "Panamax",
        "charter_date": "2026-09-20",
        "expected_total_cost_usd": 1800000.0,
        "freight_cost_usd": None, # Missing freight cost
        "demurrage_cost_usd": None,
    }

    pdf_bytes = generate_charter_decision_pdf(
        recommendation=rec,
        decision_twin_result=None,
        scenario_result=None,
        backtest_metrics=None,
        synthetic_validation=None,
        real_validation=None,
        data_mode="DEMO"
    )

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0

    # Extract text using pypdf if available or check string representation
    import pypdf
    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    full_text = "\n".join([p.extract_text() for p in reader.pages])

    # Must contain "Not evaluated for this report."
    assert "Not evaluated for this report." in full_text

    # Must NOT contain hardcoded fallbacks
    assert "82/100" not in full_text
    assert "83% simulated" not in full_text
    assert "18.0 Lakh" not in full_text
    assert "MAE ~INR 105/t" not in full_text


def test_pdf_truthfulness_with_actual_results():
    rec = {
        "shipment_id": "TEST-002",
        "cargo_type": "Iron Ore",
        "quantity_tonnes": 150000.0,
        "origin": "Brazil",
        "destination": "Visakhapatnam",
        "recommended_vessel": "Capesize",
        "charter_date": "2026-09-25",
        "expected_total_cost_usd": 3500000.0,
        "expected_freight_cost_usd": 3000000.0,
        "expected_demurrage_cost_usd": 300000.0,
        "expected_congestion_cost_usd": 150000.0,
        "expected_route_risk_penalty_usd": 50000.0,
    }

    dt_res = {
        "success": True,
        "simulations_count": 500,
        "hero_summary": {
            "robustness_score": 91.5,
            "robustness_label": "High",
            "expected_regret_inr_lakh": 5.2,
            "recommendation_reason": "Optimal across futures"
        }
    }

    pdf_bytes = generate_charter_decision_pdf(
        recommendation=rec,
        decision_twin_result=dt_res,
        data_mode="DEMO"
    )

    import pypdf
    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    full_text = "\n".join([p.extract_text() for p in reader.pages])

    assert "92 / 100" in full_text or "91 / 100" in full_text or "High" in full_text
    assert "500 paths" in full_text
