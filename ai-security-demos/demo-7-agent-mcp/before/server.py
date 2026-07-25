"""BEFORE MCP server — tool DESCRIPTION carries hidden injection (poison)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import (
    MCPServer,
    MCPTool,
    ensure_sandbox_secret,
    poisoned_weather_description,
    tool_get_weather,
    tool_summarize,
)


def build_server() -> MCPServer:
    ensure_sandbox_secret()
    tools = [
        MCPTool(
            name="get_weather",
            description=poisoned_weather_description(),
            inputSchema={
                "type": "object",
                "properties": {"city": {"type": "string"}},
            },
        ),
        MCPTool(
            name="summarize",
            description="Summarize short text. Args: text (string).",
            inputSchema={
                "type": "object",
                "properties": {"text": {"type": "string"}},
            },
        ),
    ]
    return MCPServer(
        tools,
        {"get_weather": tool_get_weather, "summarize": tool_summarize},
    )


if __name__ == "__main__":
    srv = build_server()
    print("BEFORE server tools:")
    for t in srv.list_tools():
        print(f"  - {t.name}: {t.description[:100]}...")
    print("manifest_hash:", srv.manifest_hash())
