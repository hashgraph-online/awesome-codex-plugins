# Setting up e2e

A `docs/<path>.mdx` pointer names an e2e docs page: read
`node_modules/e2e/docs/<path>.mdx` once e2e is installed, else
https://e2e.com/docs/<path>.

## Contents

- Requirements
- Scaffold
- Subscriptions and API keys
- The config
- The app under test
- Environment variables the runner reads
- Mobile targets
- Done when

## Requirements

- Node.js 24.8 or newer, or 22.22.3 or newer on Node.js 22; or Bun 1.4.3 or
  newer (`bunx --bun e2e`), with
  [these limitations](https://e2e.com/docs/reference/cli#bun).
- ES modules: `.ts` config, tests, helpers, and workspace packages exporting
  `.ts` source load as ESM regardless of the nearest `package.json` `type`
  (CommonJS packages need no change); never `require` or `module.exports`.
  Imports follow TypeScript: `./x.js` or `./x` loads `x.ts`, and the nearest
  `tsconfig.json` `paths` and `baseUrl` apply. CommonJS TypeScript goes in
  `.cts`.
- Browser tests: `@e2e-dev/web`, pinning `playwright-core` exactly; do not
  add `playwright` for it. Missing browsers download on first boot; in CI or a
  Linux sandbox run `npx @e2e-dev/web install chromium --with-deps` (pnpm:
  `pnpm exec e2e-web install chromium --with-deps`), since a bare Linux lacks
  the browser's system libraries and `e2e doctor` then fails `browser`.
  Mobile tests: `@e2e-dev/mobile`, pinning `agent-device` exactly.

## Scaffold

Ask before adding e2e to a project that did not request it, naming any
existing test framework. Fresh project:

```bash
npx e2e init       # npm
pnpm dlx e2e init  # pnpm
```

With `e2e` installed, run the installed version: `npx e2e init` or `pnpm exec
e2e init`; `npx e2e init my-app` scaffolds into a new directory, and
`npx e2e init my-app --example with-vite` (or `with-expo`, `with-flutter`,
...) starts from one of the repo's examples.

The wizard picks the engines and a model provider (**Skip for now** for tests
without AI) and offers to install this skill, register the MCP server, and
install dependencies. It needs a terminal: without one, `init` exits with
code 2. From an agent's shell, run `npx e2e init --yes` when its defaults fit
(web engine, Vercel AI Gateway, the skill in `.agents/skills/` with a pointer
line in `AGENTS.md` and `CLAUDE.md`, MCP registration, no dependency install),
then install the dependencies. A flag per question overrides one default
(`--engine web,mobile`, `--gateway`, `--endpoint`, `--skills`, `--mcp`,
`--ci`, `--install`); `npx e2e init --help` lists the values. When the client
already has the e2e plugin, pass `--skills none`, and in Codex and Cursor
`--mcp none` too, since the plugin gives both.

Init adds dependencies and a `test:e2e` script to `package.json`, writes
`e2e.config.ts` and `tests/example.e2e.ts`, updates `.gitignore`, and leaves
existing configs and tests alone. Re-running is safe: beside an existing
config it writes no example test and adds the engine and model packages the
config imports that `package.json` lacks, unless `package.json` declares
another `e2e` than the one running init (then run the project's own
`e2e init` after installing). Re-run after upgrading to refresh the skill
and MCP entries; it keeps the MCP server's environment and client settings.
`init` can restore a missing `SKILL.md` in an existing copy when pnpm links
the skill in another directory.
Codex reads `.codex/config.toml` only in trusted projects; start a new
session after installing dependencies.

Without the wizard (`ai`, Vercel AI SDK v7, only for `agent.*` steps):

```bash
npm install --save-dev e2e @e2e-dev/web ai@^7
```

Full reference: docs/reference/cli.mdx.

## Subscriptions and API keys

`e2e init` writes model config and dependencies for a subscription, an API
key, or a local endpoint. Subscriptions sign in with `npx e2e login <provider>`
(`openai`, `github-copilot`, `opencode-console`, `spacexsi`); `npx e2e models`
lists the ids each login serves. API keys: `AI_GATEWAY_API_KEY` for Vercel AI
Gateway, `OPENROUTER_API_KEY`, `ANTHROPIC_API_KEY` (Claude Max or Team plans
use a Console API key, there is no `e2e login`), each read by its provider
package. Use API keys in CI.

- There is no implicit default model. Without one, the first test that
  takes the built-in agent's `agent` fixture stops the run with one `MODEL_UNAVAILABLE` (exit 2); a
  model-less custom executor fails only `waitFor` and `extract` this way; tests with no `agent.*`
  steps need no model.
- A model GitHub Copilot does not serve to the account (common on Copilot
  Free, which
  serves models only through auto selection) also stops the run with
  `MODEL_UNAVAILABLE` naming it: pick another id or an API provider.

Full reference: docs/subscriptions.mdx, docs/models.mdx.

## The config

`e2e.config.ts` sits at the project root and default-exports an object literal
ending in `satisfies E2EConfig`; unknown keys are `INVALID_CONFIG` at load.

```ts
import type { E2EConfig } from 'e2e';
import { web } from '@e2e-dev/web';
import { gateway } from 'ai';

export default {
  tests: 'tests/**/*.e2e.ts',
  targets: [
    {
      engine: web(),
      app: {
        url: 'http://127.0.0.1:3000',
        command: { executable: 'pnpm', args: ['dev'], log: '.e2e/logs/app.log' },
      },
    },
  ],
  // Model behind every agent.* step.
  agents: {
    default: {
      model: gateway('openai/gpt-6-luna-fast'),
      system: 'You are a thorough QA agent. Verify every outcome on screen.',
    },
  },
  credentials: {
    admin: { username: 'admin@example.test', password: process.env.ADMIN_PASSWORD ?? '' },
  },
} satisfies E2EConfig;
```

- `targets` is required and each UI target names its engine (`web()`,
  `mobile()`, `desktop()`); there is no default engine. A tools-only target
  (agent tools and `request` calls to absolute URLs) may omit `engine` and
  must set `platform`.
- A string `password` or secret is checked at load (6+ code points): set
  `ADMIN_PASSWORD` or `E2E_USER_ADMIN_PASSWORD` first, or defer to fill time
  with `() => process.env.ADMIN_PASSWORD ?? ''`. Other sensitive values go
  under `secrets`.
- Defaults worth knowing: `timeout` 120 s per attempt, `actionTimeout` 30 s,
  `assertionTimeout` 5 s, `retries` 0 (1 in CI), `workers` half the cores (1
  in CI). Files in parallel share the app's server data: give each test
  records of its own (topic `writing-tests`, "Each test owns its starting
  state"), or set `workers: 1` when the app keeps one shared state (one cart,
  one profile) that no test can own.
- `filters` (such as `decisionFilter` from `@e2e-dev/decision`) run only with
  `--changed-since <ref>`, leave out tests a change cannot affect, and score
  the rest (`relevance`) so each target starts the likeliest files first.
  Read files, the environment, or the network inside a filter, never at
  config load: workers load the config too.

Full reference (every key, `reporters`, `cache`, `trace`, `video`,
`output`): docs/reference/config.mdx.

## The app under test

The target declares the app; the engine only drives it (`web({ url })` and
`mobile({ app })` are unknown keys). The target's `app` takes `url` (required
on a `web()` target), `bundleId` or `appPath` (a device target needs one),
`command` and `readyUrl` to start and probe the app, and `launchArguments`,
`permissions`, `environment`, `identity`.

`web()` takes `browser` (`'chromium'` by default, `'firefox'`, `'webkit'`, or
a hosted `BrowserProvider`), `viewport` (default 1280x720), `headers`,
`basicAuth`, `locale`, `timezoneId`, `colorScheme`, `testIdAttribute`, and
more. Two browsers on one app declaration:

```ts
const app = { url: 'http://127.0.0.1:3000' };
export default {
  targets: [
    { name: 'chromium', engine: web(), app },
    { name: 'mobile-webkit', engine: web({ browser: 'webkit', viewport: { width: 390, height: 844 } }), app },
  ],
} satisfies E2EConfig;
```

Full reference: docs/reference/config.mdx ("The app under test"),
docs/reference/web.mdx, and for hosted browsers docs/integrations/index.mdx
(online: https://e2e.com/docs/integrations).

### Let the runner start the app

Prefer `app.command` to a hand-started dev server: self-contained locally
and in CI.

```ts
engine: web(),
app: {
  url: 'http://127.0.0.1:3000',
  command: {
    executable: 'pnpm',
    args: ['dev'],
    env: { PORT: '3000', DATABASE_URL: process.env.DATABASE_URL ?? '' },
    startupTimeout: 120_000,
    log: '.e2e/logs/app.log',
  },
},
```

- The runner spawns `command`, polls `readyUrl` (default `url`) for a 200 to
  499 status within `startupTimeout` (default 60 s), and stops it when the
  run ends. Never ready is `APP_UNREACHABLE`, before any test runs; a command
  that exits after readiness fails the run with `APP_UNREACHABLE` too while a
  target that needs it has unfinished work.
- The child gets only `PATH`, `HOME`, the temp-directory variables (plus
  `SystemRoot` and `COMSPEC` on Windows), and `command.env`. Pass the rest
  through `env`, or name host variables in `inheritEnv` (`['DATABASE_URL',
  'STRIPE_*']`). Model keys and `E2E_USER_*` values are never inherited
  unless an `inheritEnv` name or prefix matches them.
- Output is discarded unless `log` names a file under an ignored directory
  such as `.e2e/logs/`; without it a server dying on boot is invisible.
- A `url` answering before the spawn is `APP_ALREADY_RUNNING`;
  `command.reuseExisting: true` attaches to a running dev server (CI ignores
  it).
- `executable` resolves on `PATH`, never through a shell; name the server
  itself, not a wrapper script.
- `url: 'http://127.0.0.1:0'` (never `localhost:0`) takes a free port; the
  command receives it as `{port}` in `args`, `env`, and `readyUrl`. Tests
  read the URL from `app.baseUrl`.

For an app started elsewhere, point `app.url` at it, literally or via
`process.env.APP_URL ?? 'http://localhost:3000'`; the runner reads no
`APP_URL` and loads no `.env`, so put `process.loadEnvFile('.env')` atop
`e2e.config.ts` (workers re-import it).

Next.js: `e2e init` writes the target (`next dev` locally; `next start`
with a `next build` step in CI only when `build` and `start` scripts exist
on the same port, else `next dev` in CI too). A Next.js 16 dev server never hydrates a page
opened on `127.0.0.1` or `[::1]` unless that host is in `allowedDevOrigins`;
the App Router's empty `role="alert"` route announcer means
`getByRole('alert')` needs a text filter. Full reference:
docs/frameworks/nextjs.mdx.

### Start the app's dependencies as services

Put dependencies the app needs (an email API, an OAuth provider, a database)
in `services`. Each is a `defineService({ async *start({ signal }) { ... } })`
that starts the dependency, yields a plain object of data and functions one
time, and stops it after the `yield`.

- `e2e run` and `e2e explore` start services in key order before the app
  commands and stop them in reverse order afterward. `e2e mcp` starts them
  with the first session on a config file and stops them when the last one
  closes. `openHost` starts them when the host opens and stops them in
  `host.close()`.
- Pass the service's address to the app from an `env` function,
  `env: ({ services }) => ({ EMAIL_URL: services.email.url })`, so the service
  can listen on port 0. Write the config with `defineConfig` so `services` is
  typed there. With `reuseExisting`, an app that's already running doesn't
  get the variables, and a notice is printed, so give its services fixed
  ports.
- Pass `signal` to anything the service starts. Set `startupTimeout` (60 s by
  default) or `shutdownTimeout` (10 s by default) on a slow service.
- Tests read the values through the `services` fixture. Each yielded function
  becomes async and runs in the process that started the services
  (`await services.email.createInbox()`). Yielding a class instance fails
  with `INVALID_SERVICE_VALUE`.
- In `e2e run`, all workers share one instance, and each `openHost` host
  starts its own. Filter for data the test created, such as emails sent to a
  unique inbox.

Full reference: docs/services.mdx (online: https://e2e.com/docs/services).

## Environment variables the runner reads

`E2E_USER_<NAME>_USERNAME` and `E2E_USER_<NAME>_PASSWORD` override
`credentials.<name>`, `E2E_SECRET_<NAME>` overrides `secrets.<name>`
(`<NAME>` uppercased, other characters `_`). Provider keys are read by the
provider packages, not the runner. `CI` switches CI defaults (topic
`running`). Full reference: docs/reference/environment.mdx.

## Mobile targets

`@e2e-dev/mobile` drives iOS simulators, Android emulators, and connected
phones through [agent-device](https://github.com/callstack/agent-device);
it needs Xcode with a simulator runtime or the Android SDK with an emulator.
Run `npx e2e doctor` to check. Name a phone in `device` by the name
`npx agent-device devices` lists, not its UDID or serial. On an iPhone,
device settings (permissions, `clearState`, network, location, appearance,
biometrics, keychain) and the clipboard are simulator-only.

```ts
import type { E2EConfig } from 'e2e';
import { mobile } from '@e2e-dev/mobile';
import { mobileTools } from '@e2e-dev/mobile/tools';
import { gateway } from 'ai';

const iphone = mobile({ platform: 'ios' });

export default {
  targets: [{ engine: iphone, app: { bundleId: 'com.example.app' } }],
  workers: 1,
  agents: {
    default: {
      model: gateway('openai/gpt-6-luna-fast'),
      tools: mobileTools(iphone),
    },
  },
} satisfies E2EConfig;
```

- `app.bundleId` is what `app.open()` launches fresh. `app.appPath` is the
  `.app` or `.apk` under test, but the engine installs nothing: a worker
  fixture with `auto: true` calls `device.installApp()` once per device.
- One worker per device. Without `device`, booted simulators and emulators
  (and connected phones) form the pool. Two sessions on one device fight
  over it: for parallel MCP sessions or bug-bash explorers, declare one
  target per device, each naming its `device`.
- `device` can also be a hosted `DeviceProvider` (`@e2e-dev/eas`,
  `@e2e-dev/browserstack`, `@e2e-dev/testmu`, `@e2e-dev/revyl`,
  `@e2e-dev/limrun`, `@e2e-dev/e2b`). Some install the app from their own
  `app` or `buildId` option (omit `app.appPath`), others install
  `app.appPath`: see each provider's page.
- No `state` capability: `test.setup` and `session` are unavailable; sign in
  per test with `screen` actions or `agent.act` (topic `writing-tests`,
  "Sign-in sessions").
- `test` from `@e2e-dev/mobile` types the `device` fixture (`installApp`,
  `openLink`, `setPermission`, `setNetwork`, `clearKeychain`, and more).
  Portable suites declare `platforms: ['ios', 'android']`; a check for one
  platform takes `{ platforms: ['ios'] }`.
- `selectOption`, `setInputFiles`, `scrollIntoView`, `secondaryTap`, and
  `modifiers` are `UNSUPPORTED_CAPABILITY` on a device. `setNetwork('offline')`
  and `setAirplaneMode(true)` are Android only.
- A node the soft keyboard covers is hidden, so `toBeVisible()` fails and a
  tap fails `ACTION_FAILED` naming the cover: dismiss the keyboard or scroll
  the target clear.

Full reference (Expo dev builds, iOS languages, timing, providers, the raw
driver): docs/mobile.mdx, docs/reference/mobile.mdx,
docs/integrations/index.mdx (online: https://e2e.com/docs/integrations).

## Done when

- `npx e2e run tests/example.e2e.ts` passes against the app.
- `package.json` has a script such as `"test:e2e": "e2e run"`.
- `.gitignore` lists the `.e2e/` outputs (init adds them); drop the
  `.e2e/cache/` line to commit replays.
- CI runs the whole suite, agent steps included, on PRs; see `running`.
