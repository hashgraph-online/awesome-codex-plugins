# Deep Checks (Steps 2.5, 2a–2f, 2h, 3–3.6)

> **Extracted from:** `skills/validate/SKILL.md`.
> These are the pre-council deep analysis and preparation checks. Loaded automatically unless `--quick` mode is set.

---

### Step 2.4: Compiled Prevention Check

Before reading `.agents/rpi/next-work.jsonl`, load compiled prevention context from `.agents/pre-mortem-checks/*.md` and `.agents/planning-rules/*.md` when they exist. This is the primary reusable-prevention surface for review.

Use the tracked contracts in `docs/contracts/finding-compiler.md` and `docs/contracts/finding-registry.md`:

- prefer compiled pre-mortem checks and planning rules first
- rank by severity, `applicable_when` overlap, language overlap, changed-file overlap, and literal target-text overlap
- keep the ranking order consistent with `/plan` and `/pre-mortem`; do not invent a separate review-only heuristic
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
If ao returns prior code review patterns for this area, include them in the council packet context. Skip silently if ao is unavailable or returns no results.

### Step 2f: Bug Hunt or Deep Audit Sweep

**Skip if `--quick` (see Step 1.5).**

**Path A — Deep Audit Sweep (`--deep` or `--sweep`):**

Read `references/deep-audit-protocol.md` for the full protocol. In summary:

1. Chunk target files into batches of 3–5 (by line count — see protocol for rules)
2. Dispatch up to 8 Explore agents in parallel, each with a mandatory 8-category checklist per file
3. Merge all explorer findings into a sweep manifest at `.agents/council/sweep-manifest.md`
4. Include sweep manifest in council packet (judges shift to adjudication mode — see Step 4)

**Why:** Generalist judges exhibit satisfaction bias — they stop at ~10 findings regardless of actual issue count. Per-file explorers with category checklists eliminate this bias and find 3x more issues in a single pass.

**Path B — Lightweight Bug Hunt (default, no `--deep`/`--sweep`):**

Run a proactive bug hunt on the target files before council review:

```
/bug-hunt --audit <target>
```

If bug-hunt produces findings, include them in the council packet as `context.bug_hunt`:
```json
"bug_hunt": {
  "source": "/bug-hunt --audit",
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

### Step 2h: Check for Product Context

**Skip if `--quick` (see Step 1.5).**

```bash
if [ -f PRODUCT.md ]; then
  # PRODUCT.md exists — include developer-experience perspectives
fi
```

When `PRODUCT.md` exists in the project root AND the user did NOT pass an explicit `--preset` override:
1. Read `PRODUCT.md` content and include in the council packet via `context.files`
2. Add a single consolidated `developer-experience` perspective to the council invocation:
   - **With spec:** `/council --preset=code-review --perspectives="developer-experience" validate <target>` (3 judges: 2 code-review + 1 DX)
   - **Without spec:** `/council --perspectives="developer-experience" validate <target>` (3 judges: 2 independent + 1 DX)
   The DX judge covers api-clarity, error-experience, and discoverability in a single review.
3. With `--deep`: adds 1 more judge per mode (4 judges total).

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

Before invoking council, load the default suppression list from `references/vibe-suppressions.md` and any project-level overrides from `.agents/vibe-suppressions.jsonl`. Suppressions are applied post-verdict to classify findings as CRITICAL vs INFORMATIONAL and to filter known false positives. See [references/vibe-suppressions.md](vibe-suppressions.md) for the full pattern list.

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

### Model Cost Tiers

Vibe passes the model cost tier through to council for all validation calls. Tier resolution:

1. Explicit `--tier=<name>` flag on `/vibe`
2. Skill-specific config: `models.skill_overrides.vibe` in `.agentops/config.yaml`
3. Global default: `models.default_tier` in `.agentops/config.yaml`
4. Built-in default: `balanced`

```yaml
# Example: force quality tier for all vibe reviews
models:
  skill_overrides:
    vibe: quality
```
