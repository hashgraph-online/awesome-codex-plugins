---
name: assign
description: Assign a task to a specific role on your team.
---

# AgenTeam Assign

Assign a task to a specific team member, independent of the pipeline.

## Process

### 1. Auto-Init Guard

Check for `.agenteam/config.yaml`, `.agenteam.team/config.yaml`, or legacy
`agenteam.yaml` in the project root. If all are missing:
- Create config dir: `mkdir -p .agenteam`
- Copy the template: `cp <plugin-dir>/templates/agenteam.yaml.template .agenteam/config.yaml`
- Set the team name to the project directory name
- Generate agents: `python3 <runtime>/agenteam_rt.py generate`
- Tell the user: "AgenTeam auto-initialized with default roles. Edit `.agenteam/config.yaml` to customize."

### 2. Accept Input

Get the role name and task from the user. Examples:
- `$ateam:assign architect "Review this API design"`
- `$ateam:assign reviewer "Check auth logic in src/auth.py"`
- `@ateam assign researcher to investigate caching strategies`
- `@ateam ask pm what we should build next`

If role or task is missing, ask.

### 3. Validate Role

```bash
python3 <runtime>/agenteam_rt.py roles show <role-name>
```

If the role doesn't exist, show available roles:
```bash
python3 <runtime>/agenteam_rt.py roles list
```

### 4. Check Write Policy

If the role has `can_write: true`, check for active write locks:

```bash
python3 <runtime>/agenteam_rt.py status
```

If a write lock is active and the role needs to write:
- Inform the user: "Write lock held by <active_role>. Wait for completion or
  override with confirmation."
- Do not proceed without user approval.

### 5. Branch Isolation

If the role has `can_write: true`, isolate the work on a dedicated branch
or worktree. Assign ALWAYS applies isolation regardless of pipeline mode
(even `pipeline: hotl`), because assign is user-initiated and outside
HOTL's execution flow.

1. **Preflight:**
   ```bash
   bash <plugin-dir>/scripts/git-isolate.sh preflight
   ```
   - If `not-a-git-repo`: skip isolation (non-git projects work without it)
   - If `dirty-worktree` and mode is serial or worktree: **block.** Tell user:
     "Uncommitted changes detected. Please stash or commit before assigning
     a writing task, to ensure branch isolation."
   - If `detached-head`: **block.** Tell user: "You are in detached HEAD state.
     Please checkout a branch before assigning a writing task."

2. **Capture current branch** (before any git mutation):
   ```bash
   RETURN_BRANCH=$(git rev-parse --abbrev-ref HEAD)
   ```

3. **Get branch plan:**
   ```bash
   python3 <runtime>/agenteam_rt.py branch-plan --task "<task>" --role "<role>"
   ```

4. **Execute the plan:**
   - If `action: create-branch`:
     `bash <plugin-dir>/scripts/git-isolate.sh create-branch <branch> <base>`
   - If `action: create-worktree`:
     `bash <plugin-dir>/scripts/git-isolate.sh create-worktree <path> <branch> <base>`
   - If `action: use-current`: show the warning from the plan. Continue on
     current branch.

5. **Launch agent** on the isolated branch/worktree (step 7 below).

6. **After agent completes:**
   - If `action` was `create-branch`:
     `bash <plugin-dir>/scripts/git-isolate.sh return $RETURN_BRANCH`
     Tell user: "Work is on branch `<branch>`. Merge or create a PR when ready."
   - If `action` was `create-worktree`:
     `bash <plugin-dir>/scripts/git-isolate.sh cleanup-worktree <path>`
     Tell user: "Work is on branch `<branch>`. Worktree cleaned up (or
     preserved if it has uncommitted changes)."

If the role has `can_write: false`, skip this step entirely.

### 6. Resolve Artifact Paths

```bash
python3 <runtime>/agenteam_rt.py artifact-paths
```

Pass the resolved output paths to the agent so it writes artifacts to
the correct location (standalone vs HOTL mode).

### 7. Launch Agent

Before launch, create a durable assignment checkpoint under
`.agenteam/assignments/<assignment_id>.json`. Record `assignment_id`, role,
task, isolated cwd, start time, attempt number, configured wall and idle budget,
last heartbeat, host thread ID when available, and stop reason. Update the
heartbeat while the role is active. On controller restart, verify the recorded
PID/thread before launching anything; resume the existing host thread when the
host supports it. A fresh assignment attempt requires explicit confirmation if
side effects may already have occurred.

Launch the role as a Codex subagent using the generated agent file:
- Agent file: `.codex/agents/<role-name>.toml`
- Pass the task description as the prompt
- Pass relevant project context (current branch, recent changes, etc.)
- Pass artifact paths from step 5

### 8. Collect Output

Present the agent's output to the user with the role name as context:
"**[architect]:** <output>"

### 9. Suggest Next Step

After presenting the role's output, append a handoff suggestion:

| Completing Role | Suggestion |
|----------------|------------|
| researcher | "Next step: @Architect can design a solution based on these findings, or @Pm can turn this into a prioritized strategy. Want me to assign one of them?" |
| pm | "Next step: @Architect can design the technical approach for this. Want me to assign them?" |
| architect | "Next step: @Dev can build an implementation plan and start coding from this design. Want me to assign them?" |
| dev | "Next step: @Qa can write tests for this implementation, then @Reviewer can check it. Want me to assign @Qa?" |
| qa | "Next step: @Reviewer can review the implementation and tests together. Want me to assign them?" |
| reviewer (PASS) | "Review complete -- no blocking findings. Ready to merge or continue." |
| reviewer (WARN) | "Review complete with warnings. @Dev can address the WARN findings if you'd like. Want me to assign them?" |
| reviewer (BLOCK) | "Review blocked on the findings above. @Dev should address the BLOCK items before re-review. Want me to assign them?" |

**Rules:**
- Always present the suggestion as a question, never auto-dispatch.
- If the user says "yes" or confirms, invoke `$ateam:assign` with the suggested role and a task summary derived from the completing role's output.
- If the user says "no", "stop", or changes topic, drop it. Do not re-prompt.
- If the user asks for a different role than suggested, honor their choice.
- Include the suggestion on the same message as the role output.
- If running headless (CI=true or no TTY), omit the handoff suggestion.

## Notes

- Assign works regardless of pipeline setting
- Multiple read-only roles can be assigned in parallel
- Write roles follow the configured write policy
