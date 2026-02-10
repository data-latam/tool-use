import json
import logging
from pathlib import Path

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from .agent import AgentLoop
from .models import (
    AgentGenerateRequest,
    AgentGenerateResponse,
    ToolCallRequest,
    ToolCallResponse,
    ToolListResponse,
)
from .registry import registry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tools", tags=["tools"])

_SYSTEM_PROMPT_PATH = Path(__file__).resolve().parent.parent / "system-prompt.md"


@router.get("/", response_model=ToolListResponse)
async def list_tools():
    """List all available tools across all servers (MCP-compatible format)."""
    return {"tools": registry.list_tools()}


@router.get("/servers")
async def list_servers():
    """List registered tool servers."""
    return {"servers": registry.list_servers()}


@router.post("/execute", response_model=ToolCallResponse)
async def execute_tool(request: ToolCallRequest):
    """Execute a tool call. Format: {server, tool, arguments}."""
    try:
        result = await registry.execute(
            server_name=request.server,
            tool_name=request.tool,
            arguments=request.arguments,
        )
        return ToolCallResponse(
            server=request.server,
            tool=request.tool,
            success=True,
            result=result,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("Tool execution failed: %s.%s", request.server, request.tool)
        return ToolCallResponse(
            server=request.server,
            tool=request.tool,
            success=False,
            error=str(e),
        )


@router.post("/agent/generate", response_model=AgentGenerateResponse)
async def generate_trajectory(request: AgentGenerateRequest):
    """Run an AI agent loop to generate a trajectory from a prompt."""
    try:
        agent = AgentLoop(
            request.api_key,
            request.base_url,
            request.model,
            system_prompt=request.system_prompt or None,
        )
        turns = await agent.generate(
            request.prompt, request.max_turns, request.temperature
        )
        return AgentGenerateResponse(success=True, turns=turns)
    except httpx.HTTPStatusError as e:
        logger.exception("Agent API call failed")
        return AgentGenerateResponse(
            success=False,
            error=f"API error {e.response.status_code}: {e.response.text[:500]}",
        )
    except Exception as e:
        logger.exception("Agent generation failed")
        return AgentGenerateResponse(success=False, error=str(e))


@router.post("/agent/generate/stream")
async def generate_trajectory_stream(request: AgentGenerateRequest):
    """Stream trajectory generation turn-by-turn via SSE."""
    agent = AgentLoop(
        request.api_key,
        request.base_url,
        request.model,
        system_prompt=request.system_prompt or None,
    )

    async def event_stream():
        try:
            async for turn in agent.generate_stream(
                request.prompt, request.max_turns, request.temperature
            ):
                yield f"data: {json.dumps({'type': 'turn', 'turn': turn})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except httpx.HTTPStatusError as e:
            error_msg = f"API error {e.response.status_code}: {e.response.text[:500]}"
            logger.exception("Agent API call failed")
            yield f"data: {json.dumps({'type': 'error', 'error': error_msg})}\n\n"
        except Exception as e:
            logger.exception("Agent generation failed")
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/system-prompt")
async def get_system_prompt():
    """Read the system prompt from system-prompt.md."""
    if _SYSTEM_PROMPT_PATH.exists():
        return {"content": _SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")}
    return {"content": ""}


class SystemPromptUpdate(BaseModel):
    content: str


@router.put("/system-prompt")
async def update_system_prompt(body: SystemPromptUpdate):
    """Write the system prompt to system-prompt.md."""
    _SYSTEM_PROMPT_PATH.write_text(body.content, encoding="utf-8")
    return {"success": True}
