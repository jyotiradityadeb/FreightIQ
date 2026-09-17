"""
FreightIQ Central Configuration Module

Contains domain constants, vessel specifications, route assumptions,
cost factors, risk weights, and demo metadata.
"""

from typing import Dict, Any, List

# Currency & Display Presentation Settings for Indian Procurement Users
DISPLAY_CURRENCY = "INR"
DEMO_USD_INR_RATE = 84.0  # Configurable USD to INR conversion rate for presentation layer

# System Metadata & Disclaimers
APP_TITLE = "FreightIQ – Maritime Freight Decision Support System"
DEMO_BANNER_TEXT = "DEMO DATA — Synthetic prototype dataset for decision support evaluation."
DISCLAIMER_TEXT = (
    "International freight benchmarks may originate in USD, while FreightIQ presents decision-support "
    "costs in INR for Indian procurement users. Prototype demonstration using synthetic data. Not live maritime market data."
)

# Random Seed for Reproducibility
RANDOM_SEED = 42

# Vessel Classes and Technical Capabilities
VESSEL_CLASSES: Dict[str, Dict[str, Any]] = {
    "Capesize": {
        "min_capacity": 150000,
        "max_capacity": 200000,
        "default_capacity": 180000,
        "base_daily_charter_multiplier": 1.4,
        "daily_demurrage_rate": 25000.0,  # USD / day
        "draft_requirement_m": 18.0,
        "compatible_ports": ["Paradip", "Visakhapatnam"]
    },
    "Panamax": {
        "min_capacity": 65000,
        "max_capacity": 90000,
        "default_capacity": 75000,
        "base_daily_charter_multiplier": 1.0,
        "daily_demurrage_rate": 18000.0,  # USD / day
        "draft_requirement_m": 14.0,
        "compatible_ports": ["Paradip", "Visakhapatnam", "Kolkata/Haldia"]
    },
    "Supramax": {
        "min_capacity": 45000,
        "max_capacity": 65000,
        "default_capacity": 55000,
        "base_daily_charter_multiplier": 0.8,
        "daily_demurrage_rate": 14000.0,  # USD / day
        "draft_requirement_m": 12.0,
        "compatible_ports": ["Paradip", "Visakhapatnam", "Kolkata/Haldia"]
    }
}

# Supported Trade Routes & Maritime Assumptions (Origins to India East Coast)
ROUTES: Dict[str, Dict[str, Any]] = {
    "Australia -> Visakhapatnam": {
        "origin": "Australia",
        "destination": "Visakhapatnam",
        "distance_nm": 4500,
        "base_transit_days": 14,
        "bunker_cost_factor": 1.15,
        "base_freight_multiplier": 1.2,
        "allowed_vessels": ["Capesize", "Panamax", "Supramax"]
    },
    "Australia -> Paradip": {
        "origin": "Australia",
        "destination": "Paradip",
        "distance_nm": 4300,
        "base_transit_days": 13,
        "bunker_cost_factor": 1.12,
        "base_freight_multiplier": 1.18,
        "allowed_vessels": ["Capesize", "Panamax", "Supramax"]
    },
    "Australia -> Kolkata/Haldia": {
        "origin": "Australia",
        "destination": "Kolkata/Haldia",
        "distance_nm": 4650,
        "base_transit_days": 15,
        "bunker_cost_factor": 1.20,
        "base_freight_multiplier": 1.28,
        "allowed_vessels": ["Panamax", "Supramax"]  # Capesize cannot call Haldia due to draft limits
    },
    "Indonesia -> Visakhapatnam": {
        "origin": "Indonesia",
        "destination": "Visakhapatnam",
        "distance_nm": 2200,
        "base_transit_days": 7,
        "bunker_cost_factor": 0.70,
        "base_freight_multiplier": 0.65,
        "allowed_vessels": ["Capesize", "Panamax", "Supramax"]
    },
    "Indonesia -> Paradip": {
        "origin": "Indonesia",
        "destination": "Paradip",
        "distance_nm": 2100,
        "base_transit_days": 6.5,
        "bunker_cost_factor": 0.68,
        "base_freight_multiplier": 0.62,
        "allowed_vessels": ["Capesize", "Panamax", "Supramax"]
    },
    "Indonesia -> Kolkata/Haldia": {
        "origin": "Indonesia",
        "destination": "Kolkata/Haldia",
        "distance_nm": 2350,
        "base_transit_days": 8,
        "bunker_cost_factor": 0.75,
        "base_freight_multiplier": 0.72,
        "allowed_vessels": ["Panamax", "Supramax"]
    },
    "South Africa -> Visakhapatnam": {
        "origin": "South Africa",
        "destination": "Visakhapatnam",
        "distance_nm": 4900,
        "base_transit_days": 16,
        "bunker_cost_factor": 1.25,
        "base_freight_multiplier": 1.35,
        "allowed_vessels": ["Capesize", "Panamax", "Supramax"]
    },
    "South Africa -> Paradip": {
        "origin": "South Africa",
        "destination": "Paradip",
        "distance_nm": 5100,
        "base_transit_days": 17,
        "bunker_cost_factor": 1.30,
        "base_freight_multiplier": 1.40,
        "allowed_vessels": ["Capesize", "Panamax", "Supramax"]
    },
    "South Africa -> Kolkata/Haldia": {
        "origin": "South Africa",
        "destination": "Kolkata/Haldia",
        "distance_nm": 5300,
        "base_transit_days": 18,
        "bunker_cost_factor": 1.35,
        "base_freight_multiplier": 1.50,
        "allowed_vessels": ["Panamax", "Supramax"]
    }
}

# Cargo Specifications
CARGO_TYPES: Dict[str, Dict[str, Any]] = {
    "Iron Ore": {
        "typical_vessel": "Capesize",
        "min_qty_tonnes": 50000,
        "max_qty_tonnes": 180000,
        "default_qty_tonnes": 150000,
        "stowage_factor_cum_pt": 0.45,
        "default_origin": "Australia",
        "default_destination": "Visakhapatnam"
    },
    "Coking Coal": {
        "typical_vessel": "Panamax",
        "min_qty_tonnes": 40000,
        "max_qty_tonnes": 100000,
        "default_qty_tonnes": 75000,
        "stowage_factor_cum_pt": 0.80,
        "default_origin": "Australia",
        "default_destination": "Paradip"
    }
}

# Port Congestion & Waiting Cost Coefficients
PORT_CONFIG: Dict[str, Dict[str, Any]] = {
    "Paradip": {
        "base_congestion_index": 55.0,
        "avg_laytime_hours": 48.0,
        "congestion_cost_per_hour_usd": 750.0,
        "draft_limit_m": 17.5
    },
    "Visakhapatnam": {
        "base_congestion_index": 45.0,
        "avg_laytime_hours": 36.0,
        "congestion_cost_per_hour_usd": 650.0,
        "draft_limit_m": 16.5
    },
    "Kolkata/Haldia": {
        "base_congestion_index": 68.0,
        "avg_laytime_hours": 60.0,
        "congestion_cost_per_hour_usd": 850.0,
        "draft_limit_m": 12.5
    }
}

# Risk Weightings in Optimizer Cost Function
RISK_WEIGHTS = {
    "weather_risk_penalty_per_point": 1200.0,  # USD cost penalty per risk score point
    "event_risk_penalty_per_point": 1800.0,    # USD cost penalty per event risk point
    "availability_shortage_penalty_per_vessel": 2500.0
}
