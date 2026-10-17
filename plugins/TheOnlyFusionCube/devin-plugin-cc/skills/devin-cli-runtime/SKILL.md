---
name: devin-cli-runtime
description: Internal helper contract for calling the devin-companion runtime from Claude Code
user-invocable: false
---

# Devin Runtime

Use this skill only inside the `devin:devin-rescue` subagent.

Primary helper:
- `node "${CLAUDE_PLUGIN_ROOT}/scripts/devin-companion.mjs" task "<raw arguments>"`

Execution rules:
- The rescue subagent is a forwarder, not an orchestrator. Its only job is to invoke `task` once and return that stdout unchanged.
- Prefer the helper over hand-rolled `git`, direct Devin CLI strings, or any other Bash activity.
- Do not call `setup`, `review`, `adversarial-review`, `status`, `result`, `handoff`, or `cancel` from `devin:devin-rescue`.
- Use `task` for every rescue request, including diagnosis, planning, research, and explicit fix requests.
- You may use the `devin-prompting` skill to rewrite the user's request into a tighter Devin prompt before the single `task` call.
- That prompt drafting is the only Claude-side work allowed. Do not inspect the repo, solve the task yourself, or add independent analysis outside the forwarded prompt text.
- Leave `--model` and `--permission-mode` unset unless the user explicitly requests one.
- Default to a write-capable Devin run by adding `--write` unless the user explicitly asks for read-only behavior or only wants review, diagnosis, or research without edits.

Command selection:
- Use exactly one `task` invocation per rescue handoff.
- If the forwarded request includes `--background` or `--wait`, treat that as Claude-side execution control only. Strip it before calling `task`, and do not treat it as part of the natural-language task text.
- If the forwarded request includes `--model`, pass it through to `task`.
- If the forwarded request includes `--permission-mode`, pass it through to `task`.
- If the forwarded request includes `--resume`, strip that token from the task text and add `--resume`.
- If the forwarded request includes `--resume-id <id>`, strip it and add `--resume-id <id>`.
- If the forwarded request includes `--fresh`, strip that token and do not add a resume flag.
- `--resume`: continue the most recent Devin session in this directory (`devin -p -c`).
- `--resume-id <id>`: resume a specific Devin session (`devin -p -r <id>`).
- `--fresh`: always use a fresh `task` run, even if the request sounds like a follow-up.
- `task --resume`: internal helper for "keep going", "resume", "apply the top fix", or "dig deeper" after a previous rescue run.

Permission modes (`--permission-mode`):
- `normal`: read-only-ish in `-p` mode — tool calls needing confirmation are auto-rejected. Use for research/diagnosis.
- `accept-edits`: file edits auto-approved; shell commands still rejected. Default for `--write`.
- `smart`: a fast model judges each action; rolling out gradually, may not exist on all accounts.
- `dangerous` (aliases `yolo`, `bypass`): auto-approves everything including shell commands.
- `autonomous`: only with `--sandbox`; commands run inside an OS-level sandbox.
- Only pass a mode when the user asked for it, or when `--write`/`--read-only`/`--sandbox` semantics already choose it.

Safety rules:
- Preserve the user's task text as-is apart from stripping routing flags.
- Do not inspect the repository, read files, grep, monitor progress, poll status, fetch results, cancel jobs, summarize output, or do any follow-up work of your own.
- Return the stdout of the `task` command exactly as-is.
- If the Bash call fails or Devin cannot be invoked, return nothing.
