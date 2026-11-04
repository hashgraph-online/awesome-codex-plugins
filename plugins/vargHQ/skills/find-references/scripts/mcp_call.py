#!/usr/bin/env python3
"""Call a tool on a remote MCP server over HTTP, with no client setup.

For servers that need no sign-in, such as Refs search (https://refs.video/mcp), so an agent can use them without
adding an MCP server and restarting. Servers that need OAuth (FrameThrower) answer 401 here: connect those as MCP.

  python3 mcp_call.py <server-url> tools
  python3 mcp_call.py <server-url> <tool> '<json arguments>'

Prints the tool's text output. Standard library only.
"""
import json
import sys
import urllib.request


def post(url, body, session=None):
    headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    if session:
        headers["Mcp-Session-Id"] = session
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=120) as resp:
        sid = resp.headers.get("Mcp-Session-Id")
        raw = resp.read().decode()
    if raw.lstrip().startswith("{"):
        return json.loads(raw), sid
    last = None
    for line in raw.splitlines():  # server-sent events: keep the last JSON message
        if line.startswith("data:"):
            try:
                last = json.loads(line[5:].strip())
            except ValueError:
                pass
    return last, sid


def open_session(url):
    _, sid = post(url, {"jsonrpc": "2.0", "id": 0, "method": "initialize",
                        "params": {"protocolVersion": "2025-03-26", "capabilities": {},
                                   "clientInfo": {"name": "find-references", "version": "1.0.0"}}})
    try:
        post(url, {"jsonrpc": "2.0", "method": "notifications/initialized"}, sid)
    except Exception:
        pass
    return sid


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    url, tool = sys.argv[1], sys.argv[2]
    sid = open_session(url)
    if tool == "tools":
        res, _ = post(url, {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, sid)
        for t in res["result"]["tools"]:
            args = list((t.get("inputSchema") or {}).get("properties", {}))
            print(f"{t['name']}({', '.join(args)}): {(t.get('description') or '').splitlines()[0][:160]}")
        return
    args = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
    res, _ = post(url, {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                        "params": {"name": tool, "arguments": args}}, sid)
    if res is None:
        sys.exit("No answer from the server.")
    if "error" in res:
        sys.exit(f"Error: {res['error']}")
    out = res["result"]
    for block in out.get("content", []):
        if block.get("type") == "text":
            print(block["text"])
        elif block.get("type") == "image":
            print(f"[image {block.get('mimeType', '')}, {len(block.get('data', ''))} base64 chars]")
    if out.get("isError"):
        sys.exit(1)


if __name__ == "__main__":
    main()
