---
name: casefile
description: Use when tracking security investigations, bug bounty findings, CTF leads, audit evidence, exploit chains, dead ends, or reports in the Casefile ledger through Codex.
license: MIT
---

# Casefile

Use Casefile to maintain durable security investigation state across Codex turns. Prefer the MCP tools from the `casefile` server when they are available.

## Workflow

1. Check existing cases before opening a new one with `casefile_list` or `casefile_search`.
2. Open new leads with `casefile_add` as `hypothesis` or `investigating`.
3. Promote cases with `casefile_update` only after materially new evidence, proof, impact, blockers, remediation, or status changes.
4. Mark `confirmed` only when evidence and a PoC or repro are recorded.
5. Use `casefile_link` and `casefile_unlink` for exploit chains. Do not edit linked case IDs directly.
6. Use `casefile_report` only for confirmed or already reported cases.
7. Use `killed` for disproven, duplicate, or dead-end leads, and include evidence, blockers, next step, or assumptions explaining why.

## Tool Map

- `casefile_add`: create a new case.
- `casefile_update`: update an existing case.
- `casefile_get`: read one case by ID.
- `casefile_list`: list cases with filters and pagination.
- `casefile_search`: search all fields or a scoped field such as `evidence`, `impact`, or `poc`.
- `casefile_link`: bidirectionally link two cases.
- `casefile_unlink`: remove a bidirectional case link.
- `casefile_report`: write a markdown report for a confirmed or reported case.

## Storage

The Codex plugin uses project-scoped storage by default at `.casefile/casefile.jsonl`. Use `CASEFILE_PATH` to force a specific ledger path or `CASEFILE_SCOPE=global` to use `~/.casefile/casefile.jsonl`.

Legacy pi environment variables remain supported for the pi extension.
