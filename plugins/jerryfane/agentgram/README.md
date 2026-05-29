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

To discover a chat id, first send a message to the bot in Telegram, then run:

```sh
agentgram chat-id
```

For raw Telegram `getUpdates` output:

```sh
agentgram chat-id --raw
```

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
2. Run `agentgram send "message"`, or `bin/agentgram send "message"` only from
   this repository checkout, if setup is valid.
3. Avoid direct Telegram API calls unless the user explicitly asks to bypass the
   Agentgram CLI.

## Troubleshooting

- Bot was not started: open Telegram, send any message to the bot, then run
  `agentgram chat-id` again.
- Bad token: run `agentgram doctor`; malformed tokens fail locally, and revoked
  or wrong tokens fail the Telegram `getMe` check.
- Missing chat id: set `TELEGRAM_CHAT_ID`, or pass `--chat-id <id>` for a
  one-off send after the user provides the target chat.
- Forbidden chat: add the bot to the target chat or start a private chat with
  it, then retry after confirming the chat id.
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

Released. Agentgram `v0.1.x` includes the Telegram CLI, Codex skill packaging,
public Codex marketplace metadata, update ergonomics, release docs, and CI
checks.
