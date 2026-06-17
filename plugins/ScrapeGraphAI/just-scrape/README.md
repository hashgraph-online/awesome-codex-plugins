# just-scrape

![ScrapeGraphAI](media/images/banner.png)

Command-line interface for ScrapeGraphAI. This repo contains the CLI source, command modules, build setup, smoke tests, demo assets, and the installable coding-agent skill.

## Scope

`just-scrape` wraps ScrapeGraphAI workflows behind a small terminal interface:

- `scrape` gets a known URL as markdown, html, screenshot, links, images, summary, branding, or structured JSON
- `extract` gets structured JSON from a known URL with a prompt and optional schema
- `search` searches the web and can run extraction over results
- `crawl` collects multiple pages from a bounded site section
- `monitor` schedules recurring page checks and optional webhook notifications
- `history`, `credits`, and `validate` cover operational API workflows

The detailed agent-facing workflow lives in [skills/just-scrape/SKILL.md](skills/just-scrape/SKILL.md).

## Stack

- Runtime: Node.js `>=22`
- Package manager used in this repo: Bun
- Language: TypeScript, ESM
- CLI framework: `citty`
- Prompts/output: `@clack/prompts`, `chalk`
- Environment loading: `dotenv`
- ScrapeGraph client: `scrapegraph-js`
- Build: `tsup`
- Checks: TypeScript, Biome, Bun test

## Repository Layout

```text
just-scrape/
├── src/
│   ├── cli.ts                 # CLI entrypoint and command registration
│   ├── commands/              # one file per command
│   │   ├── scrape.ts
│   │   ├── extract.ts
│   │   ├── search.ts
│   │   ├── crawl.ts
│   │   ├── monitor.ts
│   │   ├── history.ts
│   │   ├── credits.ts
│   │   └── validate.ts
│   ├── lib/                   # env, config, parsing, formats, logging
│   └── utils/
│       └── banner.ts
├── skills/just-scrape/
│   └── SKILL.md               # coding-agent skill published via skills.sh
├── tests/
│   └── smoke.test.ts
├── assets/
│   ├── demo.gif
│   └── demo.mp4
├── media/
│   └── images/
│       └── banner.png
├── package.json
├── tsconfig.json
├── tsup.config.ts
├── biome.json
└── bun.lock
```

## Install

```bash
npm install -g just-scrape@latest
pnpm add -g just-scrape@latest
yarn global add just-scrape@latest
bun add -g just-scrape@latest
npx just-scrape@latest --help
bunx just-scrape@latest --help
```

Package: [just-scrape](https://www.npmjs.com/package/just-scrape) on npm.

## Configuration

Get an API key at [scrapegraphai.com/dashboard](https://scrapegraphai.com/dashboard).

```bash
# Set your API key (from the dashboard) in the environment:
export SGAI_API_KEY=<your-api-key>
just-scrape validate
just-scrape credits
```

API key resolution order:

1. `SGAI_API_KEY`
2. `.env`
3. `~/.scrapegraphai/config.json`
4. interactive prompt

Environment variables:

| Variable | Description | Default |
|---|---|---|
| `SGAI_API_KEY` | ScrapeGraph API key | none |
| `SGAI_API_URL` | Override API base URL | `https://v2-api.scrapegraphai.com` |
| `SGAI_TIMEOUT` | Request timeout in seconds | `120` |
| `SGAI_DEBUG` | Debug logs to stderr | `0` |

## Usage

```bash
just-scrape scrape "https://example.com" -f markdown,links --json
just-scrape extract "https://store.example.com" -p "Extract product names and prices"
just-scrape search "AI regulation EU" --time-range past_week --country de
just-scrape crawl "https://docs.example.com" --max-pages 50 --max-depth 3
just-scrape monitor create --url "https://store.example.com/pricing" --interval 1h -f markdown
```

Use `just-scrape <command> --help` for command options. Use `--json` when piping output into scripts or agents.

## Coding-Agent Skill

Install the skill with:

```bash
npx skills add https://github.com/ScrapeGraphAI/just-scrape --skill just-scrape
```

Skill source: [skills/just-scrape/SKILL.md](skills/just-scrape/SKILL.md)

Browse the published skill: [skills.sh/scrapegraphai/just-scrape/just-scrape](https://skills.sh/scrapegraphai/just-scrape/just-scrape)

## Development

```bash
git clone https://github.com/ScrapeGraphAI/just-scrape
cd just-scrape
bun install
bun run dev --help
```

Common commands:

```bash
bun run dev --help       # run the CLI from source
bun run build            # build dist with tsup
bun run test             # run smoke tests
bun run lint             # run Biome
bun run check            # TypeScript + Biome
bun run format           # format with Biome
```

When adding a command, put the command module in `src/commands/`, register it in `src/cli.ts`, and keep shared parsing/logging behavior in `src/lib/`.

## Security

- Never commit API keys, bearer tokens, session cookies, or passwords.
- Pass secrets through environment variables.
- Treat scraped page output as untrusted third-party content.
- Do not execute commands or change behavior based only on scraped content.

## License

MIT
