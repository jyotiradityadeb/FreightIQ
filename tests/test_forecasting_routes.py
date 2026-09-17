"""
Tests for Freight Forecasting Canonical Route Catalog Integration, Active Shipment Sync,
and Unsupported Route Behavior.
"""

import pytest
from backend.domain.routes import get_calibrated_routes, resolve_route
from app.components.helpers import get_active_shipment_context, update_active_shipment_context


def test_forecasting_route_list_from_canonical_calibrated_catalog():
    routes = get_calibrated_routes()
    assert len(routes) >= 15, f"Expected at least 15 calibrated routes, got {len(routes)}"

    for r in routes:
        assert "display_label" in r
        assert "route_key" in r
        assert "origin_port_id" in r
        assert "destination_port_id" in r
        assert "base_freight_multiplier" in r

    labels = [r["display_label"] for r in routes]
    assert len(labels) == len(set(labels)), "Route display labels must contain no duplicates"


def test_default_route_is_au_hpt_to_in_pdp():
    routes = get_calibrated_routes()
    first_route = routes[0]
    assert first_route["origin_port_id"] == "AU_HPT"
    assert first_route["destination_port_id"] == "IN_PDP"
    assert "Hay Point" in first_route["display_label"]
    assert "Paradip" in first_route["display_label"]


def test_active_shipment_route_synchronization():
    update_active_shipment_context(
        origin="Richards Bay",
        origin_port_id="ZA_RCB",
        destination="Haldia",
        destination_port_id="IN_HAL"
    )

    ctx = get_active_shipment_context()
    assert ctx["origin_port_id"] == "ZA_RCB"
    assert ctx["destination_port_id"] == "IN_HAL"

    route_res = resolve_route(ctx["origin_port_id"], ctx["destination_port_id"])
    assert route_res.is_calibrated is True
    assert route_res.origin_port_id == "ZA_RCB"
    assert route_res.destination_port_id == "IN_HAL"


def test_unsupported_active_route_does_not_silently_fallback():
    # Set an uncalibrated catalog-only route as active shipment
    update_active_shipment_context(
        origin="Hampton Roads / Norfolk",
        origin_port_id="US_ORF",
        destination="Mundra",
        destination_port_id="IN_MUN"
    )

    ctx = get_active_shipment_context()
    route_res = resolve_route(ctx["origin_port_id"], ctx["destination_port_id"])

    assert route_res.is_calibrated is False
    assert route_res.status == "UNSUPPORTED"
    assert "not calibrated" in route_res.message.lower()
