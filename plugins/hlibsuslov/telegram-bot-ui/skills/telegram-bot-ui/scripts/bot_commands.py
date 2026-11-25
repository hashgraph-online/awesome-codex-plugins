#!/usr/bin/env python3
"""Audit and plan a bot's command menu (Bot API setMyCommands lifecycle). Offline, standard library only.

  py -3 scripts/tgui.py commands scan  --root . [--json]
  py -3 scripts/tgui.py commands audit --root . [--json]
  py -3 scripts/tgui.py commands plan  --root . [--file bot-ui/commands.json] [--json]
  py -3 scripts/tgui.py commands diff  --root . --live-json saved-getMyCommands.json [--scope default]
                                       [--language-code ru] [--file bot-ui/commands.json] [--json]

Never needs a token and never calls Telegram. `plan` prints the exact requests to send; sending them
(for example through tgkit with TELEGRAM_LIVE=1) is a separate, explicit step.

scan   handlers (aiogram Command/CommandStart/F.text, python-telegram-bot CommandHandler/PrefixHandler,
       pyTelegramBotAPI message_handler(commands=), grammY/Telegraf bot.command / Telegraf bot.start|help,
       raw text.startswith("/x") and text == "/x") and registrations (setMyCommands / set_my_commands /
       SetMyCommands with BotCommand(...) or {"command", "description"} literals, a list reached through a
       variable, and bot-ui/commands.json), each with file:line. Python is read with `ast`, JS/TS with
       regular expressions after comments are blanked. Not detected: other languages, Telethon/Pyrogram,
       node-telegram-bot-api onText, menus built at run time (reported as unresolved) and menus set only
       in BotFather. Skipped: dot folders, node_modules, venv (any folder with pyvenv.cfg), dist, build.
audit  findings with stable codes. Exit 1 when there is an error or a warning, 0 otherwise (info never
       fails): COMMAND_NAME_INVALID, DESCRIPTION_LENGTH, COMMAND_NOT_REGISTERED, COMMAND_NO_HANDLER,
       COMMAND_DUPLICATE, TOO_MANY_COMMANDS, LOCALE_MISSING, SCOPE_SHADOWED, DESCRIPTION_STYLE.
plan   the Bot API requests that make Telegram match bot-ui/commands.json: a JSON array of
       {"method", "params"}; problems go to stderr (or into the object printed with --json); exit 1 on a
       problem. Every request is also checked in-process against the offline catalog.
diff   declaration against a saved getMyCommands response: added, removed, changed, reordered.

How Telegram picks a list (core.telegram.org/bots/api#determining-list-of-commands): the FIRST list that
is set wins and it replaces the others, nothing is merged. For each scope Telegram tries
scope + language_code, then scope with an empty language_code, then moves to the next scope:
  private chat  chat, all_private_chats, default
  group         chat_member, chat_administrators (admins), chat, all_chat_administrators (admins),
                all_group_chats, default
A narrower list therefore hides every command it leaves out, and a language list hides the fallback.

bot-ui/commands.json (format "bot-ui-commands/v1"):
  {"format": "bot-ui-commands/v1", "default_language": "en",
   "lists": [{"scope": {"type": "default"}, "language_code": "",
              "commands": [{"command": "start", "description": {"en": "Open the main menu", "ru": "..."},
                            "is_ephemeral": false, "hidden": false}]}],
   "remove": [{"scope": {"type": "all_group_chats"}, "language_code": "de"}]}
  scope          optional, default {"type": "default"}; chat scopes need chat_id, chat_member also user_id
  language_code  "" (fallback) or two lowercase letters
  description    a string, or {"<lang>": text}. In a list with language_code "" the plan emits the fallback
                 list with default_language text, plus one list per other language found in the maps (a
                 command without that language reuses the default text and audit reports LOCALE_MISSING).
                 A list with an explicit language_code takes that language's text. An explicit list wins
                 over an expanded one for the same scope and language.
  hidden         the command has a handler but is kept out of the menu (silences COMMAND_NOT_REGISTERED,
                 never sent to Telegram); it may omit description
  is_ephemeral   sent only when true
  remove         one deleteMyCommands per (scope, language_code); it cannot also be set in lists
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import re
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass, field

SCRIPTS = os.path.dirname(os.path.abspath(__file__))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

FORMAT = "bot-ui-commands/v1"
DECLARATION = "bot-ui/commands.json"
NAME_RE = re.compile(r"^[a-z0-9_]{1,32}$")
LANG_RE = re.compile(r"^(?:[a-z]{2})?$")
MAX_COMMANDS = 100
DESC_MAX = 256
SCOPE_FIELDS = {"default": (), "all_private_chats": (), "all_group_chats": (), "all_chat_administrators": (),
                "chat": ("chat_id",), "chat_administrators": ("chat_id",), "chat_member": ("chat_id", "user_id")}
SKIP_DIRS = {"node_modules", "venv", "dist", "build", "__pycache__", "site-packages"}
PY_EXT = {".py"}
JS_EXT = {".js", ".mjs", ".cjs", ".ts", ".mts", ".cts", ".jsx", ".tsx"}
MAX_BYTES = 1_500_000
SET_CALLS = {"setMyCommands", "set_my_commands", "SetMyCommands"}
TELEBOT_DECORATORS = {"message_handler", "register_message_handler", "edited_message_handler",
                      "channel_post_handler", "register_edited_message_handler"}
TEXTISH = re.compile(r"text|message|msg|command|cmd", re.I)
PREFIX_RE = re.compile(r"^/([A-Za-z0-9_]{1,32})")
EXACT_RE = re.compile(r"^/([A-Za-z0-9_]{1,32})(?:@\w+)?$")
SEVERITY = {"error": 0, "warning": 1, "info": 2}

# Narrowest scope first, as listed in the Bot API documentation.
PRIVATE_ORDER = ["chat", "all_private_chats", "default"]
GROUP_ORDER = ["chat_member", "chat_administrators", "chat", "all_chat_administrators", "all_group_chats",
               "default"]


class DeclarationError(Exception):
    pass


# ---------------------------------------------------------------- scopes


def scope_key(scope: dict | None) -> str:
    return json.dumps(scope, sort_keys=True, separators=(",", ":"))


def scope_label(scope: dict | None) -> str:
    if scope is None:
        return "unknown scope"
    extra = ",".join(f"{k}={scope[k]}" for k in ("chat_id", "user_id") if k in scope)
    return scope["type"] + (f"({extra})" if extra else "")


def lang_label(lang: str | None) -> str:
    return "?" if lang is None else (lang or "fallback")


def parse_scope(raw, where: str) -> dict:
    if raw is None:
        return {"type": "default"}
    if not isinstance(raw, dict) or raw.get("type") not in SCOPE_FIELDS:
        raise DeclarationError(f"{where}: scope must be an object whose type is one of {', '.join(SCOPE_FIELDS)}")
    kind = raw["type"]
    extra = set(raw) - {"type", *SCOPE_FIELDS[kind]}
    if extra:
        raise DeclarationError(f"{where}: scope {kind} does not take {', '.join(sorted(extra))}")
    for name in SCOPE_FIELDS[kind]:
        value = raw.get(name)
        ok = (isinstance(value, int) and not isinstance(value, bool)) or (name == "chat_id" and isinstance(value, str)
                                                                        and value != "")
        if not ok:
            raise DeclarationError(f"{where}: scope {kind} needs {name}")
    return dict(raw)


# ---------------------------------------------------------------- scan: data


@dataclass
class Handler:
    command: str
    file: str
    line: int
    framework: str


@dataclass
class Entry:
    command: str | None
    description: str | None
    line: int


@dataclass
class Registration:
    file: str
    line: int
    method: str                      # setMyCommands | set_my_commands | SetMyCommands | BotCommand | commands.json
    scope: dict | None               # None: not readable from the code
    language_code: str | None        # None: not readable from the code
    commands: list[Entry] = field(default_factory=list)
    resolved: bool = True            # False: the list itself could not be read
    source: str = "code"


def normalize_handler(name: str) -> str | None:
    name = name.strip().lstrip("/").split("@")[0].lower()
    return name if NAME_RE.match(name) else None


def iter_sources(root: str):
    for base, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if not d.startswith(".") and d not in SKIP_DIRS
                         and not os.path.exists(os.path.join(base, d, "pyvenv.cfg")))
        for name in sorted(files):
            ext = os.path.splitext(name)[1].lower()
            if ext not in PY_EXT | JS_EXT or name.endswith((".d.ts", ".min.js")):
                continue
            path = os.path.join(base, name)
            try:
                if os.path.getsize(path) <= MAX_BYTES:
                    yield path
            except OSError:
                continue


# ---------------------------------------------------------------- scan: Python


def _callee(call: ast.Call) -> str | None:
    if isinstance(call.func, ast.Name):
        return call.func.id
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    return None


def _strs(node) -> list[str]:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value]
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return [e.value for e in node.elts if isinstance(e, ast.Constant) and isinstance(e.value, str)]
    return []


def _kw(call: ast.Call, name: str):
    return next((k.value for k in call.keywords if k.arg == name), None)


def _unparse(node) -> str:
    try:
        return ast.unparse(node)
    except (ValueError, TypeError, RecursionError):
        return ""


def _py_handler_call(call: ast.Call, aiogram: bool) -> tuple[str, list[str]] | None:
    fn = _callee(call)
    if fn == "CommandStart" and aiogram:
        return "aiogram", ["start"]
    if fn == "Command" and aiogram:
        names = [s for a in call.args for s in _strs(a)]
        kw = _kw(call, "commands")
        return "aiogram", names + (_strs(kw) if kw is not None else [])
    if fn == "CommandHandler":
        node = call.args[0] if call.args else _kw(call, "command")
        return "python-telegram-bot", _strs(node) if node is not None else []
    if fn == "PrefixHandler":
        node = call.args[1] if len(call.args) > 1 else _kw(call, "command")
        return "python-telegram-bot", _strs(node) if node is not None else []
    if fn in TELEBOT_DECORATORS:
        kw = _kw(call, "commands")
        return "pyTelegramBotAPI", _strs(kw) if kw is not None else []
    return None


def _py_raw_handler(node) -> tuple[str, list[str]] | None:
    """text.startswith("/x"), text == "/x", text in ("/a", "/b"), F.text == "/x"."""
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "startswith" \
            and node.args:
        recv = _unparse(node.func.value)
        names = [m.group(1) for s in _strs(node.args[0]) if (m := PREFIX_RE.match(s))]
        if names and TEXTISH.search(recv):
            return ("aiogram" if recv.startswith("F.") else "raw"), names
    if isinstance(node, ast.Compare) and len(node.ops) == 1 and isinstance(node.ops[0], (ast.Eq, ast.In)):
        for recv, lit in ((node.left, node.comparators[0]), (node.comparators[0], node.left)):
            names = [m.group(1) for s in _strs(lit) if (m := EXACT_RE.match(s))]
            text = _unparse(recv)
            if names and not _strs(recv) and TEXTISH.search(text):
                return ("aiogram" if text.startswith("F.") else "raw"), names
    return None


def _snake(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def _literal(node):
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        inner = _literal(node.operand)
        return -inner if isinstance(inner, (int, float)) and not isinstance(inner, bool) else "?"
    return node.value if isinstance(node, ast.Constant) else "?"


def _py_scope(node) -> dict | None:
    """The scope argument as a dict; None when the code builds it at run time."""
    if node is None or (isinstance(node, ast.Constant) and node.value is None):
        return {"type": "default"}
    if isinstance(node, ast.Call):
        name = _callee(node) or ""
        kind = _snake(name[len("BotCommandScope"):]) if name.startswith("BotCommandScope") else None
        if kind == "":
            return None
        if kind in SCOPE_FIELDS:
            scope = {"type": kind}
            for i, field_name in enumerate(SCOPE_FIELDS[kind]):
                arg = _kw(node, field_name)
                arg = arg if arg is not None else (node.args[i] if len(node.args) > i else None)
                scope[field_name] = _literal(arg) if arg is not None else "?"
            return None if "?" in scope.values() else scope
    if isinstance(node, ast.Attribute) and node.attr.lower() in SCOPE_FIELDS \
            and _unparse(node.value).endswith("BotCommandScope"):
        return {"type": node.attr.lower()} if not SCOPE_FIELDS[node.attr.lower()] else None
    if isinstance(node, ast.Dict):
        raw = {k.value: v.value for k, v in zip(node.keys, node.values)
               if isinstance(k, ast.Constant) and isinstance(v, ast.Constant)}
        if raw.get("type") in SCOPE_FIELDS and len(raw) == len(node.keys):
            return raw
    return None


def _py_language(node) -> str | None:
    if node is None or (isinstance(node, ast.Constant) and node.value is None):
        return ""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _latest(env: dict, name: str, line: int):
    """The value last assigned to `name` at or before `line` (the first one when none is earlier)."""
    assigned = env[name]
    return max((a for a in assigned if a[0] <= line), key=lambda a: a[0], default=assigned[0])[1]


def _resolve_elements(node, env: dict, line: int, depth: int = 0) -> list | None:
    """The element nodes of a list literal, following names and `+` (None when not statically known)."""
    if depth > 4:
        return None
    if isinstance(node, (ast.List, ast.Tuple)):
        return list(node.elts)
    if isinstance(node, ast.Name) and node.id in env:
        return _resolve_elements(_latest(env, node.id, line), env, line, depth + 1)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = _resolve_elements(node.left, env, line, depth + 1)
        right = _resolve_elements(node.right, env, line, depth + 1)
        return None if left is None or right is None else left + right
    return None


def _command_entry(node, env: dict) -> tuple[Entry, ast.AST] | None:
    if isinstance(node, ast.Name) and node.id in env:
        node = _latest(env, node.id, node.lineno)
    if isinstance(node, ast.Call) and _callee(node) == "BotCommand":
        cmd = _kw(node, "command") if _kw(node, "command") is not None else (node.args[0] if node.args else None)
        desc = _kw(node, "description") if _kw(node, "description") is not None else (
            node.args[1] if len(node.args) > 1 else None)
    elif isinstance(node, ast.Dict):
        pairs = {k.value: v for k, v in zip(node.keys, node.values) if isinstance(k, ast.Constant)}
        if "command" not in pairs:
            return None
        cmd, desc = pairs["command"], pairs.get("description")
    elif isinstance(node, (ast.Tuple, ast.List)) and len(node.elts) == 2 and all(_strs(e) for e in node.elts):
        cmd, desc = node.elts
    else:
        return None
    text = lambda n: n.value if isinstance(n, ast.Constant) and isinstance(n.value, str) else None  # noqa: E731
    return Entry(text(cmd), text(desc), node.lineno), node


def _is_command_literal(node) -> bool:
    if isinstance(node, ast.Call):
        return _callee(node) == "BotCommand"
    if isinstance(node, ast.Dict):
        keys = {k.value for k in node.keys if isinstance(k, ast.Constant)}
        return {"command", "description"} <= keys
    return False


def scan_python(rel: str, text: str) -> tuple[list[Handler], list[Registration]] | None:
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError, RecursionError):
        return None
    aiogram = "aiogram" in text
    handlers: list[Handler] = []
    regs: list[Registration] = []
    env: dict[str, list] = defaultdict(list)
    parents: dict[int, ast.AST] = {}
    nodes = list(ast.walk(tree))
    for node in nodes:
        for child in ast.iter_child_nodes(node):
            parents[id(child)] = node
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None:
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if len(targets) == 1 and isinstance(targets[0], ast.Name):
                env[targets[0].id].append((node.lineno, node.value))
    consumed: set[int] = set()
    for node in nodes:
        if isinstance(node, ast.Call) and _callee(node) in SET_CALLS:
            cmds = node.args[0] if node.args else _kw(node, "commands")
            scope = _kw(node, "scope") if _kw(node, "scope") is not None else (
                node.args[1] if len(node.args) > 1 else None)
            lang = _kw(node, "language_code") if _kw(node, "language_code") is not None else (
                node.args[2] if len(node.args) > 2 else None)
            elements = _resolve_elements(cmds, env, node.lineno) if cmds is not None else None
            reg = Registration(rel, node.lineno, _callee(node), _py_scope(scope), _py_language(lang),
                               resolved=elements is not None)
            for el in elements or []:
                found = _command_entry(el, env)
                if found:
                    reg.commands.append(found[0])
                    consumed.add(id(found[1]))
            regs.append(reg)
            continue
        found_handler = (_py_handler_call(node, aiogram) if isinstance(node, ast.Call) else None) \
            or _py_raw_handler(node)
        if found_handler:
            framework, names = found_handler
            handlers += [Handler(n, rel, node.lineno, framework) for raw in names if (n := normalize_handler(raw))]
    loose: dict[int, Registration] = {}
    for node in nodes:
        if id(node) in consumed or not _is_command_literal(node):
            continue
        entry = _command_entry(node, env)
        if not entry:
            continue
        parent = parents.get(id(node))
        key = id(parent) if isinstance(parent, (ast.List, ast.Tuple)) else id(node)
        loose.setdefault(key, Registration(rel, node.lineno, "BotCommand", None, None)).commands.append(entry[0])
    return handlers, regs + list(loose.values())


# ---------------------------------------------------------------- scan: JS / TS


def blank_js_comments(text: str) -> str:
    """Comments become spaces; offsets and line numbers stay the same."""
    out: list[str] = []
    i, n, quote = 0, len(text), None
    while i < n:
        c = text[i]
        if quote:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(text[i + 1])
                i += 2
                continue
            if c == quote or (c == "\n" and quote != "`"):
                quote = None
            i += 1
        elif c in "\"'`":
            quote = c
            out.append(c)
            i += 1
        elif text.startswith("//", i):
            j = text.find("\n", i)
            j = n if j < 0 else j
            out.append(" " * (j - i))
            i = j
        elif text.startswith("/*", i):
            j = text.find("*/", i + 2)
            j = n if j < 0 else j + 2
            out.append("".join(ch if ch == "\n" else " " for ch in text[i:j]))
            i = j
        else:
            out.append(c)
            i += 1
    return "".join(out)


def _balanced(text: str, start: int, open_ch: str, close_ch: str) -> int:
    """Index just past the bracket that closes text[start]; -1 when it never closes."""
    depth, quote, i = 0, None, start
    while i < len(text):
        c = text[i]
        if quote:
            if c == "\\":
                i += 2
                continue
            if c == quote:
                quote = None
        elif c in "\"'`":
            quote = c
        elif c == open_ch:
            depth += 1
        elif c == close_ch:
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return -1


def _arg_spans(text: str, lo: int, hi: int) -> list[tuple[int, int]]:
    spans, depth, quote, start, i = [], 0, None, lo, lo
    while i < hi:
        c = text[i]
        if quote:
            if c == "\\":
                i += 2
                continue
            if c == quote:
                quote = None
        elif c in "\"'`":
            quote = c
        elif c in "([{":
            depth += 1
        elif c in ")]}":
            depth -= 1
        elif c == "," and depth == 0:
            spans.append((start, i))
            start = i + 1
        i += 1
    if text[start:hi].strip():
        spans.append((start, hi))
    return spans


def _js_strings(snippet: str) -> list[str]:
    return [m.group(2) for m in re.finditer(r"""(["'`])((?:\\.|(?!\1)[^\\\n])*)\1""", snippet)]


def _js_prop(obj: str, key: str) -> tuple[bool, str | None]:
    """(key present, its string literal or None when the value is an expression)."""
    m = re.search(r"""(?<![\w$])["']?%s["']?\s*:\s*(?:(["'`])((?:\\.|(?!\1)[^\\\n])*)\1)?""" % key, obj)
    if not m:
        return False, None
    return True, re.sub(r"\\(.)", r"\1", m.group(2)) if m.group(1) else None


def _js_entries(text: str, lo: int, hi: int) -> list[tuple[Entry, tuple[int, int]]]:
    found = []
    for m in re.finditer(r"\{[^{}]*\}", text[lo:hi]):
        has_cmd, cmd = _js_prop(m.group(0), "command")
        has_desc, desc = _js_prop(m.group(0), "description")
        if has_cmd and has_desc:
            start = lo + m.start()
            found.append((Entry(cmd, desc, text.count("\n", 0, start) + 1), (start, lo + m.end())))
    return found


def _js_scope(args: str) -> dict | None:
    m = re.search(r"(?<![\w$])scope\s*:\s*(\{[^{}]*\}|[\w$.]+)", args)
    if not m:
        return {"type": "default"}
    body = m.group(1)
    kind = re.search(r"""type\s*:\s*["'](\w+)["']""", body)
    if not body.startswith("{") or not kind or kind.group(1) not in SCOPE_FIELDS:
        return None
    scope: dict = {"type": kind.group(1)}
    for name in SCOPE_FIELDS[kind.group(1)]:
        value = re.search(r"""%s\s*:\s*(-?\d+|["'][^"']*["'])""" % name, body)
        if not value:
            return None
        raw = value.group(1)
        scope[name] = int(raw) if re.fullmatch(r"-?\d+", raw) else raw[1:-1]
    return scope


def scan_js(rel: str, source: str) -> tuple[list[Handler], list[Registration]]:
    text = blank_js_comments(source)
    handlers: list[Handler] = []
    regs: list[Registration] = []
    telegram = re.search(r"grammy|telegraf|telegram", text, re.I) is not None

    def line_of(pos: int) -> int:
        return text.count("\n", 0, pos) + 1

    def add(names, pos, framework):
        handlers.extend(Handler(n, rel, line_of(pos), framework) for raw in names if (n := normalize_handler(raw)))

    if telegram:
        for m in re.finditer(r"\.command\s*\(\s*(\[[^\]]*\]|[\"'`][^\"'`\n]*[\"'`])", text):
            add(_js_strings(m.group(1)), m.start(), "grammY/Telegraf")
        if re.search(r"telegraf", text, re.I):
            for m in re.finditer(r"(?<![\w$])(?:bot|composer|scene|router)\.(start|help|settings)\s*\(\s*"
                                 r"(?:async\b|function\b|\(|[A-Za-z_$][\w$]*\s*(?:=>|[,)]))", text):
                add([m.group(1)], m.start(), "grammY/Telegraf")
        recv = r"([\w$.?]*(?:text|message|msg|command|cmd)[\w$.?]*)"
        for m in re.finditer(recv + r"\s*\.startsWith\(\s*([\"'`])/([A-Za-z0-9_]{1,32})", text, re.I):
            add([m.group(3)], m.start(), "raw")
        for m in re.finditer(recv + r"\s*={2,3}\s*([\"'`])/([A-Za-z0-9_]{1,32})(?:@\w+)?\2", text, re.I):
            add([m.group(3)], m.start(), "raw")
        for m in re.finditer(r"([\"'`])/([A-Za-z0-9_]{1,32})(?:@\w+)?\1\s*={2,3}\s*" + recv, text, re.I):
            add([m.group(2)], m.start(), "raw")

    consumed: list[tuple[int, int]] = []
    for m in re.finditer(r"(?<![\w$])(?:setMyCommands|set_my_commands)\s*\(", text):
        open_at = m.end() - 1
        close = _balanced(text, open_at, "(", ")")
        if close < 0:
            continue
        args = text[open_at + 1:close - 1]
        spans = _arg_spans(text, open_at + 1, close - 1)
        first = text[spans[0][0]:spans[0][1]].strip() if spans else ""
        lo, hi = spans[0] if spans else (open_at + 1, close - 1)
        if re.fullmatch(r"[A-Za-z_$][\w$]*", first):
            decl = re.search(r"(?:const|let|var)\s+%s\b[^=\n]*=\s*(\[|\{)" % re.escape(first), text)
            lo, hi = (decl.end() - 1, _balanced(text, decl.end() - 1, decl.group(1),
                                                "]" if decl.group(1) == "[" else "}")) if decl else (0, -1)
        entries = _js_entries(text, lo, hi) if hi > lo else []
        has_lang, lang = _js_prop(args, "language_code")
        reg = Registration(rel, line_of(m.start()), m.group(0).rstrip("( \t"), _js_scope(args),
                           lang if has_lang else "", [e for e, _ in entries], resolved=bool(entries))
        regs.append(reg)
        consumed.append((open_at, close))
        consumed.extend(span for _, span in entries)
    loose: list[Registration] = []
    last_end = -1
    for entry, (start, end) in _js_entries(text, 0, len(text)):
        if any(a <= start < b for a, b in consumed):
            continue
        if loose and re.fullmatch(r"[\s,]*", text[last_end:start]):
            loose[-1].commands.append(entry)
        else:
            loose.append(Registration(rel, entry.line, "command literal", None, None, [entry]))
        last_end = end
    return handlers, regs + loose


# ---------------------------------------------------------------- scan: project


@dataclass
class Scan:
    root: str
    handlers: list[Handler]
    registrations: list[Registration]
    declaration: "Declaration | None"
    unreadable: list[str]


def read_text(path: str) -> str:
    with open(path, encoding="utf-8-sig", errors="replace") as fh:  # -sig: editors on Windows add a BOM
        return fh.read()


def scan_project(root: str, declaration_path: str | None = None) -> Scan:
    root = os.path.abspath(root)
    handlers: list[Handler] = []
    regs: list[Registration] = []
    unreadable: list[str] = []
    for path in iter_sources(root):
        rel = os.path.relpath(path, root).replace("\\", "/")
        try:
            text = read_text(path)
        except OSError:
            unreadable.append(rel)
            continue
        if os.path.splitext(path)[1].lower() in PY_EXT:
            result = scan_python(rel, text)
            if result is None:
                unreadable.append(rel)
                continue
        else:
            result = scan_js(rel, text)
        handlers += result[0]
        regs += result[1]
    declaration = None
    decl_path = declaration_path or os.path.join(root, *DECLARATION.split("/"))
    if os.path.isfile(decl_path):
        declaration = load_declaration(decl_path, root)
    return Scan(root, handlers, regs, declaration, unreadable)


# ---------------------------------------------------------------- the declaration


@dataclass
class DeclCommand:
    command: str
    description: "str | dict | None"
    is_ephemeral: bool
    hidden: bool
    line: int


@dataclass
class DeclList:
    scope: dict
    language_code: str
    commands: list[DeclCommand]
    line: int


@dataclass
class Declaration:
    file: str
    default_language: str
    lists: list[DeclList]
    remove: list[tuple[dict, str]]


def _command_lines(text: str):
    seen: dict[str, list[int]] = defaultdict(list)
    for m in re.finditer(r'"command"\s*:\s*"((?:[^"\\]|\\.)*)"', text):
        seen[m.group(1)].append(text.count("\n", 0, m.start()) + 1)
    cursor: dict[str, int] = defaultdict(int)

    def next_line(name: str) -> int:
        lines = seen.get(name) or [1]
        line = lines[min(cursor[name], len(lines) - 1)]
        cursor[name] += 1
        return line
    return next_line


def parse_language(raw, where: str) -> str:
    if raw is None:
        return ""
    if not isinstance(raw, str) or not LANG_RE.match(raw):
        raise DeclarationError(f"{where}: language_code must be empty or two lowercase letters")
    return raw


def parse_declaration(doc, text: str, file: str) -> Declaration:
    if not isinstance(doc, dict) or doc.get("format") != FORMAT:
        raise DeclarationError(f'{file}: "format" must be "{FORMAT}"')
    default_language = parse_language(doc.get("default_language", "en"), "default_language")
    if not default_language:
        raise DeclarationError("default_language must be two lowercase letters")
    if not isinstance(doc.get("lists"), list):
        raise DeclarationError('"lists" must be an array')
    next_line = _command_lines(text)
    lists: list[DeclList] = []
    for i, raw in enumerate(doc["lists"]):
        where = f"lists[{i}]"
        if not isinstance(raw, dict) or not isinstance(raw.get("commands"), list):
            raise DeclarationError(f"{where}: needs a commands array")
        commands: list[DeclCommand] = []
        for j, item in enumerate(raw["commands"]):
            at = f"{where}.commands[{j}]"
            if not isinstance(item, dict) or not isinstance(item.get("command"), str):
                raise DeclarationError(f"{at}: command must be a string")
            desc = item.get("description")
            hidden = item.get("hidden", False)
            ephemeral = item.get("is_ephemeral", False)
            if not isinstance(hidden, bool) or not isinstance(ephemeral, bool):
                raise DeclarationError(f"{at}: hidden and is_ephemeral must be booleans")
            if isinstance(desc, dict):
                if not desc or not all(LANG_RE.match(k) and k and isinstance(v, str) for k, v in desc.items()):
                    raise DeclarationError(f"{at}: description map must be two-letter language -> text")
            elif not isinstance(desc, str) and not (desc is None and hidden):
                raise DeclarationError(f"{at}: description must be a string or a language -> text map")
            commands.append(DeclCommand(item["command"], desc, ephemeral, hidden, next_line(item["command"])))
        lists.append(DeclList(parse_scope(raw.get("scope"), where), parse_language(raw.get("language_code"), where),
                              commands, commands[0].line if commands else 1))
    remove = []
    for i, raw in enumerate(doc.get("remove", [])):
        if not isinstance(raw, dict):
            raise DeclarationError(f"remove[{i}]: must be an object with scope and language_code")
        remove.append((parse_scope(raw.get("scope"), f"remove[{i}]"), parse_language(raw.get("language_code"),
                                                                                    f"remove[{i}]")))
    keys = [(scope_key(lst.scope), lst.language_code) for lst in lists]
    for k, key in enumerate(keys):
        if key in keys[:k]:
            raise DeclarationError(f"lists[{k}]: repeats the scope and language_code of an earlier list")
    decl = Declaration(file, default_language, lists, remove)
    removed = {(scope_key(s), lang) for s, lang in remove}
    for lst in expand(decl):  # the lists as sent: a description map in a list adds one per language
        if lst.key in removed:
            raise DeclarationError(f"remove: {scope_label(lst.scope)} / {lang_label(lst.language_code)} is both set "
                                   f"in lists (a description map sets its languages too) and removed")
    return decl


def load_declaration(path: str, root: str | None = None) -> Declaration:
    shown = os.path.relpath(path, root).replace("\\", "/") if root else path
    try:
        text = read_text(path)
        doc = json.loads(text)
    except OSError as exc:
        raise DeclarationError(f"cannot read {shown}: {exc}") from exc
    except ValueError as exc:
        raise DeclarationError(f"{shown} is not valid JSON: {exc}") from exc
    try:
        return parse_declaration(doc, text, shown)
    except DeclarationError as exc:
        raise DeclarationError(f"{shown}: {exc}") from exc


@dataclass
class MenuCommand:
    command: str | None
    description: str | None
    line: int
    hidden: bool = False
    is_ephemeral: bool = False
    missing_locale: str = ""         # a language the declaration has no text for (the default text is used)


@dataclass
class MenuList:
    scope: dict | None
    language_code: str | None
    commands: list[MenuCommand]
    source: str                      # code | declaration
    file: str
    line: int

    @property
    def dynamic(self) -> bool:
        return self.scope is None or self.language_code is None

    @property
    def key(self) -> tuple[str, str | None]:
        return scope_key(self.scope), self.language_code

    def visible(self) -> list[MenuCommand]:
        return [c for c in self.commands if not c.hidden]


def _pick(desc, lang: str, default: str) -> tuple[str | None, str]:
    """(text, language that had no text and fell back to the default)."""
    if not isinstance(desc, dict):
        return desc, ""
    if lang in desc:
        return desc[lang], ""
    return desc.get(default) or next(iter(desc.values())), lang


def expand(decl: Declaration) -> list[MenuList]:
    """Declaration lists as the lists Telegram will hold: one per (scope, language_code)."""
    explicit = {(scope_key(lst.scope), lst.language_code) for lst in decl.lists if lst.language_code}
    out: list[MenuList] = []

    def build(lst: DeclList, lang: str) -> MenuList:
        commands = []
        for c in lst.commands:
            text, missing = _pick(c.description, lang or decl.default_language, decl.default_language)
            commands.append(MenuCommand(c.command, text, c.line, c.hidden, c.is_ephemeral, missing))
        return MenuList(lst.scope, lang, commands, "declaration", decl.file, lst.line)

    for lst in decl.lists:
        out.append(build(lst, lst.language_code))
        if lst.language_code:
            continue
        langs: list[str] = []
        for c in lst.commands:
            if isinstance(c.description, dict):
                langs += [k for k in c.description if k != decl.default_language and k not in langs]
        out += [build(lst, lang) for lang in langs if (scope_key(lst.scope), lang) not in explicit]
    return out


# ---------------------------------------------------------------- audit


@dataclass
class Finding:
    code: str
    severity: str
    message: str
    file: str
    line: int
    command: str | None = None
    scope: str | None = None
    language_code: str | None = None


def menu_lists(scan: Scan) -> tuple[list[MenuList], list[MenuList], list[str]]:
    """(every list that is checked on its own, the lists Telegram would hold, notes)."""
    code, notes = [], []
    for reg in scan.registrations:
        if not reg.resolved:
            notes.append(f"{reg.file}:{reg.line} {reg.method}: the command list is built at run time and was not read")
            continue
        code.append(MenuList(reg.scope, reg.language_code,
                             [MenuCommand(e.command, e.description, e.line) for e in reg.commands],
                             "code", reg.file, reg.line))
    declared = expand(scan.declaration) if scan.declaration else []
    taken = {lst.key for lst in declared}
    if scan.declaration:
        taken |= {(scope_key(s), lang) for s, lang in scan.declaration.remove}
    effective = declared + [lst for lst in code if lst.key not in taken]
    return declared + code, effective, notes


def _where(lst: MenuList, command: MenuCommand | None = None) -> tuple[str, int]:
    return lst.file, command.line if command else lst.line


def check_list(lst: MenuList) -> list[Finding]:
    out: list[Finding] = []
    meta = dict(scope=scope_label(lst.scope), language_code=lang_label(lst.language_code))

    def add(code, severity, message, command=None):
        out.append(Finding(code, severity, message, *_where(lst, command), command.command if command else None,
                           **meta))

    first: dict[str, MenuCommand] = {}
    for c in lst.commands:
        if c.command is not None:
            if not NAME_RE.match(c.command):
                add("COMMAND_NAME_INVALID", "error", f"/{c.command}: a command is 1-32 characters, lowercase English "
                    "letters, digits and underscores only", c)
            key = c.command.lower()
            if key in first:
                add("COMMAND_DUPLICATE", "warning", f"/{c.command} is listed twice in this list (first at line "
                    f"{first[key].line})", c)
            first.setdefault(key, c)
        if not c.hidden and c.description is not None and not (c.description.strip()
                                                               and len(c.description) <= DESC_MAX):
            add("DESCRIPTION_LENGTH", "error", f"/{c.command}: description is {len(c.description)} characters; "
                f"Telegram takes 1-{DESC_MAX}", c)
    visible = lst.visible()
    if len(visible) > MAX_COMMANDS:
        add("TOO_MANY_COMMANDS", "error", f"{len(visible)} commands in one list; setMyCommands takes at most "
            f"{MAX_COMMANDS}")
    described = [c for c in visible if c.description and c.command]
    firsts = [c.description.lstrip()[0] for c in described if c.description.strip()]
    upper, lower = sum(ch.isupper() for ch in firsts), sum(ch.islower() for ch in firsts)
    if upper and lower:
        add("DESCRIPTION_STYLE", "info", f"descriptions mix capital and lowercase starts ({upper} vs {lower}); "
            "pick one")
    dotted = sum(c.description.rstrip().endswith(".") for c in described)
    if 0 < dotted < len(described):
        add("DESCRIPTION_STYLE", "info", f"{dotted} of {len(described)} descriptions end with a period; make it "
            "all or none")
    for c in described:
        plain = re.sub(r"\W+", " ", c.description.lower()).strip()
        if plain in {c.command, c.command.replace("_", " ")}:
            add("DESCRIPTION_STYLE", "info", f"/{c.command}: the description only repeats the command name; say "
                "what it does", c)
    return out


def check_locales(lists: list[MenuList]) -> list[Finding]:
    out: list[Finding] = []
    groups: dict[str, list[MenuList]] = defaultdict(list)
    for lst in lists:
        if not lst.dynamic:
            groups[scope_key(lst.scope)].append(lst)
    for group in groups.values():
        if len({lst.language_code for lst in group}) > 1:
            union = {c.command for lst in group for c in lst.visible() if c.command}
            for lst in group:
                missing = sorted(union - {c.command for c in lst.visible()})
                if missing:
                    out.append(Finding(
                        "LOCALE_MISSING", "warning",
                        f"the {lang_label(lst.language_code)} list of scope {scope_label(lst.scope)} lacks "
                        f"{', '.join('/' + m for m in missing)}, which other languages of the same scope list; "
                        "users of this list do not see them (a language list replaces the fallback, it is not "
                        "merged)", *_where(lst), scope=scope_label(lst.scope),
                        language_code=lang_label(lst.language_code)))
    for lst in lists:
        for c in lst.commands:
            if c.missing_locale:
                out.append(Finding(
                    "LOCALE_MISSING", "warning",
                    f"/{c.command} has no '{c.missing_locale}' description; the plan reuses the default text",
                    *_where(lst, c), c.command, scope_label(lst.scope), lang_label(lst.language_code)))
    return out


def resolution_chains(scopes: dict[str, dict]) -> list[tuple[str, list[str]]]:
    """(who sees it, scope keys from narrowest to broadest) for every scope that has a list."""
    def tkey(kind: str) -> str:
        return scope_key({"type": kind})

    members = [tkey("all_group_chats"), tkey("default")]
    admins = [tkey("all_chat_administrators"), *members]
    chains = [("private chats", [tkey("all_private_chats"), tkey("default")]),
              ("group chats", members), ("group administrators", admins)]
    for key, scope in scopes.items():
        kind = scope["type"]
        if kind == "chat":
            chains += [(f"{scope_label(scope)} as a private chat", [key, tkey("all_private_chats"), tkey("default")]),
                       (f"{scope_label(scope)} in a group", [key, *members]),
                       (f"{scope_label(scope)} for group administrators", [key, *admins])]
        elif kind == "chat_administrators":
            chains.append((f"{scope_label(scope)} for group administrators", [key, *admins]))
        elif kind == "chat_member":
            chains.append((f"{scope_label(scope)} in a group", [key, *members]))
    return chains


def check_shadowing(lists: list[MenuList]) -> list[Finding]:
    usable = [lst for lst in lists if not lst.dynamic]
    by_scope: dict[str, dict[str, MenuList]] = defaultdict(dict)
    scopes: dict[str, dict] = {}
    for lst in usable:
        by_scope[scope_key(lst.scope)].setdefault(lst.language_code, lst)
        scopes[scope_key(lst.scope)] = lst.scope
    languages = {lst.language_code for lst in usable} | {""}
    shadows: dict[tuple[int, int], dict] = {}
    for context, chain in resolution_chains(scopes):
        for lang in sorted(languages):
            found = []
            for key in chain:
                lst = by_scope.get(key, {}).get(lang) or by_scope.get(key, {}).get("")
                if lst is not None:
                    found.append(lst)
            if len(found) < 2:
                continue
            shown, hidden = found[0], found[1]
            missing = sorted({c.command for c in hidden.visible() if c.command}
                             - {c.command for c in shown.visible() if c.command})
            if missing:
                entry = shadows.setdefault((id(shown), id(hidden)), {"shown": shown, "hidden": hidden,
                                                                     "missing": missing, "contexts": []})
                entry["contexts"].append(f"{context} ({lang_label(lang)})")
    out = []
    for entry in shadows.values():
        shown, hidden = entry["shown"], entry["hidden"]
        out.append(Finding(
            "SCOPE_SHADOWED", "warning",
            f"{scope_label(shown.scope)} / {lang_label(shown.language_code)} omits "
            f"{', '.join('/' + m for m in entry['missing'])}, which {scope_label(hidden.scope)} / "
            f"{lang_label(hidden.language_code)} ({hidden.file}:{hidden.line}) lists. Telegram uses the first list "
            f"it finds and does not merge, so for {'; '.join(entry['contexts'][:3])} they are not shown; add them to "
            "the narrower list if users there should still see them",
            *_where(shown), scope=scope_label(shown.scope), language_code=lang_label(shown.language_code)))
    return out


def audit_scan(scan: Scan) -> tuple[list[Finding], list[str]]:
    checked, effective, notes = menu_lists(scan)
    findings: list[Finding] = []
    for lst in checked:
        findings += check_list(lst)
    findings += check_locales(effective)
    findings += check_shadowing(effective)

    handlers: dict[str, Handler] = {}
    for h in scan.handlers:
        handlers.setdefault(h.command, h)
    hidden = {c.command.lower() for lst in checked for c in lst.commands if c.hidden and c.command}
    in_menu: dict[str, tuple[MenuList, MenuCommand]] = {}
    for lst in checked:
        for c in lst.visible():
            if c.command:
                in_menu.setdefault(c.command.lower(), (lst, c))
    menu_source = bool(checked)
    for name, handler in sorted(handlers.items()):
        if name in in_menu or name in hidden:
            continue
        hint = ("" if menu_source else "; no menu was found in the code or in bot-ui/commands.json (if it is set "
                "in BotFather, record it there)")
        if name == "start":
            findings.append(Finding("COMMAND_NOT_REGISTERED", "info", "/start has a handler and is not in the menu; "
                                    "Telegram shows the Start button to users who have not written to the bot"
                                    + hint, handler.file, handler.line, name))
        else:
            findings.append(Finding(
                "COMMAND_NOT_REGISTERED", "warning", f"/{name} has a handler but is not in the menu{hint}; "
                "add it, or mark it \"hidden\": true in bot-ui/commands.json if it is meant to stay out",
                handler.file, handler.line, name))
    nothing = "" if handlers else " (no handler was found at all; the scan reads Python and JS/TS only)"
    for name, (lst, c) in sorted(in_menu.items()):
        if name not in handlers:
            findings.append(Finding("COMMAND_NO_HANDLER", "error", f"/{c.command} is in the menu but no handler "
                                    f"was found{nothing}", *_where(lst, c), c.command, scope_label(lst.scope),
                                    lang_label(lst.language_code)))
    for lst in checked:
        for c in lst.commands:
            if c.hidden and c.command and c.command.lower() not in handlers:
                findings.append(Finding("COMMAND_NO_HANDLER", "warning", f"/{c.command} is marked hidden but no "
                                        f"handler was found{nothing}", *_where(lst, c), c.command))
    seen, unique = set(), []
    for f in findings:
        key = (f.code, f.file, f.line, f.command, f.message)
        if key not in seen:
            seen.add(key)
            unique.append(f)
    unique.sort(key=lambda f: (SEVERITY[f.severity], f.file, f.line, f.code, f.command or ""))
    return unique, notes


# ---------------------------------------------------------------- plan


def build_requests(decl: Declaration) -> tuple[list[dict], list[str]]:
    requests, problems = [], []
    for lst in expand(decl):
        visible = lst.visible()
        label = f"{scope_label(lst.scope)} / {lang_label(lst.language_code)}"
        if not visible:
            problems.append(f"{label}: no visible command; list it under \"remove\" to clear it")
            continue
        params: dict = {"commands": [], "scope": lst.scope}
        if lst.language_code:
            params["language_code"] = lst.language_code
        for c in visible:
            item = {"command": c.command, "description": c.description}
            if c.is_ephemeral:
                item["is_ephemeral"] = True
            params["commands"].append(item)
        requests.append({"method": "setMyCommands", "params": params})
        problems += [f"{label}: {f.code} {f.message}" for f in check_list(lst) if f.severity != "info"]
    for scope, lang in decl.remove:
        params = {"scope": scope}
        if lang:
            params["language_code"] = lang
        requests.append({"method": "deleteMyCommands", "params": params})
    return requests, list(dict.fromkeys(problems))


def catalog_problems(requests: list[dict]) -> tuple[list[str], str | None]:
    try:
        from sync_bot_api import load_catalog
        from validate_payload import Validator
        validator = Validator(load_catalog())
    except (ImportError, SystemExit, OSError, ValueError, KeyError) as exc:
        return [], f"catalog check skipped: {exc}"
    problems = []
    for i, req in enumerate(requests):
        problems += [f"request {i} {req['method']}: {e}" for e in validator.check_request(req["method"],
                                                                                         req["params"]).errors]
    return problems, None


# ---------------------------------------------------------------- diff


def _live_commands(raw, where: str) -> list[dict]:
    if isinstance(raw, dict):
        for key in ("commands", "result"):
            if key in raw:
                raw = raw[key]
                break
        else:
            raw = (raw.get("response") or {}).get("result")
    if not isinstance(raw, list) or not all(isinstance(c, dict) and "command" in c for c in raw):
        raise DeclarationError(f"{where}: expected a getMyCommands result, an array of BotCommand objects")
    return raw


def parse_live(doc, scope: dict, language_code: str) -> tuple[dict[tuple[str, str], list[dict]], bool]:
    """({(scope key, language_code): live commands}, whether the file lists every scope and language)."""
    if isinstance(doc, dict) and doc.get("ok") is False:
        raise DeclarationError(f"the saved response is an error: {doc.get('description', doc)}")
    items = doc.get("lists") if isinstance(doc, dict) and "lists" in doc else None
    if items is None and isinstance(doc, list) and doc and not all(isinstance(c, dict) and "command" in c
                                                                   for c in doc):
        items = doc
    if items is None:
        return {(scope_key(scope), language_code): _live_commands(doc, "live json")}, False
    live = {}
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            raise DeclarationError(f"live json lists[{i}]: must be an object")
        s = parse_scope(item.get("scope"), f"live json lists[{i}]")
        lang = parse_language(item.get("language_code"), f"live json lists[{i}]")
        live[(scope_key(s), lang)] = _live_commands(item, f"live json lists[{i}]")
    return live, True


def diff_lists(decl: Declaration, live: dict, complete: bool) -> list[dict]:
    wanted = {}
    for lst in expand(decl):
        wanted[lst.key] = lst
    removing = {(scope_key(s), lang): s for s, lang in decl.remove}
    scopes = {scope_key(lst.scope): lst.scope for lst in wanted.values()} | {scope_key(s): s for s in removing.values()}
    result = []
    for key in sorted(set(wanted) | set(live) | set(removing)):
        if not complete and key not in live:
            continue
        have = live.get(key, [])
        want = [{"command": c.command, "description": c.description, "is_ephemeral": c.is_ephemeral}
                for c in wanted[key].visible()] if key in wanted else []
        scope = scopes.get(key[0]) or json.loads(key[0])
        entry = {"scope": scope, "language_code": key[1], "status": "same", "added": [], "removed": [],
                 "changed": [], "reordered": False}
        if key in wanted:
            have_by = {c["command"]: c for c in have}
            want_by = {c["command"]: c for c in want}
            entry["added"] = [c for c in want if c["command"] not in have_by]
            entry["removed"] = [{"command": c["command"], "description": c.get("description")}
                                for c in have if c["command"] not in want_by]
            entry["changed"] = [{"command": c["command"], "live": have_by[c["command"]].get("description"),
                                 "declared": c["description"]} for c in want if c["command"] in have_by and (
                (have_by[c["command"]].get("description") != c["description"])
                or bool(have_by[c["command"]].get("is_ephemeral", False)) != c["is_ephemeral"])]
            common_live = [c["command"] for c in have if c["command"] in want_by]
            common_want = [c["command"] for c in want if c["command"] in have_by]
            entry["reordered"] = common_live != common_want
            if not have:
                entry["status"] = "new"
            elif entry["added"] or entry["removed"] or entry["changed"] or entry["reordered"]:
                entry["status"] = "changed"
        elif key in removing:
            if have:
                entry["status"] = "to_remove"
                entry["removed"] = [{"command": c["command"], "description": c.get("description")} for c in have]
        elif have:
            entry["status"] = "undeclared"
            entry["removed"] = [{"command": c["command"], "description": c.get("description")} for c in have]
        result.append(entry)
    return result


# ---------------------------------------------------------------- CLI


def _emit(obj) -> None:
    sys.stdout.write(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


def declaration_path(args) -> str | None:
    """--file (as given, else inside the root), or the default bot-ui/commands.json when it exists."""
    if not os.path.isdir(args.root):
        raise DeclarationError(f"--root {args.root} is not a folder")
    if args.file:
        found = next((p for p in (args.file, os.path.join(args.root, args.file)) if os.path.isfile(p)), None)
        if not found:
            raise DeclarationError(f"no declaration at {args.file}")
        return found
    default = os.path.join(args.root, *DECLARATION.split("/"))
    return default if os.path.isfile(default) else None


def required_declaration(args) -> Declaration:
    path = declaration_path(args)
    if not path:
        raise DeclarationError(f"no {DECLARATION} in {args.root}; see `tgui.py commands --help` for the format")
    return load_declaration(path, args.root)


def _scope_arg(raw: str) -> dict:
    if raw.lstrip().startswith("{"):
        try:
            return parse_scope(json.loads(raw), "--scope")
        except ValueError as exc:
            raise DeclarationError(f"--scope is not valid JSON: {exc}") from exc
    return parse_scope({"type": raw}, "--scope")


def cmd_scan(args) -> int:
    scan = scan_project(args.root, declaration_path(args))
    regs = list(scan.registrations)
    if scan.declaration:
        for lst in scan.declaration.lists:
            regs.append(Registration(scan.declaration.file, lst.line, "commands.json", lst.scope, lst.language_code,
                                     [Entry(c.command, c.description if isinstance(c.description, str)
                                            else json.dumps(c.description, ensure_ascii=False), c.line)
                                      for c in lst.commands], True, "declaration"))
    if args.json:
        _emit({"root": scan.root.replace("\\", "/"), "handlers": [asdict(h) for h in scan.handlers],
               "registrations": [asdict(r) for r in regs], "unreadable": scan.unreadable})
        return 0
    print(f"handlers ({len(scan.handlers)})")
    for h in sorted(scan.handlers, key=lambda h: (h.command, h.file, h.line)):
        print(f"  /{h.command:<20} {h.file}:{h.line}  {h.framework}")
    print(f"registrations ({len(regs)})")
    for r in regs:
        scope = scope_label(r.scope)
        shown = "list not readable" if not r.resolved else f"{len(r.commands)} command(s)"
        print(f"  {r.file}:{r.line}  {r.method}  scope={scope}  language={lang_label(r.language_code)}  {shown}")
        for e in r.commands:
            print(f"    /{e.command}  {e.description if e.description is not None else '(not literal)'}  "
                  f"({r.file}:{e.line})")
    if scan.unreadable:
        print("not read: " + ", ".join(scan.unreadable))
    return 0


def cmd_audit(args) -> int:
    scan = scan_project(args.root, declaration_path(args))
    findings, notes = audit_scan(scan)
    counts = {s: sum(f.severity == s for f in findings) for s in SEVERITY}
    if args.json:
        _emit({"root": scan.root.replace("\\", "/"), "summary": counts, "findings": [asdict(f) for f in findings],
               "notes": notes, "handlers": len({h.command for h in scan.handlers}),
               "declaration": scan.declaration.file if scan.declaration else None})
    else:
        for f in findings:
            print(f"{f.file}:{f.line}  {f.severity:<7} {f.code}  {f.message}")
        for note in notes:
            print(f"note: {note}")
        print(f"{len(findings)} finding(s): {counts['error']} error, {counts['warning']} warning, "
              f"{counts['info']} info")
    return 1 if counts["error"] or counts["warning"] else 0


def cmd_plan(args) -> int:
    decl = required_declaration(args)
    requests, problems = build_requests(decl)
    found, skipped = catalog_problems(requests)
    problems += found
    if args.json:
        _emit({"requests": requests, "problems": problems, "notes": [skipped] if skipped else []})
    else:
        _emit(requests)
        for p in problems:
            print(f"problem: {p}", file=sys.stderr)
        if skipped:
            print(f"note: {skipped}", file=sys.stderr)
    return 1 if problems else 0


def cmd_diff(args) -> int:
    decl = required_declaration(args)
    try:
        doc = json.loads(read_text(args.live_json))
    except (OSError, ValueError) as exc:
        raise DeclarationError(f"cannot read {args.live_json}: {exc}") from exc
    live, complete = parse_live(doc, _scope_arg(args.scope), parse_language(args.language_code, "--language-code"))
    lists = diff_lists(decl, live, complete)
    differing = [lst for lst in lists if lst["status"] != "same"]
    summary = {"added": sum(len(x["added"]) for x in lists), "removed": sum(len(x["removed"]) for x in lists),
               "changed": sum(len(x["changed"]) for x in lists), "reordered": sum(x["reordered"] for x in lists)}
    if args.json:
        _emit({"summary": summary, "compared_every_list": complete, "lists": lists})
    else:
        for entry in lists:
            print(f"{scope_label(entry['scope'])} / {lang_label(entry['language_code'])}: {entry['status']}")
            for c in entry["added"]:
                print(f"  + /{c['command']}  {c['description']}")
            for c in entry["removed"]:
                print(f"  - /{c['command']}  {c['description']}")
            for c in entry["changed"]:
                print(f"  ~ /{c['command']}  {c['live']!r} -> {c['declared']!r}")
            if entry["reordered"]:
                print("  ~ the order differs")
        print(f"{summary['added']} added, {summary['removed']} removed, {summary['changed']} changed, "
              f"{summary['reordered']} reordered" + ("" if complete else "; compared only the one saved list"))
    return 1 if differing else 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="tgui.py commands", description="Audit and plan a bot's command menu. "
                                 "Offline; exit 0 ok, 1 findings, 2 usage.")
    sub = ap.add_subparsers(dest="verb", required=True)

    def add(name, help_text, func, file=False):
        p = sub.add_parser(name, help=help_text, description=help_text)
        p.add_argument("--root", default=".", help="the bot project (default: current folder)")
        p.add_argument("--json", action="store_true", help="machine-readable output")
        if file:
            p.add_argument("--file", help=f"declaration (default: {DECLARATION} in the root)")
        p.set_defaults(func=func)
        return p

    add("scan", "find command handlers and menu registrations with file:line", cmd_scan, file=True)
    add("audit", "findings for the menu: names, descriptions, handlers, locales, scope shadowing", cmd_audit,
        file=True)
    add("plan", "the setMyCommands / deleteMyCommands requests that match the declaration (JSON array; "
        "--json adds problems)", cmd_plan, file=True)
    p = add("diff", "declaration against a saved getMyCommands response", cmd_diff, file=True)
    p.add_argument("--live-json", required=True, help="saved getMyCommands response, or {\"lists\": [{scope, "
                   "language_code, result}]} for several lists")
    p.add_argument("--scope", default="default", help="scope of a single saved list: a type or a JSON object")
    p.add_argument("--language-code", default="", help="language of a single saved list (default: fallback)")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except DeclarationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
