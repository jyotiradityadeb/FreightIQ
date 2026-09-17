"""
FreightIQ Freight Benchmarks Adapter

Normalized connector for dry bulk freight rate benchmarks (C3/C5/Panamax routes & BDI).
"""

import datetime
from typing import Dict, Any, List
from backend.integrations.base_adapter import BaseAdapter
from backend.data_loader import load_raw_datasets


class FreightAdapter(BaseAdapter):
    def __init__(self, mode: str = "DEMO"):
        super().__init__(
            source_name="Freight Benchmarks API",
            mode=mode,
            api_url_env_var="FREIGHT_API_URL",
            api_key_env_var="FREIGHT_API_KEY",
            purpose="Freight rate forecasting & market indexing"
        )

    def get_latest(self) -> Dict[str, Any]:
        provenance = self._get_provenance_metadata()
        df = load_raw_datasets()
        latest = df.iloc[-1]

        return {
            "timestamp": latest["date"].strftime("%Y-%m-%d"),
            "freight_rate": float(latest["freight_rate"]),
            "bdi": float(latest["bdi"]),
            "capesize_index": float(latest["capesize_index"]),
            "panamax_index": float(latest["panamax_index"]),
            **provenance
        }

    def get_history(self, horizon_days: int = 30) -> List[Dict[str, Any]]:
        provenance = self._get_provenance_metadata()
        df = load_raw_datasets().tail(horizon_days)
        records = []
        for _, row in df.iterrows():
            records.append({
                "timestamp": row["date"].strftime("%Y-%m-%d"),
                "freight_rate": float(row["freight_rate"]),
                "bdi": float(row["bdi"]),
                "capesize_index": float(row["capesize_index"]),
                "panamax_index": float(row["panamax_index"]),
                **provenance
            })
        return records
