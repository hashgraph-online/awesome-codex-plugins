---
name: refactor
description: 'Execute safe refactors.'
---
# Refactor Skill

> **Quick Ref:** Safe, incremental refactoring with test verification at every step. One transformation, one test run, one commit. Never batch.

**YOU MUST EXECUTE THIS WORKFLOW. Do not just describe it.**

## Modes

### 1. Target Mode (default)

```
$refactor <file-or-function>
```

Refactor a specific file, function, or class. You identify what needs improving, plan the steps, and execute them one at a time with test verification.

### 2. Sweep Mode

```
$refactor --sweep <scope>
```

Find and fix complexity hotspots across a directory, package, or entire project. Runs `$complexity` first to identify targets, then works through them in priority order (highest complexity first).

`<scope>` can be:
- A directory path (`cli/internal/`)
- A package name (`goals`)
- `all` (entire project -- use with caution)

### 3. Extract Mode

```
$refactor --extract <pattern>
```

Extract method, class, or module from a target. The `<pattern>` describes what to extract:

- `method:<function-name>` -- extract a section of a long function into a named helper
- `module:<file>` -- split a god file into focused modules
- `class:<class-name>` -- extract a class into its own file

## Core Principle

**Every refactoring step must be verified by running tests before proceeding to the next step.**

For simplification, de-slop cleanup, over-abstraction removal, or readability-focused refactors, load [references/behavior-preserving-simplification.md](references/behavior-preserving-simplification.md) before planning transformations.

No batching. No "I'll run tests after all changes." Each transformation is atomic:

```
Transform -> Test -> Pass? -> Commit -> Next
                       |
                       No -> Revert -> Re-analyze
```

## Execution Steps

### Step 0: Pre-flight -- Establish Green Baseline

Run the full test suite for the target scope BEFORE making any changes.

**Go projects:**
```bash
cd cli && go test ./...
```

**Python projects:**
```bash
pytest
```

**If tests fail: STOP.** Do not refactor code with a broken test suite. Fix the failing tests first, or scope your refactoring to exclude the broken area.

Record the baseline:
- Number of passing tests
- Test execution time
- Any skipped tests

### Step 1: Analyze Target

**Target mode:** Read the target code. Identify:
- Cyclomatic complexity (count branches, loops, conditions)
- Function length (lines)
- Parameter count
- Nesting depth
- Code duplication
- Naming clarity

**Sweep mode:** Run `$complexity` on the scope to get a ranked list of targets:
```
$complexity <scope>
```
Sort by complexity score descending. Work the worst offenders first.

**Extract mode:** Read the target and identify the extraction boundary:
- What code moves out?
- What interface connects the pieces?
- What are the inputs and outputs of the extracted unit?

### Step 2: Plan Refactoring

For each target, produce a numbered list of specific transformations:

```
1. Extract lines 45-78 of processConfig() into validateConfig()
2. Replace nested if/else at line 92 with guard clause + early return
3. Rename `cfg` to `clusterConfig` for clarity
4. Inline single-use helper `tmpName()` at line 120
```

For each transformation, identify:
- **Which tests cover it** -- grep for test functions that exercise the target
- **Risk level** -- low (rename, formatting), medium (extract, inline), high (interface change, moved code)
- **Order dependency** -- does this step depend on a prior step?

If no tests cover the target: write tests FIRST. Do not refactor untested code.

### Step 3: Execute Step-by-Step

For EACH transformation in the plan:

#### 3a. Make ONE transformation

Apply a single, focused change. Do not combine multiple transformations. Keep the diff minimal and reviewable.

#### 3b. Run tests immediately

```bash
# Go
cd cli && go test ./...

# Python
pytest

# Or the project-specific test command
```

#### 3c. Evaluate result

**Tests pass:**
- Commit with conventional commit format:
  ```
  refactor(<scope>): <description>
  ```
  Examples:
  - `refactor(goals): extract validateConfig from processConfig`
  - `refactor(hooks): simplify conditional logic in pre-push gate`
  - `refactor(cli): reduce parameter count in NewCommand`

**Tests fail:**
- **Revert the change immediately.** Do not debug on top of a broken refactor.
- Re-read the failing test to understand what contract was violated.
- Re-analyze the transformation -- was the approach wrong, or was the scope too large?
- Retry with a smaller, safer transformation.

#### 3d. Proceed to next transformation

Repeat 3a-3c for each planned step. After completing all steps for a target, move to Step 4.

### Step 4: Post-Refactor Verification

After all transformations are complete:

1. **Run full test suite** -- not just the targeted tests, the entire suite:
   ```bash
   cd cli && go test ./...
   ```

2. **Run complexity analysis** on changed files:
   ```
   $complexity <changed-files>
   ```

3. **Compare before/after metrics:**

   | Metric | Before | After | Delta |
   |--------|--------|-------|-------|
   | Cyclomatic complexity | ? | ? | ? |
   | Lines of code | ? | ? | ? |
   | Function count | ? | ? | ? |
   | Max nesting depth | ? | ? | ? |
   | Test count | ? | ? | ? |

4. **Verify no behavioral change** -- the refactored code must do exactly what the old code did. If tests were added, they must pass against BOTH the old and new code.

### Step 5: Output Summary

Write a refactoring summary to `.agents/refactor/`:

```bash
mkdir -p .agents/refactor
```

File: `.agents/refactor/YYYY-MM-DD-refactor-<scope>.md`

Content:
```markdown
# Refactor: <scope>

**Date:** YYYY-MM-DD
**Mode:** target | sweep | extract
**Files changed:** <count>

## Targets

- <file:function> -- <what was done>

## Metrics

| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| Cyclomatic complexity | X | Y | -Z |
| Lines of code | X | Y | -Z |
| Max nesting depth | X | Y | -Z |

## Transformations Applied

1. <description> -- <commit hash>
2. <description> -- <commit hash>

## Tests

- Baseline: X passing, Y skipped
- Final: X passing, Y skipped
- New tests added: Z

## Learnings

- <anything worth noting for future refactors>
```

## Refactoring Catalog

### Extract Method

**When:** Function exceeds 30 lines, or a block of code has a clear single purpose.

**Pattern:**
```
Before: longFunction() { ... block A ... block B ... block C ... }
After:  longFunction() { doA(); doB(); doC(); }
        doA() { ... block A ... }
        doB() { ... block B ... }
        doC() { ... block C ... }
```

**Safety:** Low risk if inputs/outputs are clear. Watch for:
- Shared local variables -- pass as parameters or return as values
- Error handling -- propagate errors from extracted functions
- Side effects -- document any mutations

### Extract Module

**When:** A file exceeds 500 lines, or contains multiple unrelated concerns.

**Pattern:**
```
Before: god_file.go (800 lines, 5 concerns)
After:  config.go (validation, loading)
        metrics.go (collection, reporting)
        handlers.go (request handling)
```

**Safety:** Medium risk. Watch for:
- Circular imports between new modules
- Package-level variables shared across concerns
- Init functions with ordering dependencies

### Rename

**When:** A name is ambiguous, misleading, or uses abbreviations that obscure meaning.

**Pattern:**
```
Before: func proc(cfg *C) error
After:  func processClusterConfig(config *ClusterConfig) error
```

**Safety:** Low risk with tooling. Always:
- Search for ALL references (including string literals, comments, docs)
- Update test assertions that reference the old name
- Check exported symbols -- renaming public APIs is a breaking change

### Inline

**When:** A function or variable adds indirection without adding clarity. Single-use helpers that obscure the flow.

**Pattern:**
```
Before: x := getName(item)    // func getName(i Item) string { return i.Name }
After:  x := item.Name
```

**Safety:** Low risk. Verify the inlined code does not have side effects you are hiding.

### Simplify Conditional

**When:** Nested if/else chains exceed 3 levels, or boolean expressions are complex.

**Patterns:**
- **Guard clauses:** Move error/edge cases to top with early return
- **Early return:** Eliminate else branches by returning early
- **Table-driven logic:** Replace long switch/case with map lookup
- **Polymorphism:** Replace type-based switching with interface dispatch

```
Before:
  if err != nil {
      if isRetryable(err) {
          if attempts < max {
              retry()
          } else {
              fail()
          }
      } else {
          fail()
      }
  } else {
      succeed()
  }

After:
  if err == nil {
      succeed()
      return
  }
  if !isRetryable(err) || attempts >= max {
      fail()
      return
  }
  retry()
```

### Reduce Parameters

**When:** A function takes more than 4 parameters.

**Pattern:**
```
Before: func deploy(name, ns, image string, replicas int, labels map[string]string, timeout time.Duration) error
After:  func deploy(opts DeployOptions) error

type DeployOptions struct {
    Name     string
    NS       string
    Image    string
    Replicas int
    Labels   map[string]string
    Timeout  time.Duration
}
```

**Safety:** Medium risk -- all callers must be updated. Use the struct field convention from `go.md`: grep all call sites and update each one.

### Remove Dead Code

**When:** Functions, variables, constants, or types are defined but never referenced.

**How to identify:**
```bash
# Go: unused exports
go vet ./...
# Or use staticcheck, deadcode, or unparam tools

# Python: vulture or pylint unused-import
vulture <directory>
```

**Safety:** Low risk for truly dead code. But verify:
- Not called via reflection or string-based dispatch
- Not part of an interface implementation
- Not used in build tags or conditional compilation
- Not referenced in external packages (if this is a library)

**CLI command, flag, or cross-language surface removal:** source-language
callers are not enough. Before considering the removal complete, grep every
tracked callsite surface that agents commonly forget:

```bash
scripts/check-removed-symbol-refs.sh -- <removed-command-or-flag>
```

The check searches tracked repo files across source, shell scripts, GitHub
workflow YAML, docs, skills, Codex skills, and tests while excluding historical
changelogs and release notes. Any remaining hit is a blocker unless it is
explicitly excluded with `--exclude` and justified in the closeout.

## Guardrails

### What NOT to Refactor

- **Code you don't understand.** Read it, test it, understand it -- THEN refactor.
- **Code without tests.** Write tests first. Refactoring untested code is gambling.
- **Code under active development.** If someone else is working on it, coordinate first.
- **Performance-critical hot paths** without benchmarks. Measure before and after.

### When to Stop

- **Diminishing returns.** If complexity dropped from 45 to 12, don't chase 8.
- **Test instability.** If tests start flaking, stop and stabilize.
- **Scope creep.** Refactoring should not change behavior. If you find a bug, file an issue -- don't fix it mid-refactor.
- **Time budget exceeded.** Set a timebox. Refactoring expands to fill available time.

### Red Flags During Refactoring

- Tests pass but you changed behavior (test gap -- add a test)
- You need to refactor the tests to make them pass (you broke the contract)
- The diff is growing beyond what you can review in one sitting (split into smaller PRs)
- You are renaming things to match your preference, not for clarity (stop)

## See Also

- `$complexity` -- analyze code complexity metrics
- `$standards` -- language-specific conventions
- `$vibe` -- validate code quality post-refactor
- `$bug-hunt` -- if refactoring uncovers bugs
- `$implement` -- if refactoring requires new code

## Reference Documents

- [references/behavior-preserving-simplification.md](references/behavior-preserving-simplification.md)
