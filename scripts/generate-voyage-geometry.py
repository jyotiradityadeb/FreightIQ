"""Regenerate illustrative sea corridors for the calibrated FreightIQ routes.

Requires searoute==1.6.0 at generation time. Its graph is a geographic
illustration, not a navigation service; generated paths must never be used
for voyage planning or represented as verified routes.
"""

import json
from pathlib import Path
import sys

import searoute

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.domain.ports import get_port_by_id
from backend.domain.routes import get_calibrated_routes

PORT_AUTHORITY_COORDINATES = {
    # NQBP port-facilities fact sheet, 21°17'22.41"S 149°18'22.04"E.
    "AU_HPT": ([149.306122, -21.289558], "North Queensland Bulk Ports"),
    # Gladstone Ports Corporation 2024 fact sheet, 23°49.61'S 151°34.6'E.
    "AU_GLT": ([151.576667, -23.826833], "Gladstone Ports Corporation"),
    # Paradip Port Authority, 20°15'58.63"N 86°40'27.34"E.
    "IN_PDP": ([86.674261, 20.266286], "Paradip Port Authority"),
}


def reference_point(port):
    if port.port_id in PORT_AUTHORITY_COORDINATES:
        return PORT_AUTHORITY_COORDINATES[port.port_id]
    return [port.longitude, port.latitude], "FreightIQ port master · approximate"


def main():
    routes = {}
    for route in get_calibrated_routes():
        origin = get_port_by_id(route["origin_port_id"])
        destination = get_port_by_id(route["destination_port_id"])
        if not origin or not destination:
            continue
        start, origin_source = reference_point(origin)
        end, destination_source = reference_point(destination)
        try:
            result = searoute.searoute(start, end, units="naut")
            points = result["geometry"]["coordinates"]
            distance = result["properties"]["length"]
        except (KeyError, ValueError, TypeError):
            continue
        if len(points) < 2 or not 0 < distance < 30000:
            continue
        routes[route["route_key"]] = {
            "origin": {"name": origin.port_name, "country": origin.country, "coordinates": start, "source": origin_source},
            "destination": {"name": destination.port_name, "country": destination.country, "coordinates": end, "source": destination_source},
            "coordinates": points,
            "distance_nm": round(distance, 1),
        }
    result = {
        "source": "searoute 1.6.0 shortest-sea-graph output; illustrative, not for navigation",
        "port_coordinates": "Port authority reference points for Hay Point, Gladstone and Paradip; FreightIQ approximate port master for others",
        "routes": routes,
    }
    output = Path(__file__).resolve().parents[1] / "web" / "geo" / "voyages.json"
    output.write_text(json.dumps(result, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {len(routes)} illustrative corridors to {output}")


if __name__ == "__main__":
    main()
