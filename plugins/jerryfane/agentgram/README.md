# Agentgram

[![CI](https://github.com/jerryfane/agentgram/actions/workflows/ci.yml/badge.svg)](https://github.com/jerryfane/agentgram/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/jerryfane/agentgram)](https://github.com/jerryfane/agentgram/releases)
[![PyPI](https://img.shields.io/pypi/v/agentgram-tg)](https://pypi.org/project/agentgram-tg/)
[![License](https://img.shields.io/github/license/jerryfane/agentgram)](LICENSE)

Agentgram is a Codex Telegram plugin and agent-neutral messaging helper. It lets
Codex and other local AI agents send explicit, user-requested Telegram messages
through a Telegram bot token and chat id.

Agentgram is intentionally local-first. It does not run a hosted service, and it
does not send automatic completion notifications unless a future task explicitly
adds that behavior.

Use Agentgram when you want a Telegram notification plugin for AI agents, a
simple way to send Telegram messages from Codex, or a reusable local CLI for
agent messaging via a bot token.

## Requirements

- Python 3.12 or newer.
- A Telegram bot token from BotFather.
- A Telegram chat where the bot has been started or added.

## Configuration

Set secrets in your shell or agent runtime environment:

```sh
export TELEGRAM_BOT_TOKEN="123456:bot-token"
export TELEGRAM_CHAT_ID="123456789"
```

Do not put real tokens in tracked files. `.env` and `.env.*` are ignored for
local use, but environment variables are the preferred setup.

For local setup templates, copy [.env.example](.env.example). It contains
variable names only.

## Usage

Install the released CLI from PyPI:

```sh
pipx install agentgram-tg
```

Or install from a git checkout, then put the CLI on your `PATH`:

```sh
git clone https://github.com/jerryfane/agentgram.git ~/.agentgram/agentgram
mkdir -p ~/.local/bin
ln -sf ~/.agentgram/agentgram/bin/agentgram ~/.local/bin/agentgram
```

Run the local CLI:

```sh
agentgram doctor
agentgram send "deploy finished"
agentgram send --silent --no-preview "quiet update"
agentgram send --parse-mode HTML "<b>deploy finished</b>"
```

Send an explicit local file when a user asks for a report, log, diff, archive,
or generated artifact:

```sh
agentgram send-file ./report.md --caption "Report"
agentgram send-file --chat-id 123456789 ./dist/agentgram-plugin.zip
```

Telegram limits bot text messages to 4096 visible characters after entity
parsing. By default, Agentgram rejects over-limit `send` input so agents do not
silently truncate messages. Choose an explicit long-text mode when needed:

```sh
agentgram send --split "long plain text..."
agentgram send --as-file "long plain text..."
agentgram send --as-file --filename report.md "long plain text..."
```

`--split` sends counted plain-text chunks such as `[1/3]` and currently rejects
`--parse-mode`. `--as-file` writes a temporary UTF-8 document and sends it with
Telegram `sendDocument`; no tracked or durable temp file is left behind. Telegram
document uploads through bots are currently limited to 50 MB, and document
captions are limited to 1024 visible characters after entity parsing.

To discover a chat id, first send a message to the bot in Telegram, then run:

```sh
agentgram chat-id
```

For raw Telegram `getUpdates` output:

```sh
agentgram chat-id --raw
```

### Forwarded Inbox

To let an agent read recent context from Telegram without a user-session login,
manually forward the relevant group, channel, or private-chat messages into the
Agentgram bot chat, then ask the agent to read them. The agent can run:

```sh
agentgram inbox
agentgram inbox --limit 100
agentgram inbox --limit 500 --ack
agentgram inbox --since 3h
agentgram inbox --include-plain
agentgram inbox --format compact --output /tmp
agentgram inbox --format jsonl --output /tmp
agentgram inbox --include-plain --download-files --download-dir /tmp --ack
agentgram download-file <file_id> --output /tmp
```

The default inbox mode is equivalent to:

```sh
agentgram inbox --limit 100 --since 24h --forwarded-only --format markdown --peek
```

`--forwarded-only` excludes direct notes sent to the bot. Use
`--include-plain` when the forwarded context is mixed with direct notes to the
agent. `--format markdown` is intended for human-readable transcripts,
`--format compact` is line-oriented context for agents, `--format json` emits a
single stable JSON array, and `--format jsonl` emits one stable JSON record per
line.

Inbox reads pending Telegram Bot API updates only. It is not full Telegram chat
history, does not use MTProto user sessions, and does not run a webhook
receiver. By default, Agentgram does not store message text, captions, sender
names, raw updates, or transcripts in local files. `--output PATH` is the
explicit exception for large imports and writes only to the path requested by
the user or agent. Pending updates can expire, and they can be consumed by
another process using the same bot token.

`agentgram inbox` defaults to `--peek`, so repeated runs do not consume updates.
Peek reads are capped at 100 pending updates, matching Telegram's per-call
`getUpdates` limit. Use `--ack` only after a successful import, or when you
explicitly want to consume the rendered updates:

```sh
agentgram inbox --ack
agentgram inbox --limit 370 --ack
```

With `--ack`, Agentgram can consume up to 500 pending updates by reading
Telegram in batches of 100. Multi-batch reads first write every rendered batch
to a private JSONL staging file and flush it before acknowledging that batch;
the final user-facing output is rendered globally sorted after all batches are
imported. `--format json` is available for single-batch reads up to 100
updates; use `jsonl` for structured multi-batch imports. Telegram acknowledges
updates by offset, which also consumes all lower pending update ids. Agentgram
refuses to ack when doing so would skip fetched updates that were filtered out
and not rendered. Rerun with `--include-plain` or a narrower filter if that
happens.

For large agent imports, prefer a temporary explicit output file so terminal
output truncation does not drop the middle of the forwarded context:

```sh
agentgram inbox --limit 370 --ack --format compact --output /tmp
sed -n '1,120p' /tmp/agentgram-inbox-YYYYMMDDTHHMMSSZ-PID.txt
rm -- /tmp/agentgram-inbox-YYYYMMDDTHHMMSSZ-PID.txt
```

When `--output` points to a directory, Agentgram creates a unique private file
with mode `0600`, prints a receipt with the path, byte count, SHA-256 digest,
and suggested read/delete commands, and keeps message content out of stdout.
It refuses to overwrite existing output files. Use `--output -` to force stdout.

### Telegram File Downloads

To let an agent read a file from Telegram, send or forward the file to the
Agentgram bot chat. Sending a file only to your own saved messages is not
visible to the bot. The agent can then run:

```sh
agentgram inbox --include-plain --download-files --download-dir /tmp --ack
```

`--download-files` downloads file attachments from the rendered inbox records.
Supported attachment types include documents, photos, audio, video, animations,
voice messages, and video notes. `--download-dir` is created if it is missing;
when omitted, Agentgram creates a private temporary directory. Downloaded files
use safe local names, are written with mode `0600`, never overwrite an existing
file, and produce receipts with path, byte count, SHA-256 digest, read hints,
and delete hints. Telegram file URLs are never printed because they contain the
bot token.

With `--ack`, Agentgram acknowledges the fetched Telegram updates only after
the inbox records are rendered and all requested files download successfully.
If a download fails, the fetched updates are left pending so the user can retry
or choose a narrower command.

For advanced workflows where an agent already has a `file_id` from
`--format json` or `--format jsonl`, download that specific file directly:

```sh
agentgram download-file <file_id> --output /tmp
agentgram download-file <file_id> --output /tmp --filename report.pdf
agentgram download-file <file_id> --output ./report.pdf
```

The public Telegram Bot API currently limits bot downloads through `getFile` to
20 MB. Agentgram enforces that limit by default. Telegram's local Bot API server
is the official future path for larger downloads, but Agentgram does not deploy
or configure that server.

Forwarded authorship depends on Telegram's `forward_origin` metadata and the
sender's privacy settings. Agentgram shows the user who forwarded the message to
the bot and, when Telegram provides it, the original user, hidden-user name,
source chat, or source channel. Hidden or uncertain authorship is marked in the
transcript.

Forwarded inbox records are ordered by the original message timestamp from
Telegram's `forward_origin.date` when available, with bot receive order as the
tie-breaker. Human-readable output shows the original group timestamp first.
Structured JSON/JSONL output also includes the forwarded-copy bot timestamp as
`date_iso` and the original timestamp as `original_date_iso`.

`getUpdates` cannot be used while the same bot has an outgoing webhook set.
Remove the webhook or use a bot token dedicated to Agentgram inbox reads.

To check whether the local git checkout is current using existing local refs, or
to update with a fast-forward-only pull:

```sh
agentgram update --check
agentgram update
```

`agentgram update` refuses dirty worktrees, validates the checkout after pulling,
and prints runtime-specific next steps when it can detect them. Codex plugin
users should reinstall or refresh the plugin and start a new thread so updated
skills are loaded.

## Codex Plugin

The Codex plugin skill lives in `skills/agentgram/SKILL.md`, with the plugin
manifest at `.codex-plugin/plugin.json`. The skill tells Codex to use the local
`agentgram` CLI as the execution path. This repository also contains a public
Codex marketplace file so Agentgram can be installed as a Codex Telegram plugin.

To install Agentgram from the public Codex marketplace file in this repository:

```sh
codex plugin marketplace add jerryfane/agentgram --ref main
codex plugin add agentgram@agentgram
```

Start a new Codex thread after installing so the Agentgram skill is loaded.
Use `codex plugin marketplace upgrade agentgram` before reinstalling when you
want newer Agentgram releases.

When a user asks an agent to send a Telegram message, the agent should:

1. Run `agentgram doctor`, or `bin/agentgram doctor` only from this repository
   checkout.
2. Run `agentgram send "message"` for short text, `agentgram send-file <path>`
   for an explicit local file, or `agentgram send --split/--as-file` for long
   text, if setup is valid.
3. Run `agentgram inbox` when the user asks to read recently forwarded Telegram
   messages.
4. Run `agentgram inbox --include-plain --download-files --download-dir /tmp
   --ack` when the user asks to download and inspect a file they sent or
   forwarded to the Agentgram bot. If multiple files are present, list them and
   ask which one to inspect.
5. Confirm ambiguous file paths before sending and never send generated files
   automatically just because a task completed.
6. Avoid direct Telegram API calls unless the user explicitly asks to bypass the
   Agentgram CLI.

## Troubleshooting

- Bot was not started: open Telegram, send any message to the bot, then run
  `agentgram chat-id` again.
- Bad token: run `agentgram doctor`; malformed tokens fail locally, and revoked
  or wrong tokens fail the Telegram `getMe` check.
- Missing chat id: set `TELEGRAM_CHAT_ID`, or pass `--chat-id <id>` for a
  one-off send after the user provides the target chat.
- Message too long: use `agentgram send --split` for plain text chunks or
  `agentgram send --as-file --filename <name>` to deliver it as a document.
- File rejected: verify the path is a readable, non-empty regular file at or
  below Telegram's bot upload limit.
- Download rejected: verify the file was sent or forwarded to the Agentgram bot
  chat and is within the public Bot API download limit of 20 MB.
- Forbidden chat: add the bot to the target chat or start a private chat with
  it, then retry after confirming the chat id.
- Inbox is empty: forward messages to the bot chat and rerun before Telegram's
  pending updates expire. Check that another process has not consumed updates
  from the same bot token.
- Inbox ack is refused: rerun with `--include-plain` or narrower filters so
  Agentgram does not skip unrendered pending updates.
- Webhook conflict: remove the outgoing webhook or use a separate bot token for
  Agentgram inbox reads.
- Telegram API errors: Agentgram prints Telegram's error description without the
  bot token. Re-run `agentgram doctor` before retrying.

## Release Checks

Before release, run:

```sh
python3 -m unittest discover -s tests -v
python3 scripts/validate_manifest.py
git diff --check
```

See [docs/release-checklist.md](docs/release-checklist.md) for the full
checklist and fresh-clone smoke.

## Status

Released. Agentgram `v0.2.x` includes the Telegram CLI, file sending, long-text
delivery modes, Codex skill packaging, public Codex marketplace metadata, update
ergonomics, release docs, and CI checks.
