---
name: shellscript-coder
description: "Implement and refactor production shell scripts, command-line tools, automation, process wrappers, and Git or infrastructure helpers with reliable failures, useful logs, and machine-readable output."
requires:
  programs: []
  harness:
    - {slot: 4.shell, need: required}
    - {slot: 4.file-read-write, need: required}
---

# Shell Script Coder

Every development task has a finite budget including setup, tests, and reporting.
Before running tests, estimate duration from available timings and identify the changed
behavior or directly affected consumer. If timing is unknown, state an estimate; do not
build a timing system or run a preliminary suite. Full evaluation, unit, integration,
or repository suites require the owner's explicit request, never a skill, PRD, review,
or default command. Remove checks that neither prove the requested main function nor
expose its defects. Repeat only after a relevant change or failure.
Every new security check requires the owner's explicit approval for that specific check;
remove auxiliary security, assertion, hash, or bookkeeping blockers of useful work.


Write small, production-grade Bash that fits the repository and remains understandable during failure. Local instructions define the runtime and style; they may strengthen these rules but not weaken reliability.

## Read Before Writing

- Confirm the required shell from the shebang, callers, CI, and repository docs. Use Bash when the target is Bash; do not claim POSIX portability unless it is required and tested.
- Read the complete target script, immediate callers, sourced libraries, config, and nearby tests. Reuse existing argument, logging, state, and error conventions.
- Before changing a tool version, or using a third-party CLI, API, or service in a way neither the PRD nor existing scripts already show, read its current official documentation; for a version change, read the release notes between the two versions. Name the page and version in the report. When a PRD governs the work and lacks or contradicts that fact, add it to the PRD's execution notes.
- Decide the observable success result, failure result, exit codes, and verification command before editing.
- Preserve unrelated work. Touch only requested behavior and remove only orphans created by the change.

## Boundaries

- No backward-compatibility aliases, dual paths, legacy flags, or fallbacks unless the user confirms an external published contract requires them.
- No speculative options or abstractions. Prefer one explicit path over a configurable framework.
- Use deterministic shell or an existing deterministic helper for routing, parsing, retries, validation, and state transitions. Never ask a model to decide them.
- Never use `eval` or construct executable commands in strings. Use functions and arrays.
- Never print secrets, tokens, credential-bearing URLs, raw environment dumps, or sensitive command lines.

## Reliability

- Start new Bash scripts with `set -Eeuo pipefail` unless a documented caller contract makes one option incompatible. Handle expected nonzero statuses locally instead of globally weakening failure behavior.
- Quote every expansion unless intentional word splitting is proven and commented. Use arrays for argument lists, `--` before user-controlled paths, `[[ ... ]]` for tests, and `printf` rather than `echo` for data.
- Validate required arguments, enums, paths, and dependencies before mutation. Reject unknown flags and malformed state with a specific message and nonzero exit.
- Keep functions focused, use `local`, pass values explicitly, and avoid hidden mutable globals. Constants are uppercase and readonly where practical.
- Clean temporary files, locks, mounts, and child processes with traps or an explicit cleanup function. Preserve the original exit status.
- Write durable files atomically: create in the destination directory, flush when required, then rename. Never expose a partially written state file.
- Use `flock` or the repository's existing lock for shared state. Keep the critical section narrow and define what a lock timeout means.
- Make retryable operations idempotent. Bound retries, use a fresh observation before retrying, and distinguish “already completed” from “failed.”
- Bound external commands with a timeout when they can hang. Propagate signals to children and verify termination when orphaned processes would be harmful.
- For work that may exceed two minutes, emit per-unit progress with completed/total, rate, and ETA.

## Messages and Agent-Facing Interfaces

Design messages as operational evidence, not narration.

- Keep stdout reserved for the primary result. Send progress, diagnostics, and errors to stderr. If `--json` is supported, stdout contains exactly one valid JSON result and no decoration.
- Error messages name: operation, target, failed condition, consequence, and the next safe action. Include relevant identifiers and paths; omit secrets and noisy stack traces unless a debug mode already exists.
- Progress messages identify the current stage and include stable context so a detached AI agent can tell which task and resource produced the line.
- Use stable, documented exit codes when callers branch on failure classes. Otherwise use `0` for success and a small nonzero set; do not invent dozens of codes.
- Prefer non-interactive flags and stdin over prompts. A command intended for agents must support `--help`, reject missing inputs immediately, and never wait silently for a terminal response.
- Make input contracts explicit: required flags, accepted values, path ownership, preconditions, and whether rerunning is safe.
- Make output easy to inspect and bind to the action. For a new JSON interface, prefer a minimal envelope such as `ok`, `operation`, `target`, and either `result` or `error`; include recorded commits, digests, or state paths when they are the proof a controller needs.
- Generate JSON with `jq` or another repository-standard encoder, never by string concatenation.

## Failure Design

For every external command or multi-step mutation, answer:

1. What can fail or time out?
2. What state may already have changed?
3. Can the exact operation be retried safely?
4. What evidence lets an AI agent choose retry, repair, or stop?

Fail closed for publication, deletion, credentials, shared state, and Git ref movement. A partial success must be recorded explicitly; do not collapse it into a generic failure that encourages a destructive retry.

## Verification

Run the narrowest relevant checks first:

1. `bash -n` on every touched Bash file.
2. The repository's ShellCheck or code-check command when configured; do not add a new lint dependency just for ceremony.
3. Focused tests for one accepted path and the nearest rejected boundary.
4. When relevant, tests for timeout, interruption, retry/idempotency, concurrent writers, paths with spaces, and partial failure.
5. Stop after the affected checks pass; the repository's default suite is not permission to expand the test scope.

Use temporary directories, local bare Git remotes, and boundary fakes that assert observable behavior. Do not mock repository-internal logic. Re-read the final diff and remove any line that does not improve required correctness, diagnostics, or operability.

## Delivery

Report the changed behavior, input/output contract, important failure semantics, and exact verification commands with results. State any unverified external dependency plainly; never report success over a failing or skipped required check.
<!-- reminders:start -->
<!-- reminders:end -->
