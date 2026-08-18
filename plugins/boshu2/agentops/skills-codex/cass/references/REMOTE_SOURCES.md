# Remote Sources & Multi-Machine Search

> **One-liner:** `cass sources` lets you treat sessions on `css`, `csd`, `ts1`, `ts2`, etc. as part of your local searchable corpus. Three approaches, ordered by long-term value.

## Contents

- [Approach A — Configured Sources (preferred)](#approach-a--configured-sources-preferred)
- [Approach B — One-Shot SSH Query (no setup)](#approach-b--one-shot-ssh-query-no-setup)
- [Approach C — Parallel Fan-Out](#approach-c--parallel-fan-out-when-speed-matters)
- [Diagnostics](#diagnostics)
- [When to Use Which](#when-to-use-which)
- [Pitfalls](#pitfalls)

---

## Approach A — Configured Sources (preferred)

Persist remote machines so every `cass search` automatically spans them.

```bash
# 1. Discover SSH hosts and probe each one
cass sources discover --json
cass sources setup            # interactive wizard; auto-skips configured hosts

# 2. Or add manually
cass sources add ssh://ubuntu@css --name css --preset linux-defaults
cass sources add ssh://ubuntu@csd --name csd --preset linux-defaults
cass sources add ssh://ubuntu@ts1 --name ts1 --preset linux-defaults
cass sources add ssh://ubuntu@ts2 --name ts2 --preset linux-defaults

# 3. Sync (rsync remote → local + reindex)
cass sources sync --json                    # all sources
cass sources sync --source css --json       # one source
cass sources sync --dry-run --json          # preview only

# 4. Confirm
cass sources list --json
cass sources doctor --json                  # connectivity + path probe
```

After sync, `cass search` queries return hits with `origin_host: "css"` mixed in. Always preserve `origin_host` when reporting back to the user — it tells them which machine the prompt lives on.

### Source Schedule

```toml
# ~/.config/cass/sources.toml
[[sources]]
name = "css"
type = "ssh"
host = "css"
paths = ["~/.claude/projects", "~/.codex/sessions"]
sync_schedule = "manual"          # or "hourly", "daily"
platform = "linux"
```

### Path Mappings

When a workspace path differs between machines (e.g., `/home/user1/dp` ↔ `/data/projects`):

```bash
cass sources mappings list css --json
cass sources mappings add css --from /home/user1/dp --to /data/projects
```

Mapped paths are rewritten so `--workspace /data/projects/foo` matches both local and remote sessions.

---

## Approach B — One-Shot SSH Query (no setup)

Fastest path when you only need one query against one host.

```bash
ssh css 'cass search "KEYWORD" --json --fields minimal --limit 10' \
  | jq '[.hits[] | {host: "css", path: .source_path, line: .line_number}]'
```

Trade-off: every query incurs SSH latency (~300ms cold) + remote `cass` startup. Use Approach A for >3 queries per session.

---

## Approach C — Parallel Fan-Out (when speed matters)

Run identical query against the whole fleet simultaneously.

```bash
HOSTS="css csd ts1 ts2"
for h in $HOSTS; do
  ssh "$h" 'cass search "KEYWORD" --json --fields minimal --limit 20' > "/tmp/cass-$h.json" &
done
wait

# Merge + dedup (same source_path + line counts as the same hit)
jq -s '
  [.[] | .hits[] // empty]
  | unique_by(.source_path + ":" + (.line_number|tostring))
  | sort_by(-.score)
  | .[0:30]
' /tmp/cass-*.json
```

Use this when you don't want to write to local disk (`sources sync` writes ~tens of MB per host) or when you're ok with snapshot-in-time results.

---

## Diagnostics

```bash
cass sources list --verbose --json    # full config + sync state
cass sources doctor --source css --json
# Common failures:
#   - "host unreachable" → check ssh connectivity
#   - "remote cass not found" → ssh in and `install.sh`
#   - "rsync arg protection mismatch" → CLOSED issue #191; update macOS rsync to 3.4.1+

# Per-host probe (lightweight)
ssh css 'cass health --json'
```

---

## When to Use Which

| Need | Approach |
|------|----------|
| One query, exploratory | B (ssh one-shot) |
| Mining a project across the fleet over a session | A (configured sources) |
| Latency matters more than dedup | C (parallel fan-out) |
| Building cross-machine analytics | A + `cass analytics rebuild` after sync |

---

## Pitfalls

- `cass sources sync` rsyncs **session files**, not the index. Re-indexing happens automatically; if you pass `--no-index`, you must run `cass index --json` yourself.
- Path mappings rewrite *workspace* paths only. The `source_path` of remote hits still references the **remote** filesystem — pass back to the user verbatim, don't try to open them locally.
- Removing a source: `cass sources remove NAME --purge` deletes the synced data too. Without `--purge`, it just stops future syncs but keeps already-indexed sessions.
- If `sources doctor` reports paths as missing on macOS but they exist on the remote, that's CLOSED issue #190 — update cass past v0.3.1.
