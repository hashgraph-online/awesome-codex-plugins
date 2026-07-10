# Post-Mortem Maintenance Phases (3-6)

> **Extracted from:** `skills/post-mortem/SKILL.md`
> These phases handle backlog processing, activation, retirement, and harvesting.
> They run after council validation (Phase 1) and learning extraction (Phase 2).
> Load when `--process-only` flag is set or when running a full post-mortem.

---

### Phase 3: Process Backlog

Score, deduplicate, and flag stale learnings across the full backlog. This phase runs on ALL learnings, not just those extracted in Phase 2.

Read `references/backlog-processing.md` for detailed scoring formulas, deduplication logic, and staleness criteria.

#### Step BP.1: Load Last-Processed Marker

```bash
MARKER=".agents/ao/last-processed"
mkdir -p .agents/ao
if [ ! -f "$MARKER" ]; then
  date -v-30d +%Y-%m-%dT%H:%M:%S 2>/dev/null || date -d "30 days ago" --iso-8601=seconds > "$MARKER"
fi
LAST_PROCESSED=$(cat "$MARKER")
```

#### Step BP.2: Scan Unprocessed Learnings

```bash
find .agents/learnings/ -name "*.md" -newer "$MARKER" -not -path "*/archive/*" -type f | sort
```

If zero files found: report "Backlog empty — no unprocessed learnings" and skip to Phase 4.

#### Step BP.3: Deduplicate

For each pair of unprocessed learnings:
1. Extract `# Learning:` title
2. Normalize: lowercase, strip punctuation, collapse whitespace
3. If two normalized titles share >= 80% word overlap, merge:
   - Keep the file with highest confidence (high > medium > low); if tied, keep most recent
   - Archive the duplicate with a `merged_into:` pointer

#### Step BP.4: Score Each Learning

Compute composite score for each learning:

| Factor | Values | Points |
|--------|--------|--------|
| Confidence | high=3, medium=2, low=1 | 1-3 |
| Citations | default=1, +1 per cite in `.agents/ao/citations.jsonl` | 1+ |
| Recency | <7d=3, <30d=2, else=1 | 1-3 |

**Score = confidence + citations + recency**

#### Step BP.5: Flag Stale

Learnings that are >30 days old AND have zero citations are flagged for retirement in Phase 5.

```bash
# Flag but do not archive yet — Phase 5 handles retirement
if [ "$DAYS_OLD" -gt 30 ] && [ "$CITE_COUNT" -eq 0 ]; then
  echo "STALE: $LEARNING_FILE (${DAYS_OLD}d old, 0 citations)"
fi
```

#### Step BP.6: Report

```
Phase 3 (Process Backlog) Summary:
- N learnings scanned
- N duplicates merged
- N scored (range: X-Y)
- N flagged stale
```

#### Step BP.7: Two-Strikes Membrane Triage

The backlog is where recurring **catches** ratchet, not just learnings. Run the
membrane triage over the catch corpus:

```bash
ao membrane triage
```

For any class with **HitCount >= 2**, route it by the class's **nature**, NOT
gate-first ([ADR-0014](../../../docs/adr/ADR-0014-catch-to-producer-loop-judgment-catches-need-a-producer-route.md)).
`ao membrane triage` reports `Axis2Compilable ≈ 0` — recurring catches are almost
all **judgment-class**, so a gate is the exception, not the goal:

- **Compilable** (rare): open a compile bead for a mechanical gate (Loop B).
- **Judgment-class** (the common case): bind a **producer-side fix** — a rule in the
  owning skill's standards, a `CLAUDE.md`/`AGENTS-*.md` footgun, a `/plan`
  planning-rule, or a `/discovery` pre-mortem check. For a judgment defect this **is**
  the highest feasible binding, not a fallback. **When a gate/adversary CAUGHT a defect
  a green test missed, also append the dimension to `docs/gate/findings-ledger.md`** —
  the ledger `behavior-first-planning` reads to ratchet its Standing Review Dimensions,
  so the catch closes back into the NEXT loop's planning (S6). Then add a row to the
  **[producer-defect register](../../../docs/architecture/producer-defect-register.md)**:
  the class, the fix + surface, and the recurrence count now (the "before").

The two-strikes rule (once → handoff; repeats → promote; must-never-regress → gate,
for the compilable case) is the admission bar. The **measurement** is the register's
recurrence-before-vs-after: run `ao membrane digest --deltas --since <fix-date>` (the
fix's land date, e.g. `git show -s --format=%cI <sha>`) — it prints each class's
`before=N since=M`, auto-derived from the catch corpus — and record the numbers in the
register's "before → after" column. A class that recurs after its fix (`since > 0`)
means the binding was too weak, so escalate it. Also classify a batch of the
**unclassified-catch floor** each run — that floor is the register's fuel.

> **Honest scope:** this route does not claim a compounding moat (ADR-0004/0011 remain
> unproven, and we do not market ahead of them). It claims exactly one falsifiable
> thing — after a producer fix binds for class X, X should be caught *less*. The
> register makes that checkable.

### Phase 4: Activate

Promote high-value learnings and feed downstream systems. Read `references/activation-policy.md` for detailed promotion thresholds and procedures.

**If `--skip-activate` is set:** Skip this phase entirely. Report "Phase 4 skipped (--skip-activate)."

#### Step ACT.1: Promote to MEMORY.md

Learnings with score >= 6 are promoted:
1. Read the learning file
2. Extract title and core insight
3. Check MEMORY.md for duplicate entries (grep for key phrases)
4. If no duplicate: append to `## Key Lessons` in MEMORY.md

```markdown
## Key Lessons
- **<Title>** — <one-line insight> (source: `.agents/learnings/<filename>`)
```

**Important:** Append only. Never overwrite MEMORY.md.

#### Step ACT.2: Re-Run the Finding Compiler Idempotently

If registry rows changed during this post-mortem, rerun the compiler before feeding next-work so downstream sessions read the freshest compiled prevention outputs:

```bash
bash hooks/finding-compiler.sh --quiet 2>/dev/null || true
```

#### Step ACT.3: Feed Next-Work

Actionable improvements identified during processing -> append one schema v1.4
batch entry to `.agents/rpi/next-work.jsonl` using the tracked contract in
[`../../docs/contracts/next-work.schema.md`](../../../docs/contracts/next-work.schema.md)
and the write procedure in
[`references/harvest-next-work.md`](harvest-next-work.md):

```bash
mkdir -p .agents/rpi
# Build VALID_ITEMS via the schema-validation flow in references/harvest-next-work.md
# Then append one entry per post-mortem / epic.
ENTRY_TIMESTAMP="$(date -Iseconds)"
SOURCE_EPIC="${EPIC_ID:-recent}"
VALID_ITEMS_JSON="${VALID_ITEMS_JSON:-[]}"

printf '%s\n' "$(jq -cn \
  --arg source_epic "$SOURCE_EPIC" \
  --arg timestamp "$ENTRY_TIMESTAMP" \
  --argjson items "$VALID_ITEMS_JSON" \
  '{
    source_epic: $source_epic,
    timestamp: $timestamp,
    items: $items,
    consumed: false,
    claim_status: "available",
    claimed_by: null,
    claimed_at: null,
    consumed_by: null,
    consumed_at: null
  }'
)" >> .agents/rpi/next-work.jsonl
```

#### Step ACT.4: Update Marker

```bash
date -Iseconds > .agents/ao/last-processed
```

This must be the LAST action in Phase 4.

#### Step ACT.5: Report

```
Phase 4 (Activate) Summary:
- N promoted to MEMORY.md
- N duplicates merged
- N flagged for retirement
- N constraints compiled
- N improvements fed to next-work.jsonl
```

### Phase 5: Retire Stale

Archive learnings that are no longer earning their keep.

#### Step RET.1: Archive Stale Learnings

Learnings flagged in Phase 3 (>30d old, zero citations):

```bash
mkdir -p .agents/learnings/archive
for f in <stale-files>; do
  mv "$f" .agents/learnings/archive/
  echo "Archived: $f (stale: >30d, 0 citations)"
done
```

#### Step RET.2: Archive Superseded Learnings

Learnings merged during Phase 3 deduplication were already archived with `merged_into:` pointers. Verify the pointers are valid:

```bash
for f in .agents/learnings/archive/*.md; do
  [ -f "$f" ] || continue
  MERGED_INTO=$(grep "^merged_into:" "$f" 2>/dev/null | awk '{print $2}')
  if [ -n "$MERGED_INTO" ] && [ ! -f "$MERGED_INTO" ]; then
    echo "WARN: $f points to missing file: $MERGED_INTO"
  fi
done
```

#### Step RET.3: Clean MEMORY.md References

If any archived learning was previously promoted to MEMORY.md, remove those entries:

```bash
for f in <archived-files>; do
  BASENAME=$(basename "$f")
  # Check if MEMORY.md references this file
  if grep -q "$BASENAME" MEMORY.md 2>/dev/null; then
    echo "WARN: MEMORY.md references archived learning: $BASENAME — consider removing"
  fi
done
```

**Note:** Do not auto-delete MEMORY.md entries. WARN the user and let them decide.

#### Step RET.4: Report

```
Phase 5 (Retire) Summary:
- N stale learnings archived
- N superseded learnings archived
- N MEMORY.md references to review
```

### Step 4: Write Post-Mortem Report

**Write to:** `.agents/council/YYYY-MM-DD-post-mortem-<topic>.md`

```markdown
---
id: post-mortem-YYYY-MM-DD-<topic-slug>
type: post-mortem
date: YYYY-MM-DD
source: "[[.agents/plans/YYYY-MM-DD-<plan-slug>]]"
---

# Post-Mortem: <Epic/Topic>

**Epic:** <epic-id or "recent">
**Duration:** <elapsed time from PM_START to now>
**Cycle-Time Trend:** <compare against prior post-mortems — is this faster or slower? Check .agents/council/ for prior post-mortem Duration values>

## Council Verdict: PASS / WARN / FAIL

| Judge | Verdict | Key Finding |
|-------|---------|-------------|
| Plan-Compliance | ... | ... |
| Tech-Debt | ... | ... |
| Learnings | ... | ... |

### Implementation Assessment
<council summary>

### Concerns
<any issues found>

## Learnings (from Phase 2)

### What Went Well
- ...

### What Was Hard
- ...

### Do Differently Next Time
- ...

### Patterns to Reuse
- ...

### Anti-Patterns to Avoid
- ...

### Footgun Entries (Required)

List discovered footguns — common mistakes or surprising behaviors that cost time:

| Footgun | Impact | Prevention |
|---------|--------|-----------|
| description | how it wasted time | how to prevent |

These entries are promoted to `.agents/learnings/` and injected into future worker prompts to prevent recurrence. Zero-cycle lag between discovery and prevention.

## Knowledge Lifecycle

### Backlog Processing (Phase 3)
- Scanned: N learnings
- Merged: N duplicates
- Flagged stale: N

### Activation (Phase 4)
- Promoted to MEMORY.md: N
- Constraints compiled: N
- Next-work items fed: N

### Retirement (Phase 5)
- Archived: N learnings

## Proactive Improvement Agenda

| # | Area | Improvement | Priority | Horizon | Effort | Evidence |
|---|------|-------------|----------|---------|--------|----------|
| 1 | repo / execution / ci-automation | ... | P0/P1/P2 | now/next-cycle/later | S/M/L | ... |

## Prior Findings Resolution Tracking

| Metric | Value |
|---|---|
| Backlog entries analyzed | ... |
| Prior findings total | ... |
| Resolved findings | ... |
| Unresolved findings | ... |
| Resolution rate | ...% |

| Source Epic | Findings | Resolved | Unresolved | Resolution Rate |
|---|---:|---:|---:|---:|
| ... | ... | ... | ... | ...% |

## Command-Surface Parity Checklist

| Command File | Run-path Covered by Test? | Evidence (file:line or test name) | Intentionally Uncovered? | Reason |
|---|---|---|---|---|
| cli/cmd/ao/<command>.go | yes/no | ... | yes/no | ... |

## BF Assessment

| Level | Exist? | Bugs | Action |
|-------|--------|------|--------|
| BF1 | y/n | N | property tests |
| BF4 | y/n | N | chaos tests |

## Next Work

| # | Title | Type | Severity | Source | Target Repo |
|---|-------|------|----------|--------|-------------|
| 1 | <title> | tech-debt / improvement / pattern-fix / process-improvement | high / medium / low | council-finding / retro-learning / retro-pattern | <repo-name or *> |

### Recommended Next /rpi
/rpi "<highest-value improvement>"

## Status

[ ] CLOSED - Work complete, learnings captured
[ ] FOLLOW-UP - Issues need addressing (create new beads)
```

### Step 4.5: Synthesize Proactive Improvement Agenda (MANDATORY)

**After writing the post-mortem report, analyze extraction + council context and proactively propose improvements to repo quality and execution quality.**

Read the extraction output (from Phase 2) and the council report (from Step 3). For each learning, ask:
1. **What process does this improve?** (build, test, review, deploy, documentation, automation, etc.)
2. **What's the concrete change?** (new check, new automation, workflow change, tooling improvement)
3. **Is it actionable in one RPI cycle?** (if not, split into smaller pieces)

Coverage requirements:
- Include **ALL** improvements found (no cap).
- Cover all three surfaces:
  - `repo` (code/contracts/docs quality)
  - `execution` (planning/implementation/review workflow)
  - `ci-automation` (validation/tooling reliability)
- Include at least **1 quick win** (small, low-risk, same-session viable).

Write process improvement items with type `process-improvement` (distinct from `tech-debt` or `improvement`). Each item must have:
- `title`: imperative form, e.g. "Add pre-commit lint check"
- `area`: which part of the development process to improve
- `description`: 2-3 sentences describing the change and why retro evidence supports it
- `evidence`: which retro finding or council finding motivates this
- `priority`: P0 / P1 / P2
- `horizon`: now / next-cycle / later
- `effort`: S / M / L

**These items feed directly into Step 5 (Harvest Next Work) alongside council findings. They are the flywheel's growth vector — each cycle makes the system smarter.**

Write this into the post-mortem report under `## Proactive Improvement Agenda`.

Example output:
```markdown
## Proactive Improvement Agenda

| # | Area | Improvement | Priority | Horizon | Effort | Evidence |
|---|------|-------------|----------|---------|--------|----------|
| 1 | ci-automation | Add validation metadata requirement for Go tasks | P0 | now | S | Workers shipped untested code when metadata didn't require `go test` |
| 2 | execution | Add consistency-check finding category in review | P1 | next-cycle | M | Partial refactoring left stale references undetected |
```

### Step 4.6: Prior-Findings Resolution Tracking (MANDATORY)

After Step 4.5, compute and include prior-findings resolution tracking from `.agents/rpi/next-work.jsonl`. Read `references/harvest-next-work.md` for the jq queries that compute totals and per-source resolution rates. Write results into `## Prior Findings Resolution Tracking` in the post-mortem report.

### Step 4.7: Command-Surface Parity Gate (MANDATORY)

Before marking post-mortem complete, enforce command-surface parity for modified CLI commands:

1. Identify modified command files under `cli/cmd/ao/` from the reviewed scope.
2. For each file, record at least one tested run-path (unit/integration/e2e) in `## Command-Surface Parity Checklist`.
3. Any intentionally uncovered command family must be explicitly listed with a reason and follow-up item.

If any modified command file is missing both coverage evidence and an intentional-uncovered rationale, post-mortem cannot be marked complete.

### Step 4.8: Persist Retro History (Trend Tracking)

After writing the post-mortem report, persist a structured summary JSON to `.agents/retro/YYYY-MM-DD-<epic-slug>.json` and append an index line to `.agents/retro/index.jsonl`. When 2+ prior retros exist, compute verdict streak, average cycle time, and learnings-per-retro trend for the report. See [references/retro-history.md](retro-history.md) for the full JSON schema, write rules, and trend queries.

### Step 5: Harvest Next Work

Scan the council report and extracted learnings for actionable follow-up items:

1. **Council findings:** Extract tech debt, warnings, and improvement suggestions from the council report (items with severity "significant" or "critical" that weren't addressed in this epic)
2. **Retro patterns:** Extract recurring patterns from learnings that warrant dedicated RPIs (items from "Do Differently Next Time" and "Anti-Patterns to Avoid")
3. **Process improvements:** Include all items from Step 4.5 (type: `process-improvement`). These are the flywheel's growth vector — each cycle makes development more effective.
4. **Footgun entries (REQUIRED):** Extract platform-specific gotchas, surprising API behaviors, or silent-failure modes discovered during implementation. Each must include: trigger condition, observable symptom, and fix. Write as type `pattern-fix` with source `retro-learning`. If a footgun was discovered this cycle, it must appear in this harvest — do not defer.
5. **Write `## Next Work` section** to the post-mortem report:

```markdown
## Next Work

| # | Title | Type | Severity | Source | Target Repo |
|---|-------|------|----------|--------|-------------|
| 1 | <title> | tech-debt / improvement / pattern-fix / process-improvement | high / medium / low | council-finding / retro-learning / retro-pattern | <repo-name or *> |
```

6. **SCHEMA VALIDATION (MANDATORY):** Before writing, validate each harvested item against the tracked contract in [`docs/contracts/next-work.schema.md`](../../../docs/contracts/next-work.schema.md). Read `references/harvest-next-work.md` for the validation function and write procedure. Drop invalid items; do NOT block the entire harvest.

7. **Write to next-work.jsonl** (canonical path: `.agents/rpi/next-work.jsonl`). Read `references/harvest-next-work.md` for the write procedure (target_repo assignment, claim/finalize lifecycle, JSONL format, required fields).

8. **Do NOT auto-create bd issues.** Report the items and suggest: "Run `/rpi --spawn-next` to create an epic from these items."

If no actionable items found, write: "No follow-up items identified. Flywheel stable."

### Step 6: Feed the Knowledge Flywheel

Post-mortem automatically feeds learnings into the flywheel:

```bash
if command -v ao &>/dev/null; then
  ao forge markdown .agents/learnings/*.md 2>/dev/null
  echo "Learnings indexed in knowledge flywheel"

  # Validate and lock artifacts that passed council review
  ao temper validate --min-feedback 0 .agents/learnings/YYYY-MM-DD-*.md 2>/dev/null || true
  echo "Artifacts validated for tempering"

  # Close session and trigger full flywheel close-loop (includes adaptive feedback)
  ao session close 2>/dev/null || true
  ao flywheel close-loop --quiet 2>/dev/null || true
  echo "Session closed, flywheel loop triggered"
else
  # Learnings are already in .agents/learnings/ from Phase 2.
  # Without ao CLI, grep-based search in /research
  # will find them directly — no copy to pending needed.

  # Feedback-loop fallback: update confidence for cited learnings
  mkdir -p .agents/ao
  if [ -f .agents/ao/citations.jsonl ]; then
    echo "Processing citation feedback (ao-free fallback)..."
    # Read cited learning files and boost confidence notation
    while IFS= read -r line; do
      CITED_FILE=$(echo "$line" | grep -o '"artifact_path":"[^"]*"' | cut -d'"' -f4)
      if [ -f "$CITED_FILE" ]; then
        # Note: confidence boost tracked via citation count, not file modification
        echo "Cited: $CITED_FILE"
      fi
    done < .agents/ao/citations.jsonl
  fi

  # Session-outcome fallback: record this session's outcome
  EPIC_ID="<epic-id>"
  echo "{\"epic\": \"$EPIC_ID\", \"verdict\": \"<council-verdict>\", \"cycle_time_minutes\": 0, \"timestamp\": \"$(date -Iseconds)\"}" >> .agents/ao/outcomes.jsonl

  # Skip ao temper validate (no fallback needed — tempering is an optimization)
  echo "Flywheel fed locally (ao CLI not available — learnings searchable via grep)"
fi
```
