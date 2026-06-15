---
name: eval
description: "Quality and performance evaluation with baseline comparison. Sub-modes: correctness, performance, quality, regression. Outputs PASS/WARN/FAIL per dimension. Use for pre-ship evaluation or regression checks."
---

# Eval — Quality & Regression Gate

**CRITICAL**: Run `HARNESS_DIR=$(epic path)` first. Never use `.harness/` in the project directory.

## When to Trigger
- Before `/ship` creates a PR (automatic if eval.yaml exists)
- After `/go` completes a feature
- On explicit `/eval` command
- When user mentions "regression", "baseline", "eval suite", "quality check"
- CI: `make eval` or `epic eval --json`

## Execution Modes

4 dimensions run in parallel where possible:

1. **eval:correctness** — Test pass rate, mutation score, assertion density
2. **eval:performance** — Throughput, latency, memory (opt-in)
3. **eval:quality** — Lint, code quality, LLM-as-judge
4. **eval:regression** — Baseline comparison, score deltas

---

## Process

### Step 0: Prerequisites

```bash
HARNESS_DIR=$(epic path)
```

If `$HARNESS_DIR/eval/eval.yaml` does not exist, run scaffold:
```bash
epic eval --init
```

Read the config:
```bash
cat $HARNESS_DIR/eval/eval.yaml
```

### Step 0.5: Scaffold benchmarks (when no benchmark infrastructure exists)

If `eval.yaml` has `benchmarks: []` and no benchmark files are found in the project:

1. **Generate stub files** using the CLI:
   ```bash
   epic eval --scaffold
   ```
   Supported stacks (auto-detected from project markers):

   | Stack | Detected by | Generated file | Output format |
   |-------|-------------|----------------|---------------|
   | Rust | `Cargo.toml` | `benches/eval_harness.rs` | criterion (exit code) |
   | Python | `pyproject.toml` / `setup.py` | `benchmarks/eval_runner.py` | JSON composite |
   | TypeScript | `tsconfig.json` | `benchmarks/eval.ts` | JSON composite |
   | Node.js | `package.json` | `benchmarks/eval.mjs` | JSON composite |
   | Go | `go.mod` | `benchmarks/eval_test.go` | JSON composite |
   | Java | `pom.xml` / `build.gradle` | `benchmarks/EvalBenchmark.java` | exit code |
   | Kotlin | `build.gradle.kts` | `benchmarks/EvalBenchmark.kt` | exit code |
   | Ruby | `Gemfile` | `benchmarks/eval_benchmark.rb` | JSON composite |
   | PHP | `composer.json` | `benchmarks/eval_benchmark.php` | JSON composite |
   | C# | `*.csproj` / `*.sln` | `Benchmarks/EvalBenchmark.cs` | JSON composite |
   | Swift | `Package.swift` | `benchmarks/EvalBenchmark.swift` | JSON composite |
   | Elixir | `mix.exs` | `benchmarks/eval_benchmark.exs` | JSON composite |
   | C++ | `CMakeLists.txt` | `benchmarks/eval_benchmark.cpp` | exit code |

2. **Customize the generated file** — every file has `# TODO` / `// TODO` markers:
   - Replace placeholder logic with calls to your actual domain functions
   - Adjust the composite score weights to reflect your domain priorities
   - For precision/recall benchmarks: wire in your real test set and model

3. **If `--scaffold` can't generate a useful stub** (domain too complex, custom evaluation logic needed), generate a custom benchmark with LLM assistance:
   - Read the project's main source files to understand the domain
   - Identify the 2–3 most critical quality signals (latency, accuracy, throughput, precision/recall)
   - Write a benchmark that measures those signals and outputs `{"composite": 0.0–1.0, ...}`
   - Save to `benchmarks/eval_runner.{ext}` matching the project language

4. **Wire into eval.yaml**:
   ```yaml
   benchmarks:
     - name: eval_runner
       command: python3 benchmarks/eval_runner.py full
       result_type: composite   # parse composite field from JSON stdout
   ```
   Use `result_type: exit_code` for frameworks (criterion, JMH, BenchmarkDotNet) that manage their own output.

### Step 1: Run Rust CLI

Execute the structured evaluation via the Rust binary:
```bash
epic eval --json
```

This runs all enabled dimensions and outputs a JSON result. Capture the output.

If the CLI reports `llm_judge: SKIPPED` (no LLM available in CLI mode), proceed to Step 2 for LLM-as-judge. Otherwise, skip to Step 3.

### Step 2: LLM-as-Judge (when llm_judge enabled)

If the quality dimension has `llm_judge: true` and CLI marked it SKIPPED:

1. Sample 3–5 changed files from the current branch:
   ```bash
   git diff --name-only $(git merge-base HEAD main)
   ```

2. For each sampled file, evaluate on a 1-10 rubric:
   - **Readability** (naming, structure, flow)
   - **Correctness** (logic, edge cases, error handling)
   - **DRY** (no unjustified duplication)
   - **Security** (no obvious vulnerabilities)

3. Average scores across files. Map to 0.0–1.0 scale.

4. Record results alongside CLI output.

### Step 3: Load Baseline

```bash
cat $HARNESS_DIR/eval/baselines/latest.json
```

If no baseline exists, the current run BECOMES the first baseline. Save it:
```bash
epic eval --baseline-update
```

Report: "First baseline established. Future runs will compare against this."

### Step 4: Synthesize Report

Combine CLI output + LLM-as-judge results into a single report:

```
## Eval Report
- Branch: {branch}
- Commit: {commit_short}

### Correctness: [PASS/WARN/FAIL] — score: {score}
- Tests: {passed}/{total} passing ({pass_rate}%)
- Mutation score: {mutation_score}% (if enabled)
- Delta vs baseline: {+/-delta}

### Performance: [PASS/WARN/FAIL] — score: {score} (if enabled)
- Avg latency: {latency}ms (delta: {+/-delta})
- Throughput: {throughput} (delta: {+/-delta})

### Quality: [PASS/WARN/FAIL] — score: {score}
- Lint errors: {count}
- LLM judge: {score}/10 (if enabled)

### Regression: [PASS/FAIL]
| Dimension | Baseline | Current | Delta | Verdict |
|-----------|----------|---------|-------|---------|
| correctness | {prev} | {cur} | {delta} | {pass/fail} |
| quality | {prev} | {cur} | {delta} | {pass/fail} |

### Overall: [PASS/WARN/FAIL] — {overall_score}
```

### Step 5: Act

- **All PASS + no regression**: "Eval passed. Run `/ship` to create a PR."
- **WARN**: Show warnings. Ask whether to fix before shipping.
- **FAIL or regression detected**: List each failure with fix hint. "Fix with `/go`, then re-run `/eval`."

### Step 6: Save Results

```bash
epic eval --baseline-update  # if user approves this as new baseline
```

Results auto-saved to `$HARNESS_DIR/eval/results/EVAL-{timestamp}.json`.

---

## Anti-Rationalization

| Excuse | Rebuttal | What to do instead |
|--------|----------|-------------------|
| "Tests pass, no need for eval" | Tests pass today but regress tomorrow without baselines | Run eval and establish a baseline |
| "Performance testing is premature" | Latency regressions are invisible until users complain | Enable performance dimension, run benchmarks now |
| "Mutation testing is too slow" | Slow mutation catches bugs fast tests miss | Run on changed modules only (`--dimension correctness`) |
| "LLM-as-judge is subjective" | Subjective beats absent — fixed rubric + averaging reduces variance | Use the 4-axis rubric, average across 3+ files |
| "We can add eval later" | Later never comes; regressions accumulate silently | Start with correctness+quality, add dimensions incrementally |
| "CI will catch regressions" | CI only catches build/test failures, not quality drift | Eval measures what CI misses: mutation score, LLM quality |

## Evidence Required

- [ ] `epic eval --json` output captured (all enabled dimensions scored)
- [ ] Baseline comparison performed (or first baseline established)
- [ ] Each dimension has PASS/WARN/FAIL verdict
- [ ] No dimension regressed beyond threshold (or explicit user override)
- [ ] Results saved to `$HARNESS_DIR/eval/results/`
- [ ] LLM-as-judge scores recorded (if enabled)

## Red Flags

- Reporting PASS without actual `epic eval` output
- Skipping regression comparison "because it's the first run" (first run should ESTABLISH baseline)
- Reporting PASS with 0 test coverage
- Ignoring mutation score drops >5%
- Marking eval PASS when any dimension below minimum threshold
- Running eval on main branch instead of feature branch
