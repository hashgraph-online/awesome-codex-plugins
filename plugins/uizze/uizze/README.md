# UIZZE · Better UI for coding agents

**Build interfaces that look like your product.** Give Codex, Claude Code, Cursor, and GitHub Copilot a focused UI workflow, with optional references from **800,000+ real web and iOS screens**.

[![Stop Making UI Slop with UIZZE](https://uizze.com/landing/anti-ui-slop-skill-banner.png)](https://uizze.com/?utm_source=github&utm_medium=repository&utm_campaign=discovery&utm_content=readme_banner)

[![CI](https://github.com/uizze/uizze/actions/workflows/ci.yml/badge.svg)](https://github.com/uizze/uizze/actions/workflows/ci.yml)
[![Licenses: MIT and Apache-2.0](https://img.shields.io/badge/Licenses-MIT_%2F_Apache--2.0-black.svg)](LICENSING.md)
[![GitHub MCP Registry](https://img.shields.io/badge/GitHub-MCP_Registry-181717?logo=github)](https://github.com/mcp/uizze/uizze)

[**Explore UIZZE →**](https://uizze.com/?utm_source=github&utm_medium=repository&utm_campaign=discovery&utm_content=readme_product) · [Try a workflow](examples/agent-workflows.md) · [Connect MCP](integrations/mcp) · [Add the PR check](integrations/github-action)

## Watch UIZZE before and after

30-second mobile UI comparison: **No skills** on the left, **MCP + Skills** on the right.

https://github.com/user-attachments/assets/0137638f-d963-4e6b-a1a6-d7e2dce87600

[**Build your next screen with UIZZE →**](https://uizze.com/?utm_source=github&utm_medium=repository&utm_campaign=discovery&utm_content=readme_video)

[Try a billing screen in Claude Code, Cursor, or Copilot](examples/first-screen.md): install, copy the brief, connect optional reference search, and check the result.

## Start with your next screen

Install the free UI design skill:

```bash
npx skills add https://uizze.com --skill ui-design
```

Then give your agent a real task:

```text
Use ui-design to improve our billing settings page. Make the current plan,
payment method, and invoices easy to scan. Reuse our components and design
tokens. Include loading, empty, error, and permission states. Inspect the
result at desktop and mobile sizes and fix what breaks.
```

The skills work without an account or MCP connection. Start in an existing project: your brief, components, and design system guide the work.

| Your task | Free skill | What to ask for |
| --- | --- | --- |
| Build or redesign an interface | [`ui-design`](skills/ui-design) | A clear hierarchy, working interactions, and the states your users need |
| Fix a generic first draft | [`anti-ui-slop`](skills/anti-ui-slop) | Product-specific content, deliberate layouts, and a finish review |
| Investigate a UI decision | [`ui-radar`](skills/ui-radar) | A focused reference workflow; connect the paid MCP for live retrieval |

For a focused review, install `anti-ui-slop` instead:

```bash
npx skills add https://uizze.com --skill anti-ui-slop
```

Prefer installing from GitHub? Use `npx skills add uizze/uizze --skill ui-design`. The domain packages remain canonical; this repository mirrors all three skills.

## Bring real product references into the conversation

Use UIZZE when the agent needs to see how real products handle a specific design problem: a dense settings page, a permission flow, an invoice table, or an iOS onboarding screen.

The optional **paid MCP** connects your agent to focused reference and material search:

| Tool | What your agent gets |
| --- | --- |
| `find_ui_references` | Up to three full-screen references per result, drawn from UIZZE's web and iOS library |
| `find_ui_materials` | Up to three hosted fonts, icons, animated icons, or explicitly requested packs |

```text
Find references for a team permissions screen with inherited roles and
restricted actions. Explain which decisions would help our workflow,
then implement them using our existing components and visual language.
```

Create an agent token in [UIZZE](https://uizze.com/?utm_source=github&utm_medium=repository&utm_campaign=discovery&utm_content=readme_mcp), then follow the [MCP setup guide](integrations/mcp). References inform the design; the agent builds the interface in your own product's style. If a search returns no useful evidence, continue from the project.

## Use it where you already build

| Environment | Start here |
| --- | --- |
| Codex, Claude Code, Cursor | [Install and try your first task](examples/agent-workflows.md) |
| GitHub Copilot | [UIZZE plugin in Awesome Copilot](https://github.com/github/awesome-copilot/tree/main/plugins/uizze) |
| Gemini CLI | [Install the Uizze extension](plugins/gemini-cli/) |
| Antigravity | [Install the Uizze custom plugin](plugins/antigravity/) |
| VS Code, Windsurf / Cascade, Zed | [Native MCP connection instructions](integrations/mcp/) |
| MCP clients | [GitHub MCP Registry](https://github.com/mcp/uizze/uizze) · [Connection guide](integrations/mcp) |
| GitHub pull requests | [UI Slop Gate Action](integrations/github-action) · [Inspect actual example output](examples/pull-request-check.md) |

## Catch unfinished UI in pull requests

The free **UI Slop Gate** checks changed frontend source for inert controls, missing state markers, hardcoded colors, and combinations of generic dashboard cues. Findings appear next to the code and in the workflow summary.

```yaml
permissions:
  contents: read

steps:
  - uses: actions/checkout@v7
    with:
      fetch-depth: 2
      persist-credentials: false
  - uses: uizze/uizze@v1
    with:
      fail-on: error
```

No account, API key, or source upload. [Watch the published Action check a before-and-after example](https://github.com/uizze/uizze/actions/workflows/ui-slop-gate-example.yml), then [copy the complete workflow](integrations/github-action#usage). This is a conservative source check; use rendered inspection and your normal accessibility and usability checks alongside it.

## Build a screen with a worked example

- [Free UI task-brief builder](https://uizze.com/tools/ui-design-prompt-builder): describe the task, user, and outcome; copy or download a concrete agent prompt. No account required.
- [SaaS dashboard walkthrough](https://uizze.com/guides/saas-dashboard-design): compare information hierarchy and try loading, empty, error, and assignment states.
- [DESIGN.md template](https://uizze.com/guides/design-md-for-coding-agents): download a design contract and apply it across settings and billing.
- [Empty-state examples](https://uizze.com/guides/empty-state-ui-design): distinguish first use, no matches, service failure, and unavailable access.
- [iOS onboarding and recovery](https://uizze.com/guides/onboarding-ui-design): try a small browser prototype and explore the native SwiftUI starter.

These are original UIZZE teaching examples with fictional data. [Browse all guides](https://uizze.com/guides) for agent-specific setup, comparisons, and review workflows.

## Explore the repository

- [Practical agent workflows](examples/agent-workflows.md): billing settings, data tables, permission screens, and native iOS.
- [Reproduce a pull-request check](examples/pull-request-check.md): source, findings, and a local command.
- [Next.js starter](integrations/nextjs-starter): an existing starting point for a product-specific interface.
- [Storybook integration](integrations/storybook): review UI states alongside your components.
- [Public distribution](DISTRIBUTION.md): maintained install and catalog paths.

Production metadata: [skills index](https://uizze.com/.well-known/agent-skills/index.json) · [MCP manifest](https://uizze.com/.well-known/mcp.json) · [server card](https://uizze.com/.well-known/mcp/server-card.json) · [documentation](https://uizze.com/docs).

## License

Uizze-authored repository code and text use [MIT](LICENSE) unless a more specific notice applies. Bundled skill playbooks retain their Apache-2.0 license and third-party notices. See [the license map](LICENSING.md) before redistributing a skill package.
