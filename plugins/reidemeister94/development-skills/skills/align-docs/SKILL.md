---
name: align-docs
description: Align stale repository docs and task records; use --clean for a full documentation cleanup.
user-invocable: true
allowed-tools: Read, Edit, Write, Bash, Glob, Grep, AskUserQuestion
---

# Align docs

Make existing repository knowledge accurate and easy to find.
Continue an active workflow with its current task context and authorization.
Without task context, inspect only the entry layer and relevant references.
Exclude dependencies, caches, build output, and vendored content.

## Entry layer

Preserve or establish the project's shared entry layer:

```text
README.md                 # Human entry point.
AGENTS.md                 # Critical facts and scoped rules, under 70 lines.
CLAUDE.md                 # Exactly @AGENTS.md.
.agents/rules/            # Scoped project rules; .gitkeep if empty.
.claude/rules -> ../.agents/rules
docs/ATLAS.md             # Curated knowledge routes.
```

Inspect these files, manifests, relevant agent memory, and documents affected by the current task.
Report conflicts or missing facts before making safe in-scope repairs.
A normal run never merges or deletes first-party documents and does not scan unrelated history for archive candidates.
Use [clean mode](references/clean-mode.md) for a requested full-corpus cleanup.

## Owners and evidence

Give each fact one owner: critical facts in AGENTS, scoped instructions in rules, execution in plans, reasons in chronicles.
Keep other useful knowledge in its clearest existing home.
Verify implementation claims against code and tests, runtime claims against telemetry, promises against contracts, and decision reasons against chronicles.
Report unresolved conflicts instead of choosing an unsupported claim.

Preserve an existing AGENTS file's rules. Edit them only within the task's authorization; do not overwrite it with a template.
Use [agents-template.md](references/agents-template.md) only when creating or explicitly migrating the file.
Remove a leftover `align-docs:principles-customized` marker.
Keep personal machine facts in `.claude/CLAUDE.md` or global Codex instructions.
Ensure `.gitignore` ignores `.claude/CLAUDE.md` and `AGENTS.override.md`.
Capture lasting session facts absent from disk; with no session context, report `CAPTURE: NONE`.

## Lifecycle and routes

Use the [documentation contract](../../shared/documentation.md) for metadata and lifecycle.
Archive only documents whose changed lifecycle the task establishes:

- Completed plans with closed work and verified implementation move to `docs/plans/archive/`.
- Superseded or obsolete chronicles move to `docs/chronicles/archive/` with decision prose preserved.
- Other obsolete documents with useful history move to an adjacent `archive/`.

Keep current owners and uncertain documents active. Move durable instructions to their owner before archiving.
Use `git mv` for tracked files. Repair inbound links, moved-file links, paired IDs, and archive metadata.

Build ATLAS without frontmatter. Route recurring questions to authoritative files with a link and a when-to-read sentence.
List small curated scopes, such as rules and reference notes, completely.
Give plans and chronicles one directory route that explains `YYYY-MM-DD__<slug>.md` and legacy `NNNN__` names.
Exclude fixtures, implementation-support Markdown, ATLAS itself, and lifecycle tables.

## Check

Check the entry layer, scopes, symlink, ignored files, manifest claims, ATLAS routes, changed metadata, and Markdown links.
Run `uv run <plugin-root>/scripts/check_docs.py <repository-root>` from the installed plugin.
Use the project's documented `--legacy-before YYYY-MM-DD` cutoff when present.
The checker validates local file targets, paired IDs, names, and plan closure; it does not validate heading anchors or external URLs.
Report unrelated failures without expanding scope or claiming success.
Apply the [authoring contract](../../shared/skill-authoring.md) to changed instructions.
