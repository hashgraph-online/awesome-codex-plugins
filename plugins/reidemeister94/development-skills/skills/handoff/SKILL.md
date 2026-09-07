---
name: handoff
description: Create a self-contained temporary handoff document when the user asks to transfer the session to a new chat or runs /handoff.
argument-hint: "[focus of the next session]"
---

# Handoff

Create a standalone document that lets a person or agent continue the work in a new conversation. Follow the [writing contract](../../shared/writing.md). Preserve the user’s request, useful discoveries, exact decisions, current state, relevant files, and the next action. Do not copy the conversation or raw logs.

## Compute the path

Use the OS temp directory, never the repo:

```
${TMPDIR:-/tmp}/handoff-YYYY-MM-DD-HHMMSS-{slug}.md
```

- `{slug}` = kebab-case topic, from `$ARGUMENTS` if passed, else inferred from the work.
- Resolve `${TMPDIR:-/tmp}` with Bash; macOS may not use `/tmp`.

## Write

Write the absolute path. Keep the first three sections. Include the later sections only when they carry useful information.

```markdown
# Handoff: {topic}

## What the user wants
[Explain the requested result and why it matters. Preserve exact wording only for decisions that the next conversation must not reinterpret.]

## Where things stand
[Explain what works, what is incomplete or broken, and the evidence. Give exact files, line numbers, and errors where they matter.]

## Next step
[`$ARGUMENTS` as a clear directive, or the next concrete action inferred from the current state.]

## Decisions that must survive
- [Decision and reason. Add a rejected alternative only when it helps prevent the same debate.]

## What the next agent needs to know
- [Constraint, project rule, hidden dependency, environment detail, or known trap.]

## Files and existing work
- `path/to/file.ext` — [what it contains and why it matters]
- Plan: `docs/plans/NNNN__...md` — [what it settles]
- Chronicle: `docs/chronicles/NNNN__...md` — [what it records]
- Other: [PRD, ADR, issue, pull request, commit, or URL]

## Questions still open
- [Question, why it matters, and who can answer it.]

## Useful skills
- `development-skills:<name>` — [when and why to use it]
```

## Announce

Print `HANDOFF WRITTEN: {full absolute path}` followed by:

```
Read the handoff at: {full absolute path written above}

Then continue from the "Next step" section.
```
