import json
import math
import urllib.parse
import urllib.request
from typing import List, Dict, Optional, Tuple

from app.schemas.store import Store

OSRM_ROUTE_URL = "https://router.project-osrm.org/table/v1/driving/"  # for distance table
OSRM_ROUTE_SERVICE = "https://router.project-osrm.org/route/v1/driving/"  # for route geometry


def _haversine(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    # meters
    lat1, lon1 = math.radians(a[0]), math.radians(a[1])
    lat2, lon2 = math.radians(b[0]), math.radians(b[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    R = 6371000
    return 2 * R * math.asin(math.sqrt(math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2))


def _nearest_neighbor_order(start: Tuple[float, float], stops: List[Tuple[float, float]]) -> List[int]:
    if not stops:
        return []
    remaining = list(range(len(stops)))
    order = []
    current = start
    while remaining:
        best = min(remaining, key=lambda i: _haversine(current, stops[i]))
        order.append(best)
        current = stops[best]
        remaining.remove(best)
    return order


class RouteService:
    """Compute an ordered route for multiple store stops using OSRM where possible.

    Returns a dict containing ordered stops, total_distance_m, total_duration_s and a route_url to OSRM route geometry.
    """

    def plan_route(self, start_lat: float, start_lng: float, stops: List[Store]) -> Dict:
        coords = [(s.latitude, s.longitude) for s in stops]
        order = _nearest_neighbor_order((start_lat, start_lng), coords)
        ordered_stops = [stops[i] for i in order]

        # request OSRM route geometry for the ordered coordinates (start + stops)
        all_coords = [(start_lat, start_lng)] + [(s.latitude, s.longitude) for s in ordered_stops]
        coord_str = ";".join(f"{lon},{lat}" for lat, lon in all_coords)
        url = OSRM_ROUTE_SERVICE + urllib.parse.quote(coord_str) + "?overview=full&geometries=geojson&steps=true"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'GlucoPlateAI/0.1'})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.load(resp)
            route = data.get('routes', [None])[0]
            if route:
                total_distance = route.get('distance')
                total_duration = route.get('duration')
                geometry = route.get('geometry')
            else:
                total_distance = sum(_haversine((start_lat, start_lng), (s.latitude, s.longitude)) for s in ordered_stops)
                total_duration = None
                geometry = None
        except Exception:
            total_distance = sum(_haversine((start_lat, start_lng), (s.latitude, s.longitude)) for s in ordered_stops)
            total_duration = None
            geometry = None

        return {
            'ordered_stops': [s.dict() for s in ordered_stops],
            'order_indexes': order,
            'total_distance_m': total_distance,
            'total_duration_s': total_duration,
            'geometry': geometry,
        }
