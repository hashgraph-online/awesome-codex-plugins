---
name: project-map-find
description: Use when locating existing project features, flows, pages, modules, components, utilities, patterns, contracts, business concepts, or similar functionality before answering where something is or before building related functionality. Trigger for 项目里有没有做过, 在哪里, 类似功能, 已有功能, 复用, 不要重复造轮子, 项目里叫什么, 哪些文件, 找一下, existing feature, similar functionality, where is, reuse, avoid rebuilding, project concept, feature inventory, capability map, or implementation already exists. Do not use for pure styling, isolated bug fixes, code explanation, or tests unless the user asks for existing/related capability discovery.
---

# Project Map Find

Use `.wingman/project-map/` to narrow candidate capabilities, then verify source before strong claims. The project map is a discovery map, not final authority.

## Core Rule

Read indexes first, select a small candidate set, and verify source before strong claims. Do not turn a project-map lookup into a full repository scan unless the map is missing or clearly insufficient.

## Gate

Continue only when the user needs to locate an existing capability, compare similar implementations, map a project concept, or check for reuse/reference candidates. If the task is only editing, explaining, testing, or styling and does not ask about existing capability discovery, do not use this skill.

## Core Behavior

Answer questions like:

- whether a project already has a feature, flow, component, module, utility, pattern, contract, or concept
- where that capability lives
- what the closest matches do
- whether to reuse, extend, wrap, reference, avoid, or create new
- what source should be read next

## Lookup Workflow

1. Extract intent:
   - `Locate`: find where something is.
   - `Compare`: compare similar capabilities.
   - `Reuse Decision`: decide reuse/extend/wrap/reference/create.
   - `Concept Mapping`: map user language to project code names.
   - `Implementation Prep`: find precedents before building.

2. Check project-map availability.
   - If `.wingman/project-map/` is missing, say no project map exists yet.
   - Offer source search if useful, but do not present source-search results as map results.
   - If source search finds a durable capability, recommend `project-map-catalog`.

3. Read the smallest useful index set.
   - Always read `.wingman/project-map/index.md` when present.
   - Read `.wingman/project-map/glossary/index.md` when present.
   - Add section indexes based on intent: `features`, `flows`, `surfaces`, `components`, `modules`, `utilities`, `patterns`, `contracts`, or `domains`.
   - Read `relationships/index.md` only when it exists and the query needs cross-entry relationships.

4. Expand terms.
   - Use glossary, tags, source paths, route names, API names, business aliases, and old names.
   - Search the map for query words and expanded terms.

5. Select candidates.
   - Pick up to 5 feature/flow/domain candidates.
   - Pick up to 5 implementation candidates.
   - Pick up to 3 glossary/contract candidates.
   - For ambiguous ranking, read `references/candidate-ranking.md`.

6. Read only selected entries.
   - Prefer this order when relevant: domain -> glossary -> feature/flow -> surface -> module/component/utility/pattern/contract.
   - Do not read every entry unless indexes are missing, stale, or clearly insufficient.

7. Verify source before strong claims.
   - Source verification is required before claiming an exact route/path is current, implementation is reusable, API/type/schema shape, preferred/deprecated status, or behavior details not directly present in a source-verified entry.
   - Source verification may be skipped when the user only wants a rough map or the answer explicitly says "project map says" and labels unverified/stale evidence.

## Decisions

Use these decision labels:

- `Locate`: found where it lives, not necessarily reusable.
- `Reuse`: directly use existing implementation.
- `Extend`: expand the same semantic responsibility.
- `Wrap`: wrap existing capability with context, defaults, permissions, or layout.
- `Reference`: follow the flow/pattern but do not reuse code directly.
- `Avoid`: similar but should not be used.
- `Create New`: no suitable candidate.
- `Catalog Needed`: source search found a capability not in the project map.

## Output

Put the strongest answer first:

```markdown
Found: Yes | Partial | No

Closest Matches:

- `[Entry Name]`: [what it does]
  - Where: `[path/route]`
  - Traits: [key traits]
  - Decision: Locate | Reuse | Extend | Wrap | Reference | Avoid | Create New | Catalog Needed
  - Evidence: [entry/source]

Recommended Next Step:
[read source / reuse module / create new / catalog missing feature]

Gaps:
[missing entry, stale verification, no map coverage]
```

If no good match exists, say so directly. Distinguish "project map has no match" from "source search found no match".

## References

- Read `references/candidate-ranking.md` only when the index yields multiple plausible candidates or the best candidate is unclear.
- Read `references/output-examples.md` only when shaping a complex final response.
- Do not read all references for simple "where is X?" lookups.

## Ask The User When

- The query lacks a capability, concept, domain, or implementation target.
- Multiple user meanings are plausible and would lead to different searches.
- The user asks for a reuse decision but the required behavior or constraints are underspecified.

## Checklist

Before finishing, verify:

- [ ] I read the smallest useful index set first.
- [ ] I selected a limited candidate set.
- [ ] I read only relevant entries.
- [ ] I verified source before strong claims, or clearly labeled unverified map results.
- [ ] I included evidence and gaps.
