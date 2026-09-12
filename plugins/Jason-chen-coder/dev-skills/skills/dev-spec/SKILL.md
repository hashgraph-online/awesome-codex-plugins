---
name: dev-spec
description: 'Compatibility alias for dev-grill-docs spec-only mode. Use for explicit dev-spec requests, old dev-spec workflows, or spec-only output without CONTEXT.md / ADR updates. Ordinary requirement alignment belongs to dev-grill-docs. Preserves the feature artifact and acceptance contract, including when installed standalone.'
---

# Dev Spec

Treat `dev-spec` as `dev-grill-docs --spec-only`, forwarding `--quick` or `--deep`. Read [references/dev-baseline.md](references/dev-baseline.md).

When `dev-grill-docs` is available in the installed skill catalog, load it and apply its spec-only mode. Do not assume a sibling directory exists. When it is unavailable, use the compact compatibility contract below; no other skill is required to produce the artifact.

## Standalone compatibility contract

- Read the user's request and relevant existing docs, code, terminology, and tests before asking questions.
- Ask only about material unresolved behavior, scope, or acceptance. Preserve prior decisions; a clear request needs no mandatory interview. Record consequential evidence-backed assumptions and keep high-impact unresolved decisions explicit.
- Produce `.claude/artifacts/designs/<feature>.md` in the user's project unless the user specifies another path or chat-only output. Reuse an identifiable existing slug; otherwise choose a descriptive one without a routine confirmation turn.
- Include `Background`, `In scope`, `Out of scope`, `Solution`, and observable `Acceptance criteria` with stable `AC-1` identifiers. Include `Assumptions`, `Edge cases & risks`, `Open questions`, and core entities where relevant. The solution is a behavior sketch, not an implementation task list.
- Record source and update date. Preserve status vocabulary: `DRAFT` for proposed or unaligned intent, `ALIGNED` for materially resolved requirements supported by user direction or an accepted source, `STUCK` for concrete blocking questions, and `IMPLEMENTED` only when actual implementation evidence supports it. Changed requirements invalidate implementation status for the affected scope.
- A `STUCK` contract identifies the blocking decision, affected scope, and needed evidence or owner. Do not advance dependent implementation or planning by treating file existence as readiness.
- Report the artifact and unresolved issues. Respect intake-only or analysis-only scope. If broader implementation is already authorized, continue through the available workflow when requirements are sufficient.

## Boundaries

This alias writes no `CONTEXT.md` or `docs/adr/` unless the user explicitly adds those outputs. It does not implement code or diagnose bugs. Analysis-only and no-file instructions take precedence over the default artifact path. See [examples.md](examples.md) for compatibility cases.

## SDD Contract

Preserve `In scope`, `Out of scope`, `Assumptions`, `Open questions`, and stable `Acceptance criteria` for downstream planning, implementation, verification, and review. Existing calls to `dev-spec` keep the same artifact path and lifecycle vocabulary as `dev-grill-docs --spec-only`.

## Multi-Agent Note

Main-agent-first. If delegation is available and authorized, explorers may gather bounded facts and independent reviewers may evaluate a substantial contract; one agent owns questions and writes. In the source repository, `docs/multi-agent-policy.md` provides optional guidance, not a dependency for standalone use.
