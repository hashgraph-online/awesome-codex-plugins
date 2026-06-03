"""Command-line interface for Agentgram."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tempfile
import time
from typing import Any, Iterable, TextIO
from urllib.parse import urlsplit, urlunsplit

from . import __version__
from .telegram import (
    MAX_DOWNLOAD_BYTES,
    MAX_DOCUMENT_BYTES,
    TelegramClient,
    TelegramError,
    looks_like_token,
    validate_document_path as validate_telegram_document_path,
)


MAX_TEXT_LENGTH = 4096
MAX_CAPTION_LENGTH = 1024
TELEGRAM_UPDATE_LIMIT = 100
MAX_INBOX_LIMIT = 500
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

    inbox = subcommands.add_parser("inbox", help="read recent messages forwarded to the bot")
    inbox.add_argument("--chat-id", help=f"override {CHAT_ID_ENV}")
    inbox.add_argument("--limit", type=int, default=100, help="maximum pending updates to read; 1-100 for peek, 1-500 with --ack")
    inbox.add_argument("--since", default="24h", help="only include messages newer than this duration, e.g. 15m, 3h, 1d")
    inbox_filter = inbox.add_mutually_exclusive_group()
    inbox_filter.add_argument(
        "--forwarded-only",
        action="store_false",
        dest="include_plain",
        help="only include forwarded messages; this is the default",
    )
    inbox_filter.add_argument(
        "--include-plain",
        action="store_true",
        dest="include_plain",
        help="also include direct non-forwarded messages sent to the bot",
    )
    inbox_ack = inbox.add_mutually_exclusive_group()
    inbox_ack.add_argument(
        "--peek",
        action="store_false",
        dest="ack",
        help="read without consuming updates; this is the default",
    )
    inbox_ack.add_argument(
        "--ack",
        action="store_true",
        dest="ack",
        help="consume rendered updates after successful output",
    )
    inbox.set_defaults(func=cmd_inbox, include_plain=False, output_format="markdown", output=None, ack=False)
    inbox.add_argument(
        "--format",
        choices=("markdown", "compact", "json", "jsonl"),
        default="markdown",
        dest="output_format",
    )
    inbox.add_argument("--output", help="write inbox output to PATH, a directory, or '-' for stdout")
    inbox.add_argument("--download-files", action="store_true", help="download file attachments from rendered inbox records")
    inbox.add_argument("--download-dir", help="directory for --download-files; created if missing")
    inbox.add_argument(
        "--max-file-bytes",
        type=int,
        default=MAX_DOWNLOAD_BYTES,
        help=f"maximum bytes per downloaded Telegram file; default {MAX_DOWNLOAD_BYTES}",
    )

    download_file = subcommands.add_parser("download-file", help="download a Telegram file by file_id")
    download_file.add_argument("file_id", help="Telegram file_id from inbox JSON or JSONL output")
    download_file.add_argument("--output", required=True, help="destination file path or directory")
    download_file.add_argument("--filename", help="safe filename to use when --output is a directory")
    download_file.add_argument(
        "--max-file-bytes",
        type=int,
        default=MAX_DOWNLOAD_BYTES,
        help=f"maximum bytes to download; default {MAX_DOWNLOAD_BYTES}",
    )
    download_file.set_defaults(func=cmd_download_file)

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


def cmd_inbox(args: argparse.Namespace, *, stdout: TextIO, environ: dict[str, str]) -> int:
    token = require_env(environ, TOKEN_ENV)
    chat_id = args.chat_id or require_env(environ, CHAT_ID_ENV)
    limit = validate_inbox_limit(args.limit, ack=args.ack, output_format=args.output_format)
    download_files = bool(getattr(args, "download_files", False))
    download_dir = getattr(args, "download_dir", None)
    max_file_bytes = validate_max_file_bytes(getattr(args, "max_file_bytes", MAX_DOWNLOAD_BYTES))
    if download_dir and not download_files:
        raise CliError("--download-dir requires --download-files")
    since_seconds = parse_duration(args.since)
    client = TelegramClient(token)
    output = InboxOutput(args.output, output_format=args.output_format, stdout=stdout)
    downloader = InboxDownloader(download_dir, max_file_bytes=max_file_bytes) if download_files else None
    result = 0
    try:
        if args.ack:
            result = read_acknowledged_inbox(
                client,
                chat_id=chat_id,
                limit=limit,
                since_seconds=since_seconds,
                include_plain=args.include_plain,
                output=output,
                downloader=downloader,
                now=int(time.time()),
            )
        else:
            updates = client.get_updates(
                limit,
                timeout=0,
                allowed_updates=["message"],
            )
            records = inbox_records(
                updates,
                chat_id=chat_id,
                since_seconds=since_seconds,
                include_plain=args.include_plain,
                now=int(time.time()),
            )
            if downloader is not None:
                downloader.download_records(client, records)
            output.note_updates(updates)
            output.write_records(records)

    finally:
        output.close()
        output.print_receipt()
        if downloader is not None and should_print_download_receipts(output):
            downloader.print_receipt(stdout)
    return result


def cmd_download_file(args: argparse.Namespace, *, stdout: TextIO, environ: dict[str, str]) -> int:
    token = require_env(environ, TOKEN_ENV)
    max_file_bytes = validate_max_file_bytes(args.max_file_bytes)
    client = TelegramClient(token)
    telegram_file = client.get_file(args.file_id)
    file_path = telegram_file.get("file_path")
    if not isinstance(file_path, str) or not file_path.strip():
        raise CliError("Telegram did not return a downloadable file_path; the file may be too large")
    file_name = args.filename or file_name_from_telegram_path(file_path)
    target = resolve_download_output(args.output, file_name=file_name, explicit_filename=bool(args.filename))
    receipt = download_telegram_file(
        client,
        telegram_file=telegram_file,
        target=target,
        max_file_bytes=max_file_bytes,
    )
    print_download_receipts([receipt], stdout)
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


def validate_inbox_limit(value: int, *, ack: bool, output_format: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1 or value > MAX_INBOX_LIMIT:
        raise CliError(f"limit must be from 1 to {MAX_INBOX_LIMIT}")
    if value > TELEGRAM_UPDATE_LIMIT and not ack:
        raise CliError(f"limit above {TELEGRAM_UPDATE_LIMIT} requires --ack")
    if value > TELEGRAM_UPDATE_LIMIT and output_format == "json":
        raise CliError(f"--format json does not support --limit above {TELEGRAM_UPDATE_LIMIT}")
    return value


def validate_max_file_bytes(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise CliError("max file bytes must be a positive integer")
    if value > MAX_DOWNLOAD_BYTES:
        raise CliError(
            f"max file bytes cannot exceed the public Bot API download limit of {MAX_DOWNLOAD_BYTES} bytes"
        )
    return value


def parse_duration(value: str) -> int:
    match = re.fullmatch(r"\s*(\d+)\s*([smhd])\s*", value)
    if not match:
        raise CliError("since must be a duration like 15m, 3h, or 1d")
    amount = int(match.group(1))
    if amount <= 0:
        raise CliError("since duration must be greater than zero")
    multipliers = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    return amount * multipliers[match.group(2)]


def inbox_records(
    updates: list[dict[str, Any]],
    *,
    chat_id: str,
    since_seconds: int,
    include_plain: bool,
    now: int,
    received_index_start: int = 1,
) -> list[dict[str, Any]]:
    threshold = now - since_seconds
    records: list[dict[str, Any]] = []
    for received_index, update in enumerate(updates, start=received_index_start):
        message = update.get("message")
        if not isinstance(message, dict):
            continue
        chat = message.get("chat")
        if not isinstance(chat, dict) or str(chat.get("id")) != str(chat_id):
            continue
        message_date = message.get("date")
        if not isinstance(message_date, int) or message_date < threshold:
            continue
        forward_origin = message.get("forward_origin")
        forwarded = isinstance(forward_origin, dict)
        if not forwarded and not include_plain:
            continue
        original_date = original_message_date(forward_origin)
        records.append(
            {
                "update_id": update.get("update_id"),
                "message_id": message.get("message_id"),
                "received_index": received_index,
                "date": message_date,
                "date_iso": iso_utc(message_date),
                "original_date": original_date,
                "original_date_iso": iso_utc(original_date) if original_date is not None else None,
                "chat": render_chat(chat),
                "forwarded": forwarded,
                "forwarded_by": render_user(message.get("from")),
                "origin": render_forward_origin(forward_origin) if forwarded else plain_origin(),
                "content": extract_message_content(message),
                "attachments": extract_message_attachments(message),
            }
        )
    return sort_inbox_records(records)


def sort_inbox_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(records, key=inbox_record_sort_key)


def original_message_date(forward_origin: Any) -> int | None:
    if not isinstance(forward_origin, dict):
        return None
    date = forward_origin.get("date")
    if isinstance(date, int) and not isinstance(date, bool):
        return date
    return None


def inbox_record_sort_key(record: dict[str, Any]) -> tuple[int, int, int]:
    original_date = record.get("original_date")
    if isinstance(original_date, int) and not isinstance(original_date, bool):
        timestamp = original_date
    else:
        timestamp = int(record.get("date") or 0)
    return (timestamp, int(record.get("received_index") or 0), int(record.get("update_id") or 0))


def render_inbox_markdown(records: list[dict[str, Any]]) -> str:
    if not records:
        return "No inbox messages found."
    sections: list[str] = ["# Agentgram Inbox"]
    for record in records:
        origin = record["origin"]
        sections.append(
            "\n".join(
                [
                    f"## {inbox_display_date_iso(record)} | {origin['label']}",
                    f"- Chat: {record['chat']['label']}",
                    f"- Forwarded by: {record['forwarded_by']['label']}",
                    f"- Original source: {origin['source']}",
                    *render_timestamp_markdown_lines(record),
                    *render_attachment_markdown_lines(record.get("attachments")),
                    "",
                    record["content"],
                ]
            )
        )
    return "\n\n".join(sections)


def render_inbox_compact(records: list[dict[str, Any]], *, start_index: int = 1) -> str:
    if not records:
        return "No inbox messages found."
    lines: list[str] = []
    for index, record in enumerate(records, start=start_index):
        speaker = inbox_record_speaker(record)
        content = one_line_text(str(record["content"]))
        attachments = compact_attachment_summary(record.get("attachments"))
        if attachments:
            content = f"{content} | attachments: {attachments}"
        lines.append(f"{index}. [{inbox_display_date_iso(record)}] {speaker}: {content}")
    return "\n".join(lines)


def inbox_display_date_iso(record: dict[str, Any]) -> str:
    original_date_iso = record.get("original_date_iso")
    if isinstance(original_date_iso, str) and original_date_iso:
        return original_date_iso
    return str(record["date_iso"])


def render_timestamp_markdown_lines(record: dict[str, Any]) -> list[str]:
    original_date_iso = record.get("original_date_iso")
    if not isinstance(original_date_iso, str) or not original_date_iso:
        return []
    return [
        f"- Original sent at: {original_date_iso}",
        f"- Forwarded received at: {record['date_iso']}",
    ]


def render_attachment_markdown_lines(attachments: Any) -> list[str]:
    if not isinstance(attachments, list) or not attachments:
        return []
    lines = ["- Attachments:"]
    for attachment in attachments:
        if not isinstance(attachment, dict):
            continue
        label = attachment_label(attachment)
        download = attachment.get("download")
        if isinstance(download, dict) and download.get("path"):
            lines.append(f"  - {label} -> {download['path']}")
        else:
            lines.append(f"  - {label}")
    return lines


def attachment_label(attachment: dict[str, Any]) -> str:
    parts = [str(attachment.get("kind") or "file")]
    file_name = attachment.get("file_name")
    if isinstance(file_name, str) and file_name:
        parts.append(file_name)
    file_size = attachment.get("file_size")
    if isinstance(file_size, int):
        parts.append(f"{file_size} bytes")
    return " ".join(parts)


def compact_attachment_summary(attachments: Any) -> str:
    if not isinstance(attachments, list) or not attachments:
        return ""
    labels: list[str] = []
    for attachment in attachments:
        if not isinstance(attachment, dict):
            continue
        label = attachment_label(attachment)
        download = attachment.get("download")
        if isinstance(download, dict) and download.get("path"):
            label = f"{label} -> {download['path']}"
        labels.append(label)
    return "; ".join(labels)


def inbox_record_speaker(record: dict[str, Any]) -> str:
    if record.get("forwarded"):
        origin = record.get("origin")
        if isinstance(origin, dict):
            source = origin.get("source")
            if isinstance(source, str) and source:
                return source
    forwarded_by = record.get("forwarded_by")
    if isinstance(forwarded_by, dict):
        label = forwarded_by.get("label")
        if isinstance(label, str) and label:
            return label
    return "unknown user"


def one_line_text(value: str) -> str:
    collapsed = re.sub(r"\s+", " ", value).strip()
    return collapsed or "[empty]"


def render_inbox_jsonl(records: list[dict[str, Any]]) -> str:
    return "\n".join(json.dumps(record, sort_keys=True) for record in records)


def render_inbox_output(records: list[dict[str, Any]], output_format: str, *, start_index: int = 1) -> str:
    if output_format == "json":
        return json.dumps(records, indent=2, sort_keys=True)
    if output_format == "jsonl":
        return render_inbox_jsonl(records)
    if output_format == "compact":
        return render_inbox_compact(records, start_index=start_index)
    return render_inbox_markdown(records)


class InboxOutput:
    def __init__(self, output_path: str | None, *, output_format: str, stdout: TextIO) -> None:
        self.output_format = output_format
        self.stdout = stdout
        self.handle: TextIO | None = None
        self.path: Path | None = None
        self.record_count = 0
        self.update_count = 0
        self.byte_count = 0
        self.hasher = hashlib.sha256()
        self.next_index = 1
        if output_path and output_path != "-":
            self.path, self.handle = create_inbox_output_file(output_path, output_format=output_format)

    def note_updates(self, updates: list[dict[str, Any]]) -> None:
        self.update_count += len(updates)

    def write_records(self, records: list[dict[str, Any]]) -> None:
        rendered = render_inbox_output(records, self.output_format, start_index=self.next_index)
        if self.handle is None and rendered:
            print(rendered, file=self.stdout)
        elif rendered:
            self._write_file_text(rendered)
        self.record_count += len(records)
        self.next_index += len(records)

    def _write_file_text(self, text: str) -> None:
        if self.handle is None:
            raise CliError("inbox output file is not open")
        data = f"{text}\n".encode("utf-8")
        self.handle.write(data.decode("utf-8"))
        self.handle.flush()
        os.fsync(self.handle.fileno())
        self.byte_count += len(data)
        self.hasher.update(data)

    def close(self) -> None:
        if self.handle is not None:
            self.handle.close()
            self.handle = None

    def print_receipt(self) -> None:
        if self.path is None:
            return
        quoted_path = shlex.quote(str(self.path))
        print(
            f"wrote inbox records={self.record_count} updates={self.update_count} "
            f"format={self.output_format} bytes={self.byte_count} sha256={self.hasher.hexdigest()}",
            file=self.stdout,
        )
        print(f"path={self.path}", file=self.stdout)
        print(f"read chunks: sed -n '1,120p' {quoted_path}", file=self.stdout)
        print(f"delete after import: rm -- {quoted_path}", file=self.stdout)


class InboxRecordStage:
    def __init__(self, *, directory: Path | None = None) -> None:
        fd, path = tempfile.mkstemp(
            prefix="agentgram-inbox-stage-",
            suffix=".jsonl",
            dir=str(directory) if directory is not None else None,
        )
        self.path = Path(path)
        self.handle = os.fdopen(fd, "w", encoding="utf-8")

    def append_records(self, records: list[dict[str, Any]]) -> None:
        rendered = render_inbox_jsonl(records)
        if not rendered:
            return
        self.handle.write(f"{rendered}\n")
        self.handle.flush()
        os.fsync(self.handle.fileno())

    def read_records(self) -> list[dict[str, Any]]:
        self.handle.flush()
        records: list[dict[str, Any]] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        return records

    def close(self) -> None:
        if not self.handle.closed:
            self.handle.close()

    def cleanup(self) -> None:
        self.close()
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass


def write_staged_records_to_output(stage: InboxRecordStage, output: InboxOutput) -> None:
    output.write_records(sort_inbox_records(stage.read_records()))
    stage.cleanup()


def raise_with_retained_stage(
    exc: Exception,
    stage: InboxRecordStage,
    *,
    flush_exc: Exception | None = None,
) -> None:
    stage.close()
    if flush_exc is None:
        message = f"{exc}; staged inbox records kept at {stage.path}"
    else:
        message = (
            f"{exc}; additionally failed to render staged inbox records: {flush_exc}; "
            f"staged inbox records kept at {stage.path}"
        )
    if isinstance(exc, CliError):
        raise CliError(message) from exc
    if isinstance(exc, TelegramError):
        raise TelegramError(message) from exc
    raise RuntimeError(message) from exc


class InboxDownloader:
    def __init__(self, download_dir: str | None, *, max_file_bytes: int) -> None:
        self.download_dir = download_dir
        self._path: Path | None = None
        self.max_file_bytes = max_file_bytes
        self.receipts: list[dict[str, Any]] = []

    @property
    def path(self) -> Path:
        if self._path is None:
            self._path = resolve_download_dir(self.download_dir)
        return self._path

    def download_records(self, client: TelegramClient, records: list[dict[str, Any]]) -> None:
        for record in records:
            attachments = record.get("attachments")
            if not isinstance(attachments, list):
                continue
            for attachment in attachments:
                if not isinstance(attachment, dict):
                    continue
                target = next_available_path(self.path / sanitize_download_filename(str(attachment["file_name"])))
                receipt = download_attachment(client, attachment, target=target, max_file_bytes=self.max_file_bytes)
                attachment["download"] = receipt
                self.receipts.append(receipt)

    def print_receipt(self, stdout: TextIO) -> None:
        print_download_receipts(self.receipts, stdout)


def should_print_download_receipts(output: InboxOutput) -> bool:
    if output.path is not None:
        return True
    return output.output_format not in {"json", "jsonl"}


def resolve_download_dir(download_dir: str | None) -> Path:
    if download_dir is None:
        path = Path(tempfile.mkdtemp(prefix="agentgram-downloads-"))
        try:
            path.chmod(0o700)
        except OSError:
            pass
        return path
    path = Path(download_dir).expanduser()
    if path.exists() and not path.is_dir():
        raise CliError(f"download path is not a directory: {path}")
    if not path.exists():
        try:
            path.mkdir(mode=0o700, parents=True)
        except OSError as exc:
            raise CliError(f"cannot create download directory {path}: {exc}") from exc
    return path


def resolve_download_output(output: str, *, file_name: str, explicit_filename: bool) -> Path:
    requested = Path(output).expanduser()
    safe_name = sanitize_download_filename(file_name)
    if explicit_filename:
        if requested.exists() and not requested.is_dir():
            raise CliError("--filename requires --output to be a directory")
        if not requested.exists():
            try:
                requested.mkdir(mode=0o700, parents=True)
            except OSError as exc:
                raise CliError(f"cannot create download directory {requested}: {exc}") from exc
        return next_available_path(requested / safe_name)
    if requested.exists() and requested.is_dir():
        return next_available_path(requested / safe_name)
    if requested.exists():
        raise CliError(f"refusing to overwrite existing file: {requested}")
    parent = requested.parent
    if not parent.exists() or not parent.is_dir():
        raise CliError(f"download parent directory does not exist: {parent}")
    return requested


def next_available_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem or "file"
    suffix = path.suffix
    for index in range(2, 1000):
        candidate = path.with_name(f"{stem}-{index}{suffix}")
        if not candidate.exists():
            return candidate
    raise CliError(f"cannot find available filename for {path}")


def download_attachment(
    client: TelegramClient,
    attachment: dict[str, Any],
    *,
    target: Path,
    max_file_bytes: int,
) -> dict[str, Any]:
    file_id = attachment.get("file_id")
    if not isinstance(file_id, str) or not file_id.strip():
        raise CliError("attachment is missing file_id")
    file_size = attachment.get("file_size")
    if isinstance(file_size, int) and not isinstance(file_size, bool) and file_size > max_file_bytes:
        raise CliError(f"file is too large: {file_size} bytes; maximum is {max_file_bytes} bytes")
    telegram_file = client.get_file(file_id)
    return download_telegram_file(client, telegram_file=telegram_file, target=target, max_file_bytes=max_file_bytes)


def download_telegram_file(
    client: TelegramClient,
    *,
    telegram_file: dict[str, Any],
    target: Path,
    max_file_bytes: int,
) -> dict[str, Any]:
    file_path = telegram_file.get("file_path")
    if not isinstance(file_path, str) or not file_path.strip():
        raise CliError("Telegram did not return a downloadable file_path; the file may be too large")
    file_size = telegram_file.get("file_size")
    expected_size = file_size if isinstance(file_size, int) and not isinstance(file_size, bool) else None
    result = client.download_file(
        file_path,
        target,
        expected_size=expected_size,
        max_bytes=max_file_bytes,
    )
    return {
        "path": result["path"],
        "bytes": result["bytes"],
        "sha256": result["sha256"],
        "file_id": telegram_file.get("file_id") or "",
        "file_unique_id": telegram_file.get("file_unique_id") or "",
    }


def print_download_receipts(receipts: list[dict[str, Any]], stdout: TextIO) -> None:
    if not receipts:
        return
    print(f"downloaded files={len(receipts)}", file=stdout)
    for receipt in receipts:
        quoted_path = shlex.quote(str(receipt["path"]))
        print(
            f"path={receipt['path']} bytes={receipt['bytes']} sha256={receipt['sha256']}",
            file=stdout,
        )
        print(f"read file: {quoted_path}", file=stdout)
        print(f"delete after import: rm -- {quoted_path}", file=stdout)


def file_name_from_telegram_path(file_path: str) -> str:
    return sanitize_download_filename(file_path.rsplit("/", 1)[-1] or "telegram-file")


def create_inbox_output_file(output_path: str, *, output_format: str) -> tuple[Path, TextIO]:
    requested = Path(output_path).expanduser()
    if requested.exists() and requested.is_dir():
        target = requested / unique_inbox_output_name(output_format)
    else:
        target = requested
    parent = target.parent
    if not parent.exists() or not parent.is_dir():
        raise CliError(f"inbox output parent directory does not exist: {parent}")
    if target.exists():
        raise CliError(f"refusing to overwrite existing inbox output file: {target}")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    try:
        fd = os.open(target, flags, 0o600)
    except FileExistsError as exc:
        raise CliError(f"refusing to overwrite existing inbox output file: {target}") from exc
    except OSError as exc:
        raise CliError(f"cannot create inbox output file {target}: {exc}") from exc
    return target, os.fdopen(fd, "w", encoding="utf-8")


def unique_inbox_output_name(output_format: str) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"agentgram-inbox-{timestamp}-{os.getpid()}.{inbox_output_extension(output_format)}"


def inbox_output_extension(output_format: str) -> str:
    if output_format == "json":
        return "json"
    if output_format == "jsonl":
        return "jsonl"
    if output_format == "compact":
        return "txt"
    return "md"


def read_acknowledged_inbox(
    client: TelegramClient,
    *,
    chat_id: str,
    limit: int,
    since_seconds: int,
    include_plain: bool,
    output: InboxOutput,
    downloader: InboxDownloader | None,
    now: int,
) -> int:
    if limit > TELEGRAM_UPDATE_LIMIT:
        return read_acknowledged_inbox_buffered(
            client,
            chat_id=chat_id,
            limit=limit,
            since_seconds=since_seconds,
            include_plain=include_plain,
            output=output,
            downloader=downloader,
            now=now,
        )
    remaining = limit
    wrote_output = False
    while remaining > 0:
        batch_limit = min(TELEGRAM_UPDATE_LIMIT, remaining)
        updates = client.get_updates(batch_limit, timeout=0, allowed_updates=["message"])
        if not updates:
            if not wrote_output:
                output.write_records([])
            break
        output.note_updates(updates)
        records = inbox_records(
            updates,
            chat_id=chat_id,
            since_seconds=since_seconds,
            include_plain=include_plain,
            now=now,
        )
        if not records and wrote_output:
            break
        if downloader is not None:
            downloader.download_records(client, records)
        output.write_records(records)
        wrote_output = True
        if not records:
            break
        acknowledge_inbox_records(client, updates, records)
        remaining -= len(updates)
        if len(updates) < batch_limit:
            break
    return 0


def read_acknowledged_inbox_buffered(
    client: TelegramClient,
    *,
    chat_id: str,
    limit: int,
    since_seconds: int,
    include_plain: bool,
    output: InboxOutput,
    downloader: InboxDownloader | None,
    now: int,
) -> int:
    remaining = limit
    received_index_start = 1
    stage: InboxRecordStage | None = None
    final_output_started = False
    try:
        while remaining > 0:
            batch_limit = min(TELEGRAM_UPDATE_LIMIT, remaining)
            updates = client.get_updates(batch_limit, timeout=0, allowed_updates=["message"])
            if not updates:
                break
            output.note_updates(updates)
            records = inbox_records(
                updates,
                chat_id=chat_id,
                since_seconds=since_seconds,
                include_plain=include_plain,
                now=now,
                received_index_start=received_index_start,
            )
            received_index_start += len(updates)
            if not records:
                break
            if downloader is not None:
                downloader.download_records(client, records)
            if stage is None:
                stage = InboxRecordStage(directory=output.path.parent if output.path is not None else None)
            stage.append_records(records)
            acknowledge_inbox_records(client, updates, records)
            remaining -= len(updates)
            if len(updates) < batch_limit:
                break
        staged_records = [] if stage is None else stage.read_records()
        final_output_started = True
        output.write_records(sort_inbox_records(staged_records))
        if stage is not None:
            stage.cleanup()
            stage = None
    except Exception as exc:
        if stage is not None:
            if not final_output_started:
                try:
                    write_staged_records_to_output(stage, output)
                except Exception as flush_exc:
                    raise_with_retained_stage(exc, stage, flush_exc=flush_exc)
                stage = None
                raise
            raise_with_retained_stage(exc, stage)
        raise
    finally:
        if stage is not None:
            stage.close()
    return 0


def acknowledge_inbox_records(
    client: TelegramClient,
    updates: list[dict[str, Any]],
    records: list[dict[str, Any]],
) -> None:
    update_ids = [record.get("update_id") for record in records]
    integer_update_ids = [update_id for update_id in update_ids if isinstance(update_id, int)]
    if not integer_update_ids:
        return
    offset = max(integer_update_ids) + 1
    if offset < 0:
        raise CliError("refusing to acknowledge inbox with a negative offset")
    rendered_update_ids = set(integer_update_ids)
    hidden_update_ids = [
        update.get("update_id")
        for update in updates
        if isinstance(update.get("update_id"), int)
        and update["update_id"] < offset
        and update["update_id"] not in rendered_update_ids
    ]
    if hidden_update_ids:
        raise CliError(
            "refusing to acknowledge because some fetched updates before the ack offset were not rendered; "
            "rerun with --include-plain or narrower filters"
        )
    client.get_updates(
        1,
        offset=offset,
        timeout=0,
        allowed_updates=["message"],
    )


def extract_message_attachments(message: dict[str, Any]) -> list[dict[str, Any]]:
    attachments: list[dict[str, Any]] = []
    message_id = message.get("message_id")
    caption = message.get("caption") if isinstance(message.get("caption"), str) else None
    for kind in ("document", "audio", "video", "animation", "voice", "video_note"):
        value = message.get(kind)
        if isinstance(value, dict):
            attachment = attachment_from_file_object(kind, value, message_id=message_id, caption=caption)
            if attachment is not None:
                attachments.append(attachment)
    photo = message.get("photo")
    if isinstance(photo, list):
        best_photo = largest_photo_size(photo)
        if best_photo is not None:
            attachment = attachment_from_file_object("photo", best_photo, message_id=message_id, caption=caption)
            if attachment is not None:
                attachments.append(attachment)
    return attachments


def attachment_from_file_object(
    kind: str,
    value: dict[str, Any],
    *,
    message_id: Any,
    caption: str | None,
) -> dict[str, Any] | None:
    file_id = value.get("file_id")
    if not isinstance(file_id, str) or not file_id.strip():
        return None
    file_unique_id = value.get("file_unique_id")
    file_size = value.get("file_size")
    file_name = telegram_file_name(kind, value, message_id=message_id)
    return {
        "kind": kind,
        "file_id": file_id,
        "file_unique_id": file_unique_id if isinstance(file_unique_id, str) else "",
        "file_name": file_name["name"],
        "file_name_source": file_name["source"],
        "mime_type": value.get("mime_type") if isinstance(value.get("mime_type"), str) else "",
        "file_size": file_size if isinstance(file_size, int) and not isinstance(file_size, bool) else None,
        "caption": caption or "",
    }


def largest_photo_size(values: list[Any]) -> dict[str, Any] | None:
    candidates = [value for value in values if isinstance(value, dict) and isinstance(value.get("file_id"), str)]
    if not candidates:
        return None
    return max(candidates, key=photo_size_score)


def photo_size_score(value: dict[str, Any]) -> tuple[int, int]:
    file_size = value.get("file_size")
    if isinstance(file_size, int) and not isinstance(file_size, bool):
        size_score = file_size
    else:
        width = value.get("width")
        height = value.get("height")
        size_score = width * height if isinstance(width, int) and isinstance(height, int) else 0
    return (size_score, len(str(value.get("file_id") or "")))


def telegram_file_name(kind: str, value: dict[str, Any], *, message_id: Any) -> dict[str, str]:
    generated = generated_attachment_filename(kind, value, message_id=message_id)
    provided = value.get("file_name")
    if isinstance(provided, str) and provided.strip():
        return {"name": sanitize_telegram_filename(provided, fallback=generated), "source": "telegram"}
    title = value.get("title")
    if kind == "audio" and isinstance(title, str) and title.strip():
        return {"name": sanitize_telegram_filename(title, fallback=generated), "source": "telegram"}
    return {"name": generated, "source": "generated"}


def generated_attachment_filename(kind: str, value: dict[str, Any], *, message_id: Any) -> str:
    safe_identifier = attachment_identifier_digest(value)
    safe_message_id = re.sub(r"[^A-Za-z0-9_.-]+", "-", str(message_id or "message")).strip(".-") or "message"
    return f"{kind}-{safe_message_id}-{safe_identifier}{default_extension(kind, value)}"


def attachment_identifier_digest(value: dict[str, Any]) -> str:
    identifier = value.get("file_unique_id") or value.get("file_id")
    if not isinstance(identifier, str) or not identifier.strip():
        return "file"
    digest = hashlib.sha256(identifier.strip().encode("utf-8")).hexdigest()[:16]
    return f"id-{digest}"


def default_extension(kind: str, value: dict[str, Any]) -> str:
    mime_type = value.get("mime_type")
    if isinstance(mime_type, str):
        guessed = {
            "application/pdf": ".pdf",
            "audio/mpeg": ".mp3",
            "audio/ogg": ".ogg",
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "text/plain": ".txt",
            "video/mp4": ".mp4",
            "video/quicktime": ".mov",
        }.get(mime_type.lower())
        if guessed:
            return guessed
    return {
        "animation": ".gif",
        "audio": ".audio",
        "document": ".bin",
        "photo": ".jpg",
        "video": ".mp4",
        "video_note": ".mp4",
        "voice": ".ogg",
    }.get(kind, ".bin")


def sanitize_download_filename(value: str) -> str:
    raw = value.strip()
    if "/" in raw or "\\" in raw or Path(raw).name != raw:
        raise CliError("download filename must be a file name, not a path")
    return normalize_safe_filename(raw)


def sanitize_telegram_filename(value: str, *, fallback: str) -> str:
    candidate = re.sub(r"[\x00-\x1f/\\]+", "_", value.strip())
    try:
        return normalize_safe_filename(candidate)
    except CliError:
        return fallback


def normalize_safe_filename(value: str) -> str:
    name = Path(value).name
    name = re.sub(r"[\x00-\x1f/\\]+", "_", name).strip()
    name = name.strip(".")
    if not name or name in {".", ".."}:
        raise CliError("download filename is invalid")
    if len(name) > 160:
        stem = Path(name).stem[:120].strip(".") or "file"
        suffix = Path(name).suffix[:20]
        name = f"{stem}{suffix}"
    return name


def extract_message_content(message: dict[str, Any]) -> str:
    for field in ("text", "caption"):
        value = message.get(field)
        if isinstance(value, str) and value.strip():
            return value
    media_checks: list[tuple[str, str]] = [
        ("photo", "photo"),
        ("video", "video"),
        ("animation", "animation"),
        ("audio", "audio"),
        ("voice", "voice message"),
        ("video_note", "video note"),
        ("sticker", "sticker"),
        ("document", "document"),
        ("contact", "contact"),
        ("location", "location"),
        ("venue", "venue"),
        ("poll", "poll"),
        ("dice", "dice"),
    ]
    for key, label in media_checks:
        value = message.get(key)
        if value is None:
            continue
        details = media_details(key, value)
        return f"[{label}{': ' + details if details else ''}]"
    return "[message without text]"


def media_details(kind: str, value: Any) -> str:
    if kind == "photo" and isinstance(value, list):
        return f"{len(value)} sizes"
    if isinstance(value, dict):
        if kind == "document":
            return first_text(value, "file_name", "mime_type")
        if kind in {"video", "animation", "audio"}:
            return first_text(value, "file_name", "title", "mime_type")
        if kind == "sticker":
            return first_text(value, "emoji", "set_name")
        if kind == "contact":
            return first_text(value, "first_name", "phone_number")
        if kind == "venue":
            return first_text(value, "title", "address")
        if kind == "poll":
            return first_text(value, "question")
        if kind == "dice":
            return first_text(value, "emoji")
    return ""


def first_text(mapping: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = mapping.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return ""


def render_forward_origin(origin: Any) -> dict[str, Any]:
    if not isinstance(origin, dict):
        return plain_origin()
    origin_type = str(origin.get("type") or "unknown")
    if origin_type == "user":
        user = render_user(origin.get("sender_user"))
        source = user["label"] if user["known"] else "known user (details unavailable)"
    elif origin_type == "hidden_user":
        name = str(origin.get("sender_user_name") or "unknown user")
        source = f"{name} (privacy-hidden user)"
    elif origin_type == "chat":
        chat = render_chat(origin.get("sender_chat"))
        source = chat["label"]
        signature = origin.get("author_signature")
        if signature:
            source = f"{source}; signature: {signature}"
    elif origin_type == "channel":
        chat = render_chat(origin.get("chat"))
        source = chat["label"]
        message_id = origin.get("message_id")
        if message_id is not None:
            source = f"{source}; original message_id: {message_id}"
        signature = origin.get("author_signature")
        if signature:
            source = f"{source}; signature: {signature}"
    else:
        source = "unknown forwarded source"
    return {"type": origin_type, "label": "forwarded", "source": source}


def plain_origin() -> dict[str, str]:
    return {"type": "plain", "label": "direct", "source": "direct message to bot"}


def render_user(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {"id": None, "username": "", "name": "", "label": "unknown user", "known": False}
    name = " ".join(str(part) for part in (value.get("first_name"), value.get("last_name")) if part)
    username = str(value.get("username") or "")
    label = name or (f"@{username}" if username else "unknown user")
    if username and name:
        label = f"{name} (@{username})"
    return {
        "id": value.get("id"),
        "username": username,
        "name": name,
        "label": label,
        "known": label != "unknown user",
    }


def render_chat(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {"id": None, "type": "unknown", "title": "", "username": "", "label": "unknown chat"}
    title = str(
        value.get("title")
        or " ".join(str(part) for part in (value.get("first_name"), value.get("last_name")) if part)
        or ""
    )
    username = str(value.get("username") or "")
    label = title or (f"@{username}" if username else str(value.get("id") or "unknown chat"))
    if username and title:
        label = f"{title} (@{username})"
    return {
        "id": value.get("id"),
        "type": str(value.get("type") or "unknown"),
        "title": title,
        "username": username,
        "label": label,
    }


def iso_utc(timestamp: int) -> str:
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat().replace("+00:00", "Z")


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
