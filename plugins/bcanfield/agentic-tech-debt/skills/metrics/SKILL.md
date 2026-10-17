---
name: metrics
description: Print a debt-ops health summary from the metrics log, covering registration rate, hook feedback action rate, ADR creation, and AI-authored share. Use when the user asks for "debt-ops metrics", "debt health", "registry stats", or invokes $metrics. Read-only, never writes the log.
---

# metrics

Read the hidden metrics log and tell the user whether v1's tripwires are tripping.

## 1. Find the log

```bash
TOPLEVEL=$(git rev-parse --show-toplevel)
REPO_HASH=$(printf '%s' "$TOPLEVEL" | shasum | cut -c1-12)

# Hooks and skills share one deterministic cache base (ADR 0011). Override the
# base with DEBT_OPS_CACHE; default is ~/.cache/debt-ops.
CACHE_DIR="${DEBT_OPS_CACHE:-$HOME/.cache/debt-ops}/cache/$REPO_HASH"

LOG="$CACHE_DIR/metrics.jsonl"
if [ -f "$LOG" ]; then
  tail -n 500 "$LOG"
else
  echo "MISSING: no metrics.jsonl found for repo hash $REPO_HASH"
fi
```

If the file is missing or empty, tell the user the hooks haven't fired yet in this repo and stop.

## 2. The log format

One JSON object per line, three event shapes:

- `{"event":"edit","file":"...","registry_count":N,"ts":"..."}` — every agent edit
- `{"event":"feedback","file":"...","result":"pass|fail","ts":"..."}` — every quality-check fire
- `{"event":"session","registry_count":N,"adr_count":M,"ai_authored_count":K,"ts":"..."}` — start of each session

Timestamps are ISO-8601 UTC.

## 3. Compute the tripwires

Filter to the last 7 days. Then compute:

- **Edits / sessions** — counts of `event:edit` and `event:session`.
- **Registry growth** — last `registry_count` minus first (across either edit or session events). >0 means Discipline 1 is firing.
- **ADR growth** — last `adr_count` minus first (session events only).
- **AI-authored share trend** — first vs. last session percentage (`ai_authored_count / registry_count`, when registry_count>0).
- **Feedback pass rate** — `count(result:pass) / count(event:feedback)`.
- **FAIL → PASS rate** — for each feedback event with `result:fail`, look at the *next* feedback event for the *same* file. Count those that flipped to `pass`. Divide by total fails. Below 50% means the agent isn't reliably acting on hook output — the architectural alarm bell.

If there are fewer than 5 sessions in the window, say "need more data" and skip the verdict.

## 4. Report

One screen. No padding. Use `→` and `↑/↓` for trends. Example shape:

```
debt-ops metrics — last 7 days
─────────────────────────────────
edits           : 142  (8 sessions, ~18 edits/session)
registry        : +3
adrs            : +1
ai-authored     : 50% → 60% ↑

feedback ran    : 89 times
pass rate       : 88%
fail → pass rate: 80% (8/10)

verdict: ok
```

End with one judgment line:
- **ok** — registry growth >0 AND fail→pass rate ≥50%.
- **investigate: <reason>** — name the specific tripwire that tripped.

## Don't

- Don't write to the log.
- Don't compute metrics not listed above.
- Don't guess at health when data is thin — say "need more data" instead.
