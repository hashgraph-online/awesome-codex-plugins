# Research Protocol

Research should reduce plan risk, not produce a literature review.

In `standard` mode, the final `codex-research.md` should normally be at least
1,500 words. In `deep` mode, target at least 2,500 words. The file should be
substantial when the codebase or external docs are substantial: include verified
paths, decisions, constraints, test commands, and unresolved risks.

## Codebase Research

Use fast local discovery first:

- `rg --files`
- `rg` for relevant names, routes, schemas, tests, config, and commands
- package manifests and existing test setup

Return findings as:

- relevant files and responsibilities
- existing patterns to follow
- test command and fixture strategy
- integration points and constraints
- risks or unknowns

For each finding, prefer "evidence -> implication -> planning consequence".
Avoid generic summaries that cannot directly change the plan.

## Documentation Research

For library, framework, SDK, API, CLI, or cloud-service details, follow the
repo's documentation instructions. If Context7 is required, resolve the library
ID first, query docs, and use the fetched docs in the plan.

Use web search only when current external facts are needed and repo/system
instructions allow it.

## Parent-Writes Rule

If agents are used, they return concise findings. The parent combines results
and writes `codex-research.md`. This avoids racing writes and keeps ownership
clear.
