# Running tests

A `docs/<path>.mdx` pointer names an e2e docs page: read
`node_modules/e2e/docs/<path>.mdx` once e2e is installed, else
https://e2e.com/docs/<path>.

## Contents

- Commands
- The replay cache
- Output
- Exit codes
- Continuous integration

## Commands

```bash
npx e2e run [files...] [options]   # run tests
npx e2e list [files...] [options]  # print what run would select; starts nothing
npx e2e explore [goal] [options]   # explore toward a goal without a test file (topic explore)
npx e2e doctor [--check-model]     # can a run start: config, engine setup, models
npx e2e init [directory] [--yes]   # scaffold a project, refresh the agent skill
npx e2e guide [topic]              # print this skill; topics: setup, writing-tests, agent,
                                   # running, explore, debugging, mcp, bug-bash
npx e2e cache ls|clear|stats       # inspect or empty the replay cache
npx e2e mcp [--target <name>]      # MCP server for a coding agent (topic mcp)
npx e2e upgrade [version|tag]      # e2e and its @e2e-dev packages, and this skill's copies
npx e2e feedback -m <text> [opts]  # report a problem with e2e itself (topic debugging)
```

```bash
npx e2e run tests/signup.e2e.ts
npx e2e run signup.e2e.ts:12 --action-timeout 5000 --retries 0   # while fixing one test
npx e2e run tests/agent --tag smoke --exclude-tag slow --grep checkout
npx e2e run --target chromium --headed   # watch it
npx e2e run --last-failed   # the loop after a red run
npx e2e run --no-cache      # agent steps live, once, after the test is green
CI=1 npx e2e run            # the CI defaults, locally
```

- Files narrow the config `tests` glob, never bypass it. A bare name
  (`signup` or `signup.e2e.ts`) selects the matching test file; `file:line`
  is the test whose `test(` opens on that line.
- `--target` and `--tag` take comma-separated or repeated values; an empty
  value exits 2. `--grep` matches the title path (describe titles and test
  title), not the file or tags.
- `--retries 0` while fixing: outside strict mode a retry never replays the
  cache. `--action-timeout 5000` makes a wrong locator fail in 5 s; keep it
  above the slowest screen load and drop it once green.
- `--step` holds each step for a key; without a terminal (an agent's shell;
  if it has one, add `< /dev/null`, or `< NUL` in Windows `cmd`)
  each command returns at the next held step, then `e2e run --step next`,
  `rest`, or `stop` from the same directory (topic `debugging`, "Tools").
- `list` takes the same selection flags, prints `file › title [target]
  #tag` per test and target, and starts no app, engine, or worker.
- With a `package.json` script `"test:e2e": "e2e run"`, pnpm forwards `--`
  literally: `pnpm test:e2e -- --headed` exits 2. Write `pnpm test:e2e
  --headed` or `pnpm exec e2e run --headed`; with npm, `npm exec -- e2e run
  --headed`.
- `run`, `list`, and `explore` are also functions on `e2e/runner`. Await each
  run before the next and close every host first; overlaps reject with
  `RUNNER_BUSY` (docs/reference/runner.mdx).

Full reference: docs/reference/cli.mdx.

## The replay cache

Entries live under `.e2e/cache/` by default, one file per key. `e2e cache
ls` lists them, `stats` sums them, `clear` deletes them; with a custom
`cache.store` these file-store commands refuse (exit 2). `--no-cache` turns the cache
off for one run; `--strict-cache` fails a step whose committed recording no
longer replays (`REPLAY_STALE`) instead of calling the model.

Full reference: docs/cache.mdx.

## Output

`.e2e/` is generated output: read it, never edit it. It holds
`report.json` and `results/<test>/`, one directory per test with its
`trace.md` and an `attempt-<n>/` per attempt (screenshots, videos,
downloads, `--debug` transcripts). `results/` is cleared when a run's tests
start, except that a `--last-failed` rerun keeps the files (fresh attempts
go to `rerun-<n>/`).

- The default `list` reporter ends with a `Failed` section, one entry per
  failed test with its file and line, the error's first line, and its trace
  page, so `| tail` keeps it.
- With the default `trace` mode, `retain-on-failure`, a failed, timed-out,
  interrupted, or flaky test gets `results/<test>/trace.md` (`--trace off`
  writes none): every step, the cache's decisions, the app's
  log, the last model turns, and the screen at failure. Read it first (topic
  `debugging`).
- `report.json` is for scripts (`jq`), not for reading: every result,
  passing ones included, whatever the reporters.
- Other reporters: `--reporter list,junit` (`junit.xml`), `list,markdown`
  (`summary.md` for a pull request), `list,ctrf`, `dot`, `line`, `json` (the
  report on stdout). Two of `list`, `dot`, and `line` together are
  `INVALID_CONFIG`.

Full reference: docs/reference/reporters.mdx.

## Exit codes

| Code | Meaning |
| ---: | --- |
| 0 | Every selected test passed, was flaky, or was skipped |
| 1 | A test or setup test failed or timed out |
| 2 | CLI, config, collection, credential, model-config, or policy error |
| 3 | Engine, app process, model provider, artifact, or cleanup failure |
| 4 | Internal runner error |
| 130 | Interrupted by an external signal |

The highest code present wins. Exit 2 is deterministic: never retry it.
Only exit 3 is worth a job-level retry.
Full reference: docs/reference/cli.mdx.

## Continuous integration

`CI` set (not `0` or `false`) means `retries` 1, `workers` 1, `test.only`
and `describe.only` fail with `ONLY_IN_CI`, and the replay cache is
`read-only` unless the config sets a mode.

- `npx e2e init --yes --ci github-actions` (or `--ci gitlab`) writes a
  workflow with a job per platform the targets run on.
- Install browsers as their own step
  (`pnpm exec e2e-web install chromium --with-deps`).
- Start the app through the target's `app.command`; the runner tears it down
  on every exit path.
- Pass the model key the config reads (`AI_GATEWAY_API_KEY` for `gateway()`)
  as a secret in the run step's `env`, and commit `.e2e/cache/` so recorded
  steps replay with no model call.
- Upload `.e2e/report.json` and `.e2e/results` unless cancelled, so a test
  that passed on retry keeps its evidence.
- `--changed-since <ref>` runs the configured `filters` (such as
  `decisionFilter` from `@e2e-dev/decision`) on a pull request; never pass
  it on `pull_request_target`.
- With `--shard i/n`, give each shard its own `--output` and upload the
  whole directory; `npx e2e merge-reports <shard dirs> --output <dir>`
  builds one report for the matrix. To rerun one shard's failures first,
  reuse its `--output` with `--last-failed` and drop `--shard`.

Full reference: docs/ci.mdx, docs/ci/github-actions.mdx, docs/filters.mdx.
