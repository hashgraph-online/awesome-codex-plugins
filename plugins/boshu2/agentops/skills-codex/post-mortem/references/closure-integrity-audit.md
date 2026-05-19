# Closure Integrity Audit

**Mechanically verify that closed beads represent real completed work, not premature or phantom closures.**

This audit catches four failure modes discovered in production:

1. **Multi-wave regressions** — A later wave's worker removes code that an earlier wave added. Each wave passes tests independently, but the net result is incomplete.
2. **Phantom closures** — Beads closed with generic/empty descriptions ("task"), no spec, no git evidence.
3. **Orphaned children** — Child beads exist in `bd list` but aren't linked to parent in `bd show <parent>`.
4. **Stretch goals closed without work** — Items marked "stretch" bulk-closed when epic closes, with no implementation or documented deferral rationale.

For **evidence-only closures** that intentionally do not produce a code delta, require a proof artifact at `.agents/releases/evidence-only-closures/<target-id>.json` (or, for legacy artifacts, `.agents/council/evidence-only-closures/<target-id>.json`). The artifact is written with `bash skills/post-mortem/scripts/write-evidence-only-closure.sh` and gives later audits something durable to validate besides bead notes.

Evidence strength is ordered. Closure integrity must always resolve on the strongest available source in this order:

1. `evidence-only-packet` — a durable closure proof packet exists at `.agents/releases/evidence-only-closures/<target-id>.json` or `.agents/council/evidence-only-closures/<target-id>.json` and parses as JSON containing both `evidence_mode` and `repo_state` keys (the schema written by `write-evidence-only-closure.sh`). This is the **strongest** proof surface and short-circuits all other classification paths: when the packet is present and well-formed, the bead is accepted as PASS regardless of scoped-file extraction or git state. Use this for maintenance epics, policy closures, and any work whose proof is the packet itself rather than a code delta.
2. `commit` — commit references or commit history touching the scoped files
3. `staged` — index state proves the scoped files are queued for commit even if no commit exists yet
4. `worktree` — unstaged or untracked scoped files prove active-session work exists when neither commit nor staged evidence is available
5. `grace-window` — commit evidence found within the configurable grace window (default 24h) after bead close, covering the close-before-commit pattern

Only fall back to a weaker source when the stronger source has no qualifying evidence for that child. A dirty worktree must not downgrade a valid commit-backed closure. Conversely, a valid evidence-only packet must not be downgraded by the absence of scoped-file evidence — the packet is itself the proof.

The allowed evidence modes in audit output are: `commit`, `staged`, `worktree`, `evidence-only-packet`, `grace-window`, and the warn-only mode `discovery-seed-missing`. No catch-all or wildcard modes are accepted.

### Task-Queue Closure Mode

Most audits run against epics and their child beads. A post-mortem can also close a queue-drain task that intentionally has no child beads, such as a PR queue cleanup. In that case, `closure-integrity-audit.sh` may accept the closed non-epic target itself as `closure_mode=task-queue` instead of failing collection, but only when it finds one of these replayable proof surfaces:

- a valid durable evidence-only closure packet for the target id
- a commit message that references the target id
- a PR reference in the target text (`#123`, `PR #123`, `pull/123`, etc.) whose matching PR merge/squash commit exists in git history

No-child epics still fail collection. Closed no-child task targets without the proof above also fail with a detail explaining that task-queue fallback requires merge evidence or a durable packet.

### Discovery-phase seed artifacts (WARN-only, never FAIL)

Discovery-phase beads — the brainstorm / research / discovery children an epic spawns during the Research phase — commonly cite seed artifacts (`.agents/brainstorm/...`, `.agents/research/...`, `.agents/discovery/...`) that are ephemeral working notes, not durable proof surfaces. These seeds are often never persisted and cannot be replayed by later audits.

The discovery-miss WARN policy only runs when the bead does NOT have a valid evidence-only closure packet. A bead with such a packet PASSes via the evidence-only-packet short-circuit before discovery classification is considered.

When a CLOSED bead has **every** scoped file under `.agents/brainstorm/`, `.agents/research/`, or `.agents/discovery/` AND at least one of the following non-discovery proof surfaces exists, the audit emits `status=warn`, `evidence_mode=discovery-seed-missing`, `detail` starting with `discovery_miss:` — it does NOT hard-fail as `timing_miss`:

- a commit whose message references the bead id
- a durable evidence-only closure packet for the bead
- a `.agents/plans/` or `.agents/findings/` file referenced in the bead text that exists on disk
- any non-discovery file path referenced in the bead description or close reason that has real git history
- a substantive `Close reason:` line (≥ 24 chars) written at `bd close` time

Beads with scoped files OUTSIDE the discovery-phase prefixes that lack evidence still hard-fail as `timing_miss`. The downgrade applies only when discovery seeds are the only scoped files.

## When to Run

- **Step 2.3** of post-mortem (Reconcile Plan vs Delivered Scope)
- After `/crank` completes (before closing epic)
- During `/retro` when reviewing multi-wave epics

## Audit Procedure

Prefer `bash skills/post-mortem/scripts/closure-integrity-audit.sh --scope auto <epic-id>`
for any real audit. The shell snippets below are explanatory fallbacks, not parser
contracts.

Manual-audit footguns:

- Prefer structured CLI surfaces such as `--json` whenever they exist. Do not build automation on human-readable prose output.
- When running git discovery from hooks, helper shells, or shared-worktree sessions, unset `GIT_DIR`, `GIT_WORK_TREE`, and `GIT_COMMON_DIR` first so evidence resolves against the intended repo/worktree.

### Check 1: Evidence Precedence Per Child

For each closed child bead, verify evidence in precedence order: `commit`, then `staged`, then `worktree`. Use `bash skills/post-mortem/scripts/closure-integrity-audit.sh --scope auto <epic-id>` for the executable path, or the outline below if you are auditing manually.

```bash
EPIC_ID="<epic-id>"
FAILURES=""

# Get all children
for child in $(bd children "$EPIC_ID" 2>/dev/null | grep -oE '[a-z]{2}-[a-z0-9]+\.[0-9]+' | sort -u); do
  # 1. Commit evidence: strongest path
  COMMITS=$(git log --oneline --all --grep="$child" 2>/dev/null | wc -l | tr -d ' ')

  if [ "$COMMITS" -eq 0 ]; then
    CHILD_DESC=$(bd show "$child" 2>/dev/null)
    FILES_IN_SCOPE=$(echo "$CHILD_DESC" | grep -oP '`[^`]+\.(go|py|ts|sh|md|yaml)`' | tr -d '`')

    if [ -z "$FILES_IN_SCOPE" ]; then
      FAILURES="${FAILURES}\n- NO EVIDENCE: $child — zero commits, no file metadata"
    else
      # 2. Commit path by file history
      TOUCHED=0
      for f in $FILES_IN_SCOPE; do
        if git log --oneline --diff-filter=ACMR -- "$f" 2>/dev/null | head -1 | grep -q .; then
          TOUCHED=1
          break
        fi
      done
      if [ "$TOUCHED" -eq 0 ]; then
        # 3. Staged fallback
        STAGED=$(git diff --cached --name-only --diff-filter=ACMR -- $FILES_IN_SCOPE 2>/dev/null | head -1)
        if [ -n "$STAGED" ]; then
          continue
        fi

        # 4. Worktree fallback (unstaged or untracked)
        WORKTREE=$(
          {
            git diff --name-only --diff-filter=ACMR -- $FILES_IN_SCOPE 2>/dev/null
            git ls-files --others --exclude-standard -- $FILES_IN_SCOPE 2>/dev/null
          } | head -1
        )
        [ -z "$WORKTREE" ] && FAILURES="${FAILURES}\n- NO EVIDENCE: $child — no commit, staged, or worktree evidence for scoped files"
      fi
    fi
  fi
done
```

**Verdict:**
- 0 failures → PASS
- 1-2 failures → WARN (include in council packet, continue)
- 3+ failures → FAIL (block epic closure, investigate)

### Evidence Mode Reporting

When a child resolves on staged or worktree evidence instead of commit evidence, record that mode explicitly in the closure proof and council packet:

- `commit` — commit-backed evidence exists and wins
- `staged` — no qualifying commit evidence exists, but the scoped files are staged
- `worktree` — neither commit nor staged evidence exists, but the scoped files are present in unstaged or untracked working-tree state
- `evidence-only-packet` — no scoped files extractable, but a valid durable closure proof packet exists
- `grace-window` — commit evidence found within the grace window after bead close

When the audit accepts a no-child queue-drain task, it keeps the evidence mode as `commit` or `evidence-only-packet` and reports the shape separately under `summary.closure_modes["task-queue"]`.

Use `auto` only for audit selection logic, never as the final reported evidence mode.

### Evidence-Only Closure Packet

If a child is being closed on validation or policy evidence alone, or it closes before commit-backed proof exists, produce a packet before closeout. The writer emits both:

- Local council copy: `.agents/council/evidence-only-closures/<target-id>.json`
- Durable tracked copy: `.agents/releases/evidence-only-closures/<target-id>.json`

If the child closes before commit-backed proof exists, the durable tracked copy must be preserved with the change set.

If a child is being closed on validation or policy evidence alone, produce a packet before closeout:

```bash
bash skills/post-mortem/scripts/write-evidence-only-closure.sh \
  --target-id "<bead-id>" \
  --target-type issue \
  --producer post-mortem \
  --evidence-mode auto \
  --validation-command "bash tests/hooks/lib-hook-helpers.bats" \
  --evidence-summary "No code delta required; validation artifact captured." \
  --artifact ".agents/council/<report>.md"
```

Minimum packet fields:
- `schema_version`
- `artifact_id`
- `target_id`
- `target_type`
- `created_at`
- `producer`
- `evidence_mode`
- `validation_commands`
- `repo_state`
- `evidence`

Minimum `repo_state` fields:
- `repo_root`
- `git_branch`
- `git_dirty`
- `head_sha`
- `modified_files`
- `staged_files`
- `unstaged_files`
- `untracked_files`

### Check 2: Phantom Bead Detection

Flag children with no meaningful description or title.

```bash
for child in $(bd children "$EPIC_ID" 2>/dev/null | grep -oE '[a-z]{2}-[a-z0-9]+\.[0-9]+' | sort -u); do
  TITLE=$(bd show "$child" 2>/dev/null | head -1 | sed 's/^.*· //' | sed 's/ \[.*$//')
  DESC=$(bd show "$child" 2>/dev/null | sed -n '/^DESCRIPTION$/,/^$/p' | tail -n +2)

  # Generic titles: "task", "fix", "update", single word
  if echo "$TITLE" | grep -qP '^(task|fix|update|todo|item|work)$'; then
    FAILURES="${FAILURES}\n- PHANTOM: $child — generic title '$TITLE', no spec"
  fi

  # Empty or minimal description
  DESC_WORDS=$(echo "$DESC" | wc -w | tr -d ' ')
  if [ "$DESC_WORDS" -lt 5 ]; then
    FAILURES="${FAILURES}\n- PHANTOM: $child — description has $DESC_WORDS words (min 5)"
  fi
done
```

**Why this matters:** Phantom beads inflate completion metrics without representing real work. In the na-oh2 audit, 11 children all had "task" as their title — only the git commit revealed what they actually did.

### Check 3: Orphaned Children

Verify all children in `bd list` are linked to parent.

```bash
# Children from parent's perspective
PARENT_CHILDREN=$(bd show "$EPIC_ID" 2>/dev/null | grep '↳' | grep -oP '\w+-\w+\.\d+')

# Children from list (matching prefix)
LIST_CHILDREN=$(bd list --all 2>/dev/null | grep "^. ${EPIC_ID}\." | grep -oP '\w+-\w+\.\d+')

# Find orphans (in list but not in parent)
for child in $LIST_CHILDREN; do
  if ! echo "$PARENT_CHILDREN" | grep -q "^${child}$"; then
    FAILURES="${FAILURES}\n- ORPHAN: $child — exists in bd list but not linked to $EPIC_ID"
  fi
done
```

### Check 4: Multi-Wave Regression Detection

For multi-wave epics (crank), compare each wave's additions against the next wave's deletions.

```bash
# Get wave commits from crank notes
WAVE_COMMITS=$(bd show "$EPIC_ID" 2>/dev/null | grep 'CRANK_WAVE' | grep -oP 'at \K\S+')

# For each consecutive pair, check if Wave N+1 deleted lines Wave N added
PREV_COMMIT=""
for commit in $WAVE_COMMITS; do
  if [ -n "$PREV_COMMIT" ]; then
    # Lines added in previous wave
    ADDED=$(git diff "$PREV_COMMIT"^.."$PREV_COMMIT" 2>/dev/null | grep '^+[^+]' | sort)
    # Lines removed in current wave
    REMOVED=$(git diff "$commit"^.."$commit" 2>/dev/null | grep '^-[^-]' | sort)

    # Intersection = regressions
    REVERTED=$(comm -12 <(echo "$ADDED" | sed 's/^+//') <(echo "$REMOVED" | sed 's/^-//') 2>/dev/null | head -10)

    if [ -n "$REVERTED" ]; then
      FAILURES="${FAILURES}\n- REGRESSION: Wave removed lines that prior wave added:\n$(echo "$REVERTED" | head -5)"
    fi
  fi
  PREV_COMMIT="$commit"
done
```

**Origin:** na-vs9.4 — Wave 1 added vibe checkpoint detection (15 lines), Wave 2 removed it entirely. Both waves passed tests independently. The orphaned checkpoint writer in crank was only caught by manual audit.

### Check 5: Acceptance-Text vs Delivered Drift

For each closed child, read the bead's `Acceptance:` text and check whether it has drifted from what the closure commit delivered. Catches the case where a bead's acceptance language names a specific gate as a pass requirement but the close-note doesn't confirm the gate ran green.

```bash
for child in $CLOSED_CHILDREN; do
  ACCEPT=$(bd show "$child" 2>/dev/null \
           | awk '/^Acceptance:/,/^[A-Z][A-Z]+:|^---/' | head -50)
  CLOSE_NOTE=$(bd show "$child" 2>/dev/null \
               | awk '/COMMENTS/,0' | tail -30)
  GATE_REFS=$(printf '%s\n' "$ACCEPT" \
              | grep -oE '(scripts/check-[a-z0-9-]+\.sh|check-[a-z0-9-]+|pre-push-gate|ci-local-release)' \
              | sort -u)
  if [ -n "$GATE_REFS" ]; then
    for gate in $GATE_REFS; do
      if ! printf '%s\n' "$CLOSE_NOTE" | grep -qiE "$gate.*pass|$gate.*green|pass.*$gate"; then
        FAILURES="${FAILURES}\n- ACCEPTANCE DRIFT: $child — acceptance names gate '$gate', close-note does not confirm green"
      fi
    done
  fi
  if printf '%s\n' "$ACCEPT" | grep -qE '\bOR\b'; then
    if ! printf '%s\n' "$CLOSE_NOTE" | grep -qiE 'chose|picked|path [0-9]|operator chose|alternative'; then
      FAILURES="${FAILURES}\n- ACCEPTANCE BRANCH UNCLEAR: $child — acceptance has OR alternatives, close-note doesn't state which was satisfied"
    fi
  fi
done
```

WARN-level (not FAIL): wording variance is expected. The intent is to surface drift for council review.

Origin: v2.41-evolve-run cycle 182. `soc-w6vh.4` acceptance: "`check-no-tracked-agents` AND `check-worktree-disposition` pass". Close-note described the operator's chosen action (commit the worktree) but did NOT confirm the worktree-disposition gate ran green — because it still failed on broader fleet state. Correct alternatives: (a) explicitly narrow the bead's acceptance before closing, or (b) leave open with a scope-narrowing follow-up filed.

### Check 6: Stretch Goal Audit

For children tagged "stretch" that were closed, verify either implementation exists or deferral is documented.

```bash
for child in $(bd children "$EPIC_ID" 2>/dev/null | grep -i 'stretch' | grep -oE '[a-z]{2}-[a-z0-9]+\.[0-9]+' | sort -u); do
  STATUS=$(bd show "$child" 2>/dev/null | grep -oP 'CLOSED')
  CLOSE_REASON=$(bd show "$child" 2>/dev/null | grep 'Close reason:')
  COMMITS=$(git log --oneline --all --grep="$child" 2>/dev/null | wc -l | tr -d ' ')

  if [ -n "$STATUS" ] && [ "$COMMITS" -eq 0 ]; then
    if ! echo "$CLOSE_REASON" | grep -qi 'defer\|stretch\|intentional\|not needed'; then
      FAILURES="${FAILURES}\n- STRETCH CLOSED WITHOUT RATIONALE: $child — no commits, no deferral reason"
    fi
  fi
done
```

## Output Format

Write results into the post-mortem report under `## Closure Integrity`:

```markdown
## Closure Integrity

| Check | Result | Details |
|-------|--------|---------|
| Evidence Precedence | PASS/WARN/FAIL | N children resolved by commit/staged/worktree, M without evidence |
| Phantom Beads | PASS/WARN | N phantom beads detected |
| Orphaned Children | PASS/WARN | N orphans found |
| Multi-Wave Regression | PASS/FAIL | N regressions detected |
| Acceptance Drift | PASS/WARN | N closed beads whose acceptance text names gates that the close-note does not confirm green |
| Stretch Goals | PASS/WARN | N stretch goals closed without rationale |

### Findings
- <specific findings from each check>
```

## Integration with Council

Include closure integrity results in the council packet:

```json
{
  "context": {
    "closure_integrity": {
      "git_evidence_failures": [...],
      "evidence_modes": {
        "commit": [...],
        "staged": [...],
        "worktree": [...]
      },
      "phantom_beads": [...],
      "orphaned_children": [...],
      "wave_regressions": [...],
      "stretch_audit": [...]
    }
  }
}
```

The `plan-compliance` judge uses these to assess whether the epic should actually be marked complete.
