# Token Harbor

![Token Harbor - Let your Codex work fill the sails](output/promo/en/01-brand-hero-en.png)

Token Harbor is a local companion game for the time Codex spends thinking, reading files, and running tests. Tokens used by Codex quietly accumulate as Sail Power. Players decide when to spend that power on ports and voyages, while every Codex project contributes to one shared archipelago.

## See It in Motion

<p align="center">
  <img src="https://github.com/user-attachments/assets/657d9177-321b-4d8a-ba1f-4e0672e5e3b1" alt="Token Harbor gameplay demo showing Sail Power, fishing voyages, and a pirate encounter" width="400" />
</p>

## What You Can Play

- Start with one basic fishing skiff and zero coins, Sail Power, distance, token history, or port-construction progress. Real Codex token use funds the first voyage.
- Spend Sail Power to build Coral Port and Mistlight.
- Launch roughly 90-second manual voyages along coastal, coral, and deep-sea routes. Return at any time and keep the fish already aboard.
- Dispatch spare vessels on automated support voyages. They continue through Codex attention pauses, produce about 30% of manual catch volume, never catch legendary fish, and wait at port until cargo is collected.
- Chase fish that burst forward and evade after a hit. Common fish may reverse course, while rare fish can turn sharply or leave the screen briefly before returning; a fish is caught only when its health reaches zero.
- Repel route-scaled pirate ships by clicking to fire your cannon. Pirates follow a long-tail difficulty curve, damage the hull, and steal current-voyage catches; a wreck loses the entire haul.
- Face a deterministic 5% hurricane risk on each manual departure. The local server resolves hurricanes and pirate attacks from elapsed voyage time even when the browser is closed. Hull damage is repaired with materials first, then coins, back at port.
- Collect fourteen original fish across common, uncommon, rare, epic, and legendary tiers. Coral Port adds four tropical species, while Mistlight adds five cold-water and deep-sea species with route-specific habitats.
- Evolve each vessel through one clear class line: fishing skiff → trawler → ocean vessel → deep-sea ship. Building an extra vessel always creates a fresh fishing skiff with LV.1 gear instead of purchasing a later class outright.
- Manage and upgrade one selected vessel while separately choosing which in-port vessel is assigned to manual voyages; all other eligible ships can support automated dispatch.
- Upgrade gear and hull per vessel, while crew and harbor facilities remain fleet-wide. Every net, cannon, and fisher level has an immediate numerical effect; larger vessel classes amplify cannon damage, while hull levels add cargo capacity and vessel health.
- Unlock long-term progression in four-level port bands. The current three ports open upgrades through LV.12. Most current systems end at LV.20, while the cannon curve is ready through LV.100 for future archipelago chapters; later bands also carry sharply higher coin costs.
- Snapshot all vessel, equipment, crew, and cargo-capacity effects at departure. A vessel cannot be upgraded while it is at sea, but another idle vessel can still be managed in port; Lighthouse LV.4 adds +12% rarity and shortens voyages by 10%.
- Unload catches into dock storage, sell fish individually, or complete a three-slot dynamic order board. Orders only request fish from currently reachable seas, replace themselves after delivery, and allow one free full refresh every ten minutes.
- Pause an active voyage automatically when Codex needs approval or finishes work.
- Watch dawn, day, dusk, and night advance once per local clock hour, completing a full cycle every four hours.
- Experience clear skies, clouds, fog, heavy rain, and storms in stable 45-minute weather slots.
- Use English, Brazilian Portuguese, German, French, Japanese, Korean, Simplified Chinese, or Traditional Chinese. New users follow their device language when supported and otherwise start in English.
- Learn the game through a six-step interactive onboarding flow that can be replayed from Settings.
- On Windows, use the draggable always-on-top harbor shortcut that appears once per Codex session.

Token totals and game saves stay on the local machine. Token Harbor does not collect prompts, assistant text, file contents, or tool output.

## Long-Term Content Direction

The current three ports form Chapter I, not the complete world. The planned single-player roadmap centers on branching expeditions, vessel specializations, marine research, crew careers, evolving harbor districts, legendary hunts, rotating ocean conditions, and additional archipelago chapters without daily-streak pressure or paid gacha. Controlled randomness and collection concepts are recorded separately in the [randomized progression roadmap](docs/randomized-progression-roadmap.md). The implemented long-range combat math is recorded in [pirate and cannon balance](docs/pirate-cannon-balance.md).

## Multiplayer Direction

Each player will keep a separate harbor. Planned social features include harbor visits, daily supplies, visit keepsakes, several weekly or seasonal leaderboards, fleet challenges, and protected friend raids with short, repairable effects.

The current release is local-only and never displays fake friends or rankings. Stable player and world identities, action deduplication, revisions, an event outbox, SSE updates, and social rule contracts are already in place. See [the multiplayer architecture](docs/multiplayer-architecture.md) for the full design.

## Install

### Requirements

- Windows 10 or 11.
- The ChatGPT desktop app with Codex or Work mode and plugin support.
- The `codex` CLI and Node.js 20 or newer available in PowerShell.

### 1. Install the plugin

Open PowerShell and run:

```powershell
codex plugin marketplace add NickHOI/Token-Harbor --ref main
codex plugin add token-harbor@token-harbor
```

Restart the ChatGPT desktop app after installation so Codex can load the plugin, its hooks, and its local MCP server.

### 2. Enable Sail Power

The game works without token telemetry, but Sail Power will remain at zero until local telemetry is enabled. Clone the repository and run the privacy-preserving configuration script once:

```powershell
git clone https://github.com/NickHOI/Token-Harbor.git
cd Token-Harbor
powershell -ExecutionPolicy Bypass -File .\scripts\configure-telemetry.ps1
```

The script backs up the existing Codex configuration, keeps prompt logging disabled, and sends numeric usage events only to the Token Harbor server on `127.0.0.1`. Restart Codex after the script completes.

### 3. Open the harbor

Start a new Codex task and ask:

```text
Open my Token Harbor.
```

Codex starts the local server and returns the harbor URL. You can also ask `Show my harbor status` for a text summary.

### Update

```powershell
codex plugin marketplace upgrade token-harbor
codex plugin add token-harbor@token-harbor
```

Restart the ChatGPT desktop app after updating.

### Uninstall

```powershell
codex plugin remove token-harbor
codex plugin marketplace remove token-harbor
```

Uninstalling the plugin does not delete the local harbor save or the telemetry configuration. Restore the backup created by `configure-telemetry.ps1` if you also want to remove the local telemetry endpoint.

## Run Locally

In PowerShell:

```powershell
.\scripts\start-harbor.ps1
```

Open `http://127.0.0.1:47831/`. The server listens only on the local machine. Set `TOKEN_HARBOR_PORT` to change the API port and `TOKEN_HARBOR_DEV_PORT` to change the Vite development port; launchers, CORS, telemetry configuration, and the development proxy use the same variables. Vite uses `strictPort` so it cannot silently move away from the trusted origin.

Manual startup also opens the floating shortcut by default. The shortcut shows live Sail Power and local-server status, can be dragged to either screen edge, and opens Token Harbor in a standalone app window when Edge or Chrome is available. Use `./scripts/start-harbor.ps1 -NoFloatingEntry` to start only the game, or set `TOKEN_HARBOR_FLOATING_ENTRY=0` to disable automatic shortcut startup for Codex sessions.

## Development

```powershell
cd game
npm.cmd ci
npm.cmd run build
cd ..
node scripts/harbor-server.mjs
```

Production static assets with content hashes are cached immutably. The HTML shell and stable asset names use revalidation so a new release cannot remain hidden behind a year-long browser cache.

## Convert Real Token Use Into Sail Power

Run once:

```powershell
.\scripts\configure-telemetry.ps1
```

The script backs up `~/.codex/config.toml`, then enables the official Codex OpenTelemetry JSON exporter:

```toml
[otel]
environment = "token-harbor"
log_user_prompt = false
exporter = { otlp-http = { endpoint = "http://127.0.0.1:47831/v1/logs", protocol = "json" } }
```

After restarting Codex, each `response.completed` event credits token use at `10,000 tokens = 1 Sail Power`. Duplicate telemetry events are credited only once through durable on-disk receipts, even after the bounded in-save receipt history rolls over.

## Save Safety

The primary save is written through a flushed temporary file and the last verified save is retained as `harbor-state.json.bak`. If the primary file is unreadable, Token Harbor quarantines it and restores the backup. If both copies are unreadable, both are quarantined before a new harbor is created. The interface displays a recovery notice in either case. Save files and durable action/telemetry receipts live under `TOKEN_HARBOR_DATA_DIR`, `PLUGIN_DATA`, or the project-local `.token-harbor-data` directory, in that order.

## Plugin Layout

- `.codex-plugin/plugin.json`: Codex plugin metadata and interface settings.
- `hooks/hooks.json`: synchronization for running, approval, and completed task states.
- `.mcp.json`: the `open_harbor` and `harbor_status` tools.
- `scripts/harbor-server.mjs`: local game server and telemetry receiver.
- `scripts/harbor-floating-entry.ps1`: draggable Windows shortcut.
- `scripts/harbor-core.mjs`: Sail Power, ports, voyages, storage, and economy rules.
- `scripts/multiplayer-core.mjs`: player, world, revision, deduplication, and event contracts.
- `scripts/social-core.mjs`: friends, visits, leaderboards, and protected raid contracts.
- `game/`: the React game interface.

## Verification

```powershell
npm.cmd ci
npm.cmd ci --prefix game
npm.cmd run verify
```

`verify` runs ESLint (including React hook rules), JavaScript type checking, behavioral and process-level tests, and the production Vite build. The same command runs in the Windows GitHub Actions workflow.

Token Harbor is currently a local-first MVP. Real friends, global leaderboards, and raids still require authentication and cloud services. Game values are not money, cannot be traded, and do not affect Codex token limits or billing.

## License

Token Harbor is available under the [MIT License](LICENSE). Copyright (c) 2026 NickHOI.
