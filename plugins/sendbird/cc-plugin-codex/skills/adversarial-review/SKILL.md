---
name: adversarial-review
description: 'Run a design-challenging Claude Code review of local git changes in this repository. Args: --wait, --background, --base <ref>, --scope <auto|working-tree|branch>, --model <model>, --effort <low|medium|high|xhigh|max>, [focus text]. Defaults to opus + xhigh effort. Use only when the user wants stronger scrutiny than a normal review, such as explicit tradeoff challenge, risky-change review, or custom focus text.'
---

# Claude Code Adversarial Review

Use this skill when the user wants Claude Code to challenge the implementation approach, design choices, assumptions, or tradeoffs in this repository.

Do not treat `$cc:adversarial-review` as the default review path. Use it only when the user explicitly wants stronger scrutiny than a normal code review.
Good triggers include requests to challenge the design, challenge tradeoffs, pressure-test a risky change, question whether a migration/config/template change really removed the risk, or honor custom focus text that asks for harsher review.
If the user wants Claude Code to go beyond review and perform investigation, validation edits, or implementation work, route to `$cc:rescue` instead.
If the user asks for a local review plus a separate Claude background review and then wants the main Codex thread to aggregate the findings and apply fixes, keep the delegated Claude portion on `$cc:review` unless the user explicitly asks for the adversarial angle.
Unlike `$cc:review`, this skill accepts custom focus text after the flags. The moment the user wants to steer Claude toward a specific angle or risk question, prefer `$cc:adversarial-review`.

Resolve `<plugin-root>` as two directories above this `SKILL.md` file. Always run the companion from that active plugin root:
`node "<plugin-root>/scripts/claude-companion.mjs" adversarial-review ...`

Supported arguments: `--wait`, `--background`, `--base <ref>`, `--scope auto|working-tree|branch`, `--model <model>`, `--effort <low|medium|high|xhigh|max>`, plus optional focus text after the flags (defaults: model=opus, effort=xhigh; sonnet defaults to high; haiku has no effort)

Raw slash-command arguments:
`$ARGUMENTS`

Rules:
- This skill is review-only. Do not fix issues, apply patches, or suggest that you are about to make changes.
- Before launching the review, stay in read-only inspection mode: inspect git status and diff stats only, then ask at most one user question about whether to wait or run in background.
- Preserve the user's scope flags and custom focus text exactly.
- Use the same review target selection as `$cc:review`.

Execution mode rules:
- If the raw arguments include `--wait`, do not ask. Run in the foreground.
- If the raw arguments include `--background`, do not ask. Run in background through the built-in adversarial-review subagent path.
- Otherwise, estimate the review size before asking:
  - For working-tree review, start with `git status --short --untracked-files=all`.
  - For working-tree review, also inspect both `git diff --shortstat --cached` and `git diff --shortstat`.
  - For base-branch review, use `git diff --shortstat <base>...HEAD`.
  - Treat untracked files or directories as reviewable work for auto or working-tree review even when `git diff --shortstat` is empty.
  - Only conclude there is nothing to review when the relevant scope is actually empty.
  - Recommend waiting only when the scoped review is clearly tiny, roughly 1-2 files total and no sign of a broader directory-sized change.
  - In every other case, including unclear size, recommend background.
  - When in doubt, run the review instead of declaring that there is nothing to review.
- Then use `AskUserQuestion` exactly once with two options, putting the recommended option first and suffixing its label with `(Recommended)`:
  - `Wait for results`
  - `Run in background`

Argument handling:
- Preserve the user's arguments exactly.
- Treat `--wait` and `--background` as Codex-side execution controls only. Strip them before calling the companion command.
- Do not weaken the adversarial framing or rewrite the user's focus text.
- `$cc:adversarial-review` uses the same review target selection as `$cc:review`.
- It supports working-tree review, branch review, and `--base <ref>`.
- It does not support `--scope staged` or `--scope unstaged`.
- Unlike `$cc:review`, it can still take extra focus text after the flags.
- The companion review process itself always runs in the foreground. Background mode only changes how Codex launches that command.
- For the detailed execution contract, treat the internal runtime reference at `../../internal-skills/review-runtime/runtime.md` as supporting guidance only. It is an internal reference document, not a public skill to invoke.

Foreground flow:
- Run:
  `node "<plugin-root>/scripts/claude-companion.mjs" adversarial-review --view-state on-success <arguments with --wait/--background removed>`
- Foreground adversarial review belongs to the main Codex thread. Do not spawn a review subagent, do not invoke a generic review-runner role, and do not proxy this foreground path through any background worker abstraction.
- Do not fall back to raw `claude`, `claude-code`, `claude review`, `bash -lc ...claude...`, or any other direct Claude CLI syntax when the companion path is available. The foreground syntax contract here is the resolved companion command above, not a hand-rolled Claude invocation.
- If the resolved companion command fails, surface that failure. Do not silently retry foreground adversarial review through a different CLI shape, a generic review runner, or a custom shell wrapper.
- Present the companion stdout faithfully.
- Do not fix anything mentioned in the review output.

Background flow:
- For background adversarial review, use Codex's built-in `default` subagent instead of a detached background shell command.
- Do not satisfy background adversarial review by using a generic `claude_review_runner`-style helper role, raw Claude CLI, or any other review executor that bypasses the resolved companion command.
- Never satisfy background adversarial review by running the companion command itself with shell backgrounding such as `&`, `nohup`, detached `spawn`, or any equivalent direct background process launch.
- Background here means "spawn the forwarding child via `spawn_agent` and do not wait in the parent turn." The companion adversarial-review command inside that child still runs once, in the foreground, inside the child thread.
- Before spawning the built-in child, capture the review job id plus routing context in one call:
  `node "<plugin-root>/scripts/claude-companion.mjs" background-routing-context --kind review --json`
- If that helper returns a non-empty `jobId`, pass it into the companion command as an internal `--job-id <reserved-job-id>` routing flag.
- If that helper returns a non-empty `ownerSessionId`, include `--owner-session-id <owner-session-id>` in the companion command.
- If it returns an empty `ownerSessionId`, omit `--owner-session-id` entirely. Never leave an empty placeholder such as `--owner-session-id  --job-id`.
- If that helper returns a non-empty `parentThreadId`, pass it into the child prompt as the parent thread id for one-shot completion notification.
- If it returns an empty `parentThreadId`, omit the notification path instead of emitting a blank thread-id placeholder.
- Spawn exactly one transient forwarding child through `spawn_agent` with:
  - `agent_type: "default"`
  - `fork_context: false`
  - `model: "gpt-5.4-mini"`
  - `reasoning_effort: "medium"`
- Prefer a self-contained child message over inheriting parent history. The built-in adversarial-review child should not rely on full parent thread replay for normal operation.
- Only consider `fork_context: true` as a last resort for a short follow-up where essential context truly cannot be summarized. Avoid it for large or long-lived threads because it can exhaust the child context window.
- Before spawning the built-in child, emit one short commentary update that records the attempted subagent model selection. Default text should clearly say the parent is starting the built-in adversarial-review child with `gpt-5.4-mini` at `medium` effort.
- If `spawn_agent` rejects `gpt-5.4-mini` with an explicit model-unavailable error such as `Unknown model`, `model unavailable`, or equivalent "not in list / unavailable" wording, retry once with `model: "gpt-5.4"` and the same `reasoning_effort: "medium"`.
- If that fallback happens, emit one short commentary update that clearly says `gpt-5.4-mini` was unavailable and the parent is retrying with `gpt-5.4`.
- Do not use that fallback for arbitrary failures.
- The built-in child must be a pure forwarder. It should:
  - run exactly one shell command
  - execute:
    `node "<plugin-root>/scripts/claude-companion.mjs" adversarial-review --view-state defer <arguments with --wait/--background removed>`
  - run that command as one blocking foreground shell-tool call, not as a background terminal/session
  - do not request a shell session id, poll a shell session later, or return before the companion command exits
  - if the available shell tool is `exec_command`, call it once in non-interactive mode and wait for command exit in that same call
  - include `--owner-session-id <owner-session-id>` only when the parent resolved a non-empty owner session id
  - include `--job-id <reserved-job-id>` when the parent reserved one
  - never leave an empty routing placeholder such as `--owner-session-id  --job-id`
  - return only that command's stdout exactly, with no added commentary
  - ignore stderr progress chatter such as `[cc] ...` lines and preserve only the final stdout-equivalent result text
  - not inspect the repo or perform the review itself
  - if a parent thread id is available, allow one extra `send_input` call after a successful shell result and before finishing
  - the child prompt must mention the tool name `send_input` literally; do not replace it with a vague instruction like "send a message to the parent"
  - that `send_input` call must target the provided parent thread id, must happen at most once, and must not run on failure paths
  - that `send_input` call should use the exact tool shape `send_input({ target: <parent-thread-id>, message: <steering-message> })` with no extra prose payload
  - if the parent provided a non-empty parent thread id, do not silently drop the completion notification path from the child prompt
  - if a reserved review job id is available, use this exact notification message:
    `Background Claude Code adversarial review finished. Open it with $cc:result <reserved-job-id>.`
  - otherwise fall back to:
    `Background Claude Code adversarial review finished. Inspect it with $cc:status first, then use $cc:result for the finished job you want to open.`
  - that `send_input` message should use one of those exact steering messages instead of inlining the raw review result
  - use these steering messages instead of embedding the raw review result in the notification
  - do not embed the raw Claude result inside the notification message
  - do not include any other prose in that notification message
  - use that same steering message as the child's own final assistant message instead of echoing the raw review result
- Do not wait for completion in this turn.
- After launching, tell the user: `Claude Code adversarial review started in the background. Check the subagent session or $cc:status for progress, and once it's done, we will let you know to see the results.`
- Do not fix anything mentioned in the review output.
