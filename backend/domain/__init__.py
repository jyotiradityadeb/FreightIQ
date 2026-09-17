"""
FreightIQ Domain Package
"""

from backend.domain.commodities import COMMODITY_CATALOGUE, Commodity, create_custom_commodity
from backend.domain.vessels import VESSEL_MASTER, VesselSpecification
from backend.domain.ports import PORT_MASTER, PortSpecification
from backend.domain.routes import ROUTE_MASTER, RouteSpecification, get_route_info
