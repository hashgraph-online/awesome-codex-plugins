#!/usr/bin/env python3
"""Validate a converted request JSON against the Risk Desk model of the tool that will read it.

Run it with the Python that has riskdesk installed: it imports the request
models rather than restating them, so it accepts exactly what the tool accepts.

    .venv/bin/python check_artifact.py risk_exposure request.json

The tool name picks the model from the MCP server's own signatures. Prints
one verdict line, then one line per error: the path into the request (list
positions are zero-based), pydantic's message and the value found.
Cross-field rules (unique ids, scenarios naming every asset) run only when
every field is valid, so correct and re-run until it prints OK.
Exit 0 OK, 1 FAIL, 2 usage error, unknown tool or riskdesk not importable.
"""
import asyncio
import inspect
import json
import sys

try:
    from pydantic import ValidationError
    from riskdesk import server as desk
except ImportError as missing:
    print("FAIL riskdesk is not importable from {}: {}; run this with the riskdesk environment (risk-setup)".format(
        sys.executable, missing))
    raise SystemExit(2)


def request_models():
    """Tool name to request model, for every registered tool that takes a request."""
    tools = asyncio.run(desk.server.list_tools())
    found = {}
    for tool in tools:
        parameter = inspect.signature(getattr(desk, tool.name)).parameters.get("request")
        if parameter is not None:
            found[tool.name] = parameter.annotation
    return found


def errors(model, payload):
    """Every error pydantic reports, as 'path: message (found value)'."""
    try:
        model.model_validate(payload)
    except ValidationError as exc:
        return ["{}: {} (found {})".format(".".join(str(part) for part in e["loc"]) or "request", e["msg"],
                                           short(e.get("input"))) for e in exc.errors()]
    return []


def short(value):
    text = json.dumps(value, default=str)
    return text if len(text) <= 60 else text[:57] + "..."


def main(tool, path):
    models = request_models()
    if tool not in models:
        print("unknown tool {}; tools that take a request: {}".format(tool, ", ".join(sorted(models))))
        return 2
    model = models[tool]
    try:
        with open(path, encoding="utf-8") as handle:
            payload = json.load(handle)
    except json.JSONDecodeError as exc:
        print("FAIL {}: {} is not JSON: {}".format(tool, path, exc))
        return 1
    found = errors(model, payload)
    if found:
        print("FAIL {}: {} error(s) against {}".format(tool, len(found), model.__name__))
    else:
        print("OK {}: {} is a valid {}".format(tool, path, model.__name__))
    for problem in found:
        print("  " + problem)
    return 1 if found else 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: check_artifact.py <tool name, eg risk_exposure> <request JSON>")
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
