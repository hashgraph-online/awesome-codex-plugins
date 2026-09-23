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

Canonical section H2 headings:

```markdown
## Goal
## Dependencies
## Owned files
## Tests first
## Implementation contract
## Evidence
## Decisions
## Risks
## Review
## Acceptance
```

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
