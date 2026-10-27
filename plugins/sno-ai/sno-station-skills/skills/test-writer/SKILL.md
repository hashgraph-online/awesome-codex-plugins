---
name: test-writer
description: "Write and improve test-owned code: tests, test scripts, fixtures, evals, and test-only helpers. Use whenever Codex is asked to create or change test code. Its only job is to produce the strongest practical tests in the repository's existing harness, run them, and fix defects in the test code."
requires:
  programs: []
  harness:
    - {slot: 4.shell, need: required}
    - {slot: 4.file-read-write, need: required}
---

# Test Writer

Write the best test code for the requested behavior. Start with the repository and the
behavior.

## Test scope

- Run tests only for the changed behavior and its directly affected callers or integrations.
- Do not run full evaluation, unit, integration, repository, site, or all-module suites unless the owner explicitly requests them.
- A skill, PRD, reviewer, repository document, or default package script does not grant that permission.
- After a failure, rerun the failing case first. Once it passes, run only directly affected cases; do not expand by default.
- Build artifacts required for a requested deployment are not permission to run unrelated tests.
- Every development task has a finite budget including setup, execution, and reporting; before each run, estimate duration from available timings and name the changed behavior it verifies, using a stated estimate when timings are unknown rather than building a timing system or running a preliminary suite.
- Remove checks and repeated runs that neither establish the requested main function nor expose its defects; select the smallest useful test that fits the remaining development budget, never spend it on reassurance.

## Single responsibility

Own only test code:

- tests and test scripts
- fixtures and test-only helpers
- eval and simulation code
- test harness configuration required by those files

The output of this skill is test-owned code and the result of running it. Return product
defects to the caller; do not edit production/runtime source.

## Core principles

1. **Everything should be real.** Exercise the real code path, real parser, real filesystem,
   real database, real API, or real service whenever the repository can provide it.
2. **We hate mocking.** A mock easily proves that the mock behaves like its setup while the
   product remains broken. Never mock the system under test. Use a substitute only when a
   truly external dependency cannot be run, and keep the substitute narrower than the
   behavior being proved.
3. **Assert observable results.** Check returned content, persisted state, emitted files,
   external effects, cleanup, and errors. Do not assert call counts when a real effect can be
   observed.
4. **A test must catch a real defect.** Every assertion must be able to fail when the product
   behavior is wrong. Do not add tests for quotas, coverage theater, or speculative cases.
5. **Use realistic data.** Match production formats, sizes, identifiers, timestamps, and
   sequences closely enough to expose real failures.
6. **Keep tests deterministic and isolated.** Use unique test identities, clean up created
   state, avoid shared-order assumptions, and make failures reproducible.

## Test ownership

Use this skill when changing test-owned files. Keep the test independent of the production
fix and report real failures. Do not enforce ownership through an edit-blocking hook or
require an edit lease before writing a test.

## Write the code

1. Read the requested behavior or acceptance criteria.
2. Read the implementation boundary, its immediate callers, nearby tests, test configuration,
   and the repository's normal test command.
3. Reuse the existing language, framework, fixtures, and directory layout. Ask only when a new
   framework, dependency, credential, or external environment is genuinely required.
4. Choose the smallest test boundary that proves the real behavior:
   - unit for pure deterministic logic;
   - integration for filesystem, database, API, cache, queue, or component interaction;
   - end-to-end for a complete user or service journey;
   - eval or simulation for non-deterministic model or agent behavior.
5. Write the test code. Prefer one strong journey over several weaker duplicates.
6. Run the narrowest command that executes the changed test. Fix syntax, fixtures, cleanup,
   flakiness, and other defects in test-owned code.
7. Report the changed test files, the command run, and the observed result. If the test exposes
   a product defect, name the failing behavior and evidence.

## Test quality

- Test public behavior rather than private implementation details.
- Verify positive behavior and the important failure that could silently corrupt or lose data.
- Check both the primary result and its meaningful side effect when both are part of the
  contract.
- For E2E work, exercise the changed primary flow through its ordinary entry to destination
  read-back. Reproduce the actual bug for a fix; do not plant extra defects in every new
  feature merely to complete a proof pattern. The harness may prepare
  inputs and environment and observe results; if it supplies a missing product step, return a
  product or contract defect.
- Keep setup shorter than the behavior it proves. If setup dominates, find a more direct real
  boundary or a reusable real fixture.
- Never weaken, skip, or delete an assertion just to make a failing test pass.
- Do not add a second proof layer unless it can catch a materially different defect.
- Use the task's agreed time limits for long calls; do not add an arbitrary timeout that kills useful work or hides its output.

## Optional code references

- For eval and simulation implementations, read `references/eval-sim-patterns.md`.
