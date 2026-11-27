# Driving the app over MCP

A `docs/<path>.mdx` pointer names an e2e docs page: read
`node_modules/e2e/docs/<path>.mdx` once e2e is installed, else
https://e2e.com/docs/<path>.

`e2e mcp` serves a project's live app to a coding agent over MCP (stdio). The
coding agent drives the app the way the testing agent does, writes a test
as it walks the flow, and checks its locators and runs its lines before
writing them. Tests run with `npx e2e run` (topics `running` and
`debugging`); to fix one failing test, a session can run it and stop on the
screen where it failed.

## Contents

- Setup
- Tools
- Prefer `run_code`
- Workflow
- Attaching to a held test
- Fixing a failing test
- Rules

## Setup

The server ships with the project's `e2e` dependency. The e2e plugin for
Codex and Cursor registers it; the Claude Code plugin does not. Otherwise
`e2e init` offers to register it for Claude Code, Cursor, and Codex. Reuse
an existing registration, and start the MCP client in the project so the
command uses the installed e2e version. Use the project's package manager: `pnpm
exec e2e mcp` in a pnpm project (`npx` fails there with `EBADDEVENGINES`
when `devEngines` pins pnpm, and the client shows only `Connection
closed`), `yarn exec e2e mcp` with Yarn (`yarn --silent exec -- e2e mcp` on Yarn 1), `bunx e2e mcp` with Bun.
For Claude Code:

```bash
claude mcp add --scope project e2e -- npx e2e mcp
```

Or in the client's project config (`.mcp.json`, `.cursor/mcp.json`,
`.vscode/mcp.json`):

```json
{ "mcpServers": { "e2e": { "command": "npx", "args": ["e2e", "mcp"] } } }
```

Codex reads `[mcp_servers.e2e]` from `.codex/config.toml` in a trusted
project (`e2e init --yes --skills none --mcp .codex/config.toml` adds it).
Start a new session after registering so the tools load.

Sessions run on the project's config. In a directory without one, plain
`open_session` fails with `CONFIG_NOT_FOUND`; name the engine package
instead: `open_session {engine: "@e2e-dev/web", app: {url: "http://localhost:3000"}}`,
or `{engine: {package: "@e2e-dev/mobile", options: {platform: "ios"}}, app: {bundleId: "<app>"}}`.
That session has no credentials, secrets, or project tools.
`ENGINE_NOT_INSTALLED` names the install command: run it, or ask the user to
when the sandbox cannot, then open again. `e2e run` and
`open_session {test}` still need a config, so set the project up before
writing tests (topic `setup`). No model is needed for the deterministic
tools.

Full reference: docs/mcp-server.mdx,
docs/reference/mcp.mdx.

## Tools

Four tools on the server registered as `e2e` (`mcp__e2e__open_session` in
Claude Code): `open_session`, `tools`, `call`, and `close_session`.
Everything a session does is a catalog tool run through
`call {tool: "tap", args: {target: "n42"}}`; `tools` lists the catalog and
`tools {tool}` shows one tool's arguments.

- `open_session`: `target` when the config has several, `path` to open on
  one page (pass it whenever you know the page), `headed: true` when the
  user wants to watch, `test` to run one test first (Fixing a failing test),
  `attach` for a held test. Each session has its own browser or device.
  The reply names the first screen (path, node count) without listing it,
  and action results report changes against it: `observe` when you need
  its nodes.
- `close_session`: frees the session's slot once its cleanup finishes, even
  while an unrelated app is still stopping.
- `observe`: one node per line as `#id role "name" ...`, plus the path. Use
  ids from the newest observation; an older id works only when exactly one
  node on the newest screen reads like its node.
- The grammar verbs (`tap`, `type`, `press`, `select`, `check`, `scroll`,
  `drag`, `upload`, `navigate`, `back`, ...): each reports what changed and
  the `Test line:` that repeats it, or `No test line:` and why.
- `type_secret`: fills a configured secret by name; its test line names
  `credentials.user(name)` or `secrets.get(name)`, never the value.
- `locate`: tries one semantic locator and returns how many nodes match and
  the `screen.*` call to write.
- `run_code`: runs a test body's lines on the live session (below).
- `test_lines`: every test line printed or passed so far, in order, as a
  draft test body.
- `screenshot` (masked pixels; secure fields only), the point tools
  (`tap_at`, `type_at`, ...) after a screenshot, each with the test line of
  the listed control it acted on (or `screen.tapAt` for a bare tap), or
  `No test line:` and why, `start_recording` and `stop_recording`, and the
  project's own tools.

Resources: `e2e://guide` and `e2e://guide/<topic>` hold this skill.
Full reference: docs/reference/mcp.mdx.

## Prefer `run_code`

Use `run_code` for most of the work in a session. One call reads the
screen, computes on what it read, acts, and asserts, where single actions
take one call each and an `observe` between them. `screen`, `app`,
`expect`, `credentials`, `secrets`, `services`, and the engine's fixture
(`browser` or `device`) are in scope; there is no `page`.

- A step that repeats (rows of a list, a form with many fields): loop over
  it in one call.
- A question about the screen (how many, which one, does a total add up):
  read with `allTextContents()`, `count()`, or `inputValue()`, compute in
  JavaScript, and `return` the answer.
- A flow of several steps you already know: write them as one call, with
  the `expect` that checks the outcome at the end.
- Something `screen` does not reach: call the engine's fixture, such as
  `await browser.evaluate(() => document.title)`.

```js
const rows = screen.getByRole('listitem');
for (const name of ['Cabin', 'Office']) {
  await screen.getByLabel('Label').fill(name);
  await screen.getByRole('button', 'Add address').tap();
}
await expect(rows).toHaveCount(2);
return await rows.allTextContents();
```

Await each line: a failure nothing awaited fails the call, and an uncaught
one stops the code. Take a single action by node id instead when you want
the `Test line:` it prints. Use `screenshot` when the task is about how the
screen looks: `run_code` reads the accessibility tree, not pixels.

## Workflow

1. Read topic `writing-tests` before you write or edit any test
   (`e2e://guide/writing-tests`, or `npx e2e guide writing-tests`). Then,
   before `open_session`, create `tests/<feature>.e2e.ts` (its "Structure"
   section) with its imports, the feature's `describe(...)`, a `test(...)`
   titled with the one behavior it verifies, and the call that opens the
   screen it covers, such as `app.open('/settings/members')`. A setup test
   (`test.setup`) goes top-level instead, outside any `describe`.
   Then `open_session` and go to that screen: on the web,
   `call {tool: "navigate", args: {url: "<the path app.open names>"}}`; on
   a device, the shortest path from the launch screen. Actions that only got
   you there, such as a sign-in the test's saved session replaces, stay out
   of the test.
2. Walk the flow one screen at a time, and write each screen's steps into
   the file before you leave it. Do not walk the whole flow first and write
   the test from memory afterwards. Each step is one of two kinds:
   - An `agent.act` goal, the default for user flows whenever `e2e.config.ts`
     configures a model or custom executor: write the goal with the words on
     screen and its values in `params`, then walk its path in the session.
     Those actions stay out of the test, and so do the test lines they print.
   - A `screen` line only for low-level mechanics that are themselves under
     test (such as an empty submit, keyboard shortcut, or drag offset), a
     sign-in form in a setup test, or a project with no model configured. A
     value alone is not a reason: a goal takes it in `params`. Act on the
     control by node id, then copy the `Test line:` the action printed into
     the file. When it prints `No test line:`, try a locator with `locate`,
     or write the line and run it with `run_code`.

   A `Test line:` repeats one action; it is not the test's final shape. When
   its locator is already in the test, name it once in a `const`. Reading
   the app's source tells you the flow; it is not the walk. The names a user
   sees on the live screen are the locators, and a `data-testid` from the
   source stays the last resort.
3. When the outcome shows, add its check to the test's assert block, after
   every step: an `agent.assert`, or an `expect` you ran first with
   `call {tool: "run_code", args: {code: "await expect(screen.getByRole('status')).toHaveText('Saved');"}}`.
   Try a locator with `locate` first: zero or several matches would hit the
   test as `LOCATOR_NOT_FOUND` or `LOCATOR_AMBIGUOUS`. A role query's
   `name` is the accessible name only, while `observe` shows a `status`,
   `alert`, or `listitem` by its text: match an unlabelled status with
   `getByRole('status').filter({ hasText: 'Saved.' })` or `getByText`.

   When a `run_code` line fails, the lines before it already ran: check
   where the app is before resuming so you do not repeat an action.

   A walk that goes on to a second behavior goes into a second test in the
   same `describe`, with its own assert block: `navigate` back to the path
   its `app.open` names first. One walk, in order:

   ```text
   write   tests/members.e2e.ts: imports, describe('members'), test('invites a member as an editor'), app.open('/settings/members')
   call    open_session, then navigate {url: "/settings/members"}   its line is the app.open already written
   edit    + await agent.act('invite {email} as an editor', { params: { email: 'ada@example.test' } });
   call    tap, type, select, tap                   the goal's path; its test lines stay out
   call    run_code {code: "await expect(screen.getByRole('status')).toContainText('Invite sent');"}   passed
   edit    + that line, in the assert block
   write   + test('clears the filter with Escape'), app.open('/settings/members')
   call    navigate {url: "/settings/members"}       the new test's fresh start
   call    type {target: "n40", value: "grace"}     exact key mechanics under test; prints the test line below
           Test line: await screen.getByRole("searchbox", "Search members").fill("grace");
   call    press {target: "n40", key: "Escape"}     prints the test line below
           Test line: await screen.getByRole("searchbox", "Search members").press("Escape");
   edit    + those lines, binding the repeated searchbox locator to a const
   call    run_code {code: "await expect(screen.getByRole('searchbox', 'Search members')).toHaveValue('');"}   passed
   edit    + that line, in the assert block
   ```

   If you missed a line, `test_lines` returns every line printed or passed
   in the session, in order. Before the first run, read the file once from
   the top: each test's checks sit together at its end, each title names one
   outcome, no locator is written out twice in one test, and no block of
   steps repeats across tests (topic `writing-tests`, "Structure").
4. Run only that test: `npx e2e run tests/<feature>.e2e.ts:<line>` (topic
   `debugging`, "Rerunning a test while you fix it"). On a failure, fix from
   the run's failure block and the trace page, then rerun the same way. To
   see a screen the evidence leaves out, go straight to it instead of
   walking the flow again: `open_session {test}` stops on the failure
   screen (Fixing a failing test).
5. Leave the session open through those runs, on the screen under test,
   wherever Rules lets a run go beside it. `observe` does not reload:
   `navigate` to the screen again when a run or a fix may have changed it.
   `close_session` once the test passes; an idle session closes after 30
   minutes.

## Attaching to a held test

Pass only `attach` to `open_session`, with the ID from the pause header,
from the test run's directory and the same e2e version:
`open_session {attach: "k3f9"}`. The session has the normal tools on that
target, `run_code` with the engine's fixture (`desktop`, `browser`,
`device`) included, and its `test_lines` belong at the pause point of the
held test.
`close_session` detaches and leaves the test held; Enter, or
`npx e2e run --step next`, resumes the test and ends the attachment.

## Fixing a failing test

When a run's evidence leaves out a screen the fix needs (topic
`debugging`), don't walk the flow again from the start over `call`. A
session runs the test and stops where it failed:

1. `open_session {test: "tests/<feature>.e2e.ts:<line>"}`, where `<line>` is
   the line of the test's `test(` call, not the failing line inside it. The
   test runs the way `e2e run` runs it: hooks, fixtures, and the body.
2. Read the text above the session summary: the outcome, the error code and
   message, the failing line, the URL, and the nodes nearest a locator that
   matched nothing. The session is on the screen where the test stopped.
3. `observe` and `locate` on that screen to find the right name or the
   missing step. Act out the test's next lines with `call`, so the rerun
   finds no second mistake; where a printed `Test line:` differs from the
   test's line, use the printed one. Edit the test file.
4. To rerun, `close_session`, then `open_session {test}` again: it loads the
   edited test fresh and stops on the next failure, or on the final screen.
5. `close_session`, then confirm once with
   `npx e2e run tests/<feature>.e2e.ts:<line>`.

`afterEach` hooks and fixture teardown wait for `close_session`. A test in a
serial group, one that starts from a setup test's `session`, or one that
runs as several agents fails with `SESSION_TEST_UNSUPPORTED`: fix those with
`e2e run`. Several matches fail with `TEST_AMBIGUOUS`, listing them.

## Rules

- Record a demo or a bug for a pull request with `start_recording` once the
  screen is set up, and `stop_recording` when the part worth watching is
  over. Videos are not masked: keep secrets off screen while recording.
- A failed action is an error result naming the tool, its target, and the
  code, and still shows the screen it re-observed: re-aim from that screen.
- Nothing a session does is recorded as a test, and only a test it runs
  (`open_session {test}`) reads or writes the replay cache. The test is the
  file you write as you walk.
- On the web, a session can stay open while `e2e run` runs, unless the two
  collide over the app. Read the target's `app`:
  - No `command` (the app runs elsewhere): both use that app.
  - A `url` on port `0`: each starts its own copy. A dev server that allows
    one copy per directory (`next dev` in Next.js 16) fails the run with
    `APP_UNREACHABLE`; close the session before each run there.
  - A `command` on a fixed port with `reuseExisting: true`: a run uses the
    app the session started. If the session closes during the run, the app
    stops under it; `observe` once before a long run to reset the idle
    clock. With `CI` set, `reuseExisting` is ignored: prefix the run with
    `CI=`, or close the session first.
  - A `command` on a fixed port without it: a run beside the session fails
    with `APP_ALREADY_RUNNING`. Offer the user `reuseExisting: true`; never
    add it unasked. Until then, close the session before each run.
- On mobile, close the session before each run: a session and a run on one
  device fight over it, unless each uses a different target and device.
  Ask before adding a target to the user's config (topic `setup`).
- Parallel agents (subagents) share one server: each opens its own session
  and passes its session id to every `tools`, `call`, and `close_session`.
  On mobile, one target per device, each session on its own target.
- Session errors (`TARGET_REQUIRED`, `NO_SESSION`, `SESSION_REQUIRED`,
  `SESSION_OPEN`, `CONFIG_IN_USE`, `UNKNOWN_TOOL`, ...) say what to pass or
  close in their message. Full list: docs/reference/mcp.mdx.
