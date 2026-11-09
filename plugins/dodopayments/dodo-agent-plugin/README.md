# Dodo Payments Agent Plugin

[![License](https://img.shields.io/github/license/dodopayments/dodo-agent-plugin.svg?style=flat-square)](./LICENSE)
[![Version](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2Fdodopayments%2Fdodo-agent-plugin%2Fmain%2Fplugin.json&query=%24.version&label=version&color=blue&style=flat-square)](./CHANGELOG.md)
[![npm](https://img.shields.io/npm/v/@dodopayments/opencode-plugin.svg?style=flat-square)](https://www.npmjs.com/package/@dodopayments/opencode-plugin)
[![Discord](https://img.shields.io/discord/1305511580854779984?label=discord&style=flat-square)](https://discord.gg/bYqAp4ayYh)

The official Dodo Payments plugin for AI coding agents. Installs the Dodo Payments integration skill and MCP server across **Claude Code**, **Codex CLI**, **Cursor**, **VS Code / GitHub Copilot**, **Grok Build**, **Meta Muse Code**, **Gemini CLI**, **Antigravity**, **Junie**, **OpenCode**, and more, from a single source of truth.

This plugin conforms to the [Agent Plugins 1.0.0](https://agent-plugins.org/specification) specification: a root [`plugin.json`](./plugin.json), skills as immediate children of [`skills/`](./skills), and MCP servers in [`mcp.json`](./mcp.json). Clients with native Agent Plugins support load it directly; the provider-specific manifests in this repo are generated compatibility shims for clients that do not.

## What you get

- **Dodo Payments MCP server** (`dodopayments`) - Documentation search plus live API access (payments, subscriptions, customers, products, refunds, licenses, usage). Authenticates via browser OAuth, no local credentials required.
- **Agent skill** - One `dodo-payments` skill (listed [below](#included-skill)), written as a `SKILL.md` index with reference files your agent loads on demand when a task calls for them.

## Install

| Client | Skills | MCP | How |
|---|---|---|---|
| Claude Code | ✅ | ✅ | [Marketplace](#claude-code) |
| Codex CLI / ChatGPT | ✅ | ✅ | [Marketplace](#codex-cli) |
| Cursor (and Grok Bot) | ✅ | ✅ | [Clone](#cursor) |
| VS Code / GitHub Copilot | ✅ | ✅ | [Plugins view](#vs-code--github-copilot) · [Copilot CLI](./docs/clients/more-clients.md) |
| Grok Build | ✅ | ✅ | [`grok plugin install`](./docs/clients/grok.md) |
| grok.com, xAI API | — | ✅ | [Connector / API tool](./docs/clients/grok.md) |
| Meta Muse Code | ✅ | ✅ | [`muse plugins install`](./docs/clients/muse.md) |
| Gemini CLI | ✅ | ✅ | [Extension](#gemini-cli) |
| Google Antigravity | ✅ | ✅ | [`agy plugin install`](./docs/clients/antigravity-and-junie.md#antigravity) |
| JetBrains Junie | ✅ | ✅ | [Extension](./docs/clients/antigravity-and-junie.md#junie) |
| Kiro | ✅ | ✅ | [Power](#kiro) |
| OpenCode | ✅ | ✅ | [npm](#opencode) |
| Qwen Code, Devin, Goose, Factory Droid, Augment, OpenHands, OpenClaw, Hermes | ✅ | ✅ | [More clients](./docs/clients/more-clients.md) |
| Cline, Kilo, Zed, Warp, Amp, Continue, Kimi, … | ✅ | ✅ | [`npx skills` + `npx add-mcp`](./docs/clients/more-clients.md#skills-and-mcp-separately) |
| Claude.ai, ChatGPT, Perplexity, Mistral | — | ✅ | [Custom connector](./docs/clients/more-clients.md#mcp-only-assistants) |

### Claude Code

```bash
claude plugins marketplace add dodopayments/dodo-agent-plugin
claude plugins install dodopayments@dodopayments
```

The MCP server signs in with OAuth, so there is no API key to paste. Your client starts the sign-in when the server is added or connected (run `/mcp` if it doesn't), and a Dodo Payments consent page opens in your browser: pick the business, mode and permissions. See [Sign-in and access](#sign-in-and-access).

### Codex CLI

Register the marketplace, then install the plugin:

```bash
codex plugin marketplace add dodopayments/dodo-agent-plugin
codex plugin add dodopayments@dodopayments
```

Verify:

```bash
codex plugin list     # dodopayments  installed, enabled
codex mcp list        # dodopayments
codex mcp login dodopayments    # browser OAuth
```

You can also install from inside the TUI: run `codex`, type `/plugins`, select the **Dodo Payments** marketplace and the **dodopayments** plugin, then choose **Install plugin**.

If you added the marketplace previously and the plugin doesn't appear, refresh it:

```bash
codex plugin marketplace upgrade dodopayments
```

### Cursor

Manual install:

```bash
git clone https://github.com/dodopayments/dodo-agent-plugin.git ~/.cursor/plugins/local/dodo-agent-plugin
```

Restart Cursor. The plugin loads skills from `skills/` and MCP servers from `.mcp.json`, as declared in `.cursor-plugin/plugin.json`.

> Cursor 3.14.27 also recognises Agent Plugins 1.0.0 directly: its agent host carries both spec schema URLs and the spec's own `name` regex, and accepts either `.cursor-plugin/marketplace.json` or `.claude-plugin/marketplace.json` as a marketplace source. The generated `.cursor-plugin/plugin.json` is kept as belt-and-braces for older builds.

> Prior to v0.5.0 this clone produced a plugin with **no working skills**: `skills/` contained symlinks into a git submodule that a plain `git clone` does not fetch. Skills are now vendored as real files, so the command above works as documented. If you installed an earlier version, re-clone.

### Kiro

Kiro reads the Agent Plugins manifest natively and loads this as a Power:

```bash
git clone https://github.com/dodopayments/dodo-agent-plugin.git
```

Point Kiro at the cloned folder. Skills load from `skills/`, MCP servers from `mcp.json`, and Kiro-specific presentation comes from the `dev.kiro` extension namespace in `plugin.json`.

### Gemini CLI

```bash
gemini extensions install https://github.com/dodopayments/dodo-agent-plugin
```

`gemini-extension.json` at the repo root is the manifest, and Gemini auto-discovers the `skills/` directory next to it. Verified on Gemini CLI 0.63.0: `gemini skills list` shows the skill and `gemini mcp list` shows the server.

### VS Code / GitHub Copilot

```bash
git clone https://github.com/dodopayments/dodo-agent-plugin.git
```

Then open the Chat view, go to **Plugins**, and add the cloned folder. Skills load from `skills/`, and the MCP server loads from `.mcp.json`.

> VS Code 1.125.1 does not key off the Agent Plugins `$schema` - the string appears nowhere in its bundle. Its loader picks a manifest by probing, in order, `.plugin/plugin.json`, then `.claude-plugin/plugin.json`, then a root `plugin.json`, and defaults MCP to `.mcp.json` rather than `mcp.json`. Because this repo ships a generated `.claude-plugin/plugin.json`, VS Code loads it through that branch. Everything works, the skill and the MCP server, via the compatibility manifests rather than the spec ones.

### OpenCode

OpenCode distributes via npm. Add the plugin to your `opencode.json`:

```jsonc
{
    "$schema": "https://opencode.ai/config.json",
    "plugin": ["@dodopayments/opencode-plugin"]
}
```

Restart OpenCode. The MCP server (`dodopayments`) is registered automatically via the plugin's `config` hook as a native remote server. No manual `mcp` block required. Run `opencode mcp auth dodopayments` to open the Dodo Payments consent page.

**The skill needs the package installed locally plus one extra line.** OpenCode does not scan installed packages for skills, so point it at the package's `skills/` directory yourself. `skills.paths` entries resolve against the project directory, so the package must be present in the project's `node_modules` - OpenCode's own plugin cache is not the same location:

```bash
npm install --save-dev @dodopayments/opencode-plugin
```

```jsonc
{
    "$schema": "https://opencode.ai/config.json",
    "plugin": ["@dodopayments/opencode-plugin"],
    "skills": {
        "paths": ["node_modules/@dodopayments/opencode-plugin/skills"]
    }
}
```

An absolute path works too, and avoids the local-install requirement.

Verify with `opencode run "List every skill available to you by name."` - you should see `dodo-payments` (see [Included Skill](#included-skill)). A skills path that does not exist is ignored silently, so check rather than assume.

> Versions before 0.5.0 documented the skills as auto-discovered. They were not: nothing in OpenCode scans an installed package, so OpenCode users had the MCP servers but no skills. Setting `config.skills` from the plugin's `config` hook does not fix this either - the skill index is built before `config` hooks run, so it never registers anything.

## Included Skill

One skill, `dodo-payments`. Its `SKILL.md` is a short index; the details live in reference files that your agent loads only when the task needs them.

| Reference | Covers |
|-----------|--------|
| `checkout` | Checkout Sessions, payment links, and overlay checkout |
| `mobile-checkout` | In-app checkout for React Native, Flutter, iOS, and Android |
| `subscriptions` | Subscription lifecycle, trials, plan changes, proration, on-demand charges |
| `webhooks` | Receiving and verifying webhooks via the Standard Webhooks spec |
| `usage-billing` | Meters, event ingestion, aggregation, and per-unit pricing |
| `credits` | Credit entitlements, balances, ledger, rollover, overage, meter-based deduction |
| `license-keys` | License key activation, validation, and instance management |
| `products` | Products, pricing, add-ons, collections, images, digital delivery |
| `discounts` | Discount codes, eligibility, stacking, subscription-cycle limits |
| `localized-pricing` | Localized pricing, adaptive currency, and purchasing power parity |
| `customers` | Customers, self-service portal, payment methods, wallets |
| `refunds-disputes` | Refunds, disputes and chargebacks, access reconciliation |
| `framework-adapters` | Official `@dodopayments/*` handlers for Next.js, Express, Hono, Astro, Remix, SvelteKit, Nuxt, Fastify, TanStack, Bun, Convex |
| `better-auth` | The `@dodopayments/better-auth` plugin for customer sync, checkout, portal |
| `billing-sdk` | BillingSDK React components for pricing tables and billing UI |
| `testing-go-live` | Test mode, test payment methods, webhook testing, production launch checklist |
| `mcp` | Using the MCP server, test-mode safety rules, auth, troubleshooting |

Skill source: [`dodopayments/skills`](https://github.com/dodopayments/skills) (`dodo-payments/dodo-payments`), vendored into `skills/` as real files. Provenance (upstream commit and applied transforms) is recorded in [`.skills-source.json`](./.skills-source.json).

## Included MCP Server

| Server | Purpose | Auth |
|--------|---------|------|
| `dodopayments` | Documentation search and live API access | OAuth (browser) |

Tools:

| Tool | What it does |
|------|--------------|
| `search_docs` | Searches the guides |
| `read_docs_page` | Returns a docs page as markdown |
| `search` | Finds SDK and API methods |
| `execute` | Runs TypeScript SDK code against the signed-in account, in a sandbox |
| `feedback` | Sends a note to the Dodo team, who triage each one; emails, IDs and keys are removed first |

The server speaks Streamable HTTP over HTTPS, and every manifest dials it natively - no `npx mcp-remote` bridge and no Node dependency. The canonical `mcp.json` uses the spec's `type: "streamable-http"`; the generated `.mcp.json` (Claude Code, Cursor, VS Code, Grok Build, Devin, Goose, Droid) uses the same endpoint spelled `type: "http"`, the name that dialect uses; Muse, Antigravity, Junie and Gemini get their own spellings from the generator.

## Sign-in and access

The MCP server signs in with OAuth. No config in this plugin holds an API key, and no step asks you to paste one.

1. The server returns 401 until the client signs in, so the client starts OAuth when the server is added or connected and opens a Dodo Payments consent page in your browser. Some clients start it from a command: `/mcp` in Claude Code, `codex mcp login dodopayments`, `opencode mcp auth dodopayments`, `muse mcp login dodopayments`, or `devin mcp login dodopayments`.
2. Sign in, then pick the business, the mode (test or live) and the permissions to grant.
3. The client stores the token. To switch to another business or mode, sign out of the server in your client and sign in again.

To review or revoke access, open the Dodo Payments dashboard at **Settings > Connected Apps**.

Every client config in this repo dials `https://mcp.dodopayments.com/mcp` directly, sets no headers, and lets the client run OAuth discovery itself. A host that cannot run MCP OAuth can use `https://mcp.dodopayments.com/mcp?auth=optional`: `search_docs`, `read_docs_page` and `search` work without an account, and `execute` and `feedback` return 401. Today that is the xAI API (see [Grok](./docs/clients/grok.md)).

### Dodo CLI

The skills use the Dodo CLI for local webhook testing. It uses the same OAuth sign-in:

```bash
npm i -g dodopayments-cli   # browser sign-in needs v3.7.0 or later
dodo login                  # sign in with the browser
dodo whoami                 # show the stored sign-in
```

Over SSH or with no browser, run `dodo login --device` in place of `dodo login`, and enter the code on another device. To sign out when you finish, run `dodo logout all`.

## Enable / disable the MCP server

The MCP server ships enabled by default. You can turn it off.

### OpenCode

The npm plugin reads an environment variable before registering the MCP server:

| Env var | Effect |
|---|---|
| `DODO_DISABLE_API_MCP=1` | Skips registering `dodopayments` |

`DODO_DISABLE_KNOWLEDGE_MCP` is still accepted and does nothing.

Truthy values: `1`, `true`, `yes`, `on` (case-insensitive). Export the var in your shell profile or set it inline:

```bash
DODO_DISABLE_API_MCP=1 opencode
```

### Claude Code, Codex CLI, Cursor

These clients load MCPs from the static `.mcp.json` shipped with the plugin. To disable the server, override its entry in your own project-level config and set `"enabled": false`.

**Claude Code** - edit `.mcp.json` at your project root (or run `claude mcp disable dodopayments`):

```json
{
    "mcpServers": {
        "dodopayments": {
            "type": "http",
            "url": "https://mcp.dodopayments.com/mcp",
            "enabled": false
        }
    }
}
```

Run `/reload-plugins` to apply.

**Codex CLI / Cursor** - the same `enabled: false` pattern works in any project-level `.mcp.json` that overrides the plugin's bundled file. Restart the client after editing.

> Per-server toggles inside the Claude Code `/plugin` UI are tracked upstream in [anthropics/claude-code#27105](https://github.com/anthropics/claude-code/issues/27105) and [#46373](https://github.com/anthropics/claude-code/issues/46373). Until those land, the `enabled: false` override above is the supported path.

## A prompt to try first

Once the plugin is active, try:

```
Set up Dodo Payments webhook handlers in my Next.js app for payment.succeeded and subscription.active events.
```

Your agent will load the `dodo-payments` skill's webhooks reference, use the server's `search_docs` tool to pull the latest payload shapes, and write a handler with signature verification following the Standard Webhooks spec.

## Local development

```bash
git clone https://github.com/dodopayments/dodo-agent-plugin.git
cd dodo-agent-plugin
```

No submodules, no build step - `skills/` is vendored as real files.

Validate the Claude Code plugin and marketplace:

```bash
claude plugin validate .
```

Load the plugin directly for a dev session:

```bash
claude --plugin-dir ./dodo-agent-plugin
```

Verify everything before pushing:

```bash
npm run verify     # generated artifacts in sync + Agent Plugins conformance
```

### Repository layout

| Path | Role |
|---|---|
| `plugin.json` | **Canonical.** Agent Plugins v1.0.0 manifest and the version source of truth |
| `mcp.json` | **Canonical.** Agent Plugins v1.0.0 MCP config |
| `skills/` | **Canonical.** Skills, vendored as real files; the declared set lives in `.skills-source.json` |
| `overlays/*.json` | Hand-authored provider extras the closed spec schema cannot express |
| `.claude-plugin/`, `.cursor-plugin/`, `.codex-plugin/`, `.muse-plugin/`, `.agents/`, `.mcp.json`, `gemini-extension.json`, `plugins/dodopayments/`, `providers/` | **Generated.** Do not hand-edit - run `npm run build` |
| `scripts/build.mjs` | The single generator (`--check` for drift) |
| `scripts/conformance.mjs` | Agent Plugins conformance validator |
| `.skills-source.json` | Upstream provenance for the vendored skills |

Skills are authored in [`dodopayments/skills`](https://github.com/dodopayments/skills) and vendored here. A weekly workflow re-syncs them and opens a PR; run it on demand with the **Sync skills from upstream** workflow dispatch.

## For maintainers

The repo is configured to publish the OpenCode npm package on every GitHub Release.

**One-time setup (already done for this repo):**

- npm scope `@dodopayments` exists and is owned by Dodo Payments.
- npm Trusted Publishing (OIDC) is configured for `@dodopayments/opencode-plugin` against `publish-opencode.yml`. No npm token is stored in the repo.

**Release workflow:**

1. Bump `version` in `plugin.json` (the single source of truth).
2. Run `npm run build` to propagate it to every generated manifest.
3. Run `npm run verify`, then commit and tag.
4. Create a GitHub Release - the `Publish @dodopayments/opencode-plugin` workflow publishes to npm with provenance.

**Manual dry-run:**

- Workflow dispatch with `dry_run: true` to validate the release pipeline without publishing.

**CI checks:**

- `Verify` runs on every pull request and push to `main`: artifact drift, Agent Plugins conformance, live JSON Schema validation, an "every declared skill, zero symlinks" assertion, per-client manifest checks (Muse, Antigravity, Junie, Gemini), and an npm payload check.
- The release workflow re-runs the same gates before publishing.

## Resources

- [Dodo Payments documentation](https://docs.dodopayments.com)
- [Agent Skills docs](https://docs.dodopayments.com/developer-resources/agent-skills)
- [MCP Server docs](https://docs.dodopayments.com/developer-resources/mcp-server)
- [Skills source repo](https://github.com/dodopayments/skills)
- [Discord community](https://discord.gg/bYqAp4ayYh)

## License

MIT - see [LICENSE](./LICENSE).
