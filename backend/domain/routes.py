"""
FreightIQ Maritime Voyage Master & Route Engine
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from backend.domain.ports import get_port_by_id


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


class RouteResolution(BaseModel):
    status: str = "SUPPORTED"  # "SUPPORTED" or "UNSUPPORTED"
    is_calibrated: bool = True
    calibration_badge: str = "DEMO-CALIBRATED"
    route_key: str = ""
    origin_port_id: str = ""
    destination_port_id: str = ""
    origin_name: str = ""
    destination_name: str = ""
    distance_nm: Optional[float] = None
    estimated_transit_days: Optional[float] = None
    base_freight_multiplier: float = 1.0
    allowed_vessel_classes: List[str] = Field(default_factory=lambda: ["Capesize", "Panamax", "Supramax"])
    message: str = ""
    route_spec: Optional[RouteSpecification] = None


ROUTE_MASTER: Dict[str, RouteSpecification] = {
    # AUSTRALIA ROUTES (CANONICAL + LEGACY)
    "AU_HPT -> IN_PDP": RouteSpecification(
        origin_id="AU_HPT",
        destination_id="IN_PDP",
        route_key="AU_HPT -> IN_PDP",
        distance_nm=4850.0,
        estimated_transit_days=14.5,
        canal_or_chokepoint="Lombok Strait / Malacca Strait",
        base_freight_multiplier=1.00,
        allowed_vessel_classes=["Capesize", "Panamax", "Supramax", "Newcastlemax"]
    ),
    "Australia -> Paradip": RouteSpecification(
        origin_id="AU_HPT",
        destination_id="IN_PDP",
        route_key="Australia -> Paradip",
        distance_nm=4850.0,
        estimated_transit_days=14.5,
        canal_or_chokepoint="Lombok Strait / Malacca Strait",
        base_freight_multiplier=1.00,
        allowed_vessel_classes=["Capesize", "Panamax", "Supramax", "Kamsarmax", "Newcastlemax"]
    ),
    "AU_DBT -> IN_PDP": RouteSpecification(
        origin_id="AU_DBT",
        destination_id="IN_PDP",
        route_key="AU_DBT -> IN_PDP",
        distance_nm=4840.0,
        estimated_transit_days=14.4,
        canal_or_chokepoint="Lombok Strait",
        base_freight_multiplier=1.00,
        allowed_vessel_classes=["Capesize", "Panamax", "Supramax"]
    ),
    "AU_GLT -> IN_PDP": RouteSpecification(
        origin_id="AU_GLT",
        destination_id="IN_PDP",
        route_key="AU_GLT -> IN_PDP",
        distance_nm=4900.0,
        estimated_transit_days=14.7,
        canal_or_chokepoint="Malacca Strait",
        base_freight_multiplier=1.02,
        allowed_vessel_classes=["Panamax", "Capesize", "Supramax"]
    ),
    "AU_NCW -> IN_PDP": RouteSpecification(
        origin_id="AU_NCW",
        destination_id="IN_PDP",
        route_key="AU_NCW -> IN_PDP",
        distance_nm=5200.0,
        estimated_transit_days=15.6,
        canal_or_chokepoint="Bass Strait / Malacca Strait",
        base_freight_multiplier=1.08,
        allowed_vessel_classes=["Panamax", "Capesize", "Supramax"]
    ),
    "AU_PHE -> IN_PDP": RouteSpecification(
        origin_id="AU_PHE",
        destination_id="IN_PDP",
        route_key="AU_PHE -> IN_PDP",
        distance_nm=3600.0,
        estimated_transit_days=10.8,
        canal_or_chokepoint="Lombok Strait",
        base_freight_multiplier=0.88,
        allowed_vessel_classes=["Capesize", "Newcastlemax", "Panamax"]
    ),
    "AU_DAM -> IN_PDP": RouteSpecification(
        origin_id="AU_DAM",
        destination_id="IN_PDP",
        route_key="AU_DAM -> IN_PDP",
        distance_nm=3550.0,
        estimated_transit_days=10.6,
        canal_or_chokepoint="Sunda Strait",
        base_freight_multiplier=0.87,
        allowed_vessel_classes=["Capesize", "Newcastlemax"]
    ),
    "Australia -> Visakhapatnam": RouteSpecification(
        origin_id="AU_HPT",
        destination_id="IN_VTZ",
        route_key="Australia -> Visakhapatnam",
        distance_nm=4620.0,
        estimated_transit_days=13.8,
        canal_or_chokepoint="Malacca Strait",
        base_freight_multiplier=0.96,
        allowed_vessel_classes=["Capesize", "Panamax", "Supramax"]
    ),
    "AU_HPT -> IN_VTZ": RouteSpecification(
        origin_id="AU_HPT",
        destination_id="IN_VTZ",
        route_key="AU_HPT -> IN_VTZ",
        distance_nm=4620.0,
        estimated_transit_days=13.8,
        canal_or_chokepoint="Malacca Strait",
        base_freight_multiplier=0.96,
        allowed_vessel_classes=["Capesize", "Panamax", "Supramax"]
    ),
    "AU_HPT -> IN_GAV": RouteSpecification(
        origin_id="AU_HPT",
        destination_id="IN_GAV",
        route_key="AU_HPT -> IN_GAV",
        distance_nm=4600.0,
        estimated_transit_days=13.7,
        canal_or_chokepoint="Malacca Strait",
        base_freight_multiplier=0.95,
        allowed_vessel_classes=["Capesize", "Panamax", "Supramax", "Newcastlemax"]
    ),
    "Australia -> Gangavaram": RouteSpecification(
        origin_id="AU_HPT",
        destination_id="IN_GAV",
        route_key="Australia -> Gangavaram",
        distance_nm=4600.0,
        estimated_transit_days=13.7,
        canal_or_chokepoint="Malacca Strait",
        base_freight_multiplier=0.95,
        allowed_vessel_classes=["Capesize", "Panamax", "Supramax", "Newcastlemax"]
    ),
    "AU_HPT -> IN_DHM": RouteSpecification(
        origin_id="AU_HPT",
        destination_id="IN_DHM",
        route_key="AU_HPT -> IN_DHM",
        distance_nm=4880.0,
        estimated_transit_days=14.6,
        canal_or_chokepoint="Lombok Strait",
        base_freight_multiplier=1.01,
        allowed_vessel_classes=["Capesize", "Panamax", "Supramax"]
    ),
    "Australia -> Dhamra": RouteSpecification(
        origin_id="AU_HPT",
        destination_id="IN_DHM",
        route_key="Australia -> Dhamra",
        distance_nm=4880.0,
        estimated_transit_days=14.6,
        canal_or_chokepoint="Lombok Strait",
        base_freight_multiplier=1.01,
        allowed_vessel_classes=["Capesize", "Panamax", "Supramax"]
    ),
    "AU_HPT -> IN_HAL": RouteSpecification(
        origin_id="AU_HPT",
        destination_id="IN_HAL",
        route_key="AU_HPT -> IN_HAL",
        distance_nm=5100.0,
        estimated_transit_days=15.5,
        canal_or_chokepoint="Malacca Strait",
        base_freight_multiplier=1.06,
        allowed_vessel_classes=["Panamax", "Supramax", "Handymax"]
    ),
    "Australia -> Haldia": RouteSpecification(
        origin_id="AU_HPT",
        destination_id="IN_HAL",
        route_key="Australia -> Haldia",
        distance_nm=5100.0,
        estimated_transit_days=15.5,
        canal_or_chokepoint="Malacca Strait",
        base_freight_multiplier=1.06,
        allowed_vessel_classes=["Panamax", "Supramax", "Handymax"]
    ),

    # INDONESIA ROUTES
    "ID_TBN -> IN_PDP": RouteSpecification(
        origin_id="ID_TBN",
        destination_id="IN_PDP",
        route_key="ID_TBN -> IN_PDP",
        distance_nm=2450.0,
        estimated_transit_days=7.5,
        canal_or_chokepoint="Malacca Strait",
        base_freight_multiplier=0.62,
        allowed_vessel_classes=["Capesize", "Panamax", "Supramax"]
    ),
    "Indonesia -> Paradip": RouteSpecification(
        origin_id="ID_TBN",
        destination_id="IN_PDP",
        route_key="Indonesia -> Paradip",
        distance_nm=2450.0,
        estimated_transit_days=7.5,
        canal_or_chokepoint="Malacca Strait",
        base_freight_multiplier=0.62,
        allowed_vessel_classes=["Capesize", "Panamax", "Supramax"]
    ),
    "ID_BPN -> IN_VTZ": RouteSpecification(
        origin_id="ID_BPN",
        destination_id="IN_VTZ",
        route_key="ID_BPN -> IN_VTZ",
        distance_nm=2200.0,
        estimated_transit_days=6.8,
        canal_or_chokepoint="Malacca Strait",
        base_freight_multiplier=0.58,
        allowed_vessel_classes=["Capesize", "Panamax", "Supramax"]
    ),
    "Indonesia -> Visakhapatnam": RouteSpecification(
        origin_id="ID_TBN",
        destination_id="IN_VTZ",
        route_key="Indonesia -> Visakhapatnam",
        distance_nm=2200.0,
        estimated_transit_days=6.8,
        canal_or_chokepoint="Malacca Strait",
        base_freight_multiplier=0.58,
        allowed_vessel_classes=["Capesize", "Panamax", "Supramax"]
    ),
    "ID_TBN -> IN_HAL": RouteSpecification(
        origin_id="ID_TBN",
        destination_id="IN_HAL",
        route_key="ID_TBN -> IN_HAL",
        distance_nm=2600.0,
        estimated_transit_days=8.0,
        canal_or_chokepoint="Malacca Strait",
        base_freight_multiplier=0.66,
        allowed_vessel_classes=["Panamax", "Supramax", "Handymax"]
    ),
    "Indonesia -> Haldia": RouteSpecification(
        origin_id="ID_TBN",
        destination_id="IN_HAL",
        route_key="Indonesia -> Haldia",
        distance_nm=2600.0,
        estimated_transit_days=8.0,
        canal_or_chokepoint="Malacca Strait",
        base_freight_multiplier=0.66,
        allowed_vessel_classes=["Panamax", "Supramax", "Handymax"]
    ),

    # SOUTH AFRICA ROUTES
    "ZA_RCB -> IN_PDP": RouteSpecification(
        origin_id="ZA_RCB",
        destination_id="IN_PDP",
        route_key="ZA_RCB -> IN_PDP",
        distance_nm=4550.0,
        estimated_transit_days=13.5,
        canal_or_chokepoint="Mozambique Channel",
        base_freight_multiplier=0.94,
        allowed_vessel_classes=["Capesize", "Panamax", "Supramax"]
    ),
    "South Africa -> Paradip": RouteSpecification(
        origin_id="ZA_RCB",
        destination_id="IN_PDP",
        route_key="South Africa -> Paradip",
        distance_nm=4550.0,
        estimated_transit_days=13.5,
        canal_or_chokepoint="Mozambique Channel",
        base_freight_multiplier=0.94,
        allowed_vessel_classes=["Capesize", "Panamax", "Supramax"]
    ),
    "ZA_RCB -> IN_VTZ": RouteSpecification(
        origin_id="ZA_RCB",
        destination_id="IN_VTZ",
        route_key="ZA_RCB -> IN_VTZ",
        distance_nm=4400.0,
        estimated_transit_days=13.0,
        canal_or_chokepoint="Indian Ocean Passage",
        base_freight_multiplier=0.91,
        allowed_vessel_classes=["Capesize", "Panamax", "Supramax"]
    ),
    "South Africa -> Visakhapatnam": RouteSpecification(
        origin_id="ZA_RCB",
        destination_id="IN_VTZ",
        route_key="South Africa -> Visakhapatnam",
        distance_nm=4400.0,
        estimated_transit_days=13.0,
        canal_or_chokepoint="Indian Ocean Passage",
        base_freight_multiplier=0.91,
        allowed_vessel_classes=["Capesize", "Panamax", "Supramax"]
    ),
    "ZA_RCB -> IN_HAL": RouteSpecification(
        origin_id="ZA_RCB",
        destination_id="IN_HAL",
        route_key="ZA_RCB -> IN_HAL",
        distance_nm=4750.0,
        estimated_transit_days=14.2,
        canal_or_chokepoint="Indian Ocean Passage",
        base_freight_multiplier=0.98,
        allowed_vessel_classes=["Panamax", "Supramax", "Handymax"]
    ),
    "South Africa -> Haldia": RouteSpecification(
        origin_id="ZA_RCB",
        destination_id="IN_HAL",
        route_key="South Africa -> Haldia",
        distance_nm=4750.0,
        estimated_transit_days=14.2,
        canal_or_chokepoint="Indian Ocean Passage",
        base_freight_multiplier=0.98,
        allowed_vessel_classes=["Panamax", "Supramax", "Handymax"]
    ),

    # MOZAMBIQUE ROUTES
    "MZ_MNC -> IN_PDP": RouteSpecification(
        origin_id="MZ_MNC",
        destination_id="IN_PDP",
        route_key="MZ_MNC -> IN_PDP",
        distance_nm=3900.0,
        estimated_transit_days=11.5,
        canal_or_chokepoint="Mozambique Channel",
        base_freight_multiplier=0.85,
        allowed_vessel_classes=["Capesize", "Panamax", "Supramax"]
    ),
    "Mozambique -> Paradip": RouteSpecification(
        origin_id="MZ_MNC",
        destination_id="IN_PDP",
        route_key="Mozambique -> Paradip",
        distance_nm=3900.0,
        estimated_transit_days=11.5,
        canal_or_chokepoint="Mozambique Channel",
        base_freight_multiplier=0.85,
        allowed_vessel_classes=["Capesize", "Panamax", "Supramax"]
    ),

    # BRAZIL ROUTES
    "BR_PDM -> IN_PDP": RouteSpecification(
        origin_id="BR_PDM",
        destination_id="IN_PDP",
        route_key="BR_PDM -> IN_PDP",
        distance_nm=11200.0,
        estimated_transit_days=33.0,
        canal_or_chokepoint="Cape of Good Hope",
        base_freight_multiplier=1.85,
        allowed_vessel_classes=["Capesize", "Newcastlemax", "Valemax"]
    ),
    "BR_PDM -> IN_GAV": RouteSpecification(
        origin_id="BR_PDM",
        destination_id="IN_GAV",
        route_key="BR_PDM -> IN_GAV",
        distance_nm=11150.0,
        estimated_transit_days=32.8,
        canal_or_chokepoint="Cape of Good Hope",
        base_freight_multiplier=1.83,
        allowed_vessel_classes=["Capesize", "Newcastlemax", "Valemax"]
    ),
    "Brazil -> Paradip": RouteSpecification(
        origin_id="BR_PDM",
        destination_id="IN_PDP",
        route_key="Brazil -> Paradip",
        distance_nm=11200.0,
        estimated_transit_days=33.0,
        canal_or_chokepoint="Cape of Good Hope",
        base_freight_multiplier=1.85,
        allowed_vessel_classes=["Capesize", "Newcastlemax"]
    ),

    # INDIAN DOMESTIC COASTAL MOVEMENTS
    "IN_PDP -> IN_MAA": RouteSpecification(
        origin_id="IN_PDP",
        destination_id="IN_MAA",
        route_key="IN_PDP -> IN_MAA",
        distance_nm=650.0,
        estimated_transit_days=2.1,
        canal_or_chokepoint="Bay of Bengal Coastal Passage",
        base_freight_multiplier=0.25,
        allowed_vessel_classes=["Panamax", "Supramax", "Handymax"]
    ),
    "IN_PDP -> IN_VTZ": RouteSpecification(
        origin_id="IN_PDP",
        destination_id="IN_VTZ",
        route_key="IN_PDP -> IN_VTZ",
        distance_nm=280.0,
        estimated_transit_days=1.0,
        canal_or_chokepoint="Bay of Bengal Coastal Passage",
        base_freight_multiplier=0.15,
        allowed_vessel_classes=["Capesize", "Panamax", "Supramax"]
    ),
    "IN_PDP -> IN_TUT": RouteSpecification(
        origin_id="IN_PDP",
        destination_id="IN_TUT",
        route_key="IN_PDP -> IN_TUT",
        distance_nm=820.0,
        estimated_transit_days=2.6,
        canal_or_chokepoint="Palk Strait Outer Passage",
        base_freight_multiplier=0.30,
        allowed_vessel_classes=["Panamax", "Supramax"]
    )
}


def resolve_route(origin_id_or_name: str, destination_id_or_name: str) -> RouteResolution:
    """
    Canonical route resolver: evaluates whether a route between origin and destination
    is calibrated in model data or catalog-only.
    """
    orig_port = get_port_by_id(origin_id_or_name)
    dest_port = get_port_by_id(destination_id_or_name)

    orig_id = orig_port.port_id if orig_port else origin_id_or_name
    dest_id = dest_port.port_id if dest_port else destination_id_or_name
    orig_name = orig_port.port_name if orig_port else origin_id_or_name
    dest_name = dest_port.port_name if dest_port else destination_id_or_name

    candidate_keys = [
        f"{orig_id} -> {dest_id}",
        f"{orig_name} -> {dest_name}",
        f"{origin_id_or_name} -> {destination_id_or_name}",
    ]
    if orig_port:
        candidate_keys.append(f"{orig_port.country} -> {dest_name}")
        candidate_keys.append(f"{orig_port.country} -> {dest_id}")

    for k in candidate_keys:
        if k in ROUTE_MASTER:
            spec = ROUTE_MASTER[k]
            return RouteResolution(
                status="SUPPORTED",
                is_calibrated=True,
                calibration_badge="DEMO-CALIBRATED",
                route_key=spec.route_key,
                origin_port_id=orig_id,
                destination_port_id=dest_id,
                origin_name=orig_name,
                destination_name=dest_name,
                distance_nm=spec.distance_nm,
                estimated_transit_days=spec.estimated_transit_days,
                base_freight_multiplier=spec.base_freight_multiplier,
                allowed_vessel_classes=spec.allowed_vessel_classes,
                message="Route calibrated in demo model.",
                route_spec=spec
            )

    return RouteResolution(
        status="UNSUPPORTED",
        is_calibrated=False,
        calibration_badge="CATALOG ONLY — optimization unavailable",
        route_key=f"{orig_id} -> {dest_id}",
        origin_port_id=orig_id,
        destination_port_id=dest_id,
        origin_name=orig_name,
        destination_name=dest_name,
        distance_nm=None,
        estimated_transit_days=None,
        base_freight_multiplier=1.0,
        allowed_vessel_classes=dest_port.supported_vessel_classes if dest_port else ["Panamax", "Capesize"],
        message="Route currently not calibrated in demo model",
        route_spec=None
    )


def get_route_info(origin: str, destination: str) -> RouteSpecification:
    """Helper to retrieve or synthesize route info between any origin and destination."""
    res = resolve_route(origin, destination)
    if res.is_calibrated and res.route_spec:
        return res.route_spec

    key = f"{origin} -> {destination}"
    return RouteSpecification(
        origin_id=res.origin_port_id,
        destination_id=res.destination_port_id,
        route_key=key,
        distance_nm=4500.0,
        estimated_transit_days=13.5,
        canal_or_chokepoint="Direct Marine Route (Uncalibrated Demo Route)",
        base_freight_multiplier=1.0,
        allowed_vessel_classes=res.allowed_vessel_classes
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


def get_calibrated_routes() -> List[Dict[str, Any]]:
    """
    Returns distinct calibrated routes formatted with display label, canonical route_key,
    origin_port_id, destination_port_id, origin_name, destination_name, and base_freight_multiplier.
    """
    seen_keys = set()
    calibrated = []

    for route_key, spec in ROUTE_MASTER.items():
        orig_port = get_port_by_id(spec.origin_id)
        dest_port = get_port_by_id(spec.destination_id)

        o_id = orig_port.port_id if orig_port else spec.origin_id
        d_id = dest_port.port_id if dest_port else spec.destination_id
        o_name = orig_port.port_name if orig_port else spec.origin_id
        d_name = dest_port.port_name if dest_port else spec.destination_id

        pair_key = (o_id, d_id)
        if pair_key in seen_keys:
            continue
        seen_keys.add(pair_key)

        display_label = f"{o_name} → {d_name}"
        calibrated.append({
            "display_label": display_label,
            "route_key": f"{o_id} -> {d_id}",
            "origin_port_id": o_id,
            "destination_port_id": d_id,
            "origin_name": o_name,
            "destination_name": d_name,
            "base_freight_multiplier": spec.base_freight_multiplier,
            "route_spec": spec
        })

    return calibrated

