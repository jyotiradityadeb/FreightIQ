"""
FreightIQ Vessel Master Domain Module
"""

from typing import Dict, Any, List
from pydantic import BaseModel, Field


class VesselSpecification(BaseModel):
    vessel_class: str
    min_dwt: float
    max_dwt: float
    typical_capacity_tonnes: float
    typical_draft_m: float
    base_daily_charter_multiplier: float
    daily_demurrage_rate_usd: float
    cargo_compatibility: List[str]
    compatible_ports: List[str]
    speed_knots: float = 13.5
    fuel_consumption_t_day: float = 28.0
    availability_group: str = "Dry Bulk Fleets"


VESSEL_MASTER: Dict[str, VesselSpecification] = {
    "Handysize": VesselSpecification(
        vessel_class="Handysize",
        min_dwt=10000,
        max_dwt=39999,
        typical_capacity_tonnes=28000,
        typical_draft_m=10.2,
        base_daily_charter_multiplier=0.75,
        daily_demurrage_rate_usd=12000.0,
        cargo_compatibility=["Minor Bulk", "Limestone", "Met Coke", "Grain"],
        compatible_ports=["Paradip", "Visakhapatnam", "Haldia", "Kolkata", "Chennai", "Ennore"]
    ),
    "Handymax": VesselSpecification(
        vessel_class="Handymax",
        min_dwt=40000,
        max_dwt=49999,
        typical_capacity_tonnes=45000,
        typical_draft_m=11.5,
        base_daily_charter_multiplier=0.85,
        daily_demurrage_rate_usd=14000.0,
        cargo_compatibility=["Minor Bulk", "Thermal Coal", "Manganese Ore", "Fertilizer"],
        compatible_ports=["Paradip", "Visakhapatnam", "Haldia", "Gangavaram", "Ennore"]
    ),
    "Supramax": VesselSpecification(
        vessel_class="Supramax",
        min_dwt=50000,
        max_dwt=59999,
        typical_capacity_tonnes=55000,
        typical_draft_m=12.5,
        base_daily_charter_multiplier=0.90,
        daily_demurrage_rate_usd=16000.0,
        cargo_compatibility=["Coking Coal", "Thermal Coal", "Iron Ore", "Limestone"],
        compatible_ports=["Paradip", "Visakhapatnam", "Haldia", "Gangavaram", "Dhamra", "Ennore"]
    ),
    "Ultramax": VesselSpecification(
        vessel_class="Ultramax",
        min_dwt=60000,
        max_dwt=64999,
        typical_capacity_tonnes=62000,
        typical_draft_m=13.0,
        base_daily_charter_multiplier=0.95,
        daily_demurrage_rate_usd=18000.0,
        cargo_compatibility=["Coking Coal", "Thermal Coal", "Bauxite", "Iron Ore"],
        compatible_ports=["Paradip", "Visakhapatnam", "Gangavaram", "Dhamra", "Ennore"]
    ),
    "Panamax": VesselSpecification(
        vessel_class="Panamax",
        min_dwt=65000,
        max_dwt=81999,
        typical_capacity_tonnes=75000,
        typical_draft_m=14.2,
        base_daily_charter_multiplier=1.00,
        daily_demurrage_rate_usd=22000.0,
        cargo_compatibility=["Coking Coal", "Thermal Coal", "Iron Ore", "Bauxite", "Grain"],
        compatible_ports=["Paradip", "Visakhapatnam", "Gangavaram", "Dhamra", "Ennore", "Krishnapatnam"]
    ),
    "Kamsarmax": VesselSpecification(
        vessel_class="Kamsarmax",
        min_dwt=82000,
        max_dwt=89999,
        typical_capacity_tonnes=85000,
        typical_draft_m=14.5,
        base_daily_charter_multiplier=1.05,
        daily_demurrage_rate_usd=23000.0,
        cargo_compatibility=["Bauxite", "Coking Coal", "Thermal Coal", "Iron Ore"],
        compatible_ports=["Paradip", "Visakhapatnam", "Gangavaram", "Dhamra"]
    ),
    "Post-Panamax": VesselSpecification(
        vessel_class="Post-Panamax",
        min_dwt=90000,
        max_dwt=119999,
        typical_capacity_tonnes=98000,
        typical_draft_m=15.2,
        base_daily_charter_multiplier=1.15,
        daily_demurrage_rate_usd=24000.0,
        cargo_compatibility=["Coking Coal", "Iron Ore", "Thermal Coal"],
        compatible_ports=["Paradip", "Visakhapatnam", "Gangavaram", "Dhamra"]
    ),
    "Capesize": VesselSpecification(
        vessel_class="Capesize",
        min_dwt=120000,
        max_dwt=199999,
        typical_capacity_tonnes=175000,
        typical_draft_m=18.0,
        base_daily_charter_multiplier=1.40,
        daily_demurrage_rate_usd=28000.0,
        cargo_compatibility=["Iron Ore", "Coking Coal", "Bauxite"],
        compatible_ports=["Paradip", "Visakhapatnam", "Gangavaram", "Dhamra"]
    ),
    "Newcastlemax": VesselSpecification(
        vessel_class="Newcastlemax",
        min_dwt=200000,
        max_dwt=220000,
        typical_capacity_tonnes=205000,
        typical_draft_m=18.8,
        base_daily_charter_multiplier=1.60,
        daily_demurrage_rate_usd=32000.0,
        cargo_compatibility=["Iron Ore", "Coking Coal"],
        compatible_ports=["Paradip", "Visakhapatnam", "Gangavaram"]
    )
}


def get_vessel_by_class(vessel_class: str) -> VesselSpecification:
    """Retrieves vessel specification for a given vessel class name."""
    if vessel_class in VESSEL_MASTER:
        return VESSEL_MASTER[vessel_class]
    # Default to Panamax if unknown
    return VESSEL_MASTER["Panamax"]


def get_all_vessel_classes() -> Dict[str, VesselSpecification]:
    """Returns dictionary of all vessel specifications."""
    return VESSEL_MASTER

