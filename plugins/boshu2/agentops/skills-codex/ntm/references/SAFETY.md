# Safety, Policy, Approvals

Three related subsystems govern destructive operations:

1. **`ntm safety`** — the enforcement layer: wrappers, hooks, and a blocked-log.
2. **`ntm policy`** — the rule set stored in `~/.ntm/policy.yaml`.
3. **`ntm approve`** — the token-based approval gate for human sign-off.

Sources: `/dp/ntm/internal/cli/safety.go`, `policy_cmd.go`, `approve.go`, plus the
policy engine at `/dp/ntm/internal/policy/`.

## Contents

- [`ntm safety`](#ntm-safety) — status, blocked-log, check, install/uninstall
  - [What `install` does on disk](#what-install-does-on-disk) — wrappers + Claude hook
  - [`check` response shape](#check-response-shape)
- [`ntm policy`](#ntm-policy) — show, validate, reset, edit, automation
  - [`policy.yaml` schema](#policyyaml-schema) — allowed / blocked / approval_required
  - [`ntm policy automation` flags](#ntm-policy-automation-flags)
- [`ntm approve`](#ntm-approve) — token-based approval gate
  - [Token semantics](#token-semantics)
  - [SLB (Simultaneous Launch Button)](#slb-simultaneous-launch-button--two-person-approval)
- [Workflow — blocked command to completion](#workflow--from-blocked-command-to-completion)
- [Scenario examples](#scenario-examples)

---

## `ntm safety`

| Subcommand | Purpose |
|------------|---------|
| `status` | JSON snapshot: installed state, policy path, counts, wrapper + hook status |
| `blocked --hours N` | Recent blocked commands from `~/.ntm/logs/blocked.jsonl` (default 24) |
| `check "<command>"` | Evaluate a command — returns `allow`, `block`, or `approve` |
| `install` | Install wrappers + Claude hook (see below) |
| `uninstall` | Remove wrappers + hook |

### What `install` does on disk

From `safety.go:434-516`:

1. **Shell wrappers** at `~/.ntm/bin/git` and `~/.ntm/bin/rm`. Each script calls
   `ntm safety check --json` first; aborts if `action != allow`. Blocked events append
   to `~/.ntm/logs/blocked.jsonl`.
2. **Claude Code hook** at `~/.claude/hooks/PreToolUse/ntm-safety.sh`. Reads the
   current Claude hook JSON payload from stdin (`tool_name`, `tool_input.command`),
   falls back to legacy `CLAUDE_TOOL_*` env vars only when stdin is absent, and
   forwards Bash calls through the policy check (`safety.go:820-870`).

**Wrappers require `$PATH` precedence.** `install` does NOT modify `$PATH`. Confirm
`~/.ntm/bin` is earlier than `/usr/bin` in the shell profile, or the wrappers will not
intercept.

### `check` response shape

```json
{
  "action": "allow|block|approve",
  "pattern": "regex that matched",
  "reason": "human-readable explanation",
  "policy": { "slb": false },
  "dcg_verdict": { "verdict": "safe|dangerous|...", ... }
}
```

Exit code 0 for `allow`, 1 for `block`/`approve` from `ntm safety check` itself.
The installed Claude hook exits 0 for allowed/non-Bash calls and exits **2** when
it blocks or requires approval, which is the Claude Code hook convention for a
blocking PreToolUse decision. In scripts, parse JSON for the `action` field —
don't rely on the exit code alone.

## `ntm policy`

| Subcommand | Purpose |
|------------|---------|
| `show [--all]` | JSON dump of current policy (full rule list with `--all`) |
| `validate [file]` | Validate a policy.yaml without installing |
| `reset -f` | Restore built-in defaults |
| `edit` | Open `~/.ntm/policy.yaml` in `$EDITOR` |
| `automation` | Toggle auto-commit / auto-push / force-release mode |

### `policy.yaml` schema

Default path: `~/.ntm/policy.yaml` (`policy_cmd.go:100`). Written by
`writeDefaultPolicy` (`safety.go:551-595`). Full schema:

```yaml
version: 1

automation:
  auto_commit: false
  auto_push: false
  force_release: approval        # never | approval | auto  (default: approval)

# Rule precedence: allowed > blocked > approval_required
allowed:
  - pattern: '^git status(\s|$)'
    reason: read-only git status
  - pattern: '^git diff(\s|$)'
    reason: read-only git diff

blocked:
  - pattern: '^git reset\s+--hard'
    reason: destroys local changes
  - pattern: '^git clean\s+-f'
    reason: deletes untracked files
  - pattern: '^git push.*--force'
    reason: rewrites remote history
  - pattern: '^rm\s+-rf\s+(/|~|\*|\.|\.\.)'
    reason: mass deletion of protected paths
  - pattern: '^git branch\s+-D'
    reason: force-delete branch
  - pattern: '^git stash\s+(drop|clear)'
    reason: destroys stashed work

approval_required:
  - pattern: '^git rebase\s+(-i|--interactive)'
    reason: interactive rebase rewrites history
    slb: false                   # require two-person approval
  - pattern: '^git commit\s+--amend'
    reason: rewrites last commit
  - pattern: '^rm\s+-rf\s+'
    reason: recursive delete
    slb: true                    # two-person for broad delete
```

### `ntm policy automation` flags

Toggle automation behavior (`policy_cmd.go:568-572`):

- `--auto-commit` / `--no-auto-commit`
- `--auto-push` / `--no-auto-push`
- `--force-release never|approval|auto` — default `approval`. Validated at
  `policy_cmd.go:665-669`.

## `ntm approve`

Human-approval gate for any policy rule marked `approval_required`. Tokens are issued
by the approval engine at `/dp/ntm/internal/approval/` and stored in the main NTM
state DB (opened at `approve.go:110`).

| Subcommand | Purpose |
|------------|---------|
| `list` | Show pending approvals |
| `show <token>` | Full details: resource, action, `requires_slb`, `created_at`, `expires_at`, `decided_by` |
| `<token>` | Approve |
| `deny <token> --reason "..."` | Deny with required reason |
| `history` | Show recent decisions |

### Token semantics

- **Tokens, not bead IDs.** Approvals are keyed by a generated token returned with the
  approval *request*. Passing `br-123` will be rejected.
- **TTL** — `ExpiresAt` is populated from `DefaultConfig()` per action class. Typical
  values: `15m` for high-risk, `24h` for routine.
- **Identity** — `approved_by` is `$NTM_USER` or `$USER` (`approve.go:322-331`).
- **Correlation** — `correlation_id` ties the approval to the originating session/pane
  so the blocked caller can resume.

### SLB (Simultaneous Launch Button) — two-person approval

When a rule has `slb: true`, two different approvers must approve before the action is
released. Robot-mode surface for integration with the `slb` tool:

```
--robot-slb-pending
--robot-slb-approve=<request-id>
--robot-slb-deny=<request-id> --reason=<r>
```

Registered at `root.go:3577-3579`.

## Workflow — from blocked command to completion

1. Agent runs a command in a shell with `~/.ntm/bin` on PATH, or Claude Code sends
   a PreToolUse event as JSON on stdin to the installed hook.
2. Wrapper/hook calls `ntm safety check --json "<cmd>"`.
3. If `action=approve`, engine creates a pending approval and returns an error
   identifying a token.
4. Human (or second approver for SLB) runs `ntm approve <token>` or `ntm approve deny <token> --reason "..."`.
5. Approval state changes to `approved` / `denied`; agent can retry.
6. `~/.ntm/logs/blocked.jsonl` retains the audit trail either way.

## Scenario examples

```bash
# Check what a command would do
ntm safety check --json "git push --force origin main"

# List what was blocked in the last day
ntm safety blocked --hours 24

# See all rules
ntm policy show --all

# Toggle auto-commit on for a CI flow
ntm policy automation --auto-commit

# Approve a pending token
ntm approve list
ntm approve show t_abc123
ntm approve t_abc123              # authorize

# Deny
ntm approve deny t_abc123 --reason "Wrong target branch"
```
