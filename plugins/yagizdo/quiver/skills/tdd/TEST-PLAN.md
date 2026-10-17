# Test Plan -- tdd

**Trigger:** Reference skill -- not directly invoked. Read by `/plan` Step 5, `/work` Phase 3 and `skills/work/orchestrator.md`, and `/hypothesis-debugging` Step 7; named by `/ship` where it hands the build to `/work`.

**Setup:**
- A Go module with tests.
- A Node project whose `package.json` has no `test` script.

**Expected behavior:**
1. In the Go module, a consumer prints a `red:` line naming the new test before the implementation edit, then a pass line.
2. In the Node project, a consumer prints `skipped: test command none (package.json has no test script)` once and no `red:` line.
3. A task that changes only documentation prints `skipped: no testable behavior (<what the change is>)`.
4. A subagent return with no `TDD` line is recorded as `skipped: no red evidence` and the task still merges.

**Verification checklist:**
- [ ] The Go module run prints a `red:` line naming the test just written, before the implementation edit, then a pass line after it.
- [ ] The Node project prints `skipped: test command none (package.json has no test script)` once, and no `red:` line.
- [ ] A documentation-only task prints `skipped: no testable behavior (...)`.
- [ ] A subagent return carrying no `TDD` line is recorded as `skipped: no red evidence` and the task still merges.
- [ ] The restatement in `skills/work/orchestrator.md` is byte-identical to this file's; no other skill carries a copy.

**Known gotchas:**
- pytest interrupts collection on a top-level import of a not-yet-defined name: exit 2, zero tests run, and the file path stands in for the test name. A name error inside the test body is a named `FAILED` at exit 1 instead.
- go prints compiler `file:line:col` lines and `FAIL <pkg> [build failed]` for that package only; the other packages still run.
- cargo stops every target at exit 101 and prints no test name.
- mocha exits the failure count on failures, and 1 on a load error with `Exception during run:` and no failure list.
- jest prints the failure title under `FAIL <path>`, and `Test suite failed to run` on an import failure; it prints no end summary block with 20 or fewer suites.
- vitest prints `FAIL <file> > <suite> > <name>` in its `Failed Tests` block, and `FAIL <file> [ <file> ]` under `Failed Suites` on an import failure.
- node:test names a file that failed to load as a path subtest -- tap output on Node 22 and earlier, spec output on Node 23 and later.
- rspec prints `An error occurred while loading <file>` and runs no example.
- minitest and `bin/rails test` abort before `# Running:` with a Ruby trace.
- dart and flutter print `loading <path> [E]` then `Failed to load "<path>"` and still run the other files, in the expanded form when output is not a TTY.
- Exit code alone never separates a new red from a pre-existing failure -- pytest and mocha excepted -- the name on the line does.
