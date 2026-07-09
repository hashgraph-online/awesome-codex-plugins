# Persistent Harness / Connector Exclusion

> **One-liner:** When a connector (e.g., `openclaw`, `chatgpt`) floods the index with low-value or looped sessions, persistently exclude it via `cass sources agents`. The setting survives across runs.

## Contents

- [The Three Subcommands](#the-three-subcommands)
- [Connector Slugs](#connector-slugs)
- [What Exclude Actually Does](#what-exclude-actually-does)
- [When to Use](#when-to-use)
- [Verifying](#verifying)
- [Manual sources.toml Edit (Fallback)](#manual-sourcestoml-edit-fallback)
- [Pitfalls](#pitfalls)

---

## The Three Subcommands

```bash
cass sources agents list --json
cass sources agents exclude <agent-slug>
cass sources agents exclude <agent-slug> --keep-indexed-data
cass sources agents include <agent-slug>
```

---

## Connector Slugs

`cass capabilities --json | jq '.connectors'` returns the canonical list. As of v0.3.6:

```
codex, claude_code, gemini, clawdbot, vibe, opencode, amp,
cline, aider, cursor, chatgpt, pi_agent, factory, openclaw,
kimi, copilot, copilot_cli, qwen, crush
```

Use those exact slugs. Aliases (`claude` → `claude_code`) are accepted but get normalized.

---

## What Exclude Actually Does

`cass sources agents exclude openclaw`:

1. Writes `disabled_agents = ["openclaw"]` to `~/.config/cass/sources.toml` (creating the file if absent)
2. Halts indexing of openclaw sessions on **future** scans, syncs, and watch cycles
3. By default **purges already-indexed openclaw data** from the local archive and rebuilds lexical search → reclaims space immediately
4. With `--keep-indexed-data`: leaves prior data alone, only blocks future ingestion

The setting survives upgrades, restarts, and machine reboots. To unset: `cass sources agents include openclaw`.

---

## When to Use

| Trigger | Action |
|---------|--------|
| One harness is producing 80% of the index volume with low-value content | `exclude` it |
| openclaw / vibe / experimental agent is looping | `exclude` immediately |
| You only care about Claude+Codex on this machine | `exclude` everything else |
| You're temporarily debugging that harness | `exclude --keep-indexed-data` so a re-include restores quickly |

---

## Verifying

```bash
# Current exclusions
cass sources agents list --json | jq '.disabled_agents'

# Confirm new sessions from excluded harness are skipped
cass index --json 2>&1 | grep -i "skipping excluded"

# Confirm searches no longer return excluded-agent hits
cass search "*" --aggregate agent --limit 1 --json | jq '.aggregations.agent.buckets'
# excluded slugs should be absent
```

---

## Manual sources.toml Edit (Fallback)

The `cass sources agents` subcommand landed in commit `82d8d70e` (2026-04-20). It is **not present in the v0.3.6 release binary** but is in source HEAD. If `cass sources agents` errors with "unrecognized subcommand 'agents'", you're on a build older than that commit — edit the config directly:

```toml
# ~/.config/cass/sources.toml
disabled_agents = ["openclaw", "vibe"]

[[sources]]
name = "..."
# ...
```

Then trigger a one-off cleanup of already-indexed data:
```bash
cass index --full --force-rebuild --json   # rebuilds excluding the disabled list
```

To check what version added the subcommand:
```bash
cd /dp/coding_agent_session_search && git log --oneline --all -- src/lib.rs | grep -i "agents\|disabled_agents" | head -5
```

---

## Pitfalls

- `disabled_agents` is **case-sensitive** in normalization. The CLI normalizes; manual edits should use lowercase slugs.
- Excluding an agent **does not delete the source files** on disk — only the indexed copies. The user can always re-include and re-index without data loss.
- If you exclude a harness whose sessions live in an indexed remote source (`cass sources sync`), the remote sessions are still rsync'd to disk; only the indexing step skips them. Use `cass sources remove --purge` to stop syncing entirely.
- The default purge-on-exclude triggers a lexical rebuild. On big corpora that's a 25s blocking step. Pass `--keep-indexed-data` if you want exclude to be instant.
