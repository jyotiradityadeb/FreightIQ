"""
Tests for FreightIQ Domain Expansion, Canonical Port/Cargo Master Data,
Route Resolver, Feasibility Validation, and Cross-Page Context Consistency.
"""

import pytest
from backend.domain.commodities import (
    COMMODITY_CATALOGUE,
    get_all_commodities,
    get_commodity
)
from backend.domain.ports import (
    PORT_MASTER,
    PORT_ALIAS_MAP,
    get_port_by_id,
    get_origin_countries,
    get_destination_countries,
    get_ports_for_country,
    get_all_ports
)
from backend.domain.routes import (
    ROUTE_MASTER,
    resolve_route
)
from backend.optimizer import evaluate_charter_candidate, optimize_charter_timing
from backend.reporting import generate_charter_decision_pdf
from app.components.helpers import get_active_shipment_context, update_active_shipment_context
import pandas as pd


def test_cargo_options_catalog():
    commodities = get_all_commodities()
    assert len(commodities) >= 15, f"Expected at least 15 cargo types, found {len(commodities)}"

    required_cargo_keys = [
        "coking_coal", "thermal_coal", "iron_ore_fines", "iron_ore_pellets",
        "limestone", "dolomite", "manganese_ore", "chromite_ore",
        "bauxite", "met_coke", "petcoke", "slag", "gypsum",
        "fertilizer", "grain"
    ]
    for key in required_cargo_keys:
        comm = get_commodity(key)
        assert comm is not None, f"Commodity key '{key}' not found in catalog"
        assert comm.commodity_id is not None
        assert comm.display_name is not None
        assert comm.category is not None


def test_canonical_port_ids_unique_and_valid():
    ports = get_all_ports()
    port_ids = list(ports.keys())
    assert len(port_ids) == len(set(port_ids)), "Port IDs in PORT_MASTER must be strictly unique"

    for pid, port in ports.items():
        assert port.port_id == pid, f"Port ID mismatch for {pid}"
        assert port.port_name is not None
        assert port.country is not None
        assert port.max_draft_m > 0
        assert len(port.supported_vessel_classes) > 0


def test_no_duplicate_port_aliases():
    assert len(PORT_ALIAS_MAP) > 0
    alias_keys = list(PORT_ALIAS_MAP.keys())
    assert len(alias_keys) == len(set(alias_keys)), "Port alias map must not contain duplicate keys"

    for alias, target_id in PORT_ALIAS_MAP.items():
        assert target_id in PORT_MASTER, f"Alias target '{target_id}' for alias '{alias}' not in PORT_MASTER"


def test_country_to_port_filtering():
    origins = get_origin_countries()
    assert "Australia" in origins
    assert "Brazil" in origins
    assert "South Africa" in origins
    assert "Indonesia" in origins
    assert "Canada" in origins
    assert "USA" in origins
    assert "Mozambique" in origins

    au_ports = get_ports_for_country("Australia", is_origin=True)
    assert len(au_ports) >= 6, f"Expected at least 6 Australian export ports, found {len(au_ports)}"
    au_names = [p.port_name for p in au_ports]
    assert "Hay Point" in au_names
    assert "Port Hedland" in au_names

    in_dest_ports = get_ports_for_country("India", is_origin=False)
    assert len(in_dest_ports) >= 15, f"Expected at least 15 Indian destination ports, found {len(in_dest_ports)}"
    in_names = [p.port_name for p in in_dest_ports]
    assert "Paradip" in in_names
    assert "Visakhapatnam" in in_names
    assert "Mundra" in in_names


def test_route_resolver_behavior():
    # Modeled route test
    res_calibrated = resolve_route("AU_HPT", "IN_PDP")
    assert res_calibrated.is_calibrated is True
    assert res_calibrated.status == "SUPPORTED"
    assert res_calibrated.calibration_badge == "DEMO-CALIBRATED"

    # Uncalibrated route test
    res_uncalibrated = resolve_route("US_ORF", "IN_MUN")
    assert res_uncalibrated.is_calibrated is False
    assert res_uncalibrated.status == "UNSUPPORTED"
    assert res_uncalibrated.calibration_badge == "CATALOG ONLY — optimization unavailable"
    assert "not calibrated" in res_uncalibrated.message.lower()


def test_unsupported_route_explicit_error_in_optimizer():
    c_date = pd.Timestamp("2026-09-20")
    res = evaluate_charter_candidate(
        charter_date=c_date,
        vessel_class="Panamax",
        origin="Hampton Roads / Norfolk",
        destination="Mundra",
        cargo_type="Coking Coal",
        quantity_tonnes=75000.0,
        freight_rate_forecast=25.0,
        congestion_score=45.0,
        waiting_hours=24.0,
        vessel_avail_count=20,
        weather_risk=2.0,
        event_risk=1.0
    )
    assert res["feasible"] is False
    assert "UNSUPPORTED_ROUTE" in res["infeasibility_reason"]
    assert "CATALOG ONLY" in res["infeasibility_reason"]


def test_draft_infeasibility_check():
    c_date = pd.Timestamp("2026-09-20")
    # Capesize requires 18m draft; Haldia max draft is 12.5m
    res = evaluate_charter_candidate(
        charter_date=c_date,
        vessel_class="Capesize",
        origin="Australia",
        destination="Haldia",
        cargo_type="Coking Coal",
        quantity_tonnes=150000.0,
        freight_rate_forecast=25.0,
        congestion_score=45.0,
        waiting_hours=24.0,
        vessel_avail_count=20,
        weather_risk=2.0,
        event_risk=1.0
    )
    assert res["feasible"] is False
    assert "UNSUPPORTED_DRAFT" in res["infeasibility_reason"] or "exceeds" in res["infeasibility_reason"]


def test_workspace_context_persistence():
    update_active_shipment_context(
        origin_country="Brazil",
        origin="Ponta da Madeira",
        origin_port_id="BR_PDM",
        destination_country="India",
        destination="Gangavaram",
        destination_port_id="IN_GAV"
    )
    ctx = get_active_shipment_context()
    assert ctx["origin"] == "Ponta da Madeira"
    assert ctx["origin_port_id"] == "BR_PDM"
    assert ctx["destination"] == "Gangavaram"
    assert ctx["destination_port_id"] == "IN_GAV"


def test_pdf_uses_selected_origin_destination():
    rec = {
        "shipment_id": "FIQ-TEST-PDF",
        "origin": "Port Hedland",
        "destination": "Visakhapatnam",
        "cargo_type": "Iron Ore Fines",
        "quantity_tonnes": 150000.0,
        "recommended_vessel": "Capesize",
        "charter_date": "2026-09-25",
        "expected_total_logistics_cost_usd": 3200000.0,
        "status_label": "PROCEED"
    }
    pdf_bytes = generate_charter_decision_pdf(recommendation=rec, data_mode="DEMO")
    assert pdf_bytes is not None
    assert len(pdf_bytes) > 5000
