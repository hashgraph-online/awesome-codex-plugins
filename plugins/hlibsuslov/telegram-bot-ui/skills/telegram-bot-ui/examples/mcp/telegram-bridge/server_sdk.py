"""MCP server on the official Python SDK (mcp==2.3.0, MCP 2026-07-28).

API verified against mcp 2.3.0 on 2026-11-15: `from mcp.server import MCPServer`,
`@mcp.tool()`, `mcp.run("stdio")`; LATEST_PROTOCOL_VERSION = "2026-07-28".

  pip install -r examples/mcp/telegram-bridge/requirements.txt
  python examples/mcp/telegram-bridge/server_sdk.py [--live] [--state FILE] [--files-root DIR]
"""
from __future__ import annotations

import sys
from typing import Any

from mcp.server import MCPServer

from tools import TOOLS, UNTRUSTED, host_from_argv

host = host_from_argv(sys.argv[1:])
mcp = MCPServer("telegram-bridge", version="0.1.0",
                instructions="Reports, questions and approvals go to the operator's Telegram chat. " + UNTRUSTED)
DESC = {t["name"]: t["description"] for t in TOOLS}


@mcp.tool(description=DESC["telegram_notify"])
def telegram_notify(text: str, silent: bool = False) -> dict[str, Any]:
    return host.call("telegram_notify", {"text": text, "silent": silent})


@mcp.tool(description=DESC["telegram_progress"])
def telegram_progress(key: str, title: str | None = None, stages: list[str] | None = None,
                      stage: str | None = None, note: str | None = None, state: str = "running") -> dict[str, Any]:
    return host.call("telegram_progress", {"key": key, "title": title, "stages": stages, "stage": stage,
                                           "note": note, "state": state})


@mcp.tool(description=DESC["telegram_ask"])
def telegram_ask(question: str, choices: list[str] | None = None, default: str | None = None,
                 timeout_seconds: float = 300) -> dict[str, Any]:
    return host.call("telegram_ask", {"question": question, "choices": choices, "default": default,
                                      "timeout_seconds": timeout_seconds})


@mcp.tool(description=DESC["telegram_request_approval"])
def telegram_request_approval(summary: str, details: str | None = None, ttl_seconds: float = 600,
                              destructive: bool = False) -> dict[str, Any]:
    return host.call("telegram_request_approval", {"summary": summary, "details": details,
                                                   "ttl_seconds": ttl_seconds, "destructive": destructive})


@mcp.tool(description=DESC["telegram_send_file"])
def telegram_send_file(path: str, caption: str | None = None) -> dict[str, Any]:
    return host.call("telegram_send_file", {"path": path, "caption": caption})


@mcp.tool(description=DESC["telegram_inbox"])
def telegram_inbox(max_events: int = 20) -> dict[str, Any]:
    return host.call("telegram_inbox", {"max_events": max_events})


if __name__ == "__main__":
    mcp.run("stdio")
