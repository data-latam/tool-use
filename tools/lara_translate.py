import os

import httpx

from app.sdk import ToolServer

server = ToolServer("lara-translate", "Translation tool using MyMemory API (free, no key required)")

_API_KEY = os.getenv("MYMEMORY_API_KEY", "")
_BASE = "https://api.mymemory.translated.net"


@server.register("translate", description="Translate text from one language to another")
async def translate(text: str, source: str = "en", target: str = "it") -> dict:
    params = {
        "q": text,
        "langpair": f"{source}|{target}",
    }
    if _API_KEY:
        params["key"] = _API_KEY

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(f"{_BASE}/get", params=params)
        data = resp.json()

    match = data.get("responseData", {})
    translation = match.get("translatedText", "")
    if not translation:
        return {"result": {"error": "Translation failed"}}

    return {"result": {
        "translation": translation,
        "source": source,
        "target": target,
    }}
