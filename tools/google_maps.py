import os

import httpx

from app.sdk import ToolServer

server = ToolServer("google-maps", "Google Maps API tools for geocoding, places, directions, and elevation")

_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")
_BASE = "https://maps.googleapis.com/maps/api"


def _key():
    key = _API_KEY or os.getenv("GOOGLE_MAPS_API_KEY", "")
    if not key:
        raise ValueError("GOOGLE_MAPS_API_KEY not set")
    return key


@server.register("maps_geocode", description="Convert an address to latitude/longitude coordinates")
async def maps_geocode(address: str) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(f"{_BASE}/geocode/json", params={
            "address": address,
            "key": _key(),
        })
        data = resp.json()
    if data.get("status") != "OK" or not data.get("results"):
        return {"result": {"error": data.get("status", "NO_RESULTS")}}
    r = data["results"][0]
    loc = r["geometry"]["location"]
    return {"result": {
        "formatted_address": r.get("formatted_address", ""),
        "latitude": loc["lat"],
        "longitude": loc["lng"],
    }}


@server.register("maps_search_places", description="Search for nearby places by query and location")
async def maps_search_places(query: str, location: str, radius: int = 1000) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(f"{_BASE}/place/textsearch/json", params={
            "query": query,
            "location": location,
            "radius": radius,
            "key": _key(),
        })
        data = resp.json()
    if data.get("status") != "OK":
        return {"result": {"error": data.get("status", "NO_RESULTS"), "results": []}}
    results = []
    for p in data.get("results", [])[:5]:
        results.append({
            "name": p.get("name", ""),
            "rating": p.get("rating", 0),
            "address": p.get("formatted_address", ""),
            "place_id": p.get("place_id", ""),
        })
    return {"result": {"results": results}}


@server.register("maps_directions", description="Get directions between two locations")
async def maps_directions(origin: str, destination: str, mode: str = "walking") -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(f"{_BASE}/directions/json", params={
            "origin": origin,
            "destination": destination,
            "mode": mode,
            "key": _key(),
        })
        data = resp.json()
    if data.get("status") != "OK" or not data.get("routes"):
        return {"result": {"error": data.get("status", "NO_ROUTES")}}
    leg = data["routes"][0]["legs"][0]
    steps = [s.get("html_instructions", "").replace("<b>", "").replace("</b>", "").replace("<div>", " ").replace("</div>", "") for s in leg.get("steps", [])]
    return {"result": {
        "distance": leg["distance"]["text"],
        "duration": leg["duration"]["text"],
        "steps": steps[:10],
    }}


@server.register("maps_elevation", description="Get elevation at a latitude/longitude point")
async def maps_elevation(latitude: float, longitude: float) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(f"{_BASE}/elevation/json", params={
            "locations": f"{latitude},{longitude}",
            "key": _key(),
        })
        data = resp.json()
    if data.get("status") != "OK" or not data.get("results"):
        return {"result": {"error": data.get("status", "NO_RESULTS")}}
    r = data["results"][0]
    return {"result": {
        "elevation": round(r["elevation"], 2),
        "resolution": round(r.get("resolution", 0), 2),
    }}
