# Destructive Command Guard Patterns (Codex)

Scope freezing constrains *where* edits land. A destructive-command guard adds a second lane that constrains *what* commands run, even when the path check passes. Wire it alongside `/scope` whenever a wave touches infrastructure or shared data.

## Guard placement

Hook into PreToolUse for `shell` and `apply_patch`. Compose with the scope-path check:

```
PreToolUse(shell) → scope-path-check → destructive-command-check → allow/deny
```

A failure in either lane rejects the call. Keep the matcher sub-millisecond; fail-open past a hard latency ceiling.

## Pattern catalog

Match by tool family, not by literal regex. Normalize whitespace, quoting, and `--flag=value` vs `--flag value` first.

| Family | Patterns | Why blocked |
|---|---|---|
| Filesystem | `rm -rf` outside scratch dirs, `rm -rf .` in unknown cwd | Recursive deletion of non-scratch content has no general undo |
| Git history | `git reset --hard`, `git checkout -- <file>`, `git clean -fd`, `git stash drop`, `git stash clear` | Destroys uncommitted or stashed work |
| Git remote | `git push --force` (without `--force-with-lease`), `git branch -D`, deleting pushed tags | Rewrites or deletes shared history |
| Database | `DROP DATABASE`, `DROP TABLE`, `TRUNCATE`, `DELETE` without `WHERE` | Schema-level or unbounded deletion |
| Container/k8s | `kubectl delete namespace`, `kubectl delete --all`, `helm uninstall`, `docker system prune -a` | Sweeps live workloads or shared caches |
| Cloud / IaC | `terraform destroy`, `aws s3 rb --force`, `gcloud projects delete` | Tears down co-owned infra |

Pack each non-core family behind an opt-in flag.

## Allowlist + override

Layer three priorities, highest first:

1. Project allowlist (checked-in TOML) — reviewable in PRs, scopes by rule ID and optional path.
2. User allowlist (`~/.config/<guard>/allowlist.toml`) — per-operator habits.
3. One-shot override code printed on every block: short, bound to the exact command + cwd + a short TTL, single use. The human runs the override command; the agent never does.

Every override produces an audit log entry.

## Confirm thresholds

Make strictness configurable so the same binary runs in interactive, CI, and unattended-swarm contexts:

```toml
[thresholds]
mode = "block"          # "block" | "warn" | "log-only"
require_override_for = ["filesystem", "git-history", "database"]
auto_allow_for = ["filesystem.rm-under-build-dir"]
warn_for = ["git-remote.force-with-lease"]
```

Default to `block` on high-blast-radius families; `warn` for variants with a recoverable equivalent.

## Hook protocol

- Trigger: PreToolUse on `shell` / `apply_patch`.
- Input: harness JSON on stdin with the command string.
- Pipeline: quick-reject screen → context sanitization → normalization → allowlist check → pattern match.
- Deny: non-zero exit, structured stderr (rule ID, family, safer-variant suggestion, override code).
- Allow: exit 0, no stdout.

## Failure modes

- Confirmed match → fail-closed. Reject even if the override file is unreadable.
- Infrastructure error (missing config, parse failure, matcher panic) → fail-open with a stderr warning. Mirrors `edit-scope-guard.sh`.
- Latency ceiling exceeded → fail-open.
- Heredocs and inline scripts (`bash -c`, `python -c`, `<<EOF`) → extract the body and rescan; otherwise a one-line wrapper bypasses every rule.
- Path normalization → quoted vs unquoted variants must hit the same rule.

## Wave wiring (recommended)

1. `$scope freeze <dirs>` to bound the edit surface.
2. Enable the destructive-command guard with the families relevant to this repo (filesystem + git-history minimum).
3. Add project allowlist entries for routine safe deletions (e.g. `rm -rf ./build`, `rm -rf ./.next`).
4. Run the wave. Treat blocks as checkpoints: take the safer variant from the rule's suggestion field, or escalate for a one-shot override.
5. After the wave, `$scope unfreeze`. Leave the destructive-command guard loaded — overhead is negligible and the audit log compounds.

The two guards keep independent state but share the same fail-open posture, so a hook outage never silently disables both lanes at once.

---
> Pattern adopted from `dcg` (ACFS skill corpus). Methodology only — no verbatim text.
