---
name: align-docs
description: "Use when repository docs, README, AGENTS.md, rules, plans, chronicles, or ATLAS are stale or current work changed their lifecycle; archives task history, with --clean for corpus-wide cleanup."
user-invocable: true
allowed-tools: Read, Edit, Write, Bash, Glob, Grep, AskUserQuestion
---

# Align docs

Make the repository's existing knowledge easy for humans and agents to find and trust.
Run it inside the development-skills workflow, after a conversation, or standalone. Inside an active workflow, continue that workflow instead of starting another. When prior context exists, include lasting knowledge gathered there; otherwise follow the default steps.

Always leave this shared entry layer:

```text
README.md                 # evidence-based human entry point
AGENTS.md                 # under 70 lines; critical facts and rules index
CLAUDE.md                 # exactly @AGENTS.md
.agents/rules/            # scoped team/project rules; .gitkeep if empty
.claude/rules -> ../.agents/rules
docs/ATLAS.md             # curated routing map of the repo's knowledge
```

Resolve the git root. Inspect the entry layer, manifests, their referenced paths, agent memory, and documents created, changed, or invalidated by the current task. Without prior task context, inspect the entry layer and its references only. Read enough reliable evidence to verify claims. Exclude dependencies, caches, build output, and vendored content.

Report missing, stale, contradictory, duplicated, orphaned, or oversized knowledge before editing. A normal run may make safe in-scope fixes but never merges or deletes first-party documents.

When prior task context proves that the current task changed a document's lifecycle, also move the resulting history with `git mv`:

- a completed plan whose implementation is verified and whose durable decisions remain in a chronicle → `docs/plans/archive/`;
- a chronicle that the task superseded or made obsolete → `docs/chronicles/archive/`, preserving decision prose and lifecycle links;
- another document that the task superseded or made obsolete but whose unique history remains useful → an `archive/` beside its active collection.

Before archiving, move durable agent instructions to the right `.agents/rules/` file. Keep current owners and uncertain documents active, and make archive metadata match the path. This bounded normal run does not scan unrelated history for archive candidates.

With `--clean`, follow [clean-mode.md](references/clean-mode.md); it applies these lifecycle rules to the full corpus, and its proposal gate replaces normal apply behavior.

Give each fact one owner: brief always-read facts in AGENTS.md, scoped detail in `.agents/rules/`, execution in plans, decisions in chronicles, and other existing knowledge in its clearest current home. Prefer links over copies and preserve useful project-specific structure.

Resolve claims by what they describe: code, tests, and configuration for implementation; telemetry or live data for runtime state; approved contracts for promises; chronicles for rationale; and executable commands or CI for procedures. Report conflicts between authorities instead of guessing.

Apply the [documentation contract](../../shared/documentation.md) within its stated scope.

Build `docs/ATLAS.md` without frontmatter, as a routing map, not an inventory: the filesystem and git already enumerate files. Route every recurring question or area to its authoritative home with a link and one when-to-open line. Be exhaustive only inside small curated scopes (entry points, rules, reference shelf); give self-indexing directories such as plans and chronicles one routing entry that explains their naming convention. Exclude fixtures, implementation-support Markdown, and ATLAS itself. No lifecycle columns — validity and work state live in each document's frontmatter.

An existing AGENTS.md is authoritative: report issues, never overwrite it or prepend the template. Create AGENTS.md from [agents-template.md](references/agents-template.md) only when the file is missing or the user explicitly asks to migrate. Delete a leftover `align-docs:principles-customized` marker. A rule owns its topic; AGENTS.md only links to it.

Keep personal machine facts in `.claude/CLAUDE.md` or the user's global Codex AGENTS file. Ensure `.gitignore` contains `.claude/CLAUDE.md` and `AGENTS.override.md`.

Capture only lasting session facts that are absent from disk. A run without prior session context reports `CAPTURE: NONE`. Move useful memory to its owner; leave empty or generic memory for clean mode.

Finish by checking the AGENTS line budget, rule scopes, symlink, ignored personal files, README/manifests against disk, ATLAS routing (every area reachable, no excluded content), required frontmatter on changed docs, and Markdown links. Apply the [reduce-gate](../../shared/skill-authoring.md) to every changed instruction file.
