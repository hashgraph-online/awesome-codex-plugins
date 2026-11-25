"""Import an existing aiogram 3 bot into a bot-ui project without touching the bot's code.

    py -3 studio/bot-ui.py import --source path/to/bot [--into path/to/bot/bot-ui] [--json]

Deterministic static analysis (Python ast), no network, no model calls. It writes only the new
bot-ui/ folder (staged in a temp folder, validated, then moved into place, like `init`):

* handlers (`@router.message(...)`, `@router.callback_query(...)`, `router.message.register`)
  become screens; commands become entry points; FSM states set with `state.set_state(...)`
  become text inputs (`screen.input`);
* the first message a handler sends is its screen: text (literals, f-strings, module
  constants, `TEXTS["key"]`, `_("...")` with gettext .po / JSON / Fluent catalogs as locales),
  parse mode, media (photo, video, animation, audio, voice, video note, sticker; file_id or URL;
  a local upload becomes a data field to fill with the file_id), custom emoji (`<tg-emoji>`,
  `icon_custom_emoji_id`), keyboard (InlineKeyboardMarkup, ReplyKeyboardMarkup, ForceReply,
  ReplyKeyboardRemove, InlineKeyboardBuilder/ReplyKeyboardBuilder with `adjust`, helper
  functions that return a markup);
* sends in mutually exclusive branches (`if/else`, early `return`) become extra screens and
  the handler a registered handler with one outcome per branch;
* arrows: a button's callback_data -> the handler whose filter matches it (`F.data == ...`,
  `F.data.startswith(...)`, `CallbackData` factories), a reply button -> `F.text == label`;
  the original callback_data is kept in `callbackData`, so the running bot stays compatible;
* everything it cannot decide (computed texts or keyboards, unmatched callbacks, extra
  messages, local uploads, custom emoji eligibility) goes into a short report with file:line
  and the default it took. The agent reads the report, not the code.

Re-import keeps every screen already in the project (`import-map.json` maps source handlers
to IDs) and adds only new handlers; vanished handlers are reported, never deleted.
"""
from __future__ import annotations

import ast
import json
import os
import re
import shutil
import uuid
from dataclasses import dataclass, field
from typing import Any

from . import SCHEMA_VERSION
from .project import canonical_json, check_id, open_snapshot, replace_dir
from .validate import validate

SKIP_DIRS = {".git", ".venv", "venv", "env", "node_modules", "__pycache__", "bot-ui", ".bot-ui", "tests", "test"}
SEND_TEXT = {"answer", "reply", "send_message", "edit_text", "edit_message_text"}
SEND_MEDIA = {"photo", "video", "animation", "audio", "voice", "video_note", "sticker"}
EDIT_METHODS = {"edit_text", "edit_message_text", "edit_caption", "edit_media", "edit_message_caption",
                "edit_message_media"}
I18N_FUNCS = {"_", "gettext", "__", "t", "tr", "i18n", "get", "lazy_gettext"}
ERROR_WORDS = re.compile(r"(ошиб|не удалось|не получилось|failed|error|❌|⚠️|помилк)", re.I)
EMPTY_WORDS = re.compile(r"(пуст|ничего нет|nothing|empty|порожн)", re.I)
EMOJI_ID_ATTR = re.compile(r"""emoji-id=\\?["'](\d{1,20})""")
LONG_ID = re.compile(r"^\d{16,20}$")  # custom emoji ids are 19 digits today
ID_NAMES = re.compile(r"emoji|icon|premium", re.I)


@dataclass
class Text:
    by_locale: dict[str, str] | None  # None = computed at run time
    fields: list[str] = field(default_factory=list)
    source: str = "literal"


@dataclass
class Button:
    text: Text
    callback: str | None = None
    callback_prefix: str | None = None  # CallbackData factory prefix
    callback_eq: dict[str, Any] = field(default_factory=dict)
    url: str | None = None
    icon: str | None = None
    style: str | None = None
    dynamic: bool = False
    line: int = 0


@dataclass
class Keyboard:
    type: str
    rows: list[list[Button]]
    dynamic: bool = False
    placeholder: Text | None = None


@dataclass
class Send:
    method: str
    text: Text | None
    fmt: str
    media: dict | None
    keyboard: Keyboard | None
    edit: bool
    line: int
    branch: tuple
    local_upload: str | None = None


@dataclass
class Handler:
    file: str
    name: str
    line: int
    kind: str  # message | callback
    filters: list[dict]
    sends: list[Send]
    toasts: list[tuple[Text, int]]
    sets_state: list[str]
    branches: list[list[Send]] = field(default_factory=list)
    screen_id: str = ""


class Report:
    def __init__(self) -> None:
        self.items: list[dict] = []

    def add(self, kind: str, file: str, line: int, what: str, default: str) -> None:
        self.items.append({"kind": kind, "file": file, "line": line, "what": what, "default": default})


# ---------------------------------------------------------------------------- catalogs

def _po_unquote(s: str) -> str:
    try:
        return json.loads(s) if s.startswith('"') else s
    except json.JSONDecodeError:  # a broken catalog line: keep its text, never stop the import
        return s.strip('"')


def load_catalogs(source: str) -> dict[str, dict[str, str]]:
    """{locale: {key or msgid: text}} from gettext .po, JSON and Fluent .ftl files."""
    cats: dict[str, dict[str, str]] = {}
    for dirpath, dirnames, filenames in os.walk(source):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        rel_parts = os.path.relpath(dirpath, source).replace(os.sep, "/").split("/")
        for name in filenames:
            path = os.path.join(dirpath, name)
            lang = None
            if name.endswith(".po") and "LC_MESSAGES" in rel_parts:
                lang = rel_parts[rel_parts.index("LC_MESSAGES") - 1]
            elif name.endswith((".json", ".ftl")) and any(p in ("locales", "locale", "i18n", "lang", "translations")
                                                          for p in rel_parts):
                stem = os.path.splitext(name)[0]
                lang = stem if re.fullmatch(r"[a-z]{2,3}(-[a-z0-9]+)?", stem) else rel_parts[-1]
            if not lang or not re.fullmatch(r"[a-z]{2,3}(_[A-Za-z]+|-[a-z0-9]+)?", lang):
                continue
            lang = lang.split("_")[0].split("-")[0]
            try:
                with open(path, encoding="utf-8") as fh:
                    raw = fh.read()
            except (OSError, UnicodeDecodeError):
                continue
            target = cats.setdefault(lang, {})
            if name.endswith(".po"):
                target.update(_parse_po(raw))
            elif name.endswith(".json"):
                try:
                    _flatten(json.loads(raw), "", target)
                except json.JSONDecodeError:
                    pass
            else:
                target.update(_parse_ftl(raw))
    return cats


def _parse_po(raw: str) -> dict[str, str]:
    out, cur, key = {}, {"msgid": "", "msgstr": ""}, None
    for line in raw.splitlines() + [""]:
        line = line.strip()
        if line.startswith("msgid "):
            if cur["msgid"] and cur["msgstr"]:
                out[cur["msgid"]] = cur["msgstr"]
            cur, key = {"msgid": _po_unquote(line[6:]), "msgstr": ""}, "msgid"
        elif line.startswith("msgstr "):
            cur["msgstr"], key = _po_unquote(line[7:]), "msgstr"
        elif line.startswith('"') and key:
            cur[key] += _po_unquote(line)
        elif not line and cur["msgid"] and cur["msgstr"]:
            out[cur["msgid"]] = cur["msgstr"]
            cur, key = {"msgid": "", "msgstr": ""}, None
    return out


def _parse_ftl(raw: str) -> dict[str, str]:
    out, key = {}, None
    for line in raw.splitlines():
        m = re.match(r"^([a-zA-Z][\w-]*)\s*=\s*(.*)$", line)
        if m:
            key = m.group(1)
            out[key] = m.group(2)
        elif key and line.startswith((" ", "\t")) and line.strip():
            out[key] = (out[key] + "\n" + line.strip()).strip()
        else:
            key = None
    return {k: re.sub(r"\{\s*\$([\w-]+)\s*\}", r"{\1}", v) for k, v in out.items()}


def _flatten(obj: Any, prefix: str, out: dict) -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            _flatten(v, f"{prefix}.{k}" if prefix else str(k), out)
    elif isinstance(obj, str):
        out[prefix] = obj


# ---------------------------------------------------------------------------- AST helpers

def _escape_braces(s: str) -> str:
    return s.replace("{", "{{").replace("}", "}}")


def _dotted(node: ast.AST) -> str | None:
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return ".".join(reversed(parts))
    return None


def _field_name(expr: ast.AST, n: int) -> str:
    d = _dotted(expr)
    if d:
        parts = [p for p in d.split(".") if p not in ("message", "callback", "query", "call", "cq", "c", "m", "self", "event")]
        name = ".".join(parts[-2:]) if parts else d.split(".")[-1]
    elif isinstance(expr, ast.Call) and _dotted(expr.func):
        name = _dotted(expr.func).split(".")[-1]  # type: ignore[union-attr]
    else:
        name = f"value{n}"
    name = re.sub(r"[^a-z0-9_.-]+", "_", name.lower()).strip("._-") or f"value{n}"
    return name


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Call):
        node = node.func
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Name):
        return node.id
    return ""


def _kw(call: ast.Call, name: str) -> ast.AST | None:
    return next((k.value for k in call.keywords if k.arg == name), None)


def _const(node: ast.AST | None) -> Any:
    return node.value if isinstance(node, ast.Constant) else None


class Module:
    def __init__(self, rel: str, tree: ast.Module) -> None:
        self.rel, self.tree = rel, tree
        self.consts: dict[str, ast.AST] = {}
        self.functions: dict[str, ast.AST] = {}
        self.callback_classes: dict[str, str] = {}   # class name -> prefix
        self.state_groups: set[str] = set()
        for node in tree.body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                self.consts[node.targets[0].id] = node.value
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.value is not None:
                self.consts[node.target.id] = node.value
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.functions[node.name] = node
            elif isinstance(node, ast.ClassDef):
                bases = {_call_name(b) for b in node.bases}
                if "CallbackData" in bases:
                    prefix = next((_const(k.value) for k in node.keywords if k.arg == "prefix"), node.name.lower())
                    self.callback_classes[node.name] = prefix
                if "StatesGroup" in bases:
                    self.state_groups.add(node.name)


class Analyzer:
    def __init__(self, source: str, catalogs: dict[str, dict[str, str]], report: Report) -> None:
        self.source, self.catalogs, self.report = source, catalogs, report
        self.modules: list[Module] = []
        self.handlers: list[Handler] = []
        self.default_parse_mode: str | None = None
        self.uses_widgets = False
        self._cur_fn: ast.AST | None = None

    # ---------------------------------------------------------------- loading
    def load(self) -> None:
        for dirpath, dirnames, filenames in os.walk(self.source):
            dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS and not d.startswith("."))
            for name in sorted(filenames):
                if not name.endswith(".py"):
                    continue
                path = os.path.join(dirpath, name)
                rel = os.path.relpath(path, self.source).replace(os.sep, "/")
                try:
                    with open(path, encoding="utf-8") as fh:
                        tree = ast.parse(fh.read(), filename=rel)
                except (SyntaxError, UnicodeDecodeError) as err:
                    self.report.add("skipped", rel, 0, f"not parsed: {err}", "file ignored")
                    continue
                self.modules.append(Module(rel, tree))
        for mod in self.modules:
            for node in ast.walk(mod.tree):
                if isinstance(node, ast.Call) and _call_name(node) == "DefaultBotProperties":
                    pm = self._parse_mode(_kw(node, "parse_mode"))
                    if pm:
                        self.default_parse_mode = pm
                if isinstance(node, ast.Call) and _call_name(node) in ("send_widget", "SendWidget"):
                    self.uses_widgets = True
        self.callback_classes = {k: v for m in self.modules for k, v in m.callback_classes.items()}
        self.state_groups = {g for m in self.modules for g in m.state_groups}
        for mod in self.modules:
            self._handlers_in(mod)

    def _function(self, mod: Module, name: str) -> tuple[Module, ast.AST] | None:
        if name in mod.functions:
            return mod, mod.functions[name]
        for m in self.modules:
            if name in m.functions:
                return m, m.functions[name]
        return None

    def _const_of(self, mod: Module, name: str) -> ast.AST | None:
        if name in mod.consts:
            return mod.consts[name]
        for m in self.modules:
            if name in m.consts:
                return m.consts[name]
        return None

    # ---------------------------------------------------------------- handlers
    def _handlers_in(self, mod: Module) -> None:
        registered: dict[str, list[tuple[str, list[ast.AST]]]] = {}
        for node in ast.walk(mod.tree):
            if isinstance(node, ast.Call) and _call_name(node) == "register" and isinstance(node.func, ast.Attribute) \
                    and isinstance(node.func.value, ast.Attribute) and node.func.value.attr in ("message", "callback_query") \
                    and node.args and isinstance(node.args[0], ast.Name):
                registered.setdefault(node.args[0].id, []).append(
                    (node.func.value.attr, list(node.args[1:]) + [k.value for k in node.keywords]))
        for fn in mod.functions.values():
            kinds = []
            for dec in fn.decorator_list:  # type: ignore[attr-defined]
                if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute) and dec.func.attr in ("message", "callback_query"):
                    kinds.append((dec.func.attr, list(dec.args) + [k.value for k in dec.keywords]))
            kinds += registered.get(fn.name, [])  # type: ignore[attr-defined]
            for kind, args in kinds:
                self._handler(mod, fn, kind, args)

    def _handler(self, mod: Module, fn: ast.AST, kind: str, args: list[ast.AST]) -> None:
        filters = []
        for a in args:
            filters += self._filters(a)
        h = Handler(file=mod.rel, name=fn.name, line=fn.lineno,  # type: ignore[attr-defined]
                    kind="callback" if kind == "callback_query" else "message", filters=filters, sends=[], toasts=[],
                    sets_state=[])
        self._cur_fn = fn
        self._walk_body(mod, fn, fn.body, (), h, {})  # type: ignore[attr-defined]
        h.branches = _exclusive_groups(h.sends)
        self.handlers.append(h)

    def _filters(self, node: ast.AST) -> list[dict]:
        if isinstance(node, ast.Call):
            name = _call_name(node)
            if name == "CommandStart":
                deep = _const(_kw(node, "deep_link")) is True
                return [{"kind": "command", "value": "start", "deepLink": deep}]
            if name == "Command":
                vals = [_const(a) for a in node.args]
                cmds = _kw(node, "commands")
                if isinstance(cmds, (ast.List, ast.Tuple)):
                    vals += [_const(e) for e in cmds.elts]
                return [{"kind": "command", "value": str(v).lstrip("/")} for v in vals if isinstance(v, str)]
            if name == "StateFilter":
                return [{"kind": "state", "value": _dotted(a)} for a in node.args if _dotted(a)]
            if name == "filter" and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) \
                    and node.func.value.id in self.callback_classes:
                eq = {}
                for a in node.args:
                    if isinstance(a, ast.Compare) and isinstance(a.left, ast.Attribute) and len(a.ops) == 1 \
                            and isinstance(a.ops[0], ast.Eq):
                        eq[a.left.attr] = _const(a.comparators[0])
                return [{"kind": "callback-class", "value": self.callback_classes[node.func.value.id], "eq": eq}]
            if name == "startswith" and isinstance(node.func, ast.Attribute) and node.args:
                return [{"kind": "callback-prefix", "value": _const(node.args[0])}]
            if name == "in_" and isinstance(node.func, ast.Attribute) and node.args:
                seq = node.args[0]
                attr = node.func.value.attr if isinstance(node.func.value, ast.Attribute) else "data"
                if isinstance(seq, (ast.List, ast.Tuple, ast.Set)):
                    k = "callback" if attr == "data" else "text"
                    return [{"kind": k, "value": _const(e)} for e in seq.elts if isinstance(_const(e), str)]
        if isinstance(node, ast.Compare) and len(node.ops) == 1 and isinstance(node.ops[0], ast.Eq) \
                and isinstance(node.left, ast.Attribute) and node.left.attr in ("data", "text"):
            v = _const(node.comparators[0])
            if isinstance(v, str):
                return [{"kind": "callback" if node.left.attr == "data" else "text", "value": v}]
        if isinstance(node, ast.Attribute) and _dotted(node) and _dotted(node).split(".")[0] in self.state_groups:
            return [{"kind": "state", "value": _dotted(node)}]
        if isinstance(node, ast.BoolOp):
            return [f for v in node.values for f in self._filters(v)]
        return []

    def _walk_body(self, mod: Module, fn: ast.AST, body: list[ast.stmt], branch: tuple, h: Handler,
                   local: dict[str, ast.AST]) -> None:
        for i, stmt in enumerate(body):
            if isinstance(stmt, ast.If):
                self._walk_body(mod, fn, stmt.body, branch + ((id(stmt), "body"),), h, dict(local))
                if stmt.orelse:
                    self._walk_body(mod, fn, stmt.orelse, branch + ((id(stmt), "else"),), h, dict(local))
                elif _ends_with_return(stmt.body):
                    # code after `if ...: ...; return` runs only when the test is false
                    self._walk_body(mod, fn, body[i + 1:], branch + ((id(stmt), "else"),), h, dict(local))
                    return
                continue
            if isinstance(stmt, (ast.For, ast.AsyncFor, ast.While, ast.With, ast.AsyncWith, ast.Try)):
                inner = list(getattr(stmt, "body", []))
                for hnd in getattr(stmt, "handlers", []):
                    inner += hnd.body
                self._walk_body(mod, fn, inner, branch, h, local)
                continue
            if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
                local[stmt.targets[0].id] = stmt.value
            for node in ast.walk(stmt):
                if isinstance(node, ast.Call):
                    self._call(mod, node, branch, h, local)

    def _call(self, mod: Module, node: ast.Call, branch: tuple, h: Handler, local: dict) -> None:
        name = _call_name(node)
        if name == "set_state" and node.args and _dotted(node.args[0]):
            h.sets_state.append(_dotted(node.args[0]))  # type: ignore[arg-type]
            return
        if name == "answer" and isinstance(node.func, ast.Attribute):
            owner = _dotted(node.func.value) or ""
            last = owner.split(".")[-1]
            if h.kind == "callback" and last in ("callback", "query", "call", "cq", "c", "callback_query"):
                txt = node.args[0] if node.args else _kw(node, "text")
                if txt is not None:
                    h.toasts.append((self.text(mod, txt, local), node.lineno))
                return
        media_type = None
        for t in SEND_MEDIA:
            if name in (f"answer_{t}", f"send_{t}", f"reply_{t}"):
                media_type = t
        if name in ("edit_media", "edit_message_media"):
            media_type = "edit"
        if media_type is None and name not in SEND_TEXT and name not in ("edit_caption", "edit_message_caption"):
            return
        edit = name in EDIT_METHODS
        text_node = None
        if media_type is None:
            text_node = _kw(node, "text") or _kw(node, "caption")
            if text_node is None and node.args:
                text_node = node.args[1] if name == "send_message" and len(node.args) > 1 else node.args[0]
        else:
            text_node = _kw(node, "caption")
        pm = self._parse_mode(_kw(node, "parse_mode")) or self.default_parse_mode
        text = self.text(mod, text_node, local) if text_node is not None else None
        fmt = {"HTML": "regular.html", "MarkdownV2": "regular.markdownv2"}.get(pm or "", "regular.plain")
        if text and text.by_locale and any("<tg-emoji" in t for t in text.by_locale.values()):
            fmt = "regular.html"
        media, upload = None, None
        if media_type == "edit":
            m = _kw(node, "media") or (node.args[0] if node.args else None)
            if isinstance(m, ast.Call) and _call_name(m).startswith("InputMedia"):
                media_type = _call_name(m)[len("InputMedia"):].lower()
                media_type = {"livephoto": "photo"}.get(media_type, media_type)
                text_node = _kw(m, "caption")
                text = self.text(mod, text_node, local) if text_node is not None else None
                src = _kw(m, "media") or (m.args[0] if m.args else None)
            else:
                media_type, src = None, None
                self.report.add("computed", mod.rel, node.lineno, "edit_media with a computed media object",
                                "the screen keeps its text only")
        else:
            src = _kw(node, media_type) if media_type else None
            if media_type and src is None and node.args:
                src = node.args[1] if name.startswith("send_") and len(node.args) > 1 else node.args[0]
        if media_type in SEND_MEDIA:
            media, upload = self.media(mod, media_type, src, local, node.lineno, h)
        kb_node = _kw(node, "reply_markup")
        keyboard = self.keyboard(mod, kb_node, local, node.lineno) if kb_node is not None else None
        h.sends.append(Send(method=name, text=text, fmt=fmt, media=media, keyboard=keyboard, edit=edit,
                            line=node.lineno, branch=branch, local_upload=upload))

    def _parse_mode(self, node: ast.AST | None) -> str | None:
        if node is None:
            return None
        v = _const(node)
        if isinstance(v, str):
            return {"html": "HTML", "markdownv2": "MarkdownV2", "markdown": "MarkdownV2"}.get(v.lower())
        d = _dotted(node) or ""
        if d.endswith("HTML"):
            return "HTML"
        if d.endswith(("MARKDOWN_V2", "MarkdownV2", "MARKDOWN")):
            return "MarkdownV2"
        return None

    # ---------------------------------------------------------------- values
    def text(self, mod: Module, node: ast.AST | None, local: dict, depth: int = 0) -> Text:
        if node is None or depth > 6:
            return Text(None, source="computed")
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return Text({"*": _escape_braces(node.value)})
        if isinstance(node, ast.JoinedStr):
            out, fields = [], []
            for part in node.values:
                if isinstance(part, ast.Constant):
                    out.append(_escape_braces(str(part.value)))
                elif isinstance(part, ast.FormattedValue):
                    f = _field_name(part.value, len(fields) + 1)
                    fields.append(f)
                    out.append("{" + f + "}")
            return Text({"*": "".join(out)}, fields=fields, source="f-string")
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            a, b = self.text(mod, node.left, local, depth + 1), self.text(mod, node.right, local, depth + 1)
            if a.by_locale and b.by_locale and set(a.by_locale) == set(b.by_locale) == {"*"}:
                return Text({"*": a.by_locale["*"] + b.by_locale["*"]}, fields=a.fields + b.fields, source="concat")
            return Text(None, source="computed")
        if isinstance(node, ast.Call):
            fname = _call_name(node)
            if fname == "format" and isinstance(node.func, ast.Attribute):
                base = self.text(mod, node.func.value, local, depth + 1)
                if base.by_locale:
                    names = [k.arg for k in node.keywords if k.arg]
                    return Text(base.by_locale, fields=base.fields + names, source="format")
            if fname in I18N_FUNCS and node.args and isinstance(_const(node.args[0]), str):
                return self._i18n(_const(node.args[0]), node)
            if fname in ("str", "strip") and node.args:
                return self.text(mod, node.args[0], local, depth + 1)
        if isinstance(node, ast.Name):
            target = local.get(node.id) or self._const_of(mod, node.id)
            if target is not None and target is not node:
                return self.text(mod, target, local, depth + 1)
        if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name):
            container = self._const_of(mod, node.value.id)
            key = _const(node.slice)
            if isinstance(container, ast.Dict) and key is not None:
                for k, v in zip(container.keys, container.values):
                    if _const(k) == key:
                        return self.text(mod, v, local, depth + 1)
        return Text(None, source="computed")

    def _i18n(self, key: str, node: ast.AST) -> Text:
        by = {lang: cat[key] for lang, cat in self.catalogs.items() if key in cat}
        fields = sorted({m for t in by.values() for m in re.findall(r"\{([a-z0-9_.-]+)\}", t)})
        if all(k.isidentifier() and "." in k or "-" in k for k in [key]) and by:
            return Text(by, fields=fields, source="i18n")  # a catalog key such as "menu.title"
        # gettext: the msgid is the text in the source language, catalogs add the others
        return Text({"*": _escape_braces(key), **by}, fields=fields, source="i18n")

    def media(self, mod: Module, mtype: str, src: ast.AST | None, local: dict, line: int, h: Handler):
        v = _const(src)
        if isinstance(v, str):
            if v.startswith("https://"):
                return {"type": mtype, "file": {"url": v}}, None
            if re.fullmatch(r"[A-Za-z0-9_-]{8,}", v):
                return {"type": mtype, "file": {"fileId": v}}, None
        if isinstance(src, ast.Call) and _call_name(src) in ("FSInputFile", "InputFile", "BufferedInputFile", "URLInputFile"):
            arg = _const(src.args[0]) if src.args else None
            if _call_name(src) == "URLInputFile" and isinstance(arg, str):
                return {"type": mtype, "file": {"url": arg}}, None
            return {"type": mtype, "file": {"field": "__upload__"}}, str(arg or "local file")
        if isinstance(src, ast.Subscript) and isinstance(src.value, ast.Name):
            container = self._const_of(mod, src.value.id)
            key = _const(src.slice)
            if isinstance(container, ast.Dict):
                for k, val in zip(container.keys, container.values):
                    if _const(k) == key:
                        return self.media(mod, mtype, val, local, line, h)
        if isinstance(src, ast.Name) and (local.get(src.id) or self._const_of(mod, src.id)) is not None:
            return self.media(mod, mtype, local.get(src.id) or self._const_of(mod, src.id), local, line, h)
        return {"type": mtype, "file": {"field": "__computed__"}}, None

    def keyboard(self, mod: Module, node: ast.AST | None, local: dict, line: int, depth: int = 0,
                 fn: ast.AST | None = None) -> Keyboard | None:
        if node is None or depth > 6:
            return None
        if isinstance(node, ast.Name):
            target = local.get(node.id) or self._const_of(mod, node.id)
            return self.keyboard(mod, target, local, line, depth + 1, fn) if target is not None else \
                Keyboard("inline", [], dynamic=True)
        if not isinstance(node, ast.Call):
            return Keyboard("inline", [], dynamic=True)
        name = _call_name(node)
        if name == "InlineKeyboardMarkup":
            rows, dyn = self._rows(mod, _kw(node, "inline_keyboard"), local)
            return Keyboard("inline", rows, dynamic=dyn)
        if name == "ReplyKeyboardMarkup":
            rows, dyn = self._rows(mod, _kw(node, "keyboard"), local)
            ph = _kw(node, "input_field_placeholder")
            return Keyboard("reply", rows, dynamic=dyn, placeholder=self.text(mod, ph, local) if ph is not None else None)
        if name == "ForceReply":
            ph = _kw(node, "input_field_placeholder")
            return Keyboard("force_reply", [], placeholder=self.text(mod, ph, local) if ph is not None else None)
        if name == "ReplyKeyboardRemove":
            return Keyboard("remove", [])
        if name == "as_markup" and isinstance(node.func, ast.Attribute):
            return self._builder_in(mod, fn or self._cur_fn, node.func.value)
        found = self._function(mod, name)
        if found:
            fmod, fn = found
            flocal: dict = {}
            for stmt in ast.walk(fn):
                if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
                    flocal[stmt.targets[0].id] = stmt.value
            rets = [n.value for n in ast.walk(fn) if isinstance(n, ast.Return) and n.value is not None]
            if rets:
                return self.keyboard(fmod, rets[-1], flocal, line, depth + 1, fn)
        return Keyboard("inline", [], dynamic=True)

    def _builder_in(self, mod: Module, fn: ast.AST, obj: ast.AST) -> Keyboard:
        """InlineKeyboardBuilder / ReplyKeyboardBuilder: .button(...), .row(...), .add(...), .adjust(...)."""
        var = _dotted(obj)
        ktype, buttons, sizes, explicit_rows, dynamic = "inline", [], None, [], False
        for node in ast.walk(fn):
            if isinstance(node, ast.Assign) and _dotted(node.targets[0]) == var and isinstance(node.value, ast.Call) \
                    and _call_name(node.value) == "ReplyKeyboardBuilder":
                ktype = "reply"
            if isinstance(node, (ast.For, ast.AsyncFor, ast.ListComp)):
                for inner in ast.walk(node):
                    if isinstance(inner, ast.Call) and isinstance(inner.func, ast.Attribute) and \
                            _dotted(inner.func.value) == var and inner.func.attr in ("button", "add", "row"):
                        dynamic = True
        loop_calls = {id(n) for loop in ast.walk(fn) if isinstance(loop, (ast.For, ast.AsyncFor))
                      for n in ast.walk(loop)}
        for node in ast.walk(fn):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and _dotted(node.func.value) == var):
                continue
            if id(node) in loop_calls:
                continue
            if node.func.attr == "button":
                buttons.append(self._button(mod, node, {}))
            elif node.func.attr in ("add", "row"):
                row = [self._button(mod, a, {}) for a in node.args if isinstance(a, ast.Call)]
                if node.func.attr == "row":
                    explicit_rows.append(row)
                else:
                    buttons += row
            elif node.func.attr == "adjust":
                sizes = [int(_const(a)) for a in node.args if isinstance(_const(a), int)]
        buttons.sort(key=lambda b: b.line)
        rows = explicit_rows + _adjust(buttons, sizes)
        return Keyboard(ktype, rows, dynamic=dynamic)

    def _rows(self, mod: Module, node: ast.AST | None, local: dict) -> tuple[list[list[Button]], bool]:
        """Static rows, and whether some rows or buttons are built at run time (loops, comprehensions)."""
        if isinstance(node, ast.Name):
            node = local.get(node.id) or self._const_of(mod, node.id)
        if not isinstance(node, (ast.List, ast.Tuple)):
            return [], node is not None
        rows, dynamic = [], False
        for r in node.elts:
            if isinstance(r, ast.Name):
                r = local.get(r.id) or self._const_of(mod, r.id) or r
            if isinstance(r, (ast.List, ast.Tuple)):
                row = []
                for b in r.elts:
                    if isinstance(b, ast.Call):
                        row.append(self._button(mod, b, local))
                    else:
                        dynamic = True
                rows.append(row)
            else:
                dynamic = True
        return [r for r in rows if r], dynamic

    def _button(self, mod: Module, node: ast.Call, local: dict) -> Button:
        text_node = _kw(node, "text") or (node.args[0] if node.args else None)
        b = Button(text=self.text(mod, text_node, local), line=node.lineno)
        cb = _kw(node, "callback_data")
        if cb is not None:
            v = _const(cb)
            if isinstance(v, str):
                b.callback = v
            elif isinstance(cb, ast.Call) and _call_name(cb) == "pack" and isinstance(cb.func, ast.Attribute) \
                    and isinstance(cb.func.value, ast.Call) and _call_name(cb.func.value) in self.callback_classes:
                factory = cb.func.value
                b.callback_prefix = self.callback_classes[_call_name(factory)]
                b.callback_eq = {k.arg: _const(k.value) for k in factory.keywords if k.arg}
                b.dynamic = any(not isinstance(k.value, ast.Constant) for k in factory.keywords)
                if not b.dynamic:
                    b.callback = b.callback_prefix + "".join(f":{_const(k.value)}" for k in factory.keywords)
            else:
                b.dynamic = True
        url = _const(_kw(node, "url"))
        if isinstance(url, str):
            b.url = url
        icon = _const(_kw(node, "icon_custom_emoji_id"))
        if isinstance(icon, str):
            b.icon = icon
        style = _const(_kw(node, "style"))
        if style in ("primary", "success", "danger"):
            b.style = style
        return b


def custom_emoji_ids(an: "Analyzer") -> dict[str, str]:
    """Custom emoji ids anywhere in the bot ({id: file:line}), not only on imported screens:
    <tg-emoji emoji-id> in any string or catalog, icon_custom_emoji_id= / custom_emoji_id=,
    and long digit strings in constants, dicts or classes named like emoji/icon maps."""
    out: dict[str, str] = {}

    def add(cid: str, where: str) -> None:
        if re.fullmatch(r"\d{1,20}", cid):
            out.setdefault(cid, where)

    def digits_in(node: ast.AST, rel: str) -> None:
        for n in ast.walk(node):
            if isinstance(n, ast.Constant) and isinstance(n.value, str) and LONG_ID.match(n.value):
                add(n.value, f"{rel}:{n.lineno}")

    for mod in an.modules:
        for node in ast.walk(mod.tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                for m in EMOJI_ID_ATTR.finditer(node.value):
                    add(m.group(1), f"{mod.rel}:{node.lineno}")
            elif isinstance(node, ast.keyword) and node.arg in ("icon_custom_emoji_id", "custom_emoji_id"):
                v = _const(node.value)
                if isinstance(v, str):
                    add(v, f"{mod.rel}:{node.value.lineno}")
            elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                names = [t.id if isinstance(t, ast.Name) else t.attr if isinstance(t, ast.Attribute) else "" for t in targets]
                if node.value is not None and any(ID_NAMES.search(n) for n in names):
                    digits_in(node.value, mod.rel)
            elif isinstance(node, ast.ClassDef) and ID_NAMES.search(node.name):
                digits_in(node, mod.rel)
    for loc, cat in sorted(an.catalogs.items()):
        for key, text in cat.items():
            for m in EMOJI_ID_ATTR.finditer(text or ""):
                add(m.group(1), f"catalog {loc}: {key}")
    return dict(sorted(out.items()))


def _adjust(buttons: list[Button], sizes: list[int] | None) -> list[list[Button]]:
    if not buttons:
        return []
    if not sizes:
        return [[b] for b in buttons]
    rows, i, k = [], 0, 0
    while i < len(buttons):
        n = sizes[min(k, len(sizes) - 1)]
        rows.append(buttons[i:i + n])
        i += n
        k += 1
    return rows


def _ends_with_return(body: list[ast.stmt]) -> bool:
    return bool(body) and isinstance(body[-1], (ast.Return, ast.Raise))


def _exclusive(a: tuple, b: tuple) -> bool:
    for (na, sa), (nb, sb) in zip(a, b):
        if na != nb:
            return False
        if sa != sb:
            return True
    return False


def _exclusive_groups(sends: list[Send]) -> list[list[Send]]:
    """Groups of sends that run together; groups are mutually exclusive branches."""
    groups: list[list[Send]] = []
    for s in sends:
        for g in groups:
            if not _exclusive(g[0].branch, s.branch):
                g.append(s)
                break
        else:
            groups.append([s])
    return groups


# ---------------------------------------------------------------------------- building

class Builder:
    def __init__(self, an: Analyzer, report: Report, project_id: str, id_map: dict[str, str]) -> None:
        self.an, self.report, self.project_id = an, report, project_id
        self.id_map = dict(id_map)
        self.fields: dict[str, dict] = {}
        self.handlers: dict[str, dict] = {}
        self.screens: dict[str, dict] = {}
        self.locales: list[str] = []
        self.default = "en"
        self.custom_emoji = False

    def run(self) -> dict:
        an = self.an
        cats = an.catalogs
        source_text = " ".join(s.text.by_locale["*"] for h in an.handlers for s in h.sends
                               if s.text and s.text.by_locale and "*" in s.text.by_locale)
        cyr, lat = len(re.findall(r"[а-яёіїєґ]", source_text, re.I)), len(re.findall(r"[a-z]", source_text, re.I))
        self.default = ("uk" if re.search(r"[іїєґ]", source_text, re.I) else "ru") if cyr > lat else "en"
        self.locales = [self.default] + sorted(l for l in cats if l != self.default)
        taken = set(self.id_map.values())
        for h in an.handlers:
            key = f"{h.file}::{h.name}"
            if key in self.id_map:
                h.screen_id = self.id_map[key]
                continue
            h.screen_id = self._new_id(h, taken)
            taken.add(h.screen_id)
            self.id_map[key] = h.screen_id
        for h in an.handlers:
            self._screens_of(h)
        self._wire()
        return self.project()

    def _new_id(self, h: Handler, taken: set[str]) -> str:
        mod = os.path.splitext(os.path.basename(h.file))[0].lower()
        mod = "main" if mod in ("__init__", "bot", "main", "app", "handlers") else mod
        name = re.sub(r"^(cmd|command|on|handle|handler|cb|callback|show|send|process|get)_", "", h.name.lower())
        if name.startswith(mod + "_"):
            name = name[len(mod) + 1:]
        seg = lambda s: re.sub(r"[^a-z0-9_-]+", "_", s).strip("_-") or "screen"  # noqa: E731
        base = f"{seg(mod)}.{seg(name)}"[:60]
        if check_id(base):
            base = f"screen.{seg(h.name.lower())}"[:60]
        if base in taken:
            alt = f"{seg(mod)}.{seg(h.name.lower())}"[:60]
            base = alt if alt not in taken and not check_id(alt) else base
        out, n = base, 2
        while out in taken:
            out, n = f"{base}-{n}", n + 1
        return out

    def _loc(self, t: Text | None, file: str, line: int, what: str) -> dict | None:
        if t is None:
            return None
        if t.by_locale is None:
            self.report.add("computed", file, line, f"{what} is computed at run time", "placeholder text; fill it in")
            return {self.default: f"‹{what}›"}
        for f in t.fields:
            self.fields.setdefault(f, {"type": "string", "source": "data", "example": f"‹{f.split('.')[-1]}›"})
        if set(t.by_locale) == {"*"}:
            return {self.default: t.by_locale["*"]}
        out = dict(t.by_locale)
        if "*" in out:
            out[self.default] = out.pop("*")
        if self.default not in out:
            first = next(iter(out.values()))
            out[self.default] = first
        for l in self.locales:
            out.setdefault(l, out[self.default])
        return {l: out[l] for l in self.locales if l in out}

    def _screens_of(self, h: Handler) -> None:
        if not h.branches:
            if h.toasts:
                return  # a toast-only callback becomes an `answer` action on the pressing button
            self.report.add("no-message", h.file, h.line, f"{h.name} sends no message", "no screen created")
            return

        def unhappy(group: list[Send]) -> bool:
            texts = " ".join(t for x in group if x.text and x.text.by_locale for t in x.text.by_locale.values())
            return bool(ERROR_WORDS.search(texts) or EMPTY_WORDS.search(texts) or re.search(r"sold out|нет в наличии", texts, re.I))

        # the happy path is the screen; errors and empty states become its branches
        h.branches.sort(key=unhappy)
        for i, group in enumerate(h.branches):
            sid = h.screen_id if i == 0 else f"{h.screen_id}.alt{i}"[:64]
            with_kb = [x for x in group if x.keyboard and x.keyboard.type == "inline" and x.keyboard.rows]
            main = with_kb[-1] if with_kb else group[0]
            for extra in [x for x in group if x is not main]:
                self.report.add("extra-message", h.file, extra.line,
                                f"{h.name} also sends a message here", f"the screen is the message at line {main.line}")
            self.screens[sid] = self._screen(h, sid, main, alt=i > 0)
        if len(h.branches) > 1:
            outcomes = ["main"] + [f"alt{i}" for i in range(1, len(h.branches))]
            self.handlers[h.screen_id] = {"outcomes": outcomes,
                                         "description": f"{h.file}:{h.line} {h.name} (branches imported from if/else)"}

    def _screen(self, h: Handler, sid: str, s: Send, alt: bool) -> dict:
        text = self._loc(s.text, h.file, s.line, "message text") if s.text else None
        if s.text and s.text.by_locale and any("<tg-emoji" in t for t in s.text.by_locale.values()):
            self.custom_emoji = True
        message: dict[str, Any] = {"id": "main", "format": s.fmt}
        if s.media:
            media = dict(s.media)
            f = media["file"]
            if f.get("field") in ("__upload__", "__computed__"):
                name = f"media.{sid.replace('.', '_')}"[:60]
                self.fields[name] = {"type": "string", "source": "data", "example": "file_id"}
                media["file"] = {"field": name}
                why = (f"uploads a local file ({s.local_upload})" if f["field"] == "__upload__"
                       else f"sends a computed {media['type']}")
                self.report.add("media-file", h.file, s.line, f"{h.name} {why}",
                                f"field {name}: put the file_id here (no upload by bot-ui)")
            message["media"] = media
            if media["type"] in ("sticker", "video_note"):
                text = None
        if text:
            message["text"] = text
        elif not s.media:
            message["text"] = {self.default: f"‹{h.name}›"}
            self.report.add("no-text", h.file, s.line, f"{h.name}: message without a readable text", "placeholder text")
        joined = " ".join((text or {}).values())
        kind = "entry" if any(f["kind"] == "command" and f["value"] == "start" for f in h.filters) and not alt else \
            "error" if ERROR_WORDS.search(joined) else "empty" if EMPTY_WORDS.search(joined) else \
            "form" if h.sets_state else "menu" if s.keyboard and s.keyboard.rows else "result"
        first = re.sub(r"<[^>]+>", "", (text or {}).get(self.default, "")).strip().split("\n")[0].strip()
        title = (first[:40] + ("…" if len(first) > 40 else "")) if first and not first.startswith("‹") else h.name
        screen: dict[str, Any] = {"id": sid, "title": title + (" (branch)" if alt else ""), "kind": kind,
                                  "audience": "private", "notes": f"imported from {h.file}:{s.line}", "message": message}
        screen["_edit"] = s.edit
        if s.keyboard:
            screen["_keyboard"] = s.keyboard
            if s.keyboard.dynamic:
                self.report.add("computed-keyboard", h.file, s.line, f"{h.name}: buttons built in a loop or at run time",
                                "static buttons kept; list items are not on the map")
        if h.sets_state:
            screen["_sets_state"] = h.sets_state[-1]
        return screen

    def _targets_for(self, b: Button) -> list[Handler]:
        out = []
        for h in self.an.handlers:
            if h.kind != "callback":
                continue
            for f in h.filters:
                if f["kind"] == "callback" and b.callback is not None and f["value"] == b.callback:
                    out.append((0, h))
                elif f["kind"] == "callback-class" and b.callback_prefix == f["value"] and \
                        all(b.callback_eq.get(k) == v for k, v in f["eq"].items()):
                    out.append((1, h))
                elif f["kind"] == "callback-prefix" and f["value"] and b.callback and b.callback.startswith(f["value"]):
                    out.append((2, h))
        out.sort(key=lambda x: x[0])
        return [h for _, h in out]

    def _text_target(self, label: str) -> Handler | None:
        for h in self.an.handlers:
            if h.kind == "message" and any(f["kind"] == "text" and f["value"] == label for f in h.filters):
                return h
        return None

    def _action_for_handler(self, target: Handler, label: dict, extra: dict) -> dict:
        if target.screen_id in self.handlers:
            outs = self.handlers[target.screen_id]["outcomes"]
            return {"label": label, "type": "handler", "handlerId": target.screen_id,
                    "outcomes": {o: target.screen_id if o == "main" else f"{target.screen_id}.{o}" for o in outs}, **extra}
        if target.screen_id in self.screens:
            act = {"label": label, "type": "navigate", "to": target.screen_id, **extra}
            act["presentation"] = "edit" if self.edits.get(target.screen_id) else "send"
            return act
        if target.toasts:
            t = self._loc(target.toasts[0][0], target.file, target.toasts[0][1], "toast") or {self.default: "OK"}
            return {"label": label, "type": "answer", "text": t, **extra}
        return {"label": label, "type": "disabled", **extra}

    def _wire(self) -> None:
        self.edits = {sid: bool(sc.get("_edit")) for sid, sc in self.screens.items()}
        by_state: dict[str, Handler] = {}
        for h in self.an.handlers:
            for f in h.filters:
                if f["kind"] == "state":
                    by_state[f["value"]] = h
        for sid, screen in self.screens.items():
            kb: Keyboard | None = screen.pop("_keyboard", None)
            screen.pop("_edit", None)  # read from self.edits, filled before wiring
            state = screen.pop("_sets_state", None)
            src_file, src_line = screen["notes"][len("imported from "):].rsplit(":", 1)
            actions, rows, used = {}, [], set()
            if kb is not None:
                for row in kb.rows:
                    out_row = []
                    for b in row:
                        label = self._loc(b.text, src_file, b.line, "button label") or {self.default: "…"}
                        default_label = label.get(self.default, "")
                        aid = _action_id(default_label, used)
                        used.add(aid)
                        extra: dict[str, Any] = {}
                        if b.icon:
                            extra["icon"] = {"customEmojiId": b.icon}
                            self.custom_emoji = True
                        if b.style:
                            extra["style"] = b.style
                        if b.url:
                            act = {"label": label, "type": "url", "url": b.url, **extra}
                        elif kb.type == "reply":
                            src = (b.text.by_locale or {})
                            t = self._text_target(src.get("*") or src.get(self.default) or "")
                            if t is None:
                                self.report.add("unmatched-text", src_file, b.line,
                                                f"reply button {default_label!r} has no F.text handler", "disabled button")
                                act = {"label": label, "type": "disabled", **extra}
                            else:
                                act = self._action_for_handler(t, label, extra)
                                act["presentation"] = "send"
                        else:
                            ts = self._targets_for(b)
                            if b.callback:
                                extra["callbackData"] = b.callback[:64]
                            if not ts:
                                why = "callback_data is computed" if b.dynamic else f"callback_data {b.callback!r} has no handler"
                                self.report.add("unmatched-callback", src_file, b.line, f"button {default_label!r}: {why}",
                                                "disabled button")
                                act = {"label": label, "type": "disabled", **{k: v for k, v in extra.items()
                                                                               if k != "callbackData"}}
                            else:
                                if len(ts) > 1:
                                    self.report.add("ambiguous-callback", src_file, b.line,
                                                    f"button {default_label!r} matches {', '.join(t.name for t in ts)}",
                                                    f"first: {ts[0].name}")
                                act = self._action_for_handler(ts[0], label, extra)
                        actions[aid] = act
                        out_row.append(aid)
                    if out_row:
                        rows.append(out_row[:8])
                screen["keyboard"] = {"type": kb.type, "rows": rows}
                if kb.placeholder is not None and kb.type in ("reply", "force_reply"):
                    ph = self._loc(kb.placeholder, src_file, int(src_line), "input placeholder")
                    if ph:
                        screen["keyboard"]["placeholder"] = ph
                if kb.type in ("force_reply", "remove"):
                    screen["keyboard"].pop("rows")
            if actions:
                screen["actions"] = actions
            if state:
                nxt = by_state.get(state)
                field_name = "input." + re.sub(r"[^a-z0-9_]+", "_", state.split(".")[-1].lower())
                if nxt and nxt.screen_id in self.screens:
                    self.fields[field_name] = {"type": "string", "source": "input", "maxLength": 4096}
                    screen["input"] = {"field": field_name, "to": nxt.screen_id}
                else:
                    self.report.add("state-unhandled", src_file, int(src_line), f"state {state} has no imported handler",
                                    "no input on this screen")

    def project(self) -> dict:
        entries, seen = [], set()
        for h in self.an.handlers:
            if h.screen_id not in self.screens:
                continue
            for f in h.filters:
                if f["kind"] == "command" and f.get("deepLink"):
                    if "deeplink" not in seen:
                        seen.add("deeplink")
                        entries.append({"id": "start-link", "type": "deeplink", "payload": "*", "screen": h.screen_id})
                    continue
                if f["kind"] == "command" and f["value"] not in seen and re.fullmatch(r"[a-z0-9_]{1,32}", f["value"]):
                    seen.add(f["value"])
                    entries.append({"id": f["value"].replace("_", "-"), "type": "command", "command": f["value"],
                                    "screen": h.screen_id})
        if not entries and self.screens:
            first = next(iter(self.screens))
            self.report.add("no-entry", "", 0, "no /command handler found", f"/start -> {first}")
            entries.append({"id": "start", "type": "command", "command": "start", "screen": first})
        caps: dict[str, Any] = {"widgets": self.an.uses_widgets, "richMessages": False}
        if self.custom_emoji:
            caps["customEmoji"] = "none"
            self.report.add("custom-emoji", "", 0, "the bot uses custom (premium) emoji",
                            "capabilities.customEmoji = none: set 'fragment' or 'owner_premium' if the bot qualifies, "
                            "otherwise Telegram drops them silently")
        return {"schemaVersion": SCHEMA_VERSION, "projectId": self.project_id, "title": self.project_id,
                "defaultLocale": self.default, "locales": self.locales, "entryPoints": entries,
                "contexts": ["private"], "fields": dict(sorted(self.fields.items())),
                "handlers": self.handlers, "capabilities": caps,
                "adapter": {"sdk": "aiogram", "source": "imported by bot-ui import; the bot's code is unchanged"}}


def _action_id(label: str, used: set[str]) -> str:
    translit = str.maketrans("абвгдеёжзийклмнопрстуфхцчшщъыьэюяієїґ",
                             "abvgdeejziyklmnoprstufhccss_y_euyieig")
    base = re.sub(r"[^a-z0-9]+", "_", label.lower().translate(translit)).strip("_")[:24].strip("_") or "button"
    if not re.match(r"^[a-z0-9]", base):
        base = "b_" + base
    out, n = base, 2
    while out in used:
        out, n = f"{base}_{n}", n + 1
    return out


# ---------------------------------------------------------------------------- entry point

def _smoke(project: dict, screens: dict) -> list[dict]:
    """One short scenario per button of the /start screen, so `simulate` has something to run."""
    start = next((e["screen"] for e in project["entryPoints"] if e.get("command") == "start"), None)
    if not start or start not in screens:
        return []
    s = screens[start]
    handlers = {hid: [h["outcomes"][0]] for hid, h in project["handlers"].items()}
    out = []
    for aid in [a for row in (s.get("keyboard") or {}).get("rows", []) for a in row][:12]:
        act = s["actions"][aid]
        steps: list[dict] = [{"command": "start"}]
        if (s.get("keyboard") or {}).get("type") == "reply":
            steps.append({"text": act["label"][project["defaultLocale"]]})
        else:
            steps.append({"press": aid})
        if act.get("type") == "navigate":
            steps.append({"expect": {"screen": act["to"]}})
        out.append({"scenarioId": f"import.start.{aid.replace('_', '-')}", "title": f"/start, then {aid}",
                    "locale": project["defaultLocale"], "context": {"chat": "private"}, "data": {},
                    "handlers": handlers, "steps": steps})
    return out


def import_bot(source: str, into: str, *, project_id: str | None = None, dry_run: bool = False) -> dict:
    source, into = os.path.abspath(source), os.path.abspath(into)
    report = Report()
    an = Analyzer(source, load_catalogs(source), report)
    an.load()
    existing = os.path.isfile(os.path.join(into, "project.json"))
    map_path = os.path.join(into, "import-map.json")
    id_map: dict[str, str] = {}
    if existing and os.path.isfile(map_path):
        with open(map_path, encoding="utf-8") as fh:
            id_map = json.load(fh).get("handlers", {})
    pid = project_id or re.sub(r"[^a-z0-9-]+", "-", os.path.basename(source).lower()).strip("-") or "bot"
    if check_id(pid):
        pid = "bot"
    b = Builder(an, report, pid, id_map)
    project = b.run()
    screens = b.screens
    files: dict[str, bytes] = {"project.json": canonical_json(project, "project")}
    for sid, doc in screens.items():
        files[f"screens/{sid}.json"] = canonical_json(doc, "screen")
    for sc in _smoke(project, screens):
        files[f"scenarios/{sc['scenarioId']}.json"] = (json.dumps(sc, ensure_ascii=False, indent=2) + "\n").encode()
    map_doc = {"format": "bot-ui-import-map/v1", "source": "aiogram",
               "handlers": dict(sorted(b.id_map.items()))}
    emoji_ids = custom_emoji_ids(an)
    if emoji_ids:
        map_doc["customEmoji"] = emoji_ids
        report.add("emoji-packs", "", 0, f"{len(emoji_ids)} custom emoji id(s) in the bot's code; their packs are not "
                                         "in the project's emoji library yet",
                   f"bot-ui emoji import-used --project {into} (or import --emoji-packs) imports every pack they come from")
    result = {"ok": True, "project": into, "projectId": pid, "existing": existing,
              "stats": {"files": len(an.modules), "handlers": len(an.handlers), "screens": len(screens),
                        "arrows": sum(1 for s in screens.values() for a in (s.get("actions") or {}).values()
                                      if a.get("type") in ("navigate", "handler")) +
                        sum(1 for s in screens.values() if s.get("input")),
                        "media": sum(1 for s in screens.values() if s["message"].get("media")),
                        "locales": project["locales"], "customEmoji": len(emoji_ids)},
              "report": report.items, "status": "static"}
    if existing:
        return _reimport(into, files, map_doc, result, dry_run)
    stage = os.path.join(os.path.dirname(into), f".{os.path.basename(into)}.bot-ui-import-{uuid.uuid4().hex[:8]}")
    for rel, data in files.items():
        path = os.path.join(stage, *rel.split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as fh:
            fh.write(data)
    with open(os.path.join(stage, "import-map.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(map_doc, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    with open(os.path.join(stage, ".gitattributes"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("* text=auto eol=lf\n")
    diags = validate(open_snapshot(stage))
    shutil.rmtree(os.path.join(stage, ".bot-ui"), ignore_errors=True)
    result["diagnostics"] = [d.to_json() for d in diags if d.severity != "info"]
    result["errors"] = sum(1 for d in diags if d.severity == "error")
    untranslated: dict[str, int] = {}
    for d in diags:
        if d.code == "LOCALE_TEXT_MISSING":
            loc = d.pointer.rsplit("/", 1)[-1]
            untranslated[loc] = untranslated.get(loc, 0) + 1
    for loc, n in sorted(untranslated.items()):
        report.add("untranslated", "", 0, f"{n} texts and labels have no '{loc}' translation in the bot's catalogs",
                   f"users with '{loc}' see '{project['defaultLocale']}'; translate in the Studio or the catalogs")
    for d in diags:
        if d.severity == "error":
            report.add("invalid", d.file, 0, f"{d.code} {d.pointer}: {d.message}", "fix before the first save")
    if dry_run:
        shutil.rmtree(stage, ignore_errors=True)
        result["dryRun"] = True
        return result
    os.makedirs(os.path.dirname(into), exist_ok=True)
    if os.path.isdir(into) and not os.listdir(into):
        os.rmdir(into)
    replace_dir(stage, into)
    result["revision"] = open_snapshot(into).revision
    return result


def _reimport(into: str, files: dict[str, bytes], map_doc: dict, result: dict, dry_run: bool) -> dict:
    """Add screens for new handlers only; keep every screen already in the project."""
    from .store import write_patch
    snap = open_snapshot(into)
    known = set(snap.screens)
    new = {rel: data for rel, data in files.items() if rel.startswith("screens/") and rel[8:-5] not in known}
    gone = sorted(sid for sid in known if f"screens/{sid}.json" not in files)
    result["kept"] = sorted(known & {rel[8:-5] for rel in files if rel.startswith("screens/")})
    result["added"] = sorted(rel[8:-5] for rel in new)
    result["gone"] = gone
    for sid in gone:
        result["report"].append({"kind": "handler-gone", "file": "", "line": 0,
                                 "what": f"{sid} has no source handler any more", "default": "kept; delete it yourself"})
    if not new and not dry_run:
        _write_map(into, map_doc)  # the found custom emoji ids stay current
    if not new or dry_run:
        result["dryRun"] = dry_run
        result["revision"] = snap.revision
        return result
    changes = [{"screenId": rel[8:-5], "create": json.loads(data)} for rel, data in sorted(new.items())]
    res = write_patch(into, {"format": "bot-ui-patch/v1", "projectId": (snap.project or {}).get("projectId"),
                             "baseRevision": snap.revision, "changes": changes})
    _write_map(into, map_doc)
    result["revision"] = res.revision
    result["diff"] = res.diff
    return result


def _write_map(into: str, map_doc: dict) -> None:
    with open(os.path.join(into, "import-map.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(map_doc, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def report_markdown(result: dict) -> str:
    st = result["stats"]
    lines = [f"bot-ui import: {st['handlers']} handlers in {st['files']} files -> {st['screens']} screens, "
             f"{st['arrows']} arrows, {st['media']} media screens, locales {', '.join(st['locales'])} (static, read-only on the bot)"]
    if result.get("existing"):
        lines.append(f"re-import: kept {len(result['kept'])}, added {len(result['added'])}, gone {len(result['gone'])}")
    if result.get("errors"):
        lines.append(f"{result['errors']} validation error(s): bot-ui validate --project {result['project']}")
    if result["report"]:
        lines.append(f"\n{len(result['report'])} item(s) to review (file:line - what - default taken):")
        for it in result["report"]:
            where = f"{it['file']}:{it['line']}" if it["file"] else "project"
            lines.append(f"  [{it['kind']}] {where} - {it['what']} - {it['default']}")
    return "\n".join(lines)
