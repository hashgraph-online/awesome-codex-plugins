---
name: verification
description: "Verification command resolution and evidence rule for skills that run a project's tests or build before calling work done. Resolves the test and build command from project instructions, then from the stack, then to none; defines what a pass, fail, or skipped claim must quote."
user-invocable: false
---

# Verification

Reference skill read by `/work`, `/ship`, `/design-build`, and `/hypothesis-debugging` at their verification step. It is never invoked and never runs a command itself: the consumer resolves the command by the rules here, runs it, and quotes the evidence.

## Command Resolution

```
test: <command> | none (<reason>)
build: <command> | none (<reason>)
source: docs | stack | none
```

The consumer resolves once, before the first task runs, records these three lines, and passes the resolved command to every subagent as a literal. `none` is a value, not a gap to fill: it carries its reason in the parentheses and is never promoted to a guess. Test and build resolve independently under the same rules; `source` names the rule that produced the test command.

Apply the rules in order. The first rule that yields a command decides `source`.

1. *Project instructions.* A command named in the project's `CLAUDE.md`, `AGENTS.md`, or equivalent agent-instruction file, in a Testing or Build section. When present it wins and `source` is `docs`.
2. *Stack detection.* The table below, matched on files at the project root. `source` is `stack`.
3. *None.* `source` is `none`. Write the reason in the parentheses; never substitute a guess.

A command from rule 1 or 2 is confirmed before it runs: the script or task is declared in the manifest, and the tool is on `PATH` (`command -v`). A command that fails confirmation resolves to `none` with the reason, not to the next rule.

| Stack | Signal | Test command | Build command | Confirm | Summary line | Exit caveat |
|-------|--------|--------------|---------------|---------|--------------|-------------|
| **Node** | `package.json`; package manager from the lockfile (`package-lock.json` npm, `pnpm-lock.yaml` pnpm, `yarn.lock` yarn, `bun.lock` or `bun.lockb` bun); a `packageManager` field overrides | `CI=true <pm> run test` | `<pm> run build` | `scripts.test` in `package.json` is a string that is not the placeholder `echo "Error: no test specified" && exit 1`, and `command -v <pm>` finds the resolved manager; same for `scripts.build`; a missing script is `none` | jest `Tests: N passed, N total`; vitest `Tests  N passed (N)`; mocha `N passing`; node:test `pass N` (spec reporter, the default since Node 23) or `# pass N` (tap, Node <=22 on a pipe) | mocha exits the failure count; jest and vitest exit 1 on zero test files; node:test exits 0 and prints `pass 0`, so only the summary line separates `skipped` from `pass`; `bun test` is not the script, use `bun run test` |
| **Python** | `pyproject.toml`, `setup.py`, or `requirements*.txt`; runner from `uv.lock` (`uv run pytest`), `poetry.lock` (`poetry run pytest`), else `python -m pytest`; `python -m unittest discover` only when pytest is not declared and `tests/` or `test_*.py` exists | as resolved | `uv build` / `poetry build` / `python -m build` only when `pyproject.toml` has `[build-system]` or `setup.py` exists, else `none (application, no build step)` | pytest declared in `pyproject.toml`, `requirements*.txt`, `tox.ini`, or a `pytest.ini` exists, and `import pytest` succeeds under the resolved runner (`uv run python -c "import pytest"`, `poetry run python -c "import pytest"`, else `python -c "import pytest"`); `python -m build` needs `import build` under the same runner | pytest `N passed in Xs`; unittest `Ran N tests` then `OK` | exit 5 from pytest, or from unittest on 3.12+, means no tests ran: `skipped`, not `fail` |
| **Go** | `go.mod` | `go test ./...` | `go build ./...` | `command -v go` | `ok  <pkg>  Xs` per package; build prints nothing on success, quote `no output, exit 0` | exit 0 with only `[no test files]` lines is `skipped`, not `pass` |
| **Rust** | `Cargo.toml`; add `--workspace` when a `[workspace]` table exists | `cargo test` | `cargo build` | `command -v cargo` | `test result: ok. N passed; ...` once per target, quote the last line and the target count; build `Finished ... target(s) in Xs` | exit 101 on failure; `0 passed` on every target is `skipped` |
| **Ruby** | `Gemfile` and `Gemfile.lock`; `rspec-core` in the lock -> `bundle exec rspec`; `minitest` in the lock with `test/` -> `bundle exec rake test`; `bin/rails` present -> `bin/rails test` | as resolved | `bundle exec rake build` only when a `*.gemspec` exists and the Rakefile requires `bundler/gem_tasks`, else `none (application, no build task)` | `bundle exec rake -T test` lists the task for rake-based runners; `command -v bundle` | rspec `N examples, N failures`; minitest `N runs, N assertions, N failures, N errors` | `0 examples` or `0 runs` exits 0 and is `skipped` |
| **Flutter/Dart** | `pubspec.yaml`; Flutter when `sdk: flutter` appears under `dependencies`, else Dart | `flutter test` (Dart: `dart test`) | `flutter analyze` (Dart: `dart analyze`); `flutter build <target>` only when the matching platform directory (`android/`, `ios/`, `web/`, `macos/`, `linux/`, `windows/`) exists and the consumer asked for an artifact; never `flutter build apk` on a project with no `android/` | `command -v flutter` (or `dart`) and `test/` contains at least one `*_test.dart` | "All tests passed!", "Some tests failed.", "No tests ran."; analyze "No issues found!" | "No tests ran." exits 79: read the line, not the code; `skipped`, not `fail` |

### Cross-cutting rules

1. Exit 0 is not evidence. The summary line must show at least one test executed; otherwise the outcome is `skipped`.
2. Compare exit codes as zero versus nonzero, never `== 1`. pytest and unittest exit 5 when nothing ran, the Dart test runner exits 79, cargo exits 101, and mocha exits the failure count.
3. Never let a runner wait. `CI=true` on every Node script, `vitest run` in place of a bare `vitest` script, and the consumer's own wait rules for cold builds.
4. A command is runnable only when the tool is on `PATH` and the script or task is declared. Otherwise it is `none`.
5. A failure whose first error line names a service, port, or environment variable (a `docker-compose.yml`, `.env.example`, or `DATABASE_URL` in test config is the usual signal) is reported verbatim and flagged as environmental. It is not counted as a code failure and not retried.

## Evidence Rule

- **Pass** is this run's exit code plus the runner's summary line, from a run made after the last edit. When the runner prints no summary, the last output line stands in.
- **Fail** is the first failing test name plus the first error line. More output belongs in a report file, not in the evidence line.
- **Skipped** carries its reason: `none` from resolution, a failed confirmation, or a zero-test run. It never counts as a pass; a consumer that requires a pass treats skipped as not passed.
- **No evidence means not run.** "Should pass", "ran earlier", and "the change is safe" are not outcomes.
- **A command that has not returned is not a pass.** Waiting for it is the consumer's business.

Consumers quote the outcome in one of these line formats:

```
pass:    <command> -> exit 0: <summary line>
fail:    <command> -> exit <code>: <first failing test> -- <first error line>
skipped: <reason>
```

## For Skill Authors

- Read this file at the verification step, not at skill start.
- Resolve once per run in the controller and pass the resolved command into any subagent prompt as a literal (`Test command: npm test`), never as "detect the test command".
- Require the evidence line format back from a subagent, and paste the `### Subagent restatement` below into its prompt verbatim. It is the only text from this file that is copied anywhere, and `tests/skills/test-verification-contract.sh` compares the copies to it.
- Do not restate the resolution table. When a stack is missing, add a row here.

### Subagent restatement

Run the test command you were given exactly as written, and report a pass only by quoting this run's exit code and the runner's summary line -- a run that executed zero tests, a command that has not returned, or a result remembered from an earlier run is not a pass. On failure, quote the first failing test name and the first error line.
