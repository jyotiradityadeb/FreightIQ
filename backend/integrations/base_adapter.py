"""
FreightIQ Base Data Adapter Contract

Provides standard abstract contract for data sources with data provenance fields
and graceful fallback handling for unconfigured LIVE_READY connectors.
"""

import os
import datetime
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class BaseAdapter(ABC):
    """
    Abstract Base Class for FreightIQ Data Connectors.
    """

    def __init__(
        self,
        source_name: str,
        mode: str = "DEMO",
        api_url_env_var: Optional[str] = None,
        api_key_env_var: Optional[str] = None,
        purpose: str = "Decision Support Feed"
    ):
        self.source_name = source_name
        self.mode = mode.upper()
        self.api_url = os.getenv(api_url_env_var) if api_url_env_var else None
        self.api_key = os.getenv(api_key_env_var) if api_key_env_var else None
        self.purpose = purpose

    def is_configured(self) -> bool:
        """Checks whether live API endpoint credentials are provided."""
        if self.mode == "DEMO":
            return True
        return bool(self.api_url and self.api_key)

    def health_check(self) -> Dict[str, Any]:
        """Returns connector health and configuration status."""
        configured = self.is_configured()
        if self.mode == "DEMO":
            status = "HEALTHY"
            health_str = "Healthy"
        elif configured:
            status = "HEALTHY"
            health_str = "Healthy"
        else:
            status = "NOT_CONFIGURED"
            health_str = "Not Configured"

        return {
            "source_name": self.source_name,
            "mode": self.mode,
            "status": status,
            "health": health_str,
            "is_configured": configured,
            "purpose": self.purpose,
            "last_update": datetime.datetime.now().strftime("%H:%M IST")
        }

    def _get_provenance_metadata(self) -> Dict[str, str]:
        """Returns standard data provenance metadata fields."""
        if self.mode == "DEMO":
            src_label = f"{self.source_name} (Synthetic Demo)"
            src_mode = "DEMO"
        else:
            src_label = self.source_name if self.is_configured() else f"{self.source_name} (Unconfigured Fallback)"
            src_mode = "LIVE_READY"

        return {
            "source_name": src_label,
            "source_mode": src_mode,
            "retrieved_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        }

    @abstractmethod
    def get_latest(self) -> Dict[str, Any]:
        """Returns normalized latest record."""
        pass

    @abstractmethod
    def get_history(self, horizon_days: int = 30) -> List[Dict[str, Any]]:
        """Returns normalized historical/forecast records."""
        pass

    def get_metadata(self) -> Dict[str, Any]:
        """Returns connector metadata."""
        return {
            "source_name": self.source_name,
            "mode": self.mode,
            "purpose": self.purpose,
            "is_configured": self.is_configured(),
            "provenance": self._get_provenance_metadata()
        }
