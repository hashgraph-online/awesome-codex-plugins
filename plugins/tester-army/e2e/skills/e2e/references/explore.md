# Exploring without a test

A `docs/<path>.mdx` pointer names an e2e docs page: read
`node_modules/e2e/docs/<path>.mdx` once e2e is installed, else
https://e2e.com/docs/<path>.

`e2e explore` runs the agent against the app with a goal instead of a test
file: see what it can do with an app before tests exist, hunt for regressions
on a branch, or find what is worth turning into a test. It needs a config with
a target and an agent that holds a model, nothing else. With no config, it
runs the `e2e init` wizard first in a terminal; without one (an agent's
shell, CI) it fails with `CONFIG_NOT_FOUND`, so run `npx e2e init --yes` first.

```bash
npx e2e explore   # goal: "Explore the app and find bugs"
npx e2e explore 'Explore checkout like a first-time buyer and report anything off'
npx e2e explore --target web --max-steps 4 --headed
npx e2e explore 'Hunt for broken forms' --video
npx e2e explore --session admin 'Explore the admin settings'
npx e2e explore --changed-since origin/main   # explore what the branch changed
```

## Contents

- What a run does
- Start signed in
- Flags
- Reading the result
- When it does not fit

## What a run does

1. Opens the app: the target's URL, or on a device the pinned app, launched
   fresh. Explore installs no build, so a local device target needs
   `app.bundleId`; an `appPath` alone leaves nothing to launch.
2. Plans one step: a structured model call reads the goal, the steps and
   findings so far, and the current screen, and answers with a title and a
   concrete charter for one flow, or decides the goal is covered.
3. Runs the charter as an `agent.act()` step with the project's tools plus
   `report_finding`. The agent reports each defect the moment it has evidence:
   title, `issue` or `warning`, severity 1 to 5, expected, actual, reproduction
   steps. The runner adds the path and a redacted screenshot.
4. Repeats until the planner finishes, the step limit, the clock, or three
   failed or blocked steps in a row that reported nothing; then asks for a
   closing assessment.

A failed step does not end the run: it is recorded, and only reported issues
fail the product verdict. A run whose charters were all blocked stays blocked.
A step that hits its action or time budget ended at its limit and counts as
neither. Configured `credentials` reach the explorer as step secrets: the
planner knows the account names and usernames, and the agent fills passwords
with `type_secret` by name. That tool is offered only when the engine can fill
secrets; otherwise the agent skips signing in and says so in the step summary.

## Start signed in

`--session <name>` starts from a session a setup test saves
(`test.setup('...', { sessions: ['admin'] }, ...)` and `session.save('admin')`,
topic `writing-tests`). The run collects the config's test files, runs exactly
the setup that declares the session, then restores it into the exploration
and opens the app, as a test with
`{ session: 'admin' }` does. No other test runs. The setup runs as for
`e2e run`, with the configured agents, cache, and retries; only the
exploration runs as the explorer. The planner and the agent are told they
start signed in, so no charter is spent signing in again. A name no setup
declares fails before any app process starts with `COLLECTION_ERROR`, naming
the declared sessions.

Findings keep their screenshots after a setup that filled a secret. Only
configured secrets are redacted (topic `writing-tests`).

## Flags

- `[goal]`: one quoted sentence naming the area and the posture; default
  `Explore the app and find bugs`.
- `--target <id>` (default: the first target), `--agent <name>`,
  `--session <name>`, `--max-steps <n>` (default 8),
  `--timeout <ms>` (default 600000; the last minute is for the assessment).
- `--changed-since <ref>` explores what the branch changed since the merge
  base: only a defect the change can cause is an `issue`, one elsewhere is a
  `warning`. With no goal, the planner may skip a change no user can see
  (docs or tests only); that run ends `skipped` and passes. In CI it needs
  the base in the checkout (`fetch-depth: 0`), and a clean working tree for
  the skip.
- `--headed`, `--video`, `--trace`, `--debug`, and `--ai-trace` mean what
  they mean for `e2e run`. The exploration is one attempt, so a retry mode
  records nothing: pass `--trace on`.

The replay cache is off and retries are zero for the exploration. Per-step
action and model-call budgets default to 40 each; `agents.<name>.maxSteps`
and `maxModelCalls` override them.
Full reference: docs/explore.mdx, docs/reference/cli.mdx.

## Reading the result

- Exit code `0`: steps ran, no `issue` was reported, and not every charter
  was blocked; warnings are allowed. With `--changed-since`, a change the
  planner skipped before the first step is also `0`. `1`: at least one
  `issue`, or no step ran and nothing was found. A run whose charters were all blocked is `blocked` and exits with
  the first blocker's code, as for `run` (1 for an automation limit, 2 for a
  missing model, credentials, or setup; 3 for an unavailable environment).
- The terminal lists each finding as it is reported, then a `Findings`
  section (issues first, most severe first) with where it was seen, its
  screenshot path, expected against actual, and the steps that reach it,
  then the closing `Assessment`.
- `.e2e/report.json` holds the record under `run.explore` (goal, steps,
  findings with `reproduction`, `expected`, `actual`). Screenshots are in
  `.e2e/results/explore-<slug>-<id>/attempt-1/`.

Turn a finding into a test: its `reproduction` steps are the `agent.act()`
instructions or `screen.*` actions, and `expected` is the assertion.

## When it does not fit

The agents entry's `tools` and `system` carry over to the explorer; a
hand-rolled `StepExecutor` under `executor` is replaced by the built-in agent
for the run, with a notice on stderr, and needs a `model` on the entry (or the
executor's) or explore fails before it starts. Findings are the model's claims
plus evidence, not verified reproductions: read `actual` against the
screenshot before filing a bug.
