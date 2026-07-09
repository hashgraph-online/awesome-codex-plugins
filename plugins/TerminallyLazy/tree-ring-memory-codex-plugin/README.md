# Tree Ring Memory Codex Plugin

Tree Ring Memory is a local-first memory lifecycle practice for Codex agents.

This plugin packages one Codex skill that teaches agents when to recall, write,
audit, consolidate, and forget project memory using the open-source
[Tree Ring Memory](https://github.com/TerminallyLazy/Tree-Ring-Memory) CLI.

It does not run a background service, scrape chats, or capture transcripts.
The active agent chooses when a memory action is useful, source-linked, and
privacy-safe.

## What It Adds

- Recall before context-dependent project work.
- Concise memory writes for validated decisions, lessons, warnings, and user
  preferences.
- Evidence-backed outcomes through `tree-ring evidence`.
- Explicit forgetting, redaction, and supersession guidance.
- DOX and Revolve adapter usage with dry-run-first guardrails.

## Install Tree Ring Memory

macOS ARM64 with Homebrew:

```bash
brew tap TerminallyLazy/tree-ring
brew install tree-ring
```

For other install paths, use the canonical project README:
<https://github.com/TerminallyLazy/Tree-Ring-Memory#install>

## Use

After installing this plugin in Codex, ask:

```text
Use Tree Ring Memory to recall durable project context before editing.
Use Tree Ring Memory to capture this validated lesson without storing a transcript.
Use Tree Ring Memory to audit stale or sensitive memory before closeout.
```

The skill will look for project-local `.tree-ring/SKILL.md` and
`.tree-ring/CLI.md` files first. If they are absent, it falls back to the public
CLI commands documented in the main framework repository.

## Canonical Project

- Framework repo: <https://github.com/TerminallyLazy/Tree-Ring-Memory>
- Launch page: <https://terminallylazy.github.io/Tree-Ring-Memory/>
- Homebrew tap: <https://github.com/TerminallyLazy/homebrew-tree-ring>

## Security

This plugin ships instructions only. It does not include remote MCP servers,
webhooks, analytics, credentials, or networked runtime code.

See [SECURITY.md](SECURITY.md) for disclosure and privacy guidance.
