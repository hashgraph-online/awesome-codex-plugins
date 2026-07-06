---
name: dcg
description: Handle blocked destructive commands. Use
---
<!-- TOC: Core Insight | THE EXACT WORKFLOW | Quick Reference | Safe Alternatives | What Gets Blocked | Anti-Patterns | Configuration | References -->

# DCG: When You Get Blocked

> **Core Insight:** Blocks are checkpoints, not errors. A safe alternative almost always exists. Find it before mentioning override.

## Quick Navigation

| I need to... | Go to |
|--------------|-------|
| Handle a block right now | [THE EXACT WORKFLOW](#the-exact-workflow) |
| Find a safe alternative | [Safe Alternatives](#safe-alternatives) |
| See all CLI commands | [COMMANDS.md](references/COMMANDS.md) |
| Enable more rule packs | [PACKS.md](references/PACKS.md) |
| Configure per-project | [CONFIG.md](references/CONFIG.md) |
| Debug hook issues | [TROUBLESHOOTING.md](references/TROUBLESHOOTING.md) |

---

## THE EXACT WORKFLOW

When blocked, follow this sequence every time:

```
1. Run `dcg explain "cmd"` → Understand why (see trace)
2. Check Safe Alternatives table → Use if exists (DON'T mention override)
3. No alternative? → Explain risk clearly, let human decide
4. Human approves? → THEY run: dcg allow-once CODE
```

**Never:** Ask for override first. Never retry silently. Never circumvent.

**Example block output:**
```
BLOCKED: git reset --hard HEAD
Rule: core.git:reset-hard
Reason: Discards uncommitted changes permanently
Allow-once code: ab12
Safer alternative: git stash
```

**Good response:**
> "I wanted to discard changes but `git reset --hard` was blocked. Let me use `git stash` instead—recoverable if needed." [proceeds with stash]

## Safe Alternatives

| Blocked | Use Instead | Why |
|---------|-------------|-----|
| `git reset --hard` | `git stash` | Recoverable |
| `git checkout -- file` | `git stash push file` | Preserves changes |
| `git push --force` | `git push --force-with-lease` | Checks remote unchanged |
| `git clean -fd` | `git clean -fdn` (preview) | Shows what would delete |
| `git stash drop` | `git stash list` first | Verify which stash |
| `rm -rf /path` | `rm -ri /path` or verify path | Interactive/confirm |
| `kubectl delete namespace` | `kubectl delete -l app=X` | Selective deletion |
| `DROP DATABASE` | Backup first | Human approves |
| `docker system prune -a` | `docker system df` first | See what's used |

## Quick Reference

```bash
dcg doctor              # Health check — hook registered?
dcg explain "cmd"       # WHY is it blocked? (with trace)
dcg test "cmd"          # Would this be blocked? (dry-run)
dcg allow-once CODE     # Human approves (THEY run this)
dcg packs               # List available rule packs
dcg scan --staged       # Pre-commit: scan for issues
```

---

## What Gets Blocked

| Category | Patterns | Safe Variants |
|----------|----------|---------------|
| Git destructive | `reset --hard`, `checkout --` | `stash`, `restore --staged` |
| Git history | `push --force`, `branch -D` | `--force-with-lease`, `-d` |
| Git stash | `stash drop`, `stash clear` | `stash list` first |
| Filesystem | `rm -rf` (dangerous paths) | `/tmp/*` allowed |
| Database | `DROP`, `TRUNCATE`, `DELETE` w/o WHERE | Add WHERE clause |
| K8s | `delete namespace`, `delete --all` | `-l` label selector |

**Context-aware:** `rm -rf ./build` allowed, `rm -rf /` blocked.

**`dcg explain` example (7-step pipeline):**
```bash
$ dcg explain "git reset --hard HEAD"
BLOCKED by core.git:reset-hard

Evaluation trace:
  1. Config allow overrides: no match
  2. Config block overrides: no match
  3. Heredoc detection: not applicable
  4. Quick reject: triggered (contains "reset")
  5. Context sanitization: no changes
  6. Normalization: git reset --hard HEAD
  7. Pack evaluation:
     - Safe patterns: no match
     - Destructive: MATCH "reset --hard"

Suggestion: Use `git stash` to preserve changes
```

## Anti-Patterns

```
❌ "Command blocked. Run dcg allow-once ab12"  → Find alternative first!
❌ *Retrying silently or circumventing*         → Always acknowledge blocks
❌ Treating blocks as errors                    → They're checkpoints
❌ Asking user to allow-once without explaining → They need context
```

## Configuration

```toml
# .dcg.toml — enable rule packs per-project
[packs]
enabled = ["database.postgresql", "kubernetes.kubectl", "cloud.aws"]

[overrides]
allow_patterns = ["rm -rf ./node_modules"]  # Project-specific safe
```

**Environment variables:**
- `DCG_PACKS="containers.docker,kubernetes"` — Enable packs
- `DCG_DISABLE="kubernetes.helm"` — Disable specific packs
- `DCG_BYPASS=1` — Escape hatch (human-only)

## Key Facts

- **49+ rule packs** available (database, containers, k8s, cloud, etc.)
- **Sub-millisecond latency** — won't slow your workflow
- **Fail-open on timeout** — if DCG hangs, command runs (with warning)
- **Heredoc scanning** — inline scripts (`bash -c`, `python -c`) are analyzed
- **Allow-once codes** — 4 hex chars, 24h expiry, bound to exact command+directory

## The Incident That Started It All

> On December 17, 2025, an AI agent ran `git checkout --` on files containing hours of uncommitted work. The files were recovered via `git fsck --lost-found`, but it proved: **instructions don't prevent execution—mechanical enforcement does.**

---

## Validation

```bash
# Quick health check
dcg doctor | head -20

# Test if a command would be blocked
dcg test "git reset --hard HEAD"

# Should show: WOULD BE BLOCKED
```

---

## Scripts

| Script | Usage |
|--------|-------|
| `./scripts/validate-dcg.sh` | Full installation validation |

---

## References

- [COMMANDS.md](references/COMMANDS.md) — Full CLI reference with `dcg explain`, `dcg scan`
- [PACKS.md](references/PACKS.md) — 49+ rule pack system (database, k8s, cloud, etc.)
- [CONFIG.md](references/CONFIG.md) — Configuration, agent profiles, heredoc settings
- [SCENARIOS.md](references/SCENARIOS.md) — Detailed examples with good/bad responses
- [PHILOSOPHY.md](references/PHILOSOPHY.md) — Why DCG works this way
- [TROUBLESHOOTING.md](references/TROUBLESHOOTING.md) — Common issues and fixes
