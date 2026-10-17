# Staff Engineer Mode Skill Contract

Every specialist file must be concise, triggerable, and artifact-oriented.

## Required SKILL.md Shape

- YAML frontmatter with `name` and trigger-only `description`.
- `# Skill Name`
- `## Iron Law`
- `## Overview`
- `## When To Use`
- `## When Not To Use`
- `## Info To Gather`
- `## Workflow`
- `## Synthesized Default`
- `## Exceptions`
- `## Response Quality Bar`
- `## Required Outputs`
- `## Checks Before Moving On`
- `## Red Flags - Stop And Rework`
- `## Common Mistakes`

Published specialist prose intentionally omits per-specialist source,
reference, bibliography, citation, and reading-list sections. Maintain the
shared source index as a curated library; do not imply that unpublished
synthesis notes or one-to-one claim mappings exist.

Every specialist Response Quality Bar must require technology-agnostic guidance
by default: do not introduce provider, product, framework, database, protocol,
or command names unless the user supplied them or explicitly requested
tool-specific guidance.

Every specialist's Required Outputs must include an output-shape rule: render
the matching shared template headings or tables in the reply, or use the same
shape. Keep templates, checklists, and reviews user-visible.

The router supplies common lifecycle behavior once for all specialists:

- Ideation: identify risks, defaults, unknowns, options, and the next decision before code exists.
- Design: shape the target artifact, tradeoffs, checks, and details to gather.
- Development: guide sequencing, code boundaries, checks, and acceptance criteria.
- Testing: define release-blocking tests, evals, fixtures, and failure probes.
- Release: define rollout, observability, abort, rollback, and readiness details.
- Maintenance: define owners, drift checks, cleanup triggers, and refresh cadence.
- Existing artifact: use current code, docs, telemetry, incidents, or diffs as context for the next engineering decision; do not wait for a finished artifact before guiding design, build, release, or operation.
- Missing details: state assumptions and say what to check next instead of blocking lifecycle guidance.

Specialists may add domain-specific phase rules, but must not repeat the common
block verbatim. Required Outputs are an artifact menu: narrow answers render the
smallest core artifact plus risk-triggered sections; broad work uses the smallest
owned template set covering its distinct artifacts.

Non-exception specialists must not be written as after-the-fact audit or review specialists. They must
guide the next decision from context, artifact, surface, risk, and available
details, even when the prompt does not name a formal phase.

## Routing Rules

- Prefer one primary specialist.
- Recommend at most two follow-up routes.
- Infer artifact, phase, surface, and risk from prompt, repo, files, branch context, and conversation before withholding routing.
- Do not ask intake questions for artifact, phase, surface, or risk; withhold routing only when no in-scope engineering lifecycle/control frame is present.
- Do not route to out-of-scope business, marketing, legal, procurement, staffing, compensation, or broad compliance-program work.
- Eval-harness routing blocks are only for confident in-scope routing; low-confidence, ambiguous, and out-of-scope prompts must not emit routing blocks.
- Keep the router `SKILL.md` compact; detailed routing boundary notes belong in `skills/staff-engineer-mode/references/routing-matrix.md`.
