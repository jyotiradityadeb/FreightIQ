"""
FreightIQ Global Port Master Domain Module
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class PortSpecification(BaseModel):
    port_id: str
    port_name: str
    country: str
    region: str
    latitude: float
    longitude: float
    max_draft_m: float
    cargo_categories: List[str]
    congestion_source: str = "Synthetic Demo Feed"
    waiting_time_source: str = "Synthetic Demo Feed"
    status: str = "Active Operational Node"
    data_freshness_policy: str = "DAILY"
    is_assumption: bool = True


PORT_MASTER: Dict[str, PortSpecification] = {
    # INDIA EAST COAST DESTINATION PORTS
    "Paradip": PortSpecification(
        port_id="Paradip",
        port_name="Paradip Port",
        country="India",
        region="East Coast India",
        latitude=20.2644,
        longitude=86.6744,
        max_draft_m=17.5,
        cargo_categories=["Coking Coal", "Thermal Coal", "Iron Ore", "Limestone", "Bauxite"],
        is_assumption=True
    ),
    "Visakhapatnam": PortSpecification(
        port_id="Visakhapatnam",
        port_name="Visakhapatnam Port (Vizag)",
        country="India",
        region="East Coast India",
        latitude=17.6868,
        longitude=83.2185,
        max_draft_m=18.1,
        cargo_categories=["Coking Coal", "Iron Ore", "Manganese Ore", "Thermal Coal"],
        is_assumption=True
    ),
    "Gangavaram": PortSpecification(
        port_id="Gangavaram",
        port_name="Gangavaram Deepwater Port",
        country="India",
        region="East Coast India",
        latitude=17.6200,
        longitude=83.2350,
        max_draft_m=19.5,
        cargo_categories=["Coking Coal", "Iron Ore", "Capesize Imports"],
        is_assumption=True
    ),
    "Dhamra": PortSpecification(
        port_id="Dhamra",
        port_name="Dhamra Port",
        country="India",
        region="East Coast India",
        latitude=20.8000,
        longitude=86.9700,
        max_draft_m=18.0,
        cargo_categories=["Coking Coal", "Thermal Coal", "Iron Ore"],
        is_assumption=True
    ),
    "Haldia": PortSpecification(
        port_id="Haldia",
        port_name="Haldia Dock Complex (Kolkata Port Trust)",
        country="India",
        region="East Coast India",
        latitude=22.0258,
        longitude=88.0583,
        max_draft_m=12.5,
        cargo_categories=["Coking Coal", "Thermal Coal", "Limestone", "Dolomite"],
        is_assumption=True
    ),
    "Kolkata": PortSpecification(
        port_id="Kolkata",
        port_name="Kolkata Port",
        country="India",
        region="East Coast India",
        latitude=22.5400,
        longitude=88.3300,
        max_draft_m=10.5,
        cargo_categories=["Handysize Cargo", "Break Bulk"],
        is_assumption=True
    ),
    "Ennore": PortSpecification(
        port_id="Ennore",
        port_name="Ennore / Kamarajar Port",
        country="India",
        region="East Coast India",
        latitude=13.2600,
        longitude=80.3300,
        max_draft_m=16.0,
        cargo_categories=["Thermal Coal", "Iron Ore", "Car Carrier"],
        is_assumption=True
    ),
    "Chennai": PortSpecification(
        port_id="Chennai",
        port_name="Chennai Port",
        country="India",
        region="East Coast India",
        latitude=13.0827,
        longitude=80.2707,
        max_draft_m=15.0,
        cargo_categories=["Containers", "Dry Bulk", "Cars"],
        is_assumption=True
    ),
    "Krishnapatnam": PortSpecification(
        port_id="Krishnapatnam",
        port_name="Krishnapatnam Port",
        country="India",
        region="East Coast India",
        latitude=14.2500,
        longitude=80.1200,
        max_draft_m=18.5,
        cargo_categories=["Thermal Coal", "Coking Coal", "Containers"],
        is_assumption=True
    ),

    # MAJOR OVERSEAS BULK ORIGIN PORTS / REGIONS
    "Australia": PortSpecification(
        port_id="Australia",
        port_name="Hay Point / Gladstone / Newcastle (Australia Region)",
        country="Australia",
        region="Queensland / NSW",
        latitude=-21.2833,
        longitude=149.3000,
        max_draft_m=20.0,
        cargo_categories=["Coking Coal", "Thermal Coal", "Grain"],
        is_assumption=True
    ),
    "Indonesia": PortSpecification(
        port_id="Indonesia",
        port_name="Taboneo / Samarinda (Indonesia Region)",
        country="Indonesia",
        region="South Kalimantan",
        latitude=-3.6000,
        longitude=114.5000,
        max_draft_m=15.0,
        cargo_categories=["Thermal Coal", "Bauxite"],
        is_assumption=True
    ),
    "South Africa": PortSpecification(
        port_id="South Africa",
        port_name="Richards Bay (South Africa Region)",
        country="South Africa",
        region="KwaZulu-Natal",
        latitude=-28.8000,
        longitude=32.0833,
        max_draft_m=19.0,
        cargo_categories=["Thermal Coal", "Manganese Ore", "Chromite"],
        is_assumption=True
    ),
    "Mozambique": PortSpecification(
        port_id="Mozambique",
        port_name="Nacala / Beira (Mozambique Region)",
        country="Mozambique",
        region="Nampula",
        latitude=-14.5500,
        longitude=40.6833,
        max_draft_m=18.0,
        cargo_categories=["Coking Coal"],
        is_assumption=True
    ),
    "Brazil": PortSpecification(
        port_id="Brazil",
        port_name="Tubarao / Itaqui (Brazil Region)",
        country="Brazil",
        region="Espirito Santo",
        latitude=-20.2833,
        longitude=-40.2500,
        max_draft_m=22.0,
        cargo_categories=["Iron Ore", "Pellets"],
        is_assumption=True
    )
}


def get_port_by_id(port_id: str) -> Optional[PortSpecification]:
    """Retrieves a port specification by ID or name."""
    if port_id in PORT_MASTER:
        return PORT_MASTER[port_id]
    for pid, port in PORT_MASTER.items():
        if port.port_name.lower() == port_id.lower():
            return port
    return None


def get_ports_by_region(region: str) -> List[PortSpecification]:
    """Returns ports belonging to a region or country."""
    reg_lower = region.lower()
    return [
        p for p in PORT_MASTER.values()
        if reg_lower in p.region.lower() or reg_lower in p.country.lower()
    ]

