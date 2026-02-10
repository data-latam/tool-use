import importlib.util
import logging
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Auto-discovers .py files in tools/ and registers whatever `server` they export."""

    def __init__(self) -> None:
        self._servers: dict[str, Any] = {}

    def load_tools(self, tools_dir: str | Path) -> None:
        tools_dir = Path(tools_dir)
        if not tools_dir.exists():
            logger.warning("Tools directory not found: %s", tools_dir)
            return

        for py_file in sorted(tools_dir.glob("*.py")):
            if py_file.name.startswith("_"):
                continue
            self._load_module(py_file)

    def _load_module(self, path: Path) -> None:
        module_name = f"tools.{path.stem}"
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            logger.warning("Cannot load %s", path)
            return

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        server = getattr(module, "server", None)
        if server is None:
            logger.warning("No 'server' in %s — skipping", path.name)
            return

        self._servers[server.name] = server
        logger.info("Loaded: %s  (%s)", server.name, path.name)

    # -- queries ------------------------------------------------------------
    def list_servers(self) -> list[str]:
        return list(self._servers.keys())

    def list_tools(self) -> list[dict[str, Any]]:
        tools: list[dict[str, Any]] = []
        for name, srv in self._servers.items():
            for tool_name, tool_cfg in srv.get_tools_config().items():
                params = tool_cfg.get("parameters", {})
                properties: dict[str, Any] = {}
                required: list[str] = []
                for pname, pcfg in params.items():
                    properties[pname] = {
                        "type": pcfg.get("type", "string"),
                        "description": pcfg.get("description", ""),
                    }
                    if pcfg.get("required", False):
                        required.append(pname)

                tools.append(
                    {
                        "server": name,
                        "name": tool_name,
                        "full_name": f"{name}.{tool_name}",
                        "description": tool_cfg.get("description", ""),
                        "inputSchema": {
                            "type": "object",
                            "properties": properties,
                            "required": required,
                        },
                    }
                )
        return tools

    # -- execution ----------------------------------------------------------
    async def execute(
        self, server_name: str, tool_name: str, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        server = self._servers.get(server_name)
        if not server:
            raise ValueError(f"Unknown server: {server_name}")
        if tool_name not in server.get_tool_names():
            raise ValueError(f"Unknown tool '{tool_name}' in '{server_name}'")
        return await server.execute(tool_name, arguments)


registry = ToolRegistry()
