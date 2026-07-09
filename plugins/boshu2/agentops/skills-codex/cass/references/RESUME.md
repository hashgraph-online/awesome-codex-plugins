# Cross-Harness Session Resume

> **One-liner:** `cass resume PATH` resolves any indexed session into the exact command its native CLI uses to continue the conversation. Works across Claude Code, Codex, Gemini CLI, OpenCode, pi_agent.

## Contents

- [The Three Modes](#the-three-modes)
- [Per-Harness Behavior](#per-harness-behavior)
- [The Subagent Trap](#the-subagent-trap)
- [The Resume → Search Loop](#the-resume--search-loop)
- [When Resume Won't Work](#when-resume-wont-work)
- [What `cass resume` is NOT](#what-cass-resume-is-not)

---

## The Three Modes

```bash
# 1. Print argv tokens, one per line (for the caller to wrap)
cass resume /path/to/session.jsonl
# claude
# resume
# 8efcc298-90d8-4764-9144-944c40f1a321

# 2. Emit a single shell-escaped command line
cass resume /path/to/session.jsonl --shell
# claude resume '8efcc298-90d8-4764-9144-944c40f1a321'
eval "$(cass resume /path/to/session.jsonl --shell)"

# 3. Replace the current process (mutually exclusive with --shell/--json)
cass resume /path/to/session.jsonl --exec
```

---

## Per-Harness Behavior

`cass resume` detects the harness from the file path and emits the **command its native CLI expects**. Don't memorize the argv shape — just read what `cass resume PATH --shell` prints.

| Detected Agent | Source path layout | --agent override |
|----------------|--------------------|------------------|
| Claude Code | `~/.claude/projects/<workspace>/<uuid>.jsonl` | `claude` / `claude-code` / `claude_code` |
| Codex | `~/.codex/sessions/<YYYY/MM/DD>/rollout-*.jsonl` | `codex` |
| OpenCode | `~/.opencode/...` | `opencode` |
| Gemini | `~/.gemini/...` | `gemini` |
| pi_agent (mono) | `~/.pi/...` | `pi_agent` / `pi-agent` (auto) or `pi` (force) |
| Oh My Pi | `~/.pi/...` | `omp` / `oh-my-pi` / `ohmypi` |

Override the auto-detected harness with `--agent`:

```bash
cass resume /weird/path.jsonl --agent claude   # force Claude Code resume form
cass resume /weird/path.jsonl --agent omp      # force Oh My Pi
```

---

## The Subagent Trap

Subagent files are **NOT resumable** — they're orchestrated by a parent session.

```bash
cass resume /home/x/.claude/projects/<ws>/subagents/agent-a0b4d4b58a1fd73da.jsonl --json
# {"error":{"code":5,"kind":"session_id_not_found",
#  "message":"filename stem 'agent-a0b4d4b58a1fd73da' does not look like a Claude Code session UUID (expected 8-4-4-4-12 hex)",
#  "hint":"Did you pass a project directory or notes file instead..."}}
```

Recover the parent session via `cass context`. The schema is:

```json
{
  "source":  {"path": "...", "agent": "...", "workspace": "...", ...},
  "counts":  {"same_workspace": 12, "same_day": 8, "same_agent": 15},
  "related": {
    "same_workspace": [{"path": "...", "agent": "...", "title": "...", ...}, ...],
    "same_day":       [...],
    "same_agent":     [...]
  }
}
```

Note: items use `.path` (not `.source_path`) and `related` is an **object**, not a flat array.

```bash
# Find the parent (first non-subagent file in same_workspace)
cass context /path/to/subagents/agent-XXXXX.jsonl --json \
  | jq -r '.related.same_workspace[]
            | select(.path | contains("subagents") | not)
            | .path' \
  | head -1
```

Then `cass resume` that path.

---

## The Resume → Search Loop

A common pattern: search for a past task, resume the agent that did it, hand off the next prompt.

```bash
# 1. Find the right past session
HIT=$(cass search "implement auth flow" --workspace /myrepo --json --fields summary --limit 1 \
       | jq -r '.hits[0].source_path')

# 2. Print the command without executing
cass resume "$HIT" --shell

# 3. Drop the user into the resumed conversation
cass resume "$HIT" --exec
```

Or for inspection only:

```bash
cass expand "$HIT" --line 1 --context 5    # see the original prompt
```

---

## When Resume Won't Work

| Symptom | Cause | Fix |
|---------|-------|-----|
| `session_id_not_found` for `agent-*.jsonl` | Subagent file | Use `cass context` to find parent |
| `unknown harness` | Path doesn't match any connector layout | Pass `--agent` explicitly |
| Resumed session won't open | The native CLI was upgraded and changed its session schema | Try the harness's own `--list` to see if the ID is still valid; the source jsonl is your fallback |
| `cross_agent_session_resumer#9` style: Codex → Pi resumption broken | Cross-harness resume requires casr (separate tool) | Use the matching native CLI; cass resume only does *same-harness* |

---

## What `cass resume` is NOT

It is **not** a cross-CLI translator. Resuming a Codex conversation always uses the Codex CLI; Claude → Claude; etc. For genuine cross-CLI continuation, invoke the standalone `casr` skill (cross-skill reference — load via `casr` rather than following a path; the file at `../..casr/SKILL.md` is documentation only and not part of this skill's progressive-disclosure tree).
