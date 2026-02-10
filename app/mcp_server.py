"""
MCP Server layer — exposes the same tools/ as an MCP-compatible server.

Clients (Claude, GPT, etc.) connect via SSE at /mcp/sse
and send tool calls to /mcp/messages/
"""

import json
import logging

from mcp.server import Server
from mcp.server.sse import SseServerTransport
import mcp.types as types

from .registry import registry

logger = logging.getLogger(__name__)

# -- MCP server instance ----------------------------------------------------

mcp = Server("tool-use-mcp")

# SSE transport — tells clients to POST to /mcp/messages/
sse = SseServerTransport("/messages/")


# -- handlers ---------------------------------------------------------------

@mcp.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name=t["full_name"],
            description=t["description"],
            inputSchema=t["inputSchema"],
        )
        for t in registry.list_tools()
    ]


@mcp.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent]:
    server_name, tool_name = name.split(".", 1)
    result = await registry.execute(server_name, tool_name, arguments or {})
    return [
        types.TextContent(type="text", text=json.dumps(result, default=str))
    ]
