# Writing tests

A `docs/<path>.mdx` pointer names an e2e docs page: read
`node_modules/e2e/docs/<path>.mdx` once e2e is installed, else
https://e2e.com/docs/<path>.

## Contents

- A complete file
- Structure: one describe, arrange-act-assert, one behavior
- Registration
- Fixtures
- Locators
- expect
- Sign-in sessions
- Start near the screen under test
- The browser fixture (browser only)
- Habits

Always read "A complete file" and "Structure" first. Load later API sections
(`Registration`, `Fixtures`, `Locators`, `expect`, `Sign-in sessions`,
`The browser fixture`) only as needed: each keeps the rules that trip
agents up and names the docs page with the full API.

## A complete file

```ts
// tests/todos.e2e.ts
import { test, expect } from 'e2e';

test.describe('todos', { tags: ['todos'] }, () => {
  test.beforeEach(async ({ app }) => {
    await app.open('/todos');
  });

  const labels = { list: 'Todos', remaining: 'Remaining' };
  const title = 'Write the release notes';
  const other = 'Book the venue';
  const addTodo = 'Add a todo named {title}';

  test('adds a todo to the list', async ({ agent, screen }) => {
    await agent.act(addTodo, { params: { title } });

    await expect(screen.getByRole('checkbox', title)).not.toBeChecked();
    await expect(screen.getByRole('list', labels.list).getByRole('listitem')).toHaveCount(1);
    await expect(screen.getByRole('status', labels.remaining)).toHaveText('1 remaining');
  });

  test('marks a todo as done', async ({ agent, screen }) => {
    const todo = screen.getByRole('checkbox', title);
    await agent.act(addTodo, { params: { title: other } });
    await agent.act(addTodo, { params: { title } });
    await todo.waitFor();

    // the second todo shown: this list adds new todos at the end
    await agent.act('Mark {title} as done', { params: { title } });

    await expect(todo).toBeChecked();
    await expect(screen.getByRole('checkbox', other)).not.toBeChecked();
    await expect(screen.getByRole('status', labels.remaining)).toHaveText('1 remaining');
  });

  test('ignores an empty submission', async ({ screen }) => {
    // An exact interaction: the empty submit is the point of the test.
    await screen.getByRole('button', 'Add').tap();

    await expect(screen.getByRole('list', labels.list).getByRole('listitem')).toHaveCount(0);
  });
});
```

The agent drives the flow. A passing `agent.assert` or locator matcher
checks the outcome and confirms the preceding actions for replay. `screen`
actions are for low-level mechanics under test (like `ignores an empty
submission` above), `test.setup` sign-in, or configs with no model; a goal
takes its values in `params`. Files match the config
`tests` glob, default `tests/**/*.e2e.ts`. In a browser every test starts
from a fresh context with no page open, so it calls `app.open()` first; on a
device a test that skips `app.open()` starts where the previous test left
the app.

## Structure: one describe, arrange-act-assert, one behavior

Write every test so a failing title names what broke.

- **One top-level `describe` per feature.** Put every test for the feature and
  its shared hooks inside one `describe('todos')` per file. Nest `describe`
  only to share a hook or option (`session`, `agentContext`, `tags`). Exception:
  `test.setup` must be top-level, outside any `describe`.
- **Arrange, act, assert in order.** Inside `describe`, put `beforeAll`, then
  `beforeEach`, then shared constants, then tests. Inside a test, keep act and
  assert separated by a blank line:
  - **Arrange:** reach the starting state via `session`, fixtures, hooks, or
    one-off setup. End UI setup with a wait (`locator.waitFor()`,
    `agent.waitFor()`) so setup fails there and confirms setup `agent.act` steps
    for the replay cache.
  - **Act:** pursue the test's one goal. Start with one `agent.act` call
    spelling out required fields, choices, buttons, and order; split when a
    later step needs a known screen state, risks `maxSteps`/`maxModelCalls`
    budgets, or needs a middle step boundary (explain why and wait for the
    intermediate screen state). Before leaving a screen or calling
    `agent.assert`, wait for the required state.
  - **Assert:**
    - Put every `expect`, `expect.poll`, and `agent.assert` here, with nothing
      after them (exception: `session.save()` in a setup test).
    - Never assert mid-way: wait on a narrowed locator instead, such as
      `balance.filter({ hasText: /^\$10\.00$/ }).waitFor()` (use anchored
      `hasText` on leaf status/value nodes since it checks subtree text on web
      and individual nodes on core/mobile; use
      `filter({ has: screen.getByText(name) })` for exact row matching),
      `screen.getByRole('switch', 'Lock card', { checked: true }).waitFor()`,
      or `heading.waitFor({ state: 'hidden' })` after an earlier positive wait
      (`hidden` passes immediately on zero matches, including typos, and still
      confirms prior `agent.act` steps).
    - Never move a pre-reload or pre-navigation assertion past a reload or
      navigation (split the earlier phase into its own test instead). Never
      stash one-shot reads (`isVisible()`, `isEnabled()`, `count()`,
      `inputValue()`, `textContent()`, `getAttribute()`, `browser.evaluate()`)
      mid-flow into local variables just to assert them at the end: leave a
      precondition as `.waitFor()` alone with no extra `expect`, split earlier
      phases so retrying matchers run on the live screen, or use
      `expect.poll(...)` for computed CSS/DOM checks. When a computed arrange
      precondition is missing, `throw` directly instead of inventing a
      fallback value.
    - On zero-match timeout, waits report `LOCATOR_NOT_FOUND` and checks
      `ASSERTION_FAILED`; two matches throw `LOCATOR_AMBIGUOUS` on either.
- **One behavior and one goal per test.** Title names one outcome
  (`'marks a todo as done'`, not `'adds and completes a todo'`). Multiple
  assertions checking that one outcome are fine; a second behavior is a second
  test that arranges its own starting state. Never undo an action before
  asserting its effect (returning to the starting value hides a no-op), and
  never leave a screen before checking what the test promised on it.
- **Prove the change on the changed record.** Ask what wrong behavior would
  still pass (no-op, deleted row, wrong row, unsaved reload). Pick an end value
  the start cannot show, write expected values as literals, and scope checks to
  the record's row/card/dialog (never `.first()`). When persistence is part of
  the promise, wait for confirmation, reopen afresh, and compare against inputs
  (plus a fresh API/storage read by id when available). Check only promised
  behavior; the title claims only what assert checks.
- **Act on the second item shown, never the first.** When a test removes,
  edits, renames, completes, or toggles one item of a list (a row, a line,
  a card), its arrange block adds two items, and its act picks the second
  item the list shows. In a list that shows the newest item first, that is
  the item added first. Its assert block then checks that the first item is
  still there, unchanged. An app that always changes the first row passes a
  test that acts on the first row.

  ```ts
  // Bad: deletes the first todo, so an app that always deletes row 1 passes.
  await agent.act(addTodo, { params: { title: other } });
  await agent.act(addTodo, { params: { title } });
  await agent.act('Delete {title}', { params: { title: other } });

  // Good: deletes the second todo (this list adds new todos at the end),
  // then checks the first one is still there and unchanged.
  const todo = screen.getByRole('checkbox', title);
  const otherTodo = screen.getByRole('checkbox', other);
  await agent.act(addTodo, { params: { title: other } });
  await agent.act(addTodo, { params: { title } });
  await todo.waitFor();

  await agent.act('Delete {title}', { params: { title } });

  await expect(todo).toHaveCount(0);
  await expect(otherTodo).toBeVisible();
  await expect(otherTodo).not.toBeChecked();
  ```

  Before running the file, check every list-mutation test acts on the second
  item shown. Read-only lists can target an existing non-first item; tests
  explicitly about position 1 can act on the first item.
- **Refusals and multi-user delivery.** When a refusal promises no persisted
  write, wait for the refusal message (or assert it in its own test), reopen
  after an independent readiness wait, and assert records stayed unchanged;
  put a follow-up retry in its own test.
  For recipient delivery, keep a separate recipient session open and scope
  checks to the run-unique message (and history after reopen if promised).
- **Each test owns its starting state and passes alone.**
  - **Client vs. server state:** browsers isolate contexts per test (restoring
    `session` state without leaking earlier tests' client changes); on Android
    and iOS simulators, reset with `app.clearState()` (plus
    `device.clearKeychain()` on iOS simulator when sign-in uses keychain; on a
    physical iPhone, `app.clearState()` is simulator-only, so reinstall with
    `device.installApp(path, { reinstall: true })`).
  - **Fixture-owned server data:** create shared server records with a
    run-unique `randomUUID()` name in a `test.extend` fixture, capture the
    returned id from a 2xx response before asserting the exact status, and
    delete it in `finally` (`try`/`finally` around creation and `use()` cleans
    up partial setup once the fixture obtains a usable id, as well as failed
    tests). Even when a test deletes its record, keep fixture teardown and
    accept `404` so an earlier failure never leaks. Without a test API, seed
    and delete through the UI in the fixture; never clean up at the end of a
    test body.
  - **No coupling or unwaited branching:** never chain tests across shared
    state, never use `serial: true` to hide coupling, and never branch or skip
    on `isVisible()`/`count()` (they do not wait). Every test must pass when
    run alone by `file:line`, twice in a row.
- **Name and reuse what the tests repeat.** Check existing `tests/`, fixtures,
  helpers, and [page objects](https://e2e.com/docs/page-object-model) first
  and reuse or extend them (including existing screen helpers or page objects
  the project already uses) instead of duplicating setup. Define repeated
  selector inputs, values, or prompts once inside `describe` (or a
  feature-local module as specs grow) and keep single-use ones inline; bind
  repeated locators to local `const`s. Pass variables to prompts in `params`
  (`unique()` for run-unique values so the replay cache hits).
- **Prefer `agent.act` when a model is configured.** When `e2e.config.ts`
  configures a model or custom executor on `agents.default` (or on a named
  `agents.<name>`, selected with `{ agent: '<name>' }` on the test or
  `--agent <name>` on the CLI), default to `agent.act` for user flows (forms,
  buttons, list/CRUD mutations, navigation, auth, with values in `params`),
  and do not avoid `agent.act` on new user flows merely because a `test.setup`
  or login file uses `screen.*`. Pair `agent.act` with verifying checks at the
  end so eligible confirmed `act` steps record and replay without new `act`
  model calls (model-backed judgments such as `agent.assert` still call the
  model on reruns). Reserve `screen.*` actions for low-level mechanics that
  are themselves under test (such as `ignores an empty submission` above, a
  keyboard shortcut, or a drag offset), a `test.setup` sign-in form, or a
  project with no model configured. Use `expect` for exact values, counts, or
  field states; use `agent.assert` alone when the screen shows the full
  semantic or visual outcome, pairing a deterministic `expect` when exact
  phrasing or state must also hold (topic `debugging`, "Flaky tests"). A
  passing locator/engine matcher, `locator.waitFor`, `agent.assert`, or
  `agent.waitFor` confirms preceding `agent.act` steps for the replay cache
  (`expect.poll` and plain-value `expect` confirm nothing).

## Registration

```ts
test('title', async ({ app, screen }) => {});
test('title', { tags: ['smoke'], retries: 2, timeout: 60_000 }, async ({ app }) => {});
describe('group', { tags: ['billing'] }, () => { /* tests and hooks */ });
beforeEach(async ({ app }) => {});     // per attempt, with test fixtures
afterEach(async ({ screen }) => {});   // runs after failures too
beforeAll(async ({ platform }) => {}); // worker fixtures only
test.each([{ user: 'Ada' }, { user: 'Grace' }])('signs in as $user', async ({ user }, { app }) => {});
test.setup('sign in', { sessions: ['admin'] }, async ({ app, screen, session }) => {}); // see Sign-in sessions
```

- Import `test`, `describe`, and the hooks from `e2e`, or from
  `@e2e-dev/web`, `@e2e-dev/mobile`, or `@e2e-dev/desktop` to type their
  fixture. A `test.extend()` chain registers hooks that see its fixtures
  through `test.beforeEach`.
- Everything registers at import, so a `describe` body is synchronous
  (`async` is a `COLLECTION_ERROR`).
- `test.only` and `describe.only` are for local runs: CI fails with
  `ONLY_IN_CI`.
- `beforeAll` and `afterAll` get worker fixtures only. On web, `browser`,
  `app`, and `screen` are test fixtures, so UI setup goes in `beforeEach`;
  on mobile, `device`, `app`, and `screen` are worker fixtures and keep
  their state between tests. Naming a test fixture in a suite hook is a
  `COLLECTION_ERROR`.
- `test.skip`, `test.fixme`, `test.fail`, `test.slow`, `test.setTimeout`, `test.step`,
  `test.for`, `serial` and `parallel` groups, and every test option:
  Full reference: docs/reference/test.mdx.

## Fixtures

Find the module that exports the project's fixture-aware `test`. Choose
the spec's final path before writing the import, then resolve the import
from the spec's directory. Run that spec after adding or moving it and
confirm the runner collects and executes the intended test.

- **Destructure the first parameter.** A test body, a hook, and a fixture
  function name what they use as `async ({ app, screen }) => {}` (a
  `test.each` or `test.for` body takes its row first and the fixtures in
  the parameter after it); `async (fixtures) => {}`, `async (_, use)`, and
  a rest property are `COLLECTION_ERROR`. A fixture that needs nothing takes `({}, use)`.
- **Fixtures run on demand.** A test sets up the fixtures it, its hooks,
  and those fixtures name. One that exists for its side effect takes
  `[fn, { auto: true }]`. Naming a fixture no target provides fails at
  collection.
- **Guard teardown.** `test.extend` fixtures set up before `beforeEach` and
  still run their teardown when `beforeEach` calls `test.skip(...)`. Guard
  teardown with a `created` or `mutated` flag (or clean up only what this
  attempt wrote) so skipped or failed-before-mutation attempts never touch
  shared state.
- **Route by tag, not by sniffing.** To split tests across same-platform
  targets (desktop and mobile viewports), tag tests (`{ tags: [...] }`) and
  run each target with `--target <name> --tag <tag>` rather than reading
  `window.innerWidth` or `timeZone` in `beforeEach`, which boots every test
  on every target and turns a misconfigured target into a green skip.
- **Extend a built-in.** A fixture named like an existing one extends it
  (`app: async ({ app }, use) => { await app.open('/x'); await use(app); }`).
- **Worker fixtures** (`[fn, { scope: 'worker' }]`, second type argument of
  `extend`) are set up once per worker and target. Declare them in a module
  the test files import, never in a test file, which reloads after a
  failure.
- **Typing across targets:** `as const satisfies E2EConfig` on the config,
  then `base.extend<{}, {}, typeof config>()`. Passing `typeof config` also
  types the `services` fixture.

Built-in fixtures: `app` and `screen` always; `agent` with a configured
model (else `MODEL_UNAVAILABLE`, topic `agent`); `request` for HTTP calls;
`platform` (`web`, `ios`, `android`, or an engine's label); `services`, the
values the config's services yield (topic `setup`); `browser` from
`@e2e-dev/web`, `device` from `@e2e-dev/mobile`, `desktop` from
`@e2e-dev/desktop`; `session` only in `test.setup`. `app` opens the app
(`open(path?)`, `back()`, `restart()`, `clearState()`), takes screenshots,
and records video. Full reference: docs/fixtures.mdx, docs/reference/app.mdx,
docs/reference/request.mdx.

## Locators

`screen.getBy*` builds a lazy query, resolved only by an action, read, or
assertion. Every query also exists on a locator, scoped to its subtree.

For a collection check, start at the owning list or table and query only
its items or rows. When the requirement names the whole collection, check
every row in that container, including duplicates. If order can change,
sort copies before comparing the complete observed and expected lists.

- **Queries, in order of preference:** `getByRole(role, name?, { checked?,
  disabled?, expanded?, level?, ... })` first, then `getByLabel`,
  `getByPlaceholder`, `getByText`, `getByDisplayValue`, and `getByTestId`
  last. The second argument to `getByRole` is the accessible name. For
  visible text in an unlabelled list item or status, use
  `getByRole('listitem').filter({ hasText: message })`.
- **Text matches exactly** after whitespace normalization (whole string,
  case-sensitive) for a role name, label, placeholder, and `getByText`:
  `'Save'` misses `Save changes`, unlike Playwright. `exact: false` is a
  case-insensitive substring; a `RegExp` matches as written. A missed query
  makes a negated assertion pass, so check it positively.
- **Exactly one match** per action, read, or assertion. Two fail at once
  with `LOCATOR_AMBIGUOUS`; at zero, actions and reads end in
  `LOCATOR_NOT_FOUND` and assertions in `ASSERTION_FAILED`. Any number is
  fine for `toHaveCount`, list-form `toHaveText` and `toContainText`,
  `count()`, `all()`, and `allTextContents()`. At zero, `toBeHidden()` and
  negated `toBeVisible`, `toBeAttached`, and `toBeInViewport` pass,
  `isVisible()` reads `false`, and `isHidden()` reads `true`.
- **Narrow** with `filter({ hasText })` (a case-insensitive substring),
  `filter({ has: locator })`, `filter({ hasNot })`, `filter({ hasNotText })`,
  `{ visible: true }` on the query itself
  (`getByText('Save', { visible: true })`), scoping under another locator,
  or `nth(i)` with a comment. `a.or(b)` is still strict.
- **Actions** wait for one actionable node (`actionTimeout`, 30 s): `tap()`,
  `fill()`, `press()`, `check()`, `selectOption()`, `hover()`, `dragTo()`,
  `setInputFiles()`, and more. `fill` sends no key events; when the app
  reacts to keystrokes (autocomplete, masked input) use
  `pressSequentially`. Coordinates (`screen.tapAt`) are a last resort.
- **Reads** (`textContent()`, `inputValue()`, `isChecked()`) wait for one
  match, then read once with no retry; `isVisible()` and `count()` answer
  at once. For a value that has to settle use `expect`, not a read.
  `screen.tree()` and `screen.debug()` show the screen as the agent reads
  it.

Every query, role, option, action, and read: Full reference:
docs/reference/screen.mdx.

## expect

`expect(locator)` polls up to `assertionTimeout` (5 s) or `{ timeout }`;
`.not` passes once the negation has held for 1 s. `expect(value)` is
synchronous. `toHaveText` compares the whole normalized text,
`toContainText` a substring or RegExp. List forms:
`toHaveText(['Alpha', 'Beta'])` needs exactly those matches in order;
`toContainText(['Alpha', 'Beta'])` needs each entry in a distinct match, in
order, extra matches allowed.

```ts
await expect(screen.getByRole('dialog')).not.toBeVisible({ timeout: 10_000 });
await expect(browser).toHaveURL('/dashboard');   // relative to the base URL, or a RegExp
expect(order).toMatchObject({ id: expect.any(Number), lines: [{ sku: 'a' }] });
expect(response).toBeOK();                                  // status 200-299
const users = expect(await response.json()).toMatchSchema(z.array(User)); // any Standard Schema; typed output
```

- `expect.poll(read)` re-reads a computed value until a value matcher
  passes. `expect(fn).toPass()` retries a block of assertions that must
  pass together. `expect.soft(x)` keeps a failure and lets the body run on.
- Screenshots: `await expect(screen).toHaveScreenshot('home.png')`. The
  first run writes the file and fails: look at it, commit it, rerun.
  Files are per target and OS, so write CI's from a CI job with `-u`
  (docs/visual-testing.mdx).

Every matcher and option: Full reference: docs/reference/expect.mdx.

## Sign-in sessions

Save sign-in state under a name in a setup test, and declare it with
`session`. Selecting a dependent test alone still runs its setup.

For a test of two users interacting, use distinct accounts in separate
sessions. Restore the primary user's named session through `session`.
For the second user, import `launch` from `@e2e-dev/core` and `web` from
`@e2e-dev/web/engine`, call `launch(web(), options)` from the test with a
fresh engine, then `host.newSession()`. `launch(web(), options)` starts a
local default browser rather than reusing target provider options. Sign in
with that user's test credentials and check the outcome on the screen of
the user who should see it. See the [chat example](https://e2e.com/docs/core#open-a-host-inside-a-test)
for sign-in and cleanup.

```ts
// tests/auth.setup.e2e.ts
import { test } from '@e2e-dev/web';
import { expect, credentials } from 'e2e';

test.setup('authenticate as admin', { sessions: ['admin'] }, async ({ app, screen, session, browser }) => {
  const admin = credentials.user('admin');
  await app.open('/login');
  await screen.getByLabel('Email').fill(admin.username);
  await screen.getByLabel('Password').fill(admin.password);
  await screen.getByRole('button', 'Sign in').tap();
  await expect(browser).toHaveURL('/dashboard'); // prove the sign-in worked before saving
  await session.save('admin');
});
```

```ts
// tests/dashboard.e2e.ts
import { describe, test, expect } from 'e2e';

describe('dashboard', { session: 'admin' }, () => {
  test('opens directly when signed in', async ({ app, screen }) => {
    await app.open('/dashboard');

    await expect(screen.getByRole('heading', 'Dashboard')).toBeVisible();
  });
});
```

- Setup tests are top-level, outside any `describe`; exactly one setup
  saves a given name, and its body saves every name it declares
  (`SESSION_CONTRACT` otherwise).
- A session holds cookies, local storage, and IndexedDB for one run; server
  state is not part of it.
- Credentials live in the config, values in the environment:

```ts
credentials: {
  admin: { username: 'admin@example.test', password: process.env.ADMIN_PASSWORD ?? '' },
},
```

- A static password or secret needs 6 or more characters (code points), else
  `INVALID_CONFIG` at config load. `E2E_USER_<NAME>_PASSWORD` and
  `E2E_SECRET_<NAME>` override a value per run.
- `credentials.user('admin').password` and `secrets.get('stripe-key')` are
  handles with no plaintext: pass them only to `fill()` or `agent.act`
  `params`. A registered value passed as a plain string is redacted to
  `<secret:name>` everywhere, so the agent cannot type it: pass the handle.
- Screenshots, the model's included, mask secure fields only. A secret in a
  plain input, or a value the app shows elsewhere, is in the image: use
  test credentials.

Full reference: docs/authentication.mdx.

## Start near the screen under test

Begin each test as close to its screen as the app allows:

- Declare `session` for auth on web (devices have no named sessions; sign in per test), open routes directly (`app.open('/projects/42/settings')`; on devices use `app.linkBase` or `device.openLink(...)`), and seed data via the app's API in a `test.extend` fixture (`browser.cookies(url)` returns only the cookies the browser sends to that URL; check create and delete statuses).

```ts
import { randomUUID } from 'node:crypto';
import { describe, test } from '@e2e-dev/web';
import { expect } from 'e2e';
import { z } from 'zod';

const projectTest = test.extend<{ project: { id: string } }>({
  project: async ({ app, browser, request }, use) => {
    const cookies = await browser.cookies(`${app.baseUrl}/api/projects`);
    if (cookies.length === 0) throw new Error('not signed in: the app has no cookies');
    const headers = { cookie: cookies.map((c) => `${c.name}=${c.value}`).join('; ') };
    let projectId: string | undefined;
    try {
      const created = await request.post(`${app.baseUrl}/api/projects`, { json: { name: `Project ${randomUUID()}` }, headers });
      const parsed = z.object({ id: z.string() }).safeParse(await created.json().catch(() => undefined));
      if (parsed.success && created.status >= 200 && created.status < 300) projectId = parsed.data.id;
      expect(created.status).toBe(201);
      if (!parsed.success) throw parsed.error;
      await use(parsed.data);
    } finally {
      if (projectId !== undefined) {
        const deleted = await request.delete(`${app.baseUrl}/api/projects/${projectId}`, { headers });
        expect([200, 204, 404]).toContain(deleted.status);
      }
    }
  },
});

describe('project settings', { session: 'admin' }, () => {
  projectTest('renames a project', async ({ agent, app, screen, project }) => {
    await app.open(`/projects/${project.id}/settings`); // straight to the screen under test

    await agent.act('Rename the project to {name} and save', { params: { name: 'Atlas' } });
    await screen.getByRole('status').filter({ hasText: /^Saved$/ }).waitFor();
    await app.open(`/projects/${project.id}/settings`); // reopened: the promise is that it is saved

    await expect(screen.getByLabel('Name')).toHaveValue('Atlas');
  });
});
```

Grow multi-screen tests one screen at a time locally with `--retries 0` (outside `CI` so the cache records), keeping titles and passing goal wording stable so confirmed `agent.act` steps replay while you finish the rest. Pass run-unique values to goal `params` via `unique(value)` (topic `agent`).

## The browser fixture (browser only)

Prefer `app` and `screen`; `browser` is for what only a browser has, and a
portable suite declares `platforms: ['web']`. Page methods act on the one
active tab. A tab the app opens (`target="_blank"`) opens in the
background: `waitForPopup(() => trigger)` makes it active and returns it.

- **Navigation:** `goto(path)`, `reload()`, `back()`, `url()`, `title()`,
  `waitForURL(glob | RegExp)`. `toHaveURL` compares a string exactly.
- **Network:** `route(pattern, handler)` mocks or alters requests (the
  handler calls exactly one of `fulfill`, `continue`, `fallback`, `abort`).
  `waitForResponse` and `waitForRequest` take a pattern or a predicate:
  start them before the triggering action, usually in `Promise.all`.
  `setNetwork('offline')` cuts the network until `setNetwork('online')`
  restores it or the test ends.
- **Page:** `evaluate(fn, arg?)` runs in the page (JSON in and out, no
  closures); `addInitScript` and `clock.install()` go before `app.open`;
  `frameLocator(css)` scopes a `Screen` to an iframe.
- **State:** `cookies(url?)`, `setCookies`, `clearCookies`, `setViewport`,
  `emulateMedia({ colorScheme, reducedMotion })`.
- **Dialogs and downloads:** register `onDialog('accept' | 'dismiss' |
  handler)` before the tap that opens the dialog (an unanswered dialog
  fails the next step with `INVALID_STATE`); `waitForDownload(() =>
  trigger)` returns `{ path, absolutePath, suggestedFilename }`: read the
  saved file through `absolutePath`.
- **Identity:** `name` (`'chromium'`, `'firefox'`, or `'webkit'`; always
  `'chromium'` over CDP) and `version` are properties. Skip on a browser in
  the body: `test.skip(browser.name === 'firefox', 'reason')`.
- `locator(css)` and `keyboard`/`mouse` are last resorts: prefer a
  `screen` locator.

Patterns use Playwright's glob grammar (`*` within one path segment, `**`
across `/`); a relative one resolves against the base URL. Full reference:
docs/reference/web.mdx, docs/browser.mdx.

## Habits

- Prefer user-visible names (roles, labels, text) over `browser.locator` or `getByTestId` (last resort).
- APIs live in the same suite: `request.get('/api/users')` (relative to `app.baseUrl`; `request` sends no browser cookies, so serialize `browser.cookies(url)` into `headers.cookie` as `name=value` pairs joined by `; `, as in the fixture above) plus value matchers on `response.status` and `await response.json()`.
- No sleeps or polling loops: wait for state via locators, `expect` `{ timeout }`, or `agent.waitFor(...)`.
- `await` every step, `expect.poll`, and `toPass`, else `STEP_NOT_AWAITED`.
- Assert required literal fragments with `toContain`, and semantic outcomes (where negation or phrasing can flip meaning) with `agent.assert`.
