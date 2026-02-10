from typing import Any

from pydantic import BaseModel


class ToolCallRequest(BaseModel):
    """Request to execute a tool. Mirrors MCP tool call format."""

    server: str
    tool: str
    arguments: dict[str, Any] = {}


class ToolCallResponse(BaseModel):
    server: str
    tool: str
    success: bool
    result: dict[str, Any] | None = None
    error: str | None = None


class ToolInfo(BaseModel):
    server: str
    name: str
    full_name: str
    description: str
    inputSchema: dict[str, Any]


class ToolListResponse(BaseModel):
    tools: list[ToolInfo]


class AgentGenerateRequest(BaseModel):
    """Request to generate a trajectory via an OpenAI-compatible model."""

    prompt: str
    api_key: str
    base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    model: str = "gemini-2.5-flash"
    max_turns: int = 10
    temperature: float = 0.7
    system_prompt: str = ""


class AgentGenerateResponse(BaseModel):
    success: bool
    turns: list[dict[str, Any]] = []
    error: str | None = None
