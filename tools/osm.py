"""OpenStreetMap — geocoding, nearby search, routing. No API key needed."""

import httpx

from app.sdk import ToolServer

server = ToolServer("osm-mcp-server", "OpenStreetMap — geocoding, places, directions")

_NOMINATIM = "https://nominatim.openstreetmap.org"
_OSRM = "https://router.project-osrm.org"
_OVERPASS = "https://overpass-api.de/api/interpreter"
_HEADERS = {"User-Agent": "ToolUseAPI/0.1"}


@server.register(
    "geocode_address", description="Convert an address to latitude/longitude"
)
async def geocode_address(address: str) -> dict:
    async with httpx.AsyncClient(headers=_HEADERS, timeout=15) as client:
        resp = await client.get(
            f"{_NOMINATIM}/search",
            params={"q": address, "format": "json", "limit": 1},
        )
        results = resp.json()
        if not results:
            return {"error": "Address not found"}
        r = results[0]
        return {
            "result": {
                "lat": float(r["lat"]),
                "lon": float(r["lon"]),
                "display_name": r["display_name"],
            }
        }


@server.register(
    "reverse_geocode", description="Convert latitude/longitude to an address"
)
async def reverse_geocode(latitude: float, longitude: float) -> dict:
    async with httpx.AsyncClient(headers=_HEADERS, timeout=15) as client:
        resp = await client.get(
            f"{_NOMINATIM}/reverse",
            params={"lat": latitude, "lon": longitude, "format": "json"},
        )
        r = resp.json()
        return {
            "result": {
                "display_name": r.get("display_name", ""),
                "address": r.get("address", {}),
            }
        }


@server.register(
    "find_nearby_places",
    description="Find places near coordinates (restaurants, hotels, etc.)",
)
async def find_nearby_places(
    latitude: float,
    longitude: float,
    radius: int = 1000,
    categories: str = "restaurant",
    limit: int = 5,
) -> dict:
    # Map common categories to OSM tags
    tag_map = {
        "restaurant": '"amenity"="restaurant"',
        "hotel": '"tourism"="hotel"',
        "cafe": '"amenity"="cafe"',
        "bar": '"amenity"="bar"',
        "hospital": '"amenity"="hospital"',
        "pharmacy": '"amenity"="pharmacy"',
        "school": '"amenity"="school"',
        "parking": '"amenity"="parking"',
        "fuel": '"amenity"="fuel"',
        "supermarket": '"shop"="supermarket"',
        "museum": '"tourism"="museum"',
        "park": '"leisure"="park"',
        "bank": '"amenity"="bank"',
        "atm": '"amenity"="atm"',
    }
    osm_tag = tag_map.get(categories, f'"amenity"="{categories}"')

    query = (
        f"[out:json][timeout:15];"
        f"node[{osm_tag}](around:{radius},{latitude},{longitude});"
        f"out body {limit};"
    )
    async with httpx.AsyncClient(headers=_HEADERS, timeout=30) as client:
        resp = await client.post(_OVERPASS, data={"data": query})
        data = resp.json()

    places = []
    for el in data.get("elements", []):
        tags = el.get("tags", {})
        places.append(
            {
                "name": tags.get("name", "Unknown"),
                "lat": el.get("lat"),
                "lon": el.get("lon"),
                "category": categories,
                "address": ", ".join(
                    filter(
                        None,
                        [
                            tags.get("addr:street", ""),
                            tags.get("addr:housenumber", ""),
                            tags.get("addr:city", ""),
                        ],
                    )
                ),
                "phone": tags.get("phone", ""),
                "website": tags.get("website", ""),
            }
        )
    return {"result": places}


@server.register(
    "get_route_directions",
    description="Get directions between two points (driving, walking, or cycling)",
)
async def get_route_directions(
    from_latitude: float,
    from_longitude: float,
    to_latitude: float,
    to_longitude: float,
    mode: str = "driving",
) -> dict:
    profile = {"driving": "driving", "walking": "foot", "cycling": "bike"}.get(
        mode, "driving"
    )
    coords = f"{from_longitude},{from_latitude};{to_longitude},{to_latitude}"

    async with httpx.AsyncClient(headers=_HEADERS, timeout=15) as client:
        resp = await client.get(
            f"{_OSRM}/route/v1/{profile}/{coords}",
            params={"overview": "full", "steps": "true"},
        )
        data = resp.json()

    if data.get("code") != "Ok":
        return {"error": data.get("message", "Route not found")}

    route = data["routes"][0]
    steps = []
    for leg in route.get("legs", []):
        for step in leg.get("steps", []):
            steps.append(
                {
                    "instruction": step.get("maneuver", {}).get("type", ""),
                    "name": step.get("name", ""),
                    "distance_m": round(step.get("distance", 0)),
                    "duration_s": round(step.get("duration", 0)),
                }
            )
    return {
        "result": {
            "distance_km": round(route["distance"] / 1000, 2),
            "duration_min": round(route["duration"] / 60, 1),
            "steps": steps,
        }
    }


@server.register(
    "explore_area",
    description="Get an overview of points of interest around coordinates",
)
async def explore_area(latitude: float, longitude: float, radius: int = 500) -> dict:
    query = (
        f"[out:json][timeout:15];"
        f"("
        f'node["amenity"](around:{radius},{latitude},{longitude});'
        f'node["tourism"](around:{radius},{latitude},{longitude});'
        f'node["shop"](around:{radius},{latitude},{longitude});'
        f");"
        f"out body 20;"
    )
    async with httpx.AsyncClient(headers=_HEADERS, timeout=30) as client:
        resp = await client.post(_OVERPASS, data={"data": query})
        data = resp.json()

    places = []
    for el in data.get("elements", []):
        tags = el.get("tags", {})
        category = tags.get("amenity") or tags.get("tourism") or tags.get("shop", "")
        places.append(
            {
                "name": tags.get("name", "Unknown"),
                "category": category,
                "lat": el.get("lat"),
                "lon": el.get("lon"),
            }
        )
    return {"result": places}
