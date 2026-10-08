# Sections

Start `sections/index.md` with detected values and sequential names:

```markdown
<!-- PROJECT_CONFIG
runtime: <runtime>
test_command: <command>
END_PROJECT_CONFIG -->
<!-- SECTION_MANIFEST
section-01-foundation
END_MANIFEST -->
Dependencies: none.
Execution order: section-01-foundation.
Parallel: no siblings.
```

Add [compact-plan metadata](plan-format.md) for a single canonical section.
For detached execution, omit it and follow [physical authoring](detached-plan-format.md).
For multiple sections, use `| Section | Depends on | REQ | Owns | Tests |`;
record execution order/shared sequencing once.

For a canonical section, use four headings and bind each requirement once:

```markdown
## Contract
### REQ-001
Source: spec.md#L1-L3
Behavior: Trim label edges in the existing helper; preserve case, internal spaces and errors.
Expected: test_trim_edges maps " Ada Lovelace " to "Ada Lovelace"; current code preserves edges.
Command: uv run pytest tests/test_labels.py

## Owned files
- src/labels.py
- tests/test_labels.py

## Evidence
Inspected callers, runtime and existing tests; record actual evidence here.
Record relevant assumptions, rationale, compatibility/security risks and rollback.

## Review
Verdict: pass
Reviewed: the actual contract, source coverage, edge cases, ownership and regression evidence; record findings.
```

Replace the example with inspected facts; unfinished fields or a blocked review
cannot pass. Keep source IDs exactly; for a brief without IDs, source links must
cover its visible content. Do not hide mappings in comments or fences.

The Contract supplies implementation, tests and acceptance without repeating them
under separate headings. Dependencies/order stay in the index. Add `## Decisions`
or `## Risks` only for material detail; short evidence can hold those facts.
Depth still controls investigation and review, including compatibility, security,
alternatives and consequential failure modes. Legacy Goal/Tests first/Implementation
contract/Acceptance sections remain supported; detached plans use their physical route.

Bind `REQ-*` to observable acceptance and tests: path/case, expected RED, command.
Any language can use `Case:`/`Behavior:`, `Expected:`, and `Command:` labels.
For documentation/cosmetic-only changes, use `verification_mode: inspection`,
`Inspection: <actual check>`, `Expected: <observable result>`, and
`test_rationale: <documentation-only/cosmetic-only/formatting-only reason>`.
Keep local inputs/outputs/errors explicit. List owned repo-relative paths as
bullets or a closed `text` fence; separate read-only references. Each file has
one owner unless edits are explicitly sequenced. Include applicable rollback
and stop conditions. Link shared contracts precisely; never copy background.
Review requires a verdict plus actual reviewed scope/result.

## Compatibility

New mutable plans require a `## Compatibility` section in each section file.
Use the [shared declaration and execution contract](../../zagrosi-implement/references/compatibility.md):
one fenced JSON object declares protected source, checks and their provenance,
or `not_required` with a concrete reason. Keep the protected behavior and intended
changes in the existing Contract; do not create another behavior ledger.
An undecided draft cannot pass admission. Existing undeclared plans remain legacy;
the pinned detached protocol retains its own evidence format.
