<!-- SHARED SHIM SNIPPET (D5/D4f) — interpolated into every rendered shim whose
     host resolves *run detached* to `--detach`, never a second file an agent is
     told to open. Edited here once; it still counts against every shim's rendered
     line budget, because an agent reads it.

     No slots. Nothing host-specific may enter this file: the cap that motivates
     the loop is the host entry's timeout ceiling, and whether the loop is used at
     all is the *run detached* verb slot. A snippet that would need
     an `if` is two snippets, or it is not a snippet. -->

## Polling a detached run

`--detach` returns immediately with the run's log path and a `status` command.
Poll with that command, one call per turn. It carries the `--host` the launch
was given — the dispatcher command above bakes one in — and `--run-id` only on
an `ask` run, the one mode where the phase selector (`--phase ask`) names every
question ever asked under the plan rather than this invocation. It carries
`--wait` with no `--timeout`, so its wait is `progress.poll_s` clamped under
that same `--host`. It has the shape below, where `<host-id>` is the same host
id the dispatcher command above bakes in:

```bash
uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" status "<plan>" --host <host-id> --view run --wait
```

Make that same call **once without `--wait`** before the loop starts: it answers
in well under a second, and its `models:` table is the only thing on screen that
says which CLI and model each row runs, with the count on the `progress:` line
directly above it. The run writes that roster a few seconds in, so repeat that
one call once if no table printed; relay it once, never again — the loop reports
movement, not the roster. A table that *does* print can still be the previous
run's, because the phase dir is re-used and the write that claims it for this
fan-out drops the predecessor's `progress` only ~0.2 s in: a table under a
`progress:` step that is not `fanout` is the last run's, so make the call again
rather than relaying that one. The step is the whole test — a head line saying
the run finished is also what a dir an earlier detached run left a terminal
`run` record in prints all run long, so the tense names no run.

Read the **exit code**, which is the loop condition — never the prose:

- **0** — the run finished. Read the markers and output paths from the log path
  `status` printed.
- **2** — still running (this also covers "no run recorded yet"). Poll again.
- **3** — the run needs a human. The message names the flag or command that
  answers it; do not retry the same invocation.
- **1** — the run state is unreadable. Report it; do not guess.

Four rules make this safe, and readable, on a host that caps shell time:

- **One `status` call per shell command.** A `status` call is a file read plus a
  liveness probe and finishes in well under a second, and `--wait` compresses the
  gap into one turn. Its duration is the dispatcher's *resolved* default — 90 s
  unless the project sets `progress.poll_s` in `providers.yaml` — and whatever
  that resolves to is then clamped to sit under this host's own documented shell
  cap. That clamp is read off the `--host` on the command, which is why the block
  above spells it: with no `--host` it falls back to the tightest cap on record
  and silently shortens every wait.
- **Relay one line per poll, copied through rather than reworded.** The run
  view's `progress:` line carries the counts, and its `just finished:` line
  names which model turned terminal *during that wait*; a reworded count or name
  is one that can be wrong. Its absence claims nothing — a model that finished
  in the gap between two polls is already terminal when the next one takes its
  baseline — so every poll compares this poll's rows against the previous
  poll's and names every newly terminal row that line did not name, copying its
  spec and state word out of the `models:` table, which is a copy and not a
  recount. Nothing else from the view is relayed mid-run.
- **Never spell the wait as `sleep <n>; status` in one call.** That collapses the
  wait into a single shell command and reintroduces exactly the cap kill
  `--detach` exists to avoid; the waiting belongs *between* calls, in your own
  turn loop.
- **`status` takes no lock and writes nothing**, so it is safe while the run owns
  the phase dir. To stop a run, the only kill path is
  `... multi_llm.py status "<plan>" --abort`.
