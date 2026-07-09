---
name: handoff
description: Use when the user asks to hand off the current session to a new chat, transfer context, or runs /handoff. Produces a self-contained handoff document in the OS temp directory (NOT in the repo) — works regardless of whether an active plan file exists. Always prints the absolute path so the user can paste it into the new chat.
argument-hint: "[focus of the next session]"
disable-model-invocation: true
---

# Handoff

The doc must stand alone even when a plan/chronicle exists.

## Compute the path

Lives in the OS temp dir, NOT the repo (handoffs are short-lived):

```
${TMPDIR:-/tmp}/claude-handoff-YYYY-MM-DD-HHMMSS-{slug}.md
```

- `{slug}` = kebab-case topic, from `$ARGUMENTS` if passed, else inferred from the work.
- Resolve `${TMPDIR:-/tmp}` via `Bash` (`echo "${TMPDIR:-/tmp}"`) — macOS uses `/var/folders/.../T/`, not `/tmp`.

## Write

`Write` to the full absolute path. Fill every section. Empty section → write *"None"*, do NOT delete the header (the new agent's contract depends on the section being present).

```markdown
# Handoff — YYYY-MM-DD HH:MM — {topic}

### Goal (in the user's own words)
[Intent, quoted.]

### Focus of the next session
[`$ARGUMENTS` as a directive, or "continue from current state".]

### Current State
[File-anchored: working · broken · next step. Files, line numbers, exact errors.]

### Key Decisions
- **[Decision]** — because [reason]. Alternative [name] rejected because [reason].

### Important Context (gotchas · invariants · constraints)
- [Hidden invariants, traps, environment quirks]

### Relevant Files
- `path/to/file.ext` — [what · why · scope]

### Open Questions / Unknowns
- [Unresolved · what the user must decide] (or "None")

### Existing Artifacts (reference by path, do NOT duplicate)
- Plan: `docs/plans/NNNN__...md` — *(one-line summary, or "None")*
- Chronicle: `docs/chronicles/NNNN__...md` — *(or "None")*
- Other: PRDs · ADRs · GitHub issues · open PRs · key commits — *(path/URL each, or "None")*

### Suggested Skills for the New Agent
- `development-skills:<name>` — [why]

### Prompt for New Chat
```
Read the handoff at: {full absolute path written above}

Then continue from the "Current State" section.
```
```

## Announce

Print `HANDOFF WRITTEN: {full absolute path}` followed by the doc's "Prompt for New Chat" block (with the path filled in) for the user to paste.
