# Agent steps

A `docs/<path>.mdx` pointer names an e2e docs page: read
`node_modules/e2e/docs/<path>.mdx` once e2e is installed, else
https://e2e.com/docs/<path>.

`agent` is a fixture like `screen` and the main way a test drives the app.
Each call is one bounded invocation: fresh redacted observation, deadline,
model-call budget, no shared transcript. No agent step, no model calls.

## Contents

- Configure a model
- act: one goal per test
- assert, waitFor, extract: one question
- Write instructions the model can execute
- What the model sees
- Budgets and cost
- The replay cache
- Inspect what the model did
- Make the agent yours
- In CI

## Configure a model

Put an AI SDK model instance (not a string, `INVALID_CONFIG`) under
`agents.default`. Any AI SDK provider with tool calls works; keep `ai@^7`
installed with it. Vercel AI Gateway reads `AI_GATEWAY_API_KEY`:

```ts
import type { E2EConfig } from 'e2e';
import { web } from '@e2e-dev/web';
import { gateway } from 'ai';

export default {
  targets: [{ engine: web(), app: { url: 'http://127.0.0.1:3000' } }],
  agents: { default: { model: gateway('openai/gpt-6-luna-fast') } },
} satisfies E2EConfig;
```

- `model` drives `agent.act`; judgments use `judge` when set, else `model`.
  An entry never inherits `model` or `context` from `default`.
- `context` is what the app calls things, sent to every model call;
  `system` is how the acting agent works. `agentContext` on a test or group
  adds more. Every prompt carries the test's title path, so name a test for
  what it covers, not for the verdict it expects.
- No model for the built-in agent is one run-level `MODEL_UNAVAILABLE`
  (exit 2) when the first test acquires `agent`. Auth failures surface on
  the first model call as `MODEL_PROVIDER_FAILED`.
- `executor` replaces the built-in agent: `decisionExecutor()` from
  `@e2e-dev/decision`, or `claudeCode()` / `codex()` from `@e2e-dev/acp`
  for a coding agent the user is signed in to (no provider key).
- Pick an agent: `--agent <name>` on the CLI, `{ agent: '<name>' }` on a
  test, group, or one `agent.*` call; a list runs each test once per agent.
  Pair an agent with a `session` per persona.

Subscription logins and local models: topic `setup`. Full reference:
docs/models.mdx, docs/agents.mdx, docs/decision-models.mdx,
docs/subscriptions.mdx.

## act: one goal per test

```ts
import { credentials, unique } from 'e2e';

await agent.act('add a todo named "Buy milk"');
await agent.act('invite {email} as an editor', { params: { email: 'ada@example.test' } });
await agent.act('create a project named {name}', { params: { name: unique(`E2E ${Date.now()}`) } });

const member = credentials.user('member');
await agent.act('sign in with the given credentials', {
  params: {
    username: member.username,
    password: member.password, // a Secret: the model sees its name, the runner fills the field
  },
});
```

`act(instruction, options?)` runs a multi-action flow to a verdict and
resolves with `summary`, `modelCalls`, `actions`, and `cache`. A failure
throws an `AgentError` whose `code` says why: `ACTION_FAILED` (the product
failed), `STEP_BUDGET_EXHAUSTED` / `STEP_TIMEOUT` / `CONTEXT_OVERFLOW` (out
of room), `POLICY_DENIED` and the `AUTH_*` / `*_UNAVAILABLE` codes (blocked
from outside), `MODEL_OUTPUT_INVALID` / `MODEL_REFUSED` (the model).
Full reference: docs/reference/errors.mdx.

- `params`: values the instruction names as `{placeholders}`. The runner
  fills a `Secret`. Wrap a run-unique value in `unique()` so the replay
  cache still hits on the next run.
- `timeout` (the config `timeout`), `maxSteps` and `maxModelCalls`
  (default 25 each, may only lower the agent's limits).
- No `schema` (use `extract`) and no `vision`: the model decides when it
  needs pixels.
- Name the target as the screen names it; the agent picks the verb from
  its tools (tap, type, select, check, scroll, drag, upload, navigate,
  screenshot and point tools, `type_secret`). A control that commits
  something is pressed once per commit the step asks for.

Full reference: docs/reference/agent.mdx.

## assert, waitFor, extract: one question

```ts
import { z } from 'zod';

await agent.assert('the dashboard shows a trial badge'); // one look, one judgment

await agent.waitFor('the export finished and a download link appeared', { timeout: 120_000 }); // polls

const data = await agent.extract('every todo title and how many remain', { // structured output
  schema: z.object({ titles: z.array(z.string()), remaining: z.number().int() }),
});
expect(data.titles).toContain('Buy milk');
```

- `assert` does not poll. False is `ASSERTION_FAILED` with the model's
  explanation; too little on screen is `ASSERTION_INCONCLUSIVE`, also a
  failure, so reach the right screen first and ask about what is visible.
- Judgments see the assertion, its params, the agent's context, the test
  title, and the current screen, never prior steps. `assert` and `waitFor`
  take `params` like `act`; the judge sees a `Secret` by name only, so check
  a secret's value with a locator assertion.
- A value shown in several places must agree everywhere. Name the one you
  mean (`'the order summary total is $42.00'`) when only it matters.
- `vision`: `false` (default) the tree, `true` the tree plus a masked
  screenshot, `'only'` the screenshot alone (an overlay, a broken layout, a
  chart).
- `waitFor` judges each time the screen changes, up to `timeout` (30 s)
  then `STEP_TIMEOUT`. It needs a model even under a custom executor, is
  never cached, and spends judgments every run; raise `interval` for a
  screen that keeps changing.
- `extract` takes any Standard Schema (zod). Data the screen does not show
  is `ASSERTION_INCONCLUSIVE`, never `""` or `0`; to accept absence, ask for
  it (`'the phone, or null when none is shown'` with `.nullable()`).
- `explore: true` on `assert` lets it scroll the current screen and combine
  viewports (a list that fits a tablet but scrolls on a phone). Use
  `waitFor` for a condition that changes over time.
- Never sleep for a fixed time to let the app settle:

```ts
// BAD: guesses how long the export takes.
await new Promise((resolve) => setTimeout(resolve, 10_000));

// GOOD: waits for the state, up to the timeout.
await agent.waitFor('the export finished and a download link appeared', { timeout: 60_000 });
```

Full reference: docs/agent-steps.mdx, docs/reference/agent.mdx.

## Write instructions the model can execute

- Give each test one behavior and one goal. An `act` instruction can
  give several steps toward that goal. Name the fields, options, and
  buttons the test depends on. Specify the order when it matters.
- Keep arrange actions focused on the starting state. Wait for that
  state before acting on the behavior under test.
- Start with one call for the act block. Split at a meaningful screen
  transition when the next step needs a known state, when a long flow
  would risk the `maxSteps` or `maxModelCalls` budget, or when a failure
  in the middle needs its own step boundary. Explain why, then wait for
  the intermediate screen state. Each call has its own recording and
  budgets within the test timeout. Verify the complete path together.

```ts
test('places an order with a saved card', async ({ app, agent, screen }) => {
  await app.open('/checkout');

  // The saved card can load after the Payment heading appears.
  await agent.act('Fill the Shipping address with {address}, then choose Continue to payment.', {
    params: { address: '12 Market Street' },
  });
  await screen.getByRole('radio', 'Test card').waitFor();
  await agent.act('Select the saved Test card and choose Place order.');

  await expect(screen.getByText('Order confirmed')).toBeVisible();
});
```

- Put test data in `params` and use placeholders in the instruction.
- Leave routine waiting, scrolling, and retries to the runner.
- End the test with a check of the outcome. A passing locator or engine
  matcher, `agent.assert`, or wait confirms every `act` before it, which
  lets the cache record them; close an arrange block of `act` goals with a
  wait for its state, so a failure later in the test keeps them recorded:

```ts
await agent.act('create a workspace named "Atlas" on the Pro plan');

await expect(screen.getByRole('status')).toHaveText('Created "Atlas" on the Pro plan');
```

The model gets the instruction verbatim plus the params as a separate
block; the check also makes the test model-portable. Off-screen state (a
database row) can land after `act` returns; `expect.poll` the read instead
of sleeping.

## What the model sees

A redacted snapshot of the screen (roles, names, text, states), prior-step
summaries, and your context; never raw HTML, cookies, headers, environment
values, or a `Secret`'s value. Pixels arrive through `vision` on a judgment,
and in `act` through its screenshot and point tools, an opening screenshot
when the screen lists no interactive node, and a screenshot when the browser
engine's tree capture times out (a judgment gets that one only with `vision`
on), with secure fields masked. A frame
from another site (a hosted card field) shows as an empty `iframe` node:
script steps there with `browser.frameLocator`, and judge it with
`vision`. Nothing the model returns runs as code or selectors.

## Budgets and cost

| Call | Model calls | Default timeout |
| --- | ---: | --- |
| `act` | up to `maxModelCalls` (25) | the config `timeout`, 120 s |
| `assert`, `extract` | 2 | 30 s |
| `waitFor` | up to `maxModelCalls` (25) | 30 s |

Slow model calls: raise the step or test `timeout` for `act`, the agent's
`judgmentTimeout` for judgments, `actionTimeout` for slow UI.
`STEP_TIMEOUT` and `STEP_BUDGET_EXHAUSTED` fail the test; smaller goals
help.

## The replay cache

A passing `agent.act` saves its actions once a later check verifies the
outcome; the next run replays them without model calls, and the live agent
takes over from the current screen when the app no longer matches.
`agent.assert`, `agent.waitFor`, and `agent.extract` are never cached.

- On by default (`read-write`), `read-only` in CI, off with `--no-cache`.
  Entries live in `.e2e/cache/`; deleting it only slows the next run.
- Only a later verification records an entry: a locator or engine matcher,
  `locator.waitFor`, `browser.waitForURL`, `agent.assert`, or
  `agent.waitFor`. A plain-value `expect`, `expect.poll`, `agent.extract`,
  another `act`, or the test passing confirms nothing.
- The key holds the test file and title path, the target, the instruction
  and params, the agent, and its context: renaming a test or rewording a
  goal records it again. `step.cache.reason` says why a replay missed.
- A step that changes nothing on screen or in the route records nothing
  and runs live every run.
- While you fix a test, keep the cache on so confirmed goals replay (topic
  `debugging`, "Rerunning a test while you fix it"). Use `--no-cache` to
  rule out a stale replay (topic `debugging`, "Tools") and for one live run
  once the test passes.
- With committed recordings, `--strict-cache` in CI fails a recording that
  no longer replays with `REPLAY_STALE`; re-record with a `read-write` run
  without the flag and with `cache.strict` off, then commit.

Full reference: docs/cache.mdx.

## Inspect what the model did

```bash
npx e2e run tests/checkout.e2e.ts --debug      # step table, transcripts as artifacts
npx e2e run tests/checkout.e2e.ts --ai-trace   # writes .e2e/ai-trace.json
npx unbox-ai runs .e2e/ai-trace.json           # one line per agent step
```

Never read the trace file directly: it is megabytes of resent context.
Replayed steps make no model calls, so use `--no-cache` to trace the whole
flow. Full reference: docs/debugging.mdx.

## Make the agent yours

1. **The goal.** A failed step usually named something the screen does not;
   reword it with on-screen labels.
2. **`context`.** Vocabulary every step needs (plan names, which tab holds
   billing), once on `agents.<name>.context` or per test via `agentContext`.
3. **`system`.** How carefully it verifies, what it never does.
4. **Tools.** A test API the agent may call mid-flow (seed a cart) through
   `tools` with `defineTool(tool({ ... }), { mutates: true })` from
   `e2e/agent`.
5. **The model.** `providerOptions` for reasoning effort, or another model
   for one persona.

A custom `executor` (`StepExecutor` or `createToolLoopExecutor`) keeps the
runner's observations, budgets, and report; `system` or `tools` beside
`executor` is `INVALID_CONFIG`. Full reference: docs/tools.mdx,
docs/executors.mdx.

## In CI

Run the suite, agent steps included, on every pull request, passing the key
the config's model reads (`env: { AI_GATEWAY_API_KEY }` for `gateway()`)
from secrets. Sharing `.e2e/cache/` lets CI replay verified action steps
without model calls; CI defaults: topic `running`.
