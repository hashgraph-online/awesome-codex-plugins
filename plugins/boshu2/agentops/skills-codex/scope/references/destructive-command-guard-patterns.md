# Destructive Command Guard Patterns

A scope guard freezes *where* edits land. A destructive-command guard adds an orthogonal lane: freezing *what* commands a worker may execute, regardless of which directory it touches. This reference distills the methodology so a future scope-pack contributor can wire one in without reinventing the contract.

## Why a separate guard

Scope-only enforcement leaves a gap. A worker can stay inside the frozen directory and still run something irrecoverable from there — `rm -rf .`, `git reset --hard`, `DROP DATABASE`, `kubectl delete -A`, `terraform destroy`. The directory check passes; the blast radius does not.

The destructive-command guard sits in the same PreToolUse position as `edit-scope-guard.sh`, but its predicate is the command string rather than the target path. The two compose cleanly:

```
PreToolUse(Bash) → scope-path-check → destructive-command-check → allow/deny
```

A failure in either lane rejects the tool call.

## Pattern catalog

The guard ships a base catalog keyed by tool family. Treat each entry as an authoritative pattern, not a regex literal — the implementation should normalize whitespace, quoting, and `--flag=value` vs `--flag value` before matching.

| Family | Pattern shape | Why it qualifies |
|---|---|---|
| Filesystem | `rm -rf <abs-path-not-under-/tmp>`, `rm -rf .` from outside a known build dir | Recursive deletion of non-scratch content has no general undo |
| Git history | `git reset --hard`, `git checkout -- <file>`, `git clean -fd`, `git stash drop`, `git stash clear` | Destroys uncommitted or stashed work that no other tool tracks |
| Git remote | `git push --force` (without `--force-with-lease`), `git branch -D`, `git tag -d <pushed-tag>` | Rewrites or deletes shared history |
| Database | `DROP DATABASE`, `DROP TABLE`, `TRUNCATE`, `DELETE` without a `WHERE` clause | Schema-level or unbounded data destruction |
| Container/k8s | `kubectl delete namespace`, `kubectl delete --all`, `helm uninstall`, `docker system prune -a` | Sweeps live workloads or shared caches |
| Cloud / IaC | `terraform destroy`, `aws s3 rb --force`, `gcloud projects delete` | Tears down infrastructure that humans co-own |

Pack additional families behind opt-in flags so a CLI-only repo never loads database or k8s rules.

## Allowlist and override flow

Every pattern needs an escape hatch that records the override decision; otherwise operators silently disable the guard entirely. Implement three layers, evaluated highest to lowest priority:

1. **Project allowlist** — a checked-in file (e.g. `.agents/destructive-allowlist.toml`) listing rule IDs and optional path scopes that this repo permanently accepts. Reviewable in PRs.
2. **User allowlist** — `~/.config/<guard>/allowlist.toml` for per-operator habits (cleaning a personal Docker cache, etc.).
3. **One-shot override code** — when a block fires, the guard prints a short cryptographic code bound to the exact command + working directory + a short TTL (e.g. 24 h, single use). The human, not the agent, runs `<guard> allow-once <code>` to grant the next attempt.

The one-shot path is load-bearing. It keeps the agent honest (the code is not predictable from context) and produces an audit log entry per override.

## Confirm thresholds

Make the strictness configurable so the same binary can run in interactive, CI, and unattended-swarm contexts:

```toml
[thresholds]
mode = "block"          # "block" | "warn" | "log-only"
require_override_for = ["filesystem", "git-history", "database"]
auto_allow_for = ["filesystem.rm-under-build-dir"]
warn_for = ["git-remote.force-with-lease"]
```

Defaults: block on the high-blast-radius families, warn on near-equivalents that have a recoverable variant, log-only for purely informational rules. CI pipelines typically tighten to `mode = "block"` with a smaller allowlist; an interactive operator may relax to `warn` while pairing.

## PreToolUse hook integration

The integration mirrors `edit-scope-guard.sh`:

- **Trigger:** PreToolUse on `Bash` (Claude) or `shell` / `apply_patch` (Codex).
- **Input:** harness-supplied JSON on stdin with `tool.params.command`.
- **Pipeline:** quick-reject screen → context sanitization → normalization → allowlist check → pattern match.
- **Deny output:** non-zero exit with a structured stderr reason — rule ID, family, suggested safer variant, and the one-shot override code. The harness converts that into a tool-use refusal the model can read.
- **Allow output:** exit 0, no stdout. Side-effect-free for the common case.

Performance budget matters because the hook runs on every Bash call. Target sub-millisecond steady state, with a hard fail-open ceiling (e.g. 200 ms) so a wedged guard never stalls the swarm.

## Failure modes the guard must handle

- **Fail-closed on a confirmed match.** Pattern hits → reject, even if the override file is unreadable.
- **Fail-open on infrastructure error.** Missing config, malformed JSON, panic in the matcher → exit 0 with a stderr warning. Same defensive default as `edit-scope-guard.sh`.
- **Fail-open on timeout.** Anything past the latency ceiling skips the rest of the pipeline.
- **Heredoc and inline scripts.** `bash -c '...'`, `python -c '...'`, and `<<EOF` bodies must be extracted and rescanned; otherwise a one-line wrapper bypasses every rule.
- **Quoted path normalization.** `rm  -rf   "/var/log/"` and `rm -rf /var/log` should hit the same rule.

## Composing with `/scope`

Recommended wiring for a swarm wave:

1. `/scope freeze <dirs>` to bound the edit surface.
2. Enable the destructive-command guard with the families relevant to this repo (filesystem + git-history is a sane minimum).
3. Add project-specific allowlist entries for routine safe deletions (e.g. `rm -rf ./build`, `rm -rf ./.next`).
4. Run the wave. Treat any block as a checkpoint, not an error: pick the safer variant from the rule's suggestion field, or escalate to the human for an `allow-once`.
5. After the wave, `/scope unfreeze` and let the destructive-command guard stay loaded — its overhead is negligible and the override audit log compounds.

The two guards do not need to share state, but they should share the same fail-open posture so a hook outage never silently disables both lanes at once.

---
> Pattern adopted from `dcg` (ACFS skill corpus). Methodology only — no verbatim text.
