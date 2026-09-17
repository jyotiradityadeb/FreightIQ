"""
FreightIQ Integrations Unit Tests

Tests base adapter contract, normalized schemas, provenance fields,
unconfigured LIVE_READY fallback handling, and integration manager.
"""

import pytest
from backend.integrations.base_adapter import BaseAdapter
from backend.integrations.freight_adapter import FreightAdapter
from backend.integrations.ais_adapter import AISAdapter
from backend.integrations.commodity_adapter import CommodityAdapter
from backend.integrations.port_adapter import PortAdapter
from backend.integrations.weather_adapter import WeatherAdapter
from backend.integrations.integration_manager import IntegrationManager


def test_freight_adapter_schema():
    """Freight adapter returns valid normalized schema & provenance."""
    adapter = FreightAdapter(mode="DEMO")
    latest = adapter.get_latest()

    assert "freight_rate" in latest
    assert "bdi" in latest
    assert "source_name" in latest
    assert "source_mode" in latest
    assert latest["source_mode"] == "DEMO"
    assert "retrieved_at" in latest


def test_ais_adapter_schema():
    """AIS adapter returns valid vessel supply schema."""
    adapter = AISAdapter(mode="DEMO")
    latest = adapter.get_latest()

    assert "vessel_class" in latest
    assert "available_count" in latest
    assert latest["available_count"] >= 0
    assert "source_name" in latest


def test_commodity_adapter_schema():
    """Commodity adapter returns valid price schema."""
    adapter = CommodityAdapter(mode="DEMO")
    latest = adapter.get_latest()

    assert "coking_coal_price" in latest
    assert "iron_ore_price" in latest


def test_port_adapter_schema():
    """Port adapter returns valid congestion schema."""
    adapter = PortAdapter(mode="DEMO")
    latest = adapter.get_latest()

    assert "port" in latest
    assert "congestion_score" in latest
    assert "avg_waiting_hours" in latest


def test_weather_adapter_schema():
    """Weather adapter returns valid risk schema."""
    adapter = WeatherAdapter(mode="DEMO")
    latest = adapter.get_latest()

    assert "weather_risk_score" in latest
    assert "event_risk_score" in latest


def test_unconfigured_live_ready_fallback():
    """Unconfigured LIVE_READY adapter reports NOT_CONFIGURED status gracefully without crashing."""
    adapter = FreightAdapter(mode="LIVE_READY")
    health = adapter.health_check()

    assert health["mode"] == "LIVE_READY"
    assert health["status"] == "NOT_CONFIGURED"
    assert health["is_configured"] is False

    # Calling get_latest should not crash and should return valid fallback
    latest = adapter.get_latest()
    assert "freight_rate" in latest
    assert latest["source_mode"] == "LIVE_READY"


def test_integration_manager_summary():
    """Integration manager aggregates connector status and dataset provenance."""
    manager = IntegrationManager(mode="DEMO")
    status_summary = manager.get_connector_status_summary()
    prov_summary = manager.get_dataset_provenance_summary()

    assert len(status_summary) == 5
    assert prov_summary["mode"] == "Synthetic Demo"
    assert prov_summary["record_count"] > 0
    assert len(prov_summary["sources"]) == 5
