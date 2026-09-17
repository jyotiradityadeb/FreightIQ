"""
FreightIQ Commodity Prices Adapter

Normalized connector for Coking Coal & Iron Ore market prices.
"""

import datetime
from typing import Dict, Any, List
from backend.integrations.base_adapter import BaseAdapter
from backend.data_loader import load_raw_datasets


class CommodityAdapter(BaseAdapter):
    def __init__(self, mode: str = "DEMO"):
        super().__init__(
            source_name="Commodity Prices API",
            mode=mode,
            api_url_env_var="COMMODITY_API_URL",
            api_key_env_var="COMMODITY_API_KEY",
            purpose="Procurement context & commodity price trends"
        )

    def get_latest(self) -> Dict[str, Any]:
        provenance = self._get_provenance_metadata()
        df = load_raw_datasets()
        latest = df.iloc[-1]

        return {
            "timestamp": latest["date"].strftime("%Y-%m-%d"),
            "coking_coal_price": float(latest["coking_coal_price"]),
            "iron_ore_price": float(latest["iron_ore_price"]),
            **provenance
        }

    def get_history(self, horizon_days: int = 30) -> List[Dict[str, Any]]:
        provenance = self._get_provenance_metadata()
        df = load_raw_datasets().tail(horizon_days)
        records = []
        for _, row in df.iterrows():
            records.append({
                "timestamp": row["date"].strftime("%Y-%m-%d"),
                "coking_coal_price": float(row["coking_coal_price"]),
                "iron_ore_price": float(row["iron_ore_price"]),
                **provenance
            })
        return records
