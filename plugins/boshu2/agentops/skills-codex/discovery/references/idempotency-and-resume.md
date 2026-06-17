# Idempotency and Resume Behavior

## $discovery

`$discovery` is **idempotent at the step level** — re-running it with the same goal will not duplicate artifacts if prior outputs exist.

### Step-Level Idempotency

| Step | Behavior on Re-run |
|------|--------------------|
| Brainstorm | **Skipped** if `.agentsbrainstorm/*<goal-slug>*` exists |
| History search | **Always runs** — ao search is read-only |
| Research | **Runs again** — research output appends, does not overwrite |
| Plan | **Runs again** — creates new epic if none open, reuses if open epic matches goal |
| Pre-mortem | **Runs again** — council always produces a fresh verdict |

### Resume via `$rpi --from=discovery`

When `$rpi --from=discovery` is invoked:
- Discovery runs from Step 1 (brainstorm) regardless of prior progress
- Step-level skip logic prevents duplicate brainstorm artifacts
- A new pre-mortem verdict is always produced (council is not cached)

### Epic Deduplication

If `br list --type epic --status open` returns an epic matching the current goal, `$plan` reuses it rather than creating a duplicate. This prevents epic proliferation on re-runs.

## $validate

`$validate` is **NOT idempotent** — each run produces a new vibe report and post-mortem.

### Re-run Behavior

| Step | Behavior on Re-run |
|------|--------------------|
| Vibe | **Runs again** — produces new council report |
| Post-mortem | **Runs again** — produces new retrospective |
| Retro | **Runs again** — may capture duplicate learnings |
| Forge | **Runs again** — transcript mining is append-only |

### Resume via `$rpi --from=validation`

When `$rpi --from=validation` is invoked:
- Reads existing `execution-packet.json` for context
- Does NOT require Phase 1 or Phase 2 to have run in the current session
- Requires epic-id as argument (or reads from execution-packet)

## $rpi

The `$rpi` orchestrator itself is **stateless** — it does not persist cross-session state. Phase transitions use filesystem artifacts:

- `execution-packet.json` — discovery → crank handoff
- `phase-*-summary-*.md` — phase completion records
- `phased-state.json` — complexity and cycle tracking (written but not required for resume)

To resume a partially completed RPI cycle, use `--from=<phase>` with the appropriate epic-id.
