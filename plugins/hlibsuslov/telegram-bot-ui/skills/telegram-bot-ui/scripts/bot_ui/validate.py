"""Cross-file validation of a snapshot. One result shape for every surface:
{code, severity, file, pointer, screenId?, message}."""
from __future__ import annotations

import re
from typing import Any

from . import render, rich
from .project import Diagnostic, Snapshot, check_id

KINDS = {"entry", "menu", "form", "confirmation", "result", "error", "empty", "loading", "notification", "status"}
AUDIENCES = {"private", "group", "supergroup", "forum", "channel", "inline", "business", "channel_dm", "any"}
ACTION_TYPES = {"navigate", "back", "url", "answer", "handler", "disabled"}
KEYBOARD_TYPES = {"inline", "reply", "force_reply", "remove", "none"}
FIELD_TYPES = {"string", "number", "boolean", "enum"}
FIELD_SOURCES = {"data", "context", "state", "input"}
RULE_SOURCES = {"context", "state"}  # values typed by a user or sent by a widget are not trusted context
ENTRY_TYPES = {"command", "event", "deeplink"}
INLINE_ROW_MAX = 8
CUSTOM_EMOJI_ID = re.compile(r"^\d{1,20}$")
CUSTOM_EMOJI_ROUTES = {"fragment", "owner_premium", "none"}
URL_RE = re.compile(r"^(https?://|tg://)\S+$")
COMMAND_RE = re.compile(r"^[a-z0-9_]{1,32}$")


class _Out:
    def __init__(self) -> None:
        self.items: list[Diagnostic] = []
        self.custom_emoji: list[tuple[str, str, str]] = []  # (file, pointer, screenId) of every use
        self.custom_emoji_ids: list[tuple[str, str, str, str, str | None]] = []  # + (id, fallback or None)

    def add(self, code: str, sev: str, file: str, pointer: str, message: str, sid: str | None = None) -> None:
        self.items.append(Diagnostic(code, sev, file, pointer, message, sid))


def _type_ok(field: dict, value: Any) -> bool:
    t = field.get("type")
    if t == "enum":
        return value in (field.get("values") or [])
    if t == "string":
        return isinstance(value, str)
    if t == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if t == "boolean":
        return isinstance(value, bool)
    return False


def targets(action: dict) -> list[tuple[str, str]]:
    """(label, target screen) pairs a single action can lead to, for graphs and reachability."""
    out = []
    t = action.get("type")
    if t == "navigate":
        if isinstance(action.get("rule"), dict):
            r = action["rule"]
            out += [("match", r.get("match")), ("otherwise", r.get("otherwise"))]
        else:
            out.append(("to", action.get("to")))
    elif t == "handler":
        out += [(f"outcome:{k}", v) for k, v in (action.get("outcomes") or {}).items()]
    elif t == "back" and action.get("fallback"):
        out.append(("back-fallback", action.get("fallback")))
    return [(k, v) for k, v in out if isinstance(v, str)]


def validate(snap: Snapshot) -> list[Diagnostic]:
    out = _Out()
    out.items.extend(snap.load_diagnostics)
    project = snap.project if isinstance(snap.project, dict) else None
    if project is None:
        return out.items
    _project(project, snap, out)
    for sid, screen in snap.screens.items():
        _screen(project, snap, sid, screen, out)
    _callbacks(snap, out)
    _custom_emoji(project, snap, out)
    _reachability(project, snap, out)
    for wid, w in snap.widgets.items():
        _widget(project, snap, wid, w, out)
    for name, sc in snap.scenarios.items():
        _scenario(project, snap, name, sc, out)
    return out.items


def _project(p: dict, snap: Snapshot, out: _Out) -> None:
    f = "project.json"
    if (err := check_id(p.get("projectId"))):
        out.add("PROJECT_ID_INVALID", "error", f, "/projectId", err)
    locales = p.get("locales")
    if not isinstance(locales, list) or not locales or not all(isinstance(x, str) for x in locales):
        out.add("LOCALES_INVALID", "error", f, "/locales", "locales must be a non-empty list of language codes")
    elif p.get("defaultLocale") not in locales:
        out.add("DEFAULT_LOCALE_MISSING", "error", f, "/defaultLocale", "defaultLocale must be one of locales")
    seen_ids, seen_keys = set(), set()
    for i, ep in enumerate(p.get("entryPoints") or []):
        ptr = f"/entryPoints/{i}"
        if not isinstance(ep, dict):
            out.add("ENTRY_INVALID", "error", f, ptr, "entry point must be an object")
            continue
        if ep.get("type") not in ENTRY_TYPES:
            out.add("ENTRY_TYPE_UNKNOWN", "error", f, ptr + "/type", f"type must be one of {sorted(ENTRY_TYPES)}")
        key = (ep.get("type"), ep.get("command") or ep.get("eventKey") or ep.get("payload"))
        if ep.get("id") in seen_ids or key in seen_keys:
            out.add("ENTRY_DUPLICATE", "error", f, ptr, f"duplicate entry point {ep.get('id') or key}")
        seen_ids.add(ep.get("id"))
        seen_keys.add(key)
        if ep.get("type") == "command" and not COMMAND_RE.match(str(ep.get("command", ""))):
            out.add("COMMAND_INVALID", "error", f, ptr + "/command", "command: 1-32 of a-z, 0-9, _ (no slash)")
        if ep.get("type") == "event" and not isinstance(ep.get("eventKey"), str):
            out.add("EVENT_KEY_MISSING", "error", f, ptr + "/eventKey",
                    "an event entry needs an eventKey; a screen ID is not a public entry point")
        if ep.get("screen") not in snap.screens:
            out.add("ENTRY_TARGET_MISSING", "error", f, ptr + "/screen", f"screen {ep.get('screen')!r} does not exist")
    for name, fd in (p.get("fields") or {}).items():
        ptr = f"/fields/{name}"
        if not isinstance(fd, dict) or fd.get("type") not in FIELD_TYPES:
            out.add("FIELD_TYPE_INVALID", "error", f, ptr, f"type must be one of {sorted(FIELD_TYPES)}")
            continue
        if fd.get("source") not in FIELD_SOURCES:
            out.add("FIELD_SOURCE_INVALID", "error", f, ptr + "/source", f"source must be one of {sorted(FIELD_SOURCES)}")
        if fd["type"] == "enum" and not fd.get("values"):
            out.add("FIELD_ENUM_EMPTY", "error", f, ptr + "/values", "an enum field needs values")
    for hid, hd in (p.get("handlers") or {}).items():
        if not isinstance(hd, dict) or not isinstance(hd.get("outcomes"), list) or not hd["outcomes"]:
            out.add("HANDLER_INVALID", "error", f, f"/handlers/{hid}", "a handler declares its outcomes")


def _text_checks(p: dict, file: str, pointer: str, value: Any, fmt: str, sid: str, out: _Out,
                 *, label: bool = False, limit: int | None = None, optional: bool = False) -> None:
    default = p.get("defaultLocale")
    locales = p.get("locales") or []
    fields = p.get("fields") or {}
    if isinstance(value, str):
        value = {default: value}
    if optional and (value is None or value == {}):
        return
    if not isinstance(value, dict) or not isinstance(value.get(default), str) or not value.get(default):
        out.add("DEFAULT_LOCALE_TEXT_MISSING", "error", file, f"{pointer}/{default}",
                f"text in the default locale '{default}' is required", sid)
        return
    for loc in locales:
        if loc != default and not isinstance(value.get(loc), str):
            out.add("LOCALE_TEXT_MISSING", "warning", file, f"{pointer}/{loc}",
                    f"no '{loc}' text: users with this language see '{default}'", sid)
    for loc, text in value.items():
        if loc not in locales:
            out.add("LOCALE_UNKNOWN", "warning", file, f"{pointer}/{loc}", f"'{loc}' is not in project locales", sid)
        if not isinstance(text, str):
            continue
        for name in render.placeholders(text):
            if name not in fields:
                out.add("PLACEHOLDER_UNDECLARED", "error", file, f"{pointer}/{loc}",
                        f"{{{name}}} is not a declared field in project.json fields", sid)
        if fmt == "regular.html":
            _html_check(text, file, f"{pointer}/{loc}", sid, out)
        elif fmt == "rich.html":
            for code, sev, message in rich.check(text):
                if code != "TEXT_TOO_LONG":  # counted below with the shared rule
                    out.add(code, sev, file, f"{pointer}/{loc}", message, sid)
        n = render.utf16_len(render.visible_text(text, fmt))
        cap = limit or (64 if label else render.TEXT_MAX)
        if n > cap:
            out.add("TEXT_TOO_LONG", "error" if not label else "warning", file, f"{pointer}/{loc}",
                    f"{n} UTF-16 units > {cap}", sid)
    ph = {loc: sorted(set(render.placeholders(t))) for loc, t in value.items() if isinstance(t, str)}
    if len({tuple(v) for v in ph.values()}) > 1:
        out.add("PLACEHOLDERS_DIFFER", "warning", file, pointer, f"placeholders differ between locales: {ph}", sid)


def _html_check(text: str, file: str, pointer: str, sid: str, out: _Out) -> None:
    from .skill import load
    allowed = load("audit_copy").ALLOWED
    stack: list[str] = []
    for close, tag in re.findall(r"<(/?)([a-zA-Z-]+)[^>]*>", text):
        tag = tag.lower()
        if tag not in allowed:
            out.add("HTML_TAG_UNSUPPORTED", "error", file, pointer, f"<{tag}> is not a Telegram regular-HTML tag", sid)
        elif close:
            if not stack or stack.pop() != tag:
                out.add("HTML_UNBALANCED", "error", file, pointer, f"unbalanced </{tag}>", sid)
        else:
            stack.append(tag)
    if stack:
        out.add("HTML_UNBALANCED", "error", file, pointer, f"unclosed <{stack[-1]}>", sid)
    if re.search(r"&(?![a-zA-Z]+;|#\d+;|#x[0-9a-fA-F]+;)", text) or re.search(r"<(?![a-zA-Z/])", text):
        out.add("HTML_UNESCAPED", "error", file, pointer, "escape a bare '&' or '<' as &amp; or &lt;", sid)
    for m in re.finditer(r"<tg-emoji([^>]*)>(.*?)</tg-emoji>", text, re.S):
        out.custom_emoji.append((file, pointer, sid))
        eid = re.search(r'emoji-id="([^"]*)"', m.group(1))
        if not eid or not CUSTOM_EMOJI_ID.match(eid.group(1)):
            out.add("CUSTOM_EMOJI_INVALID", "error", file, pointer, 'tg-emoji needs emoji-id="<digits>"', sid)
        else:
            out.custom_emoji_ids.append((file, pointer, sid, eid.group(1), m.group(2)))
        if not m.group(2).strip() or len(m.group(2)) > 16 or "<" in m.group(2):
            out.add("CUSTOM_EMOJI_FALLBACK", "error", file, pointer,
                    "put one ordinary emoji inside <tg-emoji>: users who cannot see the custom emoji see it", sid)


def _screen(p: dict, snap: Snapshot, sid: str, s: dict, out: _Out) -> None:
    f = snap.screen_path(sid)
    if (err := check_id(sid)):
        out.add("SCREEN_ID_INVALID", "error", f, "/id", err, sid)
        return
    if f != f"screens/{sid}.json":
        out.add("SCREEN_FILE_NAME", "error", f, "/id", f"file must be screens/{sid}.json", sid)
    if s.get("kind") not in KINDS:
        out.add("SCREEN_KIND_UNKNOWN", "error", f, "/kind", f"kind must be one of {sorted(KINDS)}", sid)
    audience = s.get("audience", "private")
    if audience not in AUDIENCES:
        out.add("AUDIENCE_UNKNOWN", "error", f, "/audience", f"audience must be one of {sorted(AUDIENCES)}", sid)
    contexts = p.get("contexts") or ["private"]
    if audience not in contexts and audience != "any":
        out.add("AUDIENCE_NOT_ENABLED", "error", f, "/audience", f"'{audience}' is not in project contexts {contexts}", sid)
    msg = s.get("message")
    if not isinstance(msg, dict):
        out.add("MESSAGE_MISSING", "error", f, "/message", "a screen has one main message", sid)
        return
    fmt = msg.get("format", "regular.plain")
    if fmt not in render.KNOWN_FORMATS:
        out.add("FORMAT_UNKNOWN", "error", f, "/message/format", f"format {fmt!r} is not known", sid)
    elif fmt not in render.EDITABLE_FORMATS:
        out.add("FORMAT_READ_ONLY", "info", f, "/message/format",
                f"{fmt} opens read-only in the Studio; edit the file or patch it with the CLI", sid)
    media = msg.get("media")
    if media is not None:
        _media(p, f, sid, media, out)
    mtype = media.get("type") if isinstance(media, dict) else None
    if fmt in render.RICH_FORMATS:
        if media is not None:
            out.add("RICH_MEDIA_FIELD", "error", f, "/message/media",
                    "a rich screen puts media inside its HTML (<img>, <video>, <figure>); message.media is for regular formats", sid)
        _text_checks(p, f, "/message/text", msg.get("text"), fmt, sid, out, limit=rich.TEXT_MAX)
        for st, var in (msg.get("states") or {}).items():
            if isinstance(var, dict) and "text" in var:
                _text_checks(p, f, f"/message/states/{st}/text", var["text"], fmt, sid, out, limit=rich.TEXT_MAX)
    elif fmt in render.FORMATS:
        if mtype in ("sticker", "video_note"):
            if msg.get("text"):
                out.add("MEDIA_NO_CAPTION", "error", f, "/message/text",
                        f"a {mtype} has no caption; put the text on its own screen or drop it", sid)
        else:
            cap = render.CAPTION_MAX if mtype else None
            _text_checks(p, f, "/message/text", msg.get("text"), fmt, sid, out, limit=cap, optional=bool(mtype))
            for st, var in (msg.get("states") or {}).items():
                if isinstance(var, dict) and "text" in var:
                    _text_checks(p, f, f"/message/states/{st}/text", var["text"], fmt, sid, out, limit=cap)
    kb = s.get("keyboard") or {"type": "none"}
    ktype = kb.get("type", "none")
    if ktype not in KEYBOARD_TYPES:
        out.add("KEYBOARD_TYPE_UNKNOWN", "error", f, "/keyboard/type", f"type must be one of {sorted(KEYBOARD_TYPES)}", sid)
    actions = s.get("actions") or {}
    placed: dict[str, str] = {}
    for r, row in enumerate(kb.get("rows") or []):
        if not isinstance(row, list) or not row:
            out.add("KEYBOARD_ROW_INVALID", "error", f, f"/keyboard/rows/{r}", "a row is a non-empty list of action IDs", sid)
            continue
        if ktype == "inline" and len(row) > INLINE_ROW_MAX:
            out.add("KEYBOARD_ROW_TOO_WIDE", "error", f, f"/keyboard/rows/{r}", f"more than {INLINE_ROW_MAX} buttons", sid)
        for c, aid in enumerate(row):
            ptr = f"/keyboard/rows/{r}/{c}"
            if aid not in actions:
                out.add("KEYBOARD_ACTION_MISSING", "error", f, ptr, f"action {aid!r} is not defined in actions", sid)
            elif aid in placed:
                out.add("KEYBOARD_ACTION_DUPLICATE", "error", f, ptr, f"{aid!r} is already at {placed[aid]}", sid)
            placed[aid] = ptr
    if ktype in ("force_reply", "remove", "none") and kb.get("rows"):
        out.add("KEYBOARD_ROWS_IGNORED", "warning", f, "/keyboard/rows", f"{ktype} shows no buttons", sid)
    in_text = rich.screen_action_ids(s)
    for aid in sorted(in_text):
        a = actions.get(aid)
        if not isinstance(a, dict) or a.get("hidden"):
            out.add("RICH_BUTTON_ACTION_MISSING", "error", f, "/message/text",
                    f'<tg-button action="{aid}"> needs a visible action {aid!r} in actions', sid)
        elif aid in placed:
            out.add("RICH_BUTTON_ON_KEYBOARD", "warning", f, placed[aid],
                    f"{aid!r} is both in the document and on the keyboard; keep one place per action", sid)
        elif a.get("type") == "url" and a.get("style") == "link":
            out.add("RICH_BUTTON_STYLE", "warning", f, f"/actions/{aid}/style", 'style "link" is for callback buttons only; it is dropped', sid)
    labels_seen: dict[str, str] = {}
    for aid, a in actions.items():
        ptr = f"/actions/{aid}"
        if (err := check_id(aid)) or "." in aid:
            out.add("ACTION_ID_INVALID", "error", f, ptr, err or "action IDs are one segment (no '.')", sid)
        if not isinstance(a, dict):
            out.add("ACTION_INVALID", "error", f, ptr, "an action is an object", sid)
            continue
        t = a.get("type")
        if t not in ACTION_TYPES:
            out.add("ACTION_TYPE_UNKNOWN", "error", f, ptr + "/type", f"type must be one of {sorted(ACTION_TYPES)}", sid)
            continue
        if aid not in placed and aid not in in_text and not a.get("hidden"):
            out.add("ACTION_NOT_PLACED", "warning", f, ptr, "the action is not on the keyboard or in the document", sid)
        _text_checks(p, f, ptr + "/label", a.get("label"), "regular.plain", sid, out, label=True)
        lbl = render.localized(a.get("label"), p.get("defaultLocale", "en"), p.get("defaultLocale", "en"))
        if ktype == "reply" and lbl:
            if lbl in labels_seen:
                out.add("REPLY_LABEL_DUPLICATE", "error", f, ptr + "/label",
                        f"reply buttons arrive as text; '{lbl}' is also the label of {labels_seen[lbl]}", sid)
            labels_seen[lbl] = aid
        if ktype == "reply" and t == "url":
            out.add("REPLY_URL_UNSUPPORTED", "error", f, ptr + "/type", "a reply keyboard button cannot open a URL", sid)
        _action(p, snap, sid, s, aid, a, f, ptr, out)
    inp = s.get("input")
    if inp is not None:
        fd = (p.get("fields") or {}).get(inp.get("field")) if isinstance(inp, dict) else None
        if not fd or fd.get("source") != "input":
            out.add("INPUT_FIELD_INVALID", "error", f, "/input/field", "input stores into a declared field with source 'input'", sid)
        if not isinstance(inp, dict) or inp.get("to") not in snap.screens:
            out.add("INPUT_TARGET_MISSING", "error", f, "/input/to", "input.to must be an existing screen", sid)
    w = s.get("widget")
    if w is not None:
        if not isinstance(w, dict) or w.get("ref") not in snap.widgets:
            out.add("WIDGET_REF_MISSING", "error", f, "/widget/ref", f"widget {w!r} is not in widgets/", sid)
        elif audience != "private":
            out.add("WIDGET_CONTEXT", "warning", f, "/widget",
                    "production widgets work in private chats; other contexts get the fallback message", sid)
    for st in (msg.get("states") or {}):
        if st not in ("loading", "empty", "error", "stale"):
            out.add("STATE_UNKNOWN", "info", f, f"/message/states/{st}", f"state '{st}' is kept; the simulator uses loading", sid)
    _rendered_markup(p, s, sid, f, out)


def _media(p: dict, f: str, sid: str, media: Any, out: _Out) -> None:
    if not isinstance(media, dict) or media.get("type") not in render.MEDIA_TYPES:
        out.add("MEDIA_TYPE_UNKNOWN", "error", f, "/message/media/type",
                f"media type is one of {sorted(render.MEDIA_TYPES)} (documents and uploads are not part of bot-ui)", sid)
        return
    src = media.get("file")
    keys = [k for k in ("fileId", "url", "field") if isinstance(src, dict) and k in src]
    if len(keys) != 1:
        out.add("MEDIA_FILE_SOURCE", "error", f, "/message/media/file",
                "file is exactly one of {fileId}, {url} or {field}; local files are never uploaded", sid)
        return
    k, v = keys[0], src[keys[0]]
    if k == "fileId" and not (isinstance(v, str) and re.match(r"^[A-Za-z0-9_-]{8,}$", v)):
        out.add("MEDIA_FILE_ID", "error", f, "/message/media/file/fileId", "a Telegram file_id (letters, digits, _ and -)", sid)
    elif k == "url" and not (isinstance(v, str) and v.startswith("https://")):
        out.add("MEDIA_URL", "error", f, "/message/media/file/url", "an https:// URL Telegram can fetch", sid)
    elif k == "field":
        fd = (p.get("fields") or {}).get(v)
        if not fd or fd.get("type") != "string" or fd.get("source") not in ("data", "context"):
            out.add("MEDIA_FIELD", "error", f, "/message/media/file/field",
                    "a declared string field from data or context (a file_id or https URL at run time)", sid)
    if media.get("spoiler") and media["type"] not in render.SPOILER_MEDIA:
        out.add("MEDIA_SPOILER", "warning", f, "/message/media/spoiler", f"a {media['type']} cannot be hidden as a spoiler", sid)
    if media["type"] == "sticker" and not isinstance(media.get("emoji"), str):
        out.add("STICKER_EMOJI", "info", f, "/message/media/emoji", "an emoji for the sticker lets previews show it", sid)


def _action(p: dict, snap: Snapshot, sid: str, s: dict, aid: str, a: dict, f: str, ptr: str, out: _Out) -> None:
    t = a["type"]
    fields = p.get("fields") or {}
    audience = s.get("audience", "private")

    def target(to: Any, where: str) -> None:
        if not isinstance(to, str) or not to:
            out.add("TARGET_EMPTY", "error", f, where, "choose a target screen", sid)
        elif to not in snap.screens:
            out.add("TARGET_MISSING", "error", f, where, f"screen {to!r} does not exist", sid)
        else:
            ta = snap.screens[to].get("audience", "private")
            if ta != audience and "any" not in (ta, audience):
                out.add("AUDIENCE_MISMATCH", "error", f, where,
                        f"{sid} ({audience}) leads to {to} ({ta}); a transition keeps one audience", sid)

    if t == "navigate":
        has_to, rule = "to" in a, a.get("rule")
        if has_to == (rule is not None):
            out.add("NAVIGATE_TARGET", "error", f, ptr, "navigate has exactly one of 'to' or 'rule'", sid)
        if has_to:
            target(a.get("to"), ptr + "/to")
        if rule is not None:
            if not isinstance(rule, dict) or not isinstance(rule.get("when"), dict):
                out.add("RULE_INVALID", "error", f, ptr + "/rule", "rule is {when: {field, eq}, match, otherwise}", sid)
            else:
                name = rule["when"].get("field")
                fd = fields.get(name)
                if not fd:
                    out.add("RULE_FIELD_UNDECLARED", "error", f, ptr + "/rule/when/field",
                            f"field {name!r} is not declared in project.json", sid)
                elif fd.get("source") not in RULE_SOURCES:
                    out.add("RULE_FIELD_UNTRUSTED", "error", f, ptr + "/rule/when/field",
                            f"{name} comes from '{fd.get('source')}'; rules read only context or state fields", sid)
                elif "eq" not in rule["when"] or not _type_ok(fd, rule["when"]["eq"]):
                    out.add("RULE_VALUE_TYPE", "error", f, ptr + "/rule/when/eq",
                            f"value must be a {fd.get('type')}" + (f" of {fd.get('values')}" if fd.get("values") else ""), sid)
                target(rule.get("match"), ptr + "/rule/match")
                target(rule.get("otherwise"), ptr + "/rule/otherwise")
                if rule.get("match") == rule.get("otherwise") and rule.get("match"):
                    out.add("RULE_SAME_TARGETS", "warning", f, ptr + "/rule", "both branches lead to the same screen", sid)
    elif t == "handler":
        hid = a.get("handlerId")
        hd = (p.get("handlers") or {}).get(hid)
        if not hd:
            out.add("HANDLER_UNKNOWN", "error", f, ptr + "/handlerId", f"handler {hid!r} is not registered in project.json", sid)
        outcomes = a.get("outcomes") or {}
        if not outcomes:
            out.add("HANDLER_OUTCOMES_MISSING", "error", f, ptr + "/outcomes", "map each handler outcome to a screen", sid)
        for k, to in outcomes.items():
            if hd and k not in hd.get("outcomes", []):
                out.add("HANDLER_OUTCOME_UNKNOWN", "error", f, f"{ptr}/outcomes/{k}", f"{hid} has no outcome '{k}'", sid)
            target(to, f"{ptr}/outcomes/{k}")
        for k in (hd or {}).get("outcomes", []):
            if k not in outcomes:
                out.add("HANDLER_OUTCOME_UNMAPPED", "error", f, ptr + "/outcomes", f"outcome '{k}' has no target", sid)
    elif t == "back":
        if a.get("fallback") is None:
            out.add("BACK_FALLBACK_MISSING", "warning", f, ptr + "/fallback",
                    "after a restart there is no history; set a fallback screen", sid)
        else:
            target(a.get("fallback"), ptr + "/fallback")
    elif t == "url":
        if not URL_RE.match(str(a.get("url", ""))):
            out.add("URL_INVALID", "error", f, ptr + "/url", "url must be https://, http:// or tg://", sid)
    elif t == "answer":
        _text_checks(p, f, ptr + "/text", a.get("text"), "regular.plain", sid, out, label=False)
    for name, value in (a.get("set") or {}).items():
        fd = fields.get(name)
        if not fd or fd.get("source") != "state":
            out.add("SET_FIELD_INVALID", "error", f, f"{ptr}/set/{name}", "set writes declared state fields only", sid)
        elif not _type_ok(fd, value):
            out.add("SET_VALUE_TYPE", "error", f, f"{ptr}/set/{name}", f"value must be a {fd.get('type')}", sid)
    icon = a.get("icon")
    if icon is not None:
        eid = icon.get("customEmojiId") if isinstance(icon, dict) else None
        if not isinstance(eid, str) or not CUSTOM_EMOJI_ID.match(eid):
            out.add("CUSTOM_EMOJI_INVALID", "error", f, ptr + "/icon", 'icon is {"customEmojiId": "<digits>"}', sid)
        else:
            out.custom_emoji.append((f, ptr + "/icon", sid))
            out.custom_emoji_ids.append((f, ptr + "/icon", sid, eid, None))
            from .emoji import leading_emoji
            labels = a.get("label") if isinstance(a.get("label"), dict) else {"": a.get("label")}
            for loc, text in labels.items():
                lead = leading_emoji(text)
                if lead:
                    out.add("CUSTOM_EMOJI_DOUBLE_ICON", "warning", f, f"{ptr}/label" + (f"/{loc}" if loc else ""),
                            f"the button has a premium emoji icon and its label also starts with {lead}: users see two "
                            "icons; remove the emoji from the label", sid)
                    break
    if a.get("presentation") not in (None, "edit", "send"):
        out.add("PRESENTATION_INVALID", "error", f, ptr + "/presentation", "presentation is edit or send", sid)
    cb = a.get("callbackData")
    if cb is not None and (not isinstance(cb, str) or not 1 <= len(cb.encode("utf-8")) <= render.CALLBACK_MAX):
        out.add("CALLBACK_DATA_INVALID", "error", f, ptr + "/callbackData", "callback_data is 1-64 UTF-8 bytes", sid)


def _rendered_markup(p: dict, s: dict, sid: str, f: str, out: _Out) -> None:
    """Every locale's keyboard through the skill's keyboard validator (Telegram's own rules)."""
    from .skill import load
    vk = load("validate_keyboard")
    for loc in p.get("locales") or []:
        try:
            markup = render.reply_markup(render.render_screen(p, s, locale=loc))
        except Exception as err:  # malformed screen already reported above
            out.add("RENDER_FAILED", "error", f, "/keyboard", f"cannot render: {err}", sid)
            return
        if not markup or "inline_keyboard" not in markup and "keyboard" not in markup:
            continue
        rep = vk.validate(markup, context=s.get("audience", "private"))
        for e in rep.errors:
            out.add("KEYBOARD_TELEGRAM", "error", f, "/keyboard", f"[{loc}] {e}", sid)


def _custom_emoji(p: dict, snap: Snapshot, out: _Out) -> None:
    """Telegram drops custom emoji from an ineligible bot without an error: say so here."""
    route = (p.get("capabilities") or {}).get("customEmoji", "none")
    if route not in CUSTOM_EMOJI_ROUTES:
        out.add("CUSTOM_EMOJI_ROUTE", "error", "project.json", "/capabilities/customEmoji",
                f"customEmoji is one of {sorted(CUSTOM_EMOJI_ROUTES)}")
        return
    for file, pointer, sid in out.custom_emoji:
        audience = (snap.screens.get(sid) or {}).get("audience", "private")
        if route == "none":
            out.add("CUSTOM_EMOJI_INELIGIBLE", "warning", file, pointer,
                    "capabilities.customEmoji is 'none': Telegram drops custom emoji without an error, users see the "
                    "fallback emoji (text) or no icon (button); set 'fragment' or 'owner_premium' when the bot qualifies",
                    sid)
        elif route == "owner_premium" and audience in ("channel", "inline", "business", "channel_dm"):
            out.add("CUSTOM_EMOJI_CONTEXT", "warning", file, pointer,
                    f"the owner-Premium route covers private, group and supergroup chats, not {audience}", sid)
    _emoji_library(snap, out)


def _emoji_library(snap: Snapshot, out: _Out) -> None:
    """With an emoji library in the project, every custom emoji should come from it."""
    from . import emoji
    if not snap.root or not emoji.has_library(snap.root):
        return
    try:
        idx = emoji.emoji_index(emoji.load_library(snap.root))
    except emoji.EmojiError as err:
        out.add("EMOJI_LIBRARY_INVALID", "error", emoji.LIBRARY, "", err.message)
        return
    for file, pointer, sid, eid, fallback in out.custom_emoji_ids:
        e = idx.get(eid)
        if e is None:
            out.add("CUSTOM_EMOJI_UNKNOWN", "info", file, pointer,
                    f"custom emoji {eid} is not in {emoji.LIBRARY}: nobody checked it exists and the preview cannot draw "
                    "it; import its pack or pick one from the library", sid)
        elif fallback is not None and e["fallback"] and not emoji.same_emoji(fallback, e["fallback"]):
            out.add("CUSTOM_EMOJI_FALLBACK_MISMATCH", "info", file, pointer,
                    f"the fallback {fallback} differs from the pack's emoji {e['fallback']}: users without the custom "
                    "emoji see a different picture", sid)


_EFFECT_KEYS = ("type", "to", "rule", "handlerId", "outcomes", "url", "text", "fallback", "set")


def _same_effect(a: dict, b: dict) -> bool:
    """Old bots reuse one callback_data (\"menu\") on many screens; that is fine when every
    button with it does the same thing."""
    return all(a.get(k) == b.get(k) for k in _EFFECT_KEYS)


def _callbacks(snap: Snapshot, out: _Out) -> None:
    seen: dict[str, tuple[str, str, dict]] = {}
    for sid, s in snap.screens.items():
        if (s.get("keyboard") or {}).get("type") != "inline":
            continue
        for aid, a in (s.get("actions") or {}).items():
            if not isinstance(a, dict) or a.get("type") == "url":
                continue
            cb = render.callback_data(sid, aid, a)
            if cb in seen:
                other_sid, other_aid, other = seen[cb]
                if _same_effect(a, other):
                    out.add("CALLBACK_SHARED", "info", snap.screen_path(sid), f"/actions/{aid}",
                            f"callback_data {cb!r} is shared with {other_sid}/{other_aid}; both do the same", sid)
                else:
                    out.add("CALLBACK_COLLISION", "error", snap.screen_path(sid), f"/actions/{aid}",
                            f"callback_data {cb!r} is also used by {other_sid}/{other_aid} with another effect", sid)
                continue
            seen[cb] = (sid, aid, a)


def _reachability(p: dict, snap: Snapshot, out: _Out) -> None:
    edges: dict[str, set[str]] = {sid: set() for sid in snap.screens}
    for sid, s in snap.screens.items():
        for a in (s.get("actions") or {}).values():
            if isinstance(a, dict):
                edges[sid].update(t for _, t in targets(a))
        inp = s.get("input")
        if isinstance(inp, dict) and isinstance(inp.get("to"), str):
            edges[sid].add(inp["to"])
    todo = [ep.get("screen") for ep in p.get("entryPoints") or [] if isinstance(ep, dict)]
    seen: set[str] = set()
    while todo:
        cur = todo.pop()
        if cur in seen or cur not in edges:
            continue
        seen.add(cur)
        todo.extend(edges[cur])
    for sid in snap.screens:
        if sid not in seen:
            out.add("SCREEN_UNREACHABLE", "warning", snap.screen_path(sid), "",
                    "no entry point, button, handler outcome or input leads here", sid)


def _widget(p: dict, snap: Snapshot, wid: str, w: dict, out: _Out) -> None:
    f = f"widgets/{wid}/widget.json"
    if (err := check_id(wid)):
        out.add("WIDGET_ID_INVALID", "error", f, "/id", err)
    entry = w.get("entry", "index.html")
    if f"widgets/{wid}/{entry}" not in snap.files:
        out.add("WIDGET_ENTRY_MISSING", "error", f, "/entry", f"widgets/{wid}/{entry} does not exist")
    if w.get("caption") is not None:
        _text_checks(p, f, "/caption", w["caption"], "regular.plain", None, out)  # type: ignore[arg-type]
    fb = w.get("fallbackScreen")
    if fb is not None and fb not in snap.screens:
        out.add("WIDGET_FALLBACK_MISSING", "error", f, "/fallbackScreen", f"screen {fb!r} does not exist")


def _scenario(p: dict, snap: Snapshot, name: str, sc: dict, out: _Out) -> None:
    f = next((r for r in snap.files if r.startswith("scenarios/") and r.endswith(f"/{name}.json") or r == f"scenarios/{name}.json"),
             f"scenarios/{name}.json")
    if not isinstance(sc.get("steps"), list):
        out.add("SCENARIO_STEPS", "error", f, "/steps", "a scenario has a list of steps")
    for hid in (sc.get("handlers") or {}):
        if hid not in (p.get("handlers") or {}):
            out.add("SCENARIO_HANDLER_UNKNOWN", "error", f, f"/handlers/{hid}", f"handler {hid!r} is not registered")
    for key, value in (sc.get("context") or {}).items():
        fd = (p.get("fields") or {}).get(key)
        if fd and not _type_ok(fd, value):
            out.add("SCENARIO_VALUE_TYPE", "error", f, f"/context/{key}", f"value must be a {fd.get('type')}")


def summary(diags: list[Diagnostic]) -> dict[str, int]:
    out = {"error": 0, "warning": 0, "info": 0}
    for d in diags:
        out[d.severity] = out.get(d.severity, 0) + 1
    return out
