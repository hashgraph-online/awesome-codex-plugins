# AgentOps Skill Structure

`skills/<slug>/SKILL.md` is the source of truth for one AgentOps skill. Generated
catalogs, graphs, routers, counts, and Codex projections derive from its
metadata. Do not maintain a second inventory by hand.

## Package shape

```text
skills/<slug>/
├── SKILL.md           required source contract
├── references/        optional detailed material linked from SKILL.md
├── scripts/           optional repeatable mechanics
├── schemas/           optional machine-readable outputs
├── assets/            optional reusable payloads
└── SELF-TEST.md       optional trigger or behavior examples
```

Rules:

- Use a kebab-case directory and the exact filename `SKILL.md`.
- Match the frontmatter `name` to the directory.
- Keep the kernel at or below 250 lines.
- Add references, scripts, schemas, assets, or self-tests only when the skill
  needs them; their absence is not a quality defect.
- Link every reference from `SKILL.md`. Do not leave unreferenced package files.
- Put repeated deterministic mechanics in a script; keep judgment in prose.

## Frontmatter

The repository validators own the complete schema. A typical skill declares:

```yaml
---
name: example
description: 'What it does. Triggers: "phrase a caller would use".'
practices: [design-by-contract]
hexagonal_role: supporting
consumes: [explicit-input]
produces: [factual-output]
context_rel: []
skill_api_version: 1
metadata:
  capabilities: [example]
  effects: []  # NOT a default — list every side effect; keep [] only if the skill is genuinely read-only
  canonical_status: canonical
  disposition: keep_specialist
  tier: execution
  dependencies: []
output_contract: concise description or schema path
---
```

`effects` is load-bearing, not boilerplate. Declare every side effect the skill
performs — a file it writes, a process it starts, host or credential state it
mutates, a network call it makes — as a short snake_case phrase
(`write_advisory_report`, `modify_declared_subject`, `operate_gas_city`). Leave
`effects: []` only when the skill is genuinely read-only and returns to stdout;
copying `[]` onto a skill that writes is a false contract, not a safe default.

The description states both what the skill does and when it should load. Add
an inline `Triggers:` or `Use when:` marker with phrases a caller might
actually use. Also state an important false-positive boundary in the body when
the skill could be confused with a broader workflow.

Use `dependencies` only for behavior that cannot execute without the named
skill. Advisory context belongs in prose links or `context_rel`; it is not a
hard dependency. The core hard-dependency graph is only:

```text
rpi -> anti-ceremony
rpi -> plan
rpi -> implement
rpi -> validate
```

RPI invokes the anti-ceremony quick guard once before Plan. `STOP` dispatches
none of Plan, Implement, or Validate; `CONTINUE` preserves the ordered
Plan -> Implement -> fresh Validate traversal.

## Body contract

A good kernel makes five things obvious:

1. Trigger and purpose.
2. Inputs and boundaries.
3. The smallest ordered procedure.
4. Output and evidence.
5. Stop condition or unchecked scope.

Use natural language for cross-skill handoffs: “supply the result to Plan,” not
runtime-specific slash commands. A skill may describe optional adapters, but
must not silently start a runtime or assume one exists.

## Product boundary

AgentOps skills may shape intent, run one bounded experiment, establish exact
subject identity, make one fresh independent judgment, and preserve evidence.
They do not own:

- retry loops, attempt budgets, or automatic repair;
- queues, claims, leases, priorities, or work selection;
- Git state, commits, pushes, merging, release, or delivery;
- lifecycle closure, next actions, or operator notification policy.

If a specialist encounters failure, it reports the factual result and stops.
The caller decides what happens next.

## Outputs

The frontmatter `output_contract` is the binding concise declaration. Add a
body `## Output` section when readers need field meanings, a path convention,
or a validator command. Small inline skills do not need a ceremonial artifact
path, schema, filename, validator, and downstream handoff.

Structured outputs should name their schema and identity rules. Factual inline
outputs should name the fields or sentence shape. Never imply PASS, readiness,
or continuation unless the skill is Validate returning a fresh semantic result.
`verdict.v2` is an optional representation for declared consumers, not the
source of Validate's authority.

The reference example of a structured-output validator is
`skills/pattern-mining/scripts/validate-output.sh` — a small `jq` predicate that
checks a supplied output artifact against its declared contract. Copy that shape
when a skill emits a machine-readable artifact; do not reinvent it.

## Validation

Run the canonical checks after editing a skill:

```bash
bash skills/skill-builder/scripts/heal.sh --check --strict skills/<slug>
bash skills/skill-builder/scripts/audit.sh --strict skills/<slug>
bash scripts/validate-skill-frontmatter.sh --strict
python3 scripts/generate-skill-mesh.py --check
```

When metadata or behavior changes, regenerate the declared projections and
then validate them:

```bash
bash scripts/refresh-codex-artifacts.sh --scope worktree
bash scripts/validate-codex-generated-artifacts.sh --scope worktree
```

Add a focused test when the skill contains a parser, script, schema, or other
executable behavior. For a concise judgment prompt, example fixtures may be
enough. Validation should prove the behavior that exists, not reward package
size or ceremony.

## Review checklist

- The trigger and false-positive boundary are clear.
- The procedure has one owner and a bounded stop.
- The output contract matches actual behavior.
- Links resolve and optional resources are justified.
- No deleted skill, command, schema, or control-plane concept is live.
- Metadata and all generated projections agree.
