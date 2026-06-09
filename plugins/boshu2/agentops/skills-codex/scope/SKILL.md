---
name: scope
description: "Run scope."
---
# $scope — Edit Scope Guard

> **Purpose:** Declare which directories are in scope for the current work session. Edits outside the declared scope are hard-blocked by a PreToolUse hook.

**YOU MUST EXECUTE THIS WORKFLOW. Do not just describe it.**

---

## Quick Start

```bash
$scope freeze cli/cmd/ao/                   # Freeze a single directory
$scope freeze cli/cmd/ao/ skills/scope/     # Freeze multiple (additive)
$scope unfreeze cli/cmd/ao/                 # Remove one frozen directory
$scope unfreeze                             # Clear ALL frozen directories
$scope status                               # Show current lock state
$scope status --json                        # JSON output
```

---

## Behavior Contract

When `.agents/scope.lock` declares one or more `frozen_dirs`:

- Any `shell` / `apply_patch` tool call whose target path is **outside** every frozen directory is **rejected** by `hooks/edit-scope-guard.sh` with a structured stderr reason and a non-zero exit code.
- Edits to paths **under** any frozen directory are allowed.
- When the lock file is missing OR `frozen_dirs` is empty, the hook short-circuits with exit 0 (no enforcement).
- The hook fails **open** on malformed JSON or missing target-path fields. Defensive default protects against harness changes.

The lock file is written via `cli/internal/llmwiki/scope_guard.go:SafeAtomicWrite`, so concurrent `freeze` / `unfreeze` calls converge atomically.

---

## Subcommands

### `$scope freeze <dir>...`

Append one or more directories to the frozen set. Idempotent.

### `$scope unfreeze [<dir>]`

Without arguments, clears the entire frozen set. With arguments, removes just those entries.

### `$scope status [--json]`

Print the current lock state. With `--json`, emit a JSON object matching the schema in [references/lock-file-format.md](references/lock-file-format.md).

### `$scope guard` (future combo skill)

Reserved for a follow-up combo skill. Not implemented in this release.

---

## Lock File Format

`.agents/scope.lock` is a JSON object. Full schema in [references/lock-file-format.md](references/lock-file-format.md).

---

## Notes

- Wave 1 hardcodes `.agents/scope.lock`. Wave 2 (I5) routes through `lib/ao-paths.sh`.
- Hooks (session-boundary) and `agentopsd` (cron-cadence) compose; this skill is session-boundary only.
- Path-scope freezing handles *where* edits land. For a complementary lane that gates *what* commands run (`rm -rf`, `git reset --hard`, `DROP DATABASE`, `kubectl delete`, `terraform destroy`) — including allowlist layering, one-shot override codes, and PreToolUse wiring — see [references/destructive-command-guard-patterns.md](references/destructive-command-guard-patterns.md). Wire it alongside the scope guard when a wave touches infrastructure or shared data.
- When a workflow needs human approval, hook parity, or simultaneous command review rather than only path freezing, use [references/command-approval-and-hook-guardrails.md](references/command-approval-and-hook-guardrails.md).
- When authoring new hook behavior rather than using scope's existing guard, use `$hooks-authoring`.

## References

- [references/lock-file-format.md](references/lock-file-format.md)
- [references/destructive-command-guard-patterns.md](references/destructive-command-guard-patterns.md)
- [references/command-approval-and-hook-guardrails.md](references/command-approval-and-hook-guardrails.md)

## Local Resources

### references/

- [references/lock-file-format.md](references/lock-file-format.md)
- [references/destructive-command-guard-patterns.md](references/destructive-command-guard-patterns.md)
- [references/command-approval-and-hook-guardrails.md](references/command-approval-and-hook-guardrails.md)
