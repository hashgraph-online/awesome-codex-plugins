---
name: audit-agency-continuity
description: Run a read-only continuity and evidence audit of a persistent or autonomous agent workspace. Use when Codex must assess whether goals, memory, corrections, authority boundaries, commercial claims, schedules, or restart recovery are durable and verifiable; when an agent claims it can continue unattended; or before trusting a long-running multi-agent system after a session or machine restart.
---

# Audit Agency Continuity

Run the deterministic auditor before interpreting narrative documents:

```bash
python3 scripts/audit_continuity.py --project <workspace> --state-dir <state-directory>
```

Use `--json` for machine consumption. The command is read-only.

Then:

1. Treat `fail` as a contradicted or missing durability requirement.
2. Treat `warn` as unproven, not achieved.
3. Inspect cited paths only for consequential findings; do not load an entire Markdown corpus by default.
4. Separate operational continuity from commercial success. A healthy scheduler or memory database never proves revenue.
5. Never repair findings unless the user asked for changes. For a requested repair, preserve existing state, add tests, and rerun the audit.
6. Report the smallest set of decisive findings: what survives restart, what can silently drift, what requires human authority, and which claimed outcome lacks external evidence.

Do not infer that numerous documents equal memory, that a timer equals successful execution, that model agreement equals external evidence, or that gross or pending revenue proves owner-available contribution.
