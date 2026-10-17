# Canonical Plan

All depths support compact artifacts. Preserve the source spec; never use the
plan/index/section itself as its source.

## One section

Put this metadata in `sections/index.md`, beside its config/manifest blocks:

```markdown
<!-- FORGE_META
{"artifact_type":"compact_plan","depth_mode":"deep","source":"spec.md"}
END_FORGE_META -->
```

Use actual depth and planning-directory-relative source. The single manifest
section is the canonical plan, with the compact contract from
[section format](section-format.md). Evidence, decisions, risks, test mapping,
and review live there once; no duplicate `codex-plan.md` or review file.

Setup creates an unfinished example boundary, not an inferred decomposition.
Rename/split sections when the inspected task warrants it. For multiple sections,
move the shared contract and metadata to `codex-plan.md`, remove index metadata,
and keep local deltas in sections before admission. Never overwrite an admitted tree.

## Multiple sections

Use `codex-plan.md` with the same explicit `compact_plan` metadata for shared
contracts and embedded review/evidence. Sections own local deltas and link exact
IDs/anchors. Sequence shared-file changes.

Legacy physical artifacts remain supported. Detached frozen mode requires the
established physical `codex-plan.md`/`claude-plan.md` and separate review artifacts;
it rejects `compact_plan` metadata and embedded-review shortcuts.
Choose the [detached authoring route](detached-plan-format.md) before writing or freezing.

Preserve explicit source `REQ-*` IDs. When the source has none, define IDs in the
canonical `## Contract`, linking each to the unchanged brief's lines. Links use
paths relative to the planning directory and must cover visible source content;
comments and fenced example IDs do not declare requirements. Each mapping holds
behavior, inputs/outputs/errors, expected acceptance and verification together.
Keep ownership and rollback explicit. Prefer existing code/native facilities;
omit repeated background, production implementations, and placeholders.
