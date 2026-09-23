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

## Authorization and startup evidence

Resolving a command does not authorize executing it. Before reading a source or
resuming, verify task/source-owner/model/provider/destination authorization and
that the caller selected this runtime operation. Cross-harness conversion sends
content to a new recipient and requires its own applicable authorization.

Before execution, pass source-store/project/work identity and permitted intent
locators, and have the caller record the dispatch/resume request in native
comments/metadata or runtime facts. Keep the requested predecessor separate
from the actual resumed context. At startup, record the selected runtime's
observed session/context ID and resume relation with observation provenance;
it may reuse an ID or create another context. Until observed, use explicit
unknowns. Command text, a filename and successful command resolution do not
prove that resumption occurred. Preserve failed starts and unresolved links
without waiting for handoff. Follow
[session associations](SESSION_FORMATS.md#work-to-session-associations) for
supported spans and available frozen source boundaries/digests; never transfer
all work associations from a predecessor automatically.

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
# Inspect the emitted command; execute only the caller-authorized native resume.

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

Use `cass context` only to discover candidate sessions. Its `related` object
contains `same_workspace`, `same_day` and `same_agent` lists; their entries use
`.path`, not `.source_path`. These are similarity groups, not parent edges.

```bash
# Bounded candidate discovery for an authorized source; do not select a parent.
cass context /path/to/subagents/agent-XXXXX.jsonl --json
```

Verify parentage using an authorized native startup/dispatch observation or
explicit parent link in native runtime metadata, with its exact permitted
source locator. A dispatch-attested controller relation is distinct from a
native parent relation. The first non-subagent workspace hit, a matching title,
a filename or a guessed prompt line is never proof. If no link is observable,
record parent unknown and stop parent-based resume selection. Only after the
link is verified and the caller selects execution may `cass resume` target the
verified parent; do not erase the child's separate source/work association.

---

## The Resume → Search Loop

A common pattern: search for a past task, resume the agent that did it, hand off the next prompt.

```bash
# 1. Find the right past session
HIT=$(cass search "implement auth flow" --workspace /myrepo --json --fields summary --limit 1 \
       | jq -r '.hits[0].source_path')

# 2. Print the command without executing
cass resume "$HIT" --shell

# 3. Only after caller authorization and pre-execution association recording
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
| `session_id_not_found` for `agent-*.jsonl` | Subagent file | Discover candidates with `cass context`; verify a native parent link or leave parent unknown |
| `unknown harness` | Path doesn't match any connector layout | Pass `--agent` explicitly |
| Resumed session won't open | The native CLI was upgraded and changed its session schema | Try the harness's own `--list` to see if the ID is still valid; the source jsonl is your fallback |
| `cross_agent_session_resumer#9` style: Codex → Pi resumption broken | Cross-harness resume requires casr (separate tool) | Use the matching native CLI; cass resume only does *same-harness* |

---

## What `cass resume` is NOT

It is **not** a cross-CLI translator. Resuming a Codex conversation always uses the Codex CLI; Claude → Claude; etc. Genuine cross-CLI continuation is the job of `casr` (Cross Agent Session Resumer) — a separate upstream tool, not an AgentOps skill under `skills/` — while `cass resume` only does same-harness resume.
