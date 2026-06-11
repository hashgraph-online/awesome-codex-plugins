---
name: handoff
description: Use when the user asks to hand off the current session to a new chat, transfer context, or runs /handoff. Produces a self-contained handoff document in the OS temp directory (NOT in the repo) — works regardless of whether an active plan file exists. Always prints the absolute path so the user can paste it into the new chat.
argument-hint: "[focus of the next session]"
disable-model-invocation: true
---

# Handoff — Self-Contained Context Transfer

Produce a handoff document a fresh agent session can pick up from **without re-investigating**. Lives in the OS temp directory — handoffs are short-lived by design; do NOT pollute the repo.

## The Principle

**Whatever is not in this doc, the new chat will not have.** Capture every load-bearing fact at the highest possible value: the user's goal, the current state, the decisions made, the constraints discovered, the file paths touched, the open questions. Do not assume the new agent can re-derive what was learned.

This holds **whether or not a plan / chronicle file exists.** A plan reference is OPTIONAL bonus; the handoff doc must stand alone.

## Step 1 — Compute the path

```
${TMPDIR:-/tmp}/claude-handoff-YYYY-MM-DD-HHMMSS-{slug}.md
```

- `YYYY-MM-DD-HHMMSS` = current timestamp (prevents collisions, time-orders multiple handoffs).
- `{slug}` = kebab-case topic of the current session. If the user passed `$ARGUMENTS`, derive the slug from there; otherwise infer from the work performed.
- The `claude-handoff-` prefix namespaces the file inside `$TMPDIR`.

Resolve `${TMPDIR:-/tmp}` via `Bash` (`echo "${TMPDIR:-/tmp}"`) so the path is correct on the user's OS (macOS uses `/var/folders/.../T/`, Linux usually `/tmp`).

## Step 2 — Write the doc

Use the `Write` tool with the full absolute path. Fill every section. Empty sections → write *"None"* (do NOT delete the header — the contract with the new agent depends on the section being present).

```markdown
# Handoff — YYYY-MM-DD HH:MM — {topic}

### Goal (in the user's own words)
[Quote the user's intent literally. Don't paraphrase into agent-speak.]

### Focus of the next session
[If the user passed `$ARGUMENTS`, restate that as the directive for the next agent. Otherwise: "continue from current state".]

### Current State
[File-anchored. What's working · what's broken · the next concrete step. Name files, line numbers, exact errors. Avoid abstract status.]

### Key Decisions
- **[Decision]** — chosen because [reason]. Alternative considered: [name], rejected because [reason].

### Important Context (gotchas · invariants · constraints)
- [Hidden invariants — things that look wrong but are right]
- [Subtle traps — things that look right but are subtly wrong]
- [Environment quirks — env vars, paths, tool versions that matter]

### Relevant Files
- `path/to/file.ext` — [what · why · which part is in scope]

### Open Questions / Unknowns
- [What wasn't resolved · what may surface · what the user still needs to decide]
- (or "None")

### Existing Artifacts (reference, do NOT duplicate)
- Plan: `docs/plans/NNNN__...md` — *(or "None")*
- Chronicle: `docs/chronicles/NNNN__...md` — *(or "None")*
- Other: PRDs · ADRs · GitHub issues · open PRs · key commits — *(path or URL each, or "None")*

### Suggested Skills for the New Agent
- `development-skills:<name>` — [why the next session should invoke this]
- ...

### Prompt for New Chat
```
Read the handoff at: {full absolute path written above}

Then continue from the "Current State" section.
```
```

## Step 3 — Announce the path prominently

After writing the file, print to chat in this format (so the user can copy-paste without hunting):

```
HANDOFF WRITTEN: {full absolute path}

Paste into your new chat:
  Read the handoff at: {full absolute path}
```

One line, prominent, complete. The user pastes the second line; the new agent reads the file and has everything.

## Rules

- **Self-contained, not reference-only.** Even when a plan / chronicle file exists, write the Goal + Current State inline. The handoff doc must be readable as a standalone artifact. The plan is for depth; the handoff is for bootstrap.
- **Reference existing artifacts, do NOT duplicate.** Plans · chronicles · PRDs · ADRs · GitHub issues · commits — link by path or URL; restate ONLY a one-line summary of each in the handoff. Duplicating long content bloats the handoff and drifts from the source.
- **No fluff.** Every section is load-bearing. No "Summary" filler that restates the title. No filler openers.
- **User language over agent language.** Quote the user's own words for Goal and Open Questions where possible. The user's framing is signal.
- **File-anchored over abstract.** *"`src/api/cart.py:42-89` validation incomplete"* beats *"validation needs work"*. File paths and line numbers transfer; vague summaries don't.
- **Redact sensitive data.** API keys, passwords, OAuth tokens, PII, internal URLs that expose secrets → strip or replace with `[REDACTED]`. The handoff file lives in OS temp, but it may still be readable by other processes on the machine.
- **No invented files or facts.** If unsure whether a file or function exists, mark it as an Open Question rather than asserting it.

---

**Cross-link.** Principle 11 (Context is the constraint) in `../../shared/iron-rules.md`. The plan file (when one exists) is the canonical persistent record **within** a session; this handoff doc is the canonical transfer **across** sessions.
