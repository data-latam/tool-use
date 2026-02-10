"""DuckDuckGo — web search and page fetching. No API key needed."""

import asyncio
from html.parser import HTMLParser

import httpx
from ddgs import DDGS

from app.sdk import ToolServer

server = ToolServer("ddg-search", "Web search and content fetching via DuckDuckGo")


@server.register("search", description="Search the web using DuckDuckGo")
async def search(query: str, max_results: int = 5) -> dict:
    def _search():
        return list(DDGS().text(query, max_results=max_results))

    results = await asyncio.to_thread(_search)
    return {
        "result": [
            {
                "title": r.get("title", ""),
                "url": r.get("href", ""),
                "snippet": r.get("body", ""),
            }
            for r in results
        ]
    }


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts: list[str] = []
        self._skip = False

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self._skip = True

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript"):
            self._skip = False

    def handle_data(self, data):
        if not self._skip:
            t = data.strip()
            if t:
                self.parts.append(t)


@server.register("fetch_content", description="Fetch and extract text content from a URL")
async def fetch_content(url: str) -> dict:
    async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
        resp = await client.get(url, headers={"User-Agent": "ToolUseAPI/0.1"})
        text = resp.text

    if "<html" in text[:500].lower():
        extractor = _TextExtractor()
        extractor.feed(text)
        text = "\n".join(extractor.parts)

    return {"result": {"url": url, "content": text[:2000]}}
