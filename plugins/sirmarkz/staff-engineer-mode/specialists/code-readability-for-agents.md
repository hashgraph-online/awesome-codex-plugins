---
name: code-readability-for-agents
description: "Use when repo structure, boundaries, naming, file size, or canonical paths affect AI-agent code comprehension"
---

# Code Readability For Agents

## Iron Law

```
IF AN AGENT CANNOT LOCATE THE CANONICAL IMPLEMENTATION IN ONE TOOL CALL, THE STRUCTURE IS WRONG
```

Indirection that humans tolerate because they remember where things live becomes silent failure when an agent edits the wrong file, recreates a function that already exists, or hallucinates a helper that almost-but-not-quite matches the real one.

## Overview

Produces a repository legibility map for AI comprehension: a module-boundary map, a list of names that collide or mislead code search, a function-and-file size report against a defined budget, and a set of naming and layout patches that let an agent reach the canonical implementation in one tool call. Refuses to call code "clean" when an agent has to read three files to find where a behavior lives.

**Core principle:** the repository is read by agents at least as often as by humans now. If the agent cannot find the canonical implementation deterministically, the structure is wrong, not the agent.

Do not read router eval fixtures, sample prompt files, or benchmark examples as
context for normal repository legibility work. Use the user's repo, traces,
search results, and local code as evidence unless the user explicitly asks to
evaluate this skill pack.

## When To Use

- The user is shaping repo structure, module boundaries, names, or canonical paths so AI coding agents can find and modify the right code.
- The user asks why their AI coding agent keeps editing the wrong file, recreating existing functions, or producing diffs that almost-but-not-quite match the local convention.
- A codebase is being prepared for AI-assisted contribution and you want to reduce wrong-file edits and hallucinated helpers.
- A repo has god files, files that exceed sensible read budgets, or modules whose names do not predict their contents.
- Code search returns multiple plausible matches for common verbs (`process`, `handle`, `update`, `run`) and the agent guesses wrong.
- A refactor is being planned and you want module boundaries that future agents and humans can reason about.
- Onboarding (human or agent) takes longer than the work justifies because canonical implementations are buried under indirection.

## When Not To Use

- The work is broad architectural decision-making across services or system boundaries; use `architecture-decisions`.
- The work is dependency cleanup, dead-code removal, or static-analysis findings on existing code; use `dependency-and-code-hygiene`.
- The work is org-level rules for AI-assisted coding (acceptance checks, data boundaries, protected paths); use `ai-coding-governance`.
- The work is checking one specific agent diff before merge; use `agent-pr-review`.
- The work is documentation lifecycle, responsibility, or freshness of engineering docs; use `documentation-lifecycle`.
- The work is API contract design or backwards compatibility on exposed surfaces; use `api-design-and-compatibility`.
- The work is generic review routing, change-size limits, or workflow metrics with no repository legibility issue; no routed specialist applies.

## Info To Gather

- Current work phase, next decision, what is known, and assumptions where details are missing.
- Repository scope: which directories are in scope, which are vendored or generated and excluded, and which are intentionally legacy.
- Agent traces if available: examples of recent agent runs where the agent edited the wrong file, missed the canonical implementation, or recreated a helper.
- Current module map: top-level packages or directories, stated responsibilities, and the actual exports each exposes.
- Naming inventory: function and class names that recur across modules, public verbs used as names, and any names that collide on case or near-case.
- File and function size distribution: largest files, longest functions, deepest nesting, and the size budget you have agreed (or the absence of one).
- Search hit-rate signal: for the common verbs and nouns of the domain, how many candidate matches a code search returns and how an outsider would pick one.
- Test placement convention: tests next to code, in a parallel tree, or scattered; the agent's ability to find tests for a given function predicts the agent's ability to verify changes.
- Doc co-location: whether each module has a short README or doc string that names its responsibility, public surface, and non-obvious invariants.
- Examples of canonical implementations you agree should be the only place a given behavior is implemented.

## Workflow

1. **Map the repo as the agent sees it.** List top-level modules and the verbs/nouns each exposes. Record any module whose name does not predict its responsibility.
2. **Run the one-tool-call test.** For a list of representative behaviors ("how does authentication happen," "where is the rate limit applied," "what validates this input"), check whether a single grep, symbol search, or doc lookup lands on the canonical file. Behaviors that fail the test become the first findings.
3. **Find name collisions.** Surface duplicate or near-duplicate function and class names across modules, especially common verbs (`process`, `handle`, `update`, `run`, `apply`, `save`). Each collision is a candidate disambiguation patch.
4. **Identify god files.** List files that exceed the size budget, hold more than one responsibility, or mix public surface with internal helpers. Each is a candidate split.
5. **Identify oversized functions.** List functions whose length, branching depth, or argument count exceed the budget. Long functions are unsearchable by behavior; an agent finds the file but not the responsibility within it.
6. **Identify ambiguous module boundaries.** Surface modules whose exports are partly used by callers that should not depend on them, modules that import caller modules, and modules whose stated purpose contradicts their actual exports.
7. **Check the canonical-implementation rule.** For each behavior you maintain, confirm there is one and only one implementation. Multiple plausible implementations are an agent failure mode in waiting; the agent will pick the wrong one.
8. **Check test discoverability.** Confirm a function's tests can be located by an agent using only the function's name and the repo convention. Hidden test mappings are a behavior-verification gap.
9. **Check doc co-location.** Confirm each module has a short, current statement of its responsibility, public surface, and invariants. A doc that lies is worse than no doc; flag stale docs as findings.
10. **Propose patches.** Issue concrete patches: rename collisions, split god files, extract internal helpers behind a clear public surface, move misplaced exports, add or correct module-level docs, and consolidate duplicate behavior into a single canonical site.
11. **Set the agent-search heuristic.** Document the conventions an agent should follow to find code in this repo (where canonical handlers live, where validators live, where adapters live, where tests live) and the conventions a contributor must follow to keep them true.
12. **Score the legibility.** Produce a scorecard: percent of representative behaviors that pass the one-tool-call test, count of collisions, count of god files, count of oversized functions, and count of modules with stale or missing co-located docs.

## Synthesized Default

Optimize the repository for one-tool-call discovery. Keep modules narrow and predictably named. Keep files and functions inside a defined size budget. Disambiguate common verbs in names. Co-locate tests and docs. Maintain a single canonical implementation per behavior. Document the agent-search heuristic so contributors keep it true. Treat repository legibility as a first-class engineering quality, not a refactor that happens "when there is time."



## Phase Behavior

- Ideation: identify risks, defaults, unknowns, options, and the next decision before code exists.
- Design: shape the target artifact, tradeoffs, checks, and details to gather.
- Development: guide sequencing, code boundaries, checks, and acceptance criteria.
- Testing: define release-blocking tests, evals, fixtures, and failure probes.
- Release: define rollout, observability, abort, rollback, and readiness details.
- Maintenance: define owners, drift checks, cleanup triggers, and refresh cadence.
- Existing artifact: use current code, docs, telemetry, incidents, or diffs as context for the next engineering decision; do not wait for a finished artifact before guiding design, build, release, or operation.
- Missing details: state assumptions and say what to check next instead of blocking lifecycle guidance.

## Exceptions

- Generated code may exceed the size budget if the generator is maintained and the file is not edited by hand; mark it generated and exclude it from the legibility score.
- Deliberately legacy modules under active replacement may keep their shape until cutover; record the exception, cutover condition, and concrete next patch.
- Domain-driven naming may require domain words that look ambiguous to outsiders but are precise inside the domain; the disambiguation lives in the module-level doc.
- Performance-critical code may justify a longer function or denser file when splitting would cost measured throughput; record the measurement and the check path that keeps the exception honest.

## Response Quality Bar

- Lead with the legibility map, the one-tool-call failures, the renaming or splitting patches, or the agent-search heuristic requested.
- Cover module-boundary findings, name collisions, file and function size against the budget, canonical-implementation duplications, and test/doc discoverability before optional refactor breadth.
- Make recommendations actionable with file paths, exact rename targets, split boundaries, and the agent-search rule each patch protects.
- Name the details to inspect, such as code-search hit counts, file/function size measurements, agent traces where available, and the representative behaviors used for the one-tool-call test; do not state legibility without the test results.
- Stay technology-agnostic by default: do not introduce provider, product, framework, database, protocol, or command names unless the user supplied them or explicitly requested tool-specific guidance.
- Stay inside repository legibility for AI comprehension. Route system architecture, dead-code cleanup, doc lifecycle, agent controls, and per-diff review to the responsible specialist.
- Be concise: prefer compact finding tables and patch lists over generic clean-code prose.

## Required Outputs

- Output shape: render the matching shared template headings or tables in the reply, or use the same shape.
- Module-boundary map with stated responsibility, actual exports, and any contradictions.
- One-tool-call test results: a list of representative behaviors with the search query used, the candidate matches returned, and pass/fail.
- Name-collision list with each colliding name, the modules it appears in, and the proposed disambiguating renames.
- File and function size report against a stated budget, with the worst offenders listed and split or extraction patches proposed.
- Canonical-implementation report listing behaviors that have more than one plausible implementation and the proposed consolidation patch.
- Test and doc discoverability report identifying functions whose tests are not findable by convention and modules whose co-located docs are missing or stale.
- Patch list: concrete renames, file splits, module-doc additions or corrections, and consolidations, each with file paths.
- Agent-search heuristic documenting where canonical handlers, validators, adapters, and tests live in this repo, with the contributor rule that keeps it true.
- Legibility scorecard: percent passing the one-tool-call test, collision count, god-file count, oversized-function count, and stale-doc count.

## Checks Before Moving On

- `boundary_map_present`: the map lists modules with stated responsibility and contradictions are named.
- `one_tool_call_test`: representative behaviors are tested for one-tool-call discovery; failures are listed with the search used.
- `collision_inventory`: colliding or near-colliding names are listed with their modules and proposed disambiguations.
- `size_budget_check`: a file and function size budget is stated and offenders are listed against it.
- `canonical_uniqueness`: behaviors with more than one plausible implementation are listed with consolidation patches.
- `discoverability_check`: tests and module docs are findable by convention or are flagged as gaps.
- `agent_search_heuristic`: a written convention for where canonical handlers, validators, adapters, and tests live is produced and is consistent with the patches recommended.
- `patch_actionable`: each recommended patch names the file or module, the exact change, and the legibility rule it protects.

## Red Flags - Stop And Rework

- The one-tool-call test is skipped because "you know where everything is."
- A behavior has two plausible implementations and the recommendation picks one without consolidating the other.
- Renames are proposed without sweeping callers, tests, and docs.
- A god file is "split" by moving code to a new file with the same responsibility, leaving two god files.
- The agent-search heuristic is written but contradicts the actual file layout the patches produce.
- Module docs are added that restate names rather than declaring responsibility, public surface, and invariants.
- Performance or legacy exceptions lack measurement, expiry, or a concrete cleanup patch.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Optimizing only for human readability | Test the one-tool-call rule; humans tolerate indirection that breaks agents. |
| Naming functions with bare verbs | Disambiguate with the noun the verb acts on; reserve common verbs for canonical sites. |
| Letting common behaviors live in many files | Consolidate to one canonical implementation; delete or redirect the others. |
| Splitting god files by line count | Split by responsibility; two equally-mixed files are not progress. |
| Documenting modules with restated names | Document responsibility, public surface, and non-obvious invariants. |
| Hiding tests in a parallel tree without convention | Co-locate or document the mapping rule so an agent can find tests by name. |
| Treating legibility as a one-time refactor | Make the agent-search heuristic a contributor rule; guard against regression. |
