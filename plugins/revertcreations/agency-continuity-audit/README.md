# Agency Continuity Audit

A local, read-only Codex plugin that finds evidence gaps in persistent agent
workspaces.

Long-running agents can appear healthy while their objective has drifted, their
memory database is corrupt, their scheduler status is stale, or their revenue
claim is only a boolean. This audit distinguishes durable evidence from reported
claims and marks missing proof as unproven.

## Install

```bash
npx codex-marketplace add revertcreations/agency-continuity-audit --plugin --project --yes
```

Then ask Codex:

> Audit this workspace's agent continuity.

You can also run the deterministic auditor directly:

```bash
python3 skills/audit-agency-continuity/scripts/audit_continuity.py \
  --project /path/to/workspace \
  --state-dir /path/to/durable-state
```

Add `--json` for machine-readable output.

## What it checks

- An explicit objective or boundary source exists.
- Durable state exists and SQLite files pass `PRAGMA quick_check`.
- A structured correction or supersession path exists.
- Continuity evidence is current rather than stale.
- Declared objective hashes still match the workspace.
- Recovery has actually been observed across different machine boots.
- Human-authority exceptions are represented instead of silently omitted.
- Commercial claims include mature, settled-payout evidence and arithmetic.
- Scheduled-unit health is labeled as reported evidence, not an independent probe.

The report uses `pass`, `warn`, and `fail`. A warning means **unproven**, not
achieved.

## Privacy and claim boundary

The plugin runs locally, makes no network requests, installs no dependencies,
and does not modify the workspace or state directory. It reports cited paths and
compact evidence; inspect output before sharing it.

This is an evidence-surface audit, not a security certification. It does not
prove agent quality, safety, demand, or revenue merely because no failure was
found. Scheduler and continuity booleans remain self-reported unless backed by
independent observations.

## Requirements

- Python 3.10 or newer
- Optional SQLite state for integrity and correction-path checks

MIT licensed. Issues and reproducible false-positive reports are welcome.
