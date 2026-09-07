# Section format

Start `sections/index.md` with detected values and sequential names:

```markdown
<!-- PROJECT_CONFIG
runtime: <runtime>
test_command: <exact command>
END_PROJECT_CONFIG -->
<!-- SECTION_MANIFEST
section-01-foundation
END_MANIFEST -->
```

Then use `| Section | Depends on | REQ | Owns | Tests |`; state execution
order, safe parallel groups, and shared sequencing once.

Each section contains:

```markdown
# section-NN-name
Goal: ...
REQ: REQ-...
Depends: ... or none
## Exact path ownership
## Tests first
- test path/case -> expected RED; command
## Implementation
- path -> behavior/contract/error/migration delta
## Risks and rollback
## Acceptance and verification
```

Reference plan IDs and paths; copy no source or plan context. Include only
owned contracts, fixtures, edge cases, and risks. Tests precede implementation.
Each file has one owner; explicitly order unavoidable shared edits.

Generated or delegated section prompts are at most 300 words and point to the
source, plan, review, and index instead of embedding them.
