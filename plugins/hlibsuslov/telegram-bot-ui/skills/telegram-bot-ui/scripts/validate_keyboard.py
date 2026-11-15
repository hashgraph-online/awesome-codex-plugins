#!/usr/bin/env python3
"""Validate Telegram button payloads: inline, reply and rich-message buttons.

Portable: standard library only. Safe: reads local files (or stdin), never
needs a bot token, never touches the network, never sends a message.

Verified against the Bot API on 2026-11-12 (Bot API 10.4).

Accepted input shapes
  * {"inline_keyboard": [[...]], "force_reply"?: bool}      InlineKeyboardMarkup
  * {"keyboard": [[...]], ...}                              ReplyKeyboardMarkup
  * {"force_reply": true, ...}  (no keyboard)               ForceReply
  * {"remove_keyboard": true}                               ReplyKeyboardRemove
  * {"type": "buttons", "buttons": [...]}                   (Input)RichBlockButtons
  * {"blocks": [...]}                                       rich message: every button row
                                                            and inline RichTextButton
  * {"reply_markup": ...} wrapper, or a bare list of rows (= inline)

What is checked (errors -> exit 1)
  * each model's own field set: inline / reply / rich fields are not accepted
    across models (e.g. `callback_data` on a reply button, `request_contact` on
    an inline button, `pay` or `icon_custom_emoji_id` on a rich button)
  * inline + rich buttons: EXACTLY one action field; reply buttons: AT MOST one
  * `disabled` is a DisabledButton object (`{}`) and counts as the action
  * absent vs null vs false vs {}: null is always reported (strip nulls; the
    Bot API does not document null), `disabled: false` / `disabled: true` are
    type errors, `force_reply: false` is a harmless no-op
  * `style`: primary / success / danger (+ "link" for rich callback buttons)
  * `callback_data` 1-64 BYTES; `copy_text.text` 1-256 chars; placeholder 1-64
  * rich button text: plain text, custom emoji and date-time only
  * rich button rows: 1-8 buttons, align left / center / right
  * `pay` / `callback_game` first in the first row (inline only)
  * --previous FILE: an edited inline keyboard must keep `force_reply`
  * --context: fields not available in that context (ephemeral, channel,
    business, channel_dm, group, private)

Warnings (never fail): >1 primary, everything styled, duplicate labels,
emoji-only labels, wide rows, long labels, destructive labels without style,
a keyboard where every button is disabled.

NOT checked: the full schema of nested objects (WebAppInfo, LoginUrl,
SwitchInlineQueryChosenChat, KeyboardButtonRequest*), whether URLs resolve,
whether the bot may use custom emoji, client rendering.

Usage
  python scripts/validate_keyboard.py keyboard.json [--context ephemeral] [--previous old.json]
  python scripts/validate_keyboard.py < keyboard.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):  # pragma: no cover
        pass

STYLES = ("primary", "success", "danger")
RICH_STYLES = STYLES + ("link",)

INLINE_PRESENTATION = ("text", "icon_custom_emoji_id", "style")
INLINE_ACTIONS = ("url", "callback_data", "web_app", "login_url", "switch_inline_query",
                  "switch_inline_query_current_chat", "switch_inline_query_chosen_chat",
                  "copy_text", "callback_game", "pay", "disabled")
REPLY_PRESENTATION = ("text", "icon_custom_emoji_id", "style")
REPLY_ACTIONS = ("request_users", "request_chat", "request_managed_bot", "request_contact",
                 "request_location", "request_poll", "web_app")
RICH_PRESENTATION = ("text", "style")
RICH_ACTIONS = ("url", "callback_data", "web_app", "login_url", "switch_inline_query",
                "switch_inline_query_current_chat", "switch_inline_query_chosen_chat",
                "copy_text", "disabled")

OBJECT_FIELDS = {"web_app", "login_url", "switch_inline_query_chosen_chat", "copy_text",
                 "callback_game", "disabled", "request_users", "request_chat",
                 "request_managed_bot", "request_poll"}
STRING_FIELDS = {"url", "callback_data", "switch_inline_query", "switch_inline_query_current_chat"}
TRUE_FLAGS = {"pay", "request_contact", "request_location"}

INLINE_MARKUP_FIELDS = {"inline_keyboard", "force_reply"}
REPLY_MARKUP_FIELDS = {"keyboard", "is_persistent", "resize_keyboard", "one_time_keyboard",
                       "input_field_placeholder", "selective", "force_reply"}
FORCE_REPLY_FIELDS = {"force_reply", "input_field_placeholder", "selective"}

# context -> fields that are not available there (per the field descriptions)
CONTEXT_BLOCKED = {
    "ephemeral": {"web_app": "web_app isn't supported for ephemeral messages",
                  "login_url": "login_url isn't supported for ephemeral messages"},
    "channel_dm": {k: f"{k} isn't supported in channel direct messages chats" for k in (
        "switch_inline_query", "switch_inline_query_current_chat", "switch_inline_query_chosen_chat")},
    "business": {**{k: f"{k} isn't supported on behalf of a business account" for k in (
        "switch_inline_query", "switch_inline_query_current_chat", "switch_inline_query_chosen_chat")},
        "web_app": "web_app isn't supported on behalf of a business account"},
    "channel": {"switch_inline_query_current_chat": "switch_inline_query_current_chat isn't supported in channels",
                "web_app": "web_app buttons are available only in private chats"},
    "group": {"web_app": "web_app buttons are available only in private chats"},
    "private": {},
}
REPLY_KEYBOARD_BLOCKED = {"channel", "business"}

CUSTOM_EMOJI_ID_RE = re.compile(r"^\d{5,}$")
EMOJI_ONLY_RE = re.compile(r"^[\W_]+$")
MAX_CALLBACK_BYTES = 64
MAX_COPY_TEXT = 256
LONG_LABEL_WARN = 30
WIDE_ROW_WARN = 4
DANGER_WORDS = ("delete", "remove", "reset", "wipe", "unsubscribe", "leave", "log out", "logout",
                "удалить", "сбросить", "отписаться", "выйти", "slett", "slette")


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.kind = "?"
        self.buttons = 0


def _plain_rich_text(rt, where: str, rep: Report) -> str:
    if isinstance(rt, str):
        return rt
    if isinstance(rt, list):
        return "".join(_plain_rich_text(x, where, rep) for x in rt)
    if isinstance(rt, dict):
        t = rt.get("type")
        if t not in ("custom_emoji", "date_time"):
            rep.errors.append(f"{where}: rich button text may contain only plain text, "
                              f"custom emoji and date-time; got {t!r}")
        return str(rt.get("text", ""))
    rep.errors.append(f"{where}: button text must be RichText")
    return ""


def check_button(btn, model: str, where: str, rep: Report, context: str | None,
                 first_cell: bool) -> str:
    rep.buttons += 1
    if model == "reply" and isinstance(btn, str):
        if not btn.strip():
            rep.errors.append(f"{where}: empty button text")
        return btn
    if not isinstance(btn, dict):
        rep.errors.append(f"{where}: expected a button object, got {type(btn).__name__}")
        return ""
    presentation, actions = {
        "inline": (INLINE_PRESENTATION, INLINE_ACTIONS),
        "reply": (REPLY_PRESENTATION, REPLY_ACTIONS),
        "rich": (RICH_PRESENTATION, RICH_ACTIONS),
    }[model]

    for key, value in btn.items():
        if value is None:
            rep.errors.append(f"{where}: '{key}' is null - omit unused optional fields "
                              f"(null is not a documented value)")
    raw_text = btn.get("text")
    text = _plain_rich_text(raw_text, where, rep) if model == "rich" else raw_text
    if not isinstance(text, str) or not text.strip():
        rep.errors.append(f"{where}: 'text' is required and must be non-empty")
        text = ""
    label = f"{where} ('{text}')"

    present = []
    for key, value in btn.items():
        if key in presentation or value is None:
            continue
        if key not in actions:
            owner = [m for m, (_, acts) in (("inline", ("", INLINE_ACTIONS)), ("reply", ("", REPLY_ACTIONS)),
                                            ("rich", ("", RICH_ACTIONS))) if key in acts]
            if key == "icon_custom_emoji_id" and model == "rich":
                owner = ["inline/reply"]
            hint = f" (that field belongs to {'/'.join(owner)} buttons)" if owner else ""
            rep.errors.append(f"{label}: field '{key}' is not valid on a {model} button{hint}")
            continue
        if key in TRUE_FLAGS:
            if value is True:
                present.append(key)
            elif value is not False:
                rep.errors.append(f"{label}: '{key}' must be a boolean")
            elif key == "pay":
                rep.errors.append(f"{label}: 'pay' must be true to make a Pay button")
            continue
        if key in OBJECT_FIELDS and not isinstance(value, dict):
            hint = " - use {} (a DisabledButton object)" if key == "disabled" else ""
            rep.errors.append(f"{label}: '{key}' must be an object, got {json.dumps(value)}{hint}")
            continue
        if key in STRING_FIELDS and not isinstance(value, str):
            rep.errors.append(f"{label}: '{key}' must be a string")
            continue
        present.append(key)

    if model in ("inline", "rich") and len(present) != 1:
        extra = " - a disabled button has no other action" if "disabled" in present else ""
        rep.errors.append(f"{label}: needs EXACTLY one action field, found {len(present)} {present}{extra}")
    if model == "reply" and len(present) > 1:
        rep.errors.append(f"{label}: reply buttons allow AT MOST one non-text field, found {present}")

    style = btn.get("style")
    allowed = RICH_STYLES if model == "rich" else STYLES
    if style is not None and style not in allowed:
        rep.errors.append(f"{label}: style must be one of {'/'.join(allowed)}; got {style!r}")
    if model == "rich" and style == "link" and "callback_data" not in present:
        rep.errors.append(f"{label}: style 'link' is allowed only for callback buttons")

    cb = btn.get("callback_data")
    if isinstance(cb, str):
        n = len(cb.encode("utf-8"))
        if not 1 <= n <= MAX_CALLBACK_BYTES:
            rep.errors.append(f"{label}: callback_data is {n} bytes (allowed 1-{MAX_CALLBACK_BYTES})")
        elif not cb.isascii():
            rep.warnings.append(f"{label}: non-ASCII callback_data spends {n} bytes for {len(cb)} characters")
    ct = btn.get("copy_text")
    if isinstance(ct, dict):
        v = ct.get("text")
        if not isinstance(v, str) or not 1 <= len(v) <= MAX_COPY_TEXT:
            rep.errors.append(f"{label}: copy_text.text must be 1-{MAX_COPY_TEXT} characters")
    icon = btn.get("icon_custom_emoji_id")
    if icon is not None and model != "rich" and (not isinstance(icon, str) or not CUSTOM_EMOJI_ID_RE.match(icon)):
        rep.errors.append(f"{label}: icon_custom_emoji_id must be the numeric id string of a custom "
                          f"emoji - not a file_id, pack name, URL, or Unicode emoji; got {icon!r}")
    if model == "inline":
        for key in ("pay", "callback_game"):
            if key in present and not first_cell:
                rep.errors.append(f"{label}: a '{key}' button must be the first button in the first row")
    if context:
        for key in present:
            reason = CONTEXT_BLOCKED.get(context, {}).get(key)
            if reason:
                rep.errors.append(f"{label}: {reason}")

    if text and EMOJI_ONLY_RE.match(text.strip()):
        rep.warnings.append(f"{where}: label {text!r} has no words - add text next to the emoji")
    if len(text) > LONG_LABEL_WARN:
        rep.warnings.append(f"{where}: label is {len(text)} chars; it may truncate (check the longest locale)")
    if style is None and present != ["disabled"] and any(w in text.lower() for w in DANGER_WORDS):
        rep.warnings.append(f"{where}: {text!r} looks destructive but has no style - consider "
                            f"'danger' plus a confirmation step")
    return text


def check_rows(rows, model: str, rep: Report, context: str | None, prefix: str = "") -> None:
    if not isinstance(rows, list) or not rows:
        rep.errors.append(f"{prefix}keyboard has no rows")
        return
    labels: list[str] = []
    styles: list[str | None] = []
    disabled = 0
    for r, row in enumerate(rows):
        if not isinstance(row, list):
            rep.errors.append(f"{prefix}row {r + 1}: expected a list of buttons")
            continue
        if len(row) > WIDE_ROW_WARN:
            rep.warnings.append(f"{prefix}row {r + 1}: {len(row)} buttons in one row - labels may truncate")
        for col, btn in enumerate(row):
            labels.append(check_button(btn, model, f"{prefix}row {r + 1}, button {col + 1}", rep, context,
                                       r == 0 and col == 0).strip().lower())
            if isinstance(btn, dict):
                styles.append(btn.get("style"))
                disabled += isinstance(btn.get("disabled"), dict)
    _summary_warnings(labels, styles, disabled, rep, prefix)


def _summary_warnings(labels, styles, disabled, rep: Report, prefix: str) -> None:
    if styles.count("primary") > 1:
        rep.warnings.append(f"{prefix}{styles.count('primary')} 'primary' buttons - a screen should have at most one")
    if len(styles) > 1 and all(s for s in styles):
        rep.warnings.append(f"{prefix}every button is styled - with no neutral buttons there is no hierarchy")
    if labels and disabled == len(labels):
        rep.warnings.append(f"{prefix}every button is disabled - say what the user can do next, or remove the keyboard")
    for d in sorted({x for x in labels if x and labels.count(x) > 1}):
        rep.warnings.append(f"{prefix}duplicate label in one keyboard: {d!r}")


def _check_flag(doc: dict, key: str, rep: Report) -> None:
    if key in doc and doc[key] is None:
        rep.errors.append(f"markup: '{key}' is null - omit it or pass a boolean")
    elif key in doc and not isinstance(doc[key], bool):
        rep.errors.append(f"markup: '{key}' must be a boolean")


def _rich_rows(blocks, path: str, out: list) -> None:
    """Collect button rows and inline RichTextButtons from a rich message."""
    if isinstance(blocks, dict):
        if blocks.get("type") == "buttons":
            out.append((path, blocks))
        if blocks.get("type") == "button" and "button" in blocks:
            out.append((path, {"type": "buttons", "buttons": [blocks["button"]], "_inline": True}))
        for k, v in blocks.items():
            if isinstance(v, (list, dict)) and k != "buttons":
                _rich_rows(v, f"{path}.{k}", out)
    elif isinstance(blocks, list):
        for i, b in enumerate(blocks):
            _rich_rows(b, f"{path}[{i}]", out)


def check_rich_row(block: dict, rep: Report, context: str | None, where: str) -> None:
    buttons = block.get("buttons")
    if not isinstance(buttons, list) or not (1 <= len(buttons) <= 8 or block.get("_inline")):
        rep.errors.append(f"{where}: a button row needs 1-8 buttons")
        buttons = buttons if isinstance(buttons, list) else []
    align = block.get("align")
    if align is not None and align not in ("left", "center", "right"):
        rep.errors.append(f"{where}: align must be left, center or right")
    labels, styles = [], []
    for i, b in enumerate(buttons):
        labels.append(check_button(b, "rich", f"{where} button {i + 1}", rep, context, False).strip().lower())
        if isinstance(b, dict):
            styles.append(b.get("style"))
    _summary_warnings(labels, styles, sum(isinstance(b, dict) and isinstance(b.get("disabled"), dict)
                                          for b in buttons), rep, f"{where}: ")


def validate(doc, *, context: str | None = None, previous=None) -> Report:
    rep = Report()
    if isinstance(doc, dict) and "reply_markup" in doc:
        doc = doc["reply_markup"]
    if isinstance(doc, list):
        doc = {"inline_keyboard": doc}
    if not isinstance(doc, dict):
        rep.errors.append("expected an object or a list of rows")
        return rep
    if "inline_keyboard" in doc:
        rep.kind = "inline"
        for k in doc:
            if k not in INLINE_MARKUP_FIELDS:
                rep.errors.append(f"markup: '{k}' is not a field of InlineKeyboardMarkup")
        _check_flag(doc, "force_reply", rep)
        check_rows(doc["inline_keyboard"], "inline", rep, context)
        if previous is not None:
            prev = previous.get("reply_markup", previous) if isinstance(previous, dict) else {}
            if bool(prev.get("force_reply")) != bool(doc.get("force_reply")):
                rep.errors.append("edit: InlineKeyboardMarkup.force_reply can't be changed when the inline "
                                  "keyboard is edited - send a new message or keep the original value")
    elif "keyboard" in doc:
        rep.kind = "reply"
        for k in doc:
            if k not in REPLY_MARKUP_FIELDS:
                rep.errors.append(f"markup: '{k}' is not a field of ReplyKeyboardMarkup")
        for flag in ("force_reply", "is_persistent", "resize_keyboard", "one_time_keyboard", "selective"):
            _check_flag(doc, flag, rep)
        ph = doc.get("input_field_placeholder")
        if ph is not None and (not isinstance(ph, str) or not 1 <= len(ph) <= 64):
            rep.errors.append("markup: input_field_placeholder must be 1-64 characters")
        if context in REPLY_KEYBOARD_BLOCKED:
            rep.errors.append(f"markup: reply keyboards aren't supported in {context} messages")
        check_rows(doc["keyboard"], "reply", rep, context)
    elif doc.get("type") == "buttons":
        rep.kind = "rich"
        check_rich_row(doc, rep, context, "buttons")
    elif "blocks" in doc:
        rep.kind = "rich"
        rows: list = []
        _rich_rows(doc["blocks"], "blocks", rows)
        if not rows:
            rep.warnings.append("rich message has no buttons")
        for path, block in rows:
            check_rich_row(block, rep, context, path)
    elif "remove_keyboard" in doc:
        rep.kind = "remove"
        if doc.get("remove_keyboard") is not True:
            rep.errors.append("ReplyKeyboardRemove: remove_keyboard must be true")
    elif "force_reply" in doc:
        rep.kind = "force_reply"
        for k in doc:
            if k not in FORCE_REPLY_FIELDS:
                rep.errors.append(f"markup: '{k}' is not a field of ForceReply")
        if doc.get("force_reply") is not True:
            rep.errors.append("ForceReply: force_reply must be true (False shows nothing - "
                              "omit reply_markup instead)")
        if context == "channel":
            rep.errors.append("ForceReply isn't supported in channels")
        ph = doc.get("input_field_placeholder")
        if ph is not None and (not isinstance(ph, str) or not 1 <= len(ph) <= 64):
            rep.errors.append("ForceReply: input_field_placeholder must be 1-64 characters")
    else:
        rep.errors.append("unrecognised markup: expected inline_keyboard, keyboard, force_reply, "
                          "remove_keyboard, a rich 'buttons' block or rich 'blocks'")
    return rep


def _load(path: str | None):
    raw = sys.stdin.read() if path is None else open(path, "r", encoding="utf-8").read()
    return json.loads(raw)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("file", nargs="?")
    ap.add_argument("--context", choices=sorted(CONTEXT_BLOCKED))
    ap.add_argument("--previous", help="markup the message had before this edit")
    args = ap.parse_args(argv)
    try:
        doc = _load(args.file)
        prev = _load(args.previous) if args.previous else None
    except (OSError, ValueError) as exc:
        print(f"FAIL: {exc}")
        return 1
    rep = validate(doc, context=args.context, previous=prev)
    for w in rep.warnings:
        print(f"WARN: {w}")
    for e in rep.errors:
        print(f"FAIL: {e}")
    if rep.errors:
        print(f"\n{len(rep.errors)} error(s), {len(rep.warnings)} warning(s). INVALID ({rep.kind}).")
        return 1
    print(f"\nOK: {rep.kind} markup structurally valid ({rep.buttons} button(s)). "
          f"{len(rep.warnings)} warning(s). Partial check - see the docstring for what is not checked.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
