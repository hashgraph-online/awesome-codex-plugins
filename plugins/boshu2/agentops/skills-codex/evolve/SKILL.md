---
name: evolve
description: "Run autonomous improvement loops."
---
# $evolve — Goal-Driven Compounding Loop

> Measure what's wrong. Fix the worst thing. Measure again. Compound.

**Codex orchestration default:** keep the skill name `$evolve`. In Codex,
run the loop by chaining Codex skills: `$evolve` selects work and invokes
complete `$rpi --auto` cycles. Each cycle's post-mortem checkpoint is a
**re-plan point, not just stop/continue** — it may re-scope, reorder, drop, or
add to the *remaining* queue/goal (`$rpi`'s
[Agile Re-Plan Loop](../rpi/references/agile-replan-loop.md) one altitude up:
agile across cycles, not a fixed backlog). Treat retired CLI wrappers as terminal
commands for humans/non-skill runtimes, not the Codex default. Substrates dispatch
the whole `$evolve` loop as one unit through NTM, Agent Mail, or `ao agent`; former
RPI CLI wrappers are retired under ADR-0009.

**Operator cadence:** post-mortem finished work, analyze repo state, select/create
the next highest-value item, let `$rpi` handle research → planning → pre-mortem →
implementation → validation, then harvest follow-ups and repeat until a kill
switch, max-cycle cap, regression breaker, or real dormancy stops the run.

Always-on autonomous loop over `$rpi`. Work selection order:
1. **Harvested `.agents/rpi/next-work.jsonl` work** (freshest concrete follow-up)
2. **Open ready beads work** (`br ready`)
3. **Failing goals and directive gaps** (`ao goals measure`)
4. **Testing improvements** (missing/thin coverage, missing regression tests)
5. **Validation tightening and bug-hunt passes** (gates, audits, bug sweeps)
6. **Complexity / TODO / FIXME / drift / dead code / stale docs / stale research mining**
7. **Concrete feature suggestions** derived from repo purpose when no sharper work exists

**Dormancy is last resort.** Empty queues mean "run the generator layers", not "stop". Go dormant only after queue and generator layers come up empty across multiple consecutive passes.

**Live skill edit immune system:** if a cycle edits `skills/<slug>/SKILL.md`, run
`ao skills edit seal --skill <slug> --actor "${AGENT_NAME:-agent}"` before handoff
— the seal creates the rollback commit and records the `Skill-Edit` trailers for
the daily digest. Critical skills in `docs/contracts/critical-skills.txt` reject
unattended edits; use `--allow-critical` only when Bo supervises.

```bash
$evolve                      # Run until kill switch, max-cycles, or real dormancy
$evolve --max-cycles=5       # Cap at 5 cycles
$evolve --dry-run            # Show what would be worked on, don't execute
$evolve --quality            # Quality-first: prioritize post-mortem findings
$evolve --compile            # Mine → Defrag warmup before first cycle
# All flags in the Flags table below; they compose (e.g. --quality --max-cycles=10).
```

## Delineation vs $dream

| Lane | Runs | Mutates code? | Mutates corpus? | Outer loop? | Budget |
|------|------|---------------|-----------------|-------------|--------|
| `$dream` | nightly, private local | **No** | **Yes (heavy)** | **Yes (convergence)** | wall-clock + plateau |
| `$evolve` | daytime, operator-driven | Yes (via `$rpi`) | Yes (light) | Yes | cycle cap |

Dream owns knowledge compounding; `$evolve` owns code compounding. Both share fitness substrate (`corpus.Compute` / `ao goals measure`). Dream runs overnight; `$evolve` starts the day on the fresh corpus.

## Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--max-cycles=N` | unlimited | Stop after `N` completed cycles |
| `--dry-run` | off | Show planned cycle actions without executing |
| `--beads-only` | off | Skip goal measurement and run backlog-only selection |
| `--skip-baseline` | off | Skip first-run baseline snapshot |
| `--quality` | off | Prioritize harvested post-mortem findings |
| `--compile` | off | Run `ao mine` + `ao defrag` warmup before cycle 1 |
| `--test-first` | on | Pass strict-quality defaults through to `$rpi` |
| `--no-test-first` | off | Explicitly disable test-first passthrough to `$rpi` |

## Managing the PROGRAM.md / AUTODEV.md contract (absorbed from $autodev)

$evolve also fires for the folded-in use-cases of the retired `$autodev` skill:
"manage PROGRAM.md/AUTODEV.md", "autodev loop rules", "evolve/factory tick
boundaries", PROGRAM.md repair. The contract is the config/intent layer the
loop reads each cycle — NOT a loop itself. The **ao autodev CLI (legacy-tagged `ao` builds) outlives the
retired skill** (contract spec: `docs/contracts/autodev-program.md`). Step 0
consumes a valid contract; this section is the create/validate/repair surface.
In Codex, `$autodev` hands work to `$evolve` or `$rpi` as skill invocations.

Detect (`PROGRAM.md` takes precedence; `AUTODEV.md` is the compatibility alias),
validate before use, init only when setup was requested:

```bash
if [ -f PROGRAM.md ]; then PROGRAM_PATH=PROGRAM.md
elif [ -f AUTODEV.md ]; then PROGRAM_PATH=AUTODEV.md
else PROGRAM_PATH=; fi
ao autodev validate --json ${PROGRAM_PATH:+--file "$PROGRAM_PATH"}
ao autodev init "<objective>"   # no contract + setup requested; infer objective from repo context
```

On validation failure, patch the missing required sections — `Objective`,
`Mutable Scope`, `Immutable Scope`, `Experiment Unit`, `Validation Commands`,
`Decision Policy`, `Escalation Rules`, `Stop Conditions` — then rerun the
validate command. Prefer narrow mutable scope and concrete validation commands;
work crossing immutable scope becomes a bead, never a silently widened contract.

Routing: define/repair the repo-local autonomous policy → this section +
ao autodev; run the repeated improvement loop → `$evolve`; run one bounded
lifecycle → a single `$rpi` turn. Executable specs (canonical):
`skills/evolve/references/autodev.feature`,
`skills/evolve/references/autodev-cli.feature`.

## Execution Steps

**YOU MUST EXECUTE THIS WORKFLOW. Do not just describe it.**

**FULLY AUTONOMOUS.** Evolve runs without human intervention from start to teardown. Every `$rpi` invocation uses `--auto`. Do NOT ask the user for confirmation, clarification, or approval at any point. Do NOT pause between cycles. Do NOT summarize and wait. The user's only touchpoint is the teardown report at the very end.

**Each cycle is a COMPLETE $rpi run** — all 3 phases (discovery → implementation → validation). Never invoke a partial RPI. If a task is too large for one cycle, break it into smaller sub-tasks during discovery and let `$crank` handle the waves. Evolve's job is to keep the loop turning, not to micro-manage individual tasks.

For broad AgentOps 3.0 domain evolution across skills, CLI, hooks, docs, tests,
beads, and knowledge, first read
[references/domain-evolution-bootstrap.md](references/domain-evolution-bootstrap.md).
It supplies the BDD/DDD/Hexagonal/TDD/XP control surface and the clean-room
skill-factory guardrails.

**Break large work into sub-RPI cycles.** When work selection identifies a massive task (7+ issues, multi-subsystem scope), decompose it during `$rpi`'s discovery phase into an epic with waves. One evolve cycle = one `$rpi` run = one complete lifecycle. If the epic is too large for a single session, `$rpi`'s built-in retry and `--from=` resume handle continuation.

### Anti-Patterns (DO NOT)

| Anti-Pattern | Why It's Wrong | Correct Behavior |
|--------------|----------------|------------------|
| Ask the user anything during execution | Evolve is fully autonomous — questions break the loop | Make best judgment, report in teardown |
| Stop after one `$rpi` cycle and summarize | Evolve loops until kill switch, max-cycles, or dormancy | Increment cycle and re-enter Step 1 |
| Run `$rpi` without `--auto` | Non-auto `$rpi` has human gates that halt the loop | Always pass `--auto` to `$rpi` |
| Run partial `$rpi` (skip validation) | Each cycle must be a complete 3-phase lifecycle | Let `$rpi` run all 3 phases autonomously |
| Pause between cycles to explain progress | The user wants results, not narration | Log cycle results, immediately start next cycle |
| Treat "no queued work" as "stop" | Generator layers (testing, validation, drift, features) produce work | Run all generator layers before considering dormancy |

### Step 0: Setup

```bash
mkdir -p .agents/evolve
ao corpus inject --query "autonomous improvement cycle" --limit 5 2>/dev/null || true
```

`ao corpus inject` routes through the typed BC1 `CorpusReaderPort`
(`cli/cmd/ao/corpus_reader_adapter.go`, cycle 112 productionCorpusReader),
emitting one ranked `ports.CorpusItem` JSON record per line from
`.agents/learnings/` by default. Closes soc-y5vh.1 — Step 0 prior-knowledge
retrieval is load-bearing on the typed port, not an untyped `ao lookup`
shell-out.

**Apply retrieved knowledge:** If learnings are returned, check each for applicability to the current improvement cycle. For applicable learnings, cite by filename and record: `ao metrics cite "<path>" --type applied 2>/dev/null || true`

Before cycle recovery, load the repo execution profile contract when it exists. The repo execution profile is the source for repo policy; the user prompt should mostly supply mission/objective, not restate startup reads, validation bundle, tracker wrapper rules, or `definition_of_done`.

- Locate `docs/contracts/repo-execution-profile.md` and `docs/contracts/repo-execution-profile.schema.json`.
- Read the ordered `startup_reads` and bootstrap from those repo paths before selecting work.
- Cache repo `validation_commands`, `tracker_commands`, and `definition_of_done` into session state.
- If the repo execution profile is present but missing required fields, stop or downgrade with an explicit warning before cycle 1. Do not silently invent repo policy.

Then load the repo-local autodev program contract when it exists. The execution profile remains the repo bootstrap and landing-policy layer; `PROGRAM.md` or `AUTODEV.md` is the repo-local execution layer for the current improvement loop.

- Locate `PROGRAM.md` and `AUTODEV.md`. `PROGRAM.md` takes precedence.
- Read the resolved program before cycle recovery and cache `program_path`, `mutable_scope`, `immutable_scope`, `validation_commands`, `decision_policy`, and `stop_conditions` into session state.
- If the program file exists but is structurally invalid, stop or downgrade with an explicit warning before cycle 1. Do not silently ignore a broken operator contract.
- When a program contract exists, prefer work that can land wholly inside mutable scope. Do not silently widen scope around immutable files.

Recover cycle number, queue/generator streaks, and the last claimed work item from disk (survives context compaction):
```bash
if [ -f .agents/evolve/cycle-history.jsonl ]; then
  CYCLE=$(( $(tail -1 .agents/evolve/cycle-history.jsonl | jq -r '.cycle // 0') + 1 ))
else
  CYCLE=1
fi
SESSION_START_SHA=$(git rev-parse HEAD)

# Recover idle streak from disk (not in-memory — survives compaction)
# Portable: forward-scanning awk counts trailing idle run without tac (unavailable on stock macOS)
IDLE_STREAK=$(awk '/"result"\s*:\s*"(idle|unchanged)"/{streak++; next} {streak=0} END{print streak+0}' \
  .agents/evolve/cycle-history.jsonl 2>/dev/null)

PRODUCTIVE_THIS_SESSION=0

# Recover generator state and queue claim state
if [ -f .agents/evolve/session-state.json ]; then
  GENERATOR_EMPTY_STREAK=$(jq -r '.generator_empty_streak // 0' .agents/evolve/session-state.json 2>/dev/null || echo 0)
  LAST_SELECTED_SOURCE=$(jq -r '.last_selected_source // empty' .agents/evolve/session-state.json 2>/dev/null || true)
  CLAIMED_WORK_REF=$(jq -r '.claimed_work.ref // empty' .agents/evolve/session-state.json 2>/dev/null || true)
else
  GENERATOR_EMPTY_STREAK=0
  LAST_SELECTED_SOURCE=""
  CLAIMED_WORK_REF=""
fi

# Circuit breaker: stop if last productive cycle was >60 minutes ago
LAST_PRODUCTIVE_TS=$(grep -v '"idle"\|"unchanged"' .agents/evolve/cycle-history.jsonl 2>/dev/null \
  | tail -1 | jq -r '.timestamp // empty')
# Time-based circuit breaker
if [ -n "$LAST_PRODUCTIVE_TS" ]; then
  NOW_EPOCH=$(date +%s)
  LAST_EPOCH=$(date -j -f "%Y-%m-%dT%H:%M:%S%z" "$LAST_PRODUCTIVE_TS" +%s 2>/dev/null \
    || date -d "$LAST_PRODUCTIVE_TS" +%s 2>/dev/null || echo 0)
  if [ "$LAST_EPOCH" -gt 1000000000 ] && [ $((NOW_EPOCH - LAST_EPOCH)) -ge 3600 ]; then
    echo "CIRCUIT BREAKER: No productive work in 60+ minutes. Stopping."
    # go to Teardown
  fi
fi

# Track oscillating goals (improved→fail→improved→fail) to avoid burning cycles
declare -A QUARANTINED_GOALS  # goal_id → true if oscillation count >= 3

# Pre-populate quarantine list from cycle history (lightweight local scan)
if [ -f .agents/evolve/cycle-history.jsonl ]; then
  while IFS= read -r goal; do
    QUARANTINED_GOALS[$goal]=true
    echo "Quarantined oscillating goal: $goal"
  done < <(
    jq -r '.target' .agents/evolve/cycle-history.jsonl 2>/dev/null \
    | awk '{
        if (prev != "" && prev != $0) transitions[$0]++
        prev = $0
      }
      END {
        for (g in transitions) if (transitions[g] >= 3) print g
      }'
  )
fi
```

Parse flags: `--max-cycles=N` (default unlimited), `--dry-run`, `--beads-only`, `--skip-baseline`, `--quality`, `--compile`.

Track cycle-level execution state:

```text
evolve_state = {
  cycle: <current cycle number>,
  mode: <standard|quality|beads-only>,
  test_first: <true by default; false only when --no-test-first>,
  repo_profile_path: <docs/contracts/repo-execution-profile.md or null>,
  startup_reads: <ordered repo bootstrap paths>,
  validation_commands: <ordered repo validation bundle>,
  tracker_commands: <repo tracker shell wrappers>,
  definition_of_done: <repo stop predicates>,
  program_path: <PROGRAM.md|AUTODEV.md or null>,
  program_mutable_scope: <declared mutable paths/globs>,
  program_immutable_scope: <declared immutable paths/globs>,
  program_validation_commands: <ordered program validation bundle>,
  program_decision_policy: <ordered keep/revert rules>,
  program_stop_conditions: <ordered cycle done criteria>,
  generator_empty_streak: <consecutive passes where all generator layers returned nothing>,
  last_selected_source: <harvested|beads|goal|directive|testing|validation|bug-hunt|drift|feature>,
  claimed_work: <null or work reference being worked>,
  queue_refresh_count: <incremented after every $rpi cycle>
}
```

Persist `evolve_state` to `.agents/evolve/session-state.json` at each cycle boundary, after work claims, after release/finalize, and during teardown. `cycle-history.jsonl` remains the canonical cycle ledger; `session-state.json` carries resume-only state that has not yet earned a committed cycle entry. Both files are **local-only** (the nested `.agents/.gitignore` denies all paths) — record durable milestones in commit messages too. See `references/cycle-history.md` for full local-only semantics.

### Step 0.2: Compile Warmup (--compile only)

Skip if `--compile` was not passed or if `--dry-run`.

Run the mechanical half of the Compile cycle to surface fresh signal before the first evolve cycle:

```bash
mkdir -p .agents/mine .agents/defrag
echo "Compile warmup: mining signal..."
ao mine --since 26h --quiet 2>/dev/null || echo "(ao mine unavailable — skipping)"

echo "Compile warmup: defrag sweep..."
ao defrag --prune --dedup --quiet 2>/dev/null || echo "(ao defrag unavailable — skipping)"
```

Then read `.agents/mine/latest.json` and `.agents/defrag/latest.json` and note (in 1-2 sentences each):
- Any **orphaned research** files that look relevant to current goals
- Any **code hotspots** (high-CC functions with recent edits) that may be the root cause of failing goals
- Any **duplicate learnings** merged by defrag — context on what's been cleaned up

These notes inform work selection throughout the evolve session. Store them in a session variable (in-memory), not a file.

### Step 0.5: Baseline (first run only)

Skip if `--skip-baseline` or `--beads-only` or baseline already exists.

The `$evolve` skill captures this automatically before entering the RPI loop. It hashes
the active GOALS.md or GOALS.yaml file to an era ID, then writes a snapshot
under `.agents/evolve/fitness-baselines/goals-<hash>/` if that era directory
does not already contain a JSON snapshot.

For manual recovery or one-off capture:

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

### Step 1: Kill Switch Check

Run at the TOP of every cycle:

```bash
CYCLE_START_SHA=$(git rev-parse HEAD)
# Stale-kill auto-expire (closes F5 from 2026-05-18 post-mortem).
# A KILL/STOP file older than EVOLVE_KILL_TTL_DAYS (default 7) is treated as
# stale and surfaced loudly; the loop proceeds. Re-touch to keep blocking.
EVOLVE_KILL_TTL_DAYS="${EVOLVE_KILL_TTL_DAYS:-7}"
check_stale_kill() {
    local path="$1" ttl_days="$2"
    [ -f "$path" ] || return 1
    local mtime_epoch now_epoch age_days
    mtime_epoch=$(stat -c %Y "$path" 2>/dev/null || stat -f %m "$path" 2>/dev/null)
    now_epoch=$(date +%s)
    age_days=$(( (now_epoch - mtime_epoch) / 86400 ))
    if [ "$age_days" -gt "$ttl_days" ]; then
        echo "WARN: ${path} is ${age_days} days old (> ${ttl_days}); STALE, proceeding." >&2
        return 1
    fi
    return 0
}
if check_stale_kill ~/.config/evolve/KILL "$EVOLVE_KILL_TTL_DAYS"; then
    echo "KILL: $(cat ~/.config/evolve/KILL)"; exit 0
fi
if check_stale_kill .agents/evolve/STOP "$EVOLVE_KILL_TTL_DAYS"; then
    echo "STOP: $(cat .agents/evolve/STOP 2>/dev/null)"; exit 0
fi
```

### Step 2: Measure Fitness

Skip if `--beads-only`.

```bash
bash scripts/evolve-measure-fitness.sh \
  --output .agents/evolve/fitness-latest.json \
  --timeout 60 \
  --total-timeout 75
```

**Do NOT write per-cycle `fitness-{N}-pre.json` files.** The rolling file is sufficient for work selection and regression detection.

This writes a fitness snapshot to `.agents/evolve/` atomically via a temp file plus JSON validation. The AgentOps CLI is required for fitness measurement because the measurement wrapper shells out to `ao goals measure`. If measurement exceeds the whole-command bound or returns invalid JSON, the wrapper fails without clobbering the previous rolling snapshot.

### Step 3: Select Work

Selection is a ladder, not a one-shot check. After every productive cycle, return to the TOP of this step and re-read the queue before considering dormancy.

When a repo-local program contract exists, apply a scope filter before Step 4:
- candidate work that clearly requires immutable-scope edits is not eligible for direct execution
- prefer harvested, beads, goals, and generated work that can plausibly land within mutable scope
- if the selected item is inherently out of scope, escalate it or convert it into durable follow-up work instead of invoking `$rpi` and hoping discovery widens scope

**Step 3.1: Harvested work first**

Read `.agents/rpi/next-work.jsonl` and pick the highest-value unconsumed item for this repo. Prefer:
- exact repo match before `*`, then legacy unscoped entries
- already-harvested concrete implementation work before process work
- higher severity before lower severity

When evolve picks a harvested item, **claim it first**:
- set `claim_status: "in_progress"`
- set `claimed_by: "evolve:cycle-N"`
- set `claimed_at: "<timestamp>"`
- keep `consumed: false` until the `$rpi` cycle and regression gate both succeed

If the cycle fails, regresses, or is interrupted before success, release the claim and leave the item available for the next cycle.

**Step 3.2: Open ready beads**

If no harvested item is ready, check `br ready`. Pick the highest-priority unblocked issue.

**Step 3.3: Failing goals and directive gaps** (skip if `--beads-only`)

First assess directives, then goals:
- top-priority directive gap from `ao goals measure --directives`
- highest-weight failing goals (skip quarantined oscillators)
- lower-weight failing goals

This step exists even when all queued work is empty. Goals are the third source, not the stop condition.

```bash
DIRECTIVES=$(ao goals measure --directives 2>/dev/null)
FAILING=$(jq -r '.goals[] | select(.result=="fail") | .id' .agents/evolve/fitness-latest.json | head -1)
```

**Oscillation check:** Before working a failing goal, check if it has oscillated (improved→fail transitions ≥ 3 times in cycle-history.jsonl). If so, quarantine it and try the next failing goal. See `references/oscillation.md`.
```bash
# Count improved→fail transitions for this goal
OSC_COUNT=$(jq -r "select(.target==\"$FAILING\") | .result" .agents/evolve/cycle-history.jsonl \
  | awk 'prev=="improved" && $0=="fail" {count++} {prev=$0} END {print count+0}')
if [ "$OSC_COUNT" -ge 3 ]; then
  QUARANTINED_GOALS[$FAILING]=true
  echo "{\"cycle\":${CYCLE},\"target\":\"${FAILING}\",\"result\":\"quarantined\",\"oscillations\":${OSC_COUNT},\"timestamp\":\"$(date -Iseconds)\"}" >> .agents/evolve/cycle-history.jsonl
fi
```

**Step 3.4: Testing improvements**

Work generators for concrete improvement signals:
- `$test --coverage` — find test gaps and generate candidates
- `$refactor --sweep` — find complexity debt and refactor targets
- `$security audit` — check dependency health, vulnerabilities, and license compliance
- `$perf profile` — identify performance debt and optimization opportunities

When queues and goals are empty, generate concrete testing work instead of idling:
- find packages/files with thin or missing tests
- look for missing regression tests around recent bug-fix paths
- identify flaky or absent headless/runtime smokes

Convert any real finding into durable work:
- add a bead when the work needs tracked backlog ownership, or
- append a queue item under the shared next-work contract when it should flow directly back into `$rpi`

**Step 3.5: Validation tightening and bug-hunt passes**

If testing improvement generation returns nothing, run bug-hunt and validation sweeps:
- missing validation gates
- weak lint/contract coverage
- bug-hunt style audits for risky areas
- stale assumptions between docs, contracts, and runtime truth

Again: convert findings into beads or queue items, then immediately select the highest-priority result and continue.

**Step 3.6: Drift / hotspot / dead-code mining**

If the prior generators are empty, mine for:
- complexity hotspots
- stale TODO/FIXME markers
- dead code
- stale docs
- stale research
- drift between generated artifacts and source-of-truth files

Do not stop here. Normalize findings into tracked work and continue.

**Step 3.7: Feature suggestions**

If all concrete remediation layers are empty, propose one or more specific feature ideas grounded in the repo purpose, write them as durable work, and continue:
- create a bead when the feature needs review/backlog treatment
- or append a queue item with `source: "feature-suggestion"` when it is ready for the next `$rpi` cycle

**Quality mode (`--quality`)** — inverted cascade (findings before directives):

Step 3.0q: Unconsumed high-severity post-mortem findings:
```bash
HIGH=$(jq -r 'select(.consumed==false) | .items[] | select(.severity=="high") | .title' \
  .agents/rpi/next-work.jsonl 2>/dev/null | head -1)
```

Step 3.1q: Unconsumed medium-severity findings.

Step 3.2q: Open ready beads.

Step 3.3q: Emergency gates (weight >= 5) and top directive gaps.

Step 3.4q: Testing improvements.

Step 3.5q: Validation tightening / bug-hunt / drift mining.

Step 3.6q: Feature suggestions.

This inverts the standard cascade only at the top of the ladder: findings BEFORE goals and directives. It does NOT skip the generator layers.

When evolve picks a finding, claim it first in next-work.jsonl:
- Set `claim_status: "in_progress"`, `claimed_by: "evolve-quality:cycle-N"`, `claimed_at: "<timestamp>"`
- Set `consumed: true` only after the $rpi cycle and regression gate succeed
- If the $rpi cycle fails (regression), clear the claim and leave `consumed: false`

See `references/quality-mode.md` for scoring and full details.

**Nothing found?** HARD GATE — dormancy only when ALL sources empty (soc-5qit):

```bash
READY_BEADS=$(BEADS_DIR="$(ao beads dir)" br ready --json 2>/dev/null | jq -r 'length // 0' 2>/dev/null || echo 0)
HARVESTED=$(jq -r 'select(.consumed==false) | .severity' .agents/rpi/next-work.jsonl 2>/dev/null | wc -l | tr -d ' ')
FAILING_GOALS=$(jq -r '.goals[] | select(.result=="fail") | .id' .agents/evolve/fitness-latest.json 2>/dev/null | wc -l | tr -d ' ')

if [ "$READY_BEADS" -gt 0 ] || [ "$HARVESTED" -gt 0 ] || [ "$FAILING_GOALS" -gt 0 ]; then
  continue  # work exists — loop back to Step 3 (agile invariant)
fi
IDLE_STREAK=$(awk '/"result"\s*:\s*"(idle|unchanged)"/{streak++; next} {streak=0} END{print streak+0}' .agents/evolve/cycle-history.jsonl 2>/dev/null)
if [ "$GENERATOR_EMPTY_STREAK" -ge 2 ] && [ "$IDLE_STREAK" -ge 2 ]; then
  echo "Genuine stagnation: all sources empty x3."
fi
```

**Agile invariant (soc-5qit):** `br ready ≥ 1` ⇒ loop NEVER stops. Only path to stagnation-STOP is fully empty backlog + dry generators. Context exhaustion → write non-sticky `.agents/evolve/HANDOFF`, exit turn; next fire (compacted/fresh) clears HANDOFF in Step 1 and continues.

If the work layers were empty but a generator pass has not been exhausted 3 times yet, persist the new generator streak in `session-state.json` and loop back to Step 1. Empty pre-cycle work sources are not a stop reason by themselves.

A cycle is idle only if NO work source returned actionable work and every generator layer also came up empty. A cycle that targeted an oscillating goal and skipped it counts as idle only after the remaining ladder was exhausted.

If `--dry-run`: report what would be worked on and go to Teardown.

### Step 4: Execute

Primary engine: use `$rpi` for any implementation-quality work. Every `$rpi` call MUST run all 3 phases (discovery → implementation → validation). `$implement` and `$crank` are allowed only when a bead already contains execution-ready scope and skipping discovery is clearly the better path.

If a repo-local `PROGRAM.md` contract is active, `$rpi` will load it automatically. `$evolve` must compose with that behavior, not bypass it:
- Do not select work that is obviously outside mutable scope.
- If a bead or goal would require edits under immutable scope, escalate it or convert it into durable follow-up work instead of launching `$rpi`.
- When work is plausibly in scope but still uncertain, let `$rpi` discovery validate the fit and surface a scope escape explicitly.

For a **harvested item, failing goal, directive gap, testing improvement, validation tightening task, bug-hunt result, drift finding, or feature suggestion**:
```
Invoke $rpi "{normalized work title}" --auto --max-cycles=1
```

For a **beads issue**:
```
Prefer: $rpi "Land {issue_id}: {title}" --auto --max-cycles=1
Fallback: $implement {issue_id}
```
Or for an epic with children: `Invoke $crank {epic_id}`.

**CRITICAL:** `$rpi --auto` runs hands-free through all 3 phases. Do NOT intervene, ask questions, or pause between phases. Wait for `$rpi` to return its completion marker, then proceed to Step 5.

If Step 3 created durable work instead of executing it immediately, re-enter Step 3 and let the newly-created bead item win through the normal selection order.

### Step 5: Regression Gate

After execution, run the project build+test bundle. If the repo execution profile declared `validation_commands`, run them. If a repo-local program contract exists, run its `validation_commands` too, de-duplicated and in declared order after the repo bootstrap checks.

```bash
# Detect and run project build+test
if [ -f Makefile ]; then make test
elif [ -f package.json ]; then npm test
elif [ -f go.mod ]; then go build ./... && go vet ./... && go test ./... -count=1 -timeout 120s
elif [ -f Cargo.toml ]; then cargo build && cargo test
elif [ -f pyproject.toml ] || [ -f setup.py ]; then python -m pytest
else echo "No recognized build system found"; fi

# Cross-cutting constraint check (catches wiring regressions)
if [ -f scripts/check-wiring-closure.sh ]; then
  bash scripts/check-wiring-closure.sh
else
  echo "WARNING: scripts/check-wiring-closure.sh not found — skipping wiring check"
fi
```

Use the program contract's `decision_policy` as the first keep/revert rule set for the cycle:
- if the cycle breached immutable scope, treat it as regressed
- if program validation commands fail, treat it as regressed
- if the decision policy declares a revert rule that fired, revert before consuming claimed work or advancing the queue

Treat program `stop_conditions` as per-cycle done criteria. Do not mark claimed work consumed, completed, or productive until both the stop conditions and the regression gate pass.

If not `--beads-only`, also re-measure to produce a post-cycle snapshot:
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

Work finalization after the regression gate:
- **success:** finalize any claimed work item with `consumed: true`, `consumed_by`, and `consumed_at`; clear transient claim fields
- **failure/regression:** clear `claim_status`, `claimed_by`, and `claimed_at`; keep `consumed: false`; record the release in `session-state.json`

After the cycle's `$post-mortem` finishes, immediately re-read `.agents/rpi/next-work.jsonl` before selecting the next item. Never assume the queue state from before the cycle.

### Step 6: Log Cycle + Commit

Two paths: productive cycles get committed, idle cycles are local-only.

**PRODUCTIVE cycles** (result is improved, regressed, or harvested):

```bash
# Quality mode: compute quality_score BEFORE writing the JSONL entry
QUALITY_SCORE_ARGS=()
if [ "$QUALITY_MODE" = "true" ]; then
  REMAINING_HIGH=$(jq -r 'select(.consumed==false) | .items[] | select(.severity=="high")' \
    .agents/rpi/next-work.jsonl 2>/dev/null | wc -l | tr -d ' ')
  REMAINING_MEDIUM=$(jq -r 'select(.consumed==false) | .items[] | select(.severity=="medium")' \
    .agents/rpi/next-work.jsonl 2>/dev/null | wc -l | tr -d ' ')
  QUALITY_SCORE=$((100 - (REMAINING_HIGH * 10) - (REMAINING_MEDIUM * 3)))
  [ "$QUALITY_SCORE" -lt 0 ] && QUALITY_SCORE=0
  QUALITY_SCORE_ARGS=(--quality-score "$QUALITY_SCORE")
fi

ENTRY_JSON="$(
  bash scripts/evolve-log-cycle.sh \
    --cycle "$CYCLE" \
    --target "$TARGET" \
    --result "$OUTCOME" \
    --canonical-sha "$(git rev-parse --short HEAD)" \
    --cycle-start-sha "$CYCLE_START_SHA" \
    --goals-passing "$PASSING" \
    --goals-total "$TOTAL" \
    "${QUALITY_SCORE_ARGS[@]}"
)"
OUTCOME="$(printf '%s\n' "$ENTRY_JSON" | jq -r '.result')"
REAL_CHANGES=$(git diff --name-only "${CYCLE_START_SHA}..HEAD" -- ':!.agents/**' ':!GOALS.yaml' ':!GOALS.md' \
  2>/dev/null | wc -l | tr -d ' ')

# Telemetry
bash scripts/log-telemetry.sh evolve cycle-complete cycle=${CYCLE} goal=${TARGET} outcome=${OUTCOME} 2>/dev/null || true

if [ "$OUTCOME" = "unchanged" ]; then
  # No-delta cycle: leave local-only so history stays honest and stagnation logic can see it.
  :
elif [ "$REAL_CHANGES" -gt 0 ]; then
  # Full commit: real code was changed
  git add .agents/evolve/cycle-history.jsonl
  git commit -m "evolve: cycle ${CYCLE} -- ${TARGET} ${OUTCOME}"
else
  # Productive cycle with non-agent repo delta already committed by a sub-skill:
  # stage the ledger but do not create a standalone follow-up commit.
  git add .agents/evolve/cycle-history.jsonl
fi

PRODUCTIVE_THIS_SESSION=$((PRODUCTIVE_THIS_SESSION + 1))
```

**IDLE cycles** (nothing found even after generator layers):

```bash
bash scripts/evolve-log-cycle.sh \
  --cycle "$CYCLE" \
  --target "idle" \
  --result "unchanged" >/dev/null
# No git add, no git commit, no fitness snapshot write
```

**Record the XP/BDD/TDD trace.** When a cycle worked a product or goal-backed
gap, pass `--trace-json <path|inline|->` to `evolve-log-cycle.sh` (or
`ao loop append --trace-json`) so the cycle records the continuous-evolution
kernel — goal hypothesis → selected gap → Gherkin scenario → first failing
proof → red/green evidence → refactor note → validation evidence → ratchet
action → goal reshape — and a reviewer can reconstruct the cycle without the
transcript. A trivial one-shot cycle records a `trace.exemption_reason`
instead of carrying false BDD/TDD ceremony. Trace completeness is advisory,
never a gate. See `references/cycle-history.md` ("XP/BDD/TDD Evidence Trace").

### Step 7: Loop or Stop

```bash
while true; do
  # Step 1 .. Step 6
  # Stop if kill switch, max-cycles, or a real safety breaker triggers
  # Otherwise increment cycle and re-enter selection
  CYCLE=$((CYCLE + 1))
done
```

**Convergence STOP.** Before re-entering the loop, evaluate the terminal
predicate through the typed BC3 `ConvergenceCheckPort` (soc-y5vh.8):

```bash
ao loop converged --green-streak "$STREAK" --unconsumed-high-medium "$HM" --fitness-baseline
# emits {converged, ci_green_streak, unconsumed_high_medium, fitness_baseline_captured, reasons}
```

Branch on `.converged` (not hand-parsed JSON). When true (default: CI green streak
≥ 3, unconsumed HIGH+MEDIUM ≤ 1, fitness baseline captured), break the loop and run
Teardown. When a cycle edits an evolve `SKILL.md`, record the falsifiable claim via
`ao loop hypothesis append` (read back with `... list`).
See `references/convergence-mechanics.md`.

**Mandatory checkpoint #6 — session-PR threshold (NOT terminal, gates next cycle):** at `session_pr_count >= 5` (soc-waxr default), invoke `$post-mortem --deep`, wait for verdict file. PASS → continue. WARN → continue with caveat in next cycle's `notes`. FAIL or non-convergence → write STOP citing the verdict path. Agent MUST NOT self-grade or self-write STOP. Full procedure: `references/postmortem-checkpoint.md` (soc-n75z).

Push only when productive work has accumulated:
```bash
if [ $((PRODUCTIVE_THIS_SESSION % 5)) -eq 0 ] && [ "$PRODUCTIVE_THIS_SESSION" -gt 0 ]; then
  git push
fi
```

### Teardown

1. Commit any staged but uncommitted cycle-history.jsonl (from artifact-only cycles):
```bash
if git diff --cached --name-only | grep -q cycle-history.jsonl; then
  git commit -m "evolve: session teardown -- artifact-only cycles logged"
fi
```
2. Run `$post-mortem "evolve session: ${CYCLE} cycles"` to harvest learnings.
3. Push only if unpushed commits exist:
```bash
UNPUSHED=$(git log origin/main..HEAD --oneline 2>/dev/null | wc -l)
[ "$UNPUSHED" -gt 0 ] && git push
```
4. **Release-context teardown (MANDATORY when branch is release-shaped):**

   When the current branch matches `release/*`, `v*-prep`, `v*-evolve-run`, or `v\d+\.\d+*`, the teardown report MUST NOT recommend `$release` as the next step. Instead, emit the explicit pre-release checklist below — the operator must run these AND confirm green before tagging:

   ```
   ## Pre-release checklist — REQUIRED before $release

   Per-cycle --fast pre-push and ao goals measure ≠ release readiness.
   Operator MUST run and confirm green:

     [ ] 1. Regenerate CLI reference if any cobra command/flag changed:
            bash scripts/generate-cli-reference.sh
            git diff cli/docs/COMMANDS.md   # commit if non-empty

     [ ] 2. Full pre-push gate (NOT --fast):
            bash scripts/pre-push-gate.sh

     [ ] 3. Release-readiness gate:
            bash scripts/ci-local-release.sh

     [ ] 4. (Recommended) Smoke $evolve --quick --max-cycles=1 --dry-run if
            BC port wire-ups changed.

   Only after [1]–[3] pass: $release <version>
   ```

   The handoff artifact (e.g., `.agents/runs/<release>/READY-TO-TAG.md`) MUST contain this checklist verbatim, unchecked. "Ready to tag" means the boxes are checked, not that the loop ran cleanly.

5. Report summary:

```
## $evolve Complete
Cycles: N | Productive: X | Regressed: Y (reverted) | Idle: Z
Stop reason: stagnation | circuit-breaker | max-cycles | kill-switch
```

In quality mode, the report includes additional fields:
```
## $evolve Complete (quality mode)
Cycles: N | Findings resolved: X | Goals fixed: Y | Idle: Z
Quality score: start → end (delta)
Remaining unconsumed: H high, M medium
Stop reason: stagnation | circuit-breaker | max-cycles | kill-switch
```

## Examples

Per-flag behavior is in the Flags table and the invocation block above. Bare
`$evolve` runs the overnight flow beads → harvested → goals → testing → bug hunt
→ feature suggestion before dormancy. See `references/examples.md` for detailed
walkthroughs.

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Loop exits immediately | Remove `~/.config/evolve/KILL` or `.agents/evolve/STOP` |
| Stagnation after repeated empty passes | Queue layers and producer layers were empty across multiple passes — dormancy is the fallback outcome |
| `ao goals measure` hangs | Use `--timeout 30 --total-timeout 75` or `--beads-only` to skip |
| Regression gate reverts | Review reverted changes, narrow scope, re-run; claimed work items must be released back to available state |

See `references/cycle-history.md` for troubleshooting.

## Output Specification

**Format:** a per-cycle markdown summary to stdout (goals fixed, fitness delta, result); machine-readable cycle records.
**Files:** appends `.agents/evolve/cycle-history.jsonl`; writes `.agents/evolve/fitness-latest.json` and `.agents/evolve/session-state.json`; honors control files `.agents/evolve/{STOP,DORMANT,HANDOFF}`.
**Exit signal:** the cycle result (improved / no-change / blocked); resume a paused cycle via `$evolve --resume`.

## References

- [cycle-history](references/cycle-history.md) — JSONL format, recovery, kill switch
- [compounding](references/compounding.md) — Flywheel and work harvesting
- [goals-schema](references/goals-schema.md) — GOALS.yaml format and metrics
- [parallel-execution](references/parallel-execution.md) — Parallel $swarm architecture
- [teardown](references/teardown.md) — Trajectory + session summary
- [examples](references/examples.md) — Examples
- [artifacts](references/artifacts.md) — Generated files registry
- [oscillation](references/oscillation.md) — Detection and quarantine
- [quality-mode](references/quality-mode.md) — Scoring, cascade, artifacts
- [convergence-mechanics](references/convergence-mechanics.md) — Convergence semantics
- [postmortem-checkpoint](references/postmortem-checkpoint.md) — Checkpoint procedure
- [autonomous-execution](references/autonomous-execution.md) — Loop cadence; handoff re-arms

## See Also

- `skills/rpi/SKILL.md` — Full lifecycle orchestrator, called per cycle
- `skills/crank/SKILL.md` — Epic execution for beads epics
- `docs/contracts/autodev-program.md` — Bounded autonomous development contract
- `GOALS.yaml` — Fitness goals
- [test](../test/SKILL.md) — Test generation
- [refactor](../refactor/SKILL.md) — Safe, verified refactoring
- [security](../security/SKILL.md) — Dependency audit + vuln scanning (absorbs deps)
- [perf](../validate/SKILL.md) — Performance profiling and benchmarking

<!-- Lifecycle integration wired: 2026-03-28. See skills/evolve/SKILL.md for canonical -->
