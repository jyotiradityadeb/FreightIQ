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
        stowage_factor_m3_t=1.20,
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
        stowage_factor_m3_t=1.25,
        typical_lot_min=40000,
        typical_lot_max=160000,
        preferred_vessel_classes=["Panamax", "Supramax"],
        default_demurrage_rate_usd_day=18000.0,
        source_region_preferences=["Indonesia", "South Africa", "Australia"]
    ),
    "iron_ore_fines": Commodity(
        commodity_id="iron_ore_fines",
        display_name="Iron Ore Fines",
        category="Iron & Steel Raw Material",
        bulk_type="Major Bulk",
        density_t_m3=2.40,
        stowage_factor_m3_t=0.45,
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
        stowage_factor_m3_t=0.50,
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
        stowage_factor_m3_t=0.70,
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
        stowage_factor_m3_t=0.65,
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
        stowage_factor_m3_t=0.50,
        typical_lot_min=20000,
        typical_lot_max=60000,
        preferred_vessel_classes=["Supramax", "Handysize"],
        default_demurrage_rate_usd_day=15000.0,
        source_region_preferences=["South Africa", "Gabon", "Australia"]
    ),
    "chromite_ore": Commodity(
        commodity_id="chromite_ore",
        display_name="Chromite Ore",
        category="Specialty Ore",
        bulk_type="Minor Bulk",
        density_t_m3=2.20,
        stowage_factor_m3_t=0.48,
        typical_lot_min=15000,
        typical_lot_max=45000,
        preferred_vessel_classes=["Handymax", "Handysize"],
        default_demurrage_rate_usd_day=14000.0,
        source_region_preferences=["South Africa", "Turkey", "Oman"]
    ),
    "bauxite": Commodity(
        commodity_id="bauxite",
        display_name="Bauxite",
        category="Non-Ferrous Ores",
        bulk_type="Major Bulk",
        density_t_m3=1.30,
        stowage_factor_m3_t=0.77,
        typical_lot_min=50000,
        typical_lot_max=180000,
        preferred_vessel_classes=["Capesize", "Panamax"],
        default_demurrage_rate_usd_day=21000.0,
        source_region_preferences=["Guinea", "Australia", "Indonesia"]
    ),
    "met_coke": Commodity(
        commodity_id="met_coke",
        display_name="Coke / Met Coke",
        category="Refined Carbon",
        bulk_type="Minor Bulk",
        density_t_m3=0.55,
        stowage_factor_m3_t=1.82,
        typical_lot_min=20000,
        typical_lot_max=60000,
        preferred_vessel_classes=["Supramax", "Panamax"],
        default_demurrage_rate_usd_day=17000.0,
        source_region_preferences=["China", "Japan", "Poland"]
    ),
    "petcoke": Commodity(
        commodity_id="petcoke",
        display_name="Petroleum Coke",
        category="Refined Carbon",
        bulk_type="Minor Bulk",
        density_t_m3=0.75,
        stowage_factor_m3_t=1.33,
        typical_lot_min=30000,
        typical_lot_max=80000,
        preferred_vessel_classes=["Panamax", "Supramax"],
        default_demurrage_rate_usd_day=18000.0,
        source_region_preferences=["USA", "Saudi Arabia", "UAE"]
    ),
    "slag": Commodity(
        commodity_id="slag",
        display_name="Metallurgical Slag",
        category="Industrial Byproducts",
        bulk_type="Minor Bulk",
        density_t_m3=1.40,
        stowage_factor_m3_t=0.71,
        typical_lot_min=20000,
        typical_lot_max=50000,
        preferred_vessel_classes=["Supramax", "Handymax"],
        default_demurrage_rate_usd_day=14000.0,
        source_region_preferences=["Japan", "China", "South Korea"]
    ),
    "gypsum": Commodity(
        commodity_id="gypsum",
        display_name="Gypsum",
        category="Industrial Minerals",
        bulk_type="Minor Bulk",
        density_t_m3=1.30,
        stowage_factor_m3_t=0.77,
        typical_lot_min=25000,
        typical_lot_max=60000,
        preferred_vessel_classes=["Supramax", "Handymax"],
        default_demurrage_rate_usd_day=15000.0,
        source_region_preferences=["Oman", "Thailand", "UAE"]
    ),
    "fertilizer": Commodity(
        commodity_id="fertilizer",
        display_name="Fertilizer / Urea",
        category="Agricultural Chemicals",
        bulk_type="Minor Bulk",
        density_t_m3=0.95,
        stowage_factor_m3_t=1.05,
        typical_lot_min=25000,
        typical_lot_max=65000,
        preferred_vessel_classes=["Supramax", "Handymax"],
        default_demurrage_rate_usd_day=16000.0,
        source_region_preferences=["Jordan", "Morocco", "Saudi Arabia"]
    ),
    "grain": Commodity(
        commodity_id="grain",
        display_name="Grain / Bulk Agricultural Cargo",
        category="Agri-Bulk",
        bulk_type="Major Bulk",
        density_t_m3=0.76,
        stowage_factor_m3_t=1.32,
        typical_lot_min=30000,
        typical_lot_max=75000,
        preferred_vessel_classes=["Panamax", "Supramax"],
        default_demurrage_rate_usd_day=18000.0,
        source_region_preferences=["Australia", "Canada", "USA"]
    )
}

# Alias mapping for backward compatibility
COMMODITY_ALIASES: Dict[str, str] = {
    "iron_ore": "iron_ore_fines",
    "iron ore": "iron_ore_fines",
    "iron ore fines": "iron_ore_fines",
    "iron ore fines/lump": "iron_ore_fines",
    "coking coal": "coking_coal",
    "thermal coal": "thermal_coal",
    "coke": "met_coke",
    "metallurgical coke": "met_coke",
    "petroleum coke": "petcoke",
    "petcoke": "petcoke",
    "fertilizer": "fertilizer",
    "bulk fertilizer (rock phosphate / urea)": "fertilizer",
    "grain": "grain",
    "agricultural grain (wheat / maize)": "grain"
}


def get_all_commodities() -> Dict[str, Commodity]:
    """Returns all configured commodities in the catalogue."""
    return COMMODITY_CATALOGUE


def get_commodity(commodity_id: str) -> Optional[Commodity]:
    """Retrieves a commodity specification by ID, display name, or alias."""
    if not commodity_id:
        return None
    normalized_id = commodity_id.lower().replace(" ", "_")
    if normalized_id in COMMODITY_CATALOGUE:
        return COMMODITY_CATALOGUE[normalized_id]
    alias_target = COMMODITY_ALIASES.get(commodity_id.lower()) or COMMODITY_ALIASES.get(normalized_id)
    if alias_target and alias_target in COMMODITY_CATALOGUE:
        return COMMODITY_CATALOGUE[alias_target]
    for c in COMMODITY_CATALOGUE.values():
        if c.display_name.lower() == commodity_id.lower():
            return c
    return None


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

