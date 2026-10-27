# Call record

`calls.jsonl` holds one JSON object per tool call. Every adapter emits this shape, and `aggregate.py` reads nothing else, so a harness is supported as soon as its adapter does. `scripts/common.py` holds the same field list (`REQUIRED`, `OPTIONAL`, `KINDS`); change both together.

## Fields

| Field | Required | Meaning |
|---|---|---|
| `agent` | yes | The tool loop that ran the call: `Claude Code`, `Codex`, `OpenCode`. |
| `harness` | yes | The surface the user worked in: `Claude Code CLI`, `Codex Desktop`, or `<frontend> → <agent>` when a frontend drives another agent (`T3 Code → Codex`). |
| `session` | yes | The harness's session or thread id. |
| `id` | yes | The call id, unique within the agent across all sessions. `extract.py` keeps one record per (`agent`, `id`), so copies from resumed or forked sessions, or from two sources describing one call, count once. Build a fallback id from the session and something unique inside it, never from a per-session counter alone. |
| `ts` | yes | Start, epoch milliseconds. |
| `dur_ms` | yes | Start to result, milliseconds, never negative. |
| `tool` | yes | The harness's own tool name (`Bash`, `exec_command`, `mcp__playwright__browser_click`). |
| `kind` | yes | One of the kinds below. |
| `command` | shell only | The shell command, secrets masked and clipped to 2,000 characters. The categories are built from it. |
| `mcp_server`, `mcp_tool` | MCP only | Server and tool names. |
| `detail` | no | A short hint for spot checks (a file path, a query), clipped to 160 characters. |
| `project` | no | Basename of the working directory, for grouping. |
| `error` | no | The call failed or the command exited non-zero. |
| `background` | no | The call only started work that runs on after it returns. |
| `human_wait` | no | The duration includes the user answering an approval prompt. |
| `subagent` | no | The call ran inside a subagent. |
| `mode` | no | The session's permission or approval mode (`auto`, `acceptEdits`, `on-request`). |
| `approval` | no | How the harness approved this call, in its own words (`classifier`, `mode`, `rule`). |
| `version` | no | The agent's release, to catch a slow version. |
| `timing` | no | How `ts` and `dur_ms` were obtained, below. |
| `src` | no | Absolute `path:line` of the raw log line that closed the call, for spot checks. |

## Kinds

`shell` (any command execution) · `read` (file or image read) · `search` (grep, glob, file listing) · `edit` (any file write or patch) · `web` (fetch or web search) · `mcp` (any MCP tool) · `subagent` (spawning or messaging another agent) · `wait` (a tool whose job is to wait: sleep, wait-for-agent, monitor) · `review` (an automatic approval reviewer's turn) · `ask_user` (a question to the user) · `other`.

A `subagent` call's duration contains the subagent's own calls, which appear as records too. Category totals are therefore tool time, not wall time; never add them up to a working day.

## Timing

- `exact`: the harness recorded this call's start and end (or its duration).
- `derived`: the start and end come from the timestamps of the lines that issued the call and returned its result.
- `inferred`: only message-level timestamps exist, so the duration includes model time around the call. Use such calls for long-running patterns only, never for overhead comparisons of fast operations.
