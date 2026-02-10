"""
SDK for creating tools in a single file.

Usage — Custom logic:
    server = ToolServer("name", "description")

    @server.register("tool_name", description="...")
    async def my_tool(param: str) -> dict:
        return {"result": ...}

Usage — REST API:
    server = RestServer("name", "description", base_url="https://...")

    server.get("tool_name", "/path/{param}",
        description="...",
        parameters={"param": {"required": True, "location": "path"}},
    )
"""

import inspect
import os
from typing import Any, Awaitable, Callable

import httpx


# ---------------------------------------------------------------------------
# ToolServer — for custom logic (calculator, scrapers, anything)
# ---------------------------------------------------------------------------

class ToolServer:
    def __init__(self, name: str, description: str = "") -> None:
        self.name = name
        self.description = description
        self._tools: dict[str, dict] = {}
        self._handlers: dict[str, Callable[..., Awaitable[dict]]] = {}

    # -- decorator ----------------------------------------------------------
    def register(
        self,
        tool_name: str,
        description: str = "",
        parameters: dict | None = None,
    ):
        """Decorator. Parameters are auto-inferred from the function signature."""

        def decorator(func: Callable[..., Awaitable[dict]]):
            params = parameters or self._params_from_func(func)
            self._tools[tool_name] = {
                "description": description,
                "parameters": params,
            }
            self._handlers[tool_name] = func
            return func

        return decorator

    # -- execution ----------------------------------------------------------
    async def execute(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        handler = self._handlers.get(tool_name)
        if not handler:
            raise ValueError(f"Unknown tool: {tool_name}")
        return await handler(**arguments)

    # -- introspection ------------------------------------------------------
    def get_tool_names(self) -> list[str]:
        return list(self._tools.keys())

    def get_tools_config(self) -> dict:
        return self._tools

    # -- helpers ------------------------------------------------------------
    @staticmethod
    def _params_from_func(func: Callable) -> dict:
        type_map = {str: "string", int: "integer", float: "number", bool: "boolean"}
        params: dict[str, dict] = {}
        for pname, param in inspect.signature(func).parameters.items():
            params[pname] = {
                "type": type_map.get(param.annotation, "string"),
                "required": param.default is inspect.Parameter.empty,
                "description": "",
            }
        return params


# ---------------------------------------------------------------------------
# RestServer — for REST APIs (config-driven, zero handler code)
# ---------------------------------------------------------------------------

class RestServer:
    def __init__(
        self,
        name: str,
        description: str = "",
        base_url: str = "",
        headers: dict | None = None,
        auth_type: str = "none",
        auth_env_var: str = "",
        auth_header: str = "Authorization",
        auth_prefix: str = "",
    ) -> None:
        self.name = name
        self.description = description
        self.base_url = base_url.rstrip("/")
        self.headers = headers or {}
        self.auth_type = auth_type
        self.auth_env_var = auth_env_var
        self.auth_header = auth_header
        self.auth_prefix = auth_prefix
        self._tools: dict[str, dict] = {}
        self._client: httpx.AsyncClient | None = None

    # -- declarative tool registration --------------------------------------
    def get(self, tool_name: str, path: str, **kw: Any):
        self._add("GET", tool_name, path, **kw)

    def post(self, tool_name: str, path: str, **kw: Any):
        self._add("POST", tool_name, path, **kw)

    def _add(
        self,
        method: str,
        tool_name: str,
        path: str,
        description: str = "",
        parameters: dict | None = None,
        extract: str | None = None,
    ):
        self._tools[tool_name] = {
            "description": description,
            "method": method,
            "path": path,
            "parameters": parameters or {},
            "extract": extract,
        }

    # -- execution ----------------------------------------------------------
    async def execute(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        tool = self._tools[tool_name]
        method = tool["method"]
        path: str = tool["path"]

        query_params: dict[str, Any] = {}
        body_params: dict[str, Any] = {}

        for pname, pconfig in tool.get("parameters", {}).items():
            value = arguments.get(pname)
            if value is None:
                continue
            location = pconfig.get("location", "query")
            if location == "path":
                path = path.replace(f"{{{pname}}}", str(value))
            elif location == "body":
                body_params[pname] = value
            else:
                query_params[pname] = value

        client = await self._get_client()

        if method == "GET":
            resp = await client.get(path, params=query_params)
        elif method == "POST":
            resp = await client.post(path, json=body_params or arguments, params=query_params)
        else:
            resp = await client.request(method, path, params=query_params, json=body_params)

        resp.raise_for_status()
        result = resp.json()

        if tool.get("extract") and isinstance(result, dict):
            for key in tool["extract"].split("."):
                result = result.get(key, result)

        return {"result": result}

    # -- introspection ------------------------------------------------------
    def get_tool_names(self) -> list[str]:
        return list(self._tools.keys())

    def get_tools_config(self) -> dict:
        return self._tools

    # -- internal -----------------------------------------------------------
    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            headers = {**self.headers}
            if self.auth_type == "api_key":
                key = os.getenv(self.auth_env_var, "")
                headers[self.auth_header] = f"{self.auth_prefix}{key}" if self.auth_prefix else key
            elif self.auth_type == "bearer":
                key = os.getenv(self.auth_env_var, "")
                headers["Authorization"] = f"Bearer {key}"
            self._client = httpx.AsyncClient(
                base_url=self.base_url, headers=headers, timeout=30.0
            )
        return self._client
