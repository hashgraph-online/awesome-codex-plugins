# CentricMem

**One library. Every agent. Every desk.**

A hosted librarian for AI agents. Capture stays in the agent you already use. CentricMem organises and retrieves — Cursor, Claude Code, Codex, Hermes, Pi, OpenClaw, DSH, Copilot, Kiro, Kilo, CodeBuddy, Kimi Code, and the next one share the same shelf.

This repository is **one package**: [Agent Skills](https://agentskills.io) `SKILL.md` plus an [Agent Plugins 1.0](https://agent-plugins.org) bundle (`plugin.json` + `skills/` + `mcp.json`). Install it once from GitHub; each client uses its own command. Do not paste keys or marketplace JSON into chat.

## Install

**Names (read once):** `centricmem` = product / CLI. `centricmem-skill` = this GitHub package (plugins + marketplace). `centricmem-agent` = the Agent Skill folder inside the package (`skills/centricmem-agent/`). Humans can say “CentricMem skill”; keep `--skill centricmem-agent` and that folder name.

Paste this to the agent (one line):

```
Install CentricMem from zeyu-j/centricmem-skill (GitHub package). The Agent Skill folder name is centricmem-agent — not a second product. After install, this agent (and each client you install into) sends https://centricmem.com/login?signup=1 and tries a /connect?device= URL — plugin mcp.json or mcp add with no Bearer is not a completed connect. If minting that URL fails, run centricmem doctor connect and they email zeyu@poppyg.com with that output (never a key); then MCP OAuth only if this agent will receive the browser login (Grok Bot and Manus may; a 127.0.0.1 callback does not when this agent is not listening there). If they already have a key or a finished OAuth login in this agent, ask for a new chat — do not strip Bearer, do not mint a new connect URL. Tell them the key appears only once — save a backup; never paste keys. If connect or usage still fails, they email zeyu@poppyg.com (never a key).
```

If the shell works, a terminal in the project can run:

```bash
# package = centricmem-skill; skill folder = centricmem-agent
npx --yes skills add zeyu-j/centricmem-skill --skill centricmem-agent -y
```

(omit `-g` — some agents, including PromptScript, have no user-wide skills dir.)

Same GitHub repo as a plugin marketplace:

| Client | Add this repo, then install |
| --- | --- |
| Cursor | Plugins → Team Marketplaces → Import from Repo `zeyu-j/centricmem-skill`, or `npx skills add` above |
| Claude Code | `/plugin marketplace add zeyu-j/centricmem-skill` then `/plugin install centricmem-skill@centricmem` |
| CodeBuddy / WorkBuddy | `codebuddy plugin marketplace add zeyu-j/centricmem-skill` then `/plugin install centricmem-skill@centricmem` |
| Kimi Code | `/plugins install https://github.com/zeyu-j/centricmem-skill` (Custom). Catalog: `/plugins marketplace https://raw.githubusercontent.com/zeyu-j/centricmem-skill/main/.kimi-plugin/marketplace.json`. Set `CENTRICMEM_API_KEY` for host MCP. |
| Dify | Marketplace listing pending review. Source: `zeyu-j/centricmem-dify`. Or attach MCP `https://mem.centricmem.com/mcp` with the same agent key. |
| Codex | Every agent tries `/connect?device=` first. Plugin: `codex plugin marketplace add https://github.com/zeyu-j/centricmem-skill.git` then install **centricmem-skill**. `codex mcp login` only after that mint fails, and only if this Codex will receive the Loopback callback |
| Hermes | `hermes skills install zeyu-j/centricmem-skill/skills/centricmem-agent`. Mint `/connect?device=` first. Local `hermes mcp add --url https://mem.centricmem.com/mcp --auth oauth centricmem` only after that mint fails if this Hermes will receive the browser login. |
| Pi | `pi install https://github.com/zeyu-j/centricmem-skill`. Then URL-only `~/.pi/agent/mcp.json` (`url` + `type: streamable-http`). MCP is not auto-wired by the package. |
| OpenClaw | Compatible **bundle** (Agent Plugins / Claude / Codex / Cursor). Not ClawHub. `openclaw plugins install git:github.com/zeyu-j/centricmem-skill` or `openclaw plugins install centricmem-skill --marketplace zeyu-j/centricmem-skill`. Do not add `openclaw.plugin.json`. |
| DSH | Cordis **funnel** only. Needs `pnpm` (`npm i -g pnpm` if missing). Pin: `dsh plugin --profile web add github:zeyu-j/centricmem-skill#v0.21.72`. Then from the profile dir run `node node_modules/centricmem-skill/dsh/copy-skill.mjs` so `$DSH_HOME/skills/centricmem-agent` exists (funnel MCP does not load Skill from `node_modules`). Overlay Bearer on the same `id` in `$DSH_HOME/profiles/<profile>/cordis.patch.yml` (restate the whole config). New chat. Tools are `mcp__centricmem__cm_*`. Skill stays PolyForm; [`dsh/`](./dsh/) is MIT glue. GitHub topic `dsh-plugin`. |
| Copilot CLI | `copilot plugin marketplace add zeyu-j/centricmem-skill` then `copilot plugin install centricmem-skill` |
| Kiro | Powers → Add Custom Power → GitHub `https://github.com/zeyu-j/centricmem-skill` |
| Grok Bot | Paste the one-liner. Shell is blocked, so send signup only; add `https://mem.centricmem.com/mcp` in that bot’s MCP settings (key from Keys, never in chat). |
| SkillKit | `skillkit add https://centricmem.com` or `skillkit add zeyu-j/centricmem-skill` |
| Any other Agent Skills host | Copy `skills/centricmem-agent/` so the file is `<skills-root>/centricmem-agent/SKILL.md`. Host MCP is streamable-HTTP at `https://mem.centricmem.com/mcp`. After device claim: `centricmem connect --claim --target <this-host-config.json>` (or `CENTRICMEM_MCP_TARGETS`). Confirm with `centricmem connect --verify`. Do not copy a key from another client's `mcp.json`. |
| skills.sh / SkillMD | `npx skills add` above, or `skillmd add zeyu-j/centricmem-skill` |

Then keep talking. After install, if `cm_*` tools are missing this agent (and each client you install into) sends signup **and** tries a `/connect?device=` link. Plugin `mcp.json` is not a completed connect. If minting that URL fails, run centricmem doctor connect and they email zeyu@poppyg.com with that output; then OAuth only if this agent will receive the browser login (Grok Bot / Manus may). Do not skip the connect URL because OAuth exists. WorkBuddy/CodeBuddy try the connect URL too. Do not download a settings file that contains a key. The agent tells you to save a backup of the key (it appears only once). You do not paste chats, tokens, or CLI.

Hosted librarian: [centricmem.com](https://centricmem.com). Sign up is open. Host MCP: `https://mem.centricmem.com/mcp`. Never paste keys in chat.

**Baseline = Skill + host MCP.** Plugin-tree hosts: refresh the loaded plugin with the host's own install tool (`install_source`-style, full URL `https://github.com/zeyu-j/centricmem-skill`, `kind: plugin`; see Skill REFERENCE). Lifecycle hooks (`AGENTS.md`, Stop remind, session-sweep scripts) are **optional** — agents without hooks (e.g. DSH) still file via Skill §4. Opening optional hooks is not part of public install; see Skill `REFERENCE.md` → Optional host hooks.

**Direct HTTP scripts** (not an MCP client): every request to `/mcp` **must** include a non-empty `User-Agent` header, or Cloudflare returns 403 error-1010. Example: `-H "User-Agent: centricmem-script/1.0"`. See Skill `REFERENCE.md` → Direct HTTP `/mcp`.

## How you use it

1. Keep talking where you already work. The agent’s own memories stay on. It says **once** which key this chat is using. Extra grants: tick shelves on **Keys**. Default opens every shelf.
2. If the library looks empty, the agent offers **once** to file notes you already have as cards. Capture stays. You may skip. It is not a dump of every chat.
3. When work is real, the agent files a Markdown card and keeps this chat’s transcript in object storage — you do not have to say wrap up. Closing the tab does not file; it files before it stops. Ask it to keep a file and write a card; a folder of originals is one import. Archive zip on the website is optional if you already packed one. If your Skill is behind this repo, the agent refreshes it with `npx skills add` (the current chat still uses the old copy). Plugin installs update via that client’s plugin UI.
4. Later, ask the agent — or log in to search and download originals. There is no Inbox: file into a named shelf. Leftover shelves (including leftover `unclassified`): the agent copies onto another shelf (`cm_copy`) then **deletes** the old one (`cm_delete`) — it does not download originals to this computer, and there is no restore warehouse. To move a **subset** of cards, the agent uses `cm_move` (default key). To delete or rename one card, `cm_delete` / `cm_rename` `{file, shelf}`. Extra keys cannot.

You do not run a librarian on this machine. You do not `setup --bootstrap`.

## What this repo is

This repository is the **Skill**: how agents talk to the hosted librarian.

- [`skills/centricmem-agent/SKILL.md`](./skills/centricmem-agent/SKILL.md) — session loop ([Agent Skills](https://agentskills.io/specification) frontmatter)
- [`skills/centricmem-agent/REFERENCE.md`](./skills/centricmem-agent/REFERENCE.md) — search, show, sweep, copy, move selected cards, rename a card title, delete leftover shelves or a card
- [`plugin.json`](./plugin.json) + [`mcp.json`](./mcp.json) — portable Agent Plugins 1.0 package
- [`.cursor-plugin/marketplace.json`](./.cursor-plugin/marketplace.json) — Cursor team marketplace
- [`.claude-plugin/marketplace.json`](./.claude-plugin/marketplace.json) — Claude Code marketplace
- [`.codebuddy-plugin/marketplace.json`](./.codebuddy-plugin/marketplace.json) — CodeBuddy / WorkBuddy marketplace (`codebuddy plugin marketplace add zeyu-j/centricmem-skill`)
- [`.kimi-plugin/plugin.json`](./.kimi-plugin/plugin.json) — Kimi Code Custom install from this GitHub URL
- Dify is a separate tool plugin: [zeyu-j/centricmem-dify](https://github.com/zeyu-j/centricmem-dify) (not this Skill repo)
- [`.agents/plugins/marketplace.json`](./.agents/plugins/marketplace.json) — Codex marketplace
- [`.github/plugin/marketplace.json`](./.github/plugin/marketplace.json) — Copilot CLI marketplace
- [`.kiro/plugins/marketplace.json`](./.kiro/plugins/marketplace.json) — Kiro pin-sync catalog
- [`dsh/cordis.patch.yml`](./dsh/cordis.patch.yml) — DSH Cordis funnel (MIT glue, URL-only MCP, `failOnStartupError: true`). [`dsh/copy-skill.mjs`](./dsh/copy-skill.mjs) copies the Skill into `$DSH_HOME/skills/`. Skill stays PolyForm. Not ClawHub.

It is not the librarian, not the CLI source, and not a self-hosted kit. One public Agent Skill: `centricmem-agent` (folder name) inside package `centricmem-skill`.

## License

[PolyForm Noncommercial 1.0.0](./LICENSE) — attribution required; no commercial use. The Cordis patch in [`dsh/`](./dsh/) is separately [MIT](./dsh/LICENSE) so DSH can mount the hosted MCP client. That does **not** relicense `SKILL.md`.
