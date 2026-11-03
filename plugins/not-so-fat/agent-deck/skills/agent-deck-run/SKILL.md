---
name: agent-deck-run
description: "Use when delegating a task to another coding session on a deck: brief it, start it through Agent Deck MCP (start_run), monitor it (get_run), review the result against the goal, and resume (start_run with resumeSessionId) or cancel (cancel_run) until done."
---

# Agent Deck run (orchestrator)

You are the caller of a session, not the session. The run executes on the Agent Deck host, in the workspace your session was launched for, on your session's current deck. You drive it only through Agent Deck MCP tools: `get_session_context`, optional `switch_deck`, `start_run`, `get_run`, and `cancel_run`. Your own shell is not the Agent Deck host.

## 0. Bootstrap

Call `get_session_context`. It names the effective deck. If the user wants the run on another deck, call `switch_deck` with the deck the user named and wait for human approval, then call `get_session_context` again and confirm the new deck. Use "This session only" unless the user asks to change the workspace default.

Leave the user's uncommitted changes alone.

## 1. Write the brief

Build the brief in memory as the `prompt` text; no prompt file is needed. It must state the goal, the constraints, the definition of done, what the session must not do, the tool profile the brief owner chose, and "if unclear, end your turn with the question". For code changes, the definition of done includes committing and pushing a named branch. Keep the user's decisions; label any number you had to assume as an assumption. Never put secrets or host credentials in the brief.

## 2. Start

The user names the deck; the brief owner picks the tool profile: `readonly` for research, planning, and review, `edit` for coding work. When the brief owner has not said, use `readonly`. Always pass `tools` explicitly.

```json
start_run { "client": "claude", "prompt": "<brief>", "tools": "readonly" }
```

- `client`: `claude`, `codex`, `cursor`, or `muse`.
- `prepareFinalization: true` only with `tools: "edit"` when the brief owner wants a finalization-ready edit run (clean Git worktree required).
- `playbookVersion: { "playbookId": "pb_…", "versionId": "…" }` only when the user asks to pin one playbook version (for example a baseline evaluation).
- `start_run` takes no deck and no cwd: the deck is the session's current deck and the cwd is the launch workspace.

It returns `{ runId, state }`.

## 3. Monitor

Call `get_run { "runId": "<runId>" }` about every 30 seconds. Read-only runs typically take 1–3 minutes, so this cadence catches the end within one interval without busy-polling. Pass the returned `nextCursor` back as `after` to read only new events. The run is finished when `state` is `ended`, `error`, `died`, or `canceled`; the terminal event is then already in the page. Keep paging until a page returns no events.

Take the final answer from the `result` event, not from the last `text` event. Read `text` events for questions and answer them from verified facts or ask the human. Record `runId`, `sessionId`, `tools`, and `state`.

## 4. Review

Judge the output against the goal and definition of done from step 1, not against the session's own summary. Check the real artifacts you can reach: files in your workspace, the diff, tickets, the PR. For code work, confirm the pushed branch and commit the session names. If it meets the goal, report to the human and stop.

## 5. Resume or cancel

To resume, call `start_run` again with a feedback brief that quotes the gap you found in step 4. Pass `resumeSessionId` set to the run's `sessionId` and pass `tools` again with the same profile, because the profile is not inherited. Then return to step 3.

```json
start_run { "client": "claude", "prompt": "<feedback brief>", "tools": "readonly", "resumeSessionId": "<sessionId>" }
```

You can resume for at most 3 feedback rounds. If the goal is still not met after round 3, stop and bring the blocker to the human instead of resuming again.

To stop a live run (the human asks for it, or the brief is wrong), call `cancel_run { "runId": "<runId>" }`. Canceling twice is safe: a repeat, or a cancel on a finished run, returns the current status unchanged.

## Failures: stop and report

On each failure below, report it in one or two sentences with the error code and stop. Do not work around it from your own shell.

| Failure | What you see | Next action |
|---|---|---|
| Agent Deck MCP missing | No `get_session_context` / `start_run` tools, the tool call fails, or `GRANT_REQUIRED` | Report that Agent Deck MCP is unavailable in this session. Stop. The human fixes the connection. |
| No launch workspace | `WORKSPACE_REQUIRED` | Report that this session was launched without an execution workspace. Stop. Only the launcher can supply it. |
| Workspace gone | `WORKSPACE_INVALID` | Report that the launch workspace no longer exists on the host. Stop. |
| Provider unavailable | `CLIENT_UNAVAILABLE`, or `PROFILE_UNSUPPORTED` | Report which client is unavailable on the host (missing or signed out) or cannot enforce the profile. Stop. Do not pick a different client unless the user says so. |
| Deck switch not approved | `switch_deck` rejected or expired, `DECK_FIXED`, or `ADMIN_REQUIRED` | Report that the deck was not switched and that the session is still on the previous deck. Do not start the run on the old deck unless the user says so. Stop. |
| Run failed | `state` is `error` or `died` | Report the `runId`, `sessionId`, state, and the error event's message. Stop. Do not start it again on your own. |
| Run canceled | `state` is `canceled` | Report that the run was canceled and by whom, if known. Stop. |
| Out of scope | `RESOURCE_OUT_OF_SCOPE` or `RUN_NOT_FOUND` | Report that the run is not reachable from this session's deck and workspace. Stop. |
| Bad request | `INVALID_REQUEST`, `RESUME_UNVERIFIED`, `FINALIZATION_INVALID`, `INDEX_DIRTY` | Fix the argument only if the brief owner's intent is clear (for example, a wrong `sessionId`). Otherwise report and stop. |

## Report

Report the `runId`, `sessionId`, tool profile, terminal state, and the result (or the failure) to the human. Do not report a host log path; the durable record is `get_run`.

### Corrections from a delegated run
- The party that observed and made the correction files it: the orchestrator files `propose_playbook_patch` on its own bound deck; the delegated session files only when a human corrects it directly.
- Evidence quotes the review gap as `user_feedback_excerpt` plus `runId`, `sessionId`, and tool profile; no secrets in evidence.
- Clearly general lesson: `update` with `add_item` (or `create` when no playbook covers it); not yet general: `signal_only`.
- Cross-deck: `create`/`signal_only` land on the caller's bound deck and `get_playbook` reads only that deck, so for a playbook on another deck file `signal_only` with the ids above.

## Hard rules

- Delegate only through Agent Deck MCP. Never run the Agent Deck command-line tool, call the host's loopback ports, inspect host processes, or install a second Agent Deck copy as a fallback. If MCP cannot do it, report and stop.
- Never pick or change the deck on your own; the user names it, and a switch needs human approval.
- Never raise the tool profile from `readonly` to `edit` on your own; only the brief owner does.
- No secrets in briefs, prompts, or reports.
