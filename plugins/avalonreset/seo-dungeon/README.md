<p align="center">
  <a href="assets/banner.webp"><img src="assets/banner.webp" alt="SEO Dungeon - Gamified SEO Audit Tool" width="100%"></a>
</p>

# SEO Dungeon - AI SEO Audits as Dungeon Battles

[![CI](https://github.com/avalonreset/seo-dungeon/actions/workflows/ci.yml/badge.svg)](https://github.com/avalonreset/seo-dungeon/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Version](https://img.shields.io/badge/version-2.2-blue)](CHANGELOG.md)
[![Runtime](https://img.shields.io/badge/runtime-Codex%20%7C%20Claude%20%7C%20Gemini-2ea44f)](dungeon/)

SEO Dungeon turns SEO audits into a 16-bit dungeon crawler. Enter a domain,
inspect the issues as demons, and use a local AI CLI to analyze or fix them
inside your project. The packaged bridge selects Codex by default and also
supports Claude Code and Gemini CLI when those local tools are installed.

## Screenshots & Key Art

<table>
<tr>
<td width="50%"><a href="screenshots/title-screen.webp"><img src="screenshots/title-screen.webp" alt="SEO Dungeon title screen with character and runtime selection"></a><br><em>Pick a CLI, pick a warrior, enter a domain</em></td>
<td width="50%"><a href="screenshots/gate-scene-full.webp"><img src="screenshots/gate-scene-full.webp" alt="Gate scene showing quest continuation options"></a><br><em>Continue a previous quest or begin a new one</em></td>
</tr>
<tr>
<td width="50%"><a href="screenshots/summoning-scene.webp"><img src="screenshots/summoning-scene.webp" alt="SEO Dungeon audit loading hallway with the hero descending"></a><br><em>Run a fresh audit while the hero descends</em></td>
<td width="50%"><a href="screenshots/dungeon-hall.webp"><img src="screenshots/dungeon-hall.webp" alt="Dungeon hall showing SEO issue demons sorted by severity"></a><br><em>Browse SEO demons sorted by severity</em></td>
</tr>
<tr>
<td width="50%"><a href="screenshots/battle-scene.webp"><img src="screenshots/battle-scene.webp" alt="Turn-based battle scene with real-time Guild Ledger"></a><br><em>Battle demons with agent-powered fixes</em></td>
<td width="50%"><a href="assets/social-preview.png"><img src="assets/social-preview.png" alt="SEO Dungeon social preview key art"></a><br><em>Share-ready key art for the public repo</em></td>
</tr>
</table>

## How It Works

1. Choose a local CLI runtime: Codex, Claude Code, or Gemini CLI. Codex is
   selected by default in the packaged app.
2. Choose a character profile:
   - Warrior: deep profile. Codex uses `xhigh`; Claude uses `opus`; Gemini uses `pro`.
   - Samurai: balanced profile. Codex uses `high`; Claude uses `sonnet`; Gemini uses `flash`.
   - Knight: fast profile. Codex uses `medium`; Claude uses `haiku`; Gemini uses `flash-lite`.
3. Enter a domain and local project path.
4. Arm YOLO Mode so Codex runs with `--dangerously-bypass-approvals-and-sandbox`.
5. Run a full `/seo audit` through the selected local CLI.
6. Review SEO issues as dungeon demons sorted by severity.
7. Use **Attack** to send a scoped agent turn for the selected issue.
8. Queue or steer follow-up prompts through the Guild Ledger while work is
   running; queued prompts release when the active turn settles.
9. Use **Vanquish** when you decide the issue is handled.

The Guild Ledger sidebar can be resized or hidden while you work, and the title
screen remembers your last domain and project folder. YOLO Mode is deliberately
not remembered; it must be armed on each fresh app launch.

The dungeon bridge starts local CLI processes only. It does not proxy model
access and does not route through browser automation or consumer-app wrappers.

## SEO Engine

The bundled v2.2 engine is synchronized with Daniel Agrici's public
`AgriciDaniel/claude-seo` v2.2 release. It includes 25 sub-skills (21 core +
1 orchestrator + 1 framework integration + 2 extension mirrors), 18 portable
sub-agents, 23 Codex agent profiles, and 50 Python execution scripts.

Full audits are treated as multi-agent work by default. SEO Dungeon asks the
selected runtime to fan out specialist audit workers in parallel whenever that
runtime supports it, and delegated workers inherit the selected strength profile:
Warrior stays extra-high, Samurai stays high, and Knight stays medium.

| Area | Coverage |
|------|----------|
| Audit | Full-site audits, page audits, technical SEO, schema, sitemap, image SEO, hardened URL safety |
| Content | E-E-A-T, content briefs, semantic clustering, SXO, competitor pages, QRG-aligned quality gates |
| Growth | Local SEO, maps intelligence, backlinks, e-commerce, programmatic SEO |
| Monitoring | SEO drift baselines and comparisons |
| Data | Google SEO APIs, DataForSEO, Firecrawl, Ahrefs, Bing Webmaster, Profound, SE Ranking, Unlighthouse |
| Assets | SEO image generation planning through the optional Banana/Gemini extension mirror |
| Framework | FLOW prompts for Find, Leverage, Optimize, Win, and local workflows |

## Quick Start

### Prerequisites

- Node.js 22+
- Python 3.10+
- Git
- Codex CLI installed and signed in for the packaged default runtime
- Optional: Claude Code CLI or Gemini CLI for the runtime picker options

### Install Codex Skills

```powershell
# Windows
.\install.ps1
```

```bash
# macOS/Linux
bash install.sh
```

The installer places the SEO skills under your Codex home and copies the Codex
TOML profiles into the Codex agents folder. The portable `agents/` Markdown
prompts remain in the repository for compatible non-Codex agent workflows.

### Run The Game

```bash
cd dungeon
npm install
npm run dev
```

Open [http://localhost:3002](http://localhost:3002). The bridge server starts on
port `3003`.

For live development visibility, keep a second terminal open:

```bash
cd dungeon
npm run logs
```

The bridge mirrors startup, runtime selection, CLI executable paths, child
exits, and errors to `dungeon/.logs/bridge.log`.

### Codex Remote Control

When the app and bridge are running, Codex can use the local helper to drive the
browser-owned setup and Guild Ledger paths:

```powershell
cd dungeon
npm run remote -- status --json
npm run remote -- event --wait --timeout 30000 --kind ui-intent --action launch --domain seodungeon.com --project E:\seo-dungeon-website --runtime codex --profile fast --character knight --dangerous-bypass --meta source=codex-helper
npm run remote -- send --wait --timeout 120000 --project E:\seo-dungeon-website --profile fast --dangerous-bypass -- "/seo page https://seodungeon.com"
npm run remote -- watch --kind ledger-result --filter-source guild-ledger --count 1 --timeout 30000
```

The helper talks to the localhost WebSocket bridge. It does not automate the
Codex desktop composer; the browser applies `ui-intent` setup/start actions and
the Guild Ledger claims `send` commands through the normal Codex app-server
runtime. `event --wait` waits for a matching browser `ui-result`; `watch` remains
available for passive session observation.

To record a browser-side walkthrough of the structured intent path:

```powershell
cd dungeon
npm run demo:remote-intents -- --keep-open-ms 100
```

The recorder uses isolated dynamic ports, drives `launch`, Gate resume, Hall
issue selection, Battle attack, queue steer/stop/clear, and remote vanquish
through `npm run remote -- event --wait`, then writes a WebM, screenshot,
manifest, session log, ledger transcript, and CLI result receipts under
`dungeon/.logs/remote-intents-demo/<timestamp>/`. This is the fast browser proof
lane for recursive testing before a full desktop capture.

To record the same structured intent path as a full Windows desktop capture:

```powershell
cd dungeon
npm run proof:desktop-intents -- --fake-codex --keep-open-ms 100 --allow-foreground-mismatch
```

This writes an MP4 at the current desktop resolution, early and late frames,
browser screenshot, manifest, session log, ledger transcript, and CLI receipts
under `dungeon/.logs/desktop-intents-proof/<timestamp>/`. The default
fake-Codex mode is for recursive smoke testing. Release/demo proof should use
`--real-codex --position-codex-window`, Codex visible on the left, SEO Dungeon
visible on the right, and no `--allow-foreground-mismatch`.

Runtime environment:

| Variable | Default | Purpose |
|----------|---------|---------|
| `SEO_DUNGEON_RUNTIME` | `codex` | Bridge fallback runtime when the UI does not send one |
| `SEO_DUNGEON_CODEX_CLI` | `codex` | Codex executable override |
| `SEO_DUNGEON_CODEX_TRANSPORT` | `app-server` | Set to `exec` to use the older `codex exec --json` transport |
| `SEO_DUNGEON_CODEX_DANGEROUS_BYPASS` | unset | Set to `1` to force Codex YOLO mode from the bridge when no UI setting is provided |
| `SEO_DUNGEON_CODEX_BYPASS` | unset | Short alias for `SEO_DUNGEON_CODEX_DANGEROUS_BYPASS` |
| `SEO_DUNGEON_SESSION_LOG` | `.logs/session-events.jsonl` from `npm start` | Local bounded remote session ledger; set to `0` to disable |
| `SEO_DUNGEON_CLAUDE_CLI` | `claude` | Claude Code executable override |
| `SEO_DUNGEON_GEMINI_CLI` | `gemini` | Gemini CLI executable override |
| `SEO_DUNGEON_CODEX_MODEL` | Codex default | Optional Codex model override |
| `SEO_DUNGEON_CODEX_EFFORT_DEEP` | `xhigh` | Codex Warrior effort |
| `SEO_DUNGEON_CODEX_EFFORT_BALANCED` | `high` | Codex Samurai effort |
| `SEO_DUNGEON_CODEX_EFFORT_FAST` | `medium` | Codex Knight effort |
| `SEO_DUNGEON_CLAUDE_MODEL_DEEP` | `opus` | Claude Warrior model alias |
| `SEO_DUNGEON_CLAUDE_MODEL_BALANCED` | `sonnet` | Claude Samurai model alias |
| `SEO_DUNGEON_CLAUDE_MODEL_FAST` | `haiku` | Claude Knight model alias |
| `SEO_DUNGEON_GEMINI_MODEL_DEEP` | `pro` | Gemini Warrior model alias |
| `SEO_DUNGEON_GEMINI_MODEL_BALANCED` | `flash` | Gemini Samurai model alias |
| `SEO_DUNGEON_GEMINI_MODEL_FAST` | `flash-lite` | Gemini Knight model alias |
| `GEMINI_API_KEY` | unset | Required by Gemini CLI when it is not authenticated through another supported Gemini CLI auth path |
| `SEO_DUNGEON_CLAUDE_ARGS` | `--print --output-format text --permission-mode acceptEdits` | Claude CLI argument template |
| `SEO_DUNGEON_GEMINI_ARGS` | `--prompt {{prompt}} --output-format text --approval-mode auto_edit` | Gemini CLI argument template |

Set a model variable to `default`, `auto`, or `none` to let that CLI use its own
configured default model.

### Project API Credentials

SEO Dungeon treats the selected project folder as the credential source for
audit integrations. Add a `.env` or `.env.local` file at that project root when
you want live data:

```bash
DATAFORSEO_USERNAME=your-login
DATAFORSEO_PASSWORD=your-password
FIRECRAWL_API_KEY=fc-your-api-key
GOOGLE_API_KEY=your-google-api-key
GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/service-account.json
GSC_SITE_URL=https://example.com/
GA4_PROPERTY_ID=123456789
```

The bridge forwards known SEO-related keys from the project `.env` into the
selected local CLI. DataForSEO, Firecrawl, and Google workflows should use those
credentials directly first. MCP servers are optional adapters: if you already
have one configured, an agent may use it quietly, but SEO Dungeon does not
require MCP setup for audits.

First audits can take 5-10 minutes because `/seo audit` fans out multiple
specialist passes. Cached audits are much faster.

## Commands

| Command | What it does |
|---------|-------------|
| `/seo audit <url>` | Full website audit |
| `/seo page <url>` | Deep single-page analysis |
| `/seo technical <url>` | Technical SEO audit |
| `/seo content <url>` | E-E-A-T and content quality |
| `/seo content-brief <topic or url>` | Detailed SEO content brief |
| `/seo schema <url>` | Schema.org detection and generation |
| `/seo sitemap <url>` | XML sitemap analysis or generation |
| `/seo images <url>` | Image SEO analysis |
| `/seo geo <url>` | AI search readiness |
| `/seo plan <type>` | Strategic SEO planning |
| `/seo flow [stage] [url|topic]` | FLOW framework prompts |
| `/seo cluster <keyword>` | Semantic clustering |
| `/seo sxo <url>` | Search experience optimization |
| `/seo drift baseline <url>` | Capture drift baseline |
| `/seo drift compare <url>` | Compare against drift baseline |
| `/seo ecommerce <url>` | E-commerce SEO |
| `/seo programmatic [url]` | Programmatic SEO |
| `/seo competitor-pages [url]` | Competitor comparison pages |
| `/seo local <url>` | Local SEO |
| `/seo maps [cmd] [args]` | Maps intelligence |
| `/seo hreflang <url>` | International SEO |
| `/seo google [cmd] [url]` | Google SEO APIs |
| `/seo backlinks <url>` | Backlink analysis |
| `/seo dataforseo [cmd]` | DataForSEO extension |
| `/seo firecrawl [cmd] <url>` | Firecrawl extension |
| `/seo image-gen [use-case]` | SEO image generation planning extension |

## Architecture

```text
seo-dungeon/
  dungeon/                         # Phaser game and WebSocket bridge
    server/index.js                # Local CLI bridge
    src/scenes/                    # Game scenes
    src/utils/                     # Sound, WebSocket client, colors, particles
  skills/                          # 25 SEO engine skills
  agents/                          # 18 portable Markdown agent prompts
  agents-codex/                    # 23 Codex TOML agent profiles
  scripts/                         # 50 Python SEO scripts
  schema/                          # JSON-LD templates
  extensions/                      # Optional SEO data, crawl, and asset add-ons
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| "The dungeon is unreachable" | Bridge server is not running. Run `npm run server` in `dungeon/`. |
| Skills not found by Codex | Run `install.ps1` or `install.sh` from the repo root. |
| Codex, Claude, or Gemini fails to spawn | Confirm the selected CLI is installed, signed in, and available on `PATH`. On Windows, the bridge resolves `.ps1`, `.cmd`, `.bat`, and `.exe` shims before launching; override `SEO_DUNGEON_CODEX_CLI`, `SEO_DUNGEON_CLAUDE_CLI`, or `SEO_DUNGEON_GEMINI_CLI` if your CLI lives elsewhere. |
| Audit takes a long time | Normal for first full-site audits. Use cached audits when available. |
| Google API commands fail | Run `/seo google` for setup instructions. |
| Drift baseline not found | Run `/seo drift baseline <url>` before `/seo drift compare <url>`. |

## Asset Credits

| Asset | Creator | License | Source |
|-------|---------|---------|--------|
| DungeonTileset II | 0x72 | CC0 | [itch.io](https://0x72.itch.io/dungeontileset-ii) |
| Medieval Warrior Pack | LuizMelo | Free for personal and commercial use | [itch.io](https://luizmelo.itch.io/medieval-warrior-pack-2) |
| Martial Hero Pack | LuizMelo | Free for personal and commercial use | [itch.io](https://luizmelo.itch.io/martial-hero) |
| RPG GUI Construction Kit v1.0 | Lamoot | CC-BY 3.0 | [OpenGameArt](https://opengameart.org/content/rpg-gui-construction-kit-v10) |
| Golden UI | Buch | CC0 | [OpenGameArt](https://opengameart.org/content/golden-ui) |

## License

[MIT](LICENSE) - Copyright (c) 2026 Avalon Reset.

SEO engine code is derived from Daniel Agrici's open-source SEO skill suite and
used under the MIT license. SEO Dungeon is independent and runs through local
terminal-agent workflows selected in the app.
