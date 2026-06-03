---
name: agentgram
description: Send explicit, user-requested Telegram messages and files from an agent session through the local Agentgram command-line tool.
---

# Agentgram

Agentgram is a small Telegram messaging helper for agents. Use this skill when
the user asks to send a Telegram message or file, verify Telegram messaging
setup, find a chat id, or update the local Agentgram install.

Before sending messages, prefer the installed `agentgram` command. If it is not
on `PATH` and Agentgram is installed as a Codex plugin, resolve the plugin root
from this skill file at `<plugin-root>/skills/agentgram/SKILL.md` and use
`<plugin-root>/bin/agentgram` (`../../bin/agentgram` relative to this file). Use
`./bin/agentgram` only after verifying the current checkout is Agentgram itself,
with `.codex-plugin/plugin.json` name `agentgram` and
`skills/agentgram/SKILL.md` present. In any other repository, report that
Agentgram is not installed instead of running project-local fallback scripts or
making an ad hoc Telegram API call.

## Commands

```sh
agentgram send "message text"
agentgram send --split "long message text"
agentgram send --as-file --filename report.md "long message text"
agentgram send-file ./report.md --caption "Report"
agentgram inbox
agentgram inbox --limit 100
agentgram inbox --limit 500 --ack
agentgram inbox --since 3h
agentgram inbox --include-plain
agentgram inbox --format compact --output /tmp
agentgram inbox --format jsonl --output /tmp
agentgram inbox --ack
agentgram inbox --include-plain --download-files --download-dir /tmp --ack
agentgram download-file <file_id> --output /tmp
agentgram chat-id
agentgram doctor
agentgram update
agentgram update --check
```

## Required Setup

Agentgram reads:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

Secrets must come from environment variables or a user-owned local config file,
never from tracked repository files, chat output, PR bodies, logs, or generated
plugin packages.

## Send Workflow

1. Resolve the safe Agentgram command as `AGENTGRAM_CMD`: `agentgram` on
   `PATH`, `<plugin-root>/bin/agentgram` from an installed Agentgram plugin, or
   `./bin/agentgram` only from a verified Agentgram checkout.
2. Run `$AGENTGRAM_CMD doctor` before sending, unless the user explicitly asks
   for a best-effort send without preflight.
3. If `doctor` only fails because `TELEGRAM_CHAT_ID` is missing and the user
   provided the target chat id for this message, proceed with
   the selected send command plus `--chat-id <id>`, such as
   `$AGENTGRAM_CMD send --chat-id <id> "message"` or
   `$AGENTGRAM_CMD send-file --chat-id <id> <path>`.
4. If `doctor` reports missing `TELEGRAM_CHAT_ID` and the user did not provide
   a chat id, run `$AGENTGRAM_CMD chat-id` only after the user has messaged the
   bot or added it to the target chat.
5. Send only the exact user-requested Telegram content.
6. Use `--chat-id` only when the user provided a specific override for that
   message.
7. Use `--parse-mode HTML` or `--parse-mode MarkdownV2` only when the user asks
   for formatted Telegram output or the message clearly requires it.

Use `$AGENTGRAM_CMD send "message text"` for explicit short text messages.
Plain text messages are limited to 4096 visible characters by Telegram.

Use `$AGENTGRAM_CMD send-file <path>` when the user explicitly asks to send a
file, report, log, diff, archive, generated artifact, or named local path. Do
not glob paths, archive directories, or infer a file to send. If the requested
path is ambiguous, ask the user to identify the exact file before sending.
`send-file` accepts `--caption`, `--parse-mode HTML|MarkdownV2`, `--silent`,
and `--chat-id`.

Use `$AGENTGRAM_CMD send --split "long text"` only when the user asks to send
long text or the text exceeds Telegram's message limit and should remain in the
chat as text. Split mode currently supports plain text only; do not combine it
with `--parse-mode`.

Use `$AGENTGRAM_CMD send --as-file --filename report.md "long text"` when the
user asks to send long text as a document, or when a long report/log/diff is
better delivered as a file. Omit `--filename` only when the default
`agentgram-message.txt` is acceptable.

Do not send automatic status updates merely because an agent task completed.
Do not send files automatically just because a task generated one. Agentgram
sends should be explicit and user-requested.

## Inbox Workflow

Use `$AGENTGRAM_CMD inbox` when the user asks to read recent Telegram messages
they forwarded to the Agentgram bot, such as "read the recent messages I
forwarded to you" or "import the Telegram context I just forwarded".

Use `$AGENTGRAM_CMD inbox --limit 100` when the user asks for the last 100
pending forwarded messages without consuming them. Peek reads support at most
100 pending updates. Use `$AGENTGRAM_CMD inbox --limit 370 --ack --format
compact --output /tmp` when the user asks to read and consume a larger
forwarded batch, such as "the last 370 messages"; acknowledged reads support up
to 500 pending updates, read Telegram in 100-update batches, stage each rendered
batch durably before acknowledging it, and render the final output globally
sorted after all batches are imported. Use `$AGENTGRAM_CMD inbox --since 3h`
when the user asks for messages from the last 3 hours. Use
`$AGENTGRAM_CMD inbox --include-plain` when the user says they also sent direct
notes to the bot, or that the forwarded context is mixed with direct messages.

The default inbox mode is `--peek`, which reads without consuming Telegram
updates. Use `$AGENTGRAM_CMD inbox --ack` only after a successful import, or
when the user explicitly asks to consume or clear the forwarded messages.
For large inbox imports, prefer `--format compact --output /tmp` so Codex can
read the generated private file in chunks and avoid terminal-output truncation.
Read the generated path with commands such as `sed -n '1,120p' <path>`, then
delete only that exact generated file with `rm -- <path>` after importing the
context. Use `--format json` only for single-batch inbox reads up to 100
updates; use `--format jsonl` for structured multi-batch output.

Inbox uses Telegram Bot API pending updates only. It is not full Telegram chat
history and does not use an MTProto user session. Pending updates can expire,
can be consumed by another process using the same bot token, and cannot be read
with `getUpdates` while an outgoing webhook is active. If Telegram reports a
webhook conflict, tell the user to remove the webhook or use a separate bot
token for Agentgram inbox reads.

Agentgram does not write message content, captions, sender names, raw updates,
or transcripts to local files unless the user or agent explicitly passes
`--output PATH`. Forwarded authorship depends on Telegram `forward_origin`
metadata and sender privacy settings; hidden or uncertain authors are marked in
the output. Forwarded inbox output is ordered by the original Telegram
`forward_origin.date` when available, with bot receive order as the tie-breaker.
In JSON/JSONL, `original_date_iso` is the original group timestamp and
`date_iso` is when the forwarded copy reached the Agentgram bot.

Use `$AGENTGRAM_CMD inbox --include-plain --download-files --download-dir /tmp
--ack` when the user asks to download or inspect a file they sent or forwarded
to the Agentgram bot. The file must be sent or forwarded to the bot chat; files
sent only to the user's personal saved messages are not visible to the bot.
If multiple files are present, list the downloaded paths or attachment names and
ask which one to inspect unless the user's request identifies the file clearly.

Use `$AGENTGRAM_CMD download-file <file_id> --output /tmp` only when you already
have a concrete `file_id` from `agentgram inbox --format json` or `--format
jsonl`. Prefer `inbox --download-files` for normal user requests because agents
usually do not know the `file_id` ahead of time.

Downloaded files are written locally with private permissions and no overwrite,
and Agentgram prints path, byte count, SHA-256 digest, read hints, and delete
hints. Do not print or reconstruct Telegram file download URLs because they
contain the bot token. Public Telegram Bot API downloads through `getFile` are
limited to 20 MB; for larger files, tell the user that Agentgram would need a
future local Bot API server setup or another transfer path.

## Update Workflow

Use `$AGENTGRAM_CMD update --check` for a read-only status check on git-based
installs. Use `$AGENTGRAM_CMD update` only when the user asks to update
Agentgram. The update command refuses dirty git checkouts, runs
`git pull --ff-only`, validates the local CLI/plugin files, and prints any Codex
refresh instructions it can detect. For Codex marketplace installs, update with
`codex plugin marketplace upgrade` and then reinstall `agentgram@agentgram`.
