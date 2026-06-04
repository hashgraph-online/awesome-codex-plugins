---
name: vibe
description: 'Validate code readiness.'
---
# Vibe Skill

> **Purpose:** Is this code ready to ship?

Three steps:
1. **Complexity analysis** — Find hotspots (radon, gocyclo)
2. **Bug hunt audit** — Systematic sweep for concrete bugs
3. **Council validation** — Multi-model judgment

---

## Quick Start

```bash
$vibe                                    # validates recent changes
$vibe recent                             # same as above
$vibe src/auth/                          # validates specific path
$vibe --quick recent                     # fast inline check, no agent spawning
$vibe --deep recent                      # 3 judges instead of 2
$vibe --sweep recent                     # deep audit: per-file explorers + council
$vibe --mixed recent                     # cross-vendor (Claude + Codex)
$vibe --preset=security-audit src/auth/  # security-focused review
$vibe --explorers=2 recent               # judges with explorer sub-agents
$vibe --debate recent                    # two-round adversarial review
```

---

## Execution Steps

**Project reviewer config:** If `.agents/reviewer-config.md` exists, its full config (`reviewers`, `plan_reviewers`, `skip_reviewers`) is passed to council for judge selection. See `$council` Step 1b.

### Crank Checkpoint Detection

Before scanning for changed files via git diff, check if a crank checkpoint exists:

```bash
if [ -f .agents/vibe-context/latest-crank-wave.json ]; then
    echo "Crank checkpoint found — using files_changed from checkpoint"
    FILES_CHANGED=$(jq -r '.files_changed[]' .agents/vibe-context/latest-crank-wave.json 2>/dev/null)
    WAVE_COUNT=$(jq -r '.wave' .agents/vibe-context/latest-crank-wave.json 2>/dev/null)
    echo "Wave $WAVE_COUNT checkpoint: $(echo "$FILES_CHANGED" | wc -l | tr -d ' ') files changed"
fi
```

When a crank checkpoint is available, use its `files_changed` list instead of re-detecting via `git diff`. This ensures vibe validates exactly the files that crank modified.

### Step 1: Determine Target

**If target provided:** Use it directly.

**If no target or "recent":** Auto-detect from git:
```bash
# Check recent commits
git diff --name-only HEAD~3 2>/dev/null | head -20
```

If nothing found, ask user.

**Pre-flight: If no files found:**
Return immediately with: "PASS (no changes to review) — no modified files detected."
Do NOT spawn agents for empty file lists.

### Step 1.5: Fast Path (--quick mode)

**If `--quick` flag is set**, skip Steps 2a through 2e as heavy pre-processing, plus 2.5 and 2f, and jump to Step 4 with inline council after Steps 2.3, 2.4, 2g, and Step 3. Domain checklists, compiled-prevention loading, test-pyramid inventory, and inline product context are cheap and high-value, so they still run in quick mode. Complexity analysis (Step 2) still runs — it's cheap and informative.

**Why:** Steps 2.5 and 2a–2f add 30–90 seconds of pre-processing that mainly feed multi-judge council packets. In --quick mode (single inline agent), those inputs are not worth the cost, but test-pyramid and product-context checks still shape the inline review meaningfully.

### Step 2: Run Complexity Analysis

**Filter by language present in the change set first.** Run only the
analyzers whose language actually appears in the diff. A docs/shell/BATS-only
epic must NOT trigger `gocyclo` against the entire `cli/` tree (it has hung
in past runs); a Python-free epic must NOT trigger `radon`.

```bash
# Detect which languages are present in the diff (or in <path> for full audits).
# Use `git diff --name-only <base>...HEAD` for a PR; fall back to listing
# files under <path> when no diff base is available.
mkdir -p .agents/council
HAS_GO=false; HAS_PY=false
DIFF_FILES="$(git diff --name-only "${BASE:-HEAD~1}"...HEAD 2>/dev/null || find <path> -type f)"
echo "$DIFF_FILES" | grep -q '\.go$'  && HAS_GO=true
echo "$DIFF_FILES" | grep -q '\.py$'  && HAS_PY=true
echo "$(date -Iseconds) preflight: HAS_GO=$HAS_GO HAS_PY=$HAS_PY" >> .agents/council/preflight.log
```

**For Python (only when `HAS_PY=true`):**
```bash
if [ "$HAS_PY" = "true" ]; then
  echo "$(date -Iseconds) preflight: checking radon" >> .agents/council/preflight.log
  if ! which radon >> .agents/council/preflight.log 2>&1; then
    echo "⚠️ COMPLEXITY SKIPPED: radon not installed (pip install radon)"
  else
    radon cc <path> -a -s 2>/dev/null | head -30
    radon mi <path> -s 2>/dev/null | head -30
  fi
else
  echo "ℹ️ COMPLEXITY SKIPPED: no .py files in diff"
fi
```

**For Go (only when `HAS_GO=true`):**
```bash
if [ "$HAS_GO" = "true" ]; then
  echo "$(date -Iseconds) preflight: checking gocyclo" >> .agents/council/preflight.log
  if ! which gocyclo >> .agents/council/preflight.log 2>&1; then
    echo "⚠️ COMPLEXITY SKIPPED: gocyclo not installed (go install github.com/fzipp/gocyclo/cmd/gocyclo@latest)"
  else
    gocyclo -over 10 <path> 2>/dev/null | head -30
  fi
else
  echo "ℹ️ COMPLEXITY SKIPPED: no .go files in diff"
fi
```

**For other languages:** Skip complexity with explicit note: "⚠️ COMPLEXITY SKIPPED: No analyzer for <language>"

**Interpret results:**

| Score | Rating | Action |
|-------|--------|--------|
| A (1-5) | Simple | Good |
| B (6-10) | Moderate | OK |
| C (11-20) | Complex | Flag for council |
| D (21-30) | Very complex | Recommend refactor |
| F (31+) | Untestable | Must refactor |

**Include complexity findings in council context.**

### Step 2.3: Load Domain-Specific Checklists

Detect code patterns in the target files and load matching domain-specific checklists from `standards/references/`:

| Trigger | Checklist | Detection |
|---------|-----------|-----------|
| SQL/ORM code | `sql-safety-checklist.md` | Files contain SQL queries, ORM imports (`database/sql`, `sqlalchemy`, `prisma`, `activerecord`, `gorm`, `knex`), or migration files in changeset |
| LLM/AI code | `llm-trust-boundary-checklist.md` | Files import `anthropic`, `openai`, `google.generativeai`, or match `*llm*`, `*prompt*`, `*completion*` patterns |
| Concurrent code | `race-condition-checklist.md` | Files use goroutines, `threading`, `asyncio`, `multiprocessing`, `sync.Mutex`, `concurrent.futures`, or shared file I/O patterns |
| Codex skills | `codex-skill.md` | Files under `skills-codex/`, or files matching `*codex*SKILL.md`, `convert.sh`, `skills-codex-overrides/`, or converter scripts |

For each matched checklist, load it by reading the file and include relevant items in the council packet as `context.domain_checklists`. Multiple checklists can be loaded simultaneously.

Skip silently if no patterns match. This step runs in both `--quick` and full modes (domain checklists are cheap to load and high-value).

### Step 2.4: Compiled Prevention Check

Before reading `.agents/rpi/next-work.jsonl`, load compiled prevention context from `.agents/pre-mortem-checks/*.md` and `.agents/planning-rules/*.md` when they exist. This is the primary reusable-prevention surface for review.

Use the tracked contracts in `docs/contracts/finding-compiler.md` and `docs/contracts/finding-registry.md`:

- prefer compiled pre-mortem checks and planning rules first
- rank by severity, `applicable_when` overlap, language overlap, changed-file overlap, and literal target-text overlap
- keep the ranking order consistent with `$plan` and `$pre-mortem`; do not invent a separate review-only heuristic
- cap at top 5 findings / compiled files
- if compiled outputs are missing, incomplete, or fewer than the matched finding set, fall back to `.agents/findings/registry.jsonl`
- fail open:
  - missing compiled directory or registry -> skip silently
  - empty compiled directory or registry -> skip silently
  - malformed line -> warn and ignore that line
  - unreadable file -> warn once and continue without findings

Include matched entries in the council packet as `known_risks` / checklist context with:
- `id`
- `pattern`
- `detection_question`
- `checklist_item`

### Step 2.5: Prior Findings Check

**Skip if `--quick` (see Step 1.5).**

Read `.agents/rpi/next-work.jsonl` and find unconsumed items with `severity=high` that match the target area. Include them in the council packet as `context.prior_findings` so judges have carry-forward context.

Treat these high-severity queue items as part of the same ranked packet used earlier in discovery/plan/pre-mortem. The review stage should inherit and refine prior findings context, not restart retrieval from scratch.

```bash
# Count unconsumed high-severity items
if [ -f .agents/rpi/next-work.jsonl ] && command -v jq &>/dev/null; then
  prior_count=$(jq -s '[.[] | select(.consumed == false) | .items[] | select(.severity == "high")] | length' \
    .agents/rpi/next-work.jsonl 2>/dev/null || echo 0)
  if [ "$prior_count" -gt 0 ]; then
    echo "Prior findings: $prior_count unconsumed high-severity items from next-work.jsonl"
    jq -s '[.[] | select(.consumed == false) | .items[] | select(.severity == "high")]' \
      .agents/rpi/next-work.jsonl 2>/dev/null
  fi
fi
```

If unconsumed high-severity items are found, include them in the council packet context:
```json
"prior_findings": {
  "source": ".agents/rpi/next-work.jsonl",
  "count": 3,
  "items": [/* array of high-severity unconsumed items */]
}
```

**Skip conditions:**
- `--quick` mode → skip
- `.agents/rpi/next-work.jsonl` does not exist → skip silently
- `jq` not on PATH → skip silently
- No unconsumed high-severity items found → skip (do not add empty `prior_findings` to packet)

### Step 2a: Run Constraint Tests

**Skip if `--quick` (see Step 1.5).**

**If the project has constraint tests, run them before council:**

```bash
# Check if constraint tests exist
if [ -d "internal/constraints" ] && ls internal/constraints/*_test.go &>/dev/null; then
  echo "Running constraint tests..."
  go test ./internal/constraints/ -run TestConstraint -v 2>&1
  # If FAIL → include failures in council context as CRITICAL findings
  # If PASS → note "N constraint tests passed" in report
fi
```

**Why:** Constraint tests catch mechanical violations (ghost references, TOCTOU races, dead code at entry points) that council judges miss.

Include constraint test results in the council packet context. Failed constraint tests are CRITICAL findings that override council PASS verdict.

### Step 2b: Metadata Verification Checklist (MANDATORY)

**Skip if `--quick` (see Step 1.5).**

Run mechanical checks BEFORE council — catches errors LLMs estimate instead of measure:
1. **File existence** — every path in `git diff --name-only HEAD~3` must exist on disk
2. **Line counts** — if a file claims "N lines", verify with `wc -l`
3. **Cross-references** — internal markdown links resolve to existing files
4. **Diagram sanity** — files with >3 ASCII boxes should have matching labels

Include failures in council packet as `context.metadata_failures` (MECHANICAL findings). If all pass, note in report.

### Step 2d: Codex Review (opt-in via `--mixed`)

**Skip unless `--mixed` is passed.** Also skip if `--quick` (see Step 1.5).

Codex review is opt-in because it adds 30–60s latency and token cost. Users explicitly request cross-vendor input with `--mixed`.

```bash
echo "$(date -Iseconds) preflight: checking codex" >> .agents/council/preflight.log
if which codex >> .agents/council/preflight.log 2>&1; then
  codex review --uncommitted > .agents/council/codex-review-pre.md 2>&1 && \
    echo "Codex review complete — output at .agents/council/codex-review-pre.md" || \
    echo "Codex review skipped (failed)"
else
  echo "Codex review skipped (CLI not found)"
fi
```

**If output exists**, summarize and include in council packet (cap at 2000 chars to prevent context bloat):
```json
"codex_review": {
  "source": "codex review --uncommitted",
  "content": "<first 2000 chars of .agents/council/codex-review-pre.md>"
}
```

**IMPORTANT:** The raw codex review can be 50k+ chars. Including the full text in every judge's packet multiplies token cost by N judges. Truncate to the first 2000 chars (covers the summary and top findings). Judges can read the full file from disk if they need more detail.

This gives council judges a Codex-generated review as pre-existing context — cheap, fast, diff-focused. It does NOT replace council judgment; it augments it.

**Skip conditions:**
- `--mixed` not passed → skip (opt-in only)
- Codex CLI not on PATH → skip silently
- `codex review` fails → skip silently, proceed with council only
- No uncommitted changes → skip (nothing to review)

### Step 2e: Search Knowledge Flywheel

**Skip if `--quick` (see Step 1.5).**

```bash
if command -v ao &>/dev/null; then
    ao search "code review findings <target>" 2>/dev/null | head -10
fi
```
**Apply retrieved knowledge (mandatory when results returned):**

If ao returns prior code review patterns, do NOT just load them as passive context. For each returned item:
1. Check: does this learning apply to the code under review? (answer yes/no)
2. If yes: include it as a `known_risk` in your review — state the pattern, what to look for, and whether the code exhibits it
3. Cite the learning by filename in your review output when it influences a finding

After applying, record the citation:
```bash
ao metrics cite "<learning-path>" --type applied 2>/dev/null || true
```

Skip silently if ao is unavailable or returns no results.

### Step 2f: Bug Hunt or Deep Audit Sweep

**Skip if `--quick` (see Step 1.5).**

**Path A — Deep Audit Sweep (`--deep` or `--sweep`):**

Read `references/deep-audit-protocol.md` for the full protocol. In summary:

1. Chunk target files into batches of 3–5 (by line count — see protocol for rules)
2. Dispatch up to 8 Explore agents in parallel, each with a mandatory 8-category checklist per file
3. Merge all explorer findings into a sweep manifest at `.agents/council/sweep-manifest.md`
4. Include sweep manifest in the council packet so judges shift to adjudication mode

**Why:** Generalist judges exhibit satisfaction bias — they stop at ~10 findings regardless of actual issue count. Per-file explorers with category checklists eliminate this bias and find 3x more issues in a single pass.

**Path B — Lightweight Bug Hunt (default, no `--deep`/`--sweep`):**

Run a proactive bug hunt on the target files before council review:

```
$bug-hunt --audit <target>
```

If bug-hunt produces findings, include them in the council packet as `context.bug_hunt`:
```json
"bug_hunt": {
  "source": "$bug-hunt --audit",
  "findings_count": 3,
  "high": 1,
  "medium": 1,
  "low": 1,
  "summary": "<first 2000 chars of bug hunt report>"
}
```

**Why:** Bug hunt catches concrete line-level bugs (resource leaks, truncation errors, dead code) that council judges — reviewing holistically — often miss.

**Skip conditions (both paths):**
- `--quick` mode → skip (fast path)
- No source files in target → skip (nothing to audit)
- Target is non-code (pure docs/config) → skip

### Test Pyramid Inventory

Assess test coverage against the test pyramid standard (see the standards skill).

Read `skills/vibe/references/test-pyramid-weighting.md` for test pyramid weighting — L3+ tests found all production bugs, weight them 5x.

**Test Pyramid Weighting:** Weight test coverage by level: L0–L1 at 1x, L2 at 3x, L3+ at 5x. Unit-only coverage is a WARN signal, not a PASS. See `references/test-pyramid-weighting.md`.

1. Identify changed modules from git diff
2. Check L0-L3 coverage for each changed module
3. Check BF4 (chaos) for boundary-touching code
4. **Compute weighted pyramid score** for changed code paths:

   **Formula:**
   ```
   weighted_score = (L0_count x 1 + L1_count x 1 + L2_count x 3 + L3_count x 5 + L4_count x 5) / max_possible
   ```
   Where `max_possible = total_test_count x 5` (the score if every test were L3+).

   Count tests at each level for changed code paths:
   - L0: Build/compile checks (weight 1)
   - L1: Unit tests (weight 1)
   - L2: Integration tests (weight 3)
   - L3: E2E/system tests (weight 5)
   - L4: Smoke/fresh-context tests (weight 5)

   **Interpretation:**
   - `weighted_score >= 0.6` — strong pyramid, L2+ tests present
   - `0.3 <= weighted_score < 0.6` — acceptable, but recommend more integration tests
   - `weighted_score < 0.3` AND all tests are L0-L1 only — **WARN: unit-only test coverage** (feeds into vibe verdict as a WARN signal, not a separate gate)

   **Include in vibe report output:**
   ```
   ## Test Pyramid Score
   | Level | Count | Weight | Contribution |
   |-------|-------|--------|--------------|
   | L0    | 2     | 1x     | 2            |
   | L1    | 8     | 1x     | 8            |
   | L2    | 0     | 3x     | 0            |
   | L3    | 0     | 5x     | 0            |
   | L4    | 0     | 5x     | 0            |
   | **Total** | **10** | | **10 / 50 = 0.20** |
   WARN: weighted_score 0.20 < 0.3 and all tests are L0-L1 only
   ```

5. Include `test_pyramid` context in review output with score data:
   ```json
   "test_pyramid": {
     "weighted_score": 0.20,
     "score_breakdown": {"L0": 2, "L1": 8, "L2": 0, "L3": 0, "L4": 0},
     "max_possible": 50,
     "warn_unit_only": true,
     "satisfaction_score": 0.20,
     "satisfaction_source": "test-pyramid-weighted"
   }
   ```

**Satisfaction exposure:** The `weighted_score` is also exposed as `satisfaction_score`
for downstream consumers (STEP 1.8 behavioral validation, verdict schema v4).
This is the same value — just labeled for the satisfaction scoring pipeline.

**Verdict rules:**
- `weighted_score < 0.3` AND all tests L0-L1 only — **WARN: unit-only coverage**
- Missing L1 on feature code — **WARN**
- Missing BF4 on boundary code — **WARN** (advisory, not blocking)
- All levels covered with `weighted_score >= 0.6` — no mention needed

When coverage gaps are found, run `$test <module>` to generate test candidates for uncovered code.

### Scenario→Test Coverage (MANDATORY when the slice has scenarios)

The test-pyramid inventory checks that tests *exist* and are well-shaped — it does NOT check that each of the slice's acceptance scenarios maps to a test. The leaf gate for that is `scripts/check-bead-scenario-coverage.sh` (C2, ag-9jle.4). It parses the bead's `## Scenarios` block (or a `.feature` file) and FAILS if any scenario lacks a `@covered-by:<test-path>` link — it works *forward from behavior*, not backward from coverage %.

```bash
# When validating a tracked bead with a ## Scenarios block:
bash scripts/check-bead-scenario-coverage.sh --bead <bead-id> --json

# When validating a .feature directly:
bash scripts/check-bead-scenario-coverage.sh skills/<skill>/references/<name>.feature --json
```

A FAIL here is a vibe blocker, not a WARN: "tests exist" or a coverage percentage is NOT sufficient — every scenario must declare a covering test. Add `@covered-by:<test-path>` (optionally `::<TestName>`) directly above each uncovered `Scenario:`. Skip only when the slice has no scenarios (free-text acceptance must be promoted to scenarios first). When the covering tests are runnable in this checkout, prefer `--run` to require they actually PASS, not merely exist.

### Step 2g: Check for Product Context

**Skip if `--quick` as a separate judge-fanout step.** In quick mode, the same DX expectations are still loaded inline during review. In non-quick modes, add the dedicated `developer-experience` perspective.

```bash
if [ -f PRODUCT.md ]; then
  # PRODUCT.md exists — include developer-experience perspectives
fi
```

When `PRODUCT.md` exists in the project root AND the user did NOT pass an explicit `--preset` override:
1. Read `PRODUCT.md` content and include in the council packet via `context.files`
2. In `--quick` mode, keep the review inline and require the reviewer to assess api-clarity, error-experience, and discoverability directly from `PRODUCT.md`.
3. In non-quick modes, add a single consolidated `developer-experience` perspective to the council invocation:
   - **With spec:** `$council --preset=code-review --perspectives="developer-experience" validate <target>` (3 judges: 2 code-review + 1 DX)
   - **Without spec:** `$council --perspectives="developer-experience" validate <target>` (3 judges: 2 independent + 1 DX)
   The DX judge covers api-clarity, error-experience, and discoverability in a single review.
4. With `--deep`: adds 1 more judge per mode (4 judges total).

When `PRODUCT.md` exists BUT the user passed an explicit `--preset`: skip DX auto-include (user's explicit preset takes precedence).

When `PRODUCT.md` does not exist: proceed to Step 3 unchanged.

> **Tip:** Create `PRODUCT.md` from `docs/PRODUCT-TEMPLATE.md` to enable developer-experience-aware code review.

### Step 3: Load the Spec (New)

**Skip if `--quick` (see Step 1.5).**

Before invoking council, try to find the relevant spec/bead:

1. **If target looks like a bead ID** (e.g., `na-0042`): `bd show <id>` to get the spec
2. **Search for plan doc:** `ls .agents/plans/ | grep <target-keyword>`
3. **Check git log:** `git log --oneline | head -10` to find the relevant bead reference

If a spec is found, include it in the council packet's `context.spec` field:
```json
{
  "spec": {
    "source": "bead na-0042",
    "content": "<the spec/bead description text>"
  }
}
```

### Step 3.5: Load Suppressions

Before invoking council, load the default suppression list from `references/vibe-suppressions.md` and any project-level overrides from `.agents/vibe-suppressions.jsonl`. Suppressions are applied post-verdict to classify findings as CRITICAL vs INFORMATIONAL and to filter known false positives. See [references/vibe-suppressions.md](references/vibe-suppressions.md) for the full pattern list.

### Step 3.6: Load Pre-Mortem Predictions (Correlation)

When a pre-mortem report exists for the current epic, load prediction IDs for downstream correlation:

```bash
# Find the most recent pre-mortem report
PM_REPORT=$(ls -t .agents/council/*pre-mortem*.md 2>/dev/null | head -1)
if [ -n "$PM_REPORT" ]; then
  # Extract prediction IDs from frontmatter
  PREDICTION_IDS=$(sed -n '/^prediction_ids:/,/^[^ -]/p' "$PM_REPORT" | grep '^\s*-' | sed 's/^\s*- //')
fi
```

For each vibe finding, check if it matches a pre-mortem prediction:
- **Match found:** Tag finding with `predicted_by: pm-YYYYMMDD-NNN`
- **No match:** Tag finding with `predicted_by: none` (surprise issue)

Include the prediction correlation in the vibe report's findings table. This feeds the post-mortem's Prediction Accuracy section. Skip silently if no pre-mortem report exists.

### Step 4: Run Council Validation

**With spec found — use code-review preset:**
```
$council --preset=code-review validate <target>
```
- `error-paths`: Trace every error handling path. What's uncaught? What fails silently?
- `api-surface`: Review every public interface. Is the contract clear? Breaking changes?
- `spec-compliance`: Compare implementation against the spec. What's missing? What diverges?

The spec content is injected into the council packet context so the `spec-compliance` judge can compare implementation against it.

**Without spec — 2 independent judges (no perspectives):**
```
$council validate <target>
```
2 independent judges (no perspective labels). Use `--deep` for 3 judges on high-stakes reviews. Override with `--quick` (inline single-agent check) or `--mixed` (cross-vendor with Codex).

**Council receives:**
- Files to review
- Complexity hotspots (from Step 2)
- Git diff context
- Spec content (when found, in `context.spec`)
- Sweep manifest (when `--deep` or `--sweep`, in `context.sweep_manifest` — judges shift to adjudication mode, see `references/deep-audit-protocol.md`)

All council flags pass through: `--quick` (inline), `--mixed` (cross-vendor), `--preset=<name>` (override perspectives), `--explorers=N`, `--debate` (adversarial 2-round). See Quick Start examples and `$council` docs.

### Step 4.5: No-self-grading invariant (author ≠ validator)

The acceptance verdict must NOT be graded by the artifact's own author. A verdict produced by the authoring context is autocorrelated — the same blind spots that shipped the bug pass it. This is the no-self-grading invariant (`ag-lmdx.4`): the independent-trust-domain check that guards the `evidenced->validated` transition.

**Rule:** the judge context MUST be distinct from the author context. Validation MAY run inside the authoring session, but the judge MUST be a **blind sub-agent** — a fresh, context-isolated agent acting as if it has no authoring context. Record `judge_id` (the isolated sub-agent context) distinct from `author_id` (the authoring context). The council judges spawned in Step 4 satisfy this when they are context-isolated sub-agents; an inline self-review by the authoring agent does NOT.

**Blind sub-agent judge spawn (the mechanism, MANDATORY when validating in the authoring session):**

When the verdict is being produced inside the session that authored the code, you MUST spawn the acceptance judge as a fresh-context sub-agent — do NOT grade inline. Concretely:

1. Spawn the judge via the Codex sub-agent mechanism (the same context-isolated sub-agents Step 4's council uses). The sub-agent is the judge; the orchestrating authoring agent is NOT.
2. Hand the blind judge **ONLY** the acceptance inputs — never the authoring conversation, plan, or reasoning:
   - the **diff/artifact** under review (changed files + `git diff`),
   - the **acceptance scenarios** (the bead's `## Scenarios` block or the `.feature` file) and any spec, complexity hotspots, and domain checklists,
   - the verdict contract (`skills/council/schemas/verdict.json`).
   Do NOT pass the authoring transcript, intermediate design notes, or "here's why I think it's correct" framing. The judge acts as if it has no authoring context.
3. Use the sub-agent's PASS/WARN/FAIL as the acceptance verdict. Record `judge_id` = the isolated sub-agent context, `author_id` = the authoring context, into the turn-input consumed by `ao turn verify` (Enforcement below).

This is what makes same-session validation trustworthy: the verdict is produced by a context that did not author the artifact, so the author's blind spots do not pass it.

**Refuse** to emit a PASS verdict when the judge context equals the author context (`judge_id == author_id`) — i.e. when no blind sub-agent was spawned and the authoring agent graded itself. Re-run the verdict through a blind sub-agent judge instead.

**Escape:** `--allow-self` (default OFF) waives the invariant for the inline fallback only (e.g. no sub-agent runtime available). Using it stamps the verdict as self-graded; downstream `ao turn verify` reports it as waived, not independently validated.

**Enforcement:** `ao turn verify <bead>` evaluates the `author_neq_validator` predicate from the turn-input file's `author_id`/`judge_id` and fails the Evidenced-Turn DoD on a self-graded verdict unless `--allow-self` is passed. The `evidenced->validated` guard rejects a self-graded verdict.

### Step 5: Council Checks

Each judge reviews for:

| Aspect | What to Look For |
|--------|------------------|
| **Correctness** | Does code do what it claims? |
| **Security** | Injection, auth issues, secrets |
| **Edge Cases** | Null handling, boundaries, errors |
| **Quality** | Dead code, duplication, clarity |
| **Complexity** | High cyclomatic scores, deep nesting |
| **Architecture** | Coupling, abstractions, patterns |

### Step 6: Interpret Verdict

| Council Verdict | Vibe Result | Action |
|-----------------|-------------|--------|
| PASS | Ready to ship | Merge/deploy |
| WARN | Review concerns | Address or accept risk |
| FAIL | Not ready | Fix issues |

### Step 7: Write Vibe Report

**Write to:** `.agents/council/YYYY-MM-DD-vibe-<target>.md` (use `date +%Y-%m-%d`)

```markdown
---
id: council-YYYY-MM-DD-vibe-<target-slug>
type: council
date: YYYY-MM-DD
---

# Vibe Report: <Target>

**Files Reviewed:** <count>

## Complexity Analysis

**Status:** ✅ Completed | ⚠️ Skipped (<reason>)

| File | Score | Rating | Notes |
|------|-------|--------|-------|
| src/auth.py | 15 | C | Consider breaking up |
| src/utils.py | 4 | A | Good |

**Hotspots:** <list files with C or worse>
**Skipped reason:** <if skipped, explain why - e.g., "radon not installed">

## Council Verdict: PASS / WARN / FAIL

| Judge | Verdict | Key Finding |
|-------|---------|-------------|
| Error-Paths | ... | ... (with spec — code-review preset) |
| API-Surface | ... | ... (with spec — code-review preset) |
| Spec-Compliance | ... | ... (with spec — code-review preset) |
| Judge 1 | ... | ... (no spec — 2 independent judges) |
| Judge 2 | ... | ... (no spec — 2 independent judges) |
| Judge 3 | ... | ... (no spec — 2 independent judges) |

## Shared Findings
- ...

## CRITICAL Findings (blocks ship)
- ... (findings that indicate correctness, security, or data-safety issues)

## INFORMATIONAL Findings (include in PR body)
- ... (style suggestions, minor improvements, suppressed/downgraded items)

## Concerns Raised
- ...

## All Findings

> Included when `--deep` or `--sweep` produces a sweep manifest. Lists ALL findings
> from explorer sweep + council adjudication. Grouped by category if >20 findings.

| # | File | Line | Category | Severity | Description | Source |
|---|------|------|----------|----------|-------------|--------|
| 1 | ... | ... | ... | ... | ... | sweep / council |

## Recommendation
<council recommendation>

## Decision

[ ] SHIP - Complexity acceptable, council passed
[ ] FIX - Address concerns before shipping
[ ] REFACTOR - High complexity, needs rework
```

### Step 8: Report to User

Tell the user:
1. Complexity hotspots (if any)
2. Council verdict (PASS/WARN/FAIL)
3. Key concerns
4. Location of vibe report

For performance-sensitive code, run `$perf profile <target>` to identify optimization opportunities.

### Step 9: Record Ratchet Progress

After council verdict:
1. If verdict is PASS or WARN:
   - Run: `ao ratchet record vibe --output "<report-path>" 2>/dev/null || true`
   - Suggest: "Run $post-mortem to capture learnings and complete the cycle."
2. If verdict is FAIL:
   - Do NOT record ratchet progress.
   - Extract ALL findings from the council report for structured retry context (group by category if >20):
     ```
     Read the council report. For each finding, format as:
     FINDING: <description> | FIX: <fix or recommendation> | REF: <ref or location>

     Fallback for v1 findings (no fix/why/ref fields):
       fix = finding.fix || finding.recommendation || "No fix specified"
       ref = finding.ref || finding.location || "No reference"
     ```
   - Tell user to fix issues and re-run $vibe, including the formatted findings as actionable guidance.

### Step 9.5: Feed Findings to Flywheel

**If verdict is WARN or FAIL**, persist reusable findings to `.agents/findings/registry.jsonl` and optionally mirror the broader narrative to a learning file.

Registry write rules:

- persist only reusable issues that should change future review or implementation behavior
- require `dedup_key`, provenance, `pattern`, `detection_question`, `checklist_item`, `applicable_when`, and `confidence`
- `applicable_when` must use the controlled vocabulary from the finding-registry contract
- append or merge by `dedup_key`
- use the contract's temp-file-plus-rename atomic write rule

If a broader prose summary still helps, also write the existing anti-pattern learning file to `.agents/learnings/YYYY-MM-DD-vibe-<target>.md`. Skip both if verdict is PASS.

After the registry update, if `hooks/finding-compiler.sh` exists, run:

```bash
bash hooks/finding-compiler.sh --quiet 2>/dev/null || true
```

This keeps the same-session post-mortem path synchronized with the latest reusable findings. `session-end-maintenance.sh` remains the idempotent backstop.

### Step 10: Test Bead Cleanup

After validation completes, clean up stale test beads (`bd list --status=open | grep -iE "test bead|test quest"`) via `bd close` to prevent bead pollution. Skip if `bd` unavailable.

---

## Integration with Workflow

```
$implement issue-123
    │
    ▼
(coding, quick lint/test as you go)
    │
    ▼
$vibe                      ← You are here
    │
    ├── Complexity analysis (find hotspots)
    ├── Bug hunt audit (find concrete bugs)
    └── Council validation (multi-model judgment)
    │
    ├── PASS → ship it
    ├── WARN → review, then ship or fix
    └── FAIL → fix, re-run $vibe
```

---

## Examples

**User says:** "Run a quick validation on the latest changes."

**Do:**
```bash
$vibe recent
```

### Validate Recent Changes

```bash
$vibe recent
```

Runs complexity on recent changes, then council reviews.

### Validate Specific Directory

```bash
$vibe src/auth/
```

Complexity + council on auth directory.

### Deep Review

```bash
$vibe --deep recent
```

Complexity + 3 judges for thorough review.

### Cross-Vendor Consensus

```bash
$vibe --mixed recent
```

Complexity + Claude + Codex judges.

See `references/examples.md` for additional examples: security audit with spec compliance, developer-experience code review with PRODUCT.md, and fast inline checks.

---

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| "COMPLEXITY SKIPPED: radon not installed" | Python complexity analyzer missing | Install with `pip install radon` or skip complexity (council still runs). |
| "COMPLEXITY SKIPPED: gocyclo not installed" | Go complexity analyzer missing | Install with `go install github.com/fzipp/gocyclo/cmd/gocyclo@latest` or skip. |
| Vibe returns PASS but constraint tests fail | Council LLMs miss mechanical violations | Check `.agents/council/<timestamp>-vibe-*.md` for constraint test results. Failed constraints override council PASS. Fix violations and re-run. |
| Codex review skipped | `--mixed` not passed, Codex CLI not on PATH, or no uncommitted changes | Codex review is opt-in — pass `--mixed` to enable. Also requires Codex CLI on PATH and uncommitted changes. |
| "No modified files detected" | Clean working tree, no recent commits | Make changes or specify target path explicitly: `$vibe src/auth/`. |
| Spec-compliance judge not spawned | No spec found in beads/plans | Reference bead ID in commit message or create plan doc in `.agents/plans/`. Without spec, vibe uses 2 independent judges (3 with `--deep`). |

---

## See Also

- `../council/SKILL.md` — Multi-model validation council
- `../complexity/SKILL.md` — Standalone complexity analysis
- `../bug-hunt/SKILL.md` — Proactive code audit and bug investigation
- [test](../test/SKILL.md) — Test generation and coverage analysis
- [perf](../perf/SKILL.md) — Performance profiling and benchmarking
- `.agents/specs/conflict-resolution-algorithm.md` — Conflict resolution between agent findings

## Reference Documents

- [references/verification-report.md](references/verification-report.md)
- [references/write-time-quality.md](references/write-time-quality.md)
- [references/deep-audit-protocol.md](references/deep-audit-protocol.md)
- [references/examples.md](references/examples.md)
- [references/go-patterns.md](references/go-patterns.md)
- [references/go-standards.md](references/go-standards.md)
- [references/json-standards.md](references/json-standards.md)
- [references/markdown-standards.md](references/markdown-standards.md)
- [references/patterns.md](references/patterns.md)
- [references/python-standards.md](references/python-standards.md)
- [references/report-format.md](references/report-format.md)
- [references/rust-standards.md](references/rust-standards.md)
- [references/shell-standards.md](references/shell-standards.md)
- [references/typescript-standards.md](references/typescript-standards.md)
- [references/vibe-coding.md](references/vibe-coding.md)
- [references/test-pyramid-weighting.md](references/test-pyramid-weighting.md)
- [references/vibe-suppressions.md](references/vibe-suppressions.md)
- [references/yaml-standards.md](references/yaml-standards.md)

## Local Resources

### references/

- [references/deep-audit-protocol.md](references/deep-audit-protocol.md)
- [references/examples.md](references/examples.md)
- [references/go-patterns.md](references/go-patterns.md)
- [references/go-standards.md](references/go-standards.md)
- [references/json-standards.md](references/json-standards.md)
- [references/markdown-standards.md](references/markdown-standards.md)
- [references/patterns.md](references/patterns.md)
- [references/python-standards.md](references/python-standards.md)
- [references/report-format.md](references/report-format.md)
- [references/rust-standards.md](references/rust-standards.md)
- [references/shell-standards.md](references/shell-standards.md)
- [references/typescript-standards.md](references/typescript-standards.md)
- [references/vibe-coding.md](references/vibe-coding.md)
- [references/test-pyramid-weighting.md](references/test-pyramid-weighting.md)
- [references/vibe-suppressions.md](references/vibe-suppressions.md)
- [references/yaml-standards.md](references/yaml-standards.md)

### scripts/

- `scripts/prescan.sh`
- `scripts/validate.sh`
