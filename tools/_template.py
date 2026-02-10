"""
TEMPLATE — Copy this file to create a new tool.

Option A — Custom logic (no external API):

    from app.sdk import ToolServer
    server = ToolServer("my_tool", "What it does")

    @server.register("tool_name", description="...")
    async def my_tool(param: str) -> dict:
        return {"result": "..."}


Option B — REST API (config only, zero code):

    from app.sdk import RestServer
    server = RestServer(
        "my_api",
        "What it does",
        base_url="https://api.example.com",
        # auth_type="bearer",       # none | api_key | bearer
        # auth_env_var="MY_KEY",    # env var with the key
    )

    server.get("tool_name", "/path/{param}",
        description="...",
        parameters={
            "param": {"type": "string", "required": True, "location": "path"},
        },
    )
"""
