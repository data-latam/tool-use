"""arXiv — search and read academic papers. No API key needed."""

import xml.etree.ElementTree as ET

import httpx

from app.sdk import ToolServer

server = ToolServer("arxiv", "Search and read academic papers from arXiv")

_API = "http://export.arxiv.org/api/query"
_NS = {"atom": "http://www.w3.org/2005/Atom"}


def _text(el, tag):
    node = el.find(tag, _NS)
    return node.text.strip() if node is not None and node.text else ""


def _parse_entry(entry):
    return {
        "id": _text(entry, "atom:id").split("/abs/")[-1],
        "title": _text(entry, "atom:title"),
        "summary": _text(entry, "atom:summary")[:500],
        "authors": [
            a.find("atom:name", _NS).text
            for a in entry.findall("atom:author", _NS)
            if a.find("atom:name", _NS) is not None
        ],
        "published": _text(entry, "atom:published"),
        "categories": [c.get("term") for c in entry.findall("atom:category", _NS)],
        "pdf_url": next(
            (
                l.get("href")
                for l in entry.findall("atom:link", _NS)
                if l.get("title") == "pdf"
            ),
            None,
        ),
    }


@server.register("search_papers", description="Search for academic papers on arXiv")
async def search_papers(
    query: str, max_results: int = 5, categories: str = ""
) -> dict:
    search_query = f"all:{query}"
    if categories:
        search_query += f" AND cat:{categories}"

    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        resp = await client.get(
            _API,
            params={
                "search_query": search_query,
                "max_results": max_results,
                "sortBy": "relevance",
            },
        )
        if resp.status_code == 429:
            return {"error": "arXiv rate limit — retry in a few seconds"}
        resp.raise_for_status()
        root = ET.fromstring(resp.text)
        return {"result": [_parse_entry(e) for e in root.findall("atom:entry", _NS)]}


@server.register("read_paper", description="Get full details of a paper by arXiv ID")
async def read_paper(paper_id: str) -> dict:
    # Accept both "2301.07041" and full URL
    paper_id = paper_id.split("/abs/")[-1].strip()

    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        resp = await client.get(_API, params={"id_list": paper_id})
        root = ET.fromstring(resp.text)
        entry = root.find("atom:entry", _NS)
        if entry is None:
            return {"error": "Paper not found"}
        return {"result": _parse_entry(entry)}
