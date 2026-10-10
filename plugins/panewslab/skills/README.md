# PANews Agent Toolkit

PANews Agent Toolkit is PANews's official agent package for cryptocurrency and blockchain news discovery, Polymarket smart money leaderboard reading, creator workflows, and PANews web-page reading.

Track crypto narratives, inspect public Polymarket smart money boards, publish faster on PANews, and turn PANews pages into agent-ready Markdown.

## Install as Skills

```bash
# Using Bun
bunx skills add panewslab/skills

# Using NPM
npx skills add panewslab/skills
```

If your AI assistant supports skill installation, you can also send:

```txt
Install PANews skills at github.com/panewslab/skills
```

Use this path when your assistant supports repository-based skill installation and expects the canonical skill collection under [skills/](skills/).

## Install as a Plugin

This repository itself is also the plugin root for Codex- and Claude Code-style plugin packaging. No extra wrapper plugin directory is required.

Plugin manifests:

- Codex: [.codex-plugin/plugin.json](.codex-plugin/plugin.json)
- Claude Code: [.claude-plugin/plugin.json](.claude-plugin/plugin.json)

Canonical plugin content:

- Skills: [skills/](skills/)
- License: [LICENSE](LICENSE)

Use this path when your host product supports plugin installation from a Git repository or local plugin root and can discover repo-root plugin manifests.

For Claude Code, the typical flow is:

```text
/plugin marketplace add panewslab/skills
/plugin install panews@panews-agent-toolkit
```

For Codex-style plugin hosts, point the host at this repository root so it can read [.codex-plugin/plugin.json](.codex-plugin/plugin.json) and the bundled [skills/](skills/).

OpenClaw compatibility is provided through the Codex- and Claude-compatible bundle layout in this repository, not through a native OpenClaw plugin manifest.

For OpenClaw, install this bundle from a local checkout or archive:

```bash
git clone https://github.com/panewslab/skills.git
cd skills
openclaw plugins install .
# or link for development
openclaw plugins install -l .
```

## Skills

| Skill                                                  | What it is for                                                                                                                                                             | Use when                                                                                                |
| ------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| [panews](skills/panews/SKILL.md)                       | Crypto and blockchain news discovery, briefings, and public smart money leaderboard reads                                                                                 | You need PANews coverage about crypto news, projects, market narratives, rankings, events, calendars, or the latest public smart money board snapshots |
| [panews-creator](skills/panews-creator/SKILL.md)       | Write, manage, and publish PANews articles with authenticated creator tools for sessions, drafts, submissions, image uploads, tag search, and columns                      | You need authenticated PANews creator operations that require `PA-User-Session`                         |
| [panews-web-viewer](skills/panews-web-viewer/SKILL.md) | Read PANews homepage, article, and column pages as Markdown with page metadata                                                                                             | You need the rendered PANews page itself as Markdown rather than structured API-style content           |

## Article content

Reader and creator CLIs exchange article bodies as Markdown. Creator content files are uploaded directly; the reader keeps the returned Markdown, including supported media HTML, intact. During the API compatibility period, requests send `PA-Content-Format: markdown`; the header will be removed when Markdown becomes the sole API body format. Requests identify this release as `panews-cli/0.2.1`.

The generated Node bundles include their runtime dependencies and need no Markdown conversion WASM or HTML parser. The web-viewer skill continues to read rendered web pages.
