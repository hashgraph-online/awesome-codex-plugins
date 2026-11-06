# bowmark plugin

[![Add to Cursor](https://cursor.com/deeplink/mcp-install-dark.svg)](cursor://anysphere.cursor-deeplink/mcp/install?name=bowmark&config=eyJ1cmwiOiJodHRwczovL2FwaS5ib3dtYXJrLmFpL21jcC9iYWRnZS1jdXJzb3IifQ==)
[![Install in VS Code](https://img.shields.io/badge/VS_Code-Install_Bowmark-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://vscode.dev/redirect/mcp/install?name=bowmark&config=%7B%22name%22%3A%22bowmark%22%2C%22type%22%3A%22http%22%2C%22url%22%3A%22https%3A%2F%2Fapi.bowmark.ai%2Fmcp%2Fbadge-vscode%22%7D)

[![MCP](https://img.shields.io/badge/MCP-server-000000?style=flat-square)](https://api.bowmark.ai/mcp)
[![npm](https://img.shields.io/npm/v/%40bowmark%2Fmcp?style=flat-square&label=%40bowmark%2Fmcp)](https://www.npmjs.com/package/@bowmark/mcp)
[![PyPI](https://img.shields.io/pypi/v/bowmark-mcp?style=flat-square)](https://pypi.org/project/bowmark-mcp/)
[![License](https://img.shields.io/badge/license-MIT-A3E635?style=flat-square)](https://opensource.org/licenses/MIT)

<sub>**LM Studio** — GitHub strips a raw `lmstudio:` link, so this one is a paste, not a button. Copy it into your browser's address bar:</sub>

```
lmstudio://add_mcp?name=bowmark&config=eyJ1cmwiOiJodHRwczovL2FwaS5ib3dtYXJrLmFpL21jcC9iYWRnZS1sbXN0dWRpbyJ9
```

The [Bowmark](https://bowmark.ai) plugin for **Claude Code**, **Codex**, **Antigravity**, and every client that reads **[Agent Plugins](https://agent-plugins.org/) 1.0.0** — installs the `bowmark` skill *and* auto-wires the hosted MCP server (`https://api.bowmark.ai/mcp`) in one step, so there's no separate `claude mcp add` / `config.toml` edit.

Jigs: small pages built on Bowmark and published for anyone to use. Each one runs with your own logins on the sites it lists, and your agent can search, open and publish them. Browse the store at https://bowmark.ai/jigs.

This package is the source of a one-way mirror to the public **[github.com/bowmark-ai/plugin](https://github.com/bowmark-ai/plugin)** (pushed on each `plugin-v*` release by [`release-plugin.yml`](../../.github/workflows/release-plugin.yml)) — same machinery as the skill mirror. The private monorepo can't be a public marketplace, but nothing here is private: only the public HTTP MCP URL and the public skill.

**One tree, five manifests, one payload.** Claude Code reads `.claude-plugin/`, Codex reads `.codex-plugin/` + `.agents/plugins/`, Cursor reads `.cursor-plugin/`, an Agent Plugins client reads the root `plugin.json` + `mcp.json`, and Antigravity reads that same root `plugin.json` + its own `mcp_config.json`. All five bundle the same skill and the same hosted MCP; nothing is duplicated but the manifest. Adding the third cost two files because the spec's conventional layout (`skills/<name>/SKILL.md`) is the layout this package already had.

**Antigravity is the one host that does NOT get its own manifest subdirectory, and that is forced, not a shortcut.** `agy plugin install <repo>` reads `plugin.json` only at the repo ROOT — confirmed against the real `agy` CLI (1.4.8, 2026-10-27) — with no `.antigravity-plugin/`-style override the way Cursor's lookup chain has one. So it shares the root Agent Plugins manifest rather than getting a sixth directory. Antigravity's own validator is lenient about the extra fields that manifest carries (`version`, `author`, `homepage`, `repository`, `license`, `keywords` — all outside its own schema's `name`/`description`/`$schema`): it logs a note (`"declares the Agent Plugins 1.0.0 $schema"`) and loads it as a **native** plugin whenever the host's `enable-agent-plugins-spec` flag is off, which is the common case. In that mode it reads `mcp_config.json` — Antigravity's own file and its own field name, `serverUrl`, never `httpUrl` or `url` — instead of the shared `mcp.json`. With the flag on, Antigravity reads `mcp.json` instead and the install is indistinguishable from any other Agent Plugins client, attributed to `agent-plugins` rather than `antigravity-plugin`. Either way the skill and one MCP server install; which file supplied the MCP server is the only thing that varies. **Without `mcp_config.json` the skill installs and the MCP server silently does not** — measured the same day: `agy plugin install` reported `skills: 1 installed` and nothing about `mcpServers` at all.

**The Agent Plugins spec deliberately says nothing about installation** — no registry, no install command, no URL scheme; §"Client-managed installation, distribution, enablement, updates, and user interface are outside the portable specification." What is portable is the *directory*, so distribution is the same git repo it already was, and each host keeps its own way in.

## Install — Claude Code

```sh
claude plugin marketplace add bowmark-ai/plugin
claude plugin install bowmark@bowmark-ai
```

## Install — Codex

```sh
codex plugin marketplace add bowmark-ai/plugin
codex /plugins            # open the plugin browser, then install Bowmark
```

## Install — Antigravity

```sh
agy plugin install https://github.com/bowmark-ai/plugin
```

## Install — an Agent Plugins client (ChatGPT, Cursor, Copilot, VS Code, Kiro, …)

There is no one command, because the spec defines no install path. Every host resolves a plugin from a **git repo or a local directory** and then reads the root `plugin.json`. Two shapes cover all of them:

```sh
# repo-level: anyone working in this checkout gets it
git clone https://github.com/bowmark-ai/plugin plugins/bowmark

# personal: the host's own plugin directory, e.g. Codex
git clone https://github.com/bowmark-ai/plugin ~/.codex/plugins/bowmark
```

Hosts with a marketplace UI (Cursor's Settings → Plugins → Team Marketplaces → Import from Repo, Codex's `/plugins` browser) point at `bowmark-ai/plugin` and read the manifests in-tree. **Cursor does not read the root `plugin.json`** — it reads `.cursor-plugin/plugin.json` first and never gets past `.claude-plugin/plugin.json` if that one is present; see the section below.

Any of the three routes gets you the skill + the MCP (tools `mcp__bowmark__get_library`, `mcp__bowmark__run`) and a card in the host's plugin directory.

Other surfaces are unchanged and live elsewhere: skill-only via `npx skills add bowmark-ai/skill` (works on Claude Code, Codex, Cursor, Copilot, OpenCode, …), MCP-only via `claude mcp add` / a Codex `[mcp_servers.bowmark]` block, or point any MCP client straight at the URL. See [bowmark.ai/#install](https://bowmark.ai/#install).

## Install in Kiro

In Kiro, open the **Powers** panel, choose **Add Custom Power**, then **Import power from GitHub**, and paste `https://github.com/bowmark-ai/plugin`. Kiro reads the root `plugin.json` and `mcp.json`, so you get the hosted Bowmark MCP server as a power.

## Privacy and support

- Privacy policy: [bowmark.ai/privacy](https://bowmark.ai/privacy)
- Support: [support@bowmark.ai](mailto:support@bowmark.ai)

## Layout

```
packages/plugin/
├── .claude-plugin/          # Claude Code
│   ├── marketplace.json     #   marketplace: bowmark-ai (source "./")
│   └── plugin.json          #   plugin: bowmark — inline mcpServers, skills
├── .codex-plugin/           # Codex
│   └── plugin.json          #   plugin: bowmark — mcpServers "./.mcp.json", skills "./skills/"
├── .cursor-plugin/          # Cursor — FIRST in Cursor's manifest lookup, and that is the point
│   └── plugin.json          #   plugin: bowmark — inline mcpServers ({url}), skills. NO $schema
├── .agents/plugins/
│   └── marketplace.json     # Codex marketplace (source {local, "./"})
├── .github/plugin/
│   └── marketplace.json     # GitHub Copilot's DEFAULT marketplace path — Copilot deprecated
│                            #   direct installs, so this is required, not convenient
├── .mcp.json                # MCP server config Codex's plugin.json references (HTTP, url)
├── plugin.json              # Agent Plugins 1.0.0 manifest — metadata ONLY, no component lists. ALSO read by Antigravity (no override directory for it)
├── mcp.json                 # Agent Plugins MCP config (streamable-http) — NOT the same file as .mcp.json
├── mcp_config.json          # Antigravity's own MCP config — `serverUrl`, read only while its enable-agent-plugins-spec flag is off
├── gemini-extension.json    # Gemini CLI extension — `httpUrl`, NOT `url`, and no bridge
├── skills/
│   └── bowmark/
│       └── SKILL.md         # MIRROR of packages/skill/bowmark/SKILL.md — do NOT edit here
├── package.json             # release-please component `plugin` (stripped from the mirror)
└── sync-skill.sh            # regenerates the skill mirror
```

**Four MCP declarations, four shapes, and none of them can be shared.** Claude declares it **inline** in `.claude-plugin/plugin.json`; Codex points its manifest at `.mcp.json` (`{ name: { url } }`); Agent Plugins reads the root `mcp.json` (`{ $schema, mcpServers: { name: { type: "streamable-http", url } } }` — `type` is REQUIRED and is `streamable-http`, not the `http` the other two spell it); Antigravity reads its own `mcp_config.json` (`{ mcpServers: { name: { serverUrl } } }` — `serverUrl`, confirmed against the real `agy` CLI; it does not accept `httpUrl` or `url`). **`mcp.json` and `.mcp.json` are different files for different hosts** and the leading dot is the only thing telling them apart, so read the path twice before editing either — `mcp_config.json` has no dotted twin to confuse it with.

`plugin.json` at the root carries **metadata only** — the schema is `additionalProperties: false` and has no `skills` or `mcpServers` field, unlike both sibling manifests. Components are found by convention (`skills/`, `mcp.json`), so there is nothing to keep in sync there and nothing to add when a skill is added.

### Cursor: `.cursor-plugin/` exists because Cursor reads `.claude-plugin/`, not the root

Cursor looks for a plugin manifest in this order and takes the first that exists:

```
.cursor-plugin/plugin.json  →  .claude-plugin/plugin.json  →  plugin.json
```

**`.claude-plugin/` is ahead of the root `plugin.json`.** So a repo carrying both hands Cursor
the Claude Code manifest, and the Agent Plugins manifest written for exactly this kind of host
is never read — despite Cursor's own docs pointing at it. Without `.cursor-plugin/`, Cursor
would install on `…/mcp/claude-code-plugin`: every Cursor user recorded as a Claude Code
install and served Claude Code's operating text. `sessions.source` is write-once, so that is
not recoverable afterwards.

Cursor also validates `$schema` against an allowlist of exactly **two** URLs —
`https://agent-plugins.org/schemas/1.0.0/plugin.schema.json` and its `mcp.schema.json`
sibling — plus **absent**. What it does with anything else changed under us mid-2026:

| Cursor | Unrecognized `$schema` |
|---|---|
| 3.15.19 | **throws out of the whole lookup.** No fall-through. Plugin shows as installed and contributes nothing; the only trace is `Cursor plugin load error …: Unsupported plugin manifest $schema version: …` in its own log |
| 3.17.19 | logs `declares an unrecognized $schema, loading anyway` and continues |

Two rules follow, and both are load-bearing:

- **Never add `$schema` to `.cursor-plugin/plugin.json`.** There is no published Cursor schema
  URL, and this file is not an Agent Plugins root manifest (it lists components; that one is
  metadata-only). Absent is the only value that is both correct and accepted.
- **`.cursor-plugin/plugin.json` must keep existing.** Deleting it does not degrade Cursor to
  the root manifest — it degrades Cursor to Claude Code's.

`mcpServers` here uses Cursor's own shape (`{ "url": … }`, no `type`), inline like Claude's.
Full reasoning and the log evidence: `docs/decisions/2026-08-24-cursor-plugin-manifest.md` in
Bowmark's internal engineering repo (not public).

**Each channel gets its own published destination** — `…/mcp/claude-code-plugin`, `…/mcp/codex-plugin`, `…/mcp/cursor-plugin`, `…/mcp/agent-plugins`, `…/mcp/antigravity-plugin`, never the bare `…/mcp`. One segment carries both the install attribution and the platform pin. The first three **pin** their platform because a host-specific manifest knows its host at install time; **`agent-plugins` and `antigravity-plugin` do not pin** — `agent-plugins` because the entire premise of the format is that six named hosts and anything else conformant read the same manifest, and `antigravity-plugin` because `antigravity` is not in the `Platform` union at all (same reasoning as `gemini-extension`). Keep all five distinct when editing: pointing two at one segment would hand one host the other's operating text. Detection and the segment list live in Bowmark's internal `apps/api/README.md` § Per-platform instructions (not public).

## The bundled skill is a mirror — edit canonical, then sync

`skills/bowmark/SKILL.md` mirrors `packages/skill/bowmark/SKILL.md`, the source of truth (minus its release-please version line — see `sync-skill.sh`). A plugin install needs the file in-tree, so it can't reference the separate skill package. **Never edit the copy directly.** After changing the canonical skill:

```sh
bash packages/plugin/sync-skill.sh           # copy canonical → plugin
bash packages/plugin/sync-skill.sh --check    # verify in sync (CI runs this)
```

CI fails any PR that changes the canonical skill without re-syncing.

## Versioning

release-please owns `package.json` `version` (component `plugin`, tag `plugin-v*`) and mirrors it into **all four** version-carrying manifests — `.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`, the root `plugin.json` and `gemini-extension.json` — at `$.version` via json updaters, so each release republishes the plugin at the new version on every host. **A new manifest means a new `extra-files` entry UNLESS it carries no version field** — miss one that does and that host serves a stale version forever with nothing failing. (The two `marketplace.json` files and `mcp_config.json` carry no version and need no entry — same shape as `mcp.json` and `.mcp.json`.) Ship changes under `feat(plugin):` / `fix(plugin):`.

## Validate

```sh
claude plugin validate packages/plugin     # Claude side has a local validator
```

There is no local `codex plugin validate`; the Codex manifests are built to the published spec ([developers.openai.com/codex/plugins](https://developers.openai.com/codex/plugins)) and confirmed on a real Codex install.

The Agent Plugins pair validates against the spec's own published JSON Schemas — the canonical copies live in [`agentplugins/agent-plugins-spec`](https://github.com/agentplugins/agent-plugins-spec) under `schemas/1.0.0/`, and both files were checked green against them (ajv, 2026-08-06). There is no CI gate for this: the schemas are fetched over the network and the fast gate is hermetic. Re-check by hand when either file changes.
