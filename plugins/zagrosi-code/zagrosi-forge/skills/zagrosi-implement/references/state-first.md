# State-first lean

An opt-in lean mode that keeps what the next session needs: `plan.md`, `status.json`
and append-only `notes.md` beside the unchanged brief. Forge checks their structure,
not their prose. Use it only when the user asks for state-first, or when the planning
directory already has `status.json`; every later command follows that file. Standard
plans never convert, and team reservations need the standard plan.

## Plan

Write `plan.md`, or run setup first to draft it from the brief:

```markdown
# Plan: labels

## Goal
Trim label edges without changing case.

## Acceptance
- REQ-001: labels lose edge whitespace.

## Sections
| Section | Files | Done when |
|---|---|---|
| section-01-trim | src/labels.py, tests/test_labels.py | `pytest tests/test_labels.py` passes |
```

```bash
python3 "{plugin_root}/scripts/zagrosi_skills.py" plan-setup --file "{spec_file}" --target-dir "{target_dir}" --state-first
```

Setup accepts lean depth only. It writes `status.json`, with every section `pending`,
and `notes.md`, or names each missing field with an example. Rerun it after editing
sections; active and done sections cannot leave the plan. Setup already checks
structure, so a plan postflight is optional.

## Sections

Mark each section as you work:

```bash
python3 "{plugin_root}/scripts/zagrosi_skills.py" implement-progress --planning-dir "{planning_dir}" --section "{section}" --stage started
python3 "{plugin_root}/scripts/zagrosi_skills.py" implement-progress --planning-dir "{planning_dir}" --section "{section}" --stage done --notes "{what changed, decisions, next step}" -- <targeted check argv>
```

`done` saves the files changed during the section's calls (or each `--file`), the
host, the time, your note and the optional captured check; a failing check keeps the
section active. Put decisions and user clarifications in notes, or append to
`notes.md` directly: the next session sees nothing else. Without a captured check,
`--command` and `--result` report what you ran. Wait for a running check before the
next state change.

## Risk triggers

A row needs standard evidence when it has `risk: <reason>` (not `low` or `none`), a
whole risk word outside code spans (security, privacy, auth and its forms, OAuth,
permissions, migration, data, database, payment, tokens, secrets, passwords,
credentials, encryption), a public-interface phrase such as `public API`, `breaking
change` or `backward compatible`, REQ IDs, or when team coordination is configured.
Setup and status list each row's reasons. Its `done` then needs `--review-status pass`
(or `fixed`), a check after `--`, and a red checkpoint (`--stage red --command ...
--result ...`) or a passing baseline (`--stage baseline -- <preservation check>`).
A section's first call records its files, and a baseline must match their non-test
source, so start before editing. Interface rows need the baseline; with one, `done`
takes that same check after `--` as the candidate.

## Finish and resume

```bash
python3 "{plugin_root}/scripts/zagrosi_skills.py" implement-verify --planning-dir "{planning_dir}" --target-dir "{target_dir}" -- <full suite argv>
```

This captures the final receipt and runs the postflight. Postflight blocks only on a
missing or unparseable plan, a section without a status or not yet done, and a
missing, failing or stale final receipt. Later edits to source, `plan.md` or the
brief stale it; notes and status do not. Run long suites in the background with a
larger `--timeout`. Where the host supports subagents, run one fresh-context review
before finish. In Claude Code, run
[delegated agents](../../zagrosi-forge/references/providers.md#delegated-agents) in the foreground when offered.

A new session starts with `status --path "{planning_dir}"`: the goal, section states,
latest notes, last verification and files changed since the last status write.
