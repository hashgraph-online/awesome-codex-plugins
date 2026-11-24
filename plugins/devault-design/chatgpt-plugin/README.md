# Devault for ChatGPT and Codex

Search and study real UI design references, analyze design patterns across shipped products, and fetch ready-made
design systems from the [Devault](https://devault.design) library, without leaving ChatGPT or Codex.

This repository is the plugin package: a manifest, the address of Devault's MCP server, three skills and an icon.
It holds no code. The tools themselves run on Devault's server, `https://devault.design/api/mcp`.

## What it does

- **Search screens** by description, and narrow them by platform, industry, screen type or company.
- **Analyze a design pattern** across the library: how common it is, where it appears and which components go with it.
- **Study a screen** at a readable size, or **find screens that look like** one you picked. Every screen comes with a
  link that opens it on devault.design.
- **Fetch a design system** (palette with contrast grades, type scale, spacing, components) as DESIGN.md, Tailwind v4,
  CSS variables, shadcn/ui, design tokens, Figma variables, SwiftUI, Android XML or an image prompt.

Try:

- "Find onboarding screens from fintech apps"
- "How do apps design paywalls? Show the numbers and a few examples"
- "Get a dark dashboard design system as Tailwind tokens"

## Install

The plugin is listed in OpenAI's plugin directory: in ChatGPT or Codex, open the plugins and search for **Devault**.
The first time a Devault tool runs, you are asked to sign in to Devault and allow the connection (OAuth). The plugin
carries no key and asks for none.

You need a Devault account whose plan includes MCP access. A search returns one page of results, and the number of
images is limited per day.

## What's in the package

| file | what it is |
|---|---|
| `plugin.json` | the manifest (Agent Plugins 1.0.0), with the listing under `extensions.com.openai` |
| `mcp.json` | one remote server, `https://devault.design/api/mcp` |
| `.codex-plugin/plugin.json`, `.mcp.json` | the same manifest and server in Codex's own plugin layout, for installers that read that |
| `skills/get-started` | introduces the plugin and gets a first result |
| `skills/research-ui-patterns` | researches how real products design a screen, flow or pattern, and reports with the screens behind it |
| `skills/apply-design-system` | finds a ready-made design system and delivers it in the format your project needs |
| `assets/logo.png` | the icon |

## Data and safety

Every tool only reads: none can change anything in your Devault account. The server receives what a tool is asked
(a search, a screen id, a style name) and records each call against your account for its daily limits. See the
[privacy policy](https://devault.design/privacy) ("What connected AI tools receive") and the
[terms](https://devault.design/terms).

Screens are references for study and inspiration. The companies shown are not affiliated with Devault.

## Support

[devault.design/support](https://devault.design/support), or email founder@devault.design. To report a security
issue, see [SECURITY.md](SECURITY.md).

## Licence

The files in this repository are under the [MIT licence](LICENSE). The licence covers this package only: the Devault
service, its library and the screens in it are not licensed by it, and are governed by the
[terms](https://devault.design/terms).
