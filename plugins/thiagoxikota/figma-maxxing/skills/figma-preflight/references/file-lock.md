# file lock

Use only the section relevant to the current operation. Inline `scripts/` and `references/` paths are relative to this skill’s directory unless a link says otherwise. Existing authorization and the entrypoint contract govern these recipes.

### Check 7: Figma file lock claimed (single-driver invariant)

One Figma file has one writer at a time. The lock script is
[`scripts/figma_lock.py`](../scripts/figma_lock.py) in this skill (Python 3, standard library only).
The commands below call it as `"${CLAUDE_SKILL_DIR}/scripts/figma_lock.py"`. Claude Code replaces
`${CLAUDE_SKILL_DIR}` with this skill's directory (the folder that holds this file) when it loads
the skill. Other agents: if the text still shows `${CLAUDE_SKILL_DIR}`, put the absolute path of
that folder in its place; never run a command with the variable empty.

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/figma_lock.py" claim <fileKey> --agent <agent> --task <task> [--ttl 1800]
python3 "${CLAUDE_SKILL_DIR}/scripts/figma_lock.py" check <fileKey>
python3 "${CLAUDE_SKILL_DIR}/scripts/figma_lock.py" release <fileKey> --agent <agent> --task <task>
python3 "${CLAUDE_SKILL_DIR}/scripts/figma_lock.py" sweep
```

How the script behaves:

- File-based: one JSON lock per `fileKey` under `~/.cache/figma-maxxing/locks/` (override with
  `FIGMA_LOCK_DIR`). Every session on the machine must use the same lock directory. A session
  with a different `FIGMA_LOCK_DIR` does not see the others' locks.
- The lock is advisory: it only protects sessions that check it.
- The lock is TTL based (`--ttl` in seconds, default 1800), with no PID tracking. A lock tied to
  the PID of a transient tool shell dies immediately (agent tool shells exit right after every
  command), which is why this lock is TTL based (field note, 2026-08).
- Every command prints one JSON object. Exit code 0 on success, 1 on conflict or when the lock
  directory stays busy (`{"error": "lock directory is busy"}`), 2 on a usage error (a `fileKey`
  that is not 1 to 64 letters, digits, `_` or `-`; a `--ttl` that is not positive; `release`
  without a task). A usage error prints the argparse message, not JSON.
- `check` prints `{"held": false}` or
  `{"held": true, "agent": ..., "task": ..., "claimed_at": ..., "expires_at": ...}`. It always
  exits 0 and never reserves the file.
- `claim` prints `{"claimed": true, "renewed": false, ...}` on a fresh claim. A `claim` by the
  same agent and task renews the lock (`"renewed": true`). A `claim` on a lock held by someone
  else exits 1 and prints the holder: `{"claimed": false, "held": true, "agent": ..., ...}`.
  Expired locks are treated as free.
- `release` prints `{"released": true, "held": false}`. If someone else holds the lock it exits 1
  and prints the holder. If nothing is held it prints `{"released": false, "held": false}` and
  exits 0.
- `sweep` deletes expired lock files and prints `{"swept": <count>}`. It is housekeeping only:
  an expired lock is already treated as free.
- `--agent` defaults to the environment variable `FIGMA_LOCK_AGENT`, then to the literal `agent`.
  `--task` defaults to `FIGMA_LOCK_TASK`. A `claim` with no task at all gets a generated
  `adhoc-<uuid>` task that you would have to copy from the claim output to release. Always pass
  an explicit `--agent` (for example `claude-code`) and `--task`.
- `release --force` releases a lock held by another task. It exists for the human, not for the
  agent. Never use it yourself.

The gate:

- Resolve the `fileKey` from the Figma URL, `figma_get_status`, or the `figma-map.md` written by
  `figma-orient` (default `docs/figma-map.md`, or the agent's own memory system).
- Diagnosis only: `python3 "${CLAUDE_SKILL_DIR}/scripts/figma_lock.py" check <fileKey>`. A free check does not reserve
  the file. Only a successful claim authorizes you to proceed.
- If `held=false`: claim it with
  `python3 "${CLAUDE_SKILL_DIR}/scripts/figma_lock.py" claim <fileKey> --agent <agent> --task <task> --ttl 1800`.
- If `held=true` and you ARE the holder (`agent` and `task` match): proceed.
- If `held=true` and you are NOT the holder: BLOCK the write. Surface who holds it and tell the
  user to either wait until `expires_at` or release the conflicting lock manually. Do NOT bypass.
- Release in cleanup or `finally`, on success and on failure alike. In a shell script, use
  `trap`. Keep exactly the same `--agent` and `--task` as the claim (or the same
  `FIGMA_LOCK_AGENT` and `FIGMA_LOCK_TASK`). An abrupt death without cleanup depends on TTL
  expiry. Never release the lock of another task.
- Release after the write completes:
  `python3 "${CLAUDE_SKILL_DIR}/scripts/figma_lock.py" release <fileKey> --agent <agent> --task <task>`.
- Lock errors keep writes blocked. Diagnose once, do not infer “no competing writer” from a process snapshot and bypass the lock. A free `check` is not a reservation. Conflicting lock release/override is a separate explicit human decision and never inferred from “fix all”.
