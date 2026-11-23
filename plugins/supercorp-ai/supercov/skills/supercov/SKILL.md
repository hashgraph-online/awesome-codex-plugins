---
name: supercov
description: Measures test coverage, mutation testing and code quality in a repository with the supercov CLI, and turns what it finds into small, focused tests or fixes. Use when the user asks to add or improve tests, find untested code or raise coverage, check whether tests would catch bugs (mutation testing, surviving mutants), or find what to refactor. Works with JavaScript, TypeScript, Python, Ruby, Rust, Go, Java and Kotlin projects.
license: MIT
---

# Supercov

Supercov runs the project's own test command and changes no source, tests or configuration. `npx supercov docs <topic>` prints the guide for the installed version; read it for anything not shown here. Topics: `agent-loop`, `mutation`, `quality`, `supported-suites`, `troubleshooting`.

## Add a test

1. Measure the full suite: `npx supercov -- <test command>`, for example `npx supercov -- npm test`.
2. List targets with `npx supercov runs latest gaps --limit 5`, pick one, and inspect it with `npx supercov runs latest file <path>`.
3. Write one focused test. Change only tests unless the user asks otherwise.
4. Rerun the same command and report the test and the coverage before and after.

## Check that the tests catch bugs

Coverage says code ran, not that a test would fail if it were wrong. Mutation testing changes the code one small edit at a time (a mutant) and checks that a test fails. Use it after writing tests, to check that they assert something, when the user asks whether the tests are good enough, and on a pull request or branch.

1. Run `npx supercov mutants -- <test command>`. It measures the suite, lists the mutants and runs each against the tests that reach it. On a branch or pull request, add `--diff <base>` (for example `--diff origin/main`) to keep only the mutants on changed lines.
2. Read the survivors. The pass's summary ends with them; `npx supercov runs latest mutants --status survived` lists them all, and `npx supercov runs latest mutants <path>` lists a file's mutants by line, each with what it changes, its verdict and why. A weak status of `not-infected` means a test ran the code but never gave it an input where the change matters (for `<` to `<=`, operands that are equal); `not-reached` that no test ran it.
3. Write a test that fails on one surviving mutant, with an assertion on the value it changes. Change only tests.
4. Run `npx supercov mutants` again and report which mutants are now killed and which still survive.

Mutation testing is fully supported for JavaScript and TypeScript, and in preview for Python, Rust, Go and Ruby; Java and Kotlin have no mutants yet. Mutants under a runner Supercov has no strong driver for are `error`, never survivors.

Some mutants no test can tell apart from the original. Do not weaken code to kill them: say why, and the user can list them in `supercov.accepted.json`. Mutation testing reruns the tests, so prefer `--diff` on a large project.

## Quality

- `npx supercov quality` ranks files by code smells, and `npx supercov quality patch` reports what a change introduced.
- It sends source files to TypeSafe using the `TYPESAFE_API_KEY` environment variable. A user who set the key has opted in, so run it without asking again. If the key is missing the command says so: tell the user how to set it, then answer from reading the code and say Supercov did not check it.

Without Node.js 22 or newer, install Supercov as the language guide at https://supercov.com/docs says, and run `supercov` instead of `npx supercov`.
