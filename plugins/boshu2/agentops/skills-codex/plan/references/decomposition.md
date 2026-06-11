# Decomposition Patterns

> Extracted from plan/SKILL.md on 2026-04-11.
> Anti-pattern pre-flight, issue granularity, conformance checks, schema strictness.

## Anti-Pattern Pre-Flight

Before finalizing issue decomposition, verify the plan avoids these confirmed failure modes:

| Anti-Pattern | Detection Question | Gate |
|---|---|---|
| **Free-text-only acceptance** | Does every bead carry an embedded `## Scenarios` Gherkin block by default? | FAIL if any bead ships free-text-only acceptance with no `## Scenarios` (Given/When/Then) block — promote it to scenarios before creating the bead |
| **Brainstorm masquerading as plan** | Does every issue have mechanically verifiable acceptance criteria? | FAIL if any issue lacks `files_exist`, `content_check`, `tests`, or `command` conformance checks |
| **Dead infrastructure** | Does the plan provision anything without an activation test? | WARN if infrastructure is created without a corresponding smoke test issue |
| **Propagation surface blindness** | Has the full propagation surface been enumerated for renames/refactors? | FAIL if structural changes lack a propagation surface table |
| **40% context budget violation** | Will implementation sessions need to load >40% context window for knowledge? | WARN if injected knowledge exceeds estimated budget |
| **Commit-per-session anti-pattern** | Does the wave structure enforce commit-per-wave? | WARN if no explicit commit cadence in execution order |

## Design Briefs for Rewrites

For any issue that says "rewrite", "redesign", or "create from scratch":
Include a **design brief** (3+ sentences) covering:
1. **Purpose** — what does this component do in the new architecture?
2. **Key artifacts** — what files/interfaces define success?
3. **Workflows** — what sequences must work?

Without a design brief, workers invent design decisions. In ol-571, a spec rewrite issue without a design brief produced output that diverged from the intended architecture.

## Issue Granularity

- **1-2 independent files** → 1 issue
- **3+ independent files with no code deps** → split into sub-issues (one per file)
  - Example: "Rewrite 4 specs" → 4 sub-issues (4.1, 4.2, 4.3, 4.4)
  - Enables N parallel workers instead of 1 serial worker
- **Shared files between issues** → serialize or assign to same worker

## Operationalization Heuristics

Each issue must be immediately executable by a swarm worker without further research:

- **File ownership (`metadata.files`):** List every file the issue touches. Workers use this for conflict detection.
- **Validation commands (`metadata.validation`):** Include runnable checks (e.g., `go test ./...`, `bash -n script.sh`). Workers run these before reporting done.
- **Homogeneous wave grouping:** Group issues by work type (all Go, all docs, all shell) within the same wave. Mixed-type waves cause toolchain context-switching and increase conflict risk.
- **Same-file serialization:** If two issues touch the same file, flag them for serialization (different waves) or merge into one issue. Never assign same-file issues to parallel workers.

## Conformance Checks

For each issue's acceptance criteria, derive at least one **mechanically verifiable** conformance check using validation-contract.md types. These checks bridge the gap between spec intent and implementation verification.

| Acceptance Criteria | Conformance Check |
|-----|------|
| "File X exists" | `files_exist: ["X"]` |
| "Function Y is implemented" | `content_check: {file: "src/foo.go", pattern: "func Y"}` |
| "Tests pass" | `tests: "go test ./..."` |
| "Endpoint returns 200" | `command: "curl -s -o /dev/null -w '%{http_code}' localhost:8080/api \| grep 200"` |
| "Config has setting Z" | `content_check: {file: "config.yaml", pattern: "setting_z:"}` |

**Rules:**
- Every issue MUST have at least one conformance check
- Checks MUST use validation-contract.md types: `files_exist`, `content_check`, `command`, `tests`, `lint`
- Prefer `content_check` and `files_exist` (fast, deterministic) over `command` (slower, environment-dependent)
- If acceptance criteria cannot be mechanically verified, flag it as underspecified
- When adding entries to config files enumerated by tests, search for hardcoded count assertions: `grep -rn 'len.*!=\|len.*==\|expected.*count' <test-dir>/`

## Schema Strictness Pre-Flight (WARN)

When any issue's file list includes JSON schema files (`*.schema.json`, files in `schemas/`), check for `additionalProperties: false`:

```bash
for f in <issue-files matching *.schema.json or schemas/*.json>; do
  if grep -q '"additionalProperties":\s*false' "$f" 2>/dev/null; then
    echo "WARN: $f has additionalProperties:false — new fields require schema update BEFORE consumer changes"
  fi
done
```

**If triggered:** Ensure schema-modifying issues are in an earlier wave than issues that reference the new fields. This prevents implementation failures where consumer SKILL.md files reference fields that the schema doesn't yet allow.

This is advisory (WARN, not FAIL). The wave decomposition in Step 5 must respect this ordering.
