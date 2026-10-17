---
name: codebase-recon
description: >
  Use when entering an unfamiliar codebase, onboarding to a new project,
  or wanting to assess codebase health before reading code — analyzes git
  history to reveal hotspots, risk areas, team structure, and development
  momentum
compatibility: Requires git. Works in any terminal-based coding agent.
metadata:
  author: yujiachen-y
  version: "1.0"
  inspired-by: https://piechowski.io/post/git-commands-before-reading-code/
---

# Codebase Recon

Analyze git history to understand a codebase before reading any code. Reveals project health, risk areas, team structure, and development momentum.

Inspired by ["The Git Commands I Run Before Reading Any Code"](https://piechowski.io/post/git-commands-before-reading-code/) by [Ally Piechowski](https://github.com/grepsedawk).

## Phase 1: Probe

Before running analysis, determine repo scale to calibrate time windows and result counts.

Run this single shell command to collect repo vitals:

```sh
echo "COMMITS=$(git rev-list --count HEAD)" && \
echo "FIRST_COMMIT=$(git log --reverse --format='%ad' --date=short | head -1)" && \
echo "LATEST_COMMIT=$(git log --format='%ad' --date=short | head -1)" && \
echo "BRANCHES=$(git branch -a | wc -l | tr -d ' ')"
```

Use the commit count to set parameters for Phase 2:

| Repo Size | Commits | `WINDOW` (--since) | `N` (--head) |
|-----------|---------|---------------------|--------------|
| Small     | <500    | (omit --since)      | 10           |
| Medium    | 500-10k | `1 year ago`        | 20           |
| Large     | >10k    | `6 months ago`      | 30           |

Print the Repo Vitals line immediately:

```
Repo Vitals: Age: [FIRST_COMMIT to LATEST_COMMIT] | Commits: [COMMITS] | Branches: [BRANCHES] | Analysis window: [WINDOW or "all time"]
```

## Phase 2: Parallel Analysis

Run all 7 commands in parallel (they are independent). Substitute `WINDOW` and `N` from Phase 1. For small repos, omit `--since` flags entirely.

### 2a. Code Hotspots

Most-changed files in the analysis window:

```sh
git log --format=format: --name-only --since="WINDOW" | sort | uniq -c | sort -nr | head -N
```

### 2b. Bus Factor

All-time contributor ranking by commit count:

```sh
git shortlog -sn --no-merges
```

### 2c. Bug Magnets

Files most associated with bug-fix commits:

```sh
git log -i -E --grep="fix|bug|broken" --name-only --format='' --since="WINDOW" | sort | uniq -c | sort -nr | head -N
```

### 2d. Team Momentum

Commit frequency by month (all time):

```sh
git log --format='%ad' --date=format:'%Y-%m' | sort | uniq -c
```

### 2e. Firefighting Frequency

Emergency/revert commits in the analysis window:

```sh
git log --oneline --since="WINDOW" | grep -iE 'revert|hotfix|emergency|rollback'
```

### 2f. Recently Added Files

New files added in the analysis window:

```sh
git log --diff-filter=A --since="WINDOW" --name-only --format='' | sort | uniq -c | sort -nr | head -N
```

### 2g. Active vs Total Contributors

Count of contributors active in the last 3 months (fixed window — measures "who's here now"):

```sh
git shortlog -sn --no-merges --since="3 months ago" | wc -l
```

Compare this count against the total from 2b.

## Cross-Referencing

After collecting all Phase 2 results, perform these cross-references before presenting the report:

1. **High-Risk Files**: Intersect code hotspots (2a) with bug magnets (2c). Files appearing in both lists are highest-risk.
2. **Risk Ownership**: For each high-risk file, run `git shortlog -sn -- <file>` to identify the primary owner.
3. **Bus Factor Risk**: If active contributors (2g) are less than 30% of total contributors (2b), flag this as a bus factor concern.
4. **Momentum Trend**: Analyze the monthly commit counts (2d):
   - Compare the average of the last 3 months to the average of the 3 months before that.
   - Rising: last 3 months average > prior 3 months average by 20%+
   - Declining: last 3 months average < prior 3 months average by 20%+
   - Erratic: month-over-month variance exceeds 50%
   - Stable: otherwise

## Report Template

Present the report in the terminal using this structure:

```
═══ Codebase Recon Report ═══

Repo Vitals
  Age: [first commit] to [latest commit] | Commits: N | Branches: N | Analysis window: WINDOW

1. Code Hotspots (most-changed files)
   [ranked list: count  filepath]

2. Bug Magnets (files with fix/bug/broken commits)
   [ranked list: count  filepath]

3. High-Risk Files (appear in BOTH hotspots AND bug magnets)
   [list with: filepath — hotspot rank #X, bug magnet rank #Y, primary owner: NAME]
   If none overlap, state: "No files appear in both lists — good sign."

4. Bus Factor
   [top 10 contributors: count  name]
   Active (last 3 months): X of Y total contributors
   [If active < 30% of total: "Warning: low active contributor ratio — knowledge concentration risk"]

5. Team Momentum
   [monthly commit counts, most recent 12 months or all if fewer]
   Trend: [rising / stable / declining / erratic]

6. Firefighting Frequency
   [list of revert/hotfix/emergency commits, or "None found"]
   Rate: N emergency commits out of M total in window (X%)

7. Recently Added Files
   [ranked list: count  filepath]

8. Recommendations
   - Start reading: [top 3 high-risk files, or top 3 hotspots if no high-risk files]
   - Talk to: [primary owner of the #1 high-risk or hotspot file]
   - Watch out: [any trend warnings — declining momentum, low bus factor, high firefighting rate]
```

After printing the report, ask:

> "Want me to save this report to a markdown file? (e.g., `docs/codebase-recon-report.md`)"

If yes, write the same content as a markdown file. Do not commit — let the user decide.
