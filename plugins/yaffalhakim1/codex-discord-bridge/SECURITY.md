# Security Policy

## Supported versions

Only the latest commit on `master` is supported. Pull before reporting;
fixes land on master and are not backported to tags.

## Reporting a vulnerability

Use GitHub's private vulnerability reporting on this repository
(Security tab > Report a vulnerability), or contact [@yaffalhakim1](https://github.com/yaffalhakim1)
directly if that is unavailable. Please do not open a public issue for
something you believe is exploitable.

Include:

- What the attacker can do and how they reach it
- The bridge component involved (Discord listener, approval flow, WebSocket
  client, state file handling)
- Reproduction steps or a proof of concept

## Scope notes

The bridge runs locally and holds two secrets: `DISCORD_BOT_TOKEN` in `.env`
and whatever auth Codex CLI itself has. Of particular interest:

- Any path that leaks the bot token or state file contents (`data/state.json`)
- Bypassing the single-controller check in `src/discord.rs` (only
  `DISCORD_CONTROLLER_USER_ID` should be able to drive Codex)
- Approval buttons accepting input from users other than the controller
- Command injection from Discord message content into the Codex process

## What is out of scope

- Self-hosted misconfiguration (publicly shared `.env`, inviting the bot to
  a server where others can message it)
- The upstream Codex CLI; report those to openai/codex
