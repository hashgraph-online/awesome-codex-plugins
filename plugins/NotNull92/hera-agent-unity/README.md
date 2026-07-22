# Hera Unity Codex Plugin

This plugin teaches Codex to use the `hera-agent-unity` CLI for live Unity Editor inspection, changes, and verification.

## Prerequisites

Install the CLI and Unity connector by following the [main project README](https://github.com/NotNull92/hera-agent-unity#install), then open the Unity project before using the skill.

## Verification

The skill starts with `doctor --json`, `status`, and compact tool discovery. After changes it re-reads the affected state, checks Unity console errors, and runs focused tests or Play Mode checks when appropriate.

## Security

Hera communicates with the local Unity Editor over localhost. Review commands before approving work that changes project assets or executes arbitrary C#.
