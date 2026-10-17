# Test Plan -- verification

**Trigger:** Reference skill -- not directly invoked. Read by `/work` Phase 2.5 and 4a, `/ship` Phase 3 and Verification Steps 1-2, `/design-build` 3d, and `/hypothesis-debugging` Step 7.

**Setup:**
- A Node project whose `package.json` has no `test` script.
- A Go module with tests.

**Expected behavior:**
1. The Node project resolves to `test: none (package.json has no test script)`.
2. The Go module resolves to `test: go test ./...` with `source: stack`.
3. A project whose `CLAUDE.md` names `make check` resolves to `test: make check` with `source: docs`.
4. A run whose summary line shows zero tests is reported `skipped`, never `pass`.

**Verification checklist:**
- [ ] The Node project prints `test: none (package.json has no test script)`; no guess is substituted.
- [ ] The Go module prints `test: go test ./...` and `source: stack`.
- [ ] The `make check` project prints `source: docs`, and the stack table is not consulted.
- [ ] A zero-test run is reported `skipped`, never `pass`.
- [ ] No consumer contains the string `flutter test`.
- [ ] The restatement in `skills/work/orchestrator.md` is byte-identical to this file's; no other skill carries a copy.

**Known gotchas:**
- Go, Ruby, Rust, and node:test exit 0 when zero tests ran; only the summary line separates `pass` from `skipped`.
- pytest, and unittest on 3.12+, exit 5 when no tests were collected: nonzero, yet `skipped` rather than `fail`.
- `No tests ran.` on Flutter and Dart exits 79, nonzero like a failure; read the line, not the code.
- vitest watches by default on a TTY when `CI` is unset, so a bare `npm test` never returns; every Node script runs as `CI=true <pm> run test`.
