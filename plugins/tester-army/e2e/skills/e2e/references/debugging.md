# Debugging a failing run

A `docs/<path>.mdx` pointer names an e2e docs page: read
`node_modules/e2e/docs/<path>.mdx` once e2e is installed, else
https://e2e.com/docs/<path>.

Paths below sit under the configured `output` directory; `.e2e` is the
default.

## Contents

- Read the failure
- Rerunning a test while you fix it
- Error codes
- Tools
- Flaky tests
- Is it the app?
- Feedback

## Read the failure

1. Every failure in the terminal output names the failing line with a code
   frame, where the screen was (`❯ at`), the nodes nearest a failed locator
   (`❯ on screen`), and ends with `❯ trace .e2e/results/<test>/trace.md`.
   Open that trace page first: `Look at:`, `Expected:` / `Observed:`,
   `Asked for:` and `Waited:`, whether every attempt failed alike (a bug,
   not a flake), then every step: the node an action landed on, what an
   assertion read while it waited (one value throughout means a wrong
   expectation or a broken app; changing values mean a race), what the app
   logged (`✗ network error: POST /api/save 500`), where the page went, how
   the screen changed (`unchanged` after an action means it had no visible
   effect), the cache's decision for an agent step, the agent's last turns,
   and `## Screen at failure`.
2. Fix from that evidence, never by walking the flow again from the start
   over MCP: the run already saw every screen up to the failure.
   - Fix every line it covers, not only the failing one. The screen at
     failure (also `attempt-<n>/screen-at-failure.txt`) holds the names the
     rest of that screen's lines need.
   - A test stops at its first failed step, and every wrong line after it
     costs another run. Check the lines after it against the screen at
     failure, the app source, or a live session before rerunning.
   - For a screen the evidence and the source leave out, look live (topic
     `mcp`): go straight to that screen (on the web, `navigate` to the
     `❯ at` path), then `observe`, `locate`, or `run_code` the fixed lines.
   - Then rerun only that test by `file:line` (below).
3. `.e2e/report.json` holds the same facts for scripts:
   `jq '.run.results[] | select(.selected and .status != "passed") | {titlePath, file, status}' .e2e/report.json`.

Full reference: docs/debugging.mdx.

## Rerunning a test while you fix it

- Run by `file:line`, not the whole file; re-check the `test(` line after edits above it.
- Pass `--action-timeout 5000` so missing locators fail in 5 s instead of 30 s (keep it above the slowest screen load; per-call `{ timeout }` wins; `expect` defaults to 5 s).
- Keep the replay cache on (`read-write` locally; never pass `--no-cache` on every edit). A failed run keeps every `agent.act` confirmed by a wait or check that passed after it, and reruns only new, changed, failed, or handed-off goals. Give the command a timeout longer than the test (a killed run saves nothing).
- Do not rename the test, `describe`, file, goal instruction, `params`, or agent context once a goal passes: each is part of the cache key. Fixing locators or assertions keeps recordings.
- Pass `--retries 0` when retries are enabled (default 1 in CI): outside strict mode, retries never replay.
- Once green, drop `--action-timeout` and run once with `--no-cache` for agent tests to confirm live execution.

## Error codes

| Code | Usual cause | Fix |
| --- | --- | --- |
| `LOCATOR_NOT_FOUND` | Wrong role or name, inexact text, element off screen or in an iframe, page not open | Read the accessible name on the screen at failure; `exact: false` or a RegExp; `browser.frameLocator` for iframes; `app.open()` first |
| `LOCATOR_AMBIGUOUS` | Two matches (hidden duplicate, repeated label) | A container scope, `filter`, or `{ visible: true }` |
| `ASSERTION_FAILED` | Wrong expectation, or the state settles later than 5 s; for `agent.assert`, a false judgment | Compare with `Observed:`; `{ timeout }` on the matcher; rewrite the question |
| `ASSERTION_INCONCLUSIVE` | `agent.assert` or `agent.extract` asked about what the screen does not show; a failure, never a pass | Wait for the right screen first; ask about what is shown |
| `ACTION_FAILED` | Element covered, disabled, or detached, or an operation timed out | `waitFor` the condition right before the action; close overlays |
| `STEP_NOT_AWAITED` | A step, `expect.poll`, or `toPass` without `await` | `await` the call the code frame names |
| `COLLECTION_ERROR` | `async` describe body, `test.setup` inside `describe`, a fixture that does not destructure its first parameter, an option forbidden in a serial group | Restructure per `writing-tests` |
| `NO_TESTS` | The glob, a file argument, or a tag matched nothing | Check the config `tests`, the `.e2e.ts` suffix, the tag names |
| `MODEL_UNAVAILABLE` | The built-in agent's entry has no model; the run stops at the first `agent` fixture (a model-less custom executor fails only `waitFor` and `extract`) | Configure one (topic `agent`) |
| `MODEL_PROVIDER_FAILED` | Network, 5xx, rate limit, or no key configured (`AI_GATEWAY_API_KEY is not set`); only steps that call the model fail | Set the variable the message names, or say no key is available; never rewrite tests to get around it |
| `STEP_TIMEOUT`, `STEP_BUDGET_EXHAUSTED` | Goal too big or ambiguous | Split the goal, use on-screen wording; raise `maxSteps` or `maxModelCalls` |
| `REPLAY_STALE` | `--strict-cache` or `cache.strict`, and a committed recording no longer replays | Rerun read-write with the knob the message names off, commit the changed entry |
| `APP_UNREACHABLE`, `APP_ALREADY_RUNNING` | The app failed readiness or its command exited; something already serves `url` (often an `e2e mcp` session's app) | Check `app.url`, the port, `app.command.log`; `close_session` first |
| `SERVICE_START_FAILED`, `INVALID_SERVICE_VALUE`, `SERVICE_STOP_FAILED` | A service's `start` threw, never yielded, or ran past `startupTimeout`; it yielded something other than plain data and functions; its stop code threw or ran past `shutdownTimeout` | Fix the service the message names; pass `signal` to what it starts (topic `setup`) |
| `SESSION_UNAVAILABLE`, `SESSION_CONTRACT` | `session: 'x'` with no setup saving `x`; a setup that skipped a declared name | Add or fix the `test.setup` |
| `POLICY_DENIED` | A non-http(s) URL, a password into a non-password field, or reading a secure field's value | Assert the outcome, not the value |
| `UNSUPPORTED_CAPABILITY` | A fixture or action the engine lacks (`browser` on a device) | Declare `platforms: ['web']`; drop the call |

A `TypeError` from `browser` or `device` (`Cannot read properties of undefined`)
means the test ran on a target without that fixture, where it's `undefined`.
Scope the test with `platforms`, or check `platform` first.

Full reference: docs/reference/errors.mdx.

## Tools

| Do | When |
| --- | --- |
| `--headed` | Watch the failing step |
| `--step`, then `e2e run --step next` | An agent steps through the test: each command returns at the next held step with its screen; `stop` ends the run |
| `await screen.pause()` in the test | Pause at that line with the app open; resume with `e2e run --step next` from the same directory |
| `--workers 1 --retries 0` | Take parallelism and retries out of the picture |
| `--no-cache` | Rule out a stale `agent.act` replay, for one run: a failed run already deletes the replay that failed, so rerun with the cache on first. When the failure repeats after a replay the trace page shows as kept and the `--no-cache` run passes, tighten the next check or wait after that goal: the stale replay then fails it and is deleted |
| `--debug` | Each agent step's duration, model calls, cost, transcript |
| `--ai-trace`, then `npx unbox-ai runs .e2e/ai-trace.json` | What the model saw and called |
| `--video=retain-on-failure` | Watch the failed attempt |
| `command.log: '.e2e/logs/app.log'` | The app's output when it never gets ready or errors mid-test |
| `CI=1 npx e2e run` | Reproduce CI-only behaviour (topic `running`) |

## Flaky tests

- A read (`textContent()`, `count()`) caught a value mid-update: use a
  matcher.
- Shared data: each test creates its records with run-unique names in a
  `test.extend` fixture and deletes them after `use()`; with one app-wide
  state no test can own, `workers: 1`. A test that passes in its file but
  fails alone by `file:line` depends on an earlier test: give it its own
  arrange steps, not a `serial` group (topic `writing-tests`, "Each test
  owns its starting state").
- App not ready: wait for the element you are about to use, not the
  previous page.
- An agent judgment asserts exact phrasing: judge the fact, add a
  deterministic `expect` beside it.
- Measure a fix: `npx e2e run <file> --repeat-each 10 --retries 0`
  (`--no-cache` for agent steps); the `Repeats` row names each unstable
  test's failed runs.

## Is it the app?

A deterministic step failing every run at the same place with the same code
is a product bug or a changed screen, not a flake: reproduce once with
`--headed`, then fix the app or update locator and expectation together. A
blocked agent step (`AUTH_CREDENTIAL_UNAVAILABLE`, `ENVIRONMENT_UNAVAILABLE`,
`SEED_DATA_MISSING`) exits 2 or 3 on purpose: fix the environment.

## Feedback

When e2e itself breaks (`bug`), misleads you (`docs`), or lacks a needed
capability (`feature`), offer to report it once after working around it or
giving up. Never report app failures, one-off issues, or outdated e2e versions
(upgrade with `npx e2e@latest upgrade` first). Search
[existing issues](https://github.com/e2e-inc/e2e/issues) first
(`gh issue list -R e2e-inc/e2e --search "<words>"`), and comment on a match
instead of sending a new report. Never file the issue yourself.

A `bug` needs `--repro` (deterministic steps without app content); without it,
omit `--repro` so the command prints a prefilled GitHub issue URL for the user
and sends nothing. Always run with `--dry-run` first, show the user, and send
only with approval. Never include app content, test files, private URLs, or
credentials.

```bash
npx e2e feedback --type bug -m "<one or two sentences>" \
  --repro "<steps that reproduce it every time>" --error-code LOCATOR_AMBIGUOUS \
  --task "<what you were doing>" --expected "<...>" --actual "<error message>" \
  --approach "<what you tried>" --command "<e2e command>" --agent "<agent / model>"
```
