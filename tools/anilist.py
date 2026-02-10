"""AniList — anime, manga, characters search. No API key needed."""

import httpx

from app.sdk import ToolServer

server = ToolServer("anilist", "AniList — search anime, characters, and staff")

_API = "https://graphql.anilist.co"


async def _gql(query: str, variables: dict | None = None) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            _API, json={"query": query, "variables": variables or {}}
        )
        return resp.json()


@server.register("search_anime", description="Search for anime by title")
async def search_anime(term: str) -> dict:
    data = await _gql(
        """
        query ($search: String) {
            Page(perPage: 5) {
                media(search: $search, type: ANIME) {
                    id
                    title { romaji english }
                    episodes status averageScore
                    genres
                    description(asHtml: false)
                }
            }
        }
        """,
        {"search": term},
    )
    media = data.get("data", {}).get("Page", {}).get("media", [])
    return {
        "result": [
            {
                "id": m["id"],
                "title": m["title"].get("english") or m["title"].get("romaji"),
                "episodes": m.get("episodes"),
                "status": m.get("status"),
                "score": m.get("averageScore"),
                "genres": m.get("genres", []),
                "description": (m.get("description") or "")[:300],
            }
            for m in media
        ]
    }


@server.register("get_anime", description="Get detailed info about an anime by ID")
async def get_anime(id: int) -> dict:
    data = await _gql(
        """
        query ($id: Int) {
            Media(id: $id, type: ANIME) {
                id
                title { romaji english native }
                description(asHtml: false)
                episodes duration status season seasonYear
                averageScore meanScore
                genres
                studios { nodes { name } }
                startDate { year month day }
                endDate { year month day }
            }
        }
        """,
        {"id": id},
    )
    return {"result": data.get("data", {}).get("Media", {})}


@server.register(
    "search_character", description="Search for anime/manga characters by name"
)
async def search_character(term: str) -> dict:
    data = await _gql(
        """
        query ($search: String) {
            Page(perPage: 5) {
                characters(search: $search) {
                    id
                    name { full native }
                    description(asHtml: false)
                    media { nodes { title { romaji } } }
                }
            }
        }
        """,
        {"search": term},
    )
    chars = data.get("data", {}).get("Page", {}).get("characters", [])
    return {
        "result": [
            {
                "id": c["id"],
                "name": c["name"].get("full"),
                "native_name": c["name"].get("native"),
                "description": (c.get("description") or "")[:300],
                "appears_in": [
                    m["title"]["romaji"]
                    for m in (c.get("media", {}).get("nodes", []))[:3]
                ],
            }
            for c in chars
        ]
    }


@server.register(
    "get_character", description="Get detailed info about a character by ID"
)
async def get_character(id: int) -> dict:
    data = await _gql(
        """
        query ($id: Int) {
            Character(id: $id) {
                id
                name { full native alternative }
                description(asHtml: false)
                gender age bloodType
                media { nodes { title { romaji english } type } }
            }
        }
        """,
        {"id": id},
    )
    return {"result": data.get("data", {}).get("Character", {})}


@server.register("search_staff", description="Search for anime staff/voice actors")
async def search_staff(term: str) -> dict:
    data = await _gql(
        """
        query ($search: String) {
            Page(perPage: 5) {
                staff(search: $search) {
                    id
                    name { full native }
                    primaryOccupations
                    description(asHtml: false)
                }
            }
        }
        """,
        {"search": term},
    )
    staff = data.get("data", {}).get("Page", {}).get("staff", [])
    return {
        "result": [
            {
                "id": s["id"],
                "name": s["name"].get("full"),
                "native_name": s["name"].get("native"),
                "occupations": s.get("primaryOccupations", []),
                "description": (s.get("description") or "")[:300],
            }
            for s in staff
        ]
    }
