import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .mcp_server import mcp as mcp_server, sse
from .registry import registry
from .router import router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# -- Raw ASGI sub-app for MCP ----------------------------------------------
# MCP's SSE transport sends responses directly via scope/receive/send,
# so we bypass Starlette's endpoint wrapper and use raw ASGI.

async def mcp_asgi(scope, receive, send):
    if scope["type"] == "lifespan":
        while True:
            msg = await receive()
            if msg["type"] == "lifespan.startup":
                await send({"type": "lifespan.startup.complete"})
            elif msg["type"] == "lifespan.shutdown":
                await send({"type": "lifespan.shutdown.complete"})
                return
        return

    if scope["type"] != "http":
        return

    path = scope.get("path", "")

    if path.endswith("/sse"):
        async with sse.connect_sse(scope, receive, send) as (read, write):
            await mcp_server.run(
                read, write, mcp_server.create_initialization_options()
            )
    elif "/messages" in path:
        await sse.handle_post_message(scope, receive, send)
    else:
        await send({
            "type": "http.response.start",
            "status": 404,
            "headers": [(b"content-type", b"text/plain")],
        })
        await send({"type": "http.response.body", "body": b"Not found"})


# -- FastAPI app -----------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    registry.load_tools(settings.tools_dir)
    logger.info(
        "Loaded %d tools from %d servers",
        len(registry.list_tools()),
        len(registry.list_servers()),
    )
    yield


app = FastAPI(
    title="Tool Use API",
    description="Standardized API gateway — REST + MCP server",
    version="0.2.0",
    lifespan=lifespan,
)

app.include_router(router)
app.mount("/mcp", mcp_asgi)

_static = Path(__file__).parent / "static"


@app.get("/")
async def playground():
    return FileResponse(_static / "index.html")


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "servers": len(registry.list_servers()),
        "tools": len(registry.list_tools()),
    }
