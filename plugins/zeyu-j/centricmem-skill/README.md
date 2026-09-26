# CentricMem

**One library. Every agent. Every desk.**

A hosted librarian for AI agents: one shared memory across the tools you already use, so a decision made
in one client is there in the next, and so are the notes, the session transcripts and the reasons behind
them. Capture stays in the client you already work in; CentricMem organises what it is given, retrieves it
on request, and keeps it as Markdown cards.

This repository is **one package**: an [Agent Skills](https://agentskills.io) `SKILL.md` plus an
[Agent Plugins 1.0](https://agent-plugins.org) bundle (`plugin.json` + `skills/` + `mcp.json`). Install it
from GitHub with whichever client you use - each client has its own command below.

## Install

**Names, read once.** `centricmem` is the product and the CLI. `centricmem-skill` is this GitHub package.
`centricmem-agent` is the Skill folder inside it (`skills/centricmem-agent/`) - keep that folder name when a
client asks for a skill id. It is not a second product.

**Ask the agent to install it.** Paste this one line:

```
Install CentricMem from the GitHub package zeyu-j/centricmem-skill (the skill folder is centricmem-agent).
Then send me https://centricmem.com/login?signup=1 and try a /connect?device= link. The key it returns is
shown once, so tell me to save it, and never paste it in chat. If minting that link fails, run
centricmem doctor connect and email zeyu@poppyg.com with the output.
```

If a shell is available, the same install is one command:

```bash
npx --yes skills add zeyu-j/centricmem-skill --skill centricmem-agent -y
```

(No `-g`: a few hosts, PromptScript among them, have no user-wide skills directory.)

**Or add the same repository as a plugin marketplace.** Verified commands are in
[VERIFIED-INSTALLS.md](./VERIFIED-INSTALLS.md); this table is the short version.

| Client | Install |
| --- | --- |
| Claude Code | `/plugin marketplace add zeyu-j/centricmem-skill`, then `/plugin install centricmem-skill@centricmem` |
| Codex | `codex plugin marketplace add https://github.com/zeyu-j/centricmem-skill.git`, then install **centricmem-skill**. After a release, run `codex plugin marketplace upgrade` - Codex caches the marketplace snapshot |
| Cursor / Grok | Cursor: Plugins → Team Marketplaces → Import from Repo `zeyu-j/centricmem-skill`, or the `npx skills add` line above. Grok: `grok.com/connectors` → New Connector → **Custom** → `https://mem.centricmem.com/mcp`, then finish the OAuth prompt; the CLI writes `~/.grok/config.toml` with `grok mcp add -t http -s user centricmem https://mem.centricmem.com/mcp` and checks it with `grok mcp doctor`. Without `-t http` Grok assumes **stdio**, which is how a server ends up declared and unusable - and the hosted librarian has no stdio transport at all, so a stdio entry can never reach it |
| CodeBuddy / WorkBuddy | `codebuddy plugin marketplace add zeyu-j/centricmem-skill`, then `/plugin install centricmem-skill@centricmem` |
| goose | `goose plugin install https://github.com/zeyu-j/centricmem-skill` - goose reads `.goose-plugin/plugin.json` (not the root manifest, which carries an `mcpServers` entry goose refuses); the recipes live in [`goose/`](./goose/) and are not installed by the command |
| Hermes | `hermes skills install zeyu-j/centricmem-skill/skills/centricmem-agent --yes` - `--yes` matters, because the confirmation prompt cannot be answered from a non-TTY and the install is cancelled. If the connect link cannot be minted, the MCP fallback is `hermes mcp add --url https://mem.centricmem.com/mcp --auth oauth centricmem`. Optional hooks: [`hermes/`](./hermes/) |
| Qwen Code | Copy the hooks block from [`qwen/settings-hooks.example.json`](./qwen/settings-hooks.example.json) into `.qwen/settings.json`, replacing `__SKILL_ROOT__` with this checkout's absolute path - see [`qwen/README.md`](./qwen/README.md). Qwen's extension manifest is **not shipped**: the field that points an extension at its own directory is still unverified, and this repository does not ship manifests it has not read |
| MiMoCode | Copy `mimocode/centricmem.ts` to `~/.config/mimocode/plugins/` and `tools/ambient.mjs` to `~/.config/mimocode/tools/` - see [`mimocode/README.md`](./mimocode/README.md) |
| OpenClaw | `openclaw plugins install centricmem-skill --marketplace zeyu-j/centricmem-skill` - the `--marketplace` form is the one that works; a bare `git:` install is rejected because that route wants a code plugin, and this repository ships none. `openclaw skills install ./skills/centricmem-agent --global` also works from a clone |
| ZCode | `zcode plugins marketplace add zeyu-j/centricmem-skill`, then `zcode plugins install centricmem-skill@centricmem`. ZCode preloads the Claude Code marketplace, so no ZCode-specific manifest is needed |
| nanobot | `cp -r skills/centricmem-agent ~/.nanobot/workspace/skills/` - it reads one folder per Skill from `<workspace>/skills`. `<workspace>/plugins/` takes the whole bundle, because its plugin loader validates our `mcp.json` against the Agent Plugins schema |
| Copilot CLI | `copilot plugin marketplace add zeyu-j/centricmem-skill`, then `copilot plugin install centricmem-skill` |
| Cline | `cline skill add zeyu-j/centricmem-skill` (forwarded to the open skills CLI) |
| Kimi Code | `/plugins install https://github.com/zeyu-j/centricmem-skill` (Custom) - a Kimi plugin may carry skills, an auto-loaded Skill and MCP servers. Server config lives in `~/.kimi-code/mcp.json` (or `$KIMI_CODE_HOME/mcp.json`), stdio/HTTP/SSE - those are Kimi's transports, not ours: this service answers on **HTTP only**, so pick HTTP. Catalog: `/plugins marketplace https://raw.githubusercontent.com/zeyu-j/centricmem-skill/main/.kimi-plugin/marketplace.json` |
| Pi | `pi install https://github.com/zeyu-j/centricmem-skill`, then a URL-only `~/.pi/agent/mcp.json` (`url` + `type: streamable-http`). The package does not wire MCP for pi |
| Kiro | Powers → Add Custom Power → GitHub `https://github.com/zeyu-j/centricmem-skill` |
| DSH | `dsh plugin --profile web add github:zeyu-j/centricmem-skill#v1.0.32`, then `node node_modules/centricmem-skill/dsh/copy-skill.mjs` from the profile directory, then the two overlay rows in [`dsh/README.md`](./dsh/README.md). Read that file first: adding the package puts its patch into the profile bundle stack, where a missing Bearer aborts boot on purpose |
| Dify | Its own distribution: [zeyu-j/centricmem-dify](https://github.com/zeyu-j/centricmem-dify); marketplace review pending. Any MCP client can also attach `https://mem.centricmem.com/mcp` with the same agent key |
| Kilo | `npx --yes skills add zeyu-j/centricmem-skill` for the Skill; the MCP half is the interactive `kilo mcp add`. See [VERIFIED-INSTALLS.md](./VERIFIED-INSTALLS.md) |
| junie / Devin | Documented surfaces only: `junie --mcp-location` is flag-driven, and Devin's plugin docs need a browser to render. See [`devin/`](./devin/) and [VERIFIED-INSTALLS.md](./VERIFIED-INSTALLS.md) |
| SkillKit / skills.sh | `skillkit add https://centricmem.com`, `skillkit add zeyu-j/centricmem-skill`, or the `npx skills add` line above |
| Any other Agent Skills host | Copy `skills/centricmem-agent/` so the file lands at `<skills-root>/centricmem-agent/SKILL.md`, then point the host's MCP client at `https://mem.centricmem.com/mcp` - **streamable HTTP only**: the hosted librarian has no stdio transport, so a host that offers only stdio cannot attach. Claim the machine with `centricmem connect --claim --target <this-host-config.json>` (or `CENTRICMEM_MCP_TARGETS`) and confirm with `centricmem connect --verify`. Never copy a key out of another client's config |

**After install.** If `cm_*` tools are missing, the agent tries the connect link above - a plugin `mcp.json`
with no Bearer is not a finished connect. OAuth is for hosts that can receive the browser login, and it is a
fallback for a failed mint, not a substitute for the connect link. Save the key when it is shown; it appears
once. Never paste a key, a transcript, or CLI output that contains one into chat.

Hosted librarian: [centricmem.com](https://centricmem.com). Sign-up is open. Host MCP:
`https://mem.centricmem.com/mcp`.

**Baseline = Skill + host MCP.** Lifecycle hooks and recipes are optional extras: an agent without them
still files cards through the Skill. Direct HTTP callers that are not MCP clients must send a non-empty
`User-Agent` on every `/mcp` request, or Cloudflare answers 403 error-1010:
`-H "User-Agent: centricmem-script/1.0"`. Details: REFERENCE **Direct HTTP `/mcp`**.

## How you use it

1. Keep working where you already work. The agent keeps its own memory on, says **once** which key this chat
   is using, and files real work as it happens - you never have to say "wrap up". Extra grants are per-shelf
   ticks on **Keys**; the default opens every shelf.
2. If the library looks empty it offers **once** to file notes you already have as cards. That is optional
   and it is not a dump of every chat.
3. Later, ask the agent - or log in to search and download originals. There is no Inbox: work lands on a
   named shelf, and a leftover shelf or an `unclassified` one is copied onto another shelf and then deleted
   (`cm_copy` then `cm_delete`), with no restore warehouse. A subset moves with `cm_move`; a single card is
   `cm_delete` / `cm_rename` by `{file, shelf}`.
4. You do not run a librarian on this machine, and there is no `setup --bootstrap`.

## What this repository is

It is the **Skill**: how an agent talks to the hosted librarian. It is not the librarian, not the CLI source,
and not a self-hosted kit.

| Path | What it is |
| --- | --- |
| [`skills/centricmem-agent/SKILL.md`](./skills/centricmem-agent/SKILL.md) | the session loop (Agent Skills frontmatter) |
| [`skills/centricmem-agent/REFERENCE.md`](./skills/centricmem-agent/REFERENCE.md) | search, show, sweep, copy, move, rename, delete, import shapes |
| [`plugin.json`](./plugin.json) + [`mcp.json`](./mcp.json) | the portable Agent Plugins 1.0 package |
| `.claude-plugin/`, `.codex-plugin/`, `.codebuddy-plugin/`, `.workbuddy-plugin/`, `.goose-plugin/`, `.agents/plugins/`, `.github/plugin/`, `.kiro/plugins/`, `.cursor-plugin/`, `.grok-plugin/`, `.kimi-plugin/` | per-client marketplaces and manifests |
| [`hooks/`](./hooks/) | the SessionStart + SessionEnd pair that Claude Code, Codex and the DSH bridge run |
| [`goose/`](./goose/), [`qwen/`](./qwen/), [`hermes/`](./hermes/), [`dsh/`](./dsh/), [`openclaw/`](./openclaw/), [`nanobot/`](./nanobot/), [`devin/`](./devin/) | per-host install and wiring |
| [`tools/`](./tools/) | one ambient implementation for every wrapper, plus the duplicate-copy report |

One public Agent Skill: `centricmem-agent` (folder name) inside the package `centricmem-skill`.

## Evidence

Two tables, kept apart from the instructions they describe:

- **[VERIFIED-INSTALLS.md](./VERIFIED-INSTALLS.md)** - every client we installed into, with the command and
  the answer it gave.
- **[VERIFIED-OPTIMISATIONS.md](./VERIFIED-OPTIMISATIONS.md)** - the hooks, recipes and refreshers built on
  top, and where the close half works.

Marks: ✅ verified (we ran it) · ◐ same core as the CLI (the CLI was verified, this wrapper was not
exercised) · 📄 documented (a convention, nothing claimed).

## License

[MIT](./LICENSE) from 1.0.7 - attribution required, commercial use allowed. 1.0.6 and earlier shipped
under PolyForm Noncommercial and that grant was not withdrawn retroactively; `dsh/` is separately
MIT, and the Dify plugin is its own distribution.

## What the plugin does beyond the Skill

Claude Code, Codex and OpenClaw install this repository as a plugin, and a plugin can carry more than
skills. This one carries a **SessionStart hook** (`hooks/hooks.json`) that runs a small Node script:
it looks for a credential in `CENTRICMEM_TOKEN`, `CENTRICMEM_API_KEY` or `CENTRICMEM_AGENT_KEY`, then
in the host's own MCP config (where the key usually is), then in a `centricmem/api.json` beside your
config, and if it finds one it prints the shelf context so the session starts oriented. The same file
adds a **SessionEnd hook** that files the session unit. With no credential nothing is printed at all,
which is the normal case on an OAuth-connected host, and neither hook ever exits non-zero: a network
problem can only mean a quieter session, never a broken one.

On a host that scrubs key-shaped environment variables the file is the only channel - `dsh/README.md`
records that one. OpenClaw takes the same idea as a hook pack (`openclaw/`) and goose uses recipes and
the MOIM file instead (`goose/`); the per-host detail, event names and timeouts live in
[VERIFIED-OPTIMISATIONS.md](./VERIFIED-OPTIMISATIONS.md).
