---
name: bootstrap
description: Initialize AgentOps project files.
---
# $bootstrap

> **Quick Ref:** Product/operations layer around the `ao quick-start` core seed. Progressive — bare repos get the golden path first, existing repos fill gaps only.

**YOU MUST EXECUTE THIS WORKFLOW. Do not just describe it.**

## Quick Start

```
$bootstrap
```

That is it. One command. Every step below is idempotent — existing artifacts are never overwritten.

## External Tools

- **ao** (optional) — AgentOps CLI. Required only for optional hook activation (Step 6). Bootstrap skips hooks gracefully when missing.
- **br** (optional, recommended) — beads_rust CLI (local-first issue tracking). Bootstrap probes for `br` in Step 0.5 and, when missing, recommends installing it. Bootstrap never installs `br` on the user's behalf.

## Flags

| Flag | Effect |
|------|--------|
| `--dry-run` | Report what would be created without doing anything |
| `--force` | Recreate artifacts even if they already exist |

## Execution Steps

### Step 0: Detect Repo State

```bash
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || { echo "NOT_A_GIT_REPO"; exit 1; }
HAS_GOALS=$([[ -f GOALS.md ]] && echo true || echo false)
HAS_PRODUCT=$([[ -f PRODUCT.md ]] && echo true || echo false)
HAS_README=$([[ -f README.md ]] && echo true || echo false)
HAS_PROGRAM=$([[ -f PROGRAM.md || -f AUTODEV.md ]] && echo true || echo false)
HAS_AGENTS=$([[ -d .agents ]] && echo true || echo false)
HAS_HOOKS=$(grep -q "agentops" .codex/settings.json 2>/dev/null && echo true || echo false)
HAS_AO=$(command -v ao >/dev/null && echo true || echo false)
HAS_BR=$(command -v br >/dev/null && echo true || echo false)
```

Classify the repo:

| State | Condition |
|-------|-----------|
| **bare** | No GOALS.md, no PRODUCT.md, no .agents/ |
| **partial** | Some artifacts present, some missing |
| **complete** | GOALS.md, PRODUCT.md, README.md, PROGRAM.md/AUTODEV.md, and .agents/ present |

If `--dry-run` is set: report the state and what would be created, including whether `br` would be recommended (when `HAS_BR` is false), then stop. Do not proceed to Steps 1-6.

If the repo is **complete** and `--force` is not set: report "Repo is fully bootstrapped. Nothing to do." and stop.

### Step 0.5: Recommend br

If `HAS_BR` is true: skip. Report "br: present."

If `HAS_BR` is false: report **"br: not installed (recommended). Install beads_rust to get local-first issue tracking."** and continue. Bootstrap does NOT run the installer — `br` is optional, the user decides.

### Step 1: GOALS.md

If `HAS_GOALS` is false (or `--force` is set):

Run the goals skill to initialize GOALS.md interactively:

```
$goals init
```

If `HAS_GOALS` is true and `--force` is not set: skip. Report "GOALS.md exists -- skipped."

### Step 2: PRODUCT.md

If `HAS_PRODUCT` is false (or `--force` is set):

Run the product skill to generate PRODUCT.md interactively:

```
$product
```

If `HAS_PRODUCT` is true and `--force` is not set: skip. Report "PRODUCT.md exists -- skipped."

### Step 3: README.md

If `HAS_README` is false (or `--force` is set) AND PRODUCT.md now exists:

Run the doc skill in README mode to generate README.md:

```
$doc --mode=readme
```

If `HAS_README` is true and `--force` is not set: skip. Report "README.md exists -- skipped."

If PRODUCT.md does not exist (Step 2 was skipped or failed): skip. Report "README.md skipped -- PRODUCT.md required first."

### Step 4: Core Seed and .agents/ Structure

If `HAS_AGENTS` is false (or `--force` is set):

Prefer the CLI golden path:

```bash
ao quick-start --no-beads
```

If `ao` is unavailable, create the minimal directory structure and report the exact command to repair later:

```bash
mkdir -p .agents/learnings .agents/council .agents/research .agents/plans .agents/rpi .agents/patterns .agents/retro .agents/handoff
```

Create `.agents/AGENTS.md` if it does not exist:

```markdown
# Agent Knowledge Store

This directory contains accumulated knowledge from agent sessions.

## Structure

| Directory | Purpose |
|-----------|---------|
| `learnings/` | Extracted lessons and patterns |
| `council/` | Council validation artifacts |
| `research/` | Research phase outputs |
| `plans/` | Implementation plans |
| `rpi/` | RPI execution packets and phase logs |

## Usage

Knowledge is automatically managed by the AgentOps flywheel:
- `$inject` surfaces relevant prior knowledge at session start
- `$post-mortem` extracts and processes new learnings
- `$compile` runs maintenance (mine, grow, defrag)
```

If `HAS_AGENTS` is true and `--force` is not set: skip. Report ".agents/ exists -- skipped."

If `ao` is unavailable after fallback creation: report "Core seed repair command: `ao quick-start --dry-run` after installing ao."

### Step 5: PROGRAM.md / AUTODEV.md

If `HAS_PROGRAM` is false (or `--force` is set):

Use the existing autodev CLI path:

```bash
ao autodev init "your current objective"
```

If `ao` is unavailable: do not create a placeholder. Report "PROGRAM.md skipped -- install ao, then run: `ao autodev init \"your current objective\"`."

If `HAS_PROGRAM` is true and `--force` is not set: skip. Report "PROGRAM.md/AUTODEV.md exists -- skipped."

### Step 6: Optional Hook Activation

Do not activate runtime agent hooks. AgentOps 3.0 is runtime-hookless:
`ao quick-start`, execution packets, explicit validation, and knowledge
compounding deliver first value without Claude/Codex runtime hooks. Routine
release authority is the local cockpit gate (`ao gate check` plus the installed
Git pre-push/pawl proof path); GitHub Actions are PR/tag/manual backstop
telemetry. There is no `ao` command or flag that installs runtime hooks —
hooks were removed from the CLI.

If the user explicitly requests hooks, they are opt-in and author-it-yourself:
point them at the `hooks-authoring` skill, which scaffolds project-local hooks
into `.codex/settings.json`. Bootstrap itself never writes hooks.

If hooks were not explicitly requested: skip. Report "Runtime hooks optional -- skipped. AgentOps 3.0 is runtime-hookless; routine release authority is the local cockpit gate. To author your own, use the `hooks-authoring` skill."

If `HAS_HOOKS` is true: report "Hooks already present in .codex/settings.json -- left untouched."

### Step 7: Report

Output a summary table:

```
Bootstrap complete.

| Artifact      | Status  |
|---------------|---------|
| GOALS.md      | created / skipped / failed |
| PRODUCT.md    | created / skipped / failed |
| README.md     | created / skipped / failed |
| PROGRAM.md    | created / skipped / failed |
| .agents/      | created / skipped / failed |
| Hooks         | optional / activated / skipped / failed |
| br            | present / recommended (not installed) |

Repo is now AgentOps-ready. Next: $rpi "your first goal"
```

## Examples

### Bare Repo

**User says:** `$bootstrap`

**What happens:** Agent detects no AgentOps artifacts. Runs $goals init, $product, $doc --mode=readme, creates .agents/ structure, leaves hooks optional. Reports all five core artifacts created.

### Partial Repo (has GOALS.md and .agents/)

**User says:** `$bootstrap`

**What happens:** Agent detects existing artifacts. Skips GOALS.md and .agents/. Runs $product, $doc --mode=readme. Leaves hooks optional unless explicitly requested. Reports two created, three skipped.

### Dry Run

**User says:** `$bootstrap --dry-run`

**What happens:** Agent detects repo state and reports what would be created. No files are written.

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|---------|
| "Not a git repo" | No .git directory | Run `git init` first |
| Goals skill fails | No project context | Provide a one-line project description when prompted |
| Product skill fails | No goals defined | Run `$goals init` manually first, then re-run `$bootstrap` |
| Hooks not activating | ao CLI not installed | Install: `brew tap boshu2/agentops https://github.com/boshu2/homebrew-agentops && brew install agentops` |
| br not installed | Recommended but optional | Install beads_rust (`br`) if you want issue tracking; otherwise ignore |
| Want to start over | Existing artifacts blocking | Use `--force` to recreate all artifacts |

## See Also

- [goals](../goals/SKILL.md) -- Fitness specification and directive management
- [product](../product/SKILL.md) -- Product definition generation
- [doc](../doc/SKILL.md) -- README generation (`--mode=readme`) + repo docs
- [status](../status/SKILL.md) -- New user onboarding (lighter than bootstrap)
- [related operator runbooks](references/related-runbooks.md) -- host-hygiene runbooks (PATH rationalization, etc.)

## Reference Documents

- [references/bootstrap.feature](references/bootstrap.feature) — Executable spec: bare repo gets golden path, existing repo fills gaps only, idempotent never-overwrite (soc-qk4b)
