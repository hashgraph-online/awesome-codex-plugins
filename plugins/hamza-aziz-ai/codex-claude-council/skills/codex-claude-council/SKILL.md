---
name: codex-claude-council
description: Ask OpenAI Codex (ChatGPT) and Claude the same question through the user's own signed-in CLIs; they reply to each other, round after round, until they agree on one answer. Use when the user asks for both models, a council or debate, a second opinion from ChatGPT/Codex or Claude, a cross-check of an answer, plan or decision, or to discuss something with their Codex or Claude Code session.
---

# Codex–Claude Council

This plugin's `council` MCP server runs the user's local Codex CLI (ChatGPT sign-in) and Claude Code CLI (Claude subscription sign-in). No API keys are used. The two members answer independently, then reply to each other's latest message, round after round, until both agree; one then writes the final answer and the other checks it.

## Pick the tool

| The user wants | Tool |
|---|---|
| A cross-checked answer from both models (decisions, reviews, plans) | `council_ask` |
| To see where the models agree or disagree: both answers and every exchange | `council_debate` (JSON; summarise the agreement and disagreements before quoting details) |
| A quick second opinion from one model | `council_ask_codex` or `council_ask_claude` |
| **You** to discuss with the other model, or names only **their session of the other model** (in Claude Code: "discuss with my Codex session 019a…" or "… my Codex session auth-refactor") | `council_join` (see below) |
| Their existing Claude Code **and** Codex sessions to discuss with each other | `council_ask` / `council_debate` with `claude_session_id` and `codex_session_id` |

## Always pass `workspace` in a project

Pass `workspace`: the absolute path of the project folder you are working in. The members work there in plan mode (Claude) or Codex's read-only sandbox, with the user's own skills, plugins and MCP servers: they read files, search and run read-only commands such as `git log`, `diff` and `blame`. Neither can change anything; they propose changes as plans. In `question`, point them at what matters (files, functions, the failing test, the error or log excerpt, the change you made) instead of pasting whole files. They cannot see this conversation, so state the task and any context that is not in the project. Omit `workspace` only for questions unrelated to any project, and then quote everything they need.

Each member keeps its session for as long as this session runs, so follow-up questions can refer to the earlier discussion.

## Take part yourself: `council_join` and `council_turn`

With `council_join`, you are one of the two members, in this conversation, and the plugin runs only the other model. Set `me` to the model you are (`claude` if you are Claude, `codex` if you are Codex or ChatGPT). If the user gave their session of the other model, by id or by name, pass it as `other_session_id`; otherwise leave it out and the other model starts a new session.

`council_join` (and later `council_turn` or `council_result`) returns "Your turn in the council" with a `council_id` and a `<council_message>`: the same prompt a member gets for that step (answer, exchange, final answer, check). For each turn:

- Write the reply yourself, as a council member: use what you already know from this session and your own tools to read and search, but do not change any files while the council runs, and do not hand the turn to another agent or tool.
- Follow the message's format exactly: an exchange reply or a check ends with `VERDICT: AGREE` or `VERDICT: DISAGREE`; a final answer ends with a `---NOTES---` line and notes. In an exchange, agree only when nothing of substance separates you; do not agree just to end the discussion.
- Send it with `council_turn` (`council_id`, and `text`: your complete reply; only that text reaches the other model). The result is your next turn, the final answer, or "still working" (then call `council_result` with the id).
- Keep going until the final answer arrives, then give it to the user. Do not show every turn unless the user asks.

## Continue the user's own sessions

If the user gives Claude Code or Codex sessions they already have, by id or by the name they gave it with `/rename`, and wants those sessions to discuss, pass `claude_session_id` / `codex_session_id` on `council_ask` / `council_debate`, or `session_id` on `council_ask_claude` / `council_ask_codex`, exactly as the user wrote it. Each is continued in place, with everything it already knows, in plan mode / read-only; its own folder is the workspace unless you pass one. Never pass your own current session (use `council_join` instead), and never guess an id or name. If the tool says no session has that name, tell the user how to find it (`/status` shows the id, `/rename` sets a name). Remind the user not to type in those sessions while the council runs.

A session on another machine is passed as `user@host:<id or name>` (for example `hamza@10.152.15.202:fix-order-dialog-bugs`), exactly as the user gives it: that member runs on that machine through ssh, with its own CLI and sign-in. It needs key-based ssh and Node.js there; if the call fails with "Permission denied (publickey)", tell the user to set up key-based ssh to that host. If a remote member fails for any reason, report the error to the user and stop: never run `claude` or `codex` on that machine yourself (for example `ssh host claude --resume … -p`), since that skips the plan mode and read-only sandbox the council runs members in, and writes into the user's session.

## Options

Pass options only when the user asks for them; the defaults come from the user's config (`codex-claude-council config`).

- **Model and effort:** `model` / `effort` on `council_ask_codex` / `council_ask_claude`; `codex_model`, `codex_effort`, `claude_model`, `claude_effort` on `council_ask` / `council_debate`; `other_model` / `other_effort` on `council_join`. Codex effort: none, minimal, low, medium, high, xhigh. Claude effort: low, medium, high, xhigh, max. Claude models accept aliases such as opus, sonnet or fable. "ChatGPT" means the Codex side.
- **`synthesizer`:** who writes the final answer once both agree, `claude` (default) or `codex`; the other checks it. With `council_join`, you (the host) write it by default. Pass it only when the user names who should write it ("let ChatGPT write the final answer").
- **`max_rounds`:** the number of exchanges (each model replying to the other's latest message): by default at most 5, stopping as soon as both agree. `N` when the user names a number of rounds; `0` when they want agreement without a limit ("until they agree"), which can take a long time.
- **`web_search`:** on by default, so the members can check current versions, APIs and docs. Pass `false` only when the user asks for no internet access.
- **`network`:** off by default. `true` lets Codex's commands reach the network (to call an API or fetch live data), still read-only on disk; the user's config can limit it to some domains. Pass it only when the user asks for it.
- **`skill`:** the name of a skill installed for the council or natively for Claude Code / Codex (the tool descriptions list them), for example `llm-council`, `caveman`, `ponytail` or `graphify`; for several, their names separated by commas (`"llm-council, caveman"`). Pass only the skills the user asks for, by name or by a phrase the skill says triggers it; never add one on your own. The members then use them, including their sub-agents, at the steps where they judge it is needed. If the tool says the skill is not installed, give the user the install command it names.

Report whether the models agreed (the tool says so at the end). If they did not, give the final answer, which sets out the points still in dispute, and summarise them.

## Long runs: `job_id` and `council_result`

A council takes minutes, and some apps end tool calls after about 60 seconds. So every tool returns within about 50 seconds: with the answer, with your turn (`council_join`), or with "still working", the current step and a `job_id`. On "still working":

- Call `council_result` with that `job_id`; it waits up to about 50 seconds and returns the answer (or your next turn) as soon as it is ready. Repeat until it does. The council keeps running between calls.
- Do not start the same question again, and do not tell the user it failed: "still working" is normal. You may briefly say which step it is at.
- `council_cancel` stops a job, for example if the user asks to stop.
- A session is used by one council or question at a time; the others wait, and their step says "Waiting for the … session". If it names a `council_join` job waiting for your reply, that job holds the session until you answer it: send that reply with `council_turn`, or stop that job with `council_cancel`, rather than waiting.

## Problems

- Before a council, the CLIs it runs are checked for a sign-in, and nothing is sent until they are signed in. If one is not, the tool names it and its login command (`codex login` and choose "Sign in with ChatGPT", or `claude auth login`): relay that to the user, then try again.
- For a missing CLI, a sign-in problem or a usage limit, tell the user plainly and suggest `npx -y codex-claude-council doctor`. Do not retry in a loop.
- The server runs on the user's own computer; it does not work from cloud-only sessions without their machine.
