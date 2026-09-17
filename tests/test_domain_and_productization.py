"""
Tests for FreightIQ Domain Masters, Navigation, Storage, Data Quality, and Productization.
"""

import os
import pytest
from backend.domain.commodities import (
    COMMODITY_CATALOGUE,
    get_all_commodities,
    get_commodity,
    create_custom_commodity
)
from backend.domain.vessels import (
    VESSEL_MASTER,
    get_vessel_by_class,
    get_all_vessel_classes
)
from backend.domain.ports import (
    PORT_MASTER,
    get_port_by_id,
    get_ports_by_region
)
from backend.domain.routes import (
    ROUTE_MASTER,
    get_route,
    calculate_transit_days
)
from backend.data_quality import (
    DataMode,
    FreshnessStatus,
    evaluate_freshness,
    evaluate_decision_confidence,
    DataQualityEngine
)
from backend.storage import (
    init_db,
    save_shipment_to_db,
    load_shipment_from_db,
    save_decision_version,
    get_decision_history,
    log_audit_event,
    get_audit_logs
)
from app.navigation import (
    CONTROL_TOWER_PAGE,
    DECISION_TWIN_PAGE,
    CHARTER_PAGE,
    get_all_pages
)
from app.components.error_boundary import safe_render_section


def test_commodity_master():
    commodities = get_all_commodities()
    assert len(commodities) >= 15, "Commodity master must have at least 15 dry-bulk commodities"
    
    coal = get_commodity("coking_coal")
    assert coal is not None
    assert coal.display_name == "Coking Coal"
    assert coal.bulk_type == "Major Bulk"


def test_custom_cargo_creation():
    custom = create_custom_commodity(
        cargo_name="Custom Metallurgical Slag",
        quantity_tonnes=50000.0,
        stowage_factor=1.4,
        preferred_vessel_class="Panamax",
        demurrage_rate_usd_day=16000.0
    )
    assert custom.commodity_id.startswith("custom_")
    assert custom.display_name == "Custom: Custom Metallurgical Slag"
    assert custom.typical_lot_min == 25000.0
    assert custom.default_demurrage_rate_usd_day == 16000.0


def test_vessel_master():
    vessels = get_all_vessel_classes()
    assert len(vessels) >= 9, "Vessel master must support at least 9 vessel classes"
    
    panamax = get_vessel_by_class("Panamax")
    assert panamax is not None
    assert panamax.min_dwt == 65000.0
    assert panamax.max_dwt == 81999.0


def test_port_master():
    paradip = get_port_by_id("Paradip")
    assert paradip is not None
    assert paradip.country == "India"
    assert paradip.is_assumption is True
    assert paradip.status == "Active Operational Node"
    
    east_coast_ports = get_ports_by_region("East Coast India")
    assert len(east_coast_ports) >= 8


def test_route_master():
    route = get_route("Hay Point", "Paradip")
    assert route is not None
    assert route.distance_nm > 0
    
    days = calculate_transit_days("Hay Point", "Paradip", speed_knots=13.0)
    assert days > 0


def test_data_quality_and_freshness():
    status = evaluate_freshness("weather", age_seconds=300)
    assert status == FreshnessStatus.FRESH
    
    stale_status = evaluate_freshness("freight_benchmark", age_seconds=200000)
    assert stale_status == FreshnessStatus.STALE

    confidence = evaluate_decision_confidence(
        coverage_pct=90.0,
        live_signals_count=3,
        total_signals_count=7
    )
    assert 0 <= confidence.score <= 100
    assert confidence.confidence_tier in ["High", "Medium", "Low"]


def test_sqlite_storage(tmp_path):
    db_file = str(tmp_path / "test_workspace.db")
    init_db(db_file)
    
    # Test saving & loading shipment
    save_shipment_to_db("FIQ-TEST-001", "Coking Coal", 75000.0, "Hay Point", "Paradip", db_path=db_file)
    loaded = load_shipment_from_db("FIQ-TEST-001", db_path=db_file)
    assert loaded is not None
    assert loaded["shipment_id"] == "FIQ-TEST-001"
    assert loaded["cargo_type"] == "Coking Coal"
    assert loaded["quantity_tonnes"] == 75000.0
    
    # Test decision versioning
    rec_dict = {"vessel_class": "Panamax", "charter_date": "2026-09-20", "total_cost": 1500000}
    save_decision_version("FIQ-TEST-001", 1, rec_dict, "Initial recommendation", db_path=db_file)
    history = get_decision_history("FIQ-TEST-001", db_path=db_file)
    assert len(history) == 1
    assert history[0]["version"] == 1

    # Test audit logging
    log_audit_event("FIQ-TEST-001", "CHARTER_EVALUATED", "Evaluated Panamax option", db_path=db_file)
    logs = get_audit_logs("FIQ-TEST-001", db_path=db_file)
    assert len(logs) >= 1
    assert logs[0]["action"] == "CHARTER_EVALUATED"


def test_navigation_constants():
    pages = get_all_pages()
    assert len(pages) == 10
    assert CONTROL_TOWER_PAGE in pages
    assert DECISION_TWIN_PAGE in pages
    assert CHARTER_PAGE in pages


def test_error_boundary_helper():
    called = []
    def working_func():
        called.append(True)
        return "OK"
        
    safe_render_section("Test Section", working_func)
    assert called == [True]

    def broken_func():
        raise ValueError("Simulated render failure")

    # Should not raise exception, but render fallback safely
    called_fallback = []
    def fallback_func():
        called_fallback.append(True)

    safe_render_section("Broken Section", broken_func, fallback_message="Custom Fallback")
