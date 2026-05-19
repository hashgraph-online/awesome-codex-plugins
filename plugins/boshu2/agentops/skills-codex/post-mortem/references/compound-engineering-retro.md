# Compound-Engineering Retro — Comparative Delta Mode

Compare iteration N vs N-1 of a domain slice using the F5.1 verdict ledger
and emit a structured learning with the delta.

**Preconditions:** the project has a `docs/domains/<name>/manifest.yaml` (a
domain slice) and the verdict ledger at `.agents/goals/verdict-ledger.json`
contains ≥2 `iteration` records for at least one of the slice's directives
(i.e., `ao goals measure` has been run at least twice).

---

## Step CE.0: Identify the slice and its directives

```bash
SLICE="<name>"                              # e.g. "billing"
MANIFEST="docs/domains/${SLICE}/manifest.yaml"
cat "$MANIFEST" | grep directive_id         # list directive IDs owned by the slice
```

Collect the stable `d-<id>` directive IDs from the manifest's `directives` list.

## Step CE.1: Extract iteration N and N-1 from the verdict ledger

The ledger is an append-only JSON file. Each entry with `"record_type": "iteration"`
represents one completed `ao goals measure` call.

```bash
LEDGER=".agents/goals/verdict-ledger.json"

# For each directive in the slice, pull the last two iteration records:
jq --arg did "<directive-id>" '
  [.records[] | select(.record_type == "iteration" and .directive_id == $did)]
  | if length < 2 then error("need ≥2 iterations") else . end
  | .[-2:] | {prev: .[0], curr: .[1]}
' "$LEDGER"
```

Repeat for every directive in the slice. Collect results into `PREV_MAP` (directive →
N-1 record) and `CURR_MAP` (directive → N record).

## Step CE.2: Compute the delta

For each directive, compare N vs N-1 on two axes:

| Axis | Improved | Regressed | Stable |
|------|----------|-----------|--------|
| **Verdict** | fail → pass | pass → fail | same |
| **Satisfaction** | `curr - prev > 0.05` | `curr - prev < -0.05` | within ±0.05 |

```bash
# Quick shell delta across all directives (reads the ledger directly):
jq --argjson dids '["d-foo","d-bar"]' '
  [ .records[] | select(.record_type == "iteration" and ([.directive_id] | inside($dids))) ]
  | group_by(.directive_id)
  | map({
      id: .[0].directive_id,
      prev: .[-2],
      curr: .[-1],
      verdict_delta: (.[-2].scenario_verdict + "→" + .[-1].scenario_verdict),
      sat_delta: (.[-1].scenario_satisfaction - .[-2].scenario_satisfaction)
    })
' "$LEDGER"
```

Classify each directive:

- **Improved**: verdict fail→pass, OR satisfaction up > 0.05
- **Regressed**: verdict pass→fail, OR satisfaction down > 0.05
- **Stable**: everything else

## Step CE.3: Measure learning yield

Count learnings drafted since N-1's `run_timestamp`:

```bash
PREV_TS="<run_timestamp of N-1 record>"   # ISO-8601 from ledger
find .agents/learnings/ -name "*.md" -newer <(date -d "$PREV_TS" +%Y-%m-%d) 2>/dev/null | wc -l
```

Also note whether any `cooldown` records were written to the ledger between N-1 and N
(re-steer proposals from the F5.3 engine).

## Step CE.4: Write the delta as a learning

Write to `.agents/learnings/YYYY-MM-DD-<slice>-iter-delta.md`:

```markdown
---
id: learning-YYYY-MM-DD-<slice>-iter-delta
type: learning
date: YYYY-MM-DD
category: feedback-loop
confidence: <high|medium|low>
maturity: provisional
status: draft
utility: 0.5
slice: <name>
iter_n_run_id: <run_id of N record>
iter_prev_run_id: <run_id of N-1 record>
---

# Compound-Engineering Retro: <slice> iteration delta

## What Improved

| Directive | Verdict N-1→N | Satisfaction N-1→N |
|-----------|---------------|--------------------|
| d-foo     | fail→pass     | 0.40→0.85 (+0.45)  |

## What Regressed

| Directive | Verdict N-1→N | Satisfaction N-1→N |
|-----------|---------------|--------------------|
| d-bar     | pass→fail     | 0.90→0.60 (−0.30)  |

## Stable Directives

- d-baz: pass→pass, 0.70→0.72 (stable)

## Learning Yield (since N-1)

N learnings drafted. N cooldown proposals in ledger.

## Root-Cause Hypotheses

<1-2 sentences on why regressions occurred, if known>

## Follow-Up Actions

- [ ] Investigate d-bar regression: <hypothesis>
- [ ] Promote if delta is validated next run
```

`status: draft` — human or Tier-3 synthesis promotes to `status: reviewed`.

## Step CE.5: Feed next-work (optional)

If regressions are high-severity, append an entry to `.agents/rpi/next-work.jsonl`
per the claim/finalize lifecycle in `references/harvest-next-work.md`.

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `ao goals measure [--goal <id>]` | Run one iteration; appends to ledger |
| `ao goals history [--goal <id>]` | Browse past iterations (summary view) |
| `jq '...' .agents/goals/verdict-ledger.json` | Raw ledger inspection |
| `cat docs/domains/<name>/manifest.yaml` | List directives owned by a slice |

The ledger artifact path is `.agents/goals/verdict-ledger.json`
(defined in `cli/internal/verdictledger/verdictledger.go:ArtifactRelPath`).
