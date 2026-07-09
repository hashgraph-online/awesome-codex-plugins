---
name: eval-regression
description: "Use when user says regression test, eval check, eval regression, test before commit, compare versions, check regressions, run evals, benchmark skill, or /eval-regression. Compares current (modified) version against last committed version to detect regressions, improvements, and behavioral changes."
user-invocable: true
allowed-tools: Glob, Read, Bash, Agent, Write, Grep, Edit
---

# Eval Regression Testing

Compare the current (working-tree) version of a plugin/skill against its last committed version to catch regressions before committing. Thin wrapper around the `skill-creator` plugin (its grader, aggregator, viewer) — locate it once:

```bash
SKILL_CREATOR_PATH=$(ls -d ~/.claude/plugins/cache/claude-plugins-official/skill-creator/*/skills/skill-creator 2>/dev/null | head -1)
```

## 1. Resolve target

Find the target from the argument: `plugins/<arg>/` (plugin) or `plugins/*/<arg>/` (skill), else cwd. Set `PLUGIN_DIR`, `PLUGIN_NAME` (from `plugin.json`), `EVALS_PATH=<PLUGIN_DIR>/evals/evals.json`.

## 2. Verify evals exist

If `evals.json` is missing/empty, offer to either show the schema (`references/regression-schemas.md`) for the user to write them, or generate 5-10 starter evals from the target's behavioral contracts (routing decisions, guard conditions, required tool sequences, anti-patterns) for review.

## 3. Detect changes

`git diff --name-only HEAD -- <PLUGIN_DIR>/`. No changes -> STOP. Otherwise flag which changed files are behavioral (SKILL.md, routing rules, workflow, patterns, agents) vs not (README, docs, formatting); if only non-behavioral, ask whether to proceed.

## 4. Setup workspace

Workspace: `plugins/<PLUGIN_NAME>-workspace/iteration-<N>/`, sibling to the plugin dir, gitignored via `*-workspace/`. Iteration numbers are sequential and never reused — next N is `(ls -d plugins/<PLUGIN_NAME>-workspace/iteration-* | sort -t- -k2 -n | tail -1) + 1`, starting at 1.

Snapshot the committed version without touching the working tree:

```bash
SNAPSHOT_DIR="plugins/<PLUGIN_NAME>-workspace/iteration-<N>/skill-snapshot"
mkdir -p "$SNAPSHOT_DIR"
git archive HEAD -- <PLUGIN_DIR>/ | tar -x -C "$SNAPSHOT_DIR"
```

Write `iteration-<N>/iteration_metadata.json` (schema in `references/regression-schemas.md`).

## 5. Run evals (parallel)

For each eval, spawn two executor subagents (Agent tool, `run_in_background: true`, all launched in one turn = 2 x N): one reading the skill from `<PLUGIN_DIR>/`, one from `<SNAPSHOT_DIR>/<PLUGIN_DIR>/`. Each subagent must respond to `eval.prompt` as Claude Code with the skill loaded, then **STOP after its first routing decision or action choice — do NOT implement** (evals measure routing, not full execution). Save transcripts to `iteration-<N>/eval-<ID>/{new,old}_version/outputs/transcript.md` and `eval_metadata.json` per eval dir.

## 6. Grade results

Grade every run in parallel using `$SKILL_CREATOR_PATH/agents/grader.md`. Per run, write `grading.json` (sibling to `outputs/`) using viewer-strict field names — `text`/`passed`/`evidence`, NOT `name`/`met`/`details`. Schema in `references/regression-schemas.md`.

## 7. Aggregate & analyze

Aggregate via skill-creator, naming the two configurations `new_version`/`old_version` (not `with_skill`/`without_skill`):

```bash
cd "$SKILL_CREATOR_PATH" && python -m scripts.aggregate_benchmark <workspace>/iteration-<N> --skill-name "$PLUGIN_NAME"
```

If it fails, write `benchmark.json`/`benchmark.md` manually per `$SKILL_CREATOR_PATH/references/schemas.md`.

Classify each eval by the old/new PASS-FAIL quadrant — only **REGRESSION (old PASS, new FAIL) is CRITICAL** (others: IMPROVEMENT, STABLE_PASS, STABLE_FAIL). Compare at the assertion level and write `iteration-<N>/regression-report.md` (template in `references/regression-schemas.md`), mapping any regression to the changed file likely responsible.

## 8. Present

Report pass-rate delta and counts per status; name each regression with its suspect file (the user decides fix or accept). If iteration > 1, offer the comparison viewer:

```bash
python "$SKILL_CREATOR_PATH/eval-viewer/generate_review.py" <workspace>/iteration-<N> \
  --skill-name "$PLUGIN_NAME" --benchmark <workspace>/iteration-<N>/benchmark.json \
  --previous-workspace <workspace>/iteration-<N-1>
```

## Rules

- Read-only on the target; never commit (the user decides).
- Same evals/assertions across both versions — only the skill version differs.

## Edge cases

- Compare against an arbitrary commit: `--base <commit>` in place of HEAD.
- Eval references a missing file: skip it, note in report.
- Subagent timeout: mark INCONCLUSIVE, not a regression.
- Committed version unchanged from a prior iteration: reuse that iteration's `old_version` results.
