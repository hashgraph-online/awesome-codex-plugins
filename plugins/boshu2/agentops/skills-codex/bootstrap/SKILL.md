---
name: bootstrap
description: 'Initialize AgentOps project files.'
---
# $bootstrap (Codex Native)

> **Quick Ref:** Product/operations layer around the `ao quick-start` core seed. Progressive -- bare repos get the golden path first, existing repos fill gaps only.

**YOU MUST EXECUTE THIS WORKFLOW. Do not just describe it.**

## Quick Start

```
$bootstrap
```

That is it. One command. Every step below is idempotent -- existing artifacts are never overwritten.

## External Tools

- **ao** (optional) -- AgentOps CLI. Required only for optional hook activation (Step 6). Bootstrap skips hooks gracefully when missing.
- **bd** (optional, recommended) -- beads CLI. Bootstrap probes for `bd` in Step 0.5 and, when missing, points the user at `scripts/install-bd.sh` with a copy-paste command. Bootstrap never installs `bd` on the user's behalf.

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
HAS_HOOKS=$(grep -rq "agentops" .git/hooks/ 2>/dev/null && echo true || echo false)
HAS_AO=$(command -v ao >/dev/null && echo true || echo false)
HAS_BD=$(command -v bd >/dev/null && echo true || echo false)
```

Classify the repo:

| State | Condition |
|-------|-----------|
| **bare** | No GOALS.md, no PRODUCT.md, no .agents/ |
| **partial** | Some artifacts present, some missing |
| **complete** | GOALS.md, PRODUCT.md, README.md, PROGRAM.md/AUTODEV.md, and .agents/ present |

If `--dry-run` is set: report the state and what would be created, including whether `bd` would be recommended (when `HAS_BD` is false), then stop. Do not proceed to Steps 1-6.

If the repo is **complete** and `--force` is not set: report "Repo is fully bootstrapped. Nothing to do." and stop.

### Step 0.5: Recommend bd

If `HAS_BD` is true: skip. Report "bd: present."

If `HAS_BD` is false: report **"bd: not installed (recommended). Install with: `bash scripts/install-bd.sh`"** and continue. Bootstrap does NOT run the installer -- `bd` is optional, the user decides.

If `scripts/install-bd.sh` is absent at the repo root, drop the install hint and just report "bd: not installed (recommended). See https://github.com/steveyegge/beads".

### Step 1: GOALS.md

If `HAS_GOALS` is false (or `--force` is set):

Invoke the existing goals path. Prefer the skill when available; otherwise use the CLI:

```bash
ao goals init
```

If neither the goals skill nor `ao` is available, do not create a placeholder. Report the exact next command: `ao goals init`.

If `HAS_GOALS` is true and `--force` is not set: skip. Report "GOALS.md exists -- skipped."

### Step 2: PRODUCT.md

If `HAS_PRODUCT` is false (or `--force` is set):

Invoke `$product` to generate PRODUCT.md from mission, personas, value props, and competitive landscape. Do not write placeholder content.

If `HAS_PRODUCT` is true and `--force` is not set: skip. Report "PRODUCT.md exists -- skipped."

### Step 3: README.md

If `HAS_README` is false (or `--force` is set) AND PRODUCT.md now exists:

Invoke `$readme` to generate README.md from PRODUCT.md content. Include project name, description, installation, usage, and contributing sections.

If `HAS_README` is true and `--force` is not set: skip. Report "README.md exists -- skipped."

If PRODUCT.md does not exist (Step 2 was skipped or failed): skip. Report "README.md skipped -- PRODUCT.md required first."

### Step 4: Core Seed and .agents/ Structure

If `HAS_AGENTS` is false (or `--force` is set):

Prefer the CLI golden path:

```bash
ao quick-start --no-beads
```

If `ao` is unavailable, create the minimal directory structure and report the exact repair command:

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

Do not activate hooks by default. AgentOps 3.0's first-value path is hookless:
`ao quick-start`, execution packets, explicit validation, and knowledge
compounding work before runtime hooks are installed.

If the user explicitly requested hook activation and `HAS_AO` is true AND
`HAS_HOOKS` is false (or `--force` is set):

```bash
ao init --hooks
```

If `HAS_AO` is false: skip. Report "Optional hooks skipped -- ao CLI not installed. Run: brew tap boshu2/agentops https://github.com/boshu2/homebrew-agentops && brew install agentops"

If hook activation was not explicitly requested: skip. Report "Hooks optional -- skipped. To opt in later, run `ao init --hooks` or `install-codex.sh --with-hooks`."

If `HAS_HOOKS` is true and `--force` is not set: skip. Report "Hooks already configured -- skipped."

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
| bd            | present / recommended (not installed) |

Repo is now AgentOps-ready. Next: $rpi "your first goal"
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|---------|
| "Not a git repo" | No .git directory | Run `git init` first |
| Goals step fails | No project context | Provide a one-line project description when prompted |
| Product step fails | No goals defined | Run goals init manually first, then re-run `$bootstrap` |
| Hooks not activating | ao CLI not installed | Install: `brew tap boshu2/agentops https://github.com/boshu2/homebrew-agentops && brew install agentops` |
| bd not installed | Recommended but optional | Install with `bash scripts/install-bd.sh` if you want issue tracking; otherwise ignore |
| Want to start over | Existing artifacts blocking | Use `--force` to recreate all artifacts |

## See Also

- `../goals/SKILL.md` -- Fitness specification and directive management
- `../product/SKILL.md` -- Product definition generation
- `../readme/SKILL.md` -- README generation
- `../quickstart/SKILL.md` -- New user onboarding (lighter than bootstrap)
- [references/related-runbooks.md](references/related-runbooks.md) -- host-hygiene runbooks (PATH rationalization, etc.)
