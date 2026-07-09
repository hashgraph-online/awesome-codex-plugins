# Fitness Scoring

## Measurement

Run the fitness measurement script to produce a rolling snapshot:

```bash
bash scripts/evolve-measure-fitness.sh \
  --output .agents/evolve/fitness-latest.json \
  --timeout 60 \
  --total-timeout 75
```

**Do NOT write per-cycle `fitness-{N}-pre.json` files.** The rolling file is sufficient for work selection and regression detection.

This writes a fitness snapshot to `.agents/evolve/` atomically via a temp file plus JSON validation. The AgentOps CLI is required for fitness measurement because the wrapper shells out to `ao goals measure`. If measurement exceeds the whole-command bound or returns invalid JSON, the wrapper fails without clobbering the previous rolling snapshot.

## Era Baseline Capture (First Run Only)

Skip if `--skip-baseline` or `--beads-only` or baseline already exists.

`/evolve` captures this automatically before entering the RPI loop. It hashes
the active GOALS.md or GOALS.yaml file to an era ID, then writes a snapshot
under `.agents/evolve/fitness-baselines/goals-<hash>/` if that era directory
does not already contain a JSON snapshot.

For manual recovery or one-off capture, compute the same era ID and use the
helper script:

```bash
GOALS_FILE=""
if [ -f GOALS.md ]; then
  GOALS_FILE="GOALS.md"
elif [ -f GOALS.yaml ]; then
  GOALS_FILE="GOALS.yaml"
fi

if [ -n "$GOALS_FILE" ]; then
  ERA_ID="goals-$(shasum -a 256 "$GOALS_FILE" | awk '{print substr($1, 1, 12)}')"
  bash scripts/evolve-capture-baseline.sh \
    --label "$ERA_ID" \
    --timeout 60 \
    --total-timeout 75
fi
```

## Post-Cycle Re-Measurement (Regression Gate)

After execution, re-measure to detect regressions:

```bash
bash scripts/evolve-measure-fitness.sh \
  --output .agents/evolve/fitness-latest-post.json \
  --timeout 60 \
  --total-timeout 75 \
  --goal "$GOAL_ID"

# Extract goal counts for cycle history entry
PASSING=$(jq '[.goals[] | select(.result=="pass")] | length' .agents/evolve/fitness-latest-post.json 2>/dev/null || echo 0)
TOTAL=$(jq '.goals | length' .agents/evolve/fitness-latest-post.json 2>/dev/null || echo 0)
```

**If regression detected** (previously-passing goal now fails):

```bash
git revert HEAD --no-edit  # single commit
# or for multiple commits:
git revert --no-commit ${CYCLE_START_SHA}..HEAD && git commit -m "revert: evolve cycle ${CYCLE} regression"
```

Set outcome to "regressed".

## Oscillation Detection

Before working a failing goal, check if it has oscillated (improved-to-fail transitions >= 3 times in `cycle-history.jsonl`). If so, quarantine it and try the next failing goal.

```bash
# Reads cycle history via BC3 LoopReaderPort (soc-y5vh.4 wrapper),
# not raw .agents/evolve/cycle-history.jsonl slurp.
OSC_COUNT=$(scripts/evolve-read-cycle-history.sh recent 0 \
  | jq -r "select(.target==\"$FAILING\") | .result" \
  | awk 'prev=="improved" && $0=="fail" {count++} {prev=$0} END {print count+0}')
if [ "$OSC_COUNT" -ge 3 ]; then
  QUARANTINED_GOALS[$FAILING]=true
  echo "{\"cycle\":${CYCLE},\"target\":\"${FAILING}\",\"result\":\"quarantined\",\"oscillations\":${OSC_COUNT},\"timestamp\":\"$(date -Iseconds)\"}" >> .agents/evolve/cycle-history.jsonl
fi
```

See also: `references/oscillation.md` for full quarantine protocol.
