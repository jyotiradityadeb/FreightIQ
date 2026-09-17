"""
FreightIQ Maritime Voyage Master & Route Engine
"""

from typing import Dict, Any, List
from pydantic import BaseModel, Field


class RouteSpecification(BaseModel):
    origin_id: str
    destination_id: str
    route_key: str
    distance_nm: float
    estimated_transit_days: float
    canal_or_chokepoint: str = "Direct Ocean Passage"
    base_freight_multiplier: float = 1.0
    allowed_vessel_classes: List[str] = Field(default_factory=lambda: ["Capesize", "Panamax", "Supramax"])
    weather_risk_index: float = 2.5
    geopolitical_risk_index: float = 1.0
    assumption_source: str = "FreightIQ Maritime Distance Matrix"


ROUTE_MASTER: Dict[str, RouteSpecification] = {
    # AUSTRALIA ROUTES
    "Australia -> Paradip": RouteSpecification(
        origin_id="Australia",
        destination_id="Paradip",
        route_key="Australia -> Paradip",
        distance_nm=4850.0,
        estimated_transit_days=14.5,
        canal_or_chokepoint="Lombok Strait / Malacca Strait",
        base_freight_multiplier=1.00,
        allowed_vessel_classes=["Capesize", "Panamax", "Supramax", "Kamsarmax", "Newcastlemax"]
    ),
    "Australia -> Visakhapatnam": RouteSpecification(
        origin_id="Australia",
        destination_id="Visakhapatnam",
        route_key="Australia -> Visakhapatnam",
        distance_nm=4620.0,
        estimated_transit_days=13.8,
        canal_or_chokepoint="Malacca Strait",
        base_freight_multiplier=0.96,
        allowed_vessel_classes=["Capesize", "Panamax", "Supramax", "Gangavaram"]
    ),
    "Australia -> Gangavaram": RouteSpecification(
        origin_id="Australia",
        destination_id="Gangavaram",
        route_key="Australia -> Gangavaram",
        distance_nm=4600.0,
        estimated_transit_days=13.7,
        canal_or_chokepoint="Malacca Strait",
        base_freight_multiplier=0.95,
        allowed_vessel_classes=["Capesize", "Panamax", "Supramax", "Newcastlemax"]
    ),
    "Australia -> Dhamra": RouteSpecification(
        origin_id="Australia",
        destination_id="Dhamra",
        route_key="Australia -> Dhamra",
        distance_nm=4880.0,
        estimated_transit_days=14.6,
        canal_or_chokepoint="Lombok Strait",
        base_freight_multiplier=1.01,
        allowed_vessel_classes=["Capesize", "Panamax", "Supramax"]
    ),
    "Australia -> Haldia": RouteSpecification(
        origin_id="Australia",
        destination_id="Haldia",
        route_key="Australia -> Haldia",
        distance_nm=5100.0,
        estimated_transit_days=15.5,
        canal_or_chokepoint="Malacca Strait",
        base_freight_multiplier=1.06,
        allowed_vessel_classes=["Panamax", "Supramax", "Handymax"]
    ),

    # INDONESIA ROUTES
    "Indonesia -> Paradip": RouteSpecification(
        origin_id="Indonesia",
        destination_id="Paradip",
        route_key="Indonesia -> Paradip",
        distance_nm=2450.0,
        estimated_transit_days=7.5,
        canal_or_chokepoint="Malacca Strait",
        base_freight_multiplier=0.62,
        allowed_vessel_classes=["Capesize", "Panamax", "Supramax"]
    ),
    "Indonesia -> Visakhapatnam": RouteSpecification(
        origin_id="Indonesia",
        destination_id="Visakhapatnam",
        route_key="Indonesia -> Visakhapatnam",
        distance_nm=2200.0,
        estimated_transit_days=6.8,
        canal_or_chokepoint="Malacca Strait",
        base_freight_multiplier=0.58,
        allowed_vessel_classes=["Capesize", "Panamax", "Supramax"]
    ),
    "Indonesia -> Haldia": RouteSpecification(
        origin_id="Indonesia",
        destination_id="Haldia",
        route_key="Indonesia -> Haldia",
        distance_nm=2600.0,
        estimated_transit_days=8.0,
        canal_or_chokepoint="Malacca Strait",
        base_freight_multiplier=0.66,
        allowed_vessel_classes=["Panamax", "Supramax", "Handymax"]
    ),

    # SOUTH AFRICA ROUTES
    "South Africa -> Paradip": RouteSpecification(
        origin_id="South Africa",
        destination_id="Paradip",
        route_key="South Africa -> Paradip",
        distance_nm=4550.0,
        estimated_transit_days=13.5,
        canal_or_chokepoint="Mozambique Channel",
        base_freight_multiplier=0.94,
        allowed_vessel_classes=["Capesize", "Panamax", "Supramax"]
    ),
    "South Africa -> Visakhapatnam": RouteSpecification(
        origin_id="South Africa",
        destination_id="Visakhapatnam",
        route_key="South Africa -> Visakhapatnam",
        distance_nm=4400.0,
        estimated_transit_days=13.0,
        canal_or_chokepoint="Indian Ocean Passage",
        base_freight_multiplier=0.91,
        allowed_vessel_classes=["Capesize", "Panamax", "Supramax"]
    ),
    "South Africa -> Haldia": RouteSpecification(
        origin_id="South Africa",
        destination_id="Haldia",
        route_key="South Africa -> Haldia",
        distance_nm=4750.0,
        estimated_transit_days=14.2,
        canal_or_chokepoint="Indian Ocean Passage",
        base_freight_multiplier=0.98,
        allowed_vessel_classes=["Panamax", "Supramax", "Handymax"]
    ),

    # MOZAMBIQUE ROUTES
    "Mozambique -> Paradip": RouteSpecification(
        origin_id="Mozambique",
        destination_id="Paradip",
        route_key="Mozambique -> Paradip",
        distance_nm=3900.0,
        estimated_transit_days=11.5,
        canal_or_chokepoint="Mozambique Channel",
        base_freight_multiplier=0.85,
        allowed_vessel_classes=["Capesize", "Panamax", "Supramax"]
    ),

    # BRAZIL ROUTES
    "Brazil -> Paradip": RouteSpecification(
        origin_id="Brazil",
        destination_id="Paradip",
        route_key="Brazil -> Paradip",
        distance_nm=11200.0,
        estimated_transit_days=33.0,
        canal_or_chokepoint="Cape of Good Hope",
        base_freight_multiplier=1.85,
        allowed_vessel_classes=["Capesize", "Newcastlemax"]
    )
}


def get_route_info(origin: str, destination: str) -> RouteSpecification:
    """Helper to retrieve or synthesize route info between any origin and destination."""
    key = f"{origin} -> {destination}"
    if key in ROUTE_MASTER:
        return ROUTE_MASTER[key]
    
    # Synthesize fallback route
    return RouteSpecification(
        origin_id=origin,
        destination_id=destination,
        route_key=key,
        distance_nm=4500.0,
        estimated_transit_days=13.5,
        canal_or_chokepoint="Direct Marine Route",
        base_freight_multiplier=1.0,
        allowed_vessel_classes=["Capesize", "Panamax", "Supramax"]
    )


def get_route(origin: str, destination: str) -> RouteSpecification:
    """Alias for get_route_info."""
    return get_route_info(origin, destination)


def calculate_transit_days(origin: str, destination: str, speed_knots: float = 13.5) -> float:
    """Calculates estimated voyage transit days based on distance and vessel speed."""
    info = get_route_info(origin, destination)
    speed = max(5.0, speed_knots)
    hours = info.distance_nm / speed
    return round(hours / 24.0, 1)

