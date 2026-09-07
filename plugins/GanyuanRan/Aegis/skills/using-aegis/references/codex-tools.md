# Codex Tool Mapping

Skills use Claude Code tool names. When you encounter these in a skill, use your platform equivalent:

| Skill references | Codex equivalent |
|-----------------|------------------|
| `Task` tool (dispatch subagent) | `spawn_agent` (see [Named agent dispatch](#named-agent-dispatch)) |
| Multiple `Task` calls (parallel) | Multiple `spawn_agent` calls |
| Task returns result | `wait` |
| Task completes automatically | `close_agent` to free slot |
| `TodoWrite` (task tracking) | `update_plan` |
| `Skill` tool (invoke a skill) | Skills load natively — just follow the instructions |
| `Read`, `Write`, `Edit` (files) | Use your native file tools |
| `Bash` (run commands) | Use your native shell tools |

## Subagent dispatch requires multi-agent support

Add to your Codex config (`~/.codex/config.toml`):

```toml
[features]
multi_agent = true
```

This enables `spawn_agent`, `wait`, and `close_agent` for skills like `dispatching-parallel-agents` and `subagent-driven-development`.

## Reviewer subagent dispatch

Aegis keeps reviewer prompt content in skill-local templates, not in a root
`agents/` directory. Codex does not have a named agent registry —
`spawn_agent` creates generic agents from built-in roles (`default`,
`explorer`, `worker`).

When a skill says to dispatch a reviewer subagent:

1. Find the relevant skill-local prompt template such as
   `skills/requesting-code-review/code-reviewer.md` or
   `skills/subagent-driven-development/code-quality-reviewer-prompt.md`
2. Read the prompt content
3. Fill any template placeholders (`{BASE_SHA}`, `{WHAT_WAS_IMPLEMENTED}`, etc.)
4. Spawn a `worker` agent with the filled content as the `message`

| Skill instruction | Codex equivalent |
|-------------------|------------------|
| reviewer subagent with `requesting-code-review/code-reviewer.md` | `spawn_agent(agent_type="worker", message=...)` with the filled template |
| `Task tool (general-purpose)` with inline prompt | `spawn_agent(message=...)` with the same prompt |

### Message framing

The `message` parameter is user-level input, not a system prompt. Structure it
for maximum instruction adherence:

```
Your task is to perform the following. Follow the instructions below exactly.

<agent-instructions>
[filled prompt content from the agent's .md file]
</agent-instructions>

Execute this now. Output ONLY the structured response following the format
specified in the instructions above.
```

- Use task-delegation framing ("Your task is...") rather than persona framing ("You are...")
- Wrap instructions in XML tags — the model treats tagged blocks as authoritative
- End with an explicit execution directive to prevent summarization of the instructions

### Boundary

The canonical review prompt is `skills/requesting-code-review/code-reviewer.md`.
Do not reintroduce a root named-agent prompt as a second review checklist.

## Environment Detection

Before the first repo write, the coordinator captures `TaskStartSnapshot` with
read-only commands. Worktree/branch lifecycle skills reuse it and refresh the
state before mutation:

```bash
ROOT=$(git rev-parse --show-toplevel)
HEAD=$(git rev-parse HEAD)
GIT_DIR=$(cd "$(git rev-parse --git-dir)" 2>/dev/null && pwd -P)
GIT_COMMON=$(cd "$(git rev-parse --git-common-dir)" 2>/dev/null && pwd -P)
BRANCH=$(git branch --show-current)
git status --porcelain=v2 --branch
git worktree list --porcelain
git rev-parse --git-path MERGE_HEAD
git rev-parse --git-path rebase-merge
git rev-parse --git-path rebase-apply
git rev-parse --git-path CHERRY_PICK_HEAD
git rev-parse --git-path REVERT_HEAD
git rev-parse --git-path BISECT_LOG
```

- `GIT_DIR != GIT_COMMON` → already in a linked worktree (skip creation)
- `BRANCH` empty → detached HEAD (cannot branch/push/PR from sandbox)
- inspect the returned operation paths for existence before ordinary writes
- record initial staged/unstaged/untracked paths and task-owned path boundary
- preserve pre-existing user state; do not infer cleanliness from task scope

For a ChatGPT desktop app Codex task, also record trusted workspace binding as
exposed by the session/environment or a host-native lifecycle result, plus the
default command `cwd` without a per-command override. Shell output can prove
Git state and default `cwd`; it cannot by itself prove what workspace the app
has bound to the chat.

See `using-git-worktrees` Step 0 and `finishing-a-development-branch` Step 1 for
how each skill uses these signals.

The coordinating Codex agent is the only default Git mutation owner. Spawned
implementers and reviewers share the task workspace and may edit, inspect, test,
and report, but they do not stage, commit, branch, or create/remove worktrees.

## Codex Desktop Managed Worktrees

OpenAI documents ChatGPT desktop app Worktree chats as Codex-managed Git
worktrees associated with chats. Users can select **Worktree** in the composer
or use **Handoff** to move a chat between Local and Worktree; Codex manages the
Git transfer. See:
<https://learn.chatgpt.com/docs/environments/git-worktrees>.

This host lifecycle is distinct from `git worktree add` in a shell:

- an external Git worktree does not rebind the current Codex chat;
- a per-command `workdir` changes only that command's directory;
- `$CODEX_HOME/worktrees` or another managed-looking path is not trusted
  binding evidence by itself;
- Git `HEAD`, branch, and worktree readback cannot prove the app/UI/diff/review
  workspace.

When a worktree is necessary in a Desktop task:

1. If trusted host context says the current chat is already in the intended
   Worktree, reuse it and verify the joint postcondition below.
2. Otherwise use the native Worktree/Handoff capability exposed by the current
   host. Native operations may be deferred; discover capabilities before
   choosing a shell path and follow the live tool schema instead of assuming a
   stable internal tool name.
3. If the operation is UI-only, ask the user to select Worktree or Handoff and
   stop before the first task content or Git-history write. Resume in the bound
   chat and verify the postcondition after the native lifecycle operation.
4. If native binding is required but unavailable or unverifiable, fail closed.
   Do not substitute `git worktree add` plus command-level `workdir`.

Classify the current surface as `managed`, `non-managed`, or `unknown` from
trusted session/host evidence. A missing native tool or absent binding metadata
does not prove `non-managed`; `unknown` fails closed. Codex CLI uses the generic
fallback only when the current session is positively identified as a
non-managed CLI surface.

After native creation or Handoff, verify:

- trusted chat/task workspace;
- default command `cwd` without an override;
- matching Git worktree root;
- intended `HEAD` and branch/detached state.

Compare host-resolved path identity rather than raw strings. The default `cwd`
may be the worktree root or a descendant; Git invoked from that default `cwd`
must resolve to the intended root.

Codex-managed worktrees start in detached `HEAD` by default. Treat that state
as intended only when trusted host binding evidence identifies the current
workspace as the managed worktree; do not create a branch merely to normalize
it. An unexplained detached `HEAD` still stops work.

Preserve an existing unbound manual worktree. Inventory its exact state before
any separately authorized commit/patch transfer, verify the transferred result
inside the bound task, and only then consider owner-proven cleanup.

Codex CLI or another surface positively identified as lacking chat-bound
managed workspace semantics may retain the generic Git fallback in
`using-git-worktrees`; do not classify from the `Codex` product name alone.

## Codex App Finishing

When the sandbox blocks branch/push operations (for example detached HEAD in an
externally managed worktree), preserve the state. After fresh verification the
coordinator may create only a scoped task commit when the environment permits;
otherwise report the blocker and use the App's native controls:

- **"Create branch"** — names the branch, then commit/push/PR via App UI
- **"Hand off to local"** — transfers work to the user's local checkout

The coordinator can still run tests and output suggested branch names, commit
messages, and PR descriptions. Never stage or commit pre-existing user state.
