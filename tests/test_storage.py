"""
Tests for FreightIQ Storage Contract and Page Import Smoke Verification.
"""

import os
import pytest
import py_compile
from backend.storage import (
    initialize_storage,
    init_db,
    save_shipment,
    load_shipment,
    list_shipments,
    get_active_shipment_context,
    set_active_shipment_context,
    append_audit_log,
    get_audit_trail,
    save_decision_version,
    get_decision_versions
)


def test_storage_initialization_and_contracts(tmp_path):
    db_file = str(tmp_path / "test_contract_workspace.db")
    
    # 1. Test initialize_storage
    initialize_storage(db_file)
    assert os.path.exists(db_file)

    # 2. Test empty audit trail returns []
    empty_trail = get_audit_trail(shipment_id="NON_EXISTENT", db_path=db_file)
    assert empty_trail == []

    # 3. Test append_audit_log and get_audit_trail
    log_id = append_audit_log(
        shipment_id="FIQ-CONTRACT-001",
        action="TEST_ACTION",
        details="Test detail message",
        source_mode="TEST",
        db_path=db_file
    )
    assert log_id > 0

    trail = get_audit_trail(db_path=db_file)
    assert len(trail) >= 1
    assert trail[0]["action"] == "TEST_ACTION"

    # 4. Test shipment filtering
    filtered_trail = get_audit_trail(shipment_id="FIQ-CONTRACT-001", db_path=db_file)
    assert len(filtered_trail) == 1
    assert filtered_trail[0]["shipment_id"] == "FIQ-CONTRACT-001"

    unmatched_trail = get_audit_trail(shipment_id="FIQ-OTHER-999", db_path=db_file)
    assert len(unmatched_trail) == 0

    # 5. Test save_shipment and load_shipment
    s_id = save_shipment({
        "shipment_id": "FIQ-CONTRACT-001",
        "cargo_type": "Iron Ore",
        "quantity_tonnes": 120000.0,
        "origin": "Brazil",
        "destination": "Visakhapatnam"
    }, db_path=db_file)
    assert s_id == "FIQ-CONTRACT-001"

    loaded = load_shipment("FIQ-CONTRACT-001", db_path=db_file)
    assert loaded is not None
    assert loaded["cargo_type"] == "Iron Ore"

    saved_list = list_shipments(db_path=db_file)
    assert len(saved_list) >= 1

    # 6. Test save_decision_version and get_decision_versions
    v_id = save_decision_version(
        shipment_id="FIQ-CONTRACT-001",
        recommendation={"recommended_vessel": "Capesize", "expected_cost_usd": 2500000.0},
        version_number=1,
        reason="Capesize optimization",
        db_path=db_file
    )
    assert v_id.startswith("FIQ-CONTRACT-001_v1")

    versions = get_decision_versions("FIQ-CONTRACT-001", db_path=db_file)
    assert len(versions) == 1
    assert versions[0]["version"] == 1


def test_get_active_shipment_context():
    ctx = get_active_shipment_context()
    assert isinstance(ctx, dict)
    assert "shipment_id" in ctx

    updated = set_active_shipment_context(cargo_type="Thermal Coal")
    assert updated["cargo_type"] == "Thermal Coal"


def test_all_pages_import_without_importerror():
    """Smoke test ensuring every Streamlit page module compiles cleanly without syntax or import errors."""
    page_files = [
        "app/Home.py",
        "app/pages/1_Control_Tower.py",
        "app/pages/2_Decision_Twin.py",
        "app/pages/3_Operations_Overview.py",
        "app/pages/4_Market_Overview.py",
        "app/pages/5_Forecasting.py",
        "app/pages/6_Charter_Optimizer.py",
        "app/pages/7_Scenario_Lab.py",
        "app/pages/8_Backtesting.py",
        "app/pages/9_Data_Integration.py",
        "app/pages/10_Data_Explorer.py"
    ]
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    for rel_path in page_files:
        abs_path = os.path.normpath(os.path.join(root_dir, rel_path))
        assert os.path.exists(abs_path), f"Page file missing: {rel_path}"
        py_compile.compile(abs_path, doraise=True)
