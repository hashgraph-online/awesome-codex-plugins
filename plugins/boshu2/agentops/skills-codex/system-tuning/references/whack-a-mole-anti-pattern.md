# The Whack-a-Mole Anti-Pattern

> **Pattern (named in an external system-performance-remediation skill corpus).**
> You signal a child process. It dies. Seconds later something visually
> identical reappears. You signal it again. Same outcome.
>
> The cleanup target was wrong. The thing you killed was a symptom; whatever
> respawned it is the cause.

## How To Recognise It

| Signal | What it means |
|---|---|
| Same process command line reappears within seconds of a kill | A supervisor is restarting it |
| Different PIDs but identical args after each kill | A loop is recreating the work, not the same process retrying |
| `pstree` shows the suspicious process under a long-lived agent | The agent's control loop is the supervisor |
| Killing N children leaves load unchanged | You are not in the right tree at all |

## Common Sources Of The Loop

- **Coding agents** running long horizons. Their internal loop notices that
  a sub-task exited and starts another one. Killing the sub-task is futile
  unless the agent itself is told to stop.
- **systemd services** with `Restart=always` or short backoff. Use
  `systemctl stop` (or `disable --now`), not `kill`.
- **cron / systemd timers** that fire on a short cadence. Killing in between
  triggers feels like whack-a-mole because the next firing is queued.
- **Shell `while true` poll loops** that watchdog a feature flag or a file
  that never appears.
- **Parent watchers** in dev tooling (`bun --hot`, `next dev`,
  `cargo watch`) that respawn the child when the file system mtime changes.

## Counter-Strategy

1. **Find the parent.** Get the PID of the respawning child, then walk up.

   ```bash
   child_pid=12345
   parent_pid=$(ps -o ppid= -p "$child_pid" | tr -d ' ')
   ps -o pid,etimes,args -p "$parent_pid"
   ```

2. **Classify the parent.** Long-running agent, watcher, init system, or
   timer? The right action depends on the class.

3. **Apply the right control.**

   | Parent class | Right control |
   |---|---|
   | Long-horizon agent | `kill <agent_pid>`; the children will not respawn |
   | Watcher / dev server | Stop the watcher process (escalate to SIGKILL only if it ignores SIGTERM) |
   | systemd unit | `systemctl --user stop <unit>` (or system level if appropriate) |
   | cron / timer | Disable the schedule first, then kill the live invocation |
   | Shell poll loop | Kill the wrapper shell; do not chase the inner sleep child |

4. **Verify the loop is broken.** Wait a multiple of the previous respawn
   interval (e.g. 10s if respawns took 3s). If nothing comes back, the cause
   is gone. If something comes back, you climbed one level too few.

## Avoidable Causes

When you operate the box, prevent the pattern from recurring:

- Limit concurrent agents per project so multiple agents are not racing on
  the same work.
- Use issue tracking (`bd`) so each agent picks distinct work instead of
  re-attempting the same task.
- Add a real ceiling on agent age so confused agents reap themselves.
- Centralise cache directories rather than letting every agent fork a
  parallel build tree.

The goal is to make the kill ladder unnecessary in steady state. Cleanup is
acceptable; chronic cleanup is a planning problem.

## When It Is Not Whack-A-Mole

Three patterns look like whack-a-mole but are actually something else:

- **PID reuse on a busy box.** The "same" PID belongs to a different
  command. Confirm with `ps -o pid,args -p <pid>` after each round.
- **A supervisor outside your tree** restarting the child (e.g., a remote
  deploy harness). Local kills will never win; coordinate with the operator
  of the supervisor.
- **A clock-driven job** (cron, scheduled timer) that simply happens to run
  often. Pause the schedule rather than chasing each invocation.

Identify which pattern you are in before escalating signals.
