#!/usr/bin/env python3
"""Run one MCP-primary ms search over a disposable stdio server."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import signal
import subprocess
import sys
from typing import Any


class SearchError(RuntimeError):
    """A fail-closed MCP transport or response error."""


def stop_server(proc: subprocess.Popen[str]) -> None:
    """Reap the one-shot server, escalating to its private process group."""
    if proc.poll() is not None:
        return
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except (ProcessLookupError, PermissionError):
        proc.terminate()
    try:
        proc.wait(timeout=1)
        return
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        proc.kill()
    proc.wait()


def request_lines(query: str) -> str:
    messages = [
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "ms-one-shot-search", "version": "1.0"},
            },
        },
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "search", "arguments": {"query": query}},
        },
    ]
    return "".join(json.dumps(message, separators=(",", ":")) + "\n" for message in messages)


def parse_json_lines(stdout: str) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    for line_number, line in enumerate(stdout.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SearchError(f"malformed JSON-RPC line {line_number}: {exc.msg}") from exc
        if not isinstance(message, dict):
            raise SearchError(f"malformed JSON-RPC line {line_number}: expected an object")
        messages.append(message)
    if not messages:
        raise SearchError("server returned no JSON-RPC messages")
    return messages


def text_content(result: dict[str, Any]) -> str:
    content = result.get("content")
    if not isinstance(content, list):
        raise SearchError("search result missing content array")
    texts = [
        item.get("text")
        for item in content
        if isinstance(item, dict)
        and item.get("type") == "text"
        and isinstance(item.get("text"), str)
    ]
    if len(texts) != 1:
        raise SearchError(f"search result expected one text payload, got {len(texts)}")
    return texts[0]


def search_payload(messages: list[dict[str, Any]]) -> dict[str, Any]:
    matches = [message for message in messages if message.get("id") == 2]
    if len(matches) != 1:
        raise SearchError(f"expected one search response with id=2, got {len(matches)}")
    response = matches[0]
    error = response.get("error")
    if error is not None:
        if isinstance(error, dict):
            code = error.get("code", "unknown")
            message = error.get("message", "unspecified error")
            raise SearchError(f"JSON-RPC error {code}: {message}")
        raise SearchError("malformed JSON-RPC error response")

    result = response.get("result")
    if not isinstance(result, dict):
        raise SearchError("search response missing result object")
    if result.get("isError") is True:
        raise SearchError(f"MCP search error: {text_content(result)}")

    structured = result.get("structuredContent")
    if structured is not None:
        if not isinstance(structured, dict):
            raise SearchError("search structuredContent is not an object")
        payload = structured
    else:
        raw = text_content(result)
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise SearchError(f"search text is not valid JSON: {exc.msg}") from exc

    if not isinstance(payload, dict):
        raise SearchError("search payload is not an object")
    results = payload.get("results")
    count = payload.get("count")
    if not isinstance(results, list):
        raise SearchError("search payload missing results array")
    if not isinstance(count, int) or isinstance(count, bool) or count < 0:
        raise SearchError("search payload missing nonnegative integer count")
    if count != len(results):
        raise SearchError(f"search payload count={count} but has {len(results)} results")
    return payload


def run_search(query: str, timeout: float) -> dict[str, Any]:
    try:
        command = shlex.split(os.environ.get("MS_BIN", "ms"))
    except ValueError as exc:
        raise SearchError(f"invalid MS_BIN: {exc}") from exc
    if not command:
        raise SearchError("MS_BIN resolved to an empty command")
    command.extend(("mcp", "serve"))
    try:
        proc = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
    except OSError as exc:
        raise SearchError(f"could not start {command[0]!r}: {exc}") from exc

    try:
        try:
            stdout, stderr = proc.communicate(request_lines(query), timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            stop_server(proc)
            raise SearchError(f"server timed out after {timeout:g}s") from exc
        if proc.returncode != 0:
            detail = " ".join(stderr.split())[-500:] or "no stderr"
            raise SearchError(f"server exited {proc.returncode}: {detail}")
        return search_payload(parse_json_lines(stdout))
    finally:
        stop_server(proc)


def positive_timeout(raw: str) -> float:
    try:
        value = float(raw)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a number") from exc
    if value <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Search ms through a disposable MCP stdio server and print the structured result JSON."
    )
    parser.add_argument("query", help="natural-language skill search query")
    parser.add_argument(
        "--timeout",
        type=positive_timeout,
        default=os.environ.get("MS_MCP_SEARCH_TIMEOUT", "30"),
        help="server timeout in seconds (default: %(default)s; env MS_MCP_SEARCH_TIMEOUT)",
    )
    args = parser.parse_args(argv)
    try:
        payload = run_search(args.query, args.timeout)
    except SearchError as exc:
        print(f"mcp-search: {exc}", file=sys.stderr)
        return 1
    json.dump(payload, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
