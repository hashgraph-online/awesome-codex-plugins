---
name: dev-spec
description: 'Compatibility alias for dev-grill-docs spec-only mode. Use when the user explicitly says dev-spec, spec 一下, 设计文档, 帮我设计, design this, or scope this out and expects a feature intent artifact at .claude/artifacts/designs/<feature>.md. Do not maintain a separate workflow here: load dev-grill-docs and follow it with --spec-only, preserving dev-spec trigger compatibility for existing docs and downstream tools.'
---

# Dev Spec

`dev-spec` is a compatibility alias for `dev-grill-docs --spec-only`.

Use it when the user explicitly asks for `dev-spec` or uses legacy spec-trigger language. Do **not** run a separate interview protocol from this file.

---

## Trigger routing

Trigger phrases include:

- `dev-spec`
- `spec 一下`
- `设计文档`
- `帮我设计`
- `写个方案`
- `这个需求要怎么做`
- `design this`
- `scope this out`

Behavior:

1. Load `../dev-grill-docs/SKILL.md`.
2. Follow the `dev-grill-docs` workflow with `--spec-only`.
3. Produce `.claude/artifacts/designs/<feature>.md`.
4. Do not update `CONTEXT.md` or `docs/adr/` unless the user explicitly asks to update persistent docs too.

Output goes to `.claude/artifacts/designs/<feature>.md`.

Optional arguments are forwarded:

- `--quick`
- `--deep`
- default mid-depth mode

---

## Compatibility contract

Existing downstream tools may still refer to `dev-spec`. Keep these semantics stable:

- The artifact path remains `.claude/artifacts/designs/<feature>.md`.
- The artifact status remains `DRAFT | ALIGNED | IMPLEMENTED | STUCK`.
- `STUCK` still means open questions block `dev-plan`.
- Acceptance criteria remain the source consumed by `dev-plan`, `dev-tdd`, `dev-verify`, and `dev-code-review`.
- `dev-auto`, old docs, and old prompts may continue to say `dev-spec`; treat that as `dev-grill-docs --spec-only`.

---

## Hard rules

- Do not copy or fork the grill/spec workflow here.
- Do not update `CONTEXT.md` / ADR from this alias unless explicitly requested.
- Do not write code.
- Do not route bugs here; use `dev-fix`.

---

## Multi-Agent Note

`dev-spec` remains main-agent-first because it negotiates scope with the user, but the actual workflow lives in `dev-grill-docs`.

Explorers may gather bounded read-only context. Apply `../../docs/multi-agent-policy.md` for delegation boundaries.

## SDD Contract

`dev-spec` remains a stable compatibility name for the feature intent contract.

When invoked, the contract is produced by `dev-grill-docs --spec-only` and has the same downstream anchors:

- `In scope`
- `Out of scope`
- `Assumptions`
- `Open questions`
- `Acceptance criteria`
