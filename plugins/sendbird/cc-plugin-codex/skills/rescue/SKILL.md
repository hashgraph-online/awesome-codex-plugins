---
name: rescue
description: 'Delegate a substantial diagnosis, implementation, or follow-up task to Claude Code through the tracked-job runtime. Args: --background, --wait, --resume, --resume-last, --fresh, --write, --model <model>, --effort <low|medium|high|xhigh|max>, --prompt-file <path>, [task text]. Defaults to opus + xhigh effort. Use when Claude should investigate or change things, not when the user only wants review findings.'
---

# Claude Code Rescue

By default, hand this skill off through Codex's built-in `default` subagent.
Do not answer the request inline in the main Codex thread.
Spawn exactly one rescue forwarding subagent whose only job is to run one companion `task` command and return that stdout unchanged.
Foreground rescue responses must be that subagent's output verbatim.

Use this skill when the user wants Claude Code to investigate, implement, or continue substantial work in this repository.

Prefer `$cc:rescue` when the user wants Claude Code to diagnose the issue, validate a risky change by actually editing or testing, apply fixes from a prior review, or carry a task forward across multiple steps.
Do not use rescue for "just review this diff" unless the user also wants follow-through work beyond review findings.
Do not use rescue merely because the main Codex thread plans to fix things after combining its own review with a separate Claude review. Rescue is only the right delegation when Claude itself is supposed to investigate, edit, test, or otherwise own the follow-through work.

Resolve `<plugin-root>` as two directories above this `SKILL.md` file. Always run the companion from that active plugin root:
`node "<plugin-root>/scripts/claude-companion.mjs" task ...`

Raw slash-command arguments:
`$ARGUMENTS`

Supported arguments: `--background`, `--wait`, `--resume`, `--resume-last`, `--fresh`, `--write`, `--model <model>`, `--effort <low|medium|high|xhigh|max>`, `--prompt-file <path>`, plus free-text task text

Main-thread routing rules:
- If the user explicitly invoked `$cc:rescue` or `Claude Code Rescue`, do not keep the work in the main Codex thread. Delegate it.
- If the user did not supply a task, ask what Claude Code should investigate or fix.
- Treat `--background` and `--wait` as execution controls, not task text.
- `--background` and `--wait` are Codex-side execution controls only. Never forward either flag to `claude-companion.mjs task`.
- The main Codex thread owns that execution-mode choice. It decides whether to wait for the subagent. The child subagent must never reinterpret those flags as companion flags.
- Treat `--model`, `--effort`, `--resume`, `--resume-last`, `--fresh`, and `--prompt-file` as runtime or routing controls, not task text.
- If the user task text itself begins with a slash command such as `/simplify`, `/fix`, or `/review`, treat that slash command as literal Claude Code task text to be forwarded unchanged. Do not execute or reinterpret it in the parent Codex thread.
- `--model` selects the Claude model for the companion `task` command only. It does not select the Codex subagent model.
- If the user explicitly passed `--background`, run the rescue subagent in the background.
- If the user explicitly passed `--wait`, run in the foreground.
- If neither flag is present and the rescue request is small, clearly bounded, or likely to finish quickly, prefer foreground.
- If neither flag is present and the request looks complicated, open-ended, multi-step, or likely to keep Claude Code running for a while, prefer background execution for the subagent.
- This size-and-scope heuristic belongs to the main Codex thread. The child subagent does not get to override it.
- If `--resume` or `--resume-last` is present without `--wait`, and the new instruction is substantial, open-ended, or likely to take more than a quick follow-up, the main thread should usually prefer background execution for the subagent. Keep that as a parent-side choice only. Do not inject `--background` into the child request or the companion command.
- Default to `--write` unless the user explicitly wants read-only behavior or only review, diagnosis, or research without edits.
- If `--resume` or `--resume-last` is present, continue the latest tracked Claude Code task. If `--fresh` is present, start a new task.
- If none of `--resume`, `--resume-last`, or `--fresh` is present, first run:
  `node "<plugin-root>/scripts/claude-companion.mjs" task-resume-candidate --json`
- If that helper reports `available: true`, ask the user once whether to continue the current Claude Code thread or start a new one.
- Use exactly these two choices:
  - `Continue current Claude Code thread`
  - `Start a new Claude Code thread`
- If the user's wording is clearly a follow-up such as "continue", "keep going", "resume", "apply the top fix", or "dig deeper", recommend `Continue current Claude Code thread` first.
- Otherwise recommend `Start a new Claude Code thread` first.
- If the user chooses continue, add `--resume` before spawning the subagent.
- If the user chooses a new thread, add `--fresh` before spawning the subagent.
- If the helper reports `available: false`, do not ask. Delegate normally.
- Do not inspect the repo, do the task yourself, poll job status, or summarize the result in the same turn.
- If a legacy request still includes `--notify-parent-on-complete`, treat it as a compatibility alias. Background built-in rescue now attempts parent wake-up by default.

Subagent launch:
- By default, use Codex's `spawn_agent` tool with `agent_type: "default"`.
- Never satisfy background rescue by launching `claude-companion.mjs task` itself as a detached shell process. Do not use `&`, `nohup`, detached `spawn`, or any equivalent direct background process launch from the parent.
- If a legacy request still includes `--builtin-agent`, treat it as a compatibility alias for the default built-in path. It should not change behavior.
- Prefer `fork_context: false` for the built-in rescue child. The parent should pass a self-contained forwarding message instead of replaying the full parent thread by default.
- Only consider `fork_context: true` as a last resort for a short follow-up where essential context truly cannot be summarized. Avoid it for large or long-lived threads because it can exhaust the child context window.
- The built-in rescue path must set `model: "gpt-5.4-mini"` and `reasoning_effort: "medium"` on `spawn_agent` so the transient forwarding child stays cheap and predictable.
- Before spawning the built-in child, emit one short commentary update that records the attempted subagent model selection. Default text should clearly say the parent is starting the built-in rescue child with `gpt-5.4-mini` at `medium` effort.
- Prefer `gpt-5.4-mini` for that built-in child, but if `spawn_agent` rejects that model with an explicit model-availability error such as `Unknown model`, `model unavailable`, or equivalent "not in list / unavailable" wording, retry once with `model: "gpt-5.4"` and the same `reasoning_effort: "medium"`.
- If that fallback happens, emit one short commentary update that clearly says `gpt-5.4-mini` was unavailable and the parent is retrying with `gpt-5.4`.
- Do not use that fallback for arbitrary failures. If the error is not clearly a model-unavailable problem, surface it instead of silently retrying with `gpt-5.4`.
- Remove `--background` and `--wait` before spawning the subagent. Those flags control only whether the main thread waits on the subagent.
- Pass only the routing and task arguments that actually belong to `claude-companion.mjs task`.
- If the free-text task begins with `/`, preserve it verbatim in the spawned subagent request. Do not strip the slash or rewrite it into a local Codex command.
- Before spawning the built-in child, capture the task job id plus routing context in one call:
  `node "<plugin-root>/scripts/claude-companion.mjs" background-routing-context --kind task --json`
- If that helper returns a non-empty `ownerSessionId`, include `--owner-session-id <owner-session-id>` in the companion command so tracked Claude Code jobs stay attached to the user-facing parent session for `$cc:status` / `$cc:result`.
- If it returns an empty `ownerSessionId`, omit `--owner-session-id` entirely. Never leave an empty routing placeholder such as `--owner-session-id  --job-id`.
- If that helper returns a non-empty `jobId`, pass it into the companion command as an internal `--job-id <reserved-job-id>` routing flag.
- Add an internal companion routing flag that reflects whether the user will see this result in the current turn:
  - Foreground rescue must add `--view-state on-success`
  - Background rescue must add `--view-state defer`
- Any user-supplied `--model` flag is for the Claude companion only and must be forwarded unchanged to `task`.
- If that helper returns a non-empty `parentThreadId`, pass it into the child prompt as the parent thread id for one-shot completion notification.
- If it returns an empty `parentThreadId`, continue without parent wake-up instead of blocking the rescue.
- This parent wake-up attempt is now the default for background built-in rescue on persistent Codex/Desktop threads. It is still best-effort and should silently degrade on one-shot `codex exec` runs.
- For the built-in rescue path, the parent thread owns prompt shaping. The built-in child should stay a pure executor.
- For the built-in rescue path, treat the internal runtime reference at `../../internal-skills/cli-runtime/runtime.md` as the command-building contract for the forwarding worker. It is an internal reference document, not a public skill to invoke.
- If the built-in rescue request is vague, chatty, or a follow-up, the parent may tighten only the task text before composing the exact companion command.
- Prefer passing a small structured `<parent_context>` block instead of forked thread history when the child needs a little prior context.
- Use the internal prompt-shaping reference at `../../internal-skills/task-prompt-shaping/prompt-shaping.md` as deeper guidance for that parent-side tightening. It is an internal reference document, not a public skill to invoke.
  - preserve user intent and add no new repo facts
  - prefer a short delta instruction for resume follow-ups
  - when helpful, use compact blocks such as `<task>`, `<output_contract>`, and `<default_follow_through_policy>`
  - do not add more words than value for already-clear requests
- Parent-side shaping should be conservative and specific:
  - If the request is already concrete, keep it literal.
  - If the request names a concrete file, path, or artifact such as `README.md`, and also includes explicit source/style/installation constraints, keep the full task text literal apart from stripping routing flags. Do not compress it into a shorter delta.
  - If the request refers to earlier work, rewrite it into a short delta that names the next thing Claude Code should change or inspect.
  - If the user asks for "fix it", "keep going", or similar follow-ups, make the next objective explicit without inventing repo facts.
  - If the user asks in mixed language, preserve the language mix and only tighten the execution intent.
  - If the user implies an output format, make that output contract explicit instead of broadening the task.
- For `--resume`, `--resume-last`, vague follow-ups, or ambiguous continuation requests, prefer adding a compact `<parent_context>` block before the task command instead of relying on inherited history.
- Keep `<parent_context>` small and structured. Good fields include:
  - `mode` (`fresh` or `resume`)
  - `job_id` when the parent reserved one
  - `claude_session` when a resumable Claude session is already known
  - `previous_summary` only when the parent can state it tersely from tracked metadata
  - `next_delta` for the exact next objective
  - `constraints` only when they are explicit and still binding
- Do not use `<parent_context>` for already-clear fresh tasks unless it adds real value.
- Keep `<parent_context>` deterministic and short. Do not turn it into a free-form summary of the whole parent thread.
- For the built-in rescue path, parent-side shaping must happen before the command is handed to the child. The child must not do an additional interpretation pass.
- If the resolved rescue task text is shell-hostile or likely to break a single inline shell string, materialize it into a temporary prompt file first and use `--prompt-file` instead of embedding the task directly in the command.
- Treat any of the following as prompt-file triggers unless the user already supplied `--prompt-file`:
  - multi-line task text
  - single quotes, backticks, or XML-style blocks such as `<task>` / `<output_contract>`
  - long concrete requests where inline shell quoting would be brittle
- When using a prompt file, preserve the exact resolved task text byte-for-byte in that file and point the companion command at that file with an absolute `--prompt-file` path.
- Prefer a temporary path outside the repository checkout, for example under the OS temp directory such as `/tmp` on POSIX systems, so rescue prompt staging does not dirty the repo.
- Materialize that prompt file with a normal file-write tool or other structured write path. Do not try to generate it by re-embedding the long task text inside another fragile one-line shell string.
- If the user is not satisfied with a built-in rescue result, the parent should treat the next rescue request as a follow-up and prefer `--resume` or `--resume-last` with a short delta instruction when a resumable Claude Code session exists.
- The built-in rescue path must use a compact strict forwarding message. It must:
  - identify the child as a transient forwarding worker for Claude Code rescue
  - include exactly one shell command to run
  - run that command as one blocking foreground shell-tool call, not as a background terminal/session
  - do not request a shell session id, poll a shell session later, or return before the companion command exits
  - if the available shell tool is `exec_command`, call it once in non-interactive mode and wait for command exit in that same call
  - for foreground rescue only, tell the child to return that command's stdout text exactly, with no preamble, summary, code fence, trimming, normalization, or punctuation changes
  - tell the child to ignore stderr progress chatter such as `[cc] ...` lines and preserve only the stdout-equivalent final result text
  - if a parent thread id is provided for experimental background notification, allow one extra `send_input` call after a successful shell result and before finishing
  - the child prompt must mention the tool name `send_input` literally; do not replace it with a vague instruction like "send a message to the parent"
  - that `send_input` call must target the provided parent thread id, must happen at most once, and must not run on failure paths
  - that `send_input` call should use the exact tool shape `send_input({ target: <parent-thread-id>, message: <steering-message> })` with no extra prose payload
  - if the parent provided a non-empty parent thread id, do not silently drop the completion notification path from the child prompt
  - that `send_input` message should use a short user-facing template that steers the parent toward explicit result retrieval instead of inlining the raw result
  - if a reserved companion job id is available, use this exact high-level shape for the notification message:
    `Background Claude Code rescue finished. Open it with $cc:result <reserved-job-id>.`
  - if no reserved job id is available, fall back to:
    `Background Claude Code rescue finished. Inspect it with $cc:status first, then use $cc:result for the finished job you want to open.`
  - if the parent thread is already busy with unrelated work, prefer these steering messages over embedding the raw result text
  - do not embed the raw Claude result inside the notification message
  - do not include any other prose in that notification message
  - for background rescue, use that same steering message as the child's own final assistant message instead of echoing the raw companion result
  - tell the child not to inspect the repository, read files, grep, or do the task directly
  - tell the child not to reinterpret routing flags that were already resolved by the parent
  - tell the child to copy the resolved rescue task text byte-for-byte into that exact command after parent-side routing flags are removed
  - explicitly forbid appending terminal punctuation, adding quotes, dropping prefixes such as `completed:`, or stripping leading slash commands such as `/simplify`
  - include one short exact-output example such as `completed:/simplify make the output compact`
  - say that auth/setup failures from the companion must be returned unchanged

Execution:
- Foreground: spawn the rescue subagent, wait for it to finish, and return its stdout.
- Background: spawn the rescue subagent without waiting for it in this turn. The subagent still runs the companion `task` command in the foreground inside its own thread. Background here describes only the parent thread's wait behavior.
- Default background notify: when the parent thread id was captured successfully, the background built-in child may wake the parent with one synthetic follow-up turn after success.

Output:
- Foreground: return the subagent's companion stdout exactly as-is. Do not paraphrase, summarize, or add commentary before or after it.
- Background: do not wait for the subagent output. After launching it, tell the user `Claude Code rescue started in the background. Check the subagent session or $cc:status for progress, and once it's done, we will let you know to see the results.`
- If the companion reports missing setup or authentication, direct the user to `$cc:setup`.
