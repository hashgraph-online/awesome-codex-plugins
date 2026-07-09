# Anti-Patterns (Long Form)

> **Why this exists:** Mined sessions show the same wasteful behaviors repeating across hundreds of agent runs. Each item below has a real-world cost; the "instead" is the move that actually works.

## Contents

- [1. Asking the User to Do What You're Authorized To Do](#1-asking-the-user-to-do-what-youre-authorized-to-do)
- [2. Dropping the Whole Index](#2-dropping-the-whole-index)
- [3. Treating "Stale" as "Broken"](#3-treating-stale-as-broken)
- [4. `--limit 0` for "no limit"](#4---limit-0-for-no-limit)
- [5. Piping `cass export` Into Anything](#5-piping-cass-export-into-anything)
- [6. Searching Without a Workspace, Then Filtering Client-Side](#6-searching-without-a-workspace-then-filtering-client-side)
- [7. Workspace Path Drift](#7-workspace-path-drift)
- [8. Searching for Tool Output](#8-searching-for-tool-output)
- [9. Default Fields on Wide Scans](#9-default-fields-on-wide-scans)
- [10. Ignoring `_meta` and `_warning`](#10-ignoring-_meta-and-_warning)
- [11. Bare `cass`](#11-bare-cass)
- [12. Running `cass index --full` Every Loop](#12-running-cass-index---full-every-loop)
- [Summary](#summary)

---

## 1. Asking the User to Do What You're Authorized To Do

**Bad:**
> "Your cass index is stale. Could you run `cass index --full` and let me know when it's done?"

**Why bad:** The user has 22 agents waiting. Every "could you" multiplies their interrupt cost.

**Instead:**
```bash
cass doctor --fix --json   # safe by default; preserves all source data
cass index --json &        # background refresh while you proceed
```
Then proceed and mention the rebuild ran in passing.

**Authorization scope:** Anything under `~/.local/share/coding-agent-search/` is yours to manage. Source session files (`~/.claude/projects/`, `~/.codex/sessions/`) are NOT — those are user data.

---

## 2. Dropping the Whole Index

**Bad:**
```bash
rm -rf ~/.local/share/coding-agent-search
cass index --full --json   # rebuild from scratch
```

**Why bad:** Throws away 4M+ messages of indexed history. Rebuild from raw sessions takes 25min on a typical fleet. Loses analytics rollups (no easy recovery).

**Instead:**
```bash
cass doctor --fix --json   # rebuilds only what's broken
```

`doctor --fix` already backs up corrupt DBs, so you never lose data even when the original is bad.

---

## 3. Treating "Stale" as "Broken"

**Bad:** Seeing `cass status` say `healthy: false, recommended_action: "Run cass index"` and immediately running `cass index --full --force-rebuild` (25s blocking).

**Why bad:** The index is stale only because it's older than the threshold (default 30 min). The data is still **correct** — it just doesn't have sessions from the last 30 min indexed yet.

**Instead:**
```bash
state=$(cass status --json | jq -r '.index | "\(.fresh)/\(.stale)/\(.documents // "N")"')
case "$state" in
  true/*)        echo "fresh — search now" ;;
  false/true/*)  echo "stale but usable"
                 # ALWAYS wrap bg cass index in `timeout` — without it, a hung
                 # rebuild silently strands forever. See scripts/recover.sh.
                 ( timeout 600 cass index --json >/tmp/cass-bg.$$.log 2>&1 </dev/null & ) 2>/dev/null ;;
  */*/0|*null)   echo "broken" && timeout 60 cass doctor --fix --json ;;
esac
```

The agent's first search returns immediately on the still-correct stale index. The background `cass index` finishes in 1–3s for incremental refreshes.

---

## 4. `--limit 0` for "no limit"

**Bad:** `cass search "X" --limit 0 --json` (worked in earlier cass versions; no-ops or returns RAM-capped result in v0.3+, panicked before).

**Why bad:** Unbounded scans burn context. Even with the modern RAM cap, you get random truncation.

**Instead:** Pick a real number.
- Aggregations: `--limit 1` and parse `.aggregations.*` only
- Wide scans: `--limit 50` + `--fields minimal` + iterate via `--cursor`
- Sampling: `--limit 5 --fields summary`

---

## 5. Piping `cass export` Into Anything

**Bad:**
```bash
cass export /path.jsonl --format json | jq '.[0:50]'
```

**Why bad:** Large exports trigger broken-pipe panic when the consumer closes early.

**Instead:**
```bash
cass export /path.jsonl --format json --include-tools -o /tmp/export.json
jq '.[0:50]' /tmp/export.json
```

Always `-o`. The file is cheap; the panic isn't.

---

## 6. Searching Without a Workspace, Then Filtering Client-Side

**Bad:**
```bash
cass search "auth" --json --limit 500 \
  | jq '[.hits[] | select(.workspace == "/data/projects/myrepo")]'
```

**Why bad:** Server returned 500 hits, you keep maybe 50. 10x context waste.

**Instead:**
```bash
cass search "auth" --workspace /data/projects/myrepo --json --limit 50
```

Server-side filtering is free. Client-side filtering is paid in tokens.

---

## 7. Workspace Path Drift

**Bad:** `cass search "X" --workspace /data/projects/myrepo/` — note trailing slash. Returns 0 hits. You assume the corpus is empty.

**Why bad:** Workspace strings are case-sensitive and trailing-slash-sensitive. The canonical key may be `/data/projects/myrepo` (no slash) or different case.

**Instead:** Probe first.
```bash
cass search "X" --aggregate workspace --limit 1 --json \
  | jq '.aggregations.workspace.buckets[] | select(.key | contains("myrepo"))'
```
Use the exact key from the bucket.

---

## 8. Searching for Tool Output

**Bad:** Looking for the exact bytes of a `Bash` tool's stdout via `cass search`. Finds nothing. Concludes the session doesn't exist.

**Why bad:** cass deliberately skips large tool outputs at index time to keep the corpus searchable on prompts and replies. Tool outputs are still **in the source file**.

**Instead:**
```bash
cass search "near-by user-prompt phrase" --json --fields minimal --limit 10 \
  | jq -r '.hits[0].source_path' | xargs rg -n "the exact tool output bytes"
```

Find the session via prompt, then `rg` for the bytes inside.

---

## 9. Default Fields on Wide Scans

**Bad:** `cass search "X" --json --limit 100` (no `--fields`). Returns ~3KB per hit × 100 = 300KB of context. With a 200K context budget, you've burned 1.5% on one tool call.

**Instead:**
```bash
cass search "X" --json --fields minimal --limit 100   # ~60KB total
```

Upgrade to `--fields summary` only for the few hits you decide to inspect.

---

## 10. Ignoring `_meta` and `_warning`

**Bad:** Reading `.hits` and reporting confidently — without checking that the index was fresh, the search wasn't truncated, and no fallback happened.

**Instead:**
```bash
cass search "X" --robot-meta --json | jq '{
  warning: ._warning,
  fresh: ._meta.index_freshness.fresh,
  fallback: ._meta.fallback_mode,
  clamped: ._meta.hits_clamped,
  total: .total_matches,
  shown: .count
}'
```

If `_warning` is non-null, mention it. If `hits_clamped: true`, paginate. If `fallback_mode != null`, your `--mode hybrid` actually ran lexical-only.

---

## 11. Bare `cass`

**Bad:** Running `cass` with no args inside an agent session. Launches the interactive TUI, blocks the agent's terminal, requires the user to Ctrl+C.

**Instead:** **Always** use `--json` or `--robot`. If you genuinely need TUI semantics from automation, `cass tui --once --asciicast /tmp/snap.cast` renders a single frame and exits.

---

## 12. Running `cass index --full` Every Loop

**Bad:** Pre-flight in a tight loop runs `cass index --full --json` every iteration. 25s × 60 iter = 25 min wasted.

**Instead:**
```bash
# Once at startup
cass status --json | jq -e '.index.fresh' >/dev/null || cass index --json

# Or use watch mode and never refresh inline
cass index --watch --json &   # one daemon, all agents share the index
```

---

## Summary

The pattern across these anti-patterns: **lack of trust in cass**. Trust the autonomous-recovery commands. Trust the safe-by-default `doctor --fix`. Trust the stale-but-correct lexical index. Trust the server to filter. Then your agent stops bothering the user.
