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

## Update Workflow

Use `$AGENTGRAM_CMD update --check` for a read-only status check on git-based
installs. Use `$AGENTGRAM_CMD update` only when the user asks to update
Agentgram. The update command refuses dirty git checkouts, runs
`git pull --ff-only`, validates the local CLI/plugin files, and prints any Codex
refresh instructions it can detect. For Codex marketplace installs, update with
`codex plugin marketplace upgrade` and then reinstall `agentgram@agentgram`.
