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
  # Fallback carries an `error` key, NOT '{"jobs":[]}': an empty job list is a
  # legitimate glab answer, so it makes a dead CLI read as "pipeline with no jobs"
  # and the watch goes silent (LM-002: silence is not success).
  s=$(glab ci status -R <OWNER>/<REPO> --output json 2>/dev/null || echo '{"error":"glab-ci-status-failed"}')
  # Anything that is not a jobs-carrying object — the sentinel above, or raw
  # non-JSON glab noise — becomes a visible `error:` line, never silence.
  if ! jq -e 'type=="object" and has("jobs")' <<<"$s" >/dev/null 2>&1; then
    echo "$(date -u +%H:%M:%SZ) error: glab ci status unusable — $(printf '%.60s' "$s")"
    sleep 30
    continue
  fi
  cur=$(jq -r '.jobs[] | select(.status!="running" and .status!="pending") | "\(.name): \(.status)"' <<<"$s" 2>/dev/null | sort)
  comm -13 <(echo "$prev") <(echo "$cur")
  prev=$cur
  jq -e '(.jobs|length) > 0 and (.jobs | all(.status=="success" or .status=="failed" or .status=="canceled" or .status=="skipped"))' <<<"$s" >/dev/null 2>&1 && {
    sha=$(gh api repos/Kanevry/session-orchestrator/commits/main --jq '.sha' 2>/dev/null || echo "(mirror unreachable)")
    echo "GitHub mirror main: $sha"
    break
  }
  sleep 30
done
```

**Coverage.** Emits a line for each job transitioning out of `running` /
`pending`, **plus an `error:` line on every iteration where glab produced
nothing usable** — a dead CLI, an auth expiry, or a network drop surfaces as a
notification rather than as absence. Terminates when **all** jobs are in a
terminal state (`success`, `failed`, `canceled`, `skipped`). The final line
prints the GitHub mirror SHA. Silence now carries exactly one meaning: the
pipeline is running and no job has changed state.

If you feed this snippet's output through a downstream `grep -E` filter, the
alternation must include `error` alongside the job-status tokens — the failure
signature is a word, not an absence.

**Probed 2026-08-14 (glab 1.91.0), three corrections — #1022.** The snippet
above was silence-is-not-success in its own right until that date, and each
half failed into the next one's fallback:

- `--pipeline-id LATEST` is not a glab flag on any `ci` subcommand
  (`ERROR Unknown flag`, exit 1), so `$s` was always the `||` fallback. There is
  no replacement — the argument-less form already selects the current branch's
  pipeline. Avoid `--branch=<name>` here: it pins a snapshot taken when the
  monitor was armed.
- The payload is an OBJECT (`{"jobs":[…],"pipeline":{…}}`), so `.[]` raised
  `Cannot index array with string "status"` (jq exit 5) on every real response.
  The accessor is `.jobs[]`.
- `all(…)` over the empty fallback returns **true**, so the loop broke and
  printed the mirror SHA on its FIRST iteration whenever glab hiccuped — a
  transient network error read as "pipeline finished". The `(.jobs|length) > 0`
  guard is what makes the fallback non-terminal; verified by running the
  terminal test against `{"jobs":[]}` (exit 1 = keep watching) versus the old
  form against `[]` (exit 0 = break).

**Amended 2026-08-24 — #1077.** The `{"jobs":[]}` fallback the third bullet
describes was still *indistinguishable from a real answer*: a pipeline can
legitimately report zero jobs, so a dead glab produced a well-formed payload,
no `error`, and no output. Non-terminal is not the same as visible. The
fallback is now `{"error":"glab-ci-status-failed"}` plus the shape guard at the
top of the loop, and the `(.jobs|length) > 0` terminal guard stays as the
second line of defence for a genuine zero-job response. Probed: the sentinel
and raw non-JSON glab noise both emit the `error:` line;
`{"jobs":[],"pipeline":{}}` and a populated payload both take the normal path.

**GitHub-mirror equivalent.** When the pipeline is GitHub-Actions-native (PR
checks rather than a GitLab pipeline), use
`gh pr checks -R <OWNER>/<REPO> <pr> --watch --fail-fast`
as the `command` source — it streams each check transition and exits non-zero on
the first failure, so the terminal state is never silent.

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

**timeout_ms.** `3600000` (1 h — the 1 h ceiling this file uses; repo-internal convention, upstream documents no explicit `timeout_ms` maximum)

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
30-min sleep matches the `1200s+` idle-tick band from
`.claude/rules/loop-and-monitor.md` LM-003 (idle observation-rate; under the
1-hour subscription cache TTL there is no cache penalty here anyway).

---

## Pattern 5 — GitHub mirror push verification (secret-scanner safety net)

**When.** After `git push github main` when there is any chance of a
secret-scanner false positive. The plugin hit one on 2026-04-28 (the
`${SCHEMA_DRIFT_TOKEN}` placeholder); silent push success without mirror
parity bit the operator a day later.

**Description.** `github mirror parity vs local main`

**timeout_ms.** `300000` (5 min — push usually completes in seconds; this is the wall-clock ceiling **for this watch**, **not** the `/loop` cadence band that LM-003 in `.claude/rules/loop-and-monitor.md` warns against)

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

## Pattern 6 — WebSocket event source (`ws://` / `wss://`, v2.1.195+)

**When.** The upstream already speaks WebSocket (a CI relay, an error-tracker
push socket, a daemon's `GET /events` upgraded to WS). Point Monitor's `ws`
source at it directly — the server pushes each text frame as one notification,
so there is no polling script and no `grep --line-buffered` line-buffering
pitfall to get right. Prefer this over a `command` source whenever a socket is
available.

**Input shape.** Monitor takes a `ws` source *instead of* a `command` source —
the two are mutually exclusive, never combined:

```jsonc
{
  "ws": {
    "url": "wss://relay.internal.example/ci-events",  // ws:// or wss:// only
    "protocols": ["ci-events.v1"]                      // optional subprotocols
  }
}
```

The `url` must be a bare `ws://`/`wss://` URL — **no embedded credentials, no
whitespace, ASCII-only**. Each inbound **text** message becomes one
notification (multi-line frames included). A **binary** frame is surfaced as the
placeholder `[binary frame, N bytes]` rather than decoded.

**Coverage / termination.** Two clean terminations and one **silent** one — the
silent case is the whole reason this pattern needs the silence-is-not-success
discipline:

- **Socket close** → the watch ends and reports the close code (a clean,
  visible terminal state).
- **Frame > 1 MiB → the watch ends SILENTLY.** No close code, no error line —
  it just stops. Therefore **always subscribe to a filtered / compact feed**
  (a pre-narrowed event topic), **never a raw feed** whose payloads can cross
  1 MiB. A raw firehose that occasionally emits a large frame is
  indistinguishable from a healthy-but-quiet socket, which is exactly the
  crash-reads-as-success trap this file exists to prevent.

**Caveats.**

- **Own approval prompt.** A `ws` source raises its own connect-approval prompt
  and has **no "skip future" affordance** — each armed socket is approved
  explicitly.
- **SSRF denials.** Monitor refuses `ws` URLs pointing at private,
  link-local, or cloud-metadata hosts, and honours `sandbox.network.deniedDomains`
  plus `allowManagedDomainsOnly`. Point it at a reachable, allow-listed relay,
  not an internal-range host.
- **When to stay on `command`.** If frames must be filtered or reshaped
  shell-side before they are notification-worthy, keep the `command` (tail/grep)
  source per `.claude/rules/loop-and-monitor.md` LM-002 — the `ws` source
  delivers frames verbatim, with no shell-side filter seam.

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
