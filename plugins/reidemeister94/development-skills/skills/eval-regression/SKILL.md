---
name: eval-regression
description: "Use when user says regression test, eval check, eval regression, test before commit, compare versions, check regressions, run evals, benchmark skill, or /eval-regression. Compares current (modified) version against last committed version to detect regressions, improvements, and behavioral changes."
user-invocable: true
allowed-tools: Glob, Read, Bash, Agent, Write, Grep, Edit
---

# Eval Regression Testing

Compare the current (modified) version of a plugin/skill against its last committed version. Detect regressions before committing.

**Requires:** `skill-creator` plugin (provides grader agents, aggregator scripts, eval viewer).

---

## Step 1: Resolve Target

Parse the argument to find the target plugin/skill.

1. Search order:
   - `plugins/<arg>/` — plugin name
   - `plugins/*/<arg>/` — skill within a plugin
   - Current directory if no argument
2. Verify `.claude-plugin/plugin.json` exists (for plugins) or `SKILL.md` exists (for skills)
3. Set:
   - `PLUGIN_DIR` = resolved plugin directory
   - `PLUGIN_NAME` = name from `plugin.json` or directory name
   - `PLUGIN_VERSION` = version from `plugin.json`
   - `EVALS_PATH` = `<PLUGIN_DIR>/evals/evals.json`

---

## Step 2: Verify Evals Exist

Read `EVALS_PATH`.

**If evals.json missing or empty**, tell the user:

> No evals found at `<EVALS_PATH>`.
>
> For meaningful regression tests, the best approach is to create evals from **real usage scenarios** — actual prompts you've used with this skill where you know the expected behavior.
>
> Alternatively, I can analyze the skill's SKILL.md files and generate starter evals covering the main behavioral contracts.
>
> 1. **I'll create evals manually** (recommended) — I'll show you the format
> 2. **Generate starter evals** — I'll analyze and create test cases now

If user chooses (1), show the evals.json schema from `references/regression-schemas.md` in this skill's directory, then STOP.

If user chooses (2):
1. Read all SKILL.md files + routing rules + agent definitions in the target
2. Identify key behavioral contracts: routing decisions, guard conditions, required tool sequences, anti-patterns
3. Generate 5-10 evals covering: happy paths, boundary cases, guard conditions
4. Write to `<PLUGIN_DIR>/evals/evals.json`
5. Present evals summary to user for review before proceeding

---

## Step 3: Detect Changes

```bash
git diff --name-only HEAD -- <PLUGIN_DIR>/
```

**No changes:** Inform user and STOP. Nothing to regression-test.

**Changes found:** List them, categorized as:
- **Behavioral**: SKILL.md, routing rules, workflow, patterns, agents — these affect eval outcomes
- **Non-behavioral**: README, docs, formatting — unlikely to affect evals

If only non-behavioral changes, ask user if they still want to run evals (they may skip).

---

## Step 4: Setup Workspace

Workspace location: `plugins/<PLUGIN_NAME>-workspace/` (sibling to plugin directory, gitignored).

1. Determine next iteration number:
   ```bash
   ls -d plugins/<PLUGIN_NAME>-workspace/iteration-* 2>/dev/null | sort -t- -k2 -n | tail -1
   ```
   Increment by 1. If no previous iterations, start at 1.

2. Create iteration directory:
   ```bash
   mkdir -p plugins/<PLUGIN_NAME>-workspace/iteration-<N>
   ```

3. **Snapshot the committed (old) version:**
   ```bash
   SNAPSHOT_DIR="plugins/<PLUGIN_NAME>-workspace/iteration-<N>/skill-snapshot"
   mkdir -p "$SNAPSHOT_DIR"
   cd <project-root>
   git archive HEAD -- <PLUGIN_DIR>/ | tar -x -C "$SNAPSHOT_DIR"
   ```
   This gives you the complete old version without touching the working directory.

4. Record metadata:
   ```json
   // iteration-<N>/iteration_metadata.json
   {
     "iteration": N,
     "old_version": "<version from git>",
     "new_version": "<version from working dir>",
     "timestamp": "<ISO 8601>",
     "changed_files": ["list", "of", "changed", "files"],
     "evals_count": <number>
   }
   ```

---

## Step 5: Run Evals (Parallel Execution)

Load evals from `EVALS_PATH`. For each eval, spawn **two executor subagents** — one for the new version, one for the old version.

### Locate skill-creator

```bash
SKILL_CREATOR_PATH=$(ls -d ~/.claude/plugins/cache/claude-plugins-official/skill-creator/*/skills/skill-creator 2>/dev/null | head -1)
```

### Executor prompt template

For **each eval**, spawn two subagents using the Agent tool. Launch ALL subagents in the same turn (parallel).

**New version executor:**
```
You are testing a skill's behavioral compliance for regression testing.

1. Read the skill files starting from: <PLUGIN_DIR>/
   - Read SKILL.md files relevant to this eval
   - Read any referenced files (routing rules, patterns, etc.)

2. Now respond to this eval prompt AS IF you were Claude Code with this skill loaded:

   <eval.prompt>

   Input files (if any): <eval.files>

3. Follow the skill's instructions exactly as written
4. Document your reasoning: which skill would you invoke, what routing decisions you make
5. STOP after your first routing decision or significant action choice — do NOT implement

Save your response as a transcript to:
  <workspace>/iteration-<N>/eval-<ID>/new_version/outputs/transcript.md

Format the transcript as:
## Eval Prompt
<the prompt>

## Routing Decision
<your analysis and decision>

## Tool Calls (planned)
<what tools/skills you would invoke and why>
```

**Old version executor:**
Same prompt but reading from the snapshot:
```
Read the skill files starting from: <workspace>/iteration-<N>/skill-snapshot/<PLUGIN_DIR>/
```
Save to: `<workspace>/iteration-<N>/eval-<ID>/old_version/outputs/transcript.md`

### Write eval_metadata.json

For each eval directory, write:
```json
{
  "eval_id": <eval.id>,
  "eval_name": "<eval.name>",
  "prompt": "<eval.prompt>",
  "assertions": [<eval.assertions>]
}
```

### Execution strategy

- Launch all subagents with `run_in_background: true`
- Group: all new_version runs + all old_version runs = 2 * N_evals subagents
- Wait for completion notifications
- As each completes, save timing data to `timing.json` if available

---

## Step 6: Grade Results

After all executors complete, grade each run.

Read the grader instructions: `$SKILL_CREATOR_PATH/agents/grader.md`

For each eval, for each version (new, old):
1. Read the transcript from `outputs/transcript.md`
2. Evaluate each assertion against the transcript
3. For behavioral assertions: check if the described behavior matches the assertion's `pass_criteria`
4. Write `grading.json` to the run directory (sibling to `outputs/`)

**Grading.json format** (viewer-strict field names):
```json
{
  "expectations": [
    {
      "text": "<assertion check description>",
      "passed": true,
      "evidence": "Specific transcript quote or observation supporting the verdict"
    }
  ],
  "summary": {
    "passed": 5,
    "failed": 0,
    "total": 5,
    "pass_rate": 1.0
  }
}
```

**Grade in parallel** — spawn grader subagents for all runs simultaneously.

---

## Step 7: Aggregate & Regression Analysis

### 7a: Aggregate benchmark

Try the skill-creator aggregation script first:
```bash
cd "$SKILL_CREATOR_PATH" && python -m scripts.aggregate_benchmark \
  <workspace>/iteration-<N> \
  --skill-name "$PLUGIN_NAME"
```

If the script fails or doesn't handle the directory layout, generate `benchmark.json` and `benchmark.md` manually following the schema in `$SKILL_CREATOR_PATH/references/schemas.md`.

Configurations in benchmark: `new_version` and `old_version` (instead of `with_skill`/`without_skill`).

### 7b: Regression analysis

This is the core value of this skill. Compare new vs old results per-eval:

| Status | Condition | Severity |
|--------|-----------|----------|
| **REGRESSION** | Old PASS, New FAIL | CRITICAL |
| **IMPROVEMENT** | Old FAIL, New PASS | Positive |
| **STABLE_PASS** | Both PASS | No change |
| **STABLE_FAIL** | Both FAIL | Pre-existing |

For each eval, compare at the **assertion level**:
- Which specific assertions regressed?
- Which improved?
- What's the overall pass rate delta?

Write regression report to `<workspace>/iteration-<N>/regression-report.md`:

```markdown
# Regression Report: <PLUGIN_NAME>
## <old_version> -> <new_version> | <timestamp>

## Executive Summary
- Evals: <total> | Assertions: <total>
- Regressions: <count> | Improvements: <count>
- Old pass rate: <X>% | New pass rate: <Y>% | Delta: <Z>%
- Verdict: <SAFE TO COMMIT | REGRESSIONS FOUND — REVIEW REQUIRED>

## Regressions (MUST REVIEW)
| Eval | Assertion | Old | New | Evidence |
|------|-----------|-----|-----|----------|
| ...  | ...       | PASS| FAIL| ...      |

## Improvements
| Eval | Assertion | Old | New | Evidence |
|------|-----------|-----|-----|----------|

## Per-Eval Details
[For each eval: name, category, old result, new result, assertion-level comparison]

## Changed Files That May Have Caused Regressions
[Map regressions to specific file changes when possible]
```

---

## Step 8: Present Results

### Always show: concise summary

```
Regression Test: <PLUGIN_NAME> v<old> -> v<new>
============================================================
Changed files:  <N> files (<behavioral_count> behavioral)
Evals run:      <N> (<assertions> assertions)
Old pass rate:  <X>%
New pass rate:  <Y>%

Regressions:    <count>  |  Improvements: <count>
Stable pass:    <count>  |  Stable fail:  <count>

[If regressions > 0:]
REGRESSIONS DETECTED:
  <eval-name> / <assertion>: was PASS, now FAIL
    -> <brief evidence>

[If regressions == 0:]
No regressions. Safe to commit.

Full report:  <path to regression-report.md>
Benchmark:    <path to benchmark.md>
```

### Offer viewer (if iteration > 1)

If previous iterations exist, offer to launch the interactive comparison viewer:
```bash
python "$SKILL_CREATOR_PATH/eval-viewer/generate_review.py" \
  <workspace>/iteration-<N> \
  --skill-name "$PLUGIN_NAME" \
  --benchmark <workspace>/iteration-<N>/benchmark.json \
  --previous-workspace <workspace>/iteration-<N-1>
```

### Guidance based on results

- **No regressions**: "Safe to commit. Run `/commit` when ready."
- **Regressions found**: "Review the regressions above. The changes in `<files>` likely caused them. Fix the regressions before committing, or accept them if intentional behavioral changes."
- **All regressions + improvements**: "Trade-off detected: you gained `<improvements>` but lost `<regressions>`. Review whether this is acceptable."

---

## Rules

- **Read-only testing** — never modify the target plugin during the test
- **Never commit** — the user decides when to commit
- **Parallel execution** — run all evals in parallel for speed
- **Strict grading fields** — viewer requires `text`, `passed`, `evidence` (not `name`/`met`/`details`)
- **Iteration numbers** — sequential, never reused
- **Workspace is gitignored** — `*-workspace/` pattern in `.gitignore`
- **Deterministic comparison** — same evals, same assertions, only the skill version differs

## Edge Cases

- **No git changes but user wants to compare**: Allow specifying `--base <commit>` to compare against a specific commit
- **Evals reference files that don't exist**: Skip that eval, note it in the report
- **Subagent timeout**: Note the eval as INCONCLUSIVE, don't count as regression
- **Previous iteration exists with same version**: Reuse old_version results if the committed version hasn't changed (optimization)
