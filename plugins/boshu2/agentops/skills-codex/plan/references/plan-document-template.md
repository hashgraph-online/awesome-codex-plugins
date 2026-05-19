# Plan Document Template

> Extracted from plan/SKILL.md on 2026-04-11.
> Canonical template written to `.agents/plans/YYYY-MM-DD-<goal-slug>.md` at Step 6.

**Baseline Audit Gate (mechanical):** Before writing the plan, verify the `## Baseline Audit` table has at least 1 row with both a command and a result:
- If `## Baseline Audit` is empty or missing: **BLOCK** with "Plan lacks baseline audit. Run quantitative checks first."
- If any row has a command but no result (or vice versa): **WARN** with "Incomplete audit row — run the command and record the result."
- **Opt-out:** `--skip-audit-gate` flag (for documentation-only plans with no quantitative claims).

```markdown
---
id: plan-YYYY-MM-DD-<goal-slug>
type: plan
date: YYYY-MM-DD
source: "[[.agents/research/YYYY-MM-DD-<research-slug>]]"
intent_issue: "<path to filled-in docs/templates/intent-issue.md, or bd issue id>"
---

# Plan: <Goal>

## Context
<1-2 paragraphs explaining the problem, current state, and why this change is needed. Include `Applied findings: <id, id, ...>` from `.agents/planning-rules/*.md` first, with `.agents/findings/registry.jsonl` as fallback.>

Applied findings:
- `<finding-id>` — `<how it changed the plan>`

## Intent Issue

> The upstream BDD intent issue this plan decomposes. Plan is move 3 of the [operating loop](../../docs/architecture/operating-loop.md): it consumes a [BDD intent issue](../../docs/templates/intent-issue.md) and turns its acceptance examples into vertical slices. If no intent issue exists yet, write one before planning non-trivial work.

- **Intent issue:** `<path to filled-in intent-issue.md, or bd issue id>`
- **Bounded context:** `<from intent issue — the BC this work lands in>`
- **Domain terms:** `<key ubiquitous-language terms the slices use>`

Acceptance examples carried from the intent issue (one Gherkin scenario per behavior — these map 1:1 to slices below):

```gherkin
Feature: <feature name from intent issue>

  Scenario: <happy path>
    Given <...>
    When <...>
    Then <...>

  Scenario: <edge / failure>
    Given <...>
    When <...>
    Then <...>
```

## Files to Modify

| File | Change |
|------|--------|
| `path/to/file.go` | Description of change |
| `path/to/new_file.go` | **NEW** — description |

> **Codex parity rule:** Whenever this table includes a `skills/<name>/` path, default-include the matching `skills-codex/<name>/` path on the same row (or a paired row) and add `scripts/regen-codex-hashes.sh` to the validation step. Skipping the codex mirror produces silent parity drift caught only by CI.

## Boundaries

**Always:** <non-negotiable requirements — security, backward compat, testing, etc.>
**Ask First:** <decisions needing human input before proceeding — in auto mode, logged only>
**Never:** <explicit out-of-scope items preventing scope creep>

## Baseline Audit

| Metric | Command | Result |
|--------|---------|--------|
| <what was measured> | `<grep/wc/ls command used>` | <result> |

## Implementation

### 1. <Change Group Name>

In `path/to/file.go`:

- **Modify `functionName`**: Add `paramName Type` parameter. If `paramName != ""` and condition, return `"value"`.

- **Add `NewStruct`**:
  ```go
  type NewStruct struct {
      FieldName string `json:"field_name,omitempty"`
  }
  ```

- **Key functions to reuse:**
  - `existingHelper()` at `path/to/file.go:123`
  - `anotherFunc()` at `path/to/other.go:456`

### 2. <Next Change Group>

<Same pattern — exact symbols, inline code, reuse references>

## Tests

**`path/to/file_test.go`** — add:
- `TestFunctionName_ScenarioA`: Input X produces output Y
- `TestFunctionName_ScenarioB`: Edge case Z handled correctly

**`path/to/new_test.go`** — **NEW**:
- `TestNewFeature_HappyPath`: Normal flow succeeds
- `TestNewFeature_ErrorCase`: Bad input returns error

## Slice Validation Plan

> Move 3 + 5 of the operating loop. One row per vertical slice — each slice covers a single Given/When/Then behavior from the Intent Issue, names a **first failing test** (TDD: write the test, watch it fail for the right reason, then implement), a disjoint write scope, the bounded context, and an owner. Full template: [`docs/templates/slice-validation.md`](../../docs/templates/slice-validation.md).

| Slice ID | Behavior under test | First failing test | Write scope | Validation lane | Owner | Acceptance example covered |
|----------|--------------------|--------------------|-------------|-----------------|-------|----------------------------|
| S1 | <single Given/When/Then behavior> | `<file:test_name>` — must fail for missing behavior, not syntax | `<files / packages this slice modifies>` | L1 unit / L2 integration / L3 e2e / property / snapshot / council | `<agent or human>` | Scenario: <name from Intent Issue> |
| S2 | … | … | … | … | … | … |

### Wave Validity

> If slices are planned to run in parallel, every row must pass. Any failed row → those slices run **sequential**. Default to sequential when in doubt.

| Check | Status | Notes |
|-------|--------|-------|
| Distinct write scopes (modified-files sets are disjoint) | [ ] | <overlapping files if any> |
| No shared migration / schema / generated file | [ ] | |
| No shared CLI surface (flags / arguments) | [ ] | |
| Integration order declared if it matters | [ ] | <named order or "n/a"> |
| Owner per slice (one agent or one human, no joint) | [ ] | |
| Discard path per slice (rollback or drop-and-re-plan) | [ ] | |

**Wave decision:** [ ] parallel  [ ] sequential

### Roll-up Acceptance

> The bead closes only when every acceptance example from the Intent Issue has a passing test linked to it. Activity logs do not close beads. This is the behavior layer; the machine-checkable layer is the Conformance Checks table below — keep both.

| Acceptance example from Intent Issue | Slice(s) that cover it | Passing-test evidence | Status |
|---------------------------------------|------------------------|------------------------|--------|
| Scenario: <happy path name> | S1 | `<file:test_name>` — green at `<git sha>` | [ ] |
| Scenario: <edge name> | S2 | `<file:test_name>` — green at `<git sha>` | [ ] |

## Conformance Checks

> Machine-checkable acceptance layer. Gherkin in the Roll-up Acceptance table is the behavior layer; this table stays the mechanically verified gate — do not replace it with Gherkin prose.

| Issue | Check Type | Check |
|-------|-----------|-------|
| Issue 1 | content_check | `{file: "src/auth.go", pattern: "func Authenticate"}` |
| Issue 1 | tests | `go test ./src/auth/...` |
| Issue 2 | files_exist | `["docs/api-v2.md"]` |

## Verification

1. **Unit tests**: `go test ./path/to/ -run "TestFoo" -v`
2. **Full suite**: `go test ./... -short -timeout 120s`
3. **Manual simulation**:
   ```bash
   # Create test scenario
   mkdir -p .test/data
   echo '{"key": "value"}' > .test/data/input.json
   # Run the tool
   ./bin/tool --flag value
   # Verify expected output
   cat .test/data/output.json  # Should show "result"
   ```

## Issues

### Issue 1: <Title>
**Dependencies:** None
**Acceptance:** <how to verify>
**Description:** <what to do — reference Implementation section for symbol-level detail>

### Issue 2: <Title>
**Dependencies:** Issue 1
**Acceptance:** <how to verify>
**Description:** <what to do>

## Execution Order

**Wave 1** (parallel): Issue 1, Issue 3
**Wave 2** (after Wave 1): Issue 2, Issue 4
**Wave 3** (after Wave 2): Issue 5

## Planning Rules Compliance

| Rule | Status | Justification |
|------|--------|---------------|
| PR-001: Mechanical Enforcement | PASS / N-A | [justification] |
| PR-002: External Validation | PASS / N-A | [justification] |
| PR-003: Feedback Loops | PASS / N-A | [justification] |
| PR-004: Separation Over Layering | PASS / N-A | [justification] |
| PR-005: Process Gates First | PASS / N-A | [justification] |
| PR-006: Cross-Layer Consistency | PASS / N-A | [justification] |
| PR-007: Phased Rollout | PASS / N-A | [justification] |

Unchecked rules: 0

## Post-Merge Cleanup

After bulk-merging wave results, audit for scaffold-era names:
- Rename placeholder function/variable names (e.g., `handleThing`, `processItem`) to domain-specific names
- Search with `grep -rn 'TODO\|FIXME\|HACK\|XXX' <modified-files>` for deferred cleanup markers
- If any `skills/` files were modified, run `scripts/regen-codex-hashes.sh` to sync codex parity and copy reference files.

## Next Steps
- Run `/pre-mortem` to validate plan
- Run `/crank` for autonomous execution
- Or `/implement <issue>` for single issue
```
