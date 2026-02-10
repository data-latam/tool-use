"""Wikipedia — article summaries and search. No API key needed."""

from app.sdk import RestServer

server = RestServer(
    "wikipedia",
    "Wikipedia REST API for article summaries and search",
    base_url="https://en.wikipedia.org",
    headers={"User-Agent": "ToolUseAPI/0.1"},
)

server.get(
    "get_summary",
    "/api/rest_v1/page/summary/{title}",
    description="Get a summary of a Wikipedia article",
    parameters={
        "title": {
            "type": "string",
            "required": True,
            "location": "path",
            "description": "Article title (e.g. 'Python_(programming_language)')",
        },
    },
)

server.get(
    "search",
    "/w/rest.php/v1/search/page",
    description="Search Wikipedia articles",
    parameters={
        "q": {
            "type": "string",
            "required": True,
            "location": "query",
            "description": "Search query",
        },
        "limit": {
            "type": "integer",
            "required": False,
            "location": "query",
            "description": "Max results (default 10)",
        },
    },
    extract="pages",
)
