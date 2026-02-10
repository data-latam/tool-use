import json
import logging
import re
from collections.abc import AsyncIterator
from typing import Any

import httpx

from .registry import registry

logger = logging.getLogger(__name__)

# Separator for function names: "ddg-search__search" instead of "ddg-search.search"
# because OpenAI/Gemini APIs only allow [a-zA-Z0-9_-] in function names.
_SEP = "__"

_FALLBACK_SYSTEM_PROMPT = (
    "You are a helpful AI assistant. You MUST use tools to answer every question. "
    "NEVER answer from memory alone. Structure responses with [REASONING] and [MESSAGE] sections."
)


def _build_tool_list_text() -> str:
    """Build a text list of tools for the system prompt."""
    lines: list[str] = []
    for tool in registry.list_tools():
        lines.append(f"- `{tool['server']}.{tool['name']}`: {tool['description']}")
    return "\n".join(lines) if lines else "- (no tools available)"


def _parse_sections(content: str) -> tuple[str, str]:
    """Parse [REASONING] and [MESSAGE] sections from model content.

    Returns (reasoning, message). Falls back gracefully if markers are missing.
    """
    if not content:
        return "", ""

    reasoning = ""
    message = ""

    # Try to extract [REASONING] ... [MESSAGE] ...
    r_match = re.search(
        r"\[REASONING\]\s*\n?(.*?)(?=\[MESSAGE\]|\Z)",
        content,
        re.DOTALL | re.IGNORECASE,
    )
    m_match = re.search(
        r"\[MESSAGE\]\s*\n?(.*)",
        content,
        re.DOTALL | re.IGNORECASE,
    )

    if r_match:
        reasoning = r_match.group(1).strip()
    if m_match:
        message = m_match.group(1).strip()

    # Fallback: if no markers found, put everything in message
    if not reasoning and not message:
        return "", content.strip()

    # If only one section found, use it appropriately
    if reasoning and not message:
        return reasoning, ""
    if message and not reasoning:
        return "", message

    return reasoning, message


class AgentLoop:
    """Run an OpenAI-compatible agent loop using registered tools."""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        system_prompt: str | None = None,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.system_prompt = system_prompt or _FALLBACK_SYSTEM_PROMPT

    def _build_system_prompt(self) -> str:
        """Inject the dynamic tool list into the system prompt."""
        tool_list = _build_tool_list_text()
        prompt = self.system_prompt
        if "{tool_list}" in prompt:
            prompt = prompt.replace("{tool_list}", tool_list)
        else:
            # Append tool list if placeholder not found
            prompt += "\n\n## Available tools\n" + tool_list
        return prompt

    def _build_function_schemas(
        self,
    ) -> tuple[list[dict[str, Any]], dict[str, tuple[str, str]]]:
        """Convert registry tools to OpenAI function calling format."""
        functions: list[dict[str, Any]] = []
        name_map: dict[str, tuple[str, str]] = {}

        for tool in registry.list_tools():
            func_name = f"{tool['server']}{_SEP}{tool['name']}"
            name_map[func_name] = (tool["server"], tool["name"])

            functions.append({
                "type": "function",
                "function": {
                    "name": func_name,
                    "description": tool["description"],
                    "parameters": tool["inputSchema"],
                },
            })
        return functions, name_map

    async def generate_stream(
        self,
        prompt: str,
        max_turns: int = 10,
        temperature: float = 0.7,
    ) -> AsyncIterator[dict[str, Any]]:
        """Run agent loop, yielding each turn dict as it completes."""
        tools, name_map = self._build_function_schemas()
        system_prompt = self._build_system_prompt()
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]

        async with httpx.AsyncClient(timeout=120.0) as client:
            for turn_num in range(1, max_turns + 1):
                # Force tool use on first turn so model doesn't skip
                force_tool = turn_num == 1

                try:
                    response = await self._call_model(
                        client, messages, tools, temperature,
                        tool_choice="required" if force_tool else "auto",
                    )
                except Exception as e:
                    logger.exception("Model API call failed on turn %d", turn_num)
                    yield {
                        "turn": turn_num,
                        "reasoning": f"API call failed: {e}",
                        "message": f"Error calling model: {e}",
                        "tool_calls": [],
                    }
                    break

                choice = response["choices"][0]
                msg = choice["message"]

                content = msg.get("content") or ""

                # Check for model-native thinking fields first
                native_reasoning = (
                    msg.get("reasoning_content")
                    or msg.get("thinking")
                    or ""
                )

                tool_calls_raw = msg.get("tool_calls") or []

                # Parse [REASONING] and [MESSAGE] from content
                if native_reasoning:
                    # Model has separate thinking — content is the message
                    reasoning = native_reasoning
                    message = content
                else:
                    # Parse from structured content
                    reasoning, message = _parse_sections(content)

                if not tool_calls_raw:
                    # Final answer turn
                    yield {
                        "turn": turn_num,
                        "reasoning": reasoning,
                        "message": message or content,
                        "tool_calls": [],
                    }
                    break

                # Process tool calls
                turn_tool_calls: list[dict[str, Any]] = []

                assistant_msg: dict[str, Any] = {
                    "role": "assistant",
                    "tool_calls": msg["tool_calls"],
                }
                if content:
                    assistant_msg["content"] = content
                messages.append(assistant_msg)

                for tc in tool_calls_raw:
                    func = tc["function"]
                    raw_name = func["name"]

                    if raw_name in name_map:
                        server_name, tool_name = name_map[raw_name]
                    elif _SEP in raw_name:
                        server_name, tool_name = raw_name.split(_SEP, 1)
                    elif "." in raw_name:
                        server_name, tool_name = raw_name.split(".", 1)
                    else:
                        server_name, tool_name = self._fuzzy_resolve(
                            raw_name, name_map
                        )

                    try:
                        arguments = json.loads(func.get("arguments", "{}"))
                    except (json.JSONDecodeError, TypeError):
                        arguments = {}

                    try:
                        result = await registry.execute(
                            server_name, tool_name, arguments
                        )
                        output = {"success": True, "result": result}
                    except Exception as e:
                        logger.warning(
                            "Tool execution failed: %s.%s — %s",
                            server_name, tool_name, e,
                        )
                        output = {"success": False, "error": str(e)}

                    turn_tool_calls.append({
                        "server": server_name,
                        "tool": tool_name,
                        "arguments": arguments,
                        "output": output,
                    })

                    # Truncate large outputs before sending back to model
                    output_str = json.dumps(output)
                    if len(output_str) > 3000:
                        output_str = output_str[:3000] + '..."}'
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": output_str,
                    })

                # Auto-fill reasoning/message if model returned empty
                if turn_tool_calls:
                    tool_descs = ", ".join(
                        f"`{tc['server']}.{tc['tool']}`"
                        for tc in turn_tool_calls
                    )
                    if not reasoning:
                        reasoning = (
                            f"I need to use {tool_descs} to answer the user's question."
                        )
                    if not message:
                        message = f"Let me look that up using {tool_descs}."

                yield {
                    "turn": turn_num,
                    "reasoning": reasoning,
                    "message": message,
                    "tool_calls": turn_tool_calls,
                }

    async def generate(
        self,
        prompt: str,
        max_turns: int = 10,
        temperature: float = 0.7,
    ) -> list[dict[str, Any]]:
        """Non-streaming convenience wrapper."""
        turns: list[dict[str, Any]] = []
        async for turn in self.generate_stream(prompt, max_turns, temperature):
            turns.append(turn)
        return turns

    @staticmethod
    def _fuzzy_resolve(
        bare_name: str,
        name_map: dict[str, tuple[str, str]],
    ) -> tuple[str, str]:
        """Match a bare tool name (e.g. 'search') to a registered tool."""
        for func_name, (server, tool) in name_map.items():
            if tool == bare_name:
                logger.info(
                    "Fuzzy-resolved bare name '%s' → %s.%s",
                    bare_name, server, tool,
                )
                return server, tool
        logger.warning("Could not resolve tool name: '%s'", bare_name)
        return "", bare_name

    async def _call_model(
        self,
        client: httpx.AsyncClient,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        temperature: float,
        tool_choice: str = "auto",
    ) -> dict[str, Any]:
        """POST to /chat/completions (OpenAI-compatible)."""
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = tool_choice
            payload["parallel_tool_calls"] = False

        logger.info("Sending %d tools, %d messages to %s", len(tools), len(messages), self.model)
        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        msg = data.get("choices", [{}])[0].get("message", {})
        logger.info(
            "Response: tool_calls=%d, content_len=%d, finish=%s",
            len(msg.get("tool_calls") or []),
            len(msg.get("content") or ""),
            data.get("choices", [{}])[0].get("finish_reason", "?"),
        )
        return data
