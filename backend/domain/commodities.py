"""
FreightIQ Commodity Master & Custom Cargo Domain Module
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class Commodity(BaseModel):
    commodity_id: str
    display_name: str
    category: str = "Dry Bulk"
    bulk_type: str = "Major Bulk"
    density_t_m3: float = 0.85
    typical_lot_min: float = 20000.0
    typical_lot_max: float = 180000.0
    preferred_vessel_classes: List[str] = Field(default_factory=lambda: ["Panamax", "Capesize"])
    handling_category: str = "Standard Grab"
    stowage_factor_m3_t: float = 1.2
    hazard_class: str = "Non-Hazardous"
    default_demurrage_rate_usd_day: float = 22000.0
    source_region_preferences: List[str] = Field(default_factory=lambda: ["Australia", "Indonesia", "South Africa"])
    active: bool = True


COMMODITY_CATALOGUE: Dict[str, Commodity] = {
    "coking_coal": Commodity(
        commodity_id="coking_coal",
        display_name="Coking Coal",
        category="Metallurgical Raw Material",
        bulk_type="Major Bulk",
        density_t_m3=0.85,
        typical_lot_min=50000,
        typical_lot_max=150000,
        preferred_vessel_classes=["Panamax", "Capesize"],
        default_demurrage_rate_usd_day=22000.0,
        source_region_preferences=["Australia", "Mozambique", "USA"]
    ),
    "thermal_coal": Commodity(
        commodity_id="thermal_coal",
        display_name="Thermal Coal",
        category="Energy Coal",
        bulk_type="Major Bulk",
        density_t_m3=0.80,
        typical_lot_min=40000,
        typical_lot_max=160000,
        preferred_vessel_classes=["Panamax", "Supramax"],
        default_demurrage_rate_usd_day=18000.0,
        source_region_preferences=["Indonesia", "South Africa", "Australia"]
    ),
    "iron_ore": Commodity(
        commodity_id="iron_ore",
        display_name="Iron Ore Fines/Lump",
        category="Iron & Steel Raw Material",
        bulk_type="Major Bulk",
        density_t_m3=2.40,
        typical_lot_min=60000,
        typical_lot_max=200000,
        preferred_vessel_classes=["Capesize", "Newcastlemax", "Panamax"],
        default_demurrage_rate_usd_day=25000.0,
        source_region_preferences=["Australia", "Brazil", "South Africa"]
    ),
    "iron_ore_pellets": Commodity(
        commodity_id="iron_ore_pellets",
        display_name="Iron Ore Pellets",
        category="Beneficiated Ore",
        bulk_type="Major Bulk",
        density_t_m3=2.20,
        typical_lot_min=50000,
        typical_lot_max=150000,
        preferred_vessel_classes=["Capesize", "Panamax"],
        default_demurrage_rate_usd_day=24000.0,
        source_region_preferences=["Brazil", "Bahrain", "India"]
    ),
    "limestone": Commodity(
        commodity_id="limestone",
        display_name="Limestone",
        category="Flux & Industrial Minerals",
        bulk_type="Minor Bulk",
        density_t_m3=1.50,
        typical_lot_min=30000,
        typical_lot_max=80000,
        preferred_vessel_classes=["Supramax", "Panamax"],
        default_demurrage_rate_usd_day=16000.0,
        source_region_preferences=["UAE", "Oman", "Malaysia"]
    ),
    "dolomite": Commodity(
        commodity_id="dolomite",
        display_name="Dolomite",
        category="Flux Materials",
        bulk_type="Minor Bulk",
        density_t_m3=1.60,
        typical_lot_min=25000,
        typical_lot_max=75000,
        preferred_vessel_classes=["Supramax", "Handymax"],
        default_demurrage_rate_usd_day=15000.0,
        source_region_preferences=["UAE", "Oman", "Bhutan"]
    ),
    "manganese_ore": Commodity(
        commodity_id="manganese_ore",
        display_name="Manganese Ore",
        category="Alloy Raw Material",
        bulk_type="Minor Bulk",
        density_t_m3=2.10,
        typical_lot_min=20000,
        typical_lot_max=60000,
        preferred_vessel_classes=["Supramax", "Handysize"],
        default_demurrage_rate_usd_day=15000.0,
        source_region_preferences=["South Africa", "Gabon", "Australia"]
    ),
    "bauxite": Commodity(
        commodity_id="bauxite",
        display_name="Bauxite",
        category="Non-Ferrous Ores",
        bulk_type="Major Bulk",
        density_t_m3=1.30,
        typical_lot_min=50000,
        typical_lot_max=180000,
        preferred_vessel_classes=["Capesize", "Panamax"],
        default_demurrage_rate_usd_day=21000.0,
        source_region_preferences=["Guinea", "Australia", "Indonesia"]
    ),
    "chromite_ore": Commodity(
        commodity_id="chromite_ore",
        display_name="Chromite Ore",
        category="Specialty Ore",
        bulk_type="Minor Bulk",
        density_t_m3=2.20,
        typical_lot_min=15000,
        typical_lot_max=45000,
        preferred_vessel_classes=["Handymax", "Handysize"],
        default_demurrage_rate_usd_day=14000.0,
        source_region_preferences=["South Africa", "Turkey", "Oman"]
    ),
    "met_coke": Commodity(
        commodity_id="met_coke",
        display_name="Metallurgical Coke",
        category="Refined Carbon",
        bulk_type="Minor Bulk",
        density_t_m3=0.55,
        typical_lot_min=20000,
        typical_lot_max=60000,
        preferred_vessel_classes=["Supramax", "Panamax"],
        default_demurrage_rate_usd_day=17000.0,
        source_region_preferences=["China", "Japan", "Poland"]
    ),
    "pci_coal": Commodity(
        commodity_id="pci_coal",
        display_name="PCI Coal",
        category="Blast Furnace Fuel",
        bulk_type="Major Bulk",
        density_t_m3=0.82,
        typical_lot_min=45000,
        typical_lot_max=120000,
        preferred_vessel_classes=["Panamax", "Capesize"],
        default_demurrage_rate_usd_day=20000.0,
        source_region_preferences=["Australia", "Russia", "USA"]
    ),
    "fluxes": Commodity(
        commodity_id="fluxes",
        display_name="Steelmaking Fluxes & Additives",
        category="Industrial Additives",
        bulk_type="Minor Bulk",
        density_t_m3=1.40,
        typical_lot_min=15000,
        typical_lot_max=50000,
        preferred_vessel_classes=["Supramax", "Handysize"],
        default_demurrage_rate_usd_day=14000.0,
        source_region_preferences=["UAE", "Oman", "Vietnam"]
    ),
    "fertilizer": Commodity(
        commodity_id="fertilizer",
        display_name="Bulk Fertilizer (Rock Phosphate / Urea)",
        category="Agricultural Chemicals",
        bulk_type="Minor Bulk",
        density_t_m3=0.95,
        typical_lot_min=25000,
        typical_lot_max=65000,
        preferred_vessel_classes=["Supramax", "Handymax"],
        default_demurrage_rate_usd_day=16000.0,
        source_region_preferences=["Jordan", "Morocco", "Saudi Arabia"]
    ),
    "grain": Commodity(
        commodity_id="grain",
        display_name="Agricultural Grain (Wheat / Maize)",
        category="Agri-Bulk",
        bulk_type="Major Bulk",
        density_t_m3=0.76,
        typical_lot_min=30000,
        typical_lot_max=75000,
        preferred_vessel_classes=["Panamax", "Supramax"],
        default_demurrage_rate_usd_day=18000.0,
        source_region_preferences=["Australia", "Canada", "Black Sea"]
    ),
    "cement_clinker": Commodity(
        commodity_id="cement_clinker",
        display_name="Cement Clinker",
        category="Building Materials",
        bulk_type="Minor Bulk",
        density_t_m3=1.35,
        typical_lot_min=25000,
        typical_lot_max=55000,
        preferred_vessel_classes=["Supramax", "Handymax"],
        default_demurrage_rate_usd_day=15000.0,
        source_region_preferences=["Vietnam", "UAE", "Thailand"]
    )
}


def get_all_commodities() -> Dict[str, Commodity]:
    """Returns all configured commodities in the catalogue."""
    return COMMODITY_CATALOGUE


def get_commodity(commodity_id: str) -> Optional[Commodity]:
    """Retrieves a commodity specification by ID or name."""
    normalized_id = commodity_id.lower().replace(" ", "_")
    return COMMODITY_CATALOGUE.get(normalized_id)


def create_custom_commodity(
    cargo_name: str,
    quantity_tonnes: float,
    stowage_factor: float = 1.2,
    preferred_vessel_class: str = "Panamax",
    demurrage_rate_usd_day: float = 20000.0
) -> Commodity:
    """Creates a configuration-driven Custom Bulk Commodity instance."""
    cid = f"custom_{cargo_name.lower().replace(' ', '_')}"
    return Commodity(
        commodity_id=cid,
        display_name=f"Custom: {cargo_name}",
        category="Custom User Commodity",
        bulk_type="User Defined",
        density_t_m3=1.0 / max(0.1, stowage_factor),
        typical_lot_min=max(10000.0, quantity_tonnes * 0.5),
        typical_lot_max=quantity_tonnes * 1.5,
        preferred_vessel_classes=[preferred_vessel_class] if preferred_vessel_class != "Auto" else ["Panamax", "Capesize", "Supramax"],
        stowage_factor_m3_t=stowage_factor,
        default_demurrage_rate_usd_day=demurrage_rate_usd_day
    )

