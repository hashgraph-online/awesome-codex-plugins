"""Inventory of an existing aiogram bot: entry points, callbacks, keyboards and texts, with
their source location and a confidence, plus a proposed screen list. Read-only: it never
writes a project. Static analysis (Python ast), so dynamic texts and keyboards are reported
as such instead of guessed.

    py -3 studio/bot-ui.py inventory --source path/to/bot --json
"""
from __future__ import annotations

import ast
import os
import re
from typing import Any

BUTTONS = {"InlineKeyboardButton", "KeyboardButton"}
SENDS = {"answer", "edit_text", "send_message", "reply", "edit_message_text", "answer_photo"}


def _str(node: ast.AST | None) -> str | None:
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def _kw(call: ast.Call, name: str) -> ast.AST | None:
    return next((k.value for k in call.keywords if k.arg == name), None)


def _filter_desc(node: ast.AST) -> dict | None:
    """aiogram filters: Command("x"), CommandStart(), F.data == "x", F.data.startswith("x:")."""
    if isinstance(node, ast.Call):
        fn = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", "")
        if fn == "CommandStart":
            return {"kind": "command", "value": "start"}
        if fn == "Command" and node.args:
            vals = [_str(a) for a in node.args]
            return {"kind": "command", "value": ",".join(v for v in vals if v)}
        if fn == "startswith" and isinstance(node.func, ast.Attribute) and node.args:
            return {"kind": "callback-prefix", "value": _str(node.args[0])}
    if isinstance(node, ast.Compare) and len(node.ops) == 1 and isinstance(node.ops[0], ast.Eq):
        if isinstance(node.left, ast.Attribute) and node.left.attr in ("data", "text"):
            v = _str(node.comparators[0])
            return {"kind": "callback" if node.left.attr == "data" else "text", "value": v}
    return None


def _screen_id(name: str) -> str:
    base = re.sub(r"^(cmd|on|handle|cb|show|send)_", "", name.lower())
    base = re.sub(r"[^a-z0-9_]+", "_", base).strip("_") or "screen"
    return f"imported.{base}"[:64]


def scan(source: str) -> dict[str, Any]:
    files = []
    for dirpath, dirnames, filenames in os.walk(source):
        dirnames[:] = [d for d in dirnames if not d.startswith(".") and d not in ("venv", ".venv", "node_modules", "__pycache__")]
        files += [os.path.join(dirpath, f) for f in filenames if f.endswith(".py")]
    out: dict[str, Any] = {"source": os.path.basename(os.path.abspath(source)), "sdk": "aiogram", "files": len(files),
                           "entryPoints": [], "callbacks": [], "buttons": [], "texts": [], "dynamic": [],
                           "proposedScreens": [], "status": "static"}
    for path in sorted(files):
        rel = os.path.relpath(path, source).replace(os.sep, "/")
        try:
            with open(path, encoding="utf-8") as fh:
                tree = ast.parse(fh.read(), filename=rel)
        except (SyntaxError, UnicodeDecodeError) as err:
            out["dynamic"].append({"file": rel, "line": 0, "what": f"not parsed: {err}"})
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                _handler(node, rel, out)
            elif isinstance(node, ast.Call):
                name = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", "")
                if name in BUTTONS:
                    text, cb, url = _kw(node, "text"), _kw(node, "callback_data"), _kw(node, "url")
                    entry = {"file": rel, "line": node.lineno, "text": _str(text), "kind": "inline" if name.startswith("Inline") else "reply"}
                    if cb is not None:
                        entry["callbackData"] = _str(cb)
                    if url is not None:
                        entry["url"] = _str(url)
                    entry["confidence"] = "high" if entry["text"] and (cb is None or entry.get("callbackData")) else "low"
                    if entry["confidence"] == "low":
                        out["dynamic"].append({"file": rel, "line": node.lineno, "what": f"{name} with computed text or callback_data"})
                    out["buttons"].append(entry)
    callbacks = {c["value"] for c in out["callbacks"] if c["kind"] == "callback"}
    prefixes = [c["value"] for c in out["callbacks"] if c["kind"] == "callback-prefix" and c["value"]]
    for b in out["buttons"]:
        cb = b.get("callbackData")
        if cb and cb not in callbacks and not any(cb.startswith(p) for p in prefixes):
            out["dynamic"].append({"file": b["file"], "line": b["line"], "what": f"callback_data {cb!r} has no static handler"})
    return out


def _handler(fn: ast.AST, rel: str, out: dict) -> None:
    filters = []
    for dec in fn.decorator_list:  # type: ignore[attr-defined]
        if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute) and dec.func.attr in ("message", "callback_query"):
            for arg in dec.args:
                d = _filter_desc(arg)
                if d:
                    filters.append(d)
            if not dec.args:
                filters.append({"kind": "any-" + dec.func.attr, "value": None})
    if not filters:
        return
    texts = []
    for node in ast.walk(fn):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in SENDS:
            arg = node.args[0] if node.args and node.func.attr not in ("send_message",) else (node.args[1] if len(node.args) > 1 else _kw(node, "text"))
            s = _str(arg)
            if s is None and arg is not None:
                out["dynamic"].append({"file": rel, "line": node.lineno, "what": f"{node.func.attr}() with a computed text"})
            elif s:
                texts.append(s)
                out["texts"].append({"file": rel, "line": node.lineno, "handler": fn.name, "text": s,  # type: ignore[attr-defined]
                                     "format": "regular.html" if re.search(r"</?(b|i|u|s|code|a)\b", s) else "regular.plain"})
    for f in filters:
        rec = {"file": rel, "line": fn.lineno, "handler": fn.name, **f}  # type: ignore[attr-defined]
        if f["kind"] == "command":
            out["entryPoints"].append(rec)
        else:
            out["callbacks"].append(rec)
    out["proposedScreens"].append({
        "id": _screen_id(fn.name), "sourceHandler": f"{rel}:{fn.lineno} {fn.name}",  # type: ignore[attr-defined]
        "triggers": filters, "texts": texts,
        "keepCallbackData": [f["value"] for f in filters if f["kind"] == "callback" and f["value"]],
        "confidence": "high" if texts and all(f["value"] for f in filters) else "medium" if texts else "low"})
