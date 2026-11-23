---
name: docs-repo
description: Docs & Repo skill. Invoke via docs-repo agent or when updating README/ADRs; do not auto-load.
version: 0.1.1
category: core
disable-model-invocation: true
---

# Docs & Repo

Keep README, setup/runbooks, and ADRs current when behavior or architecture changes.

## Standard (required)

Documentation belongs to the **project**, not the chat or the author. Follow rule `docs-professional-standard`:

- Professional, inheritable voice (system behavior, not “today I…”)
- No transient references: people, unrelated projects, session drama, client-specific workspace IDs
- Timeless where possible; verify against code
- Docs/HANDOFF/inventories are **indicative**; delivery truth comes from code, APIs, infra, SHAs, and published artifacts (never docs alone)
- Inheritance test: a new maintainer can use it in 12 months without the chat

Also follow `agent-output-hygiene` (no agent metalinguage in artifacts).
