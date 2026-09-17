"""
FreightIQ Decision-Model Parameter Loader

Reads config/decision_model.yaml once at import time and exposes:
  - Individual named constants for use in optimizer / cost-model code
  - DECISION_PARAMS registry (list of dicts) for the provenance UI table
"""

import os
import yaml
from typing import Any, Dict, List

_YAML_PATH = os.path.join(
    os.path.dirname(__file__), "..", "config", "decision_model.yaml"
)


def _load() -> Dict[str, Any]:
    with open(_YAML_PATH, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return data.get("parameters", {})


_PARAMS: Dict[str, Any] = _load()


def _v(name: str) -> Any:
    return _PARAMS[name]["value"]


# ── Named constants (import these in optimizer / decision_twin) ───────────────

DEMURRAGE_EXPOSURE_FACTOR: float = _v("demurrage_exposure_factor")
CONGESTION_COST_MULTIPLIER: float = _v("congestion_cost_multiplier")
VESSEL_AVAILABILITY_MIN_THRESHOLD: int = int(_v("vessel_availability_min_threshold"))
RISK_FACTOR_LOW: float = _v("risk_factor_low_tolerance")
RISK_FACTOR_MEDIUM: float = _v("risk_factor_medium_tolerance")
RISK_FACTOR_HIGH: float = _v("risk_factor_high_tolerance")
WEATHER_RISK_PENALTY_PER_POINT: float = _v("weather_risk_penalty_per_point")
EVENT_RISK_PENALTY_PER_POINT: float = _v("event_risk_penalty_per_point")
AVAILABILITY_SHORTAGE_PENALTY_PER_VESSEL: float = _v("availability_shortage_penalty_per_vessel")
FREIGHT_TREND_THRESHOLD: float = _v("freight_trend_detection_threshold")
CONGESTION_TO_WAITING_HOURS_FACTOR: float = _v("congestion_to_waiting_hours_factor")


# ── Provenance registry (for Data Integration admin table) ────────────────────

def get_decision_params_registry() -> List[Dict[str, Any]]:
    """Returns a flat list of parameter provenance records for display."""
    rows = []
    for name, meta in _PARAMS.items():
        sr = meta.get("sensitivity_range", {})
        rows.append({
            "parameter": name,
            "value": meta["value"],
            "unit": meta.get("unit", ""),
            "classification": meta.get("classification", ""),
            "source": meta.get("source", ""),
            "note": (meta.get("note") or "").strip().replace("\n", " "),
            "sensitivity_min": sr.get("min"),
            "sensitivity_max": sr.get("max"),
            "editable": meta.get("editable", False),
        })
    return rows
