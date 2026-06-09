---
name: writing-plans
description: Use after design approval to create a dated executable workflow file with bite-sized tasks, exact file paths, and loop/gate definitions.
---

# Writing HOTL Plans

## Overview

Produce a dated workflow file that `loop-execution` can execute. The canonical filename is `YYYY-MM-DD-<slug>-workflow.md`, where `<slug>` is a short kebab-case identity derived from the intent (e.g., `2026-04-22-add-rate-limiting-workflow.md`). Each step should be 2-5 minutes of work. Include loop conditions and gates from the design's governance contract.

**Announce:** "I'm using the writing-plans skill to create the executable workflow."

## Output Filename

Save as `YYYY-MM-DD-<slug>-workflow.md`, where:

- `YYYY-MM-DD` is the current local date
- `<slug>` is a short kebab-case semantic identity derived from the intent (e.g., `add-user-auth`, `refactor-api`)

Examples:

- `2026-04-22-add-user-auth-workflow.md`
- `2026-04-22-refactor-api-workflow.md`

The date makes workflow revisions easy to sort chronologically. The semantic identity remains `<slug>`, not the date-prefixed filename.

## Semantic Identity

The canonical workflow filename is human-friendly, but the stable execution identity is still `<slug>`.

- Filename: `YYYY-MM-DD-<slug>-workflow.md`
- Semantic identity: `<slug>`
- Default branch derivation: `hotl/<slug>`

When a later workflow revision is created for the same feature, it should use a new dated filename while keeping the same semantic identity.

## Output Directory

Default: `docs/plans`. Opt-in override via `.hotl/config.yml: workflows_dir: <path>`. Resolution procedure:

1. Resolve the install path of `hotl-config-resolve.sh` using the same six-location rule documented for `document-lint.sh` and `hotl-config.sh` (see `skills/document-review/SKILL.md`):
   1. In-repo: `scripts/hotl-config-resolve.sh`
   2. Codex native-skills install: `~/.codex/hotl/scripts/hotl-config-resolve.sh`
   3. Codex plugin install: `~/.codex/plugins/hotl-source/scripts/hotl-config-resolve.sh`
   4. Codex plugin cache fallback: `~/.codex/plugins/cache/codex-plugins/hotl/*/scripts/hotl-config-resolve.sh`
   5. Cline install fallback: `~/.cline/hotl/scripts/hotl-config-resolve.sh`
   6. Claude Code plugin fallback: `~/.claude/plugins/hotl/scripts/hotl-config-resolve.sh`

2. Invoke the resolver as a command proxy — it forwards argv to `hotl-config.sh`, no intermediate path-locator step:

   ```bash
   bash <resolved-hotl-config-resolve.sh> get workflows_dir --default=docs/plans
   ```

3. Use the returned directory as the output location. `docs/plans` is the canonical default. Any other value is an opt-in override — write `YYYY-MM-DD-<slug>-workflow.md` inside that directory, creating it if needed.

Projects with no `.hotl/config.yml` receive `docs/plans` from the `--default=docs/plans` fallback.

Format:

```markdown
---
intent: [from design's intent contract]
success_criteria: [from design's intent contract]
risk_level: low | medium | high
auto_approve: true | false
# branch: custom/branch-name   # optional — execution derives hotl/<slug> if absent
# worktree: host                # optional: only when a host tool already put this task on a feature-branch worktree
# dirty_worktree: allow         # optional — proceed even if non-HOTL files are uncommitted
---

## Steps

- [ ] **Step N: [Step name]**
action: [what to do]
loop: false | until [condition]
max_iterations: [number, default 3]
verify: [scalar command OR typed block]
gate: human | auto   # optional
```

**CRITICAL — field indentation:** `action:`, `loop:`, `verify:`, `max_iterations:`, and `gate:` MUST start at column 0 (no leading spaces). The document linter matches `^action:`, `^loop:`, etc. — any indentation (even 2 spaces under the list item) will fail validation. Only the sub-fields of structured `verify:` blocks (like `type:`, `path:`, `assert:`) are indented.

## Typed Verification

Choose the appropriate verify type for each step:

- **shell** — for test suites, linters, build commands (default; scalar shorthand accepted)
- **browser** — for UI work requiring visual inspection (capability-gated; falls back to human-review)
- **human-review** — for subjective quality checks with no automated signal
- **artifact** — for verifying files/outputs exist and meet criteria

```yaml
# Scalar shorthand (type: shell)
verify: pytest tests/ -v

# Structured
verify:
  type: browser
  url: http://localhost:3000/dashboard
  check: priority badge renders with correct color

# Artifact with structured assert
verify:
  type: artifact
  path: migrations
  assert:
    kind: matches-glob
    value: "*.sql"

# Greenfield scaffold check
verify:
  type: artifact
  path: src
  assert:
    kind: exists

# Multiple checks per step
verify:
  - type: shell
    command: npm test
  - type: artifact
    path: coverage/lcov.info
    assert:
      kind: exists
```

## Step Granularity

Break work into atomic steps:
- "Write failing test for X" (loop: false, verify: pytest)
- "Implement X" (loop: until tests pass, verify: pytest)
- "Fix lint errors" (loop: until clean, verify: ruff check .)
- "Verify UI renders correctly" (loop: false, verify: type: browser)
- "Human review of security logic" (loop: false, gate: human — REQUIRED for risk_level: high)

## No Placeholders

Every workflow step must contain enough concrete information for an agent to execute it without guessing. These are plan failures:

- `TBD`, `TODO`, `later`, `fill in`, or empty sections
- Vague instructions such as "add validation", "handle edge cases", "improve error handling", or "update docs" without exact files and success signals
- "Similar to Step N", "repeat the pattern", or references that require reading another step to know what to do
- Functions, files, commands, artifacts, or config keys referenced before they are defined
- Verification that does not prove the step's action worked
- Human-review checks where an automated shell, browser, or artifact check would provide a deterministic signal

If a step cannot be made concrete yet, stop and ask for clarification instead of saving the workflow.

## Branch And Worktree Authoring Guidance

- Default execution branch is `hotl/<slug>` unless the workflow frontmatter sets `branch: ...`
- Default execution mode is an isolated worktree; HOTL copies the workflow into that worktree at the same relative path before execution
- Use `branch:` only when downstream tooling or verify logic truly depends on a specific branch name
- Use `worktree: false` only when execution must stay in the current checkout rather than a separate worktree
- To keep execution on the exact current branch, set both `branch: <current-branch>` and `worktree: false`
- Use `worktree: host` when Codex or another host tool already created the execution worktree and HOTL should use the current feature branch exactly as-is
- Avoid brittle verify steps such as `git branch --show-current | grep '^feature/'` unless the workflow pins `branch:` to match that exact convention
- If a step must confirm the workflow file exists, use its repo-relative path; HOTL preserves that relative path inside the isolated worktree
- If the workflow is authored on a non-`main`/`master` branch and does not pin `branch:` or `worktree:`, execution should pause and ask whether to continue on the current branch or use HOTL's isolated execution branch/worktree

Example:

- If verify expects `pv6-ui/...`, set `branch: pv6-ui/plan-amendments`
- If branch name does not matter, let HOTL derive `hotl/<slug>` and do not assert a custom prefix
- If you want to keep using `pv6-ui/plan-amendments` itself, set `branch: pv6-ui/plan-amendments` and `worktree: false`
- If Codex already opened the task in a worktree on `pv6-ui/plan-amendments`, set `worktree: host` and omit `branch:`

## Artifact Verification Rules

- Prefer `kind: exists` when the step creates a new file or directory from scratch
- Use `kind: matches-glob` only when `path` is an existing directory and `value` is a filename glob such as `*.tsx` or `*.md`
- Do not put directory segments in `value`; write `path: src` with `value: "*.tsx"`, not `path: .` with `value: "src/*.tsx"`
- For greenfield frontend scaffolds, Step 1 should usually verify `src` or `package.json` with `kind: exists`, not `matches-glob`

## risk_level Guidelines

- **low:** UI changes, new endpoints, non-critical features
- **medium:** Schema changes, refactors, performance work
- **high:** Auth/authz, encryption, privacy logic, billing, multi-tenant isolation

`risk_level: high` **always** generates `gate: human` on security-sensitive steps, regardless of `auto_approve`.

## Self-Check Loop

After saving the workflow file, run a self-check before offering execution options. Review the workflow for:

- **Step sizing** — each step should be 2-5 minutes of atomic work
- **No placeholders** — no TBD/TODO text, vague instructions, undefined references, or "similar to Step N" shortcuts
- **Verify coverage** — every looped step has a verify command that tests what the step claims
- **Gate placement** — risky steps (auth, encryption, billing, secrets) have `gate: human`
- **Loop safety** — `max_iterations` is reasonable (typically 3-5)
- **Ordering** — logical dependencies between steps are respected

If issues are found, fix them in the workflow file and re-check until clean. Do not ask the user to review — this is an internal quality pass.

## After Saving

Once the self-check passes, offer execution options:

**"Workflow saved to `<resolved-workflows-dir>/YYYY-MM-DD-<slug>-workflow.md`. How would you like to execute?"**

Present the three execution modes using the current host tool's native invocation style. Never show Claude Code slash commands in Codex or any other skill-based agent.

Use these mappings:

1. **Loop execution (this session)** — runs steps autonomously with auto-approve
   - **Codex:** ask me to use `$hotl:loop-execution` on `<resolved-workflows-dir>/YYYY-MM-DD-<slug>-workflow.md`
   - **Claude Code:** `/hotl:loop <resolved-workflows-dir>/YYYY-MM-DD-<slug>-workflow.md`
2. **Manual execution** — linear execution with explicit checkpoints
   - **Codex:** ask me to use `$hotl:executing-plans` on `<resolved-workflows-dir>/YYYY-MM-DD-<slug>-workflow.md`
   - **Claude Code:** `/hotl:execute-plan <resolved-workflows-dir>/YYYY-MM-DD-<slug>-workflow.md`
3. **Subagent execution (this session)** — delegates implementation-friendly steps to fresh subagents while the controller keeps gates and verification
   - **Codex:** ask me to use `$hotl:subagent-execution` on `<resolved-workflows-dir>/YYYY-MM-DD-<slug>-workflow.md`
   - **Claude Code:** `/hotl:subagent-execute <resolved-workflows-dir>/YYYY-MM-DD-<slug>-workflow.md`

If a previous run was interrupted, point the user to the host tool's native resume entry point.
- **Codex:** ask me to use `$hotl:resuming` on `<resolved-workflows-dir>/YYYY-MM-DD-<slug>-workflow.md`
- **Claude Code:** `/hotl:resume <resolved-workflows-dir>/YYYY-MM-DD-<slug>-workflow.md`
- **Other agents:** use that agent's native skill/command invocation instead of inventing Claude-style slash commands

*(Always tell the user the exact workflow filename so they can pass it to the execution request if multiple workflow files exist.)*

If execution starts from a non-`main`/`master` branch and the workflow does not already pin `branch:` or `worktree:`, tell the user HOTL will ask one more continuity question at execution time:
- continue on the current branch in this checkout
- use HOTL's isolated execution branch/worktree (recommended)
- choose a custom execution branch
