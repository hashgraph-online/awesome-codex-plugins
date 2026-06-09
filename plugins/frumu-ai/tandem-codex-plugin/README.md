<div align="center">
  <img src="./assets/readme-hero.png" alt="Tandem Codex Plugin" width="500">

  <h1>Tandem Codex Plugin</h1>

  <p><strong>Plan with Codex. Govern with Tandem. Run with receipts.</strong></p>

  <p>
    A Codex CLI plugin that turns Codex into a <em>Tandem Workflow Architect</em>:
    a plan-mode design partner that helps you shape Tandem workflows and hands
    them to the Tandem engine for validation, preview, and run.
  </p>

  <p>
    <a href="https://tandem.ac/"><img src="https://img.shields.io/website?url=https%3A%2F%2Ftandem.ac%2F&label=tandem.ac&logo=firefox&style=for-the-badge" alt="Website"></a>
    <a href="https://docs.tandem.ac/"><img src="https://img.shields.io/badge/docs-tandem.ac-2563EB?logo=readthedocs&logoColor=white&style=for-the-badge" alt="Docs"></a>
    <a href="https://github.com/frumu-ai/tandem"><img src="https://img.shields.io/badge/github-frumu--ai%2Ftandem-181717?logo=github&style=for-the-badge" alt="Tandem GitHub"></a>
    <a href="https://github.com/frumu-ai/tandem-codex-plugin"><img src="https://img.shields.io/badge/plugin-repo-181717?logo=github&style=for-the-badge" alt="Plugin Repository"></a>
    <a href="https://github.com/frumu-ai/tandem-codex-plugin/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/frumu-ai/tandem-codex-plugin/ci.yml?branch=main&label=CI&logo=github&style=for-the-badge" alt="CI"></a>
    <a href="https://github.com/frumu-ai/tandem-codex-plugin/actions/workflows/plugin-scanner.yml"><img src="https://img.shields.io/github/actions/workflow/status/frumu-ai/tandem-codex-plugin/plugin-scanner.yml?branch=main&label=scanner&logo=shield&style=for-the-badge" alt="Plugin Scanner"></a>
    <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge" alt="License: MIT"></a>
  </p>
</div>

> Codex helps you think. Tandem runs and governs. This plugin glues the two
> together without replacing either.

---

## 1. What this is

A focused Codex plugin (skill + Tandem Docs MCP + shared design rules + worked
examples) that:

- Walks you through designing a Tandem workflow from intent
  (`/create-workflow` template) or by hand-assembling a complex multi-agent DAG
  (`/build-complex-workflow` template).
- Calls the **real Tandem HTTP API** to draft, preview, validate, and apply
  workflows — so the engine is always the source of truth.
- Bakes in Tandem's actual policy primitives: `tool_policy`, `mcp_policy`,
  `approval_policy`, `scope_policy`, `model_policy`, `output_contract`,
  schedules, and triage gates.
- Refuses to apply or run anything destructive, externally visible, public,
  paid, or irreversible without explicit user approval.

## 2. Who it's for

- **Tandem operators** who use Codex daily and want a structured way to
  design new workflows without leaving the CLI.
- **Workflow authors** who already know Tandem and want a faster scaffolding
  loop than a blank editor.
- **Teams** who want Codex's design help while keeping all execution and
  governance inside Tandem.

This plugin does **not** target users who have never used Tandem. It assumes
a running Tandem engine, an engine token, and a Tandem-configured model
provider/default model for workflows that execute model work.

## 3. How it helps Tandem users

- Accelerates the **first 80%** of authoring: trigger, agents, per-stage
  prompts, output contracts, approval gates, MCP allowlists.
- Forces good defaults: every external write is approval-gated, every stage
  has an explicit `output_contract`, every agent has a tool allowlist.
- Treats source-only fields as engine-validated, not Codex-fabricated. When
  Codex doesn't know an exact field name, it asks the engine instead of
  guessing.
- Surfaces engine errors verbatim, then helps you fix them.

## 4. Install in Codex

### From GitHub

```bash
codex plugin marketplace add frumu-ai/tandem-codex-plugin
```

In the Codex TUI:

```
/plugins
```

Find **Tandem Workflow Architect** and install it. The plugin skill and
bundled Tandem Docs MCP server appear once installed.

The files in `commands/` are workflow templates the skill can follow.
Some Codex builds may expose them as slash commands; if yours does not,
describe the same goal in chat and the skill will use the corresponding
template.

You can pin a branch, tag, or commit with:

```bash
codex plugin marketplace add frumu-ai/tandem-codex-plugin@main
```

### From a local checkout (development)

Use a local marketplace root only when developing or testing unpublished
changes:

```bash
git clone https://github.com/frumu-ai/tandem-codex-plugin.git
cd tandem-codex-plugin
codex plugin marketplace add "$(pwd)"
```

Codex accepts `owner/repo[@ref]`, HTTPS Git URLs, SSH URLs, and local
marketplace root directories. It caches installed plugins under
`~/.codex/plugins/cache/<marketplace>/<plugin>/<version>/`.

## 5. Install Tandem

The plugin doesn't bundle the engine. Pick one of two supported paths:

### A. CLI binaries / headless

```bash
npm install -g @frumu/tandem
tandem doctor
tandem-engine status
tandem-engine serve --hostname 127.0.0.1 --port 39731
```

`@frumu/tandem` ships the `tandem` master CLI and the `tandem-engine`
runtime. Use this path on servers, in CI, or when you want
terminal-first setup. Use `tandem-engine` for engine-specific commands
such as `serve`, `status`, `providers`, and `token generate`.

### B. Control panel (recommended for local dev)

```bash
npm install -g @frumu/tandem
tandem install panel               # installs @frumu/tandem-panel
tandem panel init                  # provisions the panel + engine + token
tandem panel open                  # optional: open the web admin
```

The control panel ([`@frumu/tandem-panel`](https://www.npmjs.com/package/@frumu/tandem-panel))
gives you a web UI for chats, routines, swarms, memory, channels, and ops
against the same engine the plugin talks to.

> **Legacy compatibility.** Older docs reference a standalone `tandem-setup`
> CLI shipped by `@frumu/tandem-panel`. Use the `tandem install panel` flow
> above unless documentation you trust says otherwise for your version.

After either path the engine listens on `TANDEM_BASE_URL` (default
`http://127.0.0.1:39731`). Run Tandem's first-run checks (`tandem doctor`
for the master CLI and `tandem-engine status` for the engine), then
discover where the installer wrote the token by running `/tandem-setup`
in Codex and verify everything end-to-end with `/tandem-doctor`.

## 6. Configure plugin auth

The `@frumu/tandem-client` `TandemClient` constructor takes a string
`token`; the SDK does not itself read env vars or files. The plugin's
helper scripts (`scripts/`) resolve the token from the environment in
this order, then pass the resulting string to the SDK constructor:

1. `TANDEM_API_TOKEN` environment variable.
2. `TANDEM_API_TOKEN_FILE` environment variable pointing at a file that
   contains the token. The scripts read and trim the file. Path is
   whatever your installer chose — the plugin does not assume a
   location.
3. (Calling the SDK directly outside the plugin?) Pass `token` to
   `new TandemClient({ baseUrl, token })` yourself.

A dev-only escape hatch (`TANDEM_UNSAFE_NO_API_TOKEN=1`) is supported but
**not recommended**. The engine logs a warning on every request when this
is set. Do not use it on hosted, public, or shared engines.

The engine accepts the token via any one of these request headers (the SDK
picks one for you; use whichever you prefer when hand-rolling fetch):

- `X-Agent-Token: <token>`
- `X-Tandem-Token: <token>`
- `Authorization: Bearer <token>`

Copy `.env.example` to `.env` and set the variable(s) that match your
setup. Detailed recipe and troubleshooting:
[`shared/tandem-auth.md`](./shared/tandem-auth.md).

## 7. Configure model providers

Codex authentication is separate from Tandem provider authentication.
Logging into Codex does not automatically give the Tandem engine access
to OpenAI, Anthropic, OpenRouter, or any other model provider.

For local dev, configure model access through the Tandem engine. Use
`tandem-engine providers` to list supported provider IDs, set
provider-specific environment variables such as `OPENAI_API_KEY`,
`ANTHROPIC_API_KEY`, or `OPENROUTER_API_KEY`, and choose provider/model
defaults through engine config or command options:

```bash
tandem-engine providers
tandem-engine serve --provider openai --model gpt-4o-mini
tandem-engine run "Smoke test provider setup" --provider openai --model gpt-4o-mini
```

For one process or one command, `--api-key` can override the selected
provider key. The SDK surface is also available for trusted local setup
scripts:

```ts
await client.providers.catalog();
await client.providers.config();
await client.providers.setApiKey(providerId, apiKey);
await client.providers.setDefaults(providerId, modelId);
```

Do not paste provider API keys into Codex chat. Pass them directly from
a private local shell/session, engine config, or provider-specific env
vars. Run `/tandem-doctor` after setup; it checks engine auth and
provider/model readiness.

## 8. The plan-mode loop

This is what the plugin's skill walks you through every time:

1. **Understand intent.** What are you actually trying to automate? What's
   the trigger, the inputs, and the desired artifact?
2. **Classify.** Is this a single-agent routine, a multi-agent V2 DAG, a
   planner-generated workflow, or a revision/repair of an existing one?
3. **Draft Tandem-shaped JSON.** Per-stage objective, prompt,
   `output_contract`, `tool_policy`, `mcp_policy`, `approval_policy`,
   `model_policy`, `scope_policy`, schedule, triage gate.
4. **Explain the graph in plain language.** No JSON dump until the user
   sees the picture.
5. **Ask only blocking questions.** Don't ask for things Tandem can answer
   later, but do stop if Tandem has no configured provider/default model
   and the next step would execute model work.
6. **Validate via the API.** Use prompt-based
   `client.workflowPlans.preview({ prompt, planSource, workspaceRoot? })`
   for one-shot drafts, `client.workflowPlans.chatMessage` round-trips
   for in-progress chat drafts, `client.workflowPlans.importPreview({ bundle })`
   for bundles, or `client.automationsV2.create({ ...payload, status: "paused" })`
   for V2 DAGs. `preview` is **not** a preview-by-`plan_id` call.
7. **Apply only with explicit approval.** Never auto-apply. Never auto-run.

Full design rules: [`shared/tandem-workflow-design-rules.md`](./shared/tandem-workflow-design-rules.md).

## 9. Build from intent

```
/create-workflow
```

Describe the goal in plain language. The skill calls
`client.workflowPlans.chatStart({ prompt, planSource: "intent_planner_page", workspaceRoot? })`,
returns a `plan_id`, and shows the draft DAG. Iterate with:

```
/revise-workflow <plan_id> "<change>"
```

When ready, apply. This calls `workflowPlans.apply`, **writes the
returned `plan_package_bundle` to disk** (default
`.tandem-codex/plan-bundles/<plan_id>.json`), and follows up with
`importPreview` so you see the engine's compatibility report:

```
/apply-workflow <plan_id>
```

If `importPreview` reports compatible, finalize the import behind a
separate explicit approval. The plugin/skill will never run this step
without a clear "yes, import":

```
/import-preview-workflow .tandem-codex/plan-bundles/<plan_id>.json
```

There is no separate user-facing npm workflow CLI for this plugin. Use
the Codex slash commands above when working from Codex. Use
`tandem-engine` or the Tandem control panel for Tandem runtime
operations outside Codex.

For one-shot prompt validation (no chat session) or to preview an
existing bundle without applying:

```
/preview-workflow "<one-line workflow goal>"
/preview-workflow ./path/to/bundle.json
```

The full documented flow is
`chatStart → chatMessage → apply → importPreview → importPlan`. The
plugin pauses at every step that touches your live Tandem so you can
inspect before committing. Bundles live under `.tandem-codex/`, which
is git-ignored.

Worked examples:
[`examples/README.md`](./examples/README.md),
[`examples/reddit-research-to-notion.md`](./examples/reddit-research-to-notion.md) and
[`examples/market-research-pain-points-to-notion-row.md`](./examples/market-research-pain-points-to-notion-row.md).

## 10. Build a complex manual workflow

```
/build-complex-workflow
```

The skill walks you through each agent (id, display name, model, tool
allowlist, MCP allowlist), each node in the DAG (`agent_id`, `objective`,
`prompt`, `output_contract`, `depends_on`, `approval_policy`), and the
schedule. It assembles a V2 automation JSON and calls
`client.automationsV2.create` with `status: "paused"` so you can inspect
before arming.

Worked example: [`examples/manual-complex-workflow.md`](./examples/manual-complex-workflow.md).

## 11. How MCP fits in

Tandem already knows how to manage workflow MCP servers. The plugin's job is to:

- Help you decide **which** MCP tools each agent needs.
- Generate explicit `mcp_policy.allowed_servers` and
  `mcp_policy.allowed_tools` for each agent.
- Call out when an MCP isn't connected yet (`client.mcp.list()`,
  `client.mcp.listTools()`)
  and refuse to fabricate a tool name.

The plugin bundles the Tandem Docs MCP server at `https://tandem.ac/mcp` so
Codex can look up current Tandem API and workflow documentation while helping
you plan. Configure workflow execution MCP servers in your Tandem engine
(control panel or `POST /mcp`), not in this plugin. Each example workflow
documents which runtime MCP servers it expects.

Additional MCP examples:

- [`examples/support-ticket-triage-zendesk-slack.md`](./examples/support-ticket-triage-zendesk-slack.md)
  shows support-ticket triage with approved Zendesk notes and Slack
  escalation.
- [`examples/meeting-prep-calendar-crm-brief.md`](./examples/meeting-prep-calendar-crm-brief.md)
  shows daily meeting prep from calendar, CRM, and email.
- [`examples/invoice-intake-approval-accounting.md`](./examples/invoice-intake-approval-accounting.md)
  shows invoice extraction and approved accounting bill drafts.
- [`examples/churn-risk-monitor-crm-slack.md`](./examples/churn-risk-monitor-crm-slack.md)
  shows customer-success risk monitoring and approved escalations.
- [`examples/security-advisory-triage-github-linear.md`](./examples/security-advisory-triage-github-linear.md)
  shows dependency advisory triage and approved remediation issues.
- [`examples/prospect-email-drafts-gmail-approval.md`](./examples/prospect-email-drafts-gmail-approval.md)
  shows prospect research, Gmail draft creation, and final send approval.
- [`examples/market-research-pain-points-to-notion-row.md`](./examples/market-research-pain-points-to-notion-row.md)
  shows web research plus Reddit pain-point mining saved to a Notion
  database row.

## 12. What this plugin does NOT do

- It does **not** replace Tandem's planner, validator, or runtime.
- It does **not** store, cache, or transmit your engine token. Tokens stay
  in your shell env or token file.
- It does **not** run workflows in Codex. Every `run` is a Tandem API call.
- It does **not** auto-apply or auto-run anything destructive, externally
  visible, public, paid, or irreversible. Approval is mandatory for any
  write outside the workspace.
- It does **not** invent Tandem field names. When a field is uncertain, the
  skill asks the engine or asks you, never both.

## 13. Layout note

This repository is both the Codex plugin root and the marketplace root. The
install command points Codex at the repo root, and
`.agents/plugins/marketplace.json` describes the Git-backed plugin source for
distribution.

Two paths are required by the **Codex plugin specification**
(see [developers.openai.com/codex/plugins/build](https://developers.openai.com/codex/plugins/build)):

| Path | Why |
|---|---|
| `.codex-plugin/plugin.json` | Codex's required plugin manifest location. |
| `.agents/plugins/marketplace.json` | Repo-scoped Codex marketplace entry. |

The plugin payload lives at the repo root: `skills/`, `commands/`, `shared/`,
`scripts/`, `.mcp.json`, and `assets/`.

## 14. Release flow

Codex reads the plugin version from `.codex-plugin/plugin.json` and caches
installs under `~/.codex/plugins/cache/<marketplace>/<plugin>/<version>/`.
Keep `package.json` and `.codex-plugin/plugin.json` on the same semver.

For a release:

```bash
npm run version:set -- 0.1.1
npm run release:check -- v0.1.1
git add package.json package-lock.json .codex-plugin/plugin.json
git commit -m "Release v0.1.1"
git tag v0.1.1
git push origin main --tags
```

The `Release` GitHub Action runs on `v*.*.*` tags, checks that the tag
matches the plugin version, runs `npm run build`, compiles release notes
from `docs/WHATS_NEW_vX.Y.Z.md`, `RELEASE_NOTES.md`, or `CHANGELOG.md`
(in that order), and creates a GitHub Release from the compiled notes.

Full checklist: [`docs/RELEASE_PROCESS.md`](./docs/RELEASE_PROCESS.md).

---

## Layout at a glance

```
.codex-plugin/plugin.json        Codex manifest
.agents/plugins/marketplace.json Repo-scoped marketplace entry
.mcp.json                        Plugin-bundled Tandem Docs MCP config
skills/tandem-workflow-plan-mode/SKILL.md
commands/{create,revise,build-complex,preview,validate,apply,import-preview,run}-workflow.md
commands/{tandem-setup,tandem-doctor}.md
scripts/lib/tandem-config.ts        Shared base-URL/token resolution + client factory
scripts/tandem-api-healthcheck.ts
scripts/tandem-create-workflow-draft.ts
scripts/tandem-preview-workflow.ts
scripts/tandem-revise-workflow.ts
scripts/tandem-apply-workflow.ts
scripts/tandem-import-plan.ts
shared/tandem-workflow-design-rules.md
shared/tandem-api-discovery-notes.md
shared/tandem-output-contracts.md
shared/tandem-approval-gates.md
shared/tandem-auth.md
examples/README.md
examples/{reddit-research-to-notion,market-research-pain-points-to-notion-row,prospect-email-drafts-gmail-approval,support-ticket-triage-zendesk-slack,meeting-prep-calendar-crm-brief,invoice-intake-approval-accounting,churn-risk-monitor-crm-slack,security-advisory-triage-github-linear,github-bug-monitor,manual-complex-workflow,repo-task-runner}.md
```

## References

- Codex plugin spec: <https://developers.openai.com/codex/plugins/build>
- Codex skills: <https://developers.openai.com/codex/skills>
- Codex MCP: <https://developers.openai.com/codex/mcp>
- Tandem auth: <https://docs.tandem.ac/engine-authentication-for-agents/>
- Tandem TypeScript SDK: <https://docs.tandem.ac/sdk/typescript/>
- Tandem scheduling: <https://docs.tandem.ac/sdk/scheduling-automations/>
- Tandem MCP automated agents: <https://docs.tandem.ac/mcp-automated-agents/>

## License

MIT.
