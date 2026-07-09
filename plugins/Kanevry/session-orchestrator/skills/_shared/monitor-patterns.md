# Monitor Filter Patterns

> Vetted Monitor-tool snippets for the recurring observation points in the
> session-orchestrator workflow. Each snippet ships with the description
> string, recommended timeout / persistent flag, and an explicit failure
> coverage note (per the **silence-is-not-success** rule from
> `.claude/rules/loop-and-monitor.md`).

## Why this file exists

Anthropic recommends `Monitor` over `/loop` for any stream-able event
(https://code.claude.com/docs/en/scheduled-tasks). The Monitor tool turns
each stdout line into a notification, avoiding poll-token cost. But a
naïve filter that matches only the success marker reads identical to a
crash — silent. The snippets below are calibrated to emit on **every
terminal state**, not just the happy path.

When in doubt, copy a snippet, adjust the path or repo, and arm it. Do
not invent new filters from scratch unless you have re-derived the
coverage check.

---

## Pattern 1 — GitLab pipeline + GitHub mirror sync (post-push)

**When.** After `git push origin main` from `commands/close.md` Phase 6.
Watches the GitLab pipeline through to a terminal status, then prints
the GitHub mirror's main-branch SHA so the operator can confirm parity.

**Description.** `pipeline + mirror sync after push`

**timeout_ms.** `1800000` (30 min — most pipelines finish well inside)

**persistent.** `false`

```bash
prev=""
while true; do
  s=$(glab ci status --pipeline-id LATEST --output json 2>/dev/null || echo '[]')
  cur=$(jq -r '.[] | select(.status!="running" and .status!="pending") | "\(.name): \(.status)"' <<<"$s" 2>/dev/null | sort)
  comm -13 <(echo "$prev") <(echo "$cur")
  prev=$cur
  jq -e 'all(.status=="success" or .status=="failed" or .status=="canceled" or .status=="skipped")' <<<"$s" >/dev/null 2>&1 && {
    sha=$(gh api repos/Kanevry/session-orchestrator/commits/main --jq '.sha' 2>/dev/null || echo "(mirror unreachable)")
    echo "GitHub mirror main: $sha"
    break
  }
  sleep 30
done
```

**Coverage.** Emits a line for each job transitioning out of `running` /
`pending`. Terminates when **all** jobs are in a terminal state (`success`,
`failed`, `canceled`, `skipped`). The final line prints the GitHub mirror
SHA — silence at the end means glab JSON parsing failed (the `||` fallbacks
prevent the whole loop from dying).

---

## Pattern 2 — Long-running test suite (`npm test` ≥ 2700 cases)

**When.** During a deep session's Quality wave when the suite takes long
enough that synchronous stdout is impractical. Monitor surfaces progress
and any failure signature without re-running the suite.

**Description.** `vitest progress + failure signatures`

**timeout_ms.** `1200000` (20 min)

**persistent.** `false`

```bash
# Pre-req: npm test 2>&1 | tee vitest.log was started in another terminal
tail -f vitest.log | grep -E --line-buffered \
  "Test Files.*passed|Test Files.*failed|Tests.*failed|FAIL |PASS |Traceback|Error:|AssertionError|UnhandledRejection|OOM|Killed|Aborted"
```

**Coverage.** Matches both success markers (`Test Files … passed`,
`PASS `) and the full failure surface: vitest's own
`FAIL ` / `Tests.*failed`, Node's `Traceback` / `AssertionError` /
`UnhandledRejection`, and OS-level kill signatures (`OOM`, `Killed`,
`Aborted`). A crashed worker produces at least one of the failure tokens
within 200 ms — never silent.

---

## Pattern 3 — `autopilot.jsonl` live read-out

**When.** Operator runs `/autopilot --headless` in terminal A and wants
a live dashboard in terminal B without building telemetry tooling.

**Description.** `autopilot iteration + kill-switch tail`

**timeout_ms.** `3600000` (1 h, the Monitor max)

**persistent.** `true` (run for the lifetime of the session — autopilot
runs can take hours)

```bash
tail -f .orchestrator/metrics/autopilot.jsonl | jq -r --line-buffered '
  select(.kind == "iteration" or .kind == "kill_switch" or .kind == "loop_end") |
  "\(.timestamp) iter=\(.iteration // "—") mode=\(.mode // "—") status=\(.status // "—") kill=\(.kill_switch // "none")"
'
```

**Coverage.** Emits on three event kinds: per-iteration progress,
kill-switch firings (the ten tracked in
`scripts/lib/autopilot/kill-switches.mjs`), and the loop-end record. A
silent autopilot run means autopilot is not actually writing to the
JSONL — that itself is a signal worth surfacing manually.

**Detachment seam (Spike #640).** A headless autopilot run detached via
Bash `run_in_background` (`node scripts/autopilot.mjs --headless … &`)
is observed through the returned **task-id**, its **output-file**
(`.../tasks/<id>.output`), and the **completion notification** — never
through `TaskList` / `claude agents`, which lists nested *agent* sessions
only and returns "No tasks found" for a Bash-backgrounded process even
while the run is healthy. This JSONL tail is therefore the **primary live
view** once a run is detached, not a supplementary one. Stop a detached
run with `TaskStop(task_id)`, not the in-session `/tasks`/`/stop` slash
commands.

---

## Pattern 4 — Vault-mirror backlog watcher (long sessions)

**When.** Multi-hour deep session where vault-mirror auto-commit (GH#31)
fires only at session-end / evolve. Surfaces drift before it accumulates.

**Description.** `vault 40-learnings/50-sessions backlog`

**timeout_ms.** `3600000` (1 h)

**persistent.** `true`

```bash
prev=0
while true; do
  n=$(git -C ~/Projects/vault status --short 40-learnings/ 50-sessions/ 2>/dev/null | wc -l | tr -d ' ')
  if [ "$n" != "$prev" ]; then
    echo "$(date -u +%H:%M:%SZ) vault-mirror backlog: $n files"
    prev=$n
  fi
  sleep 1800
done
```

**Coverage.** Emits **only on change** to keep the stream quiet during
idle work. A drop to zero is also reported (e.g. when session-end runs
mirror-commit). Silence = no drift, which is the desired idle state. The
30-min sleep matches the `1200s+` cadence band from
`.claude/rules/loop-and-monitor.md` LM-003.

---

## Pattern 5 — GitHub mirror push verification (secret-scanner safety net)

**When.** After `git push github main` when there is any chance of a
secret-scanner false positive. The plugin hit one on 2026-04-28 (the
`${SCHEMA_DRIFT_TOKEN}` placeholder); silent push success without mirror
parity bit the operator a day later.

**Description.** `github mirror parity vs local main`

**timeout_ms.** `300000` (5 min — push usually completes in seconds; this is the Monitor wall-clock ceiling, **not** the `/loop` cadence band that LM-003 in `.claude/rules/loop-and-monitor.md` warns against)

**persistent.** `false`

```bash
local_sha=$(git rev-parse main)
prev=""
while true; do
  remote_sha=$(gh api repos/Kanevry/session-orchestrator/commits/main --jq '.sha' 2>/dev/null || echo "unreachable")
  if [ "$remote_sha" != "$prev" ]; then
    if [ "$remote_sha" = "$local_sha" ]; then
      echo "mirror parity OK: $remote_sha"
      break
    elif [ "$remote_sha" = "unreachable" ]; then
      echo "$(date -u +%H:%M:%SZ) GitHub API unreachable — retrying"
    else
      echo "$(date -u +%H:%M:%SZ) mirror at $remote_sha (local $local_sha)"
    fi
    prev=$remote_sha
  fi
  sleep 15
done
```

**Coverage.** Emits on every SHA transition and on API unreachability.
Terminates only when remote SHA matches local — never silent. If the
push was actually rejected by GitHub's secret scanner, the remote SHA
never advances and the watcher keeps emitting the stale-SHA line every
15 s until the operator notices.

---

## Pattern — `/tmux-layout` (operator-side persistent visualization)

> Per ADR-0007 + GitLab #561 #562 #563. Opt-in skill, NOT Monitor/loop replacement.

`/tmux-layout` is a sibling primitive to `Monitor` and `/loop` — not a substitute. The three serve genuinely different purposes:

| Primitive | Purpose | When to use |
|---|---|---|
| **`Monitor` tool** | Event-driven stream → coordinator reaction | The coordinator must REACT to each terminal-state line (CI fails → take action, build error → patch). Each stdout line = one coordinator notification. |
| **`/loop` skill** | Periodic coordinator-side polling | "Check vault-staleness every 30 minutes while session runs." Lives inside the coordinator's turn budget. |
| **`/tmux-layout` skill** | Operator-side persistent visualization (4-pane) | The OPERATOR (human) wants to peripherally observe side-channels — STATE.md tail, CI watch, events.jsonl — in a SECOND terminal without coordinator reaction. Pure observability. |

**Key distinction:** `/tmux-layout` visualizes the *outputs* of `Monitor` and `/loop` peripherally so the coordinator pane stays focused on decisions (AUQ-001). It does NOT replace either — Pane 3 of the default layout, for example, runs a `glab ci status` poll-loop equivalent to a `/loop` cadence, but the coordinator does not see those refreshes (the operator does).

**See also:** `docs/adr/0007-tmux-visualization-substrate.md`, `skills/tmux-layout/SKILL.md`.

---

## Anti-patterns

- **`tail -f log | grep "passed"`** — silent on failure. See LM-002.
- **`while true; do …; sleep 0.5; done`** with no change detection —
  spams notifications and gets auto-stopped by Monitor's volume guard.
- **Forgetting `--line-buffered`** in `grep` pipes — pipe buffering
  delays events by minutes, which usually masks itself as "no events".
- **Unbounded `tail -f` for one-shot signals** — use Bash with
  `run_in_background` and an `until` loop instead. See the Monitor tool
  docs.
- **Using Monitor as a `/loop` replacement for periodic scans without a
  stream** (e.g. polling `glab issue list`). Use `/loop` dynamic mode.

---

## See also

- `.claude/rules/loop-and-monitor.md` — primitive routing (Monitor vs
  `/loop` vs Routines)
- `.claude/loop.md` — bare-`/loop` body that delegates to Monitor where
  appropriate
- "Background Detachment Test" (#640; archived in the private Meta-Vault) — empirical
  verification of the Bash `run_in_background` + `TaskStop` detachment
  seam behind Pattern 3
- Anthropic Monitor tool reference (in-session)
