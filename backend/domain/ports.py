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
    port_type: str = "bulk_port"
    supported_vessel_classes: List[str] = Field(default_factory=lambda: ["Panamax", "Capesize", "Supramax"])
    congestion_source: str = "Synthetic Demo Feed"
    waiting_time_source: str = "Synthetic Demo Feed"
    status: str = "Active Operational Node"
    data_freshness_policy: str = "DAILY"
    is_assumption: bool = True
    is_origin: bool = True
    is_destination: bool = True


PORT_MASTER: Dict[str, PortSpecification] = {
    # AUSTRALIA (MAJOR EXPORT ORIGINS)
    "AU_HPT": PortSpecification(
        port_id="AU_HPT",
        port_name="Hay Point",
        country="Australia",
        region="Queensland",
        latitude=-21.2833,
        longitude=149.3000,
        max_draft_m=20.0,
        cargo_categories=["Coking Coal", "Thermal Coal"],
        port_type="export_terminal",
        supported_vessel_classes=["Capesize", "Panamax", "Supramax", "Newcastlemax"],
        is_origin=True,
        is_destination=False
    ),
    "AU_DBT": PortSpecification(
        port_id="AU_DBT",
        port_name="Dalrymple Bay",
        country="Australia",
        region="Queensland",
        latitude=-21.2640,
        longitude=149.2900,
        max_draft_m=20.0,
        cargo_categories=["Coking Coal", "Thermal Coal"],
        port_type="export_terminal",
        supported_vessel_classes=["Capesize", "Panamax", "Supramax"],
        is_origin=True,
        is_destination=False
    ),
    "AU_GLT": PortSpecification(
        port_id="AU_GLT",
        port_name="Gladstone",
        country="Australia",
        region="Queensland",
        latitude=-23.8400,
        longitude=151.2500,
        max_draft_m=16.5,
        cargo_categories=["Coking Coal", "Thermal Coal", "Bauxite", "Grain"],
        port_type="bulk_port",
        supported_vessel_classes=["Panamax", "Capesize", "Supramax"],
        is_origin=True,
        is_destination=False
    ),
    "AU_NCW": PortSpecification(
        port_id="AU_NCW",
        port_name="Newcastle",
        country="Australia",
        region="New South Wales",
        latitude=-32.9200,
        longitude=151.7800,
        max_draft_m=15.5,
        cargo_categories=["Thermal Coal", "Coking Coal", "Grain"],
        port_type="bulk_port",
        supported_vessel_classes=["Panamax", "Capesize", "Supramax"],
        is_origin=True,
        is_destination=False
    ),
    "AU_PHE": PortSpecification(
        port_id="AU_PHE",
        port_name="Port Hedland",
        country="Australia",
        region="Western Australia",
        latitude=-20.3100,
        longitude=118.5700,
        max_draft_m=20.0,
        cargo_categories=["Iron Ore Fines", "Iron Ore Pellets", "Manganese Ore"],
        port_type="export_terminal",
        supported_vessel_classes=["Capesize", "Newcastlemax", "Valemax"],
        is_origin=True,
        is_destination=False
    ),
    "AU_DAM": PortSpecification(
        port_id="AU_DAM",
        port_name="Dampier",
        country="Australia",
        region="Western Australia",
        latitude=-20.6600,
        longitude=116.7100,
        max_draft_m=19.5,
        cargo_categories=["Iron Ore Fines", "Iron Ore Pellets"],
        port_type="export_terminal",
        supported_vessel_classes=["Capesize", "Newcastlemax"],
        is_origin=True,
        is_destination=False
    ),

    # BRAZIL (MAJOR EXPORT ORIGINS)
    "BR_PDM": PortSpecification(
        port_id="BR_PDM",
        port_name="Ponta da Madeira",
        country="Brazil",
        region="Maranhão",
        latitude=-2.5600,
        longitude=-44.3700,
        max_draft_m=23.0,
        cargo_categories=["Iron Ore Fines", "Iron Ore Pellets", "Manganese Ore"],
        port_type="export_terminal",
        supported_vessel_classes=["Capesize", "Valemax", "Newcastlemax"],
        is_origin=True,
        is_destination=False
    ),
    "BR_TUB": PortSpecification(
        port_id="BR_TUB",
        port_name="Tubarão",
        country="Brazil",
        region="Espírito Santo",
        latitude=-20.2833,
        longitude=-40.2500,
        max_draft_m=22.5,
        cargo_categories=["Iron Ore Fines", "Iron Ore Pellets"],
        port_type="export_terminal",
        supported_vessel_classes=["Capesize", "Panamax"],
        is_origin=True,
        is_destination=False
    ),

    # SOUTH AFRICA (MAJOR EXPORT ORIGINS)
    "ZA_RCB": PortSpecification(
        port_id="ZA_RCB",
        port_name="Richards Bay",
        country="South Africa",
        region="KwaZulu-Natal",
        latitude=-28.8000,
        longitude=32.0833,
        max_draft_m=19.0,
        cargo_categories=["Thermal Coal", "Manganese Ore", "Chromite Ore", "Titanium Slag"],
        port_type="bulk_port",
        supported_vessel_classes=["Capesize", "Panamax", "Supramax"],
        is_origin=True,
        is_destination=False
    ),
    "ZA_SDB": PortSpecification(
        port_id="ZA_SDB",
        port_name="Saldanha Bay",
        country="South Africa",
        region="Western Cape",
        latitude=-33.0300,
        longitude=17.9800,
        max_draft_m=20.5,
        cargo_categories=["Iron Ore Fines", "Iron Ore Pellets"],
        port_type="export_terminal",
        supported_vessel_classes=["Capesize", "Newcastlemax"],
        is_origin=True,
        is_destination=False
    ),

    # INDONESIA (MAJOR EXPORT ORIGINS)
    "ID_TBN": PortSpecification(
        port_id="ID_TBN",
        port_name="Taboneo / Banjarmasin",
        country="Indonesia",
        region="South Kalimantan",
        latitude=-3.6000,
        longitude=114.5000,
        max_draft_m=15.0,
        cargo_categories=["Thermal Coal", "Bauxite"],
        port_type="anchorage_cluster",
        supported_vessel_classes=["Panamax", "Supramax", "Capesize"],
        is_origin=True,
        is_destination=False
    ),
    "ID_BPN": PortSpecification(
        port_id="ID_BPN",
        port_name="Balikpapan",
        country="Indonesia",
        region="East Kalimantan",
        latitude=-1.2600,
        longitude=116.8300,
        max_draft_m=14.5,
        cargo_categories=["Thermal Coal", "Coke / Met Coke"],
        port_type="bulk_port",
        supported_vessel_classes=["Panamax", "Supramax"],
        is_origin=True,
        is_destination=False
    ),
    "ID_SRD": PortSpecification(
        port_id="ID_SRD",
        port_name="Samarinda",
        country="Indonesia",
        region="East Kalimantan",
        latitude=-0.5000,
        longitude=117.1500,
        max_draft_m=12.0,
        cargo_categories=["Thermal Coal"],
        port_type="anchorage_cluster",
        supported_vessel_classes=["Supramax", "Handymax"],
        is_origin=True,
        is_destination=False
    ),

    # CANADA (MAJOR EXPORT ORIGINS)
    "CA_VAN": PortSpecification(
        port_id="CA_VAN",
        port_name="Vancouver",
        country="Canada",
        region="British Columbia",
        latitude=49.2800,
        longitude=-123.1200,
        max_draft_m=15.5,
        cargo_categories=["Coking Coal", "Thermal Coal", "Grain / Bulk Agricultural Cargo", "Fertilizer / Urea"],
        port_type="bulk_port",
        supported_vessel_classes=["Panamax", "Supramax"],
        is_origin=True,
        is_destination=False
    ),
    "CA_PRU": PortSpecification(
        port_id="CA_PRU",
        port_name="Prince Rupert",
        country="Canada",
        region="British Columbia",
        latitude=54.3100,
        longitude=-130.3200,
        max_draft_m=18.0,
        cargo_categories=["Coking Coal", "Thermal Coal", "Grain / Bulk Agricultural Cargo"],
        port_type="bulk_port",
        supported_vessel_classes=["Capesize", "Panamax"],
        is_origin=True,
        is_destination=False
    ),

    # USA (MAJOR EXPORT ORIGINS)
    "US_ORF": PortSpecification(
        port_id="US_ORF",
        port_name="Hampton Roads / Norfolk",
        country="USA",
        region="Virginia",
        latitude=36.9500,
        longitude=-76.3300,
        max_draft_m=15.2,
        cargo_categories=["Coking Coal", "Thermal Coal", "Petroleum Coke"],
        port_type="bulk_port",
        supported_vessel_classes=["Panamax", "Capesize"],
        is_origin=True,
        is_destination=False
    ),
    "US_MOB": PortSpecification(
        port_id="US_MOB",
        port_name="Mobile",
        country="USA",
        region="Alabama",
        latitude=30.6900,
        longitude=-88.0400,
        max_draft_m=13.7,
        cargo_categories=["Coking Coal", "Thermal Coal", "Petroleum Coke"],
        port_type="bulk_port",
        supported_vessel_classes=["Panamax", "Supramax"],
        is_origin=True,
        is_destination=False
    ),

    # MOZAMBIQUE (MAJOR EXPORT ORIGINS)
    "MZ_MNC": PortSpecification(
        port_id="MZ_MNC",
        port_name="Nacala",
        country="Mozambique",
        region="Nampula",
        latitude=-14.5500,
        longitude=40.6833,
        max_draft_m=18.0,
        cargo_categories=["Coking Coal", "Thermal Coal"],
        port_type="bulk_port",
        supported_vessel_classes=["Capesize", "Panamax"],
        is_origin=True,
        is_destination=False
    ),
    "MZ_BEW": PortSpecification(
        port_id="MZ_BEW",
        port_name="Beira",
        country="Mozambique",
        region="Sofala",
        latitude=-19.8400,
        longitude=34.8400,
        max_draft_m=10.5,
        cargo_categories=["Coking Coal", "Thermal Coal"],
        port_type="bulk_port",
        supported_vessel_classes=["Handymax", "Handysize"],
        is_origin=True,
        is_destination=False
    ),

    # INDIA (EAST COAST DESTINATION & COASTAL ORIGIN PORTS)
    "IN_PDP": PortSpecification(
        port_id="IN_PDP",
        port_name="Paradip",
        country="India",
        region="East Coast",
        latitude=20.2644,
        longitude=86.6744,
        max_draft_m=17.5,
        cargo_categories=["Coking Coal", "Thermal Coal", "Iron Ore Fines", "Limestone", "Bauxite", "Dolomite", "Gypsum"],
        port_type="bulk_port",
        supported_vessel_classes=["Capesize", "Panamax", "Supramax"],
        is_origin=True,
        is_destination=True
    ),
    "IN_DHM": PortSpecification(
        port_id="IN_DHM",
        port_name="Dhamra",
        country="India",
        region="East Coast",
        latitude=20.8000,
        longitude=86.9700,
        max_draft_m=18.0,
        cargo_categories=["Coking Coal", "Thermal Coal", "Iron Ore Fines", "Limestone"],
        port_type="deepwater_port",
        supported_vessel_classes=["Capesize", "Panamax", "Supramax"],
        is_origin=True,
        is_destination=True
    ),
    "IN_HAL": PortSpecification(
        port_id="IN_HAL",
        port_name="Haldia",
        country="India",
        region="East Coast",
        latitude=22.0258,
        longitude=88.0583,
        max_draft_m=12.5,
        cargo_categories=["Coking Coal", "Thermal Coal", "Limestone", "Dolomite", "Petroleum Coke"],
        port_type="dock_complex",
        supported_vessel_classes=["Panamax", "Supramax", "Handymax"],
        is_origin=True,
        is_destination=True
    ),
    "IN_CCU": PortSpecification(
        port_id="IN_CCU",
        port_name="Kolkata",
        country="India",
        region="East Coast",
        latitude=22.5400,
        longitude=88.3300,
        max_draft_m=10.5,
        cargo_categories=["Limestone", "Dolomite", "Fertilizer / Urea", "Break Bulk"],
        port_type="riverine_port",
        supported_vessel_classes=["Handysize", "Supramax"],
        is_origin=True,
        is_destination=True
    ),
    "IN_VTZ": PortSpecification(
        port_id="IN_VTZ",
        port_name="Visakhapatnam",
        country="India",
        region="East Coast",
        latitude=17.6868,
        longitude=83.2185,
        max_draft_m=18.1,
        cargo_categories=["Coking Coal", "Iron Ore Fines", "Manganese Ore", "Thermal Coal", "Coke / Met Coke"],
        port_type="bulk_port",
        supported_vessel_classes=["Capesize", "Panamax", "Supramax"],
        is_origin=True,
        is_destination=True
    ),
    "IN_GAV": PortSpecification(
        port_id="IN_GAV",
        port_name="Gangavaram",
        country="India",
        region="East Coast",
        latitude=17.6200,
        longitude=83.2350,
        max_draft_m=19.5,
        cargo_categories=["Coking Coal", "Iron Ore Fines", "Iron Ore Pellets", "Capesize Imports"],
        port_type="deepwater_port",
        supported_vessel_classes=["Capesize", "Newcastlemax", "Panamax"],
        is_origin=True,
        is_destination=True
    ),
    "IN_KPT": PortSpecification(
        port_id="IN_KPT",
        port_name="Krishnapatnam",
        country="India",
        region="East Coast",
        latitude=14.2500,
        longitude=80.1200,
        max_draft_m=18.5,
        cargo_categories=["Thermal Coal", "Coking Coal", "Fertilizer / Urea", "Limestone"],
        port_type="deepwater_port",
        supported_vessel_classes=["Capesize", "Panamax", "Supramax"],
        is_origin=True,
        is_destination=True
    ),
    "IN_ENR": PortSpecification(
        port_id="IN_ENR",
        port_name="Kamarajar / Ennore",
        country="India",
        region="East Coast",
        latitude=13.2600,
        longitude=80.3300,
        max_draft_m=16.0,
        cargo_categories=["Thermal Coal", "Iron Ore Fines", "Car Carrier"],
        port_type="bulk_port",
        supported_vessel_classes=["Panamax", "Capesize"],
        is_origin=True,
        is_destination=True
    ),
    "IN_MAA": PortSpecification(
        port_id="IN_MAA",
        port_name="Chennai",
        country="India",
        region="East Coast",
        latitude=13.0827,
        longitude=80.2707,
        max_draft_m=15.0,
        cargo_categories=["Containers", "Dry Bulk", "Cars", "Limestone"],
        port_type="bulk_port",
        supported_vessel_classes=["Panamax", "Supramax"],
        is_origin=True,
        is_destination=True
    ),
    "IN_TUT": PortSpecification(
        port_id="IN_TUT",
        port_name="V.O. Chidambaranar (Tuticorin)",
        country="India",
        region="East Coast",
        latitude=8.7500,
        longitude=78.1800,
        max_draft_m=14.2,
        cargo_categories=["Thermal Coal", "Copper Ore", "Fertilizer / Urea", "Limestone"],
        port_type="bulk_port",
        supported_vessel_classes=["Panamax", "Supramax"],
        is_origin=True,
        is_destination=True
    ),

    # INDIA (WEST COAST DESTINATION & COASTAL ORIGIN PORTS)
    "IN_MUN": PortSpecification(
        port_id="IN_MUN",
        port_name="Mundra",
        country="India",
        region="West Coast",
        latitude=22.7400,
        longitude=69.7000,
        max_draft_m=17.5,
        cargo_categories=["Thermal Coal", "Fertilizer / Urea", "Crude Oil", "Containers"],
        port_type="bulk_port",
        supported_vessel_classes=["Capesize", "Panamax", "Supramax"],
        is_origin=True,
        is_destination=True
    ),
    "IN_IXY": PortSpecification(
        port_id="IN_IXY",
        port_name="Deendayal / Kandla",
        country="India",
        region="West Coast",
        latitude=23.0100,
        longitude=70.2200,
        max_draft_m=14.5,
        cargo_categories=["Fertilizer / Urea", "Salt", "Grain / Bulk Agricultural Cargo", "Timber"],
        port_type="bulk_port",
        supported_vessel_classes=["Panamax", "Supramax"],
        is_origin=True,
        is_destination=True
    ),
    "IN_MRM": PortSpecification(
        port_id="IN_MRM",
        port_name="Mormugao",
        country="India",
        region="West Coast",
        latitude=15.4100,
        longitude=73.8000,
        max_draft_m=14.0,
        cargo_categories=["Iron Ore Fines", "Coking Coal", "Wood Chips"],
        port_type="bulk_port",
        supported_vessel_classes=["Panamax", "Capesize"],
        is_origin=True,
        is_destination=True
    ),
    "IN_NML": PortSpecification(
        port_id="IN_NML",
        port_name="New Mangalore",
        country="India",
        region="West Coast",
        latitude=12.9200,
        longitude=74.8100,
        max_draft_m=15.1,
        cargo_categories=["Iron Ore Pellets", "Thermal Coal", "Limestone", "Pol"],
        port_type="bulk_port",
        supported_vessel_classes=["Panamax", "Supramax"],
        is_origin=True,
        is_destination=True
    ),
    "IN_COK": PortSpecification(
        port_id="IN_COK",
        port_name="Cochin",
        country="India",
        region="West Coast",
        latitude=9.9600,
        longitude=76.2600,
        max_draft_m=14.5,
        cargo_categories=["Crude", "Fertilizer / Urea", "Containers"],
        port_type="bulk_port",
        supported_vessel_classes=["Panamax", "Supramax"],
        is_origin=True,
        is_destination=True
    ),
    "IN_BOM": PortSpecification(
        port_id="IN_BOM",
        port_name="Mumbai",
        country="India",
        region="West Coast",
        latitude=18.9500,
        longitude=72.8400,
        max_draft_m=12.0,
        cargo_categories=["Break Bulk", "Fertilizer / Urea", "General Cargo"],
        port_type="bulk_port",
        supported_vessel_classes=["Panamax", "Supramax"],
        is_origin=True,
        is_destination=True
    ),
    "IN_NSA": PortSpecification(
        port_id="IN_NSA",
        port_name="JNPA / Nhava Sheva",
        country="India",
        region="West Coast",
        latitude=18.9500,
        longitude=72.9500,
        max_draft_m=15.0,
        cargo_categories=["Containers", "Bulk Liquid"],
        port_type="bulk_port",
        supported_vessel_classes=["Panamax", "Supramax"],
        is_origin=True,
        is_destination=True
    )
}

# Alias resolution mapping for legacy callers & dropdown inputs
PORT_ALIAS_MAP: Dict[str, str] = {
    # Countries -> Default Port
    "australia": "AU_HPT",
    "brazil": "BR_PDM",
    "south africa": "ZA_RCB",
    "indonesia": "ID_TBN",
    "canada": "CA_VAN",
    "usa": "US_ORF",
    "mozambique": "MZ_MNC",
    "india": "IN_PDP",

    # Port names -> Canonical ID
    "hay point": "AU_HPT",
    "dalrymple bay": "AU_DBT",
    "gladstone": "AU_GLT",
    "newcastle": "AU_NCW",
    "port hedland": "AU_PHE",
    "dampier": "AU_DAM",
    "ponta da madeira": "BR_PDM",
    "tubarao": "BR_TUB",
    "tubarão": "BR_TUB",
    "richards bay": "ZA_RCB",
    "saldanha bay": "ZA_SDB",
    "taboneo": "ID_TBN",
    "taboneo / banjarmasin": "ID_TBN",
    "banjarmasin": "ID_TBN",
    "balikpapan": "ID_BPN",
    "samarinda": "ID_SRD",
    "vancouver": "CA_VAN",
    "prince rupert": "CA_PRU",
    "hampton roads": "US_ORF",
    "norfolk": "US_ORF",
    "hampton roads / norfolk": "US_ORF",
    "mobile": "US_MOB",
    "nacala": "MZ_MNC",
    "beira": "MZ_BEW",
    "paradip": "IN_PDP",
    "paradeep": "IN_PDP",
    "dhamra": "IN_DHM",
    "haldia": "IN_HAL",
    "kolkata": "IN_CCU",
    "kolkata/haldia": "IN_HAL",
    "visakhapatnam": "IN_VTZ",
    "vizag": "IN_VTZ",
    "gangavaram": "IN_GAV",
    "krishnapatnam": "IN_KPT",
    "ennore": "IN_ENR",
    "kamarajar": "IN_ENR",
    "kamarajar / ennore": "IN_ENR",
    "chennai": "IN_MAA",
    "tuticorin": "IN_TUT",
    "v.o. chidambaranar": "IN_TUT",
    "v.o. chidambaranar (tuticorin)": "IN_TUT",
    "v.o. chidambaranar / tuticorin": "IN_TUT",
    "mundra": "IN_MUN",
    "kandla": "IN_IXY",
    "deendayal": "IN_IXY",
    "deendayal / kandla": "IN_IXY",
    "mormugao": "IN_MRM",
    "new mangalore": "IN_NML",
    "cochin": "IN_COK",
    "mumbai": "IN_BOM",
    "nhava sheva": "IN_NSA",
    "jnpa": "IN_NSA",
    "jnpa / nhava sheva": "IN_NSA",
}


def get_port_by_id(port_id: str) -> Optional[PortSpecification]:
    """Retrieves a port specification by ID, display name, country, or legacy alias."""
    if not port_id:
        return None

    pid_clean = port_id.strip()

    # Exact canonical match
    if pid_clean in PORT_MASTER:
        return PORT_MASTER[pid_clean]

    # Check alias map
    alias_target = PORT_ALIAS_MAP.get(pid_clean.lower())
    if alias_target and alias_target in PORT_MASTER:
        return PORT_MASTER[alias_target]

    # Check port_name or country match
    for port in PORT_MASTER.values():
        if port.port_name.lower() == pid_clean.lower() or port.port_id.lower() == pid_clean.lower():
            return port

    for port in PORT_MASTER.values():
        if port.country.lower() == pid_clean.lower():
            return port

    return None


def get_ports_by_region(region: str) -> List[PortSpecification]:
    """Returns ports belonging to a region or country."""
    reg_lower = region.lower()
    return [
        p for p in PORT_MASTER.values()
        if reg_lower in p.region.lower() or reg_lower in p.country.lower() or p.region.lower() in reg_lower
    ]


def get_origin_countries() -> List[str]:
    """Returns sorted list of distinct export origin countries."""
    countries = sorted(list(set(p.country for p in PORT_MASTER.values() if p.is_origin)))
    # Ensure Australia is first if present
    if "Australia" in countries:
        countries.remove("Australia")
        countries.insert(0, "Australia")
    return countries


def get_destination_countries() -> List[str]:
    """Returns sorted list of distinct destination countries (default India)."""
    return ["India"]


def get_ports_for_country(country: str, is_origin: bool = True) -> List[PortSpecification]:
    """Returns list of port specifications in the given country matching origin/destination flag."""
    c_lower = country.lower()
    ports = [
        p for p in PORT_MASTER.values()
        if p.country.lower() == c_lower and (p.is_origin if is_origin else p.is_destination)
    ]
    if not ports:
        ports = [p for p in PORT_MASTER.values() if p.country.lower() == c_lower]
    return sorted(ports, key=lambda x: x.port_name)


def get_all_ports() -> Dict[str, PortSpecification]:
    """Returns full canonical port catalogue dictionary."""
    return PORT_MASTER

