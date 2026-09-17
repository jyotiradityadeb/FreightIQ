"""
FreightIQ Live-Data-Ready Integration Layer Package
"""

from backend.integrations.base_adapter import BaseAdapter
from backend.integrations.freight_adapter import FreightAdapter
from backend.integrations.ais_adapter import AISAdapter
from backend.integrations.commodity_adapter import CommodityAdapter
from backend.integrations.port_adapter import PortAdapter
from backend.integrations.weather_adapter import WeatherAdapter
from backend.integrations.integration_manager import IntegrationManager
