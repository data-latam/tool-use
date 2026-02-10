"""E2B — execute code in a secure cloud sandbox. Requires E2B_API_KEY."""

import os

from app.sdk import ToolServer

server = ToolServer("e2b-server", "Execute code safely in an isolated cloud sandbox")


@server.register("run_code", description="Run Python code in a secure sandbox and return output")
async def run_code(code: str) -> dict:
    api_key = os.getenv("E2B_API_KEY", "")
    if not api_key:
        return {"error": "E2B_API_KEY not set in .env"}

    from e2b_code_interpreter import AsyncSandbox

    sandbox = await AsyncSandbox.create(api_key=api_key)
    try:
        execution = await sandbox.run_code(code)
        return {
            "result": {
                "stdout": "\n".join(execution.logs.stdout),
                "stderr": "\n".join(execution.logs.stderr),
                "results": [r.text for r in execution.results if r.text],
                "error": str(execution.error) if execution.error else None,
            }
        }
    finally:
        await sandbox.kill()
