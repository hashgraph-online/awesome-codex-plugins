---
name: vibe
description: 'Validate code readiness. Use when: doing a quick readiness or sanity check that code is ready to commit or ship, short of a full review.'
practices:
- ai-assisted-dev
- llm-eval-harness
- code-complete
- pragmatic-programmer
hexagonal_role: domain
consumes:
- standards
produces:
- result.json
- verdict.json
context_rel:
- kind: shared-kernel
  with: standards
skill_api_version: 1
metadata:
  tier: judgment
  dependencies:
  - council
  - complexity
  - bug-hunt
  - standards
context:
  window: fork
  intent:
    mode: task
  sections:
    exclude:
    - HISTORY
  intel_scope: full
output_contract: skills/council/schemas/verdict.json
---
# Vibe Skill

> **Purpose:** Is this code ready to ship?

## Loop position

Per-slice quality gate within move **6 (close the bead by proving acceptance)** of the [operating loop](../../../docs/architecture/operating-loop.md). Consumes a slice's changes; produces PASS/WARN/FAIL on complexity, architecture, security, intent fit. Vibe answers "is this slice ready to be counted against the [slice-validation roll-up](../../../docs/templates/slice-validation.md)?" — it is not a substitute for the slice's first failing test (the test proves behavior; vibe judges the code that gets there).

Three steps:
1. **Complexity analysis** — Find hotspots (radon, gocyclo)
2. **Bug hunt audit** — Systematic sweep for concrete bugs
3. **Council validation** — Multi-model judgment

---

## Quick Start

```bash
/vibe                                    # validates recent changes
/vibe recent                             # same as above
/vibe src/auth/                          # validates specific path
/vibe --quick recent                     # fast inline check, no agent spawning
/vibe --structured recent                # 6-phase verification report (build→types→lint→tests→security→diff)
/vibe --deep recent                      # 3 judges instead of 2
/vibe --sweep recent                     # deep audit: per-file explorers + council
/vibe --mixed recent                     # cross-vendor (Claude + Codex)
/vibe --preset=security-audit src/auth/  # security-focused review
/vibe --explorers=2 recent               # judges with explorer sub-agents
/vibe --debate recent                    # two-round adversarial review
/vibe --tier=quality recent              # use quality tier for council calls
```

---

## Execution Steps

### Step 0: Load Prior Review Context

Before reviewing, pull relevant learnings from prior code reviews and known patterns:

```bash
if command -v ao &>/dev/null; then
    ao lookup --query "<target-scope> code review patterns" --limit 3 2>/dev/null || true
fi
```

**Apply retrieved knowledge (mandatory when results returned):**

If learnings or patterns are returned, do NOT just load them as passive context. For each returned item:
1. Check: does this learning apply to the code under review? (answer yes/no)
2. If yes: include it as a `known_risk` in your review — state the pattern, what to look for, and whether the code exhibits it
3. Cite the learning by filename in your review output when it influences a finding

After applying, record the citation:
```bash
ao metrics cite "<learning-path>" --type applied 2>/dev/null || true
```

Skip silently if ao is unavailable or returns no results.

**Project reviewer config:** If `.agents/reviewer-config.md` exists, its full config (`reviewers`, `plan_reviewers`, `skip_reviewers`) is passed to council for judge selection. See `skills/council/SKILL.md` Step 1b.

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

### Step 1.5a: Structured Verification Path (--structured mode)

**If `--structured` flag is set**, run a 6-phase mechanical verification pipeline instead of the council flow. This produces a machine-readable verification report suitable for PR gates and CI integration.

Phases: Build → Types → Lint → Tests → Security → Diff Review.

Read `references/verification-report.md` for the full report template and per-phase commands. Each phase is fail-fast — if Build fails, skip remaining phases and report NOT READY.

After all phases complete, write the structured report to `.agents/council/YYYY-MM-DD-verification-<target>.md` and output the summary table to the user.

**When to use:** Pre-PR gate, CI integration, when you need a mechanical pass/fail rather than judgment-based review.

### Step 1.5: Fast Path (--quick mode)

**If `--quick` flag is set**, skip Steps 2a through 2e as heavy pre-processing, plus 2.5 and 2f, and jump to Step 4 with inline council after Steps 2.3, 2.4, 2g, and Step 3. Domain checklists, compiled-prevention loading, test-pyramid inventory, and inline product context are cheap and high-value, so they still run in quick mode. Complexity analysis (Step 2) still runs — it's cheap and informative.

**Why:** Steps 2.5 and 2a–2f add 30–90 seconds of pre-processing that mainly feed multi-judge council packets. In --quick mode (single inline agent), those inputs are not worth the cost, but test-pyramid and product-context checks still shape the inline review meaningfully.

### Step 2: Run Complexity Analysis

Read [references/complexity-analysis.md](./complexity-analysis.md) when you need the language-detection preflight, per-language analyzer commands (radon/gocyclo), and the score interpretation table. Filter by language present in the diff before running any analyzer.

### Step 2.3: Load Domain-Specific Checklists

Detect code patterns in the target files and load matching domain-specific checklists from `standards/references/`:

| Trigger | Checklist | Detection |
|---------|-----------|-----------|
| SQL/ORM code | `sql-safety-checklist.md` | Files contain SQL queries, ORM imports (`database/sql`, `sqlalchemy`, `prisma`, `activerecord`, `gorm`, `knex`), or migration files in changeset |
| LLM/AI code | `llm-trust-boundary-checklist.md` | Files import `anthropic`, `openai`, `google.generativeai`, or match `*llm*`, `*prompt*`, `*completion*` patterns |
| Concurrent code | `race-condition-checklist.md` | Files use goroutines, `threading`, `asyncio`, `multiprocessing`, `sync.Mutex`, `concurrent.futures`, or shared file I/O patterns |
| Codex skills | `codex-skill.md` | Files under `skills-codex/`, or files matching `*codex*SKILL.md`, `convert.sh`, `skills-codex-overrides/`, or converter scripts |

For each matched checklist, load it via the Read tool and include relevant items in the council packet as `context.domain_checklists`. Multiple checklists can be loaded simultaneously.

Skip silently if no patterns match. This step runs in both `--quick` and full modes (domain checklists are cheap to load and high-value).

**Steps 2.4-2f, 2h, 3-3.6 (Deep Checks & Pre-Council Prep):** Read `references/deep-checks.md` for compiled prevention, prior findings, pre-council deep analysis checks, product context, spec loading, suppressions, pre-mortem correlation, and model cost tiers. Loaded automatically unless `--quick` mode is set. In `--quick` mode, skip directly to Step 2g.

**Compiled prevention inputs:** Load `.agents/pre-mortem-checks/` and `.agents/planning-rules/` when available. These compiled artifacts contain known_risks from prior findings that inform the review — carry matched finding IDs into council context so judges can assess whether the flywheel prevented rediscovery.

### Step 2a: Prior Findings Check

**Skip if `--quick`.** Load prior findings from `.agents/findings/registry.jsonl`.

### Step 2b: Constraint Tests

**Skip if `--quick`.** Run compiled constraint tests from `.agents/constraints/`.

### Step 2c: Metadata Checks

**Skip if `--quick`.** Verify file metadata consistency.

### Step 2.5: OL Validation

**Skip if `--quick`.** Run organizational-lint checks.

### Step 2d: Knowledge Search

**Skip if `--quick`.** Search for relevant prior learnings via `ao lookup`.

### Step 2e: Bug Hunt or Deep Audit Sweep

**Skip if `--quick`.**

**Path A — Deep Audit Sweep (`--deep` or `--sweep`):**

Read `references/deep-audit-protocol.md` for the full protocol. In summary:

1. Chunk target files into batches of 3-5 by line count
2. Dispatch up to 8 Explore agents in parallel, each with a mandatory 8-category checklist per file
3. Merge all explorer findings into a sweep manifest at `.agents/council/sweep-manifest.md`
4. Include sweep manifest in the council packet so judges shift to adjudication mode

**Why:** Generalist judges exhibit satisfaction bias — they stop after a small number of findings regardless of actual issue count. Per-file explorers with category checklists reduce that bias and surface concrete line-level issues before council adjudication.

**Path B — Lightweight Bug Hunt (default, no `--deep`/`--sweep`):**

Run proactive bug-hunt audit on target files.

### Step 2f: Codex Review

**Skip if `--quick`.** When `--mixed` is passed and Codex CLI is available, send the first 2000 chars of the diff to Codex for a parallel review. Cap input at 2000 chars to stay within Codex context budgets.

### Step 3: Product Context

**Skip if `--quick` as a separate judge-fanout step.** When `PRODUCT.md` exists and the user did not pass an explicit `--preset` override, quick mode still loads DX expectations inline in the single-agent review. In non-quick modes, add a DX (developer experience) judge: 2 independent + 1 DX judge (3 judges total). The DX judge evaluates whether the code aligns with the product's stated personas and value propositions.

### Step 2g: Test Pyramid Inventory (MANDATORY)

Read [references/test-pyramid-inventory.md](./test-pyramid-inventory.md) when you need the full inventory procedure: per-module L0–L3 coverage checks, BF1–BF5 boundary checks, the `weighted_score` formula, satisfaction-score exposure, the council-packet `test_pyramid` JSON shape, and verdict rules. Runs in both `--quick` and full modes — file existence checks are cheap. Weight L0–L1 at 1x, L2 at 3x, L3+ at 5x; `weighted_score < 0.3` with L0–L1 only is a WARN.

### Step 2g.1: Scenario→Test Coverage (MANDATORY when the slice has scenarios)

Test-pyramid inventory (2g) checks that tests *exist* and are well-shaped — it does NOT check that each of the slice's acceptance scenarios maps to a test. The leaf gate for that is `scripts/check-bead-scenario-coverage.sh` (C2, ag-9jle.4). It parses the bead's `## Scenarios` block (or a `.feature` file) and FAILS if any scenario lacks a `@covered-by:<test-path>` link — i.e. it works *forward from behavior*, not backward from coverage %.

```bash
# When validating a tracked bead with a ## Scenarios block:
# (--bead fetches the body via `br show`; BEADS_DIR defaults to <repo>/_beads — bd is retired)
bash scripts/check-bead-scenario-coverage.sh --bead <bead-id> --json

# When validating a .feature directly:
bash scripts/check-bead-scenario-coverage.sh skills/<skill>/references/<name>.feature --json
```

A FAIL here is a vibe blocker, not a WARN: "tests exist" or a coverage percentage is NOT sufficient — every scenario must declare a covering test. Add `@covered-by:<test-path>` (optionally `::<TestName>`) directly above each uncovered `Scenario:`. Skip only when the slice has no scenarios (free-text acceptance must be promoted to scenarios first — see the workflow contract). When the covering tests are runnable in this checkout, prefer `--run` to require they actually PASS, not merely exist.

### Step 4: Run Council Validation

**With spec found — use code-review preset:**
```
/council --preset=code-review validate <target>
```
- `error-paths`: Trace every error handling path. What's uncaught? What fails silently?
- `api-surface`: Review every public interface. Is the contract clear? Breaking changes?
- `spec-compliance`: Compare implementation against the spec. What's missing? What diverges?

The spec content is injected into the council packet context so the `spec-compliance` judge can compare implementation against it.

**Without spec — 2 independent judges (no perspectives):**
```
/council validate <target>
```
2 independent judges (no perspective labels). Use `--deep` for 3 judges on high-stakes reviews. Override with `--quick` (inline single-agent check) or `--mixed` (cross-vendor with Codex).

**Council receives:**
- Files to review
- Complexity hotspots (from Step 2)
- Git diff context
- Spec content (when found, in `context.spec`)
- Sweep manifest (when `--deep` or `--sweep`, in `context.sweep_manifest` — judges shift to adjudication mode, see `references/deep-audit-protocol.md`)

All council flags pass through: `--quick` (inline), `--mixed` (cross-vendor), `--preset=<name>` (override perspectives), `--explorers=N`, `--debate` (adversarial 2-round), `--tier=<name>` (model cost tier: quality/balanced/budget). See Quick Start examples and `/council` docs.

### Step 4.5: No-self-grading invariant (author ≠ validator)

The acceptance verdict must NOT be graded by the artifact's own author. A verdict produced by the authoring context is autocorrelated — the same blind spots that shipped the bug pass it. This is the no-self-grading invariant (`ag-lmdx.4`): the independent-trust-domain check that guards the `evidenced->validated` transition.

**Rule:** the judge context MUST be distinct from the author context. Validation MAY run inside the authoring session, but the judge MUST be a **blind sub-agent** — a fresh, context-isolated agent acting as if it has no authoring context. Record `judge_id` (the isolated sub-agent context) distinct from `author_id` (the authoring context). The council judges spawned in Step 4 satisfy this when they are context-isolated sub-agents; an inline self-review by the authoring agent does NOT.

**Blind sub-agent judge spawn (the mechanism, MANDATORY when validating in the authoring session):**

When the verdict is being produced inside the session that authored the code, you MUST spawn the acceptance judge as a fresh-context sub-agent — do NOT grade inline. Concretely:

1. Spawn the judge via the `Agent`/`Task` tool (the same context-isolated sub-agents Step 4's council uses). The sub-agent is the judge; the orchestrating authoring agent is NOT.
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

## Council Verdict:

| Council Verdict | Vibe Result | Action |
|-----------------|-------------|--------|
| PASS | Ready to ship | Merge/deploy |
| WARN | Review concerns | Address or accept risk |
| FAIL | Not ready | Fix issues |

### Step 7: Write Vibe Report

**Write to:** `.agents/council/YYYY-MM-DD-vibe-<target>.md` (use `date +%Y-%m-%d`)

Read `references/report-format.md` for the full vibe report markdown template. The report includes: complexity analysis, council verdict table, shared/critical/informational findings, all findings (when `--deep`/`--sweep`), recommendation, and decision checkboxes.

### Step 8: Report to User

Tell the user:
1. Complexity hotspots (if any)
2. Council verdict (PASS/WARN/FAIL)
3. Key concerns
4. Location of vibe report

### Step 9: Record Ratchet Progress & Step 9.5: Feed Findings to Flywheel

Read [references/post-verdict-actions.md](./post-verdict-actions.md) when you need the PASS/WARN/FAIL ratchet recording rules, the failure-retry finding extraction format, and the `.agents/findings/registry.jsonl` write contract (dedup_key, applicable_when vocabulary, atomic-rename rule) plus the `hooks/finding-compiler.sh` follow-up.

### Step 10: Test Bead Cleanup

After validation completes, clean up stale test beads (`bd list --status=open | grep -iE "test bead|test quest"`) via `bd close` to prevent bead pollution. Skip if `bd` unavailable.

---

## Integration with Workflow

```
/implement issue-123
    │
    ▼
(coding, quick lint/test as you go)
    │
    ▼
/vibe                      ← You are here
    │
    ├── Complexity analysis (find hotspots)
    ├── Bug hunt audit (find concrete bugs)
    └── Council validation (multi-model judgment)
    │
    ├── PASS → ship it
    ├── WARN → review, then ship or fix
    └── FAIL → fix, re-run /vibe
```

---

## Examples

**User says:** "Run a quick validation on the latest changes."

**Do:**
```bash
/vibe recent
```

### Validate Recent Changes

```bash
/vibe recent
```

Runs complexity on recent changes, then council reviews.

### Validate Specific Directory

```bash
/vibe src/auth/
```

Complexity + council on auth directory.

### Deep Review

```bash
/vibe --deep recent
```

Complexity + 3 judges for thorough review.

### Cross-Vendor Consensus

```bash
/vibe --mixed recent
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
| "No modified files detected" | Clean working tree, no recent commits | Make changes or specify target path explicitly: `/vibe src/auth/`. |
| Spec-compliance judge not spawned | No spec found in beads/plans | Reference bead ID in commit message or create plan doc in `.agents/plans/`. Without spec, vibe uses 2 independent judges (3 with `--deep`). |

---

## Write-Time Quality Hook

The `hooks/write-time-quality.sh` PostToolUse hook runs automatically after every Write/Edit tool call, catching common anti-patterns at edit time rather than review time. It checks:

- **Go:** unchecked errors, `fmt.Print` in library code
- **Python:** bare `except:`, `eval`/`exec`, missing type hints on public functions
- **Shell:** missing `set -euo pipefail`, unquoted variables

The hook is non-blocking (always exits 0) and outputs warnings via JSON. See [references/write-time-quality.md](./write-time-quality.md) for the full design.

## See Also

- `skills/council/SKILL.md` — Multi-model validation council
- `skills/complexity/SKILL.md` — Standalone complexity analysis
- `skills/bug-hunt/SKILL.md` — Proactive code audit and bug investigation
- `.agents/specs/conflict-resolution-algorithm.md` — Conflict resolution between agent findings
- [test](../../test/SKILL.md) — Test generation and coverage analysis
- [perf](../../perf/SKILL.md) — Performance profiling and benchmarking

## Reference Documents

- [references/vibe.feature](./vibe.feature) — Executable spec: council verdict (complexity/architecture/security/intent-fit), block-on-CRITICAL, verdict.json (soc-qk4b)
- [references/complexity-analysis.md](./complexity-analysis.md)
- [references/deep-checks.md](./deep-checks.md)
- [references/post-verdict-actions.md](./post-verdict-actions.md)
- [references/test-pyramid-inventory.md](./test-pyramid-inventory.md)
- [references/verification-report.md](./verification-report.md)
- [references/write-time-quality.md](./write-time-quality.md)
- [references/deep-audit-protocol.md](./deep-audit-protocol.md)
- [references/examples.md](./examples.md)
- [references/go-patterns.md](./go-patterns.md)
- [references/go-standards.md](./go-standards.md)
- [references/json-standards.md](./json-standards.md)
- [references/markdown-standards.md](./markdown-standards.md)
- [references/patterns.md](./patterns.md)
- [references/python-standards.md](./python-standards.md)
- [references/report-format.md](./report-format.md)
- [references/rust-standards.md](./rust-standards.md)
- [references/shell-standards.md](./shell-standards.md)
- [references/typescript-standards.md](./typescript-standards.md)
- [references/vibe-coding.md](./vibe-coding.md)
- [references/vibe-suppressions.md](./vibe-suppressions.md)
- [references/test-pyramid-weighting.md](./test-pyramid-weighting.md)
- [references/yaml-standards.md](./yaml-standards.md)
