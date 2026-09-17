"""
FreightIQ Port Operations Adapter

Normalized connector for discharge port congestion scores & laytime waiting hours.
"""

import datetime
from typing import Dict, Any, List
from backend.integrations.base_adapter import BaseAdapter
from backend.data_loader import load_raw_datasets


class PortAdapter(BaseAdapter):
    def __init__(self, mode: str = "DEMO"):
        super().__init__(
            source_name="Port Operations API",
            mode=mode,
            api_url_env_var="PORT_API_URL",
            api_key_env_var="PORT_API_KEY",
            purpose="Port congestion index & berth waiting time"
        )

    def get_latest(self) -> Dict[str, Any]:
        provenance = self._get_provenance_metadata()
        df = load_raw_datasets()
        latest = df.iloc[-1]

        return {
            "timestamp": latest["date"].strftime("%Y-%m-%d"),
            "port": "Paradip",
            "congestion_score": float(latest["port_congestion_score"]),
            "avg_waiting_hours": float(latest["avg_waiting_hours"]),
            **provenance
        }

    def get_history(self, horizon_days: int = 30) -> List[Dict[str, Any]]:
        provenance = self._get_provenance_metadata()
        df = load_raw_datasets().tail(horizon_days)
        records = []
        for _, row in df.iterrows():
            records.append({
                "timestamp": row["date"].strftime("%Y-%m-%d"),
                "port": "Paradip",
                "congestion_score": float(row["port_congestion_score"]),
                "avg_waiting_hours": float(row["avg_waiting_hours"]),
                **provenance
            })
        return records
