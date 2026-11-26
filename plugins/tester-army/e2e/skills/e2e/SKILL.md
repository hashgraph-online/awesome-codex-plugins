---
name: e2e
description: Writes, runs, and debugs web, mobile, and desktop end-to-end tests with e2e (mixing agent.act goals with locator assertions), drives apps live over e2e mcp, and runs e2e explore bug bashes. Use when a project uses e2e or asks for end-to-end, browser, mobile, or agentic UI tests, live app checks, or QA bug bashes.
---

# e2e: agentic end-to-end tests

e2e runs UI and API tests that mix agent instructions (`agent.act`,
`agent.assert`, `agent.waitFor`, `agent.extract`) with exact actions and
checks (`screen`, `app`, `browser`, `device`, `request`, `expect`). Engines:
`@e2e-dev/web` (browsers), `@e2e-dev/mobile` (iOS/Android), and
`@e2e-dev/desktop` (macOS prototype).

## Start here: pick the reference for the job

Load only the one reference that matches the current task before acting. Each
stands on its own; inside a long reference, read its `## Contents` list and
jump to the sections you need instead of loading unrelated topics upfront.
`npx e2e guide <topic>` prints the installed package's copy; prefer it when
versions differ.

| When you are | Topic | Read |
| --- | --- | --- |
| Adding e2e, writing `e2e.config.ts`, starting the app, configuring models or mobile targets | `setup` | [references/setup.md](references/setup.md) |
| Driving the running app live, checking UI changes, taking screenshots or videos, trying locators, recording lines over `e2e mcp` | `mcp` | [references/mcp.md](references/mcp.md) |
| Writing or fixing a test (structure, fixtures, locators, matchers, sessions, `browser`, API tests) | `writing-tests` | [references/writing-tests.md](references/writing-tests.md) |
| Adding `agent.*` steps, picking models, tuning cost/budgets, replay cache | `agent` | [references/agent.md](references/agent.md) |
| Running tests, CLI flags, CI, reporters, `report.json`, exit codes | `running` | [references/running.md](references/running.md) |
| Fixing a failed run, error codes, rerunning fast, `--headed`, `--debug`, `--ai-trace`, reporting e2e bugs | `debugging` | [references/debugging.md](references/debugging.md) |
| Running goal-driven exploration without a test file (`e2e explore`) | `explore` | [references/explore.md](references/explore.md) |
| Running a bug bash or QA pass across an app or branch | `bug-bash` | [references/bug-bash.md](references/bug-bash.md) |

References keep the rules and point to the docs for full API tables. A
pointer such as `Full reference: docs/reference/cli.mdx.` names a page that
ships in the installed package at `node_modules/e2e/docs/reference/cli.mdx`
and is online at https://e2e.com/docs/reference/cli. Read the page only when
you need an option, matcher, or flag the reference does not show. Complete
examples live at https://github.com/e2e-inc/e2e/tree/main/examples.

## Workflow

1. Inspect `e2e.config.ts` (or `.mts`/`.js`/`.mjs`), `package.json`, and
   existing tests, fixtures, helpers, and page objects under `tests/`. Reuse
   existing fixtures, helpers, and locators instead of duplicating setup. If
   e2e is not installed and the user asked for it, read `setup`.
2. Read the one matching reference (`writing-tests`: always read "A complete
   file" and "Structure" first, then only the API sections you need; `mcp`
   when driving live, writing steps as you walk and preferring `run_code`;
   `agent` when adding `agent.*` steps).
3. Shape each file per `writing-tests` ("Structure"): one top-level `describe`
   per feature, one behavior and one goal per test, arrange -> act -> assert
   with every `expect` and `agent.assert` at the end. When `e2e.config.ts`
   configures a model or executor on `agents.default` (or on a named
   `agents.<name>`, selected with `{ agent: '<name>' }` or `--agent <name>`),
   write user flows (forms, buttons, cart/CRUD mutations, navigation, auth)
   with `agent.act` (values in `params`); reuse existing fixtures, helpers,
   and page objects, and do not avoid `agent.act` on new user flows merely
   because a `test.setup` or login file uses `screen.*`. Never assert mid-way
   (use `.waitFor()` on a narrowed locator); name repeated locators/values;
   own server data and cleanup in `test.extend` fixtures (`try`/`finally`).
4. **Audit every test before running:**
   - **Prefer `agent.act` when an agent is configured:** normal UI flows
     (submitting forms, editing/deleting items, navigating, signing out) use
     `agent.act` with `params` (selecting `{ agent: '<name>' }` if only a
     named agent is configured) and end with a verifying matcher or
     `agent.assert` for replay-cache confirmation (reserve `screen.*` actions
     for low-level mechanics like keyboard shortcuts, drag offsets, or empty
     submits, `test.setup` sign-in, or model-less configs).
   - **One behavior per test (no undone actions or unchecked screens):** split
     any test whose title combines two behaviors with "and". Never undo an
     action before asserting its effect (an end state equal to the start hides
     a no-op), and never navigate past a screen before checking what that test
     promised on it.
   - **Second item shown, never the first:** in every test that removes,
     edits, or toggles one item of a list, verify arrange adds two items (`A`,
     then `B`), act targets the **second item shown** (`B` in append order,
     `A` in newest-first order, never the first), and assert checks the first
     item is unchanged. Bad: add `A`, add `B`, delete `A`. Good: add `A`, add
     `B`, delete `B`, assert `B` is gone and `A` is unchanged.
   - **No mid-test assertions:** every `expect` and `agent.assert` sits at the
     end of its test with no action after it.
   - **Every test runs alone:** no test depends on an earlier test's state;
     any test must pass when run alone by `file:line`, twice in a row.
5. Run only the test you edit:
   `npx e2e run tests/<feature>.e2e.ts:<line> --action-timeout 5000 --retries 0`,
   keeping the replay cache on until green. Once green, drop
   `--action-timeout` and verify the full suite (and once with `--no-cache`
   if it uses `agent.*`).
6. On failure, fix from the terminal failure block and
   `.e2e/results/<test>/trace.md` first (topic `debugging`); never re-walk
   from scratch over MCP just to inspect a screen.

## Rules

- **No unsolicited setup:** ask before adding e2e if not requested, naming any
  existing framework.
- **CLI and config:** run `npx e2e ...` (or `pnpm exec e2e ...`). Config and
  test files are ESM (`export default { ... } satisfies E2EConfig`); `targets`
  is required.
- **Imports:** import `test`, `describe`, hooks, `expect`, `credentials`, and
  `secrets` from `e2e`; import `test`, `describe`, and hooks from
  `@e2e-dev/web`, `@e2e-dev/mobile`, or `@e2e-dev/desktop` when using their
  engine fixture.
- **Secrets:** never put secrets in test code. Declare them under
  `credentials` or `secrets` and pass `credentials.user(name).password` or
  `secrets.get(name)` only to `fill()` or `agent.act` `params`.
- **Locators and waits:** locators resolve lazily; actions and `expect` wait;
  `count()` and `isVisible()` read immediately; two matches fail with
  `LOCATOR_AMBIGUOUS`. Never sleep; wait for state.
- **Test shape:** one behavior per test, arrange -> act -> assert with every
  check at the end. Bad: add, `expect`, toggle, `expect`. Good: two tests,
  each with checks only at the end; mid-way states use `.waitFor()`.
- **Test isolation:** each test owns its starting state and passes alone by
  `file:line` twice in a row. Clean up shared server data in a `test.extend`
  fixture (`try`/`finally`), never at the end of a test body, and never chain
  tests across shared state or branch on `isVisible()`/`count()` without a
  wait.
- **List mutations:** add two items, act on the second item shown (never the
  first), and check the first is unchanged (topic `writing-tests`, "Act on the
  second item shown").
- **Agent flows and replay:** when `agents.default` (or a selected
  `agents.<name>`) configures a model or executor, default to `agent.act` for
  UI actions (data in `params`, `unique()` for run-unique values) and end with
  a verifying matcher or `agent.assert` so replay caching records eligible
  `act` steps (reads, `expect.poll`, and plain-value `expect` confirm nothing).
  Reserve `screen.*` actions for low-level mechanics (keyboard shortcuts, drag
  offsets, empty submits), `test.setup`, or model-less configs; split
  `agent.act` when a later step needs a known screen state, risks
  `maxSteps`/`maxModelCalls` budgets, or needs a middle step boundary (topic
  `agent`).
- **Reuse existing code:** extend or import existing `tests/`, fixtures,
  helpers, and page objects instead of duplicating setup or locators.
- **MCP sessions:** in a directory without a config, `open_session {engine:
  "@e2e-dev/web", app: {url: "http://localhost:3000"}}` still works (topic
  `mcp`).
- **Runner output:** `.e2e/` is generated output: read it, never edit it.
- **e2e bugs or gaps:** when e2e itself breaks or misleads you, read
  `debugging` ("Feedback") for `npx e2e feedback`.
