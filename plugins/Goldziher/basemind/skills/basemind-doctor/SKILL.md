---
name: basemind-doctor
description: >-
  Diagnose and recover basemind when it isn't working — MCP tools missing or erroring, "no
  index" / "no indexed files", empty results that shouldn't be empty, or the MCP server seems
  dead. Runs CLI checks (no MCP server required) and gives the client-specific way to reconnect
  the server.
---

# basemind-doctor — diagnose and recover basemind

Use this when basemind isn't behaving: MCP tools aren't available or return errors, the
statusline says **no index**, queries come back empty when they shouldn't, or the `basemind serve`
MCP server appears dead. Every step here uses the **CLI**, so it works even when the MCP server is
down.

Important: a stdio MCP server (what `basemind serve` is) **cannot be restarted by an agent or by
basemind itself** — a fresh process can't resume the client's MCP `initialize` handshake.
Reconnecting the server is the **MCP client's** job (see step 4). What you _can_ do from here is
make sure the index is healthy and clear anything blocking a restart.

## 1. Is there an index?

```sh
basemind query status
```

- Errors / "no index" / `file_count: 0` with blobs present → the index is missing or lost. Build
  it: `basemind scan` (see the `basemind-scan` skill / `/bm-scan`).
- Healthy `file_count` → the index is fine; the problem is the server connection (step 4).

## 2. Is a server already running (holding the lock)?

If `basemind scan` fails with a lock error, a `basemind serve` (or `watch`) already owns the index
for this repo. Check the lock holder:

```sh
cat .basemind/.lock.meta 2>/dev/null   # {"command":"basemind serve","pid":<pid>,"acquired_unix":<ts>}
```

- If that `pid` is **alive** (`ps -p <pid>`), the server is up — use the MCP tools, or the
  `rescan` MCP tool to refresh. Don't run a CLI `scan` (it will contend on the lock).
- If that `pid` is **dead**, the lock is stale. The OS releases the advisory lock when a process
  dies, so a fresh `basemind scan` / `basemind serve` should just work — retry it. (You may delete
  the stale `.basemind/.lock.meta` to clear the advisory holder record.)

## 3. Rebuild the index if needed

```sh
basemind scan
```

Non-extractable files are skipped, not failed. After this, both the CLI and (once reconnected) the
MCP tools have a fresh index.

## 4. Reconnect the MCP server (client-specific — this is the only way to restart it)

basemind can't relaunch its own stdio server; trigger a reconnect in your client:

- **Claude Code**: reconnect the basemind MCP server from the MCP UI, or restart the session. The
  plugin's launcher re-downloads/execs the binary automatically on the next connection.
- **Cursor / others**: toggle/reconnect the basemind MCP server in the MCP settings.

While disconnected, you are not blocked: use the `basemind-cli` skill (`basemind query …`,
`basemind git …`) — it reads the same `.basemind/` index directly, no server required.

## Agent shells (embedded rmux daemon)

Only when the server was built with `--features shells`. Spawned shell sessions run under an
**embedded rmux daemon** — basemind re-execs itself (`--__internal-daemon`) rather than shelling
out to any external `rmux` binary, so there is nothing extra to install. The daemon binds a private
per-user socket under the data dir (`<data_dir>/basemind/shells/rmux.sock`, `0o700`), overridable
with `BASEMIND_SHELLS_SOCKET`. It is **separate** from the comms broker daemon.

- `shell_list` (MCP) enumerates sessions with liveness; a dead-but-listed session was killed or
  exited — re-run after `shell_kill` to confirm it's gone.
- The daemon **self-terminates once it has no sessions left**, so an idle daemon disappearing is
  expected, not a fault. A new `shell_spawn` starts a fresh one.
- Sessions are independent of `serve`: they outlive a single MCP call but are torn down by
  `shell_kill` (which also drops the comms lineage row) or when the daemon exits.

## When server logs help

`basemind serve` logs its lifecycle to stderr (captured in your client's MCP server logs):
a `MCP server starting` line with pid/version/view at startup, and an explicit
`client disconnected, exiting` (clean) or `exiting on error` (with the cause) at shutdown. If serve
keeps dying, that log line names the reason.
