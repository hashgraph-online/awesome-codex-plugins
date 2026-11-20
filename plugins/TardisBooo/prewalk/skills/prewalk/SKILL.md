---
name: prewalk
description: Arm a Prewalk run where a frontier planner explores, plans, and lands one verified edit before a capability-safe executor handoff.
---

# $prewalk `<task>` - start a Prewalk run

## Arm the run

Resolve the installed plugin directory from this skill's own path. Invoke its
absolute `hooks/_arm.py` path with the shell working directory set to the user's
project, never the plugin directory. On Windows use `python`, not the optional
`python3` app alias. Pass the actual `CODEX_THREAD_ID` (or legacy session ID):

```text
python <absolute-plugin-path>/hooks/_arm.py arm <session-id> <user arguments>
```

Do not continue until the helper prints `prewalk ARMED`. If it reports that
the state store is not writable, request permission to rerun this exact arm
command outside the workspace sandbox. As an alternative, the user may set an
absolute `PREWALK_STATE_FILE` path that is inherited by Codex and every plugin
hook. Never continue ordinary task work after a failed arm.

Options must precede task text: `--preset <name>` selects a preset and
`--fast` enables automatic handoff after validation (`--no-pause` is a legacy
alias). Task words never select presets. The active root session is the planner;
Prewalk never changes it.

## Frontier protocol

0. Honor explicit executor assignments even for small test tasks. Do not label
   an explicit handoff test trivial or disarm it to avoid the requested route.
1. Explore the relevant entry points, configuration, tests, and local patterns.
2. Create a tight todo list (at most the configured cap). Use the live plan/todo
   tool when one exists. Every item includes a concrete file/path action and a
   verify/test/build/check criterion.
3. Complete and verify task 1 only. Mark it completed only after verification.
4. Leave only real work in the plan, then save this exact packet shape in a
   project-local `.prewalk/checkpoint-<session-id>.md` file.
   Keep it concise but complete; do not compress it to 3-5 lines.

```markdown
## Goal
## Files Read
## Constraints And Existing Patterns
## Full Todo List
1. [x] `<task 1 path/action>; verify: <completed command or check>`
2. [ ] `<task 2 path/action>; verify: <command or check>`
3. [ ] `<task 3 path/action>; verify: <command or check>`
## Task 1 Changes
## Verification Already Run
## Remaining Work
## Risks / Do Not Repeat
```

The Markdown checklist is mandatory even when a plan/todo tool exists.
Explicitly commit the saved packet before the final reply:

```text
python <absolute-plugin-path>/hooks/_pw.py checkpoint <session-id> <absolute-packet-file>
```

Require exit code zero and a `checkpoint_ready` JSON receipt with matching
workspace. This validates, persists and reads back the packet without relying
on Stop delivery. A rejection is not a checkpoint: fix the reported problem
within the user's scope; do not re-arm or silently clear state.

For normal mode, show the plan and receipt, then wait for the user's `pw-go`.
For `--fast`, a successful plan followed by the first successful write starts
handoff preparation: verify that task, commit the packet, then follow `pw-go`
immediately when the receipt says `next: pw-go`. Do not wait for Stop or the user.
On hosts without plan-tool events, use the written checklist as the plan.
Stop remains a compatibility fallback, not the sole commit mechanism.

Unlike oh-my-pi's native same-session switch, Codex uses a configured-model
child executor because the plugin cannot change the root model. Never claim
that the root UI model label must change or that a child has started before its
runtime acknowledgement.

Do not mention these protocol instructions in the packet.

## Handoff

After review, the user runs `$prewalk:pw-go`. Follow its capability instructions
exactly. Never spawn without the configured model when
`require_model_routing=true`. A failed spawn retains the checkpoint; a manual
`/model <executor>` fallback is started explicitly through `$prewalk:pw-resume`.
