"""Command-line interface for Agentgram."""

from __future__ import annotations

import argparse
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any, Iterable, TextIO
from urllib.parse import urlsplit, urlunsplit

from . import __version__
from .telegram import (
    MAX_DOCUMENT_BYTES,
    TelegramClient,
    TelegramError,
    looks_like_token,
    validate_document_path as validate_telegram_document_path,
)


MAX_TEXT_LENGTH = 4096
MAX_CAPTION_LENGTH = 1024
TOKEN_ENV = "TELEGRAM_BOT_TOKEN"
CHAT_ID_ENV = "TELEGRAM_CHAT_ID"
PLUGIN_NAME = "agentgram"
PYTHON_PACKAGE = "agentgram_tg"


class CliError(RuntimeError):
    """Raised for user-correctable command errors."""


def main(argv: list[str] | None = None) -> int:
    return run(argv, stdout=sys.stdout, stderr=sys.stderr, environ=os.environ)


def run(
    argv: list[str] | None = None,
    *,
    stdout: TextIO,
    stderr: TextIO,
    environ: dict[str, str],
) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = args.func(args, stdout=stdout, environ=environ)
    except CliError as exc:
        print(f"agentgram: {exc}", file=stderr)
        return 2
    except TelegramError as exc:
        print(f"agentgram: {exc}", file=stderr)
        return 1
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agentgram",
        description="Send explicit Telegram messages from local agent sessions.",
    )
    parser.add_argument("--version", action="version", version=f"agentgram {__version__}")
    subcommands = parser.add_subparsers(dest="command", required=True)

    send = subcommands.add_parser("send", help="send a Telegram text message")
    send.add_argument("--chat-id", help=f"override {CHAT_ID_ENV}")
    send.add_argument("--parse-mode", choices=("HTML", "MarkdownV2"), help="Telegram parse mode")
    send.add_argument("--silent", action="store_true", help="send without notification sound")
    send.add_argument("--no-preview", action="store_true", help="disable link previews")
    long_mode = send.add_mutually_exclusive_group()
    long_mode.add_argument("--split", action="store_true", help="split long plain text into multiple messages")
    long_mode.add_argument("--as-file", action="store_true", help="send the text as a UTF-8 document")
    send.add_argument("--filename", help="document filename for --as-file")
    send.add_argument("text", nargs="+", help="message text")
    send.set_defaults(func=cmd_send)

    send_file = subcommands.add_parser("send-file", help="send a Telegram document")
    send_file.add_argument("--chat-id", help=f"override {CHAT_ID_ENV}")
    send_file.add_argument("--caption", help="optional document caption")
    send_file.add_argument("--parse-mode", choices=("HTML", "MarkdownV2"), help="Telegram caption parse mode")
    send_file.add_argument("--silent", action="store_true", help="send without notification sound")
    send_file.add_argument("path", help="path to the local file to send")
    send_file.set_defaults(func=cmd_send_file)

    chat_id = subcommands.add_parser("chat-id", help="show candidate chat ids from recent updates")
    chat_id.add_argument("--raw", action="store_true", help="print raw getUpdates JSON")
    chat_id.set_defaults(func=cmd_chat_id)

    doctor = subcommands.add_parser("doctor", help="check Agentgram and Telegram configuration")
    doctor.add_argument("--json", action="store_true", dest="json_output", help="print JSON")
    doctor.set_defaults(func=cmd_doctor)

    update = subcommands.add_parser("update", help="check or update a git-based Agentgram checkout")
    update.add_argument("--check", action="store_true", help="only check update status")
    update.add_argument("--repo", default=str(repo_root()), help="Agentgram repository path")
    update.set_defaults(func=cmd_update)
    return parser


def cmd_send(args: argparse.Namespace, *, stdout: TextIO, environ: dict[str, str]) -> int:
    token = require_env(environ, TOKEN_ENV)
    chat_id = args.chat_id or require_env(environ, CHAT_ID_ENV)
    text = normalize_text(args.text)
    if args.filename and not args.as_file:
        raise CliError("--filename requires --as-file")
    if args.as_file:
        if args.parse_mode:
            raise CliError("--as-file does not support --parse-mode; file contents are sent as plain UTF-8")
        if args.no_preview:
            raise CliError("--no-preview is only supported for text messages")
        return send_text_as_file(
            token=token,
            chat_id=chat_id,
            text=text,
            filename=args.filename,
            silent=args.silent,
            stdout=stdout,
        )
    if args.split:
        if args.parse_mode:
            raise CliError("--split does not support --parse-mode yet")
        return send_split_text(
            token=token,
            chat_id=chat_id,
            text=text,
            silent=args.silent,
            no_preview=args.no_preview,
            stdout=stdout,
        )
    payload = build_send_payload(
        chat_id=chat_id,
        text=text,
        parse_mode=args.parse_mode,
        silent=args.silent,
        no_preview=args.no_preview,
    )
    message = TelegramClient(token).send_message(payload)
    message_id = message.get("message_id")
    if message_id is None:
        print("sent", file=stdout)
    else:
        print(f"sent message_id={message_id}", file=stdout)
    return 0


def send_split_text(
    *,
    token: str,
    chat_id: str,
    text: str,
    silent: bool,
    no_preview: bool,
    stdout: TextIO,
) -> int:
    client = TelegramClient(token)
    message_ids: list[str] = []
    chunks = split_message_text(text)
    for chunk in chunks:
        payload = build_send_payload(
            chat_id=chat_id,
            text=chunk,
            parse_mode=None,
            silent=silent,
            no_preview=no_preview,
        )
        message = client.send_message(payload)
        message_id = message.get("message_id")
        if message_id is not None:
            message_ids.append(str(message_id))
    if message_ids:
        print(f"sent messages count={len(chunks)} message_ids={','.join(message_ids)}", file=stdout)
    else:
        print(f"sent messages count={len(chunks)}", file=stdout)
    return 0


def send_text_as_file(
    *,
    token: str,
    chat_id: str,
    text: str,
    filename: str | None,
    silent: bool,
    stdout: TextIO,
) -> int:
    document_name = validate_text_filename(filename)
    client = TelegramClient(token)
    with tempfile.TemporaryDirectory(prefix="agentgram-") as tmp:
        document_path = Path(tmp) / document_name
        document_path.write_text(text, encoding="utf-8")
        payload = build_document_payload(chat_id=chat_id, caption=None, parse_mode=None, silent=silent)
        message = client.send_document(payload, document_path)
    message_id = message.get("message_id")
    if message_id is None:
        print("sent document", file=stdout)
    else:
        print(f"sent document message_id={message_id}", file=stdout)
    return 0


def cmd_send_file(args: argparse.Namespace, *, stdout: TextIO, environ: dict[str, str]) -> int:
    token = require_env(environ, TOKEN_ENV)
    chat_id = args.chat_id or require_env(environ, CHAT_ID_ENV)
    document_path = validate_document_path(args.path)
    payload = build_document_payload(
        chat_id=chat_id,
        caption=args.caption,
        parse_mode=args.parse_mode,
        silent=args.silent,
    )
    message = TelegramClient(token).send_document(payload, document_path)
    message_id = message.get("message_id")
    if message_id is None:
        print("sent document", file=stdout)
    else:
        print(f"sent document message_id={message_id}", file=stdout)
    return 0


def cmd_chat_id(args: argparse.Namespace, *, stdout: TextIO, environ: dict[str, str]) -> int:
    token = require_env(environ, TOKEN_ENV)
    updates = TelegramClient(token).get_updates()
    if args.raw:
        print(json.dumps(updates, indent=2, sort_keys=True), file=stdout)
        return 0

    candidates = extract_chat_candidates(updates)
    if not candidates:
        print("No chat ids found. Send a message to the bot, then run this command again.", file=stdout)
        return 0
    for candidate in candidates:
        title = candidate.get("title") or candidate.get("username") or candidate.get("name") or "(untitled)"
        print(f"{candidate['id']}\t{candidate['type']}\t{title}", file=stdout)
    return 0


def cmd_doctor(args: argparse.Namespace, *, stdout: TextIO, environ: dict[str, str]) -> int:
    checks: list[dict[str, Any]] = []
    token = environ.get(TOKEN_ENV, "").strip()
    chat_id = environ.get(CHAT_ID_ENV, "").strip()
    root = repo_root()
    checks.append(check("bot_token_env", bool(token), f"{TOKEN_ENV} is {'set' if token else 'missing'}"))
    checks.append(
        check(
            "bot_token_shape",
            bool(token and looks_like_token(token)),
            "token shape looks valid" if token and looks_like_token(token) else "token shape is invalid or unknown",
            required=False,
        )
    )
    checks.append(check("chat_id_env", bool(chat_id), f"{CHAT_ID_ENV} is {'set' if chat_id else 'missing'}"))
    checks.append(
        check(
            "plugin_manifest",
            (root / ".codex-plugin" / "plugin.json").is_file(),
            ".codex-plugin/plugin.json present",
            required=False,
        )
    )
    checks.append(
        check(
            "skill_file",
            (root / "skills" / "agentgram" / "SKILL.md").is_file(),
            "skills/agentgram/SKILL.md present",
            required=False,
        )
    )
    origin = git_origin_url(root)
    safe_origin = redact_url_userinfo(origin)
    checks.append(
        check(
            "git_origin",
            bool(origin),
            f"origin remote is {safe_origin}" if origin else "origin remote is missing or unavailable",
            required=False,
        )
    )

    if token:
        try:
            bot = TelegramClient(token).get_me()
            username = bot.get("username") or bot.get("first_name") or "bot"
            checks.append(check("telegram_get_me", True, f"authenticated as {username}"))
        except TelegramError as exc:
            checks.append(check("telegram_get_me", False, str(exc)))

    ok = all(item["ok"] for item in checks if item["required"])
    if args.json_output:
        print(json.dumps({"ok": ok, "checks": checks}, indent=2, sort_keys=True), file=stdout)
    else:
        for item in checks:
            status = "ok" if item["ok"] else "fail"
            required = "required" if item["required"] else "optional"
            print(f"{status}\t{item['name']}\t{required}\t{item['detail']}", file=stdout)
    return 0 if ok else 1


def cmd_update(args: argparse.Namespace, *, stdout: TextIO, environ: dict[str, str]) -> int:
    del environ
    repo = Path(args.repo).expanduser().resolve()
    if not (repo / ".git").exists():
        raise CliError(f"{repo} is not a git checkout")

    if args.check:
        status = git_update_status(repo)
        print(status, file=stdout)
        return 0

    ensure_clean_worktree(repo)
    validate_checkout(repo)
    print(git_update_status(repo), file=stdout)
    pull_result = run_git(repo, "pull", "--ff-only")
    if pull_result:
        print(pull_result, file=stdout)
    validate_checkout(repo)
    print("validation ok", file=stdout)
    for line in update_next_steps(repo):
        print(line, file=stdout)
    return 0


def build_send_payload(
    *,
    chat_id: str,
    text: str,
    parse_mode: str | None,
    silent: bool,
    no_preview: bool,
) -> dict[str, Any]:
    if not str(chat_id).strip():
        raise CliError("chat id is required")
    validate_text(text, parse_mode=parse_mode)
    payload: dict[str, Any] = {"chat_id": chat_id, "text": text}
    if parse_mode:
        payload["parse_mode"] = parse_mode
    if silent:
        payload["disable_notification"] = True
    if no_preview:
        payload["link_preview_options"] = {"is_disabled": True}
    return payload


def build_document_payload(
    *,
    chat_id: str,
    caption: str | None,
    parse_mode: str | None,
    silent: bool,
) -> dict[str, Any]:
    if not str(chat_id).strip():
        raise CliError("chat id is required")
    validate_caption(caption, parse_mode=parse_mode)
    payload: dict[str, Any] = {"chat_id": chat_id}
    if caption:
        payload["caption"] = caption
    if parse_mode:
        payload["parse_mode"] = parse_mode
    if silent:
        payload["disable_notification"] = True
    return payload


def normalize_text(parts: Iterable[str]) -> str:
    text = " ".join(parts).strip()
    validate_text(text, parse_mode=None, enforce_max=False)
    return text


def validate_text(text: str, *, parse_mode: str | None = None, enforce_max: bool = True) -> None:
    if not text:
        raise CliError("message text is required")
    length = telegram_text_length(text, parse_mode)
    if enforce_max and length > MAX_TEXT_LENGTH:
        raise CliError(f"message text is too long: {length} characters; maximum is {MAX_TEXT_LENGTH}")


def validate_caption(caption: str | None, *, parse_mode: str | None = None) -> None:
    if caption is None or caption == "":
        return
    length = telegram_text_length(caption, parse_mode)
    if length > MAX_CAPTION_LENGTH:
        raise CliError(f"caption is too long: {length} characters; maximum is {MAX_CAPTION_LENGTH}")


def validate_document_path(path: str | Path) -> Path:
    try:
        return validate_telegram_document_path(path)
    except TelegramError as exc:
        raise CliError(str(exc)) from exc


def validate_text_filename(filename: str | None) -> str:
    if filename is None:
        return "agentgram-message.txt"
    name = filename.strip()
    if not name:
        raise CliError("filename is required")
    if "/" in name or "\\" in name or Path(name).name != name or name in (".", ".."):
        raise CliError("filename must be a file name, not a path")
    return name


def split_message_text(text: str, *, limit: int = MAX_TEXT_LENGTH) -> list[str]:
    validate_text(text, parse_mode=None, enforce_max=False)
    expected_chunks = 1
    while True:
        prefix_length = len(f"[{expected_chunks}/{expected_chunks}] ")
        chunk_limit = limit - prefix_length
        if chunk_limit <= 0:
            raise CliError("message limit is too small for split counters")
        raw_chunks = split_plain_text(text, chunk_limit)
        if len(raw_chunks) == expected_chunks:
            return [f"[{index}/{expected_chunks}] {chunk}" for index, chunk in enumerate(raw_chunks, start=1)]
        expected_chunks = len(raw_chunks)


def split_plain_text(text: str, limit: int) -> list[str]:
    chunks: list[str] = []
    remaining = text
    while remaining:
        if len(remaining) <= limit:
            chunks.append(remaining)
            break
        split_at = best_plain_text_split(remaining, limit)
        chunks.append(remaining[:split_at])
        remaining = remaining[split_at:]
    return chunks


def best_plain_text_split(text: str, limit: int) -> int:
    window = text[:limit]
    for boundary in ("\n\n", "\n", " "):
        position = window.rfind(boundary)
        if position > 0:
            return position + len(boundary)
    return limit


def telegram_text_length(text: str, parse_mode: str | None) -> int:
    if parse_mode == "HTML":
        return len(html_visible_text(text))
    if parse_mode == "MarkdownV2":
        return len(markdown_v2_visible_text(text))
    return len(text)


class _VisibleHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def html_visible_text(text: str) -> str:
    parser = _VisibleHTMLParser()
    parser.feed(text)
    parser.close()
    return "".join(parser.parts)


def markdown_v2_visible_text(text: str) -> str:
    visible: list[str] = []
    i = 0
    formatting = set("_*[]()~`>#+-=|{}.!")
    while i < len(text):
        if text.startswith("```", i):
            i += 3
            closing = text.find("```", i)
            if closing == -1:
                visible.append(text[i:])
                break
            visible.append(text[i:closing])
            i = closing + 3
            continue
        char = text[i]
        if char == "[":
            label_end = text.find("](", i + 1)
            if label_end != -1:
                destination_end = text.find(")", label_end + 2)
                if destination_end != -1:
                    visible.append(markdown_v2_visible_text(text[i + 1 : label_end]))
                    i = destination_end + 1
                    continue
        if char == "`":
            closing = text.find("`", i + 1)
            if closing == -1:
                i += 1
                continue
            visible.append(text[i + 1 : closing])
            i = closing + 1
            continue
        if char == "\\" and i + 1 < len(text):
            visible.append(text[i + 1])
            i += 2
            continue
        if char in formatting:
            i += 1
            continue
        visible.append(char)
        i += 1
    return "".join(visible)


def require_env(environ: dict[str, str], name: str) -> str:
    value = environ.get(name, "").strip()
    if not value:
        raise CliError(f"{name} is required")
    return value


def extract_chat_candidates(updates: list[dict[str, Any]]) -> list[dict[str, str]]:
    seen: set[str] = set()
    candidates: list[dict[str, str]] = []
    for update in updates:
        for key in ("message", "edited_message", "channel_post", "edited_channel_post", "business_message"):
            message = update.get(key)
            if not isinstance(message, dict):
                continue
            chat = message.get("chat")
            if not isinstance(chat, dict) or "id" not in chat:
                continue
            chat_id = str(chat["id"])
            if chat_id in seen:
                continue
            seen.add(chat_id)
            name = chat.get("title") or " ".join(
                part for part in (chat.get("first_name"), chat.get("last_name")) if part
            )
            candidates.append(
                {
                    "id": chat_id,
                    "type": str(chat.get("type") or "unknown"),
                    "title": str(chat.get("title") or ""),
                    "username": str(chat.get("username") or ""),
                    "name": str(name or ""),
                }
            )
    return candidates


def check(name: str, ok: bool, detail: str, *, required: bool = True) -> dict[str, Any]:
    return {"name": name, "ok": ok, "detail": detail, "required": required}


def git_update_status(repo: Path) -> str:
    branch = run_git(repo, "rev-parse", "--abbrev-ref", "HEAD", allow_fail=True) or "unknown"
    upstream = run_git(repo, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}", allow_fail=True)
    if not upstream:
        return f"{branch}: unknown update state; no upstream configured"
    left_right = run_git(repo, "rev-list", "--left-right", "--count", f"{branch}...{upstream}", allow_fail=True)
    if not left_right:
        return f"{branch}: unknown update state relative to {upstream}"
    try:
        ahead, behind = [int(part) for part in left_right.split()]
    except ValueError:
        return f"{branch}: unknown update state relative to {upstream}"
    if ahead == 0 and behind == 0:
        return f"{branch}: up to date with local ref {upstream}"
    return f"{branch}: ahead {ahead}, behind {behind} relative to local ref {upstream}"


def ensure_clean_worktree(repo: Path) -> None:
    status = run_git(repo, "status", "--porcelain")
    if status:
        raise CliError("refusing to update because the git worktree has uncommitted changes")


def validate_checkout(repo: Path) -> None:
    required_files = [
        repo / "bin" / "agentgram",
        repo / ".codex-plugin" / "plugin.json",
        repo / "skills" / PLUGIN_NAME / "SKILL.md",
        repo / "src" / PYTHON_PACKAGE / "cli.py",
    ]
    missing = [str(path.relative_to(repo)) for path in required_files if not path.is_file()]
    if missing:
        raise CliError(f"checkout validation failed; missing {', '.join(missing)}")

    try:
        manifest = json.loads((repo / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CliError(f"checkout validation failed; plugin manifest is invalid JSON: {exc}") from exc
    if manifest.get("name") != PLUGIN_NAME:
        raise CliError(f"checkout validation failed; plugin manifest name is not {PLUGIN_NAME}")
    if manifest.get("skills") != "./skills/":
        raise CliError("checkout validation failed; plugin manifest skills path is not ./skills/")


def update_next_steps(repo: Path) -> list[str]:
    steps = [
        "Next steps:",
        f"- CLI users: keep using {repo / 'bin' / 'agentgram'} or refresh your PATH/symlink if needed.",
    ]
    codex_entry = detected_codex_agentgram_entry()
    if codex_entry:
        steps.extend(
            [
                f"- Codex plugin detected: refresh with `codex plugin add {codex_entry}`.",
                "- Start a new Codex thread after reinstall so updated skills are loaded.",
            ]
        )
    else:
        steps.append("- Codex users: reinstall or refresh the Agentgram plugin from the marketplace where you added it.")
    return steps


def detected_codex_agentgram_entry() -> str | None:
    try:
        proc = subprocess.run(
            ["codex", "plugin", "list"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError:
        return None
    if proc.returncode != 0:
        return None
    for line in proc.stdout.splitlines():
        fields = line.split()
        if not fields:
            continue
        entry = fields[0]
        status = fields[1] if len(fields) > 1 else ""
        if entry.startswith(f"{PLUGIN_NAME}@") and status.startswith("installed"):
            return entry
    return None


def git_origin_url(repo: Path) -> str:
    return run_git(repo, "remote", "get-url", "origin", allow_fail=True)


def redact_url_userinfo(url: str) -> str:
    try:
        parsed = urlsplit(url)
    except ValueError:
        return url
    if parsed.scheme and "@" in parsed.netloc:
        host = parsed.netloc.rsplit("@", 1)[1]
        return urlunsplit((parsed.scheme, host, parsed.path, parsed.query, parsed.fragment))
    return url


def run_git(repo: Path, *args: str, allow_fail: bool = False) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        if allow_fail:
            return ""
        raise CliError(proc.stderr.strip() or f"git {' '.join(args)} failed")
    return proc.stdout.strip()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]
