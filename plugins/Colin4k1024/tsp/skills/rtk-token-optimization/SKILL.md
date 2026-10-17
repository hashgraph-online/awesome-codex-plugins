---
name: rtk-token-optimization
description: >
  High-performance CLI proxy that reduces LLM token consumption by 60-90%.
  Transparently rewrites 100+ common dev commands (git, gh, cargo, npm, docker, kubectl, aws, etc.)
  via PreToolUse hook. Single Rust binary, zero dependencies.
source: https://github.com/rtk-ai/rtk
license: Apache-2.0
trust_tier: B-proven-community
---

## Purpose

Reduce LLM token consumption in Claude Code sessions by 60-90% without changing developer workflow.
All Bash commands are transparently rewritten to their `rtk` equivalents via a PreToolUse hook.

## How It Works

```
Without rtk:                              With rtk:
Claude --git status--> shell --> git      Claude --git status--> RTK --> git
  ^        ~2,000 tokens (raw)    |        ^    ~200 tokens     |       |
  +-------------------------------+        +---- (filtered) ----+-------+
```

Four strategies applied per command type:

1. **Smart Filtering** - Removes noise (comments, whitespace, boilerplate)
2. **Grouping** - Aggregates similar items (files by directory, errors by type)
3. **Truncation** - Keeps relevant context, cuts redundancy
4. **Deduplication** - Collapses repeated log lines with counts

## Supported Commands

| Category | Commands | Typical Savings |
|----------|----------|----------------|
| Files | ls, read, find, grep, diff | 70-80% |
| Git | status, diff, log, add, commit, push | 75-92% |
| GitHub CLI | pr list, issue list, run list | 80% |
| Test Runners | cargo test, npm test, pytest, go test, vitest, playwright | 90% |
| Build & Lint | cargo build, tsc, next build, eslint, ruff, clippy | 80-85% |
| Package Managers | pnpm list, pip list, bundle install | 80% |
| Containers | docker ps/logs, kubectl pods/logs | 80% |
| AWS | sts, ec2, lambda, logs, s3, cloudformation | 80% |
| Data | json, env, log, curl, wget | 70-80% |

## Token Savings (30-min Session Estimate)

| Operation | Frequency | Standard | rtk | Savings |
|-----------|-----------|----------|-----|---------|
| ls / tree | 10x | 2,000 | 400 | -80% |
| cat / read | 20x | 40,000 | 12,000 | -70% |
| grep / rg | 8x | 16,000 | 3,200 | -80% |
| git status | 10x | 3,000 | 600 | -80% |
| git diff | 5x | 10,000 | 2,500 | -75% |
| cargo test / npm test | 5x | 25,000 | 2,500 | -90% |
| **Total** | | **~118,000** | **~23,900** | **-80%** |

## Usage

After installation, rtk works automatically via the PreToolUse hook. No manual changes needed.

### Analytics Commands

```bash
rtk gain                # Summary stats
rtk gain --graph        # ASCII graph (last 30 days)
rtk gain --daily        # Day-by-day breakdown
rtk discover            # Find missed savings opportunities
rtk session             # Show RTK adoption across recent sessions
```

### Manual Usage

```bash
rtk git status          # Compact git status
rtk read file.rs        # Smart file reading
rtk test cargo test     # Show failures only
rtk lint                # ESLint grouped by rule/file
rtk docker ps           # Compact container list
```

## Prerequisites

- `rtk` binary: `brew install rtk` or `curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/refs/heads/master/install.sh | sh`
- `jq`: required by the hook script

## Integration

- Hook: `hooks/rtk-rewrite.sh` (PreToolUse:Bash, last in chain)
- Config: `~/.config/rtk/config.toml` for customization
- Tee recovery: failed command full output saved to `~/.local/share/rtk/tee/`

## References

- [rtk GitHub](https://github.com/rtk-ai/rtk)
- [rtk Website](https://www.rtk-ai.app)
- [Troubleshooting](https://github.com/rtk-ai/rtk/blob/master/docs/TROUBLESHOOTING.md)
