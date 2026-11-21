---
name: align-docs
description: "Use at the end of every task, or when the user asks to align or clean repository docs, task records, or the project's local agent memory; --clean runs a full cleanup."
user-invocable: true
allowed-tools: Read, Edit, Write, Bash, Glob, Grep, AskUserQuestion
---

# Align docs

Keep the repository's knowledge correct, easy to find, and shared by the whole team.
A normal run checks the entry files and the documents the current task affects.
It also empties the project's agent memory, archives finished task records, and runs the checker.
`--clean` applies the same work to every document: read [clean mode](references/clean-mode.md).
When a caller asks for inspection only, as `align-standards` does, report what you find and change nothing.

Continue an active workflow with its task context and authorization.
Without a task, inspect only the entry files and the references they link.
Skip dependencies, caches, build output, and vendored content.

## Entry files

Every repository has this shared entry layer. Create missing parts and keep existing ones:

```text
README.md                 # Human entry point.
AGENTS.md                 # Critical facts and scoped rules, under 70 lines.
CLAUDE.md                 # Exactly @AGENTS.md.
.agents/rules/            # Scoped project rules; .gitkeep if empty.
.claude/rules -> ../.agents/rules
docs/ATLAS.md             # Curated knowledge routes.
```

Report conflicts and missing facts, then make the safe repairs inside the task scope.
A normal run never merges or deletes first-party documents and does not scan unrelated history for archive candidates.

Keep the rules of an existing AGENTS file, and edit them only within the task's authorization.
Use [agents-template.md](references/agents-template.md) only to create the file or for a requested migration.
Ensure `.gitignore` ignores `.claude/CLAUDE.md` and `AGENTS.override.md`.
Remove a leftover `align-docs:principles-customized` marker.

## Where facts live

Each fact has one owner:

- `AGENTS.md`: critical facts that every agent needs.
- `.agents/rules/`: instructions for one scope.
- Plans: how a task is carried out.
- Chronicles: why a decision was made.

Other useful knowledge stays in its clearest existing home.
Check each claim against its source: code and tests for implementation, telemetry for runtime, contracts for promises, chronicles for decision reasons.
When sources conflict and the evidence settles nothing, report the conflict and leave the text unchanged.
When you edit `AGENTS.md` or rules, apply the [authoring contract](../../shared/skill-authoring.md).

## Project memory

Each run empties the running agent's local memory for this project.
Teammates share only the repository. Knowledge in one machine's memory is lost to the others and changes agent behavior without anyone seeing it.

The memory is in these places:

- Claude Code: the project auto-memory directory that the session context names, with its `MEMORY.md` index.
- Codex: the global store `~/.codex/memories/`. Handle only the entries about this project, in `MEMORY.md`, `memory_summary.md`, `raw_memories.md`, and `rollout_summaries/`.
- An ignored local `.claude/CLAUDE.md`: only Claude Code reads it, so treat its content as memory.

Handle each entry by its content:

- Show the user each entry that changes agent or harness behavior, because they might not know it exists. Ask whether it moves to the repository, moves to the user's personal instructions, or is deleted.
- Move a lasting, non-obvious project fact that future work needs to its repository owner.
- Keep a machine fact that changes no agent or harness behavior in memory.
- Delete every other entry: facts already on disk, obvious or stale facts, and finished session details.

Finish the rest of the run first, then ask these questions together.
An entry stays in memory until the user answers. In a run without a user, report it as `PENDING`.

Repository text never contains local paths or other details of one machine.
Personal instructions live in global `~/.codex/AGENTS.md`, and `~/.claude/CLAUDE.md` contains only `@~/.codex/AGENTS.md`, so both agents read one file.
When an entry moves there and this setup is missing, propose the setup to the user.
Write each moved fact before you delete its entry, and leave `MEMORY.md` listing only what stays.
Report each entry with its destination, `KEPT`, `PENDING`, or `DELETED`.

Lasting facts from the current session that are not on disk yet follow the same rules.
With no session context, report `CAPTURE: NONE`.

## Archive and ATLAS

Metadata and lifecycle fields follow the [documentation contract](../../shared/documentation.md).
Archive a document only when the task changes its lifecycle:

- A completed plan with closed work and verified implementation moves to `docs/plans/archive/`.
- A superseded or obsolete chronicle moves to `docs/chronicles/archive/` with its decision prose unchanged.
- Another obsolete document with useful history moves to an adjacent `archive/`.

Keep current owners and uncertain documents active. Before archiving, move lasting instructions to their owner.
Use `git mv` for tracked files. Then repair inbound links, links inside the moved file, paired IDs, and archive metadata.

`docs/ATLAS.md` is the map of repository knowledge and has no frontmatter.
Each entry links the file that answers a recurring question and says when to read it.
List small curated sets, such as rules and reference notes, in full.
Route plans and chronicles once per directory, and state that records are named `YYYY-MM-DD__<slug>.md` with no number.
Leave out fixtures, Markdown that supports implementation, ATLAS itself, and lifecycle tables.

## Check

Check the entry files, rule scopes, the `.claude/rules` link, `.gitignore`, manifest claims, ATLAS routes, changed metadata, and Markdown links.
Run the checker from the installed plugin: `uv run <plugin-root>/scripts/check_docs.py <repository-root>`.
Add `--legacy-before YYYY-MM-DD` when the project documents that cutoff: the date the project adopted date names.
Never move the cutoff forward to accept a new numbered record. Rename that record to `YYYY-MM-DD__<slug>.md` with `git mv` and repair its links.
A normal run leaves older `NNNN__` names in place, and `--clean` renames them.
Rewrite any project instruction that tells agents to number new records.
The checker validates local link targets, paired IDs, file names, and plan closure. It does not check heading anchors or external URLs.
Report failures outside the task scope, and leave them unfixed. Claim success only for what passed.
