# NTM Integration Surfaces — External Tools via `--robot-*`

NTM exposes one-shot adapters to sibling agent-fleet tools so an agent-mode operator can
query or mutate adjacent systems without spawning sub-shells. All flags are registered
in `/dp/ntm/internal/cli/root.go`.

## Contents

- [DCG — Destructive Command Guard](#dcg--destructive-command-guard)
- [SLB — Simultaneous Launch Button](#slb--simultaneous-launch-button-two-person-approval)
- [CAAM — AI coding CLI account manager](#caam--ai-coding-cli-account-manager)
- [Quota (caut)](#quota-caut)
- [RCH — Remote compilation/build host](#rch--remote-compilationbuild-host)
- [RANO — Agent network observer](#rano--agent-network-observer)
- [RU — Multi-repo sync](#ru--multi-repo-sync)
- [GIIL — Image link downloader](#giil--image-link-downloader)
- [Agent Mail](#agent-mail)
- [CASS — Cross Agent Session Search](#cass--cross-agent-session-search)
- [Context injection](#context-injection)
- [Environment / setup probes](#environment--setup-probes)
- [JFP, MS, XF (content surfaces)](#jfp-ms-xf-content-surfaces)
- [Composition notes](#composition-notes)
- [One-line quick index](#one-line-quick-index)

---

## DCG — Destructive Command Guard

| Flag | Purpose | Source |
|------|---------|--------|
| `--robot-dcg-status` | DCG status + config | `root.go:3568` |
| `--robot-dcg-check --command=<cmd>` | Preflight a command via DCG | `root.go:3569-3571` |
| `--robot-guard` | DEPRECATED alias for `--robot-dcg-check` | `root.go:3570` |

Adapter contract, verified against current code:

- Status uses `dcg doctor --format json`.
- Checks use `dcg --robot test --format json <command>`.
- `dcg check`, inline `--json`, `--context`, and `--cwd` are not part of the
  current DCG check contract; NTM propagates cwd through `cmd.Dir`.
- If the command is wrapped in `rch exec -- ...`, NTM extracts the inner build
  command before asking DCG so build offload does not hide destructive intent.

## SLB — Simultaneous Launch Button (two-person approval)

| Flag | Purpose | Source |
|------|---------|--------|
| `--robot-slb-pending` | List pending two-person approval requests | `root.go:3577` |
| `--robot-slb-approve=<id>` | Approve by request ID | `root.go:3578` |
| `--robot-slb-deny=<id> --reason=<r>` | Deny with required reason | `root.go:3579` |

## CAAM — AI coding CLI account manager

| Flag | Purpose | Source |
|------|---------|--------|
| `--robot-account-status [--account-status-provider=<p>]` | Current account + limits for provider | `root.go:3556` |
| `--robot-accounts-list [--accounts-list-provider=<p>]` | List known accounts | `root.go:3561` |
| `--robot-switch-account=<provider[:acct]>` | Swap active account | `root.go:3562` |

## Quota (caut)

| Flag | Purpose | Source |
|------|---------|--------|
| `--robot-quota-status` | Overall quota snapshot | `root.go:3589` |
| `--robot-quota-check --provider=<p>` | Check specific provider quota | `root.go:3590-3591` |

## RCH — Remote compilation/build host

| Flag | Purpose | Source |
|------|---------|--------|
| `--robot-rch-status` | RCH orchestrator status | `root.go:3598` |
| `--robot-proxy-status` | rust_proxy status | `root.go:3599` |
| `--robot-rch-workers [--worker=<n>]` | Worker pool state | `root.go:3600-3601` |

Use `rch exec -- <command>` (for example `rch exec -- go test -short ./...`) when
repo rules require remote compilation. The NTM robot flags are health/visibility
adapters; they do not submit a build on their own.

## RANO — Agent network observer

| Flag | Purpose | Source |
|------|---------|--------|
| `--robot-rano-stats [--rano-window=5m]` | Per-agent network stats | `root.go:3594-3595` |

## RU — Multi-repo sync

| Flag | Purpose | Source |
|------|---------|--------|
| `--robot-ru-sync [--dry-run]` | Run `ru sync` returning JSON | `root.go:3583` |

## GIIL — Image link downloader

| Flag | Purpose | Source |
|------|---------|--------|
| `--robot-giil-fetch=<url>` | Download image via giil | `root.go:3586` |

## Agent Mail

| Flag | Purpose | Source |
|------|---------|--------|
| `--robot-mail` | Machine-readable digest | `root.go:3298` |
| `--robot-mail-check --mail-project=<p>` | Check with filters | `root.go:3612-3621` |

Mail-check filters: `--mail-agent`, `--thread`, `--mail-status`, `--include-bodies`,
`--urgent-only`, `--mail-verbose`, `--mail-offset`, `--mail-until`.

**Prefer `ntm mail inbox <session>`** from the CLI when you want the session-derived
form. `--mail-project=<project>` is required by `--robot-mail-check` and should not be
attached to unrelated CLI subcommands.

## CASS — Cross Agent Session Search

| Flag | Purpose | Source |
|------|---------|--------|
| `--robot-cass-status` | Index state | `root.go:3383` |
| `--robot-cass-search=<query>` | Search past sessions | `root.go:3384` |
| `--robot-cass-insights` | Aggregate insights | `root.go:3385` |
| `--robot-cass-context=<task>` | Context suggestions for a task | `root.go:3386` |

## Context injection

| Flag | Purpose | Source |
|------|---------|--------|
| `--robot-context-inject=<session>` | Inject AGENTS.md / README.md into panes | `root.go:3604-3609` |

Knobs: `--inject-files=<csv>`, `--inject-max-bytes=<N>`, `--inject-all`,
`--inject-pane=<i>`, `--inject-dry-run`.

## Environment / setup probes

| Flag | Purpose | Source |
|------|---------|--------|
| `--robot-env=<session\|global>` | Session or global env snapshot | `root.go:3565` |
| `--robot-setup` / `--robot-acfs-status` | Bootstrap readiness (deps, dirs, tokens) | `root.go:3304-3305` |
| `--robot-tools` | Tool availability (tmux, git, etc.) | `root.go:3301` |

## JFP, MS, XF (content surfaces)

| Flag | Purpose | Source |
|------|---------|--------|
| `--robot-jfp-status\|list\|search\|show\|suggest\|install\|export\|update\|installed\|categories\|tags\|bundles` | Jeffrey's Fave Prompts registry | `root.go:3395-3406` |
| `--robot-ms-search=<q>` / `--robot-ms-show=<id>` | MS registry lookup | `root.go:3415-3416` |
| `--robot-xf-search=<q>` / `--robot-xf-status` | X/Twitter archive search | `root.go:3419-3420` |

## Composition notes

These adapters return structured JSON, not TUI state. They are safe to call from a
loop and safe to pipe through `jq`. Because they proxy to external binaries:

- A missing external tool yields a structured error rather than a crash.
- Each integration respects its own authentication (CAAM for accounts, slb for SLB, etc.).
- Most adapters respect `--robot-format` and `--robot-verbosity`.

## One-line quick index

```bash
ntm --robot-dcg-status                          # what DCG is blocking now
ntm --robot-dcg-check --command="git status"    # preflight without running
ntm --robot-slb-pending                         # pending two-person approvals
ntm --robot-accounts-list                       # list CAAM accounts
ntm --robot-switch-account=claude:alice2        # rotate CAAM account
ntm --robot-quota-check --provider=claude       # quota check
ntm --robot-rch-status                          # remote compile host status
ntm --robot-rano-stats                          # agent network stats
ntm --robot-ru-sync --dry-run                   # preview multi-repo sync
ntm --robot-mail                                # mail digest for current workspace
ntm --robot-mail-check --mail-project=myproject # filtered project inbox
ntm --robot-cass-search="authentication error"  # session search
ntm --robot-context-inject=myproject --inject-all  # inject AGENTS.md into panes
```
