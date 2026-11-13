# e2e

[e2e](https://e2e.com) is an open source end-to-end testing framework
for web and mobile apps. A test mixes agent goals (`agent.act`) with exact
locator steps and assertions, and runs in a browser or on an iOS simulator,
Android emulator, or phone.

## Skills

- **e2e**: set up e2e in a project, write and fix tests, run them, debug a
  failed run, drive the running app over the e2e MCP server, explore an app
  toward a goal, and bug bash a branch with each bug proven by a repro test.
- **create-verification-skill**: generate a project-local `verify-<app>`
  skill and feature map on top of e2e. Invoke it with
  `/e2e:create-verification-skill` in Claude Code or
  `$e2e:create-verification-skill` in Codex. It loads only when invoked.
- **migrate-to-e2e**: port a Playwright, Cypress, Selenium, Appium, Detox, Maestro,
  or TesterArmy suite to e2e one slice at a time, with the old suite running beside the
  new one and a `MIGRATION.md` file the next session resumes from.

## Install

The [e2e-inc/e2e](https://github.com/e2e-inc/e2e) repository is a
marketplace for Claude Code, Codex, and Cursor. All three marketplace files
point to `plugins/e2e`, and installation copies this directory into the
client's cache. Grok Build reads the Claude Code files.

Claude Code:

```bash
claude plugin marketplace add e2e-inc/e2e
claude plugin install e2e@e2e
```

Codex:

```bash
codex plugin marketplace add e2e-inc/e2e
codex plugin add e2e@e2e
```

Cursor loads plugins from `~/.cursor/plugins/local/`. Copy this directory
there, then run **Developer: Reload Window**:

```bash
repo=$(mktemp -d)
git clone --depth 1 https://github.com/e2e-inc/e2e "$repo"
mkdir -p ~/.cursor/plugins/local
rm -rf ~/.cursor/plugins/local/e2e
cp -R "$repo/plugins/e2e" ~/.cursor/plugins/local/
```

On Teams and Enterprise, local plugins need the admin setting Allow Local
Plugin Imports, or an admin imports `e2e-inc/e2e` under Team Marketplaces
in the Cursor dashboard.

Start a new session after installing. The plugin's version follows e2e
releases. Update it with `claude plugin marketplace update e2e` followed by
`claude plugin update e2e@e2e`, or in Codex with
`codex plugin marketplace upgrade e2e`, then start a new session. In
Cursor, run the commands above again.

To try local changes, run the same commands from the monorepo root with
`./` in place of `e2e-inc/e2e`. Claude Code reads a local marketplace
in place, so edits show at the next session start or `/reload-plugins`. For
a one-session preview, run `claude --plugin-dir ./plugins/e2e` or
`agent --plugin-dir ./plugins/e2e`.

The plugin is not listed in any client's public directory.

## Requirements

Node.js 24.8 or newer, or 22.22.3 or newer on Node.js 22. In a project that
does not use e2e yet, the skill asks before setting it up. Agent steps need a
model: an AI SDK provider key, or a ChatGPT subscription through
`npx e2e login openai`.

## MCP server

The plugin registers the e2e MCP server from `.mcp.json` as
`npx -y e2e@<version> mcp`, pinned to the e2e release the plugin version
matches. Claude Code and Codex start it in the session's working directory,
where the server finds the project's config; start the session from the
project directory after installing dependencies. `npx` runs the project's
installed `e2e` when its version matches the pin, and downloads the pinned
release otherwise.
Claude Code shows the plugin's server as `plugin:e2e:e2e`. In a directory with no e2e config, the agent can still
open a session by naming the engine package:
`open_session {engine: "@e2e-dev/web", app: {url: "http://localhost:3000"}}`.

Writing and running tests through the CLI does not require an MCP connection.

## Data

- The e2e CLI sends anonymous usage telemetry (commands, engines, versions,
  failure codes; never test content, app content, or credentials) to a
  PostHog project run by the e2e maintainers. Turn it off with
  `E2E_TELEMETRY_DISABLED=1`, `DO_NOT_TRACK=1`, or `npx e2e telemetry disable`.
  See [Telemetry](https://e2e.com/docs/telemetry).
- `npx e2e feedback` sends a report to the same project. The skill shows the
  report first and sends it only when you agree.
- Agent steps send the redacted screen to the model provider you configure.
  See [Security](https://e2e.com/docs/reference/security) for what
  is redacted.

## Maintain the package

Edit skill Markdown in the monorepo's `skills/` directory, then run
`pnpm plugins:sync`. Commit the generated copies with the source changes.
`pnpm plugins:check`, also part of `pnpm check` and CI, catches drift.

The Codex manifest owns the plugin's metadata. The sync command generates
the Claude and Cursor manifests from it and copies the root license. It also generates
`.mcp.json`, pinned to the runner version. Skill UI metadata in
`skills/*/agents/openai.yaml` and the plugin's assets are maintained here.
Keep every referenced file inside this plugin directory so cached installs
work without the rest of the monorepo. The repo's development `.mcp.json`
is outside this package.

The initial Codex manifest, icons, and skill UI metadata came from
[e2e-inc/plugins at 9954005](https://github.com/e2e-inc/plugins/tree/9954005c9688bb1928bdaad20cb8098160406931/plugins/e2e).
The shared skill content follows this monorepo's current sources.
Docs: <https://e2e.com/docs>.
