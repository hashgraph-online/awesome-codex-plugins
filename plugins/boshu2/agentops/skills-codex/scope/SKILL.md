---
name: scope
description: Hard-block edits outside declared frozen
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

- Any `Edit`, `Write`, or `Bash` tool call whose target path is **outside** every frozen directory is **rejected** by `hooks/edit-scope-guard.sh` with a structured stderr reason and a non-zero exit code (Codex converts that into a tool-use refusal).
- Edits to paths **under** any frozen directory are allowed.
- When the lock file is missing OR `frozen_dirs` is empty, the hook short-circuits with exit 0 (no enforcement; allow everything).
- The hook fails **open** on malformed JSON or missing target-path fields — do not block when the input contract is violated. Defensive default protects against harness changes.

The lock file is written via `cli/internal/llmwiki/scope_guard.go:SafeAtomicWrite`, so concurrent `freeze` / `unfreeze` calls converge atomically (last writer wins, never tears).

---

## Subcommands

### `$scope freeze <dir>...`

Append one or more directories to the frozen set. Idempotent; re-freezing an already-frozen directory is a no-op. Updates `acquired_at` (ISO-8601) and `acquired_by` (session id or PID) on every write.

### `$scope unfreeze [<dir>]`

Without arguments, clears the entire frozen set. With one or more directory arguments, removes just those entries. Removing a directory that is not frozen is a no-op.

### `$scope status [--json]`

Print the current lock state. With `--json`, emit a single JSON object matching the schema in [references/lock-file-format.md](references/lock-file-format.md). Without flags, print a human-readable summary including each frozen directory, the acquisition timestamp, and the acquiring session.

### `$scope guard` (future combo skill)

Reserved for a follow-up skill that combines `freeze` + status + spawn-orchestration. Not implemented in this release; documented here for forward reference.

---

## Lock File Format

`.agents/scope.lock` is a single JSON object. Full schema lives in [references/lock-file-format.md](references/lock-file-format.md). Key fields:

- `schema_version` — currently `1`
- `frozen_dirs` — list of repo-relative directory prefixes (trailing slash optional)
- `acquired_at` — ISO-8601 UTC timestamp
- `acquired_by` — string identifying the writer (session id, PID, or label)

---

## Examples

### Freezing scope before a swarm wave

**User says:** `$scope freeze cli/cmd/ao/ cli/internal/scope/`

**What happens:**

1. `ao scope freeze cli/cmd/ao/ cli/internal/scope/` writes `.agents/scope.lock` via `SafeAtomicWrite`.
2. `hooks/edit-scope-guard.sh` (registered as PreToolUse on `Edit|Write|Bash`) consults the lock on every subsequent tool call.
3. A worker that tries to `Write` to `skills/foo/SKILL.md` is rejected; a worker editing `cli/cmd/ao/scope.go` proceeds.

### Releasing scope at the end of a wave

**User says:** `$scope unfreeze`

**What happens:**

1. `ao scope unfreeze` rewrites `.agents/scope.lock` with `frozen_dirs: []`.
2. The hook short-circuits to exit 0 on the next tool call.

---

## Notes

- Wave 1 hardcodes the `.agents/scope.lock` path. Wave 2 (issue I5) migrates the path through `lib/ao-paths.sh`.
- The hook's defensive parse on malformed JSON is intentional. See [references/lock-file-format.md](references/lock-file-format.md) for the rationale.
- This skill is purely session-boundary (path-scope freezing within a session). Cron-cadence orchestration lives outside AgentOps on the orchestration substrate (the reference is NTM + MCP + managed-agents), not in an AgentOps-shipped daemon.
- Path-scope freezing handles *where* edits land. For a complementary lane that gates *what* commands run (`rm -rf`, `git reset --hard`, `DROP DATABASE`, `kubectl delete`, `terraform destroy`) — including allowlist layering, one-shot override codes, and PreToolUse wiring — see [references/destructive-command-guard-patterns.md](references/destructive-command-guard-patterns.md). Wire it alongside the scope guard when a wave touches infrastructure or shared data.
- When a workflow needs human approval, hook parity, or simultaneous command review rather than only path freezing, use [references/command-approval-and-hook-guardrails.md](references/command-approval-and-hook-guardrails.md).
- When authoring new hook behavior rather than using scope's existing guard, use the hook authoring guidance in `cc-hooks`.

## References

- [references/lock-file-format.md](references/lock-file-format.md)
- [references/destructive-command-guard-patterns.md](references/destructive-command-guard-patterns.md)
- [references/command-approval-and-hook-guardrails.md](references/command-approval-and-hook-guardrails.md)
- [references/scope.feature](references/scope.feature) — Executable spec: declare in-scope dirs, allow in-scope edits, hard-block out-of-scope edits via PreToolUse hook, report/release scope state (soc-qk4b)
