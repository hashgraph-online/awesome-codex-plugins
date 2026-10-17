---
name: agent-deck-run
description: "Use when delegating a task to a local coding session on a named deck: brief it, launch it detached with agent-deck run, monitor it, review the result against the goal, and resume it with feedback until done."
---

# Agent Deck run (orchestrator)

You are the caller of a session, not the session. Follow the five steps below.

## 0. Check prerequisites first

You must be able to run shell commands on the machine where the coding tool is signed in; otherwise stop and tell the human you cannot use this skill. Then check, read-only, before writing any brief:

```sh
agent-deck --version      # >= 2.1.0
agent-deck status         # Status: running
agent-deck deck list      # the deck the user named exists
claude auth status        # or: codex login status | cursor-agent status | muse --version
```

If anything fails, stop and tell the human exactly what is missing and how to fix it (the `agent-deck-setup` skill lists the fixes). Do not start a run that will fail midway.

Bind the working folder once; `run` refuses an unbound folder ("No deck assigned in <dir>: run `agent-deck use <deck>` there first"):

```sh
cd <dir> && agent-deck use <deck> --client <client>
```

Leave the user's uncommitted changes alone; use a separate git worktree or branch when the repo is dirty.

## 1. Write the brief

Write the brief to a file. It must state the goal, the constraints, the definition of done, what the session must not do, and the tool profile the brief owner chose, and "if unclear, end your turn with the question". For code changes, the definition of done includes committing and pushing a named branch. Keep the user's decisions; label any number you had to assume as an assumption. Never put secrets in the brief.

## 2. Launch detached

The user names the deck; the brief owner picks the tool profile: `readonly` for research, planning, and review, `edit` for coding work. When the brief owner has not said, the default is `readonly`.

```sh
agent-deck run <deck> --client <client> --cwd <dir> --prompt-file <brief-file> --tools readonly --detach
```

Supported `--client` values are `claude`, `codex`, `cursor`, `muse`; `agent-deck run --help` lists the clients. The examples use `claude`; substitute your client. Read the `runId`, pid, and log path from the `run <runId> detached: pid <pid> log <path>` line. If the launch fails closed on a deck binding mismatch, stop and report to the human instead of rebinding.

For per-client flags, resume ids, tool mappings, and trust behavior, see `docs/DELEGATION.md` in the agent-deck repository.

## 3. Monitor

Poll until the state leaves `running`. Poll every 30 seconds: read-only runs typically take about 1–3 minutes, so a 30-second cadence catches the end within one interval without busy-polling.

```sh
agent-deck run status <runId>
agent-deck run status <runId> --json
agent-deck run log <runId> --follow
agent-deck run log <runId> --tail 50
agent-deck run list
```

Log lines look like `<ts> text|tool|result|end ...`; a finished run ends with `result success sessionId=<id> <final text>` and `end sessionId=<id>`. With `--json`, take the final answer from the `result` line's string `result` field (claude, codex, muse), not from the last `text` line; codex token usage is in a separate `usage` field. Read `text` lines for questions; answer from verified facts or ask the human. Read the `state` field (`running|ended|error|died`), the `sessionId`, and the log path. Stop rule: on `died` or `error`, stop polling, read the tail of the log for the failure, and report to the human.

## 4. Review

Judge the session's output against the goal and definition of done from step 1, not against the session's own summary: open the real files, diff, tickets, or PR yourself. For code work, verify it landed: `git ls-remote origin <branch>` matches the session's commit. If it meets the goal, report to the human and stop.

## 5. Resume with feedback

Resume the same session with a feedback brief that quotes the gap found in step 4. Pass `--tools` again with the same profile: the profile is not inherited on resume.

```sh
agent-deck run <deck> --client <client> --cwd <dir> --prompt-file <feedback-file> --tools readonly --resume <sessionId> --detach
```

Repeat steps 3-5 until the goal is met, for at most 3 feedback rounds. If the goal is still not met after round 3, stop and bring the blocker to the human instead of resuming again.

### Corrections from a delegated run
- The party that observed and made the correction files it: the orchestrator files `propose_playbook_patch` on its own bound deck; the delegated session files only when a human corrects it directly.
- Evidence quotes the review gap as `user_feedback_excerpt` plus `runId`, `sessionId`, tool profile, and log path; no secrets in evidence.
- Clearly general lesson: `update` with `add_item` (or `create` when no playbook covers it); not yet general: `signal_only`.
- Cross-deck: `create`/`signal_only` land on the caller's bound deck and `get_playbook` reads only that deck, so for a playbook on another deck file `signal_only` with the ids above.

## Hard rules

- Never pick or change the deck on your own; the user names it.
- Never raise the tool profile from `readonly` to `edit` on your own; only the brief owner does.
- No secrets in briefs or logs.
- Report the `runId`, `sessionId`, tool profile, and log path back to the human.
