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
| **Big-batch slice** (PR-010) | Does any slice deliver more than one Given/When/Then behavior? | FAIL if a slice bundles ≥2 behaviors — split into one-behavior slices (small batches beat all-at-once; Finster 2026) |
| **Refactor folded into a feature slice** (PR-010) | Does any slice mix "make it work" (feature) with "make it clean" (refactor)? | FAIL if a slice mixes refactor + feature — split into two slices so refactor-after-green happens as its own commit (the load-bearing quality move) |
| **Over-planned thoroughness** (PR-011) | Does a small, low-risk, fully-specified slice plan full mutation (BF3) or the whole BF1–BF9 corpus? | WARN — throttle to L2 + L1 regression guards; reserve heavy BF for critical/security/high-blast-radius slices (the over-testing tax) |

## Design Briefs for Rewrites

For any issue that says "rewrite", "redesign", or "create from scratch":
Include a **design brief** (3+ sentences) covering:
1. **Purpose** — what does this component do in the new architecture?
2. **Key artifacts** — what files/interfaces define success?
3. **Workflows** — what sequences must work?

Without a design brief, workers invent design decisions. In ol-571, a spec rewrite issue without a design brief produced output that diverged from the intended architecture.

## Issue Granularity

Granularity has two axes: **behavior** (how many Given/When/Then the slice delivers) and **files** (how many the slice touches). Behavior is primary — decompose by behavior first, then use the file axis to decide parallelism.

### Behavior batch size (small batches) — primary axis

- **One behavior per slice.** Each slice delivers exactly one Given/When/Then. A slice that delivers two or more behaviors is a big-batch anti-pattern (PR-010) — split it. Small batches (one behavior per cycle) beat all-at-once across cost, changeability, and quality (Finster 2026, `skills/standards/references/agentic-workflow-evidence.md`).
- **Refactor is its own slice.** Never fold a refactor into a feature slice. "Refactor then feature" is two slices (operating-loop move 3). Refactor-after-every-green is the load-bearing quality move — scheduling it as a distinct unit is what makes it actually happen rather than get deferred to a final pass (the worst-performing cluster in the study).
- **Test-first ordering is not the quality lever** — do not add ceremony slices for it. What matters is that each slice carries a runnable acceptance test (its contract, owned by `behavior-first-planning`) and that refactor-under-green follows each green.

### File axis — decides parallelism, not batch size

- **1-2 independent files** → 1 issue
- **3+ independent files with no code deps** → split into sub-issues (one per file)
  - Example: "Rewrite 4 specs" → 4 sub-issues (4.1, 4.2, 4.3, 4.4)
  - Enables N parallel workers instead of 1 serial worker
- **Shared files between issues** → serialize or assign to same worker

The file axis never overrides the behavior axis: a single behavior spanning several files is still one slice (one contract), and several behaviors in one file are still several slices (serialized on that file).

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
