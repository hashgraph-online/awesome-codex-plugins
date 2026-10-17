---
name: supercov
description: Measures test coverage and code quality in a repository with the supercov CLI, and turns what it finds into small, focused tests or fixes. Use when the user asks to add or improve tests, find untested code or raise coverage, or find what to refactor. Works with JavaScript, TypeScript, Python, Ruby, Rust, Go, Java and Kotlin projects.
license: MIT
---

# Supercov

Supercov runs the project's own test command and changes no source, tests or configuration. `npx supercov docs <topic>` prints the guide for the installed version; read it for anything not shown here. Topics: `agent-loop`, `quality`, `supported-suites`, `troubleshooting`.

## Add a test

1. Measure the full suite: `npx supercov -- <test command>`, for example `npx supercov -- npm test`.
2. List targets with `npx supercov runs latest gaps --limit 5`, pick one, and inspect it with `npx supercov runs latest file <path>`.
3. Write one focused test. Change only tests unless the user asks otherwise.
4. Rerun the same command and report the test and the coverage before and after.

## Quality

- `npx supercov quality` ranks files by code smells, and `npx supercov quality patch` reports what a change introduced.
- It sends source files to TypeSafe using the `TYPESAFE_API_KEY` environment variable. A user who set the key has opted in, so run it without asking again. If the key is missing the command says so: tell the user how to set it, then answer from reading the code and say Supercov did not check it.

Without Node.js 22 or newer, install Supercov as the language guide at https://supercov.com/docs says, and run `supercov` instead of `npx supercov`.
