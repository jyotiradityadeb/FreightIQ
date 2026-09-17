"""
FreightIQ AIS / Vessel Tracking Adapter

Normalized connector for AIS vessel tracking, fleet position & regional supply availability.
"""

import datetime
from typing import Dict, Any, List
from backend.integrations.base_adapter import BaseAdapter
from backend.data_loader import load_raw_datasets


class AISAdapter(BaseAdapter):
    def __init__(self, mode: str = "DEMO"):
        super().__init__(
            source_name="AIS Vessel Tracking API",
            mode=mode,
            api_url_env_var="AIS_API_URL",
            api_key_env_var="AIS_API_KEY",
            purpose="Vessel availability count & fleet supply monitoring"
        )

    def get_latest(self) -> Dict[str, Any]:
        provenance = self._get_provenance_metadata()
        df = load_raw_datasets()
        latest = df.iloc[-1]

        return {
            "timestamp": latest["date"].strftime("%Y-%m-%d"),
            "vessel_class": "Panamax",
            "available_count": int(latest["vessel_availability_count"]),
            "region": "East Coast India",
            **provenance
        }

    def get_history(self, horizon_days: int = 30) -> List[Dict[str, Any]]:
        provenance = self._get_provenance_metadata()
        df = load_raw_datasets().tail(horizon_days)
        records = []
        for _, row in df.iterrows():
            records.append({
                "timestamp": row["date"].strftime("%Y-%m-%d"),
                "vessel_class": "Panamax",
                "available_count": int(row["vessel_availability_count"]),
                "region": "East Coast India",
                **provenance
            })
        return records
