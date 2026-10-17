# Security Policy

## Supported versions

The latest commit on `main` is supported. Fixes land there; there are no backport
branches and no maintained older releases.

## Reporting a vulnerability

Report privately through GitHub: open the **Security** tab of
<https://github.com/Jovan1666/commandcode-usage> and choose **Report a
vulnerability**. If that channel is not available to you, open a normal issue that
says only that you have a security report and how to reach you — put no details in
the issue itself.

The full policy — credential handling, and what is in and out of scope — is the
repository's [SECURITY.md](https://github.com/Jovan1666/commandcode-usage/blob/main/SECURITY.md).

## What this adapter touches

- Runs as a `UserPromptSubmit` hook, so it executes once per turn. Codex asks you to
  trust the hook by hash at install time; that trust prompt is the boundary.
- Reads the hook's stdin JSON (Codex passes `model`, `cwd`, `turn_id`, `session_id`)
  and `~/.codex/config.toml`, to find the provider route.
- Writes `~/.commandcode-usage/models.json`, the 24 h cache of the public model
  catalog, and nothing else.
- Its only output is one `systemMessage` line for the TUI. Nothing else is written
  to stdout, because the host treats hook stdout as instructions.

Codex passes `transcript_path` but leaves it empty, so this adapter never opens a
transcript at all.
