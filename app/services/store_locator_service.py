import json
import urllib.parse
import urllib.request
from typing import Any

from app.schemas.store import Store, StoreSearchRequest


class StoreLocatorService:
    """Find nearby food stores using OpenStreetMap Overpass API."""

    overpass_url = "https://overpass-api.de/api/interpreter"

    def find_nearby_stores(self, request: StoreSearchRequest) -> list[Store]:
        query = self._build_overpass_query(request)
        encoded = urllib.parse.urlencode({"data": query}).encode("utf-8")

        try:
            http_request = urllib.request.Request(
                self.overpass_url,
                data=encoded,
                headers={"User-Agent": "GlucoPlateAI/0.1 (learning project)"},
                method="POST",
            )
            with urllib.request.urlopen(http_request, timeout=10) as response:
                payload = response.read().decode("utf-8")
        except Exception:
            return self._fallback_stores(request)

        data = json.loads(payload)
        stores = [self._map_element(element) for element in data.get("elements", [])]
        return [store for store in stores if store.latitude and store.longitude][:50]

    def _build_overpass_query(self, request: StoreSearchRequest) -> str:
        return f"""
[out:json][timeout:25];
(
  node["shop"~"supermarket|grocery|convenience"](around:{request.radius_meters},{request.latitude},{request.longitude});
  way["shop"~"supermarket|grocery|convenience"](around:{request.radius_meters},{request.latitude},{request.longitude});
  relation["shop"~"supermarket|grocery|convenience"](around:{request.radius_meters},{request.latitude},{request.longitude});
);
out center tags;
""".strip()

    def _map_element(self, element: dict[str, Any]) -> Store:
        tags = element.get("tags", {})
        latitude = element.get("lat") or element.get("center", {}).get("lat")
        longitude = element.get("lon") or element.get("center", {}).get("lon")
        address_parts = [
            tags.get("addr:housenumber"),
            tags.get("addr:street"),
            tags.get("addr:city"),
            tags.get("addr:state"),
            tags.get("addr:postcode"),
        ]
        address = " ".join(part for part in address_parts if part) or None

        return Store(
            id=str(element.get("id")),
            name=tags.get("name") or "Unnamed food store",
            latitude=float(latitude),
            longitude=float(longitude),
            address=address,
            store_type=tags.get("shop"),
        )

    def _fallback_stores(self, request: StoreSearchRequest) -> list[Store]:
        return [
            Store(
                id="fallback-nearby-grocery",
                name="Nearby grocery store search unavailable",
                latitude=request.latitude,
                longitude=request.longitude,
                address="Store search API unavailable. Try again later.",
                store_type="unknown",
                source="fallback",
            )
        ]
