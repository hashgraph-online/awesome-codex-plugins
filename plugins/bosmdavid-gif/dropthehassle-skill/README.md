# DropTheHassle publish skill

An open [Agent Skill](https://agentskills.io) that teaches your coding agent to publish a **built
site or web app** with [DropTheHassle](https://dropthehassle.com): a free HTTPS
`yourname.dropthehassle.app` link with no account, card or DNS work, then a real domain when you
want one.

Task words it answers: **deploy website**, **buy domain**, **email on my domain**. Skills in
`skills/`: `publish-website`, `dropthehassle-publish`, `buy-domain`, `custom-domain`, `domain-email`.

Works in **Claude Code, Cursor, Codex and Windsurf**, and any other agent that reads `SKILL.md`
skills.

**Your AI can publish. It can never spend your money.** The skill tells the agent to search names
and hand you a payment link, never to buy.

## What the agent does with it

1. Checks the folder is a finished site (an `index.html` at the top), not source code, and runs the
   build first when it is (Vite, Astro, Next.js `output: 'export'`, Nuxt generate, Create React App,
   Lovable/Bolt exports). DropTheHassle serves the built files and never runs a server itself. A
   server app (SSR, API routes, server functions, a TanStack Start app) runs on AWS, Google Cloud,
   DigitalOcean or your own server and is connected with `set_backend` or the dashboard's Backend
   card: DropTheHassle then puts it behind the same link. A TanStack Start app (Lovable from
   13 May 2026) can also go online as an SPA build (`dist/client`), without its server
   functions and `/api` routes.
2. Runs a local preflight (`scripts/preflight.mjs`, no network, no dependencies) against the upload
   limits.
3. Sets up the DropTheHassle CLI (`npx -y dropthehassle@latest deploy . --email <the user's email>`; it asks you for
   your email first, never makes one up), the local MCP server
   (`npx -y dropthehassle-mcp`) or the hosted connector (`https://dropthehassle.com/mcp`).
4. Deploys, and gives you the live link plus the **claim link** (valid 7 days).
5. Checks the site is really live (the same check as
   [Is my website down?](https://dropthehassle.com/is-my-website-down)).
6. If you want your own name, checks which domains are really free and what they cost, and stops
   there until you say otherwise.

## Cursor

Install the DropTheHassle plugin from the Cursor Marketplace, or add only the MCP server.

One click: `cursor://anysphere.cursor-deeplink/mcp/install?name=dropthehassle&config=eyJ1cmwiOiJodHRwczovL2Ryb3B0aGVoYXNzbGUuY29tL21jcCJ9`

Or add to `mcp.json`:

```json
{ "mcpServers": { "dropthehassle": { "url": "https://dropthehassle.com/mcp" } } }
```

Then ask: "publish my site". No token needed.

## Install

Install the DropTheHassle skill in Claude Code, Cursor, Codex or Gemini CLI: `npx skills add bosmdavid-gif/dropthehassle-skill`

This repo has four skills. `npx skills add bosmdavid-gif/dropthehassle-skill` lists them all;
pick one or more.

| Skill | What it does |
| --- | --- |
| [`dropthehassle-publish`](skills/dropthehassle-publish) | Publish a built website or web app on a free HTTPS link: build, preflight, deploy, Update and Restore, claim link, live check. |
| [`buy-domain`](skills/buy-domain) | Find a free domain name with real availability and price, then hand you the payment link. You pay; the site goes live on it with no DNS. |
| [`custom-domain`](skills/custom-domain) | Connect a domain you already own to your site, free, with one A record you set at your registrar. |
| [`domain-email`](skills/domain-email) | Turn on a mailbox such as hello@yourdomain.com (€5 / $5 a month). You pay the link. |

Install them with the open [skills CLI](https://github.com/vercel-labs/skills), as a Claude Code
plugin, or by copying the folders.

### Any agent (skills CLI)

```bash
npx skills add bosmdavid-gif/dropthehassle-skill
```

Pick your agents in the prompt, or name them (`-g` installs for every project):

```bash
npx skills add bosmdavid-gif/dropthehassle-skill --skill dropthehassle-publish -g -a claude-code -a cursor -a codex -a windsurf -y
```

Update later with `npx skills update dropthehassle-publish -g -y`.

### Claude Code

As a plugin, inside Claude Code:

```
/plugin marketplace add bosmdavid-gif/dropthehassle-skill
/plugin install dropthehassle@dropthehassle
```

Or copy the folder:

```bash
git clone https://github.com/bosmdavid-gif/dropthehassle-skill.git
mkdir -p ~/.claude/skills
cp -r dropthehassle-skill/skills/dropthehassle-publish ~/.claude/skills/
```

Use `.claude/skills/` inside a project instead to share it with the repo. Claude picks the skill up
by itself when you ask to publish a site, or call it with `/dropthehassle-publish`
(`/dropthehassle:dropthehassle-publish` when installed as a plugin).

### Cursor

```bash
npx skills add bosmdavid-gif/dropthehassle-skill --skill dropthehassle-publish -a cursor
```

Or copy `skills/dropthehassle-publish` to `.cursor/skills/` (this project) or `~/.cursor/skills/`
(every project). Cursor also reads `.agents/skills/` and `.claude/skills/`. Type `/` in Agent chat
to call it by name.

### Codex

```bash
npx skills add bosmdavid-gif/dropthehassle-skill --skill dropthehassle-publish -a codex
```

Or copy `skills/dropthehassle-publish` to `.agents/skills/` in the repo, or `~/.agents/skills/` for
every repo. Call it with `$dropthehassle-publish`, or let Codex pick it. Codex keeps the network
off in its sandbox by default: approve the deploy command when it asks, or see
[the Codex guide](https://dropthehassle.com/guides/codex-deploy-custom-domain).

### Windsurf

```bash
npx skills add bosmdavid-gif/dropthehassle-skill --skill dropthehassle-publish -a windsurf
```

Or copy `skills/dropthehassle-publish` to `.windsurf/skills/` (this workspace) or
`~/.codeium/windsurf/skills/` (every workspace). Windsurf also reads `.agents/skills/` and
`~/.agents/skills/`. Call it with `@dropthehassle-publish`, or let Cascade pick it.

### Without skills support

Paste the contents of
[`skills/dropthehassle-publish/SKILL.md`](skills/dropthehassle-publish/SKILL.md) into your
project's `AGENTS.md` or `CLAUDE.md`, or point your AI at https://dropthehassle.com/llms.txt.

## Connect DropTheHassle (optional, for the MCP tools)

The CLI needs nothing set up. To give the agent the MCP tools too:

```bash
claude mcp add dropthehassle -- npx -y dropthehassle-mcp           # Claude Code
codex mcp add dropthehassle --url https://dropthehassle.com/mcp     # Codex
```

Cursor (`.cursor/mcp.json`), Windsurf (`.devin/mcp_config.local.json`) and others:

```json
{
  "mcpServers": {
    "dropthehassle": { "command": "npx", "args": ["-y", "dropthehassle-mcp"] }
  }
}
```

A first deploy needs no token. Account tools (your sites, renaming a link, payment links) need the
token from dropthehassle.com, menu, **Connect your AI**, set as `DTH_TOKEN`. Don't commit it. Full
setup per tool: [references/setup.md](skills/dropthehassle-publish/references/setup.md) and
[the MCP guide](https://dropthehassle.com/guides/deploy-with-your-ai-mcp).

## Try it

Open a folder with a finished site, or a project that builds to one, and ask:

> Publish this site with DropTheHassle and give me the link.

You should see the agent check or build the folder, run the preflight, deploy, and come back with
a `….dropthehassle.app` link, a claim link, and a live check. Then try:

> Is there a free .com for this?

It should list names with prices from a real search, and not create a payment link until you ask.

## What's in the box

```
skills/buy-domain/SKILL.md          # find a free name, hand over the payment link
skills/custom-domain/SKILL.md       # connect a domain you already own (one A record)
skills/domain-email/SKILL.md        # mailbox on your domain, human pays
skills/dropthehassle-publish/
├── SKILL.md                    # the workflow the agent follows
├── references/
│   ├── setup.md                # CLI, MCP and hosted connector setup per tool
│   ├── domains.md              # search, buying (human pays), own domain, renaming the link
│   └── troubleshooting.md      # every deploy answer and what to do, TanStack/Lovable
└── scripts/
    └── preflight.mjs           # local check: finished site? within the limits?
.claude-plugin/                 # Claude Code plugin + marketplace manifest
```

Run the preflight yourself:

```bash
node skills/dropthehassle-publish/scripts/preflight.mjs ./my-site
```

## Facts this skill is based on

Everything in the skill was checked on 2026-10-01 against the published packages
(`dropthehassle` CLI 0.3.0, `dropthehassle-mcp` 0.4.2 on npm), the hosted MCP server at
`https://dropthehassle.com/mcp`, and https://dropthehassle.com/llms.txt. When those change, the
tools' own messages win. Found something out of date? Open an issue.

## Links

- DropTheHassle: https://dropthehassle.com
- llms.txt: https://dropthehassle.com/llms.txt
- MCP server: https://github.com/bosmdavid-gif/dropthehassle-mcp ([npm](https://www.npmjs.com/package/dropthehassle-mcp))
- CLI: [npm `dropthehassle`](https://www.npmjs.com/package/dropthehassle)
- Guides: [publish AI-built HTML](https://dropthehassle.com/guides/put-ai-html-online),
  [Claude Code](https://dropthehassle.com/guides/claude-code-website-online),
  [Cursor](https://dropthehassle.com/guides/cursor-site-own-domain),
  [Codex](https://dropthehassle.com/guides/codex-deploy-custom-domain),
  [Windsurf](https://dropthehassle.com/guides/windsurf-deploy-custom-domain)

## Privacy and support

- Privacy: https://dropthehassle.com/privacy
- Terms: https://dropthehassle.com/terms
- Support: https://dropthehassle.com/support or info@dropthehassle.com

## License

MIT. See [LICENSE](LICENSE).
