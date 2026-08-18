---
name: project-map-catalog
description: Use when recording, registering, or updating a project feature, flow, page, component, module, utility, pattern, contract, domain, or business concept into Wingman's project map for future discovery and reuse/reference decisions. Trigger for 登记, 记录, 加入项目地图, 以后 AI 能找到, catalog, register, record, add to project map, feature inventory, capability map, or reusable capability. Do not use for explaining code, editing code, summarizing a file, or writing memory/history unless the user asks to add project-map knowledge.
---

# Project Map Catalog

Catalog exactly one project capability into `.wingman/project-map/` with evidence. The project map is an AI-readable capability map, not a source dump and not the final source of truth.

## Core Rule

Write one evidence-backed project-map entry and its indexes. Do not catalog from filenames, path names, or guesses.

## Gate

Continue only when there is a coherent capability to record. If the user asks to explain, edit, review, or summarize code without asking to record project-map knowledge, do not use this skill.

## Core Concepts

A project-map entry is one Markdown file under `.wingman/project-map/`. It records a capability, flow, surface, component, module, utility, pattern, contract, domain, or term mapping that future agents may need to locate, understand, verify, reuse, extend, wrap, reference, avoid, or replace.

Use fixed English section headings for stable parsing. Write entry content and final responses in the configured memory language when known; otherwise follow the user's current language.

## Project Map Layout

Initialize missing directories and indexes as needed:

```text
.wingman/project-map/
  README.md
  index.md
  glossary/index.md
  features/index.md
  flows/index.md
  surfaces/index.md
  components/index.md
  modules/index.md
  utilities/index.md
  patterns/index.md
  contracts/index.md
  domains/index.md
  relationships/index.md  # optional/future; do not require it for every catalog action
```

Top-level and section indexes are short routing tables. Use `Entry Path`, not `Entry`, as the path column label.

## Workflow

1. Identify the target.
   - If the user gave a path, use it as the evidence starting point.
   - If the user gave a feature or concept name, search source/docs/routes/tests/schema for evidence.
   - If the user said "this feature", use active context and recent relevant files.
   - Process exactly one coherent capability per invocation.

2. Choose the kind.
   - Use `feature`, `flow`, `surface`, `component`, `module`, `utility`, `pattern`, `contract`, `domain`, or `glossary-term`.
   - If uncertain, read `references/kind-selection.md`.

3. Read evidence before writing.
   - Read source, docs, routes, schema, tests, generated types, config, or explicit user-confirmed context.
   - For source-backed `feature`, `flow`, `surface`, `module`, and `contract` entries, prefer at least two evidence types when available.
   - For `component` and `utility`, one primary source file is acceptable, but check usages before claiming reuse scope.
   - Do not infer behavior from filename or path alone.

4. Read existing map context.
   - Read `.wingman/project-map/index.md` when it exists.
   - Read the relevant section index.
   - Search `.wingman/project-map/**/*.md` for the same source path, same capability name, same tags, or same term.

5. Decide create/update/replace.
   - Same source or same semantic capability: update the existing entry.
   - Same name but different responsibility: create a distinct entry and link it in `Related Entries` or `Similar Features`.
   - Stale or superseded entry: mark `Legacy` or `Deprecated`, and point to replacement when known.

6. Write the entry.
   - Read `references/entry-templates.md` before creating or substantially changing an entry.
   - Do not write generic source summaries.
   - Do not omit `Last Verified`, `Evidence Level`, `Use When`, `Do Not Use When`, or `Notes For Agents`.
   - Use `Unknown` rather than inventing facts.

7. Update indexes.
   - Update `.wingman/project-map/index.md`.
   - Update the relevant section `index.md`.
   - Update `glossary/index.md` only when there is a useful user-language to code-language mapping.
   - Update `relationships/index.md` only when it already exists or when a clear cross-entry relationship is important. First version may rely on each entry's `Related Entries`.

## References

- Read `references/kind-selection.md` only when kind choice is ambiguous.
- Read `references/entry-templates.md` before creating or substantially changing an entry.
- Do not read all references by default if updating only an index row or correcting a small typo.

## Ask The User When

- The target capability cannot be identified from paths, active context, source search, docs, or user wording.
- Two possible kinds would produce materially different entries and evidence does not settle the choice.
- Writing the entry would require treating an inferred business meaning as confirmed fact.

## Safety Rules

- Do not create or update multiple unrelated entries in one invocation.
- Do not write "possible" or "likely" as fact.
- Do not bulk-generate low-signal entries to cover a whole repository.
- Do not overwrite user-authored `Notes For Agents`, `Use When`, `Do Not Use When`, or status unless evidence or explicit user instruction proves they are outdated.
- If project memory current truth conflicts with a project-map entry, keep memory truth authoritative and mark the map entry as needing update.
- Do not migrate `.wingman/registry/` automatically. Treat old registry files as non-authoritative historical hints unless the user asks for migration.

## Final Response

Report concisely:

- entry name and kind
- entry path
- status and evidence level
- updated indexes
- key tags or search hints
- any unverified gaps

## Checklist

Before finishing, verify:

- [ ] I processed one coherent capability.
- [ ] I read evidence before writing facts.
- [ ] I checked existing project-map entries for duplicates.
- [ ] I created or updated exactly one main entry.
- [ ] I updated the top-level index and relevant section index.
- [ ] I clearly labeled unknown, inferred, or stale information.
