#!/usr/bin/env python3
"""Check a welcome spec: what a bot sends after /start, one scenario per entry point.

Standard library only; reads local files, never needs a token, never sends.

  py -3 scripts/validate_welcome.py bot-ui/welcome.json
  py -3 scripts/validate_welcome.py --json examples/welcome/coffee-shop.json

Format and the reasons behind every rule: references/welcome-message.md (section 10).
Every request goes through validate_payload, every reply_markup through validate_keyboard;
on top of that the welcome rules below. Errors exit 1; warnings and notes don't.

  errors    WELCOME_NO_NEW, WELCOME_SPLIT, WELCOME_ALBUM, WELCOME_ASKS_DATA, CAPTION_TOO_LONG,
            TEXT_TOO_LONG, EDIT_TEXT_ON_MEDIA, EDIT_CAPTION_ON_TEXT, EFFECT_NOT_PRIVATE
  warnings  WELCOME_NO_RETURNING, WELCOME_LANGUAGE_UNCOVERED, RETURNING_REPEATS_WELCOME,
            WELCOME_PICKER_STACKED, WELCOME_NO_ACTION, WELCOME_MENU_DUMP, WELCOME_LONG,
            FIRST_LINE_LONG, WELCOME_FILLER, WELCOME_EMOJI, STRAY_PREVIEW, WELCOME_SETUP_CALL,
            GROUP_ONBOARDING, HOME_SPLIT
  notes     WELCOME_NO_PRIMARY, MEDIA_NOT_CACHED
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import validate_keyboard  # noqa: E402
import validate_payload  # noqa: E402

MEDIA_SENDS = {"sendPhoto": "photo", "sendAnimation": "animation", "sendVideo": "video", "sendDocument": "document",
               "sendLivePhoto": "live_photo", "sendAudio": "audio", "sendVoice": "voice"}
NOT_MESSAGES = {"sendChatAction", "sendMessageDraft", "sendRichMessageDraft"}
OTHER_SENDS = {"copyMessage", "forwardMessage", "copyMessages", "forwardMessages"}
SETUP_CALLS = {"setMyCommands", "deleteMyCommands", "setMyDescription", "setMyShortDescription", "setMyName",
               "setChatMenuButton", "setMySettings", "setMyDefaultAdministratorRights"}
GROUP_CHATS = {"group", "supergroup"}
CAPTION_MAX, TEXT_MAX = 1024, 4096  # [API] characters after entity parsing
LINES_MAX, VISIBLE_MAX, FIRST_LINE_MAX, BUTTONS_MAX, EMOJI_MAX = 7, 600, 80, 6, 3  # heuristics, see the reference

TAG = re.compile(r"<[^>]+>")
URL = re.compile(r"https?://|\bt\.me/|\bwww\.", re.I)
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿⬀-⯿]")
INPUT_CUE = re.compile(r"\b(send|write|type|paste)\b|напиш|пришл|отправ|надішл|введ|вставт|вставь", re.I)
FILLER = [
    (re.compile(r"!{2,}"), "'!!'"),
    (re.compile(r"👇"), "a pointing-down emoji at the buttons"),
    (re.compile(r"\b(choose|select) an? (option|action|item)\b", re.I), "'choose an option'"),
    (re.compile(r"выберите (действие|пункт|опцию|вариант)", re.I), "'выберите действие'"),
    (re.compile(r"оберіть (дію|пункт|опцію|варіант)", re.I), "'оберіть дію'"),
    (re.compile(r"\bi(?: am|'m) (?:a|an|your) (?:\w+ )?bot\b", re.I), "'I am a bot'"),
    (re.compile(r"(?<!\w)я\s*[—–-]?\s*(?:ваш\s+|твой\s+|твій\s+)?(?:\w+\s+)?бот(?!\w)", re.I), "'я бот'"),
    (re.compile(r"dear user|уважаем\w* пользовател|шановн\w* користувач", re.I), "'dear user'"),
    (re.compile(r"(press|нажмите|натисніть|тисни|жми)\s+/help", re.I), "'press /help'"),
    (re.compile(r"\bbest bot\b|лучш\w* бот|найкращ\w* бот", re.I), "'the best bot'"),
]


def visible(text: str, parse_mode: str | None) -> str:
    """The text a reader sees, near enough for budgets: HTML tags dropped, entities decoded."""
    mode = (parse_mode or "").lower()
    if mode == "html":
        return html.unescape(TAG.sub("", text))
    if mode.startswith("markdown"):
        return re.sub(r"\\(.)", r"\1", re.sub(r"[*_~`|]|\[([^\]]*)\]\([^)]*\)", lambda m: m.group(1) or "", text))
    return text


def utf16_len(text: str) -> int:
    return len(text.encode("utf-16-le")) // 2


def message_of(method: str, params: dict) -> dict | None:
    """{kind, text, mode, markup, field} for a send or edit that shows a screen; None otherwise."""
    if method in MEDIA_SENDS:
        return {"kind": "media", "text": params.get("caption", ""), "mode": params.get("parse_mode"),
                "markup": params.get("reply_markup"), "field": "caption", "media": params.get(MEDIA_SENDS[method])}
    if method in ("sendMessage", "editMessageText"):
        return {"kind": "text", "text": params.get("text", ""), "mode": params.get("parse_mode"),
                "markup": params.get("reply_markup"), "field": "text"}
    if method == "editMessageMedia":
        media = params.get("media") if isinstance(params.get("media"), dict) else {}
        return {"kind": "media", "text": media.get("caption", ""), "mode": media.get("parse_mode"),
                "markup": params.get("reply_markup"), "field": "caption", "media": media.get("media")}
    if method == "editMessageCaption":
        return {"kind": "media", "text": params.get("caption", ""), "mode": params.get("parse_mode"),
                "markup": params.get("reply_markup"), "field": "caption"}
    if method == "sendRichMessage":
        return {"kind": "rich", "text": "", "mode": None, "markup": params.get("reply_markup"), "field": "rich"}
    return None


def is_send(method: str) -> bool:
    return (method.startswith("send") and method not in NOT_MESSAGES) or method in OTHER_SENDS


def buttons(markup) -> list[dict]:
    if not isinstance(markup, dict):
        return []
    rows = markup.get("inline_keyboard") or markup.get("keyboard") or []
    return [b if isinstance(b, dict) else {"text": b} for row in rows if isinstance(row, list) for b in row]


class Checker:
    def __init__(self) -> None:
        self.payload = validate_payload.Validator(validate_payload.load_catalog(validate_payload.DATA_DIR))
        self.found: list[dict] = []

    def add(self, level: str, code: str, where: str, message: str) -> None:
        self.found.append({"level": level, "code": code, "where": where, "message": message})

    # ------------------------------------------------------------ one screen
    def screen(self, msg: dict, where: str, first_run: bool, private: bool) -> None:
        text = msg["text"] if isinstance(msg["text"], str) else ""
        seen = visible(text, msg["mode"])
        limit = CAPTION_MAX if msg["field"] == "caption" else TEXT_MAX
        if utf16_len(seen) > limit:
            code = "CAPTION_TOO_LONG" if msg["field"] == "caption" else "TEXT_TOO_LONG"
            self.add("error", code, where, f"{msg['field']} is {utf16_len(seen)} characters, the limit is {limit}")
        lines = [ln.strip() for ln in seen.splitlines() if ln.strip()]
        if len(lines) > LINES_MAX or len(seen) > VISIBLE_MAX:
            self.add("warning", "WELCOME_LONG", where, f"{len(lines)} lines, {len(seen)} visible characters: "
                     f"keep the welcome to title, value, how it works and one promise (<= {LINES_MAX} lines)")
        if lines and len(lines[0]) > FIRST_LINE_MAX:
            self.add("warning", "FIRST_LINE_LONG", where, f"first line is {len(lines[0])} characters; "
                     f"notification and chat-list previews cut at about {FIRST_LINE_MAX}")
        for pattern, label in FILLER:
            if pattern.search(seen):
                self.add("warning", "WELCOME_FILLER", where, f"filler {label}: say what the user gets instead")
        if len(EMOJI.findall(seen)) > EMOJI_MAX:
            self.add("warning", "WELCOME_EMOJI", where, f"{len(EMOJI.findall(seen))} emoji: at most 1-2, as anchors")
        if msg["field"] == "text" and URL.search(text) and "link_preview_options" not in msg.get("params", {}):
            self.add("warning", "STRAY_PREVIEW", where, "a link in the text with no link_preview_options: its "
                     "preview takes over the welcome; set is_disabled or choose the preview on purpose")
        media = msg.get("media")
        if isinstance(media, str) and re.match(r"https?://|attach://", media):
            self.add("note", "MEDIA_NOT_CACHED", where, "media sent by URL or upload: send it once, store the "
                     "file_id and reuse it so the welcome arrives instantly")
        markup = msg["markup"]
        if markup is not None:
            rep = validate_keyboard.validate(markup)
            for e in rep.errors:
                self.add("error", "KEYBOARD", where, e)
            for w in rep.warnings:
                self.add("warning", "KEYBOARD", where, w)
        btns = buttons(markup)
        if not first_run or not private:
            return
        if not btns and not INPUT_CUE.search(seen):
            self.add("warning", "WELCOME_NO_ACTION", where, "no buttons and no 'send / write …' cue: the first "
                     "message must offer the next step")
        if len(btns) > BUTTONS_MAX:
            self.add("warning", "WELCOME_MENU_DUMP", where, f"{len(btns)} buttons: one primary and 1-3 secondary "
                     "actions; the rest lives in the menu")
        if btns and isinstance(markup, dict) and "inline_keyboard" in markup and not first_run_picker(msg) and \
                not any(b.get("style") == "primary" for b in btns):
            self.add("note", "WELCOME_NO_PRIMARY", where, "no style 'primary': mark the first useful result")

    # ------------------------------------------------------------ one scenario
    def scenario(self, sc: dict, index: int) -> dict | None:
        sid = sc.get("id") or f"#{index}"
        steps = sc.get("steps") if isinstance(sc.get("steps"), list) else []
        if not steps:
            self.add("error", "SPEC", sid, "a scenario needs steps")
            return None
        user = sc.get("user", "new")
        chat = sc.get("chat", "private")
        private = chat not in GROUP_CHATS
        first: dict | None = None
        anchor: str | None = None
        immediate_sends = 0
        group_link = False
        for i, step in enumerate(steps):
            where = f"{sid}/step {i + 1}"
            if not isinstance(step, dict) or not isinstance(step.get("method"), str):
                self.add("error", "SPEC", where, "a step is {method, params[, on]}")
                continue
            method, params = step["method"], step.get("params") if isinstance(step.get("params"), dict) else {}
            immediate = "on" not in step
            rep = self.payload.check_request(method, params)
            for e in rep.errors:
                self.add("error", "PAYLOAD", where, e)
            for w in rep.warnings:
                self.add("warning", "PAYLOAD", where, w)
            if method in SETUP_CALLS:
                self.add("warning", "WELCOME_SETUP_CALL", where, f"{method} belongs to deploy, per language, "
                         "not to the /start handler")
            if "message_effect_id" in params and not private:
                self.add("error", "EFFECT_NOT_PRIVATE", where, "message_effect_id works in private chats only")
            if method == "sendMediaGroup" and immediate:
                self.add("error", "WELCOME_ALBUM", where, "an album can't carry buttons: open with one photo")
            if params.get("ephemeral_message_parameters") is not None:
                group_link = True
            for b in buttons(params.get("reply_markup")):
                if b.get("request_contact") or b.get("request_location"):
                    if immediate and user == "new":
                        self.add("error", "WELCOME_ASKS_DATA", where, "the first message asks for a phone or "
                                 "location: ask at the moment of need, with a Skip")
                if isinstance(b.get("url"), str) and "start=" in b["url"]:
                    group_link = True
            if method.startswith("edit") and anchor:
                if method == "editMessageText" and anchor == "media":
                    self.add("error", "EDIT_TEXT_ON_MEDIA", where, "editMessageText edits text, rich and game "
                             "messages only; edit the caption or the media, or send a new message")
                if method == "editMessageCaption" and anchor == "text":
                    self.add("error", "EDIT_CAPTION_ON_TEXT", where, "a text message has no caption: use "
                             "editMessageText, or editMessageMedia to add a picture")
            msg = message_of(method, params)
            if msg is not None:
                msg["params"] = params
                if is_send(method) or method == "editMessageMedia":
                    anchor = msg["kind"]
                self.screen(msg, where, first_run=(user == "new"), private=private)
                if first is None or (first_run_picker(first) and not immediate):
                    first = msg  # the welcome is the picker's replacement when there is a picker
            if is_send(method) and immediate:
                immediate_sends += 1
        if immediate_sends > 1 and private:
            code, level = ("WELCOME_SPLIT", "error") if user == "new" else ("HOME_SPLIT", "warning")
            self.add(level, code, sid, f"{immediate_sends} messages before the user taps anything: media, text "
                     "and buttons go in one message")
        if not private and not group_link:
            self.add("warning", "GROUP_ONBOARDING", sid, "a group entry without a t.me/<bot>?start= button or "
                     "an ephemeral reply: personal onboarding belongs in the private chat")
        return first

    # ------------------------------------------------------------ the spec
    def spec(self, doc) -> None:
        if not isinstance(doc, dict) or doc.get("kind") != "welcome-spec":
            self.add("error", "SPEC", "spec", 'not a welcome spec: expected {"kind": "welcome-spec", "scenarios": [...]}')
            return
        scenarios = [s for s in doc.get("scenarios", []) if isinstance(s, dict)] \
            if isinstance(doc.get("scenarios"), list) else []
        languages = [x for x in doc.get("languages", []) if isinstance(x, str)] \
            if isinstance(doc.get("languages"), list) else []
        firsts = {}
        for i, sc in enumerate(scenarios):
            firsts[sc.get("id") or f"#{i}"] = (sc, self.scenario(sc, i))
        private = [(sc, m) for sc, m in firsts.values() if sc.get("chat", "private") not in GROUP_CHATS]
        new = [(sc, m) for sc, m in private if sc.get("user", "new") == "new"]
        returning = [(sc, m) for sc, m in private if sc.get("user") == "returning"]
        if not new:
            self.add("error", "WELCOME_NO_NEW", "spec", "no scenario for a new user in the private chat")
        if not returning:
            self.add("warning", "WELCOME_NO_RETURNING", "spec", "no returning-user scenario: what does the "
                     "second /start show?")
        uncovered = [sc for sc, _ in new if "language_code" in sc and sc["language_code"] not in languages]
        if len(languages) > 1 and not uncovered:
            self.add("warning", "WELCOME_LANGUAGE_UNCOVERED", "spec", f"{len(languages)} languages, but no scenario "
                     "for a missing or unsupported language_code (language_code null or another code)")
        for sc in uncovered:
            if any(isinstance(s, dict) and "on" in s and is_send(str(s.get("method", ""))) for s in sc["steps"]):
                self.add("warning", "WELCOME_PICKER_STACKED", sc.get("id", "?"), "the welcome after the language "
                         "pick is a new message: replace the picker (editMessageMedia / editMessageText)")
        plain_new = [m for sc, m in new if m and sc.get("entry", "/start").strip() == "/start"]
        for sc, m in returning:
            if m and plain_new and _norm(m) == _norm(plain_new[0]):
                self.add("warning", "RETURNING_REPEATS_WELCOME", sc.get("id", "?"), "returning users get the same "
                         "welcome: show home with their live object instead")


def first_run_picker(msg: dict) -> bool:
    """A text screen whose buttons all carry a language callback: the picker that the welcome replaces."""
    btns = buttons(msg.get("markup"))
    return msg["kind"] == "text" and bool(btns) and all(
        str(b.get("callback_data", "")).startswith(("lang", "language")) for b in btns)


def _norm(msg: dict) -> str:
    return re.sub(r"\s+", " ", visible(msg.get("text") or "", msg.get("mode"))).strip().lower()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("file")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    checker = Checker()
    try:
        with open(args.file, encoding="utf-8") as fh:
            checker.spec(json.load(fh))
    except (OSError, ValueError) as exc:
        checker.add("error", "SPEC", args.file, str(exc))
    found = checker.found
    counts = {lvl: sum(f["level"] == lvl for f in found) for lvl in ("error", "warning", "note")}
    if args.json:
        print(json.dumps({"file": args.file, "counts": counts, "findings": found}, ensure_ascii=False, indent=2))
    else:
        tag = {"error": "ERROR", "warning": "WARN", "note": "NOTE"}
        for f in found:
            print(f"{tag[f['level']]}: {f['code']} {f['where']}: {f['message']}")
        print(f"{counts['error']} error(s), {counts['warning']} warning(s), {counts['note']} note(s)")
    return 1 if counts["error"] else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
