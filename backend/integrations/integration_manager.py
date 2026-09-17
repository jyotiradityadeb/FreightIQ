"""
FreightIQ Integration Manager

Central management manager for data connectors, mode switching (DEMO / LIVE_READY),
health checks, connector status reporting, and data provenance aggregation.
"""

import os
import datetime
from typing import Dict, Any, List, Optional

from backend.integrations.freight_adapter import FreightAdapter
from backend.integrations.ais_adapter import AISAdapter
from backend.integrations.commodity_adapter import CommodityAdapter
from backend.integrations.port_adapter import PortAdapter
from backend.integrations.weather_adapter import WeatherAdapter
from backend.data_loader import load_raw_datasets


class IntegrationManager:
    def __init__(self, mode: Optional[str] = None):
        self.mode = mode.upper() if mode else os.getenv("DATA_MODE", "DEMO").upper()
        self.freight_adapter = FreightAdapter(mode=self.mode)
        self.ais_adapter = AISAdapter(mode=self.mode)
        self.commodity_adapter = CommodityAdapter(mode=self.mode)
        self.port_adapter = PortAdapter(mode=self.mode)
        self.weather_adapter = WeatherAdapter(mode=self.mode)

    def get_all_adapters(self) -> List[Any]:
        return [
            self.freight_adapter,
            self.ais_adapter,
            self.commodity_adapter,
            self.port_adapter,
            self.weather_adapter
        ]

    def get_connector_status_summary(self) -> List[Dict[str, Any]]:
        """Returns health and status summary for all connectors."""
        summary = []
        for adapter in self.get_all_adapters():
            chk = adapter.health_check()
            summary.append({
                "source": chk["source_name"],
                "mode": chk["mode"],
                "status": chk["status"],
                "last_update": chk["last_update"],
                "health": chk["health"],
                "purpose": chk["purpose"],
                "is_configured": chk["is_configured"]
            })
        return summary

    def get_dataset_provenance_summary(self) -> Dict[str, Any]:
        """Returns complete data provenance metadata."""
        df = load_raw_datasets()
        min_date = df["date"].min().strftime("%Y-%m-%d")
        max_date = df["date"].max().strftime("%Y-%m-%d")
        record_count = len(df)
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M IST")

        sources_list = [
            "FreightIQ Synthetic Freight Rates Benchmark Dataset",
            "FreightIQ Synthetic Commodity Prices Dataset",
            "FreightIQ Synthetic Port Congestion & Operations Dataset",
            "FreightIQ Synthetic Vessel Availability & AIS Dataset",
            "FreightIQ Synthetic Maritime Route Risk Dataset"
        ] if self.mode == "DEMO" else [
            adapter.source_name for adapter in self.get_all_adapters()
        ]

        return {
            "mode": "Synthetic Demo" if self.mode == "DEMO" else "Live Ready",
            "mode_code": self.mode,
            "date_range": f"{min_date} to {max_date}",
            "record_count": record_count,
            "last_refresh": now_str,
            "sources": sources_list,
            "disclosure": "No live commercial or government feeds are connected in the prototype unless credentials are configured."
        }
