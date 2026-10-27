"""Integration boundaries for the Stitch-derived local interface."""

from fastapi.testclient import TestClient
from io import BytesIO
from io import StringIO

import pandas as pd
import pytest
from pypdf import PdfReader

from backend.main import app
import backend.stitch_api as stitch_api


client = TestClient(app)


def test_catalog_supplies_vessel_speed_for_transit_estimate():
    response = client.get("/web/catalog")
    assert response.status_code == 200
    data = response.json()
    assert data["vessel_speeds_knots"]["Panamax"] > 0
    assert any(route["route_key"] == "AU_GLT -> IN_PDP" for route in data["routes"])


def test_explorer_summary_uses_processed_dataset():
    response = client.get("/stitch/explorer-summary")
    assert response.status_code == 200
    data = response.json()
    assert data["observations"] > 0
    assert data["features"] == len(data["quality"])
    assert data["is_demo_data"] is True


def test_explorer_csv_exports_monetary_columns_in_inr():
    for kind in ("route", "dataset"):
        response = client.get(f"/stitch/export/{kind}")
        assert response.status_code == 200
        frame = pd.read_csv(StringIO(response.text), nrows=1)
        assert "freight_rate_inr_per_tonne" in frame
        assert "freight_rate" not in frame
        assert frame["freight_rate_inr_per_tonne"].iloc[0] > 100
        assert not any("usd" in name.lower() for name in frame.columns)


def test_solve_records_the_python_recommendation(monkeypatch):
    calls = []
    monkeypatch.setattr(stitch_api, "calculate", lambda action, req: {
        "success": True,
        "recommendation": {"recommended_charter_date": "2026-09-04", "recommended_vessel": "Panamax",
                           "expected_total_logistics_cost_usd": 1059300},
    })
    monkeypatch.setattr(stitch_api, "save_shipment", lambda data: calls.append(("shipment", data)))
    monkeypatch.setattr(stitch_api, "save_decision_version",
                        lambda shipment_id, recommendation: calls.append(("decision", recommendation)) or "FIQ-2026-0001_v1")
    response = client.post("/stitch/solve", json={"route_key": "AU_HPT -> IN_PDP"})
    assert response.status_code == 200
    assert response.json()["decision_version"] == "FIQ-2026-0001_v1"
    assert calls[0][0] == "shipment"
    assert calls[1][1]["recommended_vessel"] == "Panamax"


def test_operator_note_is_audit_only(monkeypatch):
    calls = []
    monkeypatch.setattr(stitch_api, "append_audit_log", lambda **kwargs: calls.append(kwargs) or 7)
    response = client.post("/stitch/operator-note", json={
        "congestion": 45, "vessel_count": 25, "demurrage_inr_day": 1800000
    })
    assert response.status_code == 200
    assert calls[0]["action"] == "MANUAL_OVERRIDE_RECORDED"
    assert "not changed" in response.json()["message"]


def test_backtest_uses_fixed_panamax_scope():
    response = client.post("/web/backtest", json={
        "start_date": "2026-01-01", "end_date": "2026-03-01", "step_days": 30
    })
    assert response.status_code == 200
    assert response.json()["test_periods_count"] > 0


@pytest.mark.parametrize("route_key,route_label,origin_name", [
    ("AU_HPT -> IN_PDP", "AU_HPT", "Hay Point"),
    ("MZ_MNC -> IN_PDP", "MZ_MNC", "Nacala"),
])
def test_downloaded_decision_report_includes_actual_analyses(route_key, route_label, origin_name):
    response = client.post("/web/report", json={"route_key": route_key})
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    text = "\n".join(page.extract_text() for page in PdfReader(BytesIO(response.content)).pages)

    assert route_label in text
    assert origin_name in text
    assert "Not evaluated for this report" not in text
    assert "DECISION TWIN & ROBUSTNESS ANALYSIS" in text
    assert "SCENARIO ANALYSIS & STRESS TESTING" in text
    assert "Synthetic walk-forward simulation" in text
    assert "Synthetic demo-series validation" in text
    assert "not an independent final test" in text
    assert "External validation" in text
    assert "DEMO / SYNTHETIC" in text
    assert "USD" not in text
    assert "$" not in text
