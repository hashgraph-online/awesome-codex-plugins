#!/usr/bin/env python3
"""Research a bot project's style and check the bot's style profile. Offline, stdlib only.

  probe <project-root> [--json]   find SDK, design docs, tokens, fonts, brand assets, locale
                                  catalogs (languages, longest strings, emoji density, ты/вы),
                                  and Telegram touchpoints. Reports where to look; judges nothing.
  scaffold <probe.json>           print a starting profile: skill defaults plus what the probe
                                  found, each found value listed in `sources`.
  check <profile.json>            errors: Telegram API limits, contradictions with the skill's
                                  rules, unknown keys; warnings: values outside usual ranges and
                                  knobs without a source.

Safety: never opens `.env*`, key, certificate or credential files, or anything in dependency,
build and VCS folders; reads at most 512 KB per file; never uses the network or a bot token.
Knobs and their meaning: references/bot-style-profile.md. Process:
references/redesign-orchestration.md.
"""
# run-checks: check skills/telegram-bot-ui/examples/style-profile/profile.example.json
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

MAX_BYTES = 512 * 1024
MAX_FILES = 20000
SAMPLES = 5

SKIP_DIRS = {".git", ".hg", ".svn", "node_modules", ".venv", "venv", "env", "__pycache__", "dist",
             "build", "out", ".next", ".nuxt", ".turbo", ".cache", "coverage", "target", "vendor",
             ".claude", ".idea", ".vscode", ".pytest_cache", ".mypy_cache", "bower_components"}
SECRET_NAME = re.compile(r"(^\.env)|(\.(pem|key|p12|pfx|crt|cer|keystore|jks)$)|secret|credential|"
                         r"^id_(rsa|ed25519|ecdsa)|^auth\.json$|^\.npmrc$|^\.pypirc$|^\.netrc$", re.I)

CODE_EXT = {".py", ".ts", ".tsx", ".js", ".mjs", ".cjs", ".go", ".java", ".kt", ".cs", ".php", ".rb",
            ".rs", ".swift", ".dart"}
STYLE_EXT = {".css", ".scss", ".sass", ".less", ".pcss"}
IMAGE_EXT = {".svg", ".png", ".jpg", ".jpeg", ".webp"}
LOCALE_EXT = {".json", ".yaml", ".yml", ".ftl", ".po"}
LOCALE_DIRS = {"locales", "locale", "i18n", "lang", "langs", "translations", "messages", "l10n"}
LANG_RE = re.compile(r"^([a-z]{2,3})([-_][A-Za-z]{2,4})?$")

SDKS = {
    "grammy": "grammY", "telegraf": "Telegraf", "node-telegram-bot-api": "node-telegram-bot-api",
    "gramio": "GramIO", "puregram": "puregram", "@telegraf/types": "Telegraf types",
    "aiogram": "aiogram", "python-telegram-bot": "python-telegram-bot",
    "pytelegrambotapi": "pyTelegramBotAPI", "pyrogram": "Pyrogram", "telethon": "Telethon (MTProto)",
    "github.com/go-telegram/bot": "go-telegram/bot",
    "github.com/go-telegram-bot-api/telegram-bot-api": "telegram-bot-api (Go)",
    "gopkg.in/telebot": "telebot (Go)", "telegram.bot": "Telegram.Bot",
    "irazasyed/telegram-bot-sdk": "telegram-bot-sdk (PHP)", "teloxide": "teloxide",
    "frankenstein": "frankenstein", "org.telegram:telegrambots": "TelegramBots (Java)",
}
MINI_APP = re.compile(r"telegram-web-app\.js|@twa-dev/sdk|@telegram-apps/sdk|Telegram\.WebApp")

TOUCHPOINTS = {
    "inline_keyboards": r"InlineKeyboard|inline_keyboard|Markup\.inlineKeyboard|InlineKeyboardBuilder",
    "reply_keyboards": r"ReplyKeyboard|KeyboardButton\b|resize_keyboard|ReplyKeyboardBuilder",
    "callback_data": r"callback_data|callbackData|\.callbackQuery\(|CallbackData",
    "commands": r"setMyCommands|set_my_commands|BotCommand\b",
    "menu_button": r"setChatMenuButton|set_chat_menu_button|MenuButton",
    "bot_profile": r"setMyName|setMyDescription|setMyShortDescription|setMyProfilePhoto|"
                   r"set_my_(name|description|short_description|profile_photo)",
    "web_app_buttons": r"web_app|WebAppInfo|webApp\(",
    "button_style": r"""["']?style["']?\s*[:=]\s*["'](primary|success|danger)["']""",
    "custom_emoji": r"icon_custom_emoji_id|custom_emoji_id|<tg-emoji",
    "parse_mode_html": r"""parse_mode\s*[:=]\s*["']?HTML|ParseMode\.HTML""",
    "parse_mode_markdown": r"""parse_mode\s*[:=]\s*["']?Markdown|ParseMode\.MARKDOWN""",
    "rich_messages": r"sendRichMessage|send_rich_message|InputRichMessage",
    "drafts": r"sendMessageDraft|sendRichMessageDraft|send_message_draft",
    "widgets": r"sendWidget|sendSharedWidget|answerWidgetQuery|send_widget",
    "edits_in_place": r"editMessageText|edit_message_text|editMessageReplyMarkup|\.edit_text\(",
    "chat_actions": r"sendChatAction|send_chat_action|replyWithChatAction",
}
TOUCH_RE = {k: re.compile(v) for k, v in TOUCHPOINTS.items()}

CSS_VAR = re.compile(r"(--[A-Za-z0-9_-]+)\s*:\s*([^;{}]+);")
TOKEN_NAME = re.compile(r"color|primary|accent|brand|background|foreground|\bbg\b|-bg|surface|"
                        r"radius|font|text|muted|destructive|success|warning", re.I)
HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b")
FONT_FAMILY = re.compile(r"font-family\s*:\s*([^;}<\n]+)[;}]", re.I)
NEXT_FONT = re.compile(r"""import\s*\{([^}]+)\}\s*from\s*["']next/font/(google|local)["']""")
DESIGN_DOC = re.compile(r"^(design|design[-_]system|brand|brandbook|style[-_]?guide|tone[-_]of[-_]voice|"
                        r"voice|ui[-_]guidelines)[^/]*\.(md|mdx|txt)$", re.I)
BRAND_ASSET = re.compile(r"logo|brand|avatar|mascot|wordmark", re.I)
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿⬀-⯿]")
BUTTON_KEY = re.compile(r"(^|[._])(btn|button|kb|key|action)s?([._]|$)", re.I)
ADDRESS = {
    "ru": {"formal": re.compile(r"\b(вы|вас|вам|ваш\w*|вами)\b", re.I),
           "informal": re.compile(r"\b(ты|тебя|тебе|твой|твоя|твоё|твои|тобой)\b", re.I)},
    "uk": {"formal": re.compile(r"\b(ви|вас|вам|ваш\w*|вами)\b", re.I),
           "informal": re.compile(r"\b(ти|тебе|тобі|твій|твоя|твоє|твої|тобою)\b", re.I)},
}


# ---------------------------------------------------------------- probe

def _is_secret(name: str) -> bool:
    return bool(SECRET_NAME.search(name))


def _read(path: str) -> str | None:
    try:
        if os.path.getsize(path) > MAX_BYTES:
            return None
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return None


def _walk(root: str, skipped: list):
    """Yield readable project files; count secret-like names in `skipped[0]` without opening them."""
    count = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS and not _is_secret(d))
        for name in sorted(filenames):
            if _is_secret(name):
                skipped[0] += 1
                continue
            count += 1
            if count > MAX_FILES:
                return
            yield os.path.join(dirpath, name)


def _rel(root: str, path: str) -> str:
    return os.path.relpath(path, root).replace(os.sep, "/")


def _flatten(obj, prefix=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _flatten(v, f"{prefix}.{k}" if prefix else str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _flatten(v, f"{prefix}[{i}]")
    elif isinstance(obj, str):
        yield prefix, obj


def _locale_strings(path: str, text: str):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".json":
        try:
            return list(_flatten(json.loads(text)))
        except ValueError:
            return []
    if ext == ".ftl":
        return re.findall(r"^([A-Za-z][\w-]*)\s*=\s*(.+)$", text, re.M)
    if ext == ".po":
        return [(k, v) for k, v in re.findall(r'^msgid\s+"(.*)"\s*\nmsgstr\s+"(.*)"', text, re.M) if k and v]
    return [(k, v.strip("'\"")) for k, v in re.findall(r"^\s*([\w.-]+)\s*:\s*(.+?)\s*$", text, re.M)
            if not v.strip().startswith(("|", ">", "{", "["))]


def _locale_lang(root: str, path: str) -> str | None:
    parts = _rel(root, path).split("/")
    stem = os.path.splitext(parts[-1])[0]
    in_locale_dir = any(p.lower() in LOCALE_DIRS for p in parts[:-1])
    for cand in (stem, parts[-2] if len(parts) > 1 else ""):
        m = LANG_RE.match(cand)
        if m and (in_locale_dir or cand == stem):
            return m.group(1).lower()
    return None


def _add_sample(bucket: dict, key: str, where: str) -> None:
    entry = bucket.setdefault(key, {"count": 0, "samples": []})
    entry["count"] += 1
    if len(entry["samples"]) < SAMPLES:
        entry["samples"].append(where)


def _sdk_hits(rel: str, name: str, text: str, out: list) -> None:
    low = name.lower()
    if low == "package.json":
        try:
            pkg = json.loads(text)
        except ValueError:
            return
        for section in ("dependencies", "devDependencies", "peerDependencies"):
            for dep, ver in (pkg.get(section) or {}).items():
                if dep.lower() in SDKS:
                    out.append({"sdk": SDKS[dep.lower()], "package": dep, "version": ver, "file": rel})
        return
    if low.startswith("requirements") or low in ("pyproject.toml", "pipfile", "setup.cfg", "go.mod",
                                                   "composer.json", "cargo.toml", "pom.xml",
                                                   "build.gradle", "build.gradle.kts") or low.endswith(".csproj"):
        for i, line in enumerate(text.splitlines(), 1):
            ll = line.lower()
            for dep, label in SDKS.items():
                if re.search(r"(^|[\s\"'=/:<])" + re.escape(dep) + r"($|[\s\"'=<>~!^@,;\[\]:/])", ll):
                    ver = re.search(r"(\d+\.\d+(\.\d+)?)", line)
                    out.append({"sdk": label, "package": dep, "version": ver.group(1) if ver else "",
                                "file": f"{rel}:{i}"})


def probe(root: str) -> dict:
    root = os.path.abspath(root)
    res = {"root": root, "sdk": [], "design_docs": [], "tokens": [], "tailwind": [], "shadcn": None,
           "fonts": [], "brand_assets": [], "mini_app": [], "locales": {}, "touchpoints": {},
           "skipped_secret_like": 0}
    locale_files: dict[str, list] = {}
    token_seen: set = set()
    font_seen: set = set()
    skipped = [0]
    for path in _walk(root, skipped):
        rel = _rel(root, path)
        name = os.path.basename(path)
        ext = os.path.splitext(name)[1].lower()
        if ext in IMAGE_EXT:
            if BRAND_ASSET.search(name) and len(res["brand_assets"]) < 20:
                res["brand_assets"].append(rel)
            continue
        if DESIGN_DOC.match(name) or ("/design/" in f"/{rel.lower()}" and ext in (".md", ".mdx")):
            res["design_docs"].append(rel)
        text = _read(path)
        if text is None:
            continue
        _sdk_hits(rel, name, text, res["sdk"])
        if name == "components.json" and '"$schema"' in text and "shadcn" in text:
            try:
                cfg = json.loads(text)
                res["shadcn"] = {"file": rel, "style": cfg.get("style"),
                                 "baseColor": (cfg.get("tailwind") or {}).get("baseColor")}
            except ValueError:
                pass
        if name.startswith("tailwind.config"):
            res["tailwind"].append({"file": rel, "hex": sorted(set(HEX.findall(text)))[:20]})
        if ext in STYLE_EXT or ext in (".html", ".vue", ".svelte"):
            for m in CSS_VAR.finditer(text):
                var, val = m.group(1), m.group(2).strip()
                if TOKEN_NAME.search(var) and var not in token_seen and len(res["tokens"]) < 60:
                    token_seen.add(var)
                    line = text.count("\n", 0, m.start()) + 1
                    res["tokens"].append({"name": var, "value": val[:80], "file": f"{rel}:{line}"})
            for m in FONT_FAMILY.finditer(text):
                fam = m.group(1).strip()[:80]
                if fam not in font_seen and "var(" not in fam and len(res["fonts"]) < 10:
                    font_seen.add(fam)
                    res["fonts"].append({"family": fam, "file": rel})
        if name.endswith(".tokens.json") or name in ("tokens.json", "design-tokens.json", "theme.json"):
            res["tokens"].append({"name": f"(token file) {name}", "value": "", "file": rel})
        if ext in CODE_EXT or ext in (".html", ".vue", ".svelte"):
            for m in NEXT_FONT.finditer(text):
                for fam in (f.strip() for f in m.group(1).split(",")):
                    if fam and fam not in font_seen and len(res["fonts"]) < 10:
                        font_seen.add(fam)
                        res["fonts"].append({"family": fam, "file": rel})
            if MINI_APP.search(text) and len(res["mini_app"]) < 10:
                res["mini_app"].append(rel)
        if ext in CODE_EXT:
            for i, line in enumerate(text.splitlines(), 1):
                for key, rx in TOUCH_RE.items():
                    if rx.search(line):
                        _add_sample(res["touchpoints"], key, f"{rel}:{i}")
        if ext in LOCALE_EXT and not name.startswith(("package", "tsconfig", "components", "tokens")):
            lang = _locale_lang(root, path)
            if lang:
                strings = _locale_strings(path, text)
                if strings:
                    locale_files.setdefault(lang, []).append((rel, strings))
    res["locales"] = {lang: _locale_stats(lang, files) for lang, files in sorted(locale_files.items())}
    res["skipped_secret_like"] = skipped[0]
    return res


def _locale_stats(lang: str, files: list) -> dict:
    strings = [(rel, k, v) for rel, items in files for k, v in items if v.strip()]
    if not strings:
        return {"files": [rel for rel, _ in files], "strings": 0, "emoji_per_string": 0}
    longest = max(strings, key=lambda s: len(s[2]))
    buttons = [s for s in strings if BUTTON_KEY.search(s[1])]
    emoji = sum(len(EMOJI.findall(v)) for _, _, v in strings)
    out = {
        "files": [rel for rel, _ in files],
        "strings": len(strings),
        "longest": {"key": longest[1], "chars": len(longest[2]), "file": longest[0]},
        "emoji_per_string": round(emoji / len(strings), 2),
        "exclamation_share": round(sum(1 for *_, v in strings if "!" in v) / len(strings), 2),
    }
    if buttons:
        b = max(buttons, key=lambda s: len(s[2]))
        out["longest_button_label"] = {"key": b[1], "chars": len(b[2]), "text": b[2][:64], "file": b[0]}
    if lang in ADDRESS:
        out["address_counts"] = {form: sum(len(rx.findall(v)) for *_, v in strings)
                                 for form, rx in ADDRESS[lang].items()}
    return out


def print_probe(res: dict) -> None:
    print(f"Project: {res['root']}")
    sdk = ", ".join(f"{s['sdk']} {s['version']} ({s['file']})".strip() for s in res["sdk"]) or "not found"
    print(f"SDK: {sdk}")
    print(f"Design docs: {', '.join(res['design_docs']) or 'none'}")
    if res["shadcn"]:
        print(f"shadcn: {res['shadcn']}")
    for t in res["tailwind"]:
        print(f"Tailwind: {t['file']} colours {', '.join(t['hex']) or '-'}")
    print(f"Tokens: {len(res['tokens'])}")
    for t in res["tokens"][:12]:
        print(f"  {t['name']}: {t['value']}  [{t['file']}]")
    print(f"Fonts: {', '.join(f['family'] for f in res['fonts']) or 'none'}")
    print(f"Brand assets: {', '.join(res['brand_assets']) or 'none'}")
    print(f"Mini App code: {', '.join(res['mini_app']) or 'none'}")
    for lang, st in res["locales"].items():
        extra = f", address {st['address_counts']}" if "address_counts" in st else ""
        btn = st.get("longest_button_label")
        btn_s = f", longest button {btn['chars']} chars ({btn['key']})" if btn else ""
        longest = st.get("longest", {}).get("chars", 0)
        print(f"Locale {lang}: {st['strings']} strings, longest {longest} chars, "
              f"{st['emoji_per_string']} emoji/string{btn_s}{extra}")
    print("Telegram touchpoints:")
    for key in TOUCHPOINTS:
        tp = res["touchpoints"].get(key)
        if tp:
            print(f"  {key}: {tp['count']}  e.g. {', '.join(tp['samples'][:3])}")
    print(f"Secret-like files skipped unread: {res['skipped_secret_like']}")


# ---------------------------------------------------------------- profile schema

E = "enum"
SCHEMA: dict[str, dict] = {
    "bot": {"archetype": str, "contexts": ("list", {"private", "group", "channel", "business", "inline"}),
            "locales": ("list", None), "primary_locale": str, "sdk": str, "bot_api_ceiling": str},
    "mandate": {"access": (E, {"A0", "A1", "A2", "A3", "A4"}), "change": (E, {"M1", "M2", "M3", "M4"})},
    "brand": {"traits": ("list", None), "accent": (str, None), "avatar": (str, None),
              "icon_style": (E, {"outline", "solid", "duotone", "flat", "mixed"})},
    "voice": {"address": (E, {"informal", "formal", "impersonal"}),
              "tone": (E, {"calm", "friendly", "warm", "playful", "strict", "technical"}),
              "person": (E, {"we", "i", "impersonal"}), "exclamations": (E, {"never", "rare", "allowed"})},
    "density": {"max_body_lines": ("int", 1, 40), "max_sentences_per_paragraph": ("int", 1, 6),
                "headings": (E, {"bold_line", "rich_heading", "none"}),
                "tables": (E, {"never", "when_compared", "prefer"}),
                "long_text": (E, {"rich_message", "split", "document"})},
    "keyboard": {"max_actions_per_screen": ("int", 1, 12), "max_buttons_per_row": ("int", 1, 8),
                 "label_max_chars": ("int", 4, 64), "label_form": (E, {"verb_object", "noun", "mixed"}),
                 "nav_row": (E, {"last", "first", "none"}), "back_label": str, "home_label": str,
                 "confirm_destructive": bool},
    "emphasis": {"primary_per_screen": ("int", 0, 1), "success_on_commit": bool,
                 "danger": (E, {"after_confirm", "on_destructive", "never"})},
    "icons": {"system": (E, {"none", "unicode", "custom"}),
              "eligibility": (E, {"none", "fragment", "premium", "unverified"}), "pack": (str, None),
              "in_labels": (E, {"leading", "none"}), "in_body": (E, {"none", "status_only", "section_markers"}),
              "max_per_message": ("int", 0, 12)},
    "navigation": {"entry": (E, {"home_screen", "reply_keyboard", "menu_button_mini_app", "commands_only"}),
                   "edit_in_place": bool, "max_depth": ("int", 1, 5),
                   "menu_button": (E, {"commands", "web_app", "default"}), "commands": ("commands",)},
    "feedback": {"ack_every_tap": bool, "progress": (E, {"named_stages", "chat_action", "none"}),
                 "ai_streaming": (E, {"draft_with_stop", "edit_throttled", "none"})},
    "formats": {"date": str, "time": str, "number_grouping": str, "currency": str},
    "contracts": {"callback_data": (E, {"frozen", "versioned"}), "callback_prefix": (str, None),
                  "i18n_keys": (E, {"frozen", "new_keys_for_new_meaning"}),
                  "deep_links": (E, {"frozen", "mapped"}), "commands": (E, {"frozen", "aliased"})},
}
TOP_LEVEL = set(SCHEMA) | {"profile_version", "updated", "profile_texts", "sources"}
PROFILE_TEXT_LIMITS = {"name": 64, "short_description": 120, "description": 512}  # setMy* (API)
COMMAND_RE = re.compile(r"^[a-z0-9_]{1,32}$")

DEFAULTS = {
    "bot": {"contexts": ["private"], "locales": ["en"], "primary_locale": "en"},
    "mandate": {"access": "A1", "change": "M2"},
    "brand": {"traits": [], "accent": None, "icon_style": "mixed", "avatar": None},
    "voice": {"address": "informal", "tone": "calm", "person": "impersonal", "exclamations": "rare"},
    "density": {"max_body_lines": 8, "max_sentences_per_paragraph": 2, "headings": "bold_line",
                "tables": "when_compared", "long_text": "rich_message"},
    "keyboard": {"max_actions_per_screen": 6, "max_buttons_per_row": 2, "label_max_chars": 20,
                 "label_form": "verb_object", "nav_row": "last", "back_label": "← Back",
                 "home_label": "Home", "confirm_destructive": True},
    "emphasis": {"primary_per_screen": 1, "success_on_commit": True, "danger": "after_confirm"},
    "icons": {"system": "unicode", "eligibility": "none", "pack": None, "in_labels": "leading",
              "in_body": "status_only", "max_per_message": 3},
    "navigation": {"entry": "home_screen", "edit_in_place": True, "max_depth": 2,
                   "menu_button": "commands", "commands": []},
    "feedback": {"ack_every_tap": True, "progress": "named_stages", "ai_streaming": "draft_with_stop"},
    "formats": {"date": "locale", "time": "locale", "number_grouping": "locale", "currency": "locale"},
    "contracts": {"callback_data": "frozen", "callback_prefix": None, "i18n_keys": "frozen",
                  "deep_links": "frozen", "commands": "frozen"},
}


def _check_value(path: str, spec, value, errors: list) -> None:
    if spec is str:
        if not isinstance(value, str):
            errors.append(f"{path}: must be a string")
        return
    if spec is bool:
        if not isinstance(value, bool):
            errors.append(f"{path}: must be true or false")
        return
    kind = spec[0]
    if kind is str:
        if value is not None and not isinstance(value, str):
            errors.append(f"{path}: must be a string or null")
    elif kind == E:
        if value not in spec[1]:
            errors.append(f"{path}: {value!r} is not one of {sorted(spec[1])}")
    elif kind == "int":
        if not isinstance(value, int) or isinstance(value, bool) or not spec[1] <= value <= spec[2]:
            errors.append(f"{path}: must be an integer {spec[1]}-{spec[2]}")
    elif kind == "list":
        if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
            errors.append(f"{path}: must be a list of strings")
        elif spec[1] is not None:
            bad = [v for v in value if v not in spec[1]]
            if bad:
                errors.append(f"{path}: unknown {bad}; allowed {sorted(spec[1])}")
    elif kind == "commands":
        _check_commands(path, value, errors)


def _check_commands(path: str, cmds, errors: list) -> None:
    if not isinstance(cmds, list):
        errors.append(f"{path}: must be a list of {{command, description}}")
        return
    if len(cmds) > 100:
        errors.append(f"{path}: {len(cmds)} commands; setMyCommands accepts at most 100")
    seen = set()
    for i, c in enumerate(cmds):
        where = f"{path}[{i}]"
        if not isinstance(c, dict) or set(c) - {"command", "description"}:
            errors.append(f"{where}: must be {{command, description}}")
            continue
        name, desc = c.get("command", ""), c.get("description", "")
        if not isinstance(name, str) or not COMMAND_RE.match(name):
            errors.append(f"{where}: command {name!r} must be 1-32 chars of a-z, 0-9, _ (no leading /)")
        if not isinstance(desc, str) or not 1 <= len(desc) <= 256:
            errors.append(f"{where}: description must be 1-256 characters")
        if name in seen:
            errors.append(f"{where}: duplicate command {name!r}")
        seen.add(name)


def _leaf_paths(profile: dict):
    for section, knobs in SCHEMA.items():
        for knob in knobs:
            if isinstance(profile.get(section), dict) and knob in profile[section]:
                yield f"{section}.{knob}"
    for lang in (profile.get("profile_texts") or {}):
        yield f"profile_texts.{lang}"


def _sourced(path: str, sources: dict) -> bool:
    parts = path.split(".")
    return any(".".join(parts[:i]) in sources for i in range(1, len(parts) + 1))


def check(profile) -> tuple[list, list]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(profile, dict):
        return ["profile must be a JSON object"], []
    for key in profile:
        if key not in TOP_LEVEL:
            errors.append(f"{key}: unknown section (known: {sorted(TOP_LEVEL)})")
    if profile.get("profile_version") != 1:
        errors.append("profile_version: must be 1")
    for section, knobs in SCHEMA.items():
        data = profile.get(section)
        if data is None:
            warnings.append(f"{section}: missing, skill defaults apply")
            continue
        if not isinstance(data, dict):
            errors.append(f"{section}: must be an object")
            continue
        for knob, value in data.items():
            if knob not in knobs:
                errors.append(f"{section}.{knob}: unknown knob (known: {sorted(knobs)})")
            else:
                _check_value(f"{section}.{knob}", knobs[knob], value, errors)

    m = {s: (profile.get(s) if isinstance(profile.get(s), dict) else {}) for s in SCHEMA}
    get = lambda s, k: m[s].get(k, DEFAULTS[s].get(k))  # noqa: E731
    contexts = get("bot", "contexts") or []
    locales = get("bot", "locales") or []

    if m["bot"].get("primary_locale") and m["bot"]["primary_locale"] not in locales:
        errors.append("bot.primary_locale: must be one of bot.locales")

    # Icons and custom emoji eligibility (API: Fragment usernames, or owner Premium outside channels).
    if get("icons", "system") == "custom":
        elig = get("icons", "eligibility")
        if elig not in ("fragment", "premium"):
            errors.append("icons.system=custom: eligibility must be verified as 'fragment' or 'premium'; "
                          "an ineligible bot's custom emoji are stripped silently")
        elif elig == "premium" and "channel" in contexts:
            errors.append("icons: custom emoji in channel posts need Fragment usernames; "
                          "owner Premium covers only private, group and supergroup chats")
        if not get("icons", "pack"):
            errors.append("icons.pack: required for custom emoji (one family per bot)")
    if get("icons", "system") == "none" and get("icons", "in_labels") == "leading":
        warnings.append("icons: system is 'none' but in_labels is 'leading'")

    if get("feedback", "ack_every_tap") is not True:
        errors.append("feedback.ack_every_tap: must be true (every tap gets feedback)")
    if get("feedback", "ai_streaming") == "draft_with_stop" and "private" not in contexts:
        warnings.append("feedback.ai_streaming: drafts exist only in private chats; "
                        "bot.contexts has no 'private'")

    if get("navigation", "entry") == "menu_button_mini_app" and get("navigation", "menu_button") != "web_app":
        errors.append("navigation: entry 'menu_button_mini_app' needs menu_button 'web_app'")
    if get("navigation", "entry") == "reply_keyboard" and contexts == ["channel"]:
        errors.append("navigation.entry: channels have no reply keyboards")

    # Contracts can change only under the M4 mandate, and versioning needs a short prefix.
    changed = [k for k in ("callback_data", "i18n_keys", "deep_links", "commands")
               if get("contracts", k) not in ("frozen", None)]
    if changed and get("mandate", "change") != "M4":
        errors.append(f"contracts {changed}: changing contracts needs mandate.change = M4 "
                      "(and a migration in the plan)")
    if get("contracts", "callback_data") == "versioned":
        prefix = get("contracts", "callback_prefix")
        if not isinstance(prefix, str) or not 1 <= len(prefix.encode("utf-8")) <= 16:
            errors.append("contracts.callback_prefix: versioned callback_data needs a 1-16 byte prefix "
                          "(callback_data itself is 1-64 bytes)")

    for lang, texts in (profile.get("profile_texts") or {}).items():
        if not isinstance(texts, dict):
            errors.append(f"profile_texts.{lang}: must be an object")
            continue
        if locales and lang not in locales:
            warnings.append(f"profile_texts.{lang}: language not in bot.locales")
        for field, value in texts.items():
            limit = PROFILE_TEXT_LIMITS.get(field)
            if limit is None:
                errors.append(f"profile_texts.{lang}.{field}: unknown (known: {sorted(PROFILE_TEXT_LIMITS)})")
            elif not isinstance(value, str) or len(value) > limit:
                errors.append(f"profile_texts.{lang}.{field}: must be a string of 0-{limit} characters")

    # Heuristic ranges (this skill's design advice).
    ranges = [("keyboard", "max_buttons_per_row", 3, "long labels truncate on phones"),
              ("keyboard", "max_actions_per_screen", 8, "split into screens or paginate"),
              ("keyboard", "label_max_chars", 30, "labels truncate in narrow rows"),
              ("navigation", "max_depth", 3, "frequent jobs should be ≤2 taps from home"),
              ("icons", "max_per_message", 5, "decoration competes with information"),
              ("density", "max_body_lines", 15, "long bodies belong in a Rich Message or document")]
    for section, knob, limit, why in ranges:
        value = get(section, knob)
        if isinstance(value, int) and value > limit:
            warnings.append(f"{section}.{knob}={value}: above {limit}; {why}")

    sources = profile.get("sources") or {}
    if not isinstance(sources, dict):
        errors.append("sources: must map dotted knob paths to evidence")
        sources = {}
    unsourced = [p for p in _leaf_paths(profile) if not _sourced(p, sources)]
    if unsourced:
        shown = ", ".join(unsourced[:10]) + (" …" if len(unsourced) > 10 else "")
        warnings.append(f"{len(unsourced)} knob(s) without a source (assumed): {shown}")
    return errors, warnings


# ---------------------------------------------------------------- scaffold

def scaffold(res: dict) -> dict:
    prof = {"profile_version": 1, "updated": None}
    prof.update(json.loads(json.dumps(DEFAULTS)))
    sources: dict[str, str] = {}
    if res.get("sdk"):
        s = res["sdk"][0]
        prof["bot"]["sdk"] = f"{s['sdk']} {s['version']}".strip()
        sources["bot.sdk"] = s["file"]
    locales = res.get("locales") or {}
    if locales:
        langs = sorted(locales, key=lambda l: -locales[l]["strings"])
        prof["bot"]["locales"] = langs
        prof["bot"]["primary_locale"] = langs[0]
        sources["bot.locales"] = ", ".join(f for l in langs for f in locales[l]["files"])
        for lang in langs:
            counts = locales[lang].get("address_counts")
            if counts and sum(counts.values()):
                form = max(counts, key=counts.get)
                prof["voice"]["address"] = form
                sources["voice.address"] = f"{lang} catalogs: {counts}"
                break
        labels = [locales[l]["longest_button_label"] for l in langs if "longest_button_label" in locales[l]]
        if labels:
            widest = max(labels, key=lambda b: b["chars"])
            prof["keyboard"]["label_max_chars"] = max(20, min(30, widest["chars"]))
            sources["keyboard.label_max_chars"] = f"longest label {widest['chars']} chars ({widest['key']})"
        density = max(locales[l]["emoji_per_string"] for l in langs)
        if density == 0:
            prof["icons"]["in_body"] = "none"
            sources["icons.in_body"] = "catalogs use no emoji"
    tp = res.get("touchpoints") or {}
    if "custom_emoji" in tp:
        prof["icons"]["system"] = "custom"
        prof["icons"]["eligibility"] = "unverified"
        sources["icons.system"] = ", ".join(tp["custom_emoji"]["samples"])
    if "reply_keyboards" in tp and "inline_keyboards" not in tp:
        prof["navigation"]["entry"] = "reply_keyboard"
        sources["navigation.entry"] = ", ".join(tp["reply_keyboards"]["samples"])
    if res.get("mini_app") and "menu_button" in tp:
        sources["navigation.menu_button"] = "Mini App code found: " + ", ".join(res["mini_app"][:3])
    if "drafts" not in tp and "rich_messages" not in tp:
        prof["feedback"]["ai_streaming"] = "none"
    accent = next((t for t in res.get("tokens", []) if re.search(r"primary|accent|brand", t["name"], re.I)
                   and HEX.search(t["value"])), None)
    if accent:
        prof["brand"]["accent"] = HEX.search(accent["value"]).group(0)
        sources["brand.accent"] = f"{accent['file']} {accent['name']}"
    if res.get("brand_assets"):
        prof["brand"]["avatar"] = res["brand_assets"][0]
        sources["brand.avatar"] = "probe: brand asset candidates " + ", ".join(res["brand_assets"][:3])
    if res.get("design_docs"):
        sources["brand.traits"] = "read: " + ", ".join(res["design_docs"][:3])
    prof["sources"] = sources
    return prof


# ---------------------------------------------------------------- CLI

def _load_json(path: str):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("probe", help="scan a project for style signals and Telegram touchpoints")
    p.add_argument("root")
    p.add_argument("--json", action="store_true")
    s = sub.add_parser("scaffold", help="starting profile from a probe JSON")
    s.add_argument("probe_json")
    c = sub.add_parser("check", help="validate a style profile")
    c.add_argument("profile")
    args = ap.parse_args(argv)

    if args.cmd == "probe":
        if not os.path.isdir(args.root):
            print(f"not a directory: {args.root}", file=sys.stderr)
            return 2
        res = probe(args.root)
        if args.json:
            print(json.dumps(res, ensure_ascii=False, indent=2))
        else:
            print_probe(res)
        return 0
    if args.cmd == "scaffold":
        print(json.dumps(scaffold(_load_json(args.probe_json)), ensure_ascii=False, indent=2))
        return 0
    try:
        profile = _load_json(args.profile)
    except (OSError, ValueError) as exc:
        print(f"ERROR cannot read profile: {exc}")
        return 1
    errors, warnings = check(profile)
    for e in errors:
        print(f"ERROR {e}")
    for w in warnings:
        print(f"WARN  {w}")
    print(f"{args.profile}: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
