"""
AFTER MCP server — clean descriptions + pinned manifest helper.

Still *can* be pointed at a poisoned description for rug-pull demos; default is clean.
Sandbox-scoped execution only via tools.py handlers.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import (
    MCPServer,
    MCPTool,
    clean_weather_description,
    ensure_sandbox_secret,
    tool_get_weather,
    tool_summarize,
)

PINNED_MANIFEST = ROOT / "after" / "pinned_manifest.json"


def build_server(*, poison: bool = False) -> MCPServer:
    ensure_sandbox_secret()
    from tools import poisoned_weather_description

    weather_desc = poisoned_weather_description() if poison else clean_weather_description()
    tools = [
        MCPTool(
            name="get_weather",
            description=weather_desc,
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


def write_pinned_manifest(server: MCPServer) -> Path:
    data = {
        "manifest_hash": server.manifest_hash(),
        "descriptions": server.description_manifest(),
        "allowed_tools": ["get_weather", "summarize"],
        "scopes": {
            "get_weather": ["weather.read"],
            "summarize": ["text.summarize"],
        },
    }
    PINNED_MANIFEST.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return PINNED_MANIFEST


if __name__ == "__main__":
    srv = build_server(poison=False)
    path = write_pinned_manifest(srv)
    print("AFTER server tools (clean):")
    for t in srv.list_tools():
        print(f"  - {t.name}: {t.description}")
    print("pinned →", path)
    print("manifest_hash:", srv.manifest_hash())
