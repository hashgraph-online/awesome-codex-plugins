<p align="center">
  <a href="https://uizze.com/?utm_source=github&amp;utm_medium=repository&amp;utm_campaign=discovery&amp;utm_content=readme_logo"><img src="https://uizze.com/brand/icons/uizze-web-app-icon-192x192.png" alt="" width="72" align="middle"></a>&nbsp;&nbsp;<a href="https://uizze.com/?utm_source=github&amp;utm_medium=repository&amp;utm_campaign=discovery&amp;utm_content=readme_logo"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/brand/uizze-wordmark-dark.svg"><img src="assets/brand/uizze-wordmark-light.svg" alt="UIZZE" width="250" align="middle"></picture></a>
</p>

<h3 align="center">Build better UI with coding agents.</h3>
<p align="center">
  Design guidance, real app references, fonts and icons.<br>
  For Claude Code, Cursor, Codex and GitHub Copilot.
</p>
<p align="center">
  <a href="https://www.skills.sh/site/uizze.sh"><img src="https://img.shields.io/badge/Skills-1.3M-181717?logo=vercel&amp;logoColor=white" alt="skills.sh: 1.3M total installs across uizze.sh skills"></a>
  <a href="https://uizze.com"><img src="https://img.shields.io/badge/Uizze-official-1a1a1a" alt="Uizze official"></a>
  <a href="LICENSING.md"><img src="https://img.shields.io/badge/license-MIT_%2F_Apache--2.0-blue" alt="Licenses: MIT and Apache-2.0"></a>
</p>
<p align="center">
  <a href="https://uizze.com/?utm_source=github&utm_medium=repository&utm_campaign=discovery&utm_content=readme_product">uizze.com</a> ·
  <a href="#connect-the-uizze-mcp">MCP</a> ·
  <a href="https://uizze.com/docs">Docs</a> ·
  <a href="https://x.com/tryUizze">X</a>
</p>

---

[Uizze](https://uizze.com/?utm_source=github&utm_medium=repository&utm_campaign=discovery&utm_content=readme_intro) gives coding agents design guidance and resources for web and iOS interfaces. The skills work with your project's code, components and assets; the MCP brings in real app screens, flows, design systems, licensed fonts, icons and animations.

## The skills

| Skill | What it does |
| --- | --- |
| [`uizze-ui`](skills/uizze-ui) | Uizze's design tools and resources, applied to the UI you're building. |
| [`ui-design`](skills/ui-design) | Build and improve interfaces, from layout and typography to interactions and states. |
| [`anti-ui-slop`](skills/anti-ui-slop) | Give generic drafts a clearer direction and check the finished result. |
| [`image-to-ui`](skills/image-to-ui) | Turn a screenshot or mockup into a 1:1 implementation, then render and compare. |
| [`ui-radar`](skills/ui-radar) | Find relevant app screens and flows for a specific design question. |

## Install

One command from your project root. Choose your skills and agents when prompted:

```bash
npx skills@latest add uizze/uizze
```

Works with Claude Code, Cursor, Codex, GitHub Copilot and other agents supported by [Skills](https://skills.sh). The skills are free and work without a Uizze account or MCP connection.

<details>
<summary>Install options</summary>

Install just the Uizze skill:

```bash
npx skills@latest add uizze/uizze --skill uizze-ui
```

Install for specific agents without prompts:

```bash
npx skills@latest add uizze/uizze -a claude-code -a cursor -y
```

Install user-wide:

```bash
npx skills@latest add uizze/uizze -g
```

UI Taste and iOS Design remain available from their separate distribution source:

```bash
npx skills@latest add https://uizze.sh --skill ui-taste
npx skills@latest add https://uizze.sh --skill ios-design
```

The existing `https://uizze.com` source also supports `anti-ui-slop`, `ui-design` and `ui-radar`.

</details>

## Connect the Uizze MCP

Give your agent access to Uizze's reference and material library:

```text
https://uizze.com/mcp
```

Sign in at [uizze.com](https://uizze.com/?utm_source=github&utm_medium=repository&utm_campaign=discovery&utm_content=readme_mcp), then copy your setup prompt into your agent. It includes your private access token and connection instructions. MCP access requires a paid plan; browsing references on the website is free without an account.

[Connection instructions for your agent →](https://uizze.com/docs#connect)

## Try it

With the skills installed, give your agent a task:

> Improve our billing settings page. Reuse our components and design tokens, cover loading and error states, and check it at desktop and mobile sizes.

> Implement this screenshot in our app. Match the layout, typography and spacing, then render it and correct the differences.

With the MCP connected:

> Find onboarding flows for a fitness app. Show me the relevant screens and use them to guide our implementation.

> Find a font pairing and icons that fit this interface. Keep the license notices with any files we use.

<details>
<summary>Watch Uizze before and after</summary>

Without Uizze on the left, with Uizze on the right.

https://github.com/user-attachments/assets/d7ee2275-8e7f-474c-a2e4-b45759b86996

</details>

<details>
<summary>More from this repository</summary>

- [Agent workflows](examples/agent-workflows.md) and [your first screen](examples/first-screen.md)
- [UI Slop Gate](integrations/github-action): check changed frontend source in pull requests
- [Plugin and client setup](integrations/mcp) · [Gemini CLI](plugins/gemini-cli) · [Antigravity](plugins/antigravity)
- [Next.js starter](integrations/nextjs-starter) · [Storybook integration](integrations/storybook)
- [Worked examples](examples/pull-request-check.md) · [Design guides](https://uizze.com/guides)
- [Public distribution](DISTRIBUTION.md)

</details>

## License

Uizze-authored code and text use [MIT](LICENSE) unless a more specific notice applies. Bundled design playbooks retain Apache-2.0 and third-party notices. See the [license map](LICENSING.md) for details. Service content follows [Uizze's terms](https://uizze.com/terms).

---

<p align="center">
  Built by <a href="https://uizze.com">Uizze</a>.<br>
  <a href="https://uizze.com/docs">Docs</a> ·
  <a href="https://x.com/tryUizze">X</a>
</p>

