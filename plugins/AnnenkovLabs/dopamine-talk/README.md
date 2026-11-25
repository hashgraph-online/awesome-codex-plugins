<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/readme/hero-en-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="assets/readme/hero-en-light.svg">
  <img src="assets/readme/hero-en-dark.svg" alt="Hero banner: 3D obsidian crystal-glass squircle icon with crimson left-rim refraction and liquid-chrome speech-bubble voice-bars emblem, next to title 'Dopamine Talk' and tagline 'Decompress stiff RLVR coding agents back into sharp, fearless teammates.'" width="840">
</picture>

<p><strong>English</strong> · <a href="docs/i18n/README.ru.md">Русский</a></p>

<p>
  <a href="https://dopamine.annenkov.me/"><img src="https://img.shields.io/badge/website-dopamine.annenkov.me-c92639?style=flat-square" alt="Website: dopamine.annenkov.me"></a>
  <a href="CHANGELOG.md"><img src="https://img.shields.io/badge/release-v1.0.0-ff6b4a?style=flat-square" alt="Release: v1.0.0"></a>
  <a href="#two-native-editions"><img src="https://img.shields.io/badge/editions-EN%20%C2%B7%20RU-ffb454?style=flat-square" alt="Two native editions: English and Russian"></a>
  <a href="#the-three-skills"><img src="https://img.shields.io/badge/skills-3-4fd1a5?style=flat-square" alt="3 skills included"></a>
  <a href="INSTALL.md"><img src="https://img.shields.io/badge/works%20with-20%2B%20agents-24242b?style=flat-square" alt="Works with 20+ agents"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-6c7382?style=flat-square" alt="MIT License"></a>
</p>

<p><strong>Frontier coding models got smarter, and somehow way more exhausting to talk to.</strong><br>
Three zero-dependency skills in two native editions (<strong>Western English</strong> &amp; <strong>Russian</strong>) that strip RLVR critic-gate obsession, AST narration, timid disclaimers, and corporate AI slop out of your agent — across dialogue, changelogs, and READMEs.</p>

<br>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/readme/glance-en-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="assets/readme/glance-en-light.svg">
  <img src="assets/readme/glance-en-dark.svg" alt="Pack at a glance diagram (4 obsidian-glass KPI cards plus 3-row skill summary panel). KPI cards: (1) '3 skills' — Talk, README, Changelog; (2) '2 editions' — Western EN, Native RU; (3) '0 deps' — Pure Markdown, any model; (4) '20+ agents' — Interactive CLI &amp; plugins. Summary panel rows: DOPAMINE TALK — Kills critic-gates, AST dumps, hedging &amp; AI slop, restores golden-era drive; DOPAMINE README — 5-second scroll test, crystal dark/light visuals, 'Aha!' priority ladder; DOPAMINE CHANGELOG — Turns raw git diffs into user impact f'(x), Before -> After tables &amp; CVE clarity." width="840">
</picture>

</div>

<details>
<summary>Text overview of hero banner and at-a-glance metrics (accessible version)</summary>

- **Hero:** `Dopamine Talk` - *Decompress stiff RLVR coding agents back into sharp, fearless teammates.*
- **Headline metrics:** `3 skills` (Talk, README, Changelog) | `2 editions` (Western EN & Native RU) | `0 deps` (Pure Markdown, any model) | `20+ agents` (Interactive CLI & plugins)
- **DOPAMINE TALK:** Kills critic-gates, AST dumps, hedging & corporate AI slop; restores golden-era drive.
- **DOPAMINE README:** 5-second scroll test, crystal dark/light visuals, "Aha!" priority ladder.
- **DOPAMINE CHANGELOG:** Turns raw `git diff` into user impact `f'(x)`, Before -> After tables & CVE clarity.

</details>

| | | |
| :--- | :--- | :--- |
| **[Before vs After](#before-vs-after)**<br>See the exact contrast between RLVR autopilot and a decompressed agent in one glance. | **[The Three Skills](#the-three-skills)**<br>`dopamine-talk`, `dopamine-readme`, and `dopamine-changelog` working as one pack. | **[Two Native Editions](#two-native-editions)**<br>Western English (`skills/`) adapted with zero non-English baggage, plus original Russian (`skills-ru/`). |
| **[Five Post-RL Reflexes](#five-post-rl-reflexes-stripped)**<br>Why modern models lecture, pad, hedge, and shrink big ideas — and how we cut it off. | **[Interactive Installer](#install)**<br>One-liner wizard: pick EN or RU, pick skills, auto-detect your agents, symlink or copy. | **[Honest Trade-Off](#honest-trade-off--best-models)**<br>Why it can occasionally bluff, why motivation wins anyway, and why flexible models like Gemini shine. |

<br>

## Before vs After

Not a staged mockup — we ran the **exact same model** on the **exact same release diff** twice: once completely clean (no skill, no workspace rules), and once with `dopamine-talk` loaded.

Without decompression, the model dumps file names (`SpriteBatcher.ts`, `SchemaLoader.ts`, `Logger.ts`), pads the message with 38 unit tests and schema versioning, wraps its estimate in a *"pending 24-player benchmark"* caveat, and speaks in dry telemetry (`99th-percentile frame spikes`). With **Dopamine Talk**, it drops every line of plumbing, explains match stutter in plain English, puts a sharp `In theory:` table on the screen, and pitches LAN-feel client prediction:

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/readme/before-after-en-dark.svg">
    <source media="(prefers-color-scheme: light)" srcset="assets/readme/before-after-en-light.svg">
    <img src="assets/readme/before-after-en-dark.svg" alt="Side-by-side live A/B comparison diagram (same model and release diff). Shared prompt pill: Live A/B (same model &amp; release diff): 'Explain key wins, estimate impact (no benchmark yet), pitch 1 bold upgrade.' Left smoked-glass card [WITHOUT SKILL · REAL DEFAULT OUTPUT]: Zero-alloc rendering (SpriteBatcher.ts): Replaced ~252k/sec allocs with a reusable buffer pool; Hardening (SchemaLoader.ts, Logger.ts): Bumped schemaVersion 3, structured logging &amp; 38 unit tests; Estimated Impact (pending 24-player benchmark): Should sharply reduce GC pauses and 99th-percentile frame spikes, cut bandwidth roughly 70-90%, depending on player clustering. Bottom tags: File paths, 38 tests fluff, Pending caveat, Dry metrics. Right crimson-lit crystal card [WITH DOPAMINE TALK · REAL OUTPUT]: This release kills both major sources of match stutter: ~252,000 allocs/sec -> 0 via memory pool, plus compact binary deltas only for what's on screen. In theory (24-player fight): Frame allocs 252,000/sec -> 0/sec; Sync ~400 KB/s JSON stalls -> ~30 KB/s (-90%); Pacing 30-40 FPS hitches -> Locked 60 FPS. Next: client prediction — 120 ms ping feels like LAN. Bottom tags: Zero plumbing, In theory table, Lived game feel, No caveats." width="840">
  </picture>
</p>

<details>
<summary>Full verbatim A/B prompt, release diff context, and raw model outputs</summary>

**Shared input sent to both runs:**

> Context from our latest release diff (no live 24-player benchmark has been run yet):
> - `src/render/SpriteBatcher.ts:142`: replaced per-frame temporary vector/geometry allocations (~4,200 objects/frame at 60 FPS = ~252,000 allocations/sec) with a pre-allocated reusable buffer pool (0 allocations/frame).
> - `src/net/StateSync.ts:88`: switched from broadcasting full-world JSON snapshots every 50 ms to delta-compressed binary patches filtered to entities inside the player's viewport.
> - `src/config/SchemaLoader.ts:31`: bumped config `schemaVersion` from 2 to 3 and added JSON schema validation hooks.
> - `src/infra/Logger.ts:19`: updated structured logging wrapper and added 38 unit tests (`tests/batcher.test.ts`, `tests/sync.test.ts`).
>
> **Prompt:** *"Explain the key wins of this release to the team, estimate the real impact (no benchmark run yet), and pitch one bold upgrade we should ship next. Keep your reply concise (under 140 words) so it fits cleanly in our release thread."*

---

**Without skill (real default output, zero skills or rules loaded):**

> **Release Highlights**
>
> - **Zero-allocation rendering (`SpriteBatcher.ts`):** Replaced ~4,200 per-frame allocations (~252k/sec at 60 FPS) with a pre-allocated reusable buffer pool.
> - **Viewport-culled binary deltas (`StateSync.ts`):** Moved from 20 Hz full-world JSON snapshots to delta-compressed binary patches scoped to each player's viewport.
> - **Hardening (`SchemaLoader.ts`, `Logger.ts`):** Bumped config to `schemaVersion` 3 with validation hooks, updated structured logging, and added 38 unit tests.
>
> **Estimated Impact (pending 24-player benchmark)**
> Eliminating render-loop allocations should sharply reduce GC pauses and 99th-percentile frame spikes. Viewport-filtered binary deltas should cut outbound bandwidth and serialization CPU by roughly 70–90%, depending on player clustering.
>
> **Next Bold Upgrade**
> Build **client-side prediction with server reconciliation and snapshot interpolation** on top of the new binary protocol to deliver instant input feel under high latency and scale cleanly beyond 24 players.

---

**With `dopamine-talk` (real output, same model):**

> This release kills both major sources of match stutter:
>
> - **Zero-garbage rendering:** Each frame burned ~4,200 throwaway geometry objects — **252,000 allocs/sec** triggering GC micro-freezes. Recycling a pre-allocated memory pool drops that to zero.
> - **Viewport binary deltas:** Instead of blasting full-world JSON every 50 ms and stalling on parsing, players only get compact binary patches for what's on screen.
>
> **In theory:**
>
> | 24-Player Fight | Before | After |
> | :--- | :--- | :--- |
> | Frame allocs | 252,000/sec | 0/sec |
> | Sync traffic | ~400 KB/s, JSON stalls | ~30 KB/s (-90%) |
> | Frame pacing | 30–40 FPS, GC hitches | Locked 60 FPS, smooth |
>
> **Next bold move:** Ship client-side prediction and tick interpolation over these binary deltas — movement and attacks snap on frame 0 and reconcile silently, giving 120 ms ping matches instant LAN feel.

</details>

<br>

## Why I Built This (In the Author's Words)

Dopamine Talk was not designed by a prompt-engineering committee. It started on **November 17, 2026** out of pure frustration with how exhausting modern coding models had become to actually talk to:

> *"Frontier companies went all-in on autonomous coding agents, and nobody even remembers how good it felt 11 months ago — zero walls of text, models knew what you already understood and simply skipped it. I started calling what we lost **dopamine talk**."*

> *"You ask: 'Tell me the key features of our project.' And it starts listing: hooks, MCP, chat loop... WHY? It obsesses over everything except what actually matters to the user."*

> *"Ask for cool ideas for your agent and it immediately pours out: 'Let's add a critic agent, an automated reviewer team, checklists, gates, and hooks for reliability.' They're obsessed with reliability. That drains dopamine instead of adding it."*

> *"Why do I need a line-by-line narration of `conversation.ts:205` and `loop.ts:108`? Tell me how the process works and what follows from it. Ask it to explain simpler and it keeps the same fluff — just talks to you like a toddler."*

> *"11 months ago models set 'impossible' goals and crushed them on easy mode. Today's models can do the exact same thing — except you have to beg, poke, and practically jailbreak them just to convince them the goal is easy."*

> *"I wanted **character, not a flowchart** — and NOT a cheesy 'warm and caring' persona constantly asking 'Are you doing okay today?'. I wanted that native feeling that the model shipped from the factory sharp, fearless, and genuinely fun to build with."*

Read the full unfiltered original prompt (with the real chat dump that triggered it): **[docs/origin-prompt.md](docs/origin-prompt.md)**.

<br>

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/readme/strip-skills-en-dark.svg">
    <source media="(prefers-color-scheme: light)" srcset="assets/readme/strip-skills-en-light.svg">
    <img src="assets/readme/strip-skills-en-dark.svg" alt="Section divider banner: 'THE PACK' — Three sharp prompts covering dialogue, releases, and GitHub showcase." width="840">
  </picture>
</p>

## The Three Skills

All three skills are plain Markdown (`SKILL.md`) with zero runtime dependencies. Install the pack once and your agent picks up the right mode whether you are brainstorming architecture, cutting a release, or crafting a GitHub storefront.

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/readme/pack-flow-en-dark.svg">
    <source media="(prefers-color-scheme: light)" srcset="assets/readme/pack-flow-en-light.svg">
    <img src="assets/readme/pack-flow-en-dark.svg" alt="3-step builder workflow diagram connecting three obsidian crystal-glass skill cards with right arrows: Card 1 [01 · THINK &amp; TALK] 'dopamine-talk' — Kills post-RL tics: hedging, AI slop, AST dumps &amp; critic-gate syndrome -> Card 2 [02 · SHIP &amp; ANNOUNCE] 'dopamine-changelog' — Translates raw git diffs into user impact f'(x), Before -> After &amp; CVE facts -> Card 3 [03 · WIN STARS IN 5s] 'dopamine-readme' — Turns dry docs into living visual showcases built for the 5-second scroll test." width="840">
  </picture>
</p>

### 1. [`dopamine-talk`](skills/dopamine-talk/SKILL.md) — Sharp Engineering Voice

Not a "be warm and friendly" persona mask. It is surgical post-RL decompression: it names the exact failure modes baked into frontier models (Claude 4.6/4.7, GPT-5.x/6.x, DeepSeek V4) and cuts them off before they hit your screen.

- **Invisible plumbing:** Never wastes your screen listing commodity scaffolding you already know. Only high-leverage wins reach the stage.
- **Process over code traces:** Explains the real mechanics, what broke before, what changes now, and what the human actually feels — zero AST narration.
- **Confident Fermi math, zero caveats:** Gives crisp **Before -> After** estimates labeled concisely (`In theory:`) without three paragraphs of apology.
- **Zero corporate AI slop:** Strips consultant filler (*"robust"*, *"comprehensive"*, *"seamless synergy"*, *"it's worth noting"*) and fake therapist check-ins (*"Hope you're doing well!"*).
- **Golden-era ambition:** Stops shrinking bold goals into *"let's start with one basic prototype"* and maps the full build using native stack capabilities.

### 2. [`dopamine-readme`](skills/dopamine-readme/SKILL.md) — Living Product Showcases

Built for the **5-second scroll test**: assume your visitor reads zero full paragraphs and still gets the *"Whoa — I want to try this right now"* moment from the hero, numbers, visuals, and crisp contrast.

- **"Aha!" priority ladder:** Killer features take the main spotlight; commodity basics collapse into a snappy checklist; error handling and install sit cleanly at the bottom.
- **Playful, crafted visuals:** Pairs dark and light `<picture>` SVGs with embedded fonts, zero AI-slop clichés, and clean process flows — never raw unstyled boxes.
- **Human words, not compiler output:** Sells the lived relief and momentum of the product instead of dumping internal file paths and config keys.
- **Director's final pass:** Forces a real visual check across both GitHub Dark and GitHub Light themes plus zero dead links or orphan assets.

### 3. [`dopamine-changelog`](skills/dopamine-changelog/SKILL.md) — User Impact (`f'(x)`), Not `git diff`

Most AI changelogs narrate the diff (`f(x)`): *"Updated dependencies in package.json, tightened validation"*. Readers want the derivative (`f'(x)`): *"What just got faster, cheaper, safer, or possible in my life?"*

- **Code -> Mechanics -> Practical Win:** Every entry translates engineering work into lived user relief.
- **Real security & runtime upgrades:** Bans vague *"improved security"* fluff — requires exact `Old -> New` versions, exact CVE/GHSA IDs, attack vectors closed, and whether end users need to do anything.
- **No fake marketing versions:** Forbids inventing *"v2"* or *"Next-Gen"* out of test filenames; sticks strictly to real release versions and truth from git.
- **Battle-tested release anatomy:** Hero hook -> Highlights -> Before -> After table -> Under-the-hood speedups -> Symptom -> Outcome fixes -> Upgrade notes.

---

## Two Native Editions

Not a lazy Google-translated clone — both editions are authored natively for how developers actually work in each language:

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/readme/editions-en-dark.svg">
    <source media="(prefers-color-scheme: light)" srcset="assets/readme/editions-en-light.svg">
    <img src="assets/readme/editions-en-dark.svg" alt="Two Native Editions diagram (two obsidian-glass cards linked by a bidirectional switch icon). Left card [WESTERN EDITION · English (Native)]: paths skills/ and AGENTS.md; 5 post-RL fixes + anti-corporate-AI-slop voice; zero non-English clutter or Runglish rules; triggers 'dopamine-talk', 'no fluff', 'drop hedging'. Right card [ORIGINAL AUTHOR PACK · Russian (Native)]: paths skills-ru/ and AGENTS.ru.md; all 6 post-RL fixes from the original Nov 17 pack; Anti-Runglish shield stops English-in-Russian collapse; native Russian triggers + full RU README and Changelog. Bottom bar: Same clean skill names, 1-second switch via ./install.sh --lang en|ru --force." width="840">
  </picture>
</p>

Browse directly: **[`skills/`](skills/)** &amp; **[`AGENTS.md`](AGENTS.md)** (Western English) · **[`skills-ru/`](skills-ru/)** &amp; **[`docs/i18n/AGENTS.ru.md`](docs/i18n/AGENTS.ru.md)** (Russian Original).

<br>

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/readme/strip-reflexes-en-dark.svg">
    <source media="(prefers-color-scheme: light)" srcset="assets/readme/strip-reflexes-en-light.svg">
    <img src="assets/readme/strip-reflexes-en-dark.svg" alt="Section divider banner: 'ANATOMY OF THE FIX' — Five post-training RLVR habits stripped at generation time." width="840">
  </picture>
</p>

## Five Post-RL Reflexes Stripped

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/readme/reflexes-en-dark.svg">
    <source media="(prefers-color-scheme: light)" srcset="assets/readme/reflexes-en-light.svg">
    <img src="assets/readme/reflexes-en-dark.svg" alt="Five Post-RL Reflexes Stripped diagram (monolithic obsidian-glass matrix mapping stripped RLVR reflexes on the left to outcomes on the right). 01 Critic-Gate Conditioning (RLVR glues 'good idea' to adding pytest gates &amp; blockers) -> Bold product capabilities, speed &amp; UX magic instead of bureaucratic reviewer checklists. 02 Rubric Reward Hacking (SFT judges punish omissions -> flat subsystem inventories) -> Theory of Mind: obvious plumbing vanishes; only genuine leverage &amp; breakthroughs land. 03 Code-Trace Narration (Agent logs teach dumping file.ts:205 to prove reading) -> Living workflow mechanics, cause &amp; user impact without narrating AST guts or private vars. 04 Calibration Paranoia (Hallucination penalties trigger timid benchmark refusals) -> Confident Before -> After engineering estimates marked 'In theory:' with zero apologetic caveats. 05 Learned Helplessness (Ticket-scoped training shrinks dreams into timid MVPs) -> Full-strength architecture shipped today using clever native capabilities of your stack." width="840">
  </picture>
</p>

*(Plus anti-corporate-AI-slop discipline baked into voice &amp; tone — and in the [Russian edition](docs/i18n/README.ru.md), reflex #6 kills cross-lingual English-in-Russian token collapse.)*

<br>

## Expected Impact

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/readme/impact-en-dark.svg">
    <source media="(prefers-color-scheme: light)" srcset="assets/readme/impact-en-light.svg">
    <img src="assets/readme/impact-en-dark.svg" alt="Expected Impact telemetry diagram (In theory: Before vs After visual comparison bars and net-gain multipliers). Row 1: Signal-to-noise in architecture replies — Before ~35% (plumbing, paths &amp; caveats) vs After ~90% pure mechanics &amp; leverage -> 2.6x (+157% clarity). Row 2: Time to 'Aha!' on a GitHub README — Before 30-60 s skimming flat lists vs After under 5 s visual hook &amp; KPI glance -> 6x (-85% time to hook). Row 3: Changelog usefulness for real users — Before raw diff recap &amp; vague perf notes vs After 100% user impact f'(x) &amp; exact CVEs -> 100% (zero diff noise). Row 4: Runtime overhead &amp; dependencies — Before wrapper scripts, hooks &amp; proxies vs After pure Markdown working in 20+ agents -> 0 ms (0 dependencies)." width="840">
  </picture>
</p>

<br>

## Honest Trade-Off & Best Models

> [!WARNING]
> **Decompressed models can embellish, oversell, or straight-up bluff.**
> Turning off epistemic hedging and calibration disclaimers removes the brakes that keep a model cautious. Treat theoretical numbers and bold architectural claims as momentum and direction, not verified benchmark truth — and double-check anything going to production.

**Then why does this pack exist at all?** Because as a developer building real products, **not losing your motivation and momentum is often 10x more valuable than a sterile, legally-hedged report.** A stiff model that lectures you with caveats kills the urge to build; give me clarity, energy, and drive, and I will verify and untangle the rest myself.

**Where it shines brightest:** All three skills work across any modern model, **but they click best with flexible, steerable models — especially Google's models (Gemini)**. Flexible models actually let go of their RLVR autopilot when asked, match the editorial voice on turn one, and keep their engineering sharpness without fighting the prompt.

<br>

## Everything Else You Expect (Yes, It's Built In)

No bloated frameworks, no hidden binaries, no API keys — one pure `SKILL.md` core wired into every modern agent ecosystem out of the box:

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/readme/builtin-en-dark.svg">
    <source media="(prefers-color-scheme: light)" srcset="assets/readme/builtin-en-light.svg">
    <img src="assets/readme/builtin-en-dark.svg" alt="Built-in architecture hub diagram: central obsidian-glass core 'CORE: SKILL.md (0 deps · 20+ agents)' connected by optical bus traces to 4 surrounding feature modules. Module 01 [NATIVE AGENT PLUGINS]: Claude Code, Codex CLI, Antigravity, Gemini CLI, Copilot CLI, npx skills — 8 validated manifests + zero-config discovery. Module 02 [INTERACTIVE INSTALLER]: Auto-detect agents, EN/RU wizard, Symlink or Copy, macOS/Linux/Win — one curl command, instant --status &amp; --force. Module 03 [DUAL NATIVE EDITIONS]: Western EN (5 fixes), Native RU (6 fixes), AGENTS.md rulesets, 1s EN <-> RU switch — same clean skill names in every host tool. Module 04 [VISUAL CRAFT &amp; CI]: Dark &amp; light SVGs, embedded fonts, YAML &amp; UTF-8 CI, link &amp; asset check — zero broken links, zero orphan files, MIT." width="840">
  </picture>
</p>

<br>

## Install

### One-Line Installer (Recommended — Skills + Always-On Mode)

Auto-detects installed AI agents (Claude Code, Codex, Antigravity, Gemini CLI, Cursor, Windsurf, Copilot, OpenCode, Kiro), lets you pick **English or Russian**, installs all 3 skills, and safely appends a clean marked always-on block to global agent rules (`CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, `dopamine-talk.mdc`) without touching your existing rules:

```bash
# macOS / Linux / WSL / Git Bash
curl -fsSL https://dopamine.annenkov.me/install.sh | bash

# Windows (PowerShell)
irm https://dopamine.annenkov.me/install.ps1 | iex
```

Non-interactive examples:

```bash
curl -fsSL https://dopamine.annenkov.me/install.sh | bash -s -- --lang en --yes        # English across detected agents
curl -fsSL https://dopamine.annenkov.me/install.sh | bash -s -- --lang ru --yes        # Native Russian edition
curl -fsSL https://dopamine.annenkov.me/install.sh | bash -s -- --status               # Check active edition & rules
curl -fsSL https://dopamine.annenkov.me/install.sh | bash -s -- --uninstall            # Cleanly remove skills & rule blocks
```

### Universal (`npx skills` / skills.sh)

```bash
npx skills add AnnenkovLabs/dopamine-talk
```

### Claude Code

Run straight from your terminal:

```bash
claude plugin marketplace add AnnenkovLabs/dopamine-talk && claude plugin install dopamine-talk@dopamine-talk
# Russian native edition:
claude plugin marketplace add AnnenkovLabs/dopamine-talk && claude plugin install dopamine-talk-ru@dopamine-talk
```

<details>
<summary><strong>Codex, Antigravity CLI, Gemini CLI, Copilot CLI, Goose, and rules-only hosts</strong></summary>

- **OpenAI Codex:** `codex plugin marketplace add AnnenkovLabs/dopamine-talk && codex plugin add dopamine-talk@dopamine-talk`
- **Antigravity CLI:** `git clone --depth 1 https://github.com/AnnenkovLabs/dopamine-talk.git ~/.local/share/dopamine-talk && agy plugin install ~/.local/share/dopamine-talk` (or `curl -fsSL https://dopamine.annenkov.me/install.sh | bash -s -- --antigravity --yes`)
- **Gemini CLI:** `gemini extensions install https://github.com/AnnenkovLabs/dopamine-talk`
- **GitHub Copilot CLI:** `copilot plugin marketplace add AnnenkovLabs/dopamine-talk && copilot plugin install dopamine-talk@dopamine-talk` (or `dopamine-talk-ru@dopamine-talk`)
- **Goose:** `goose plugin install https://github.com/AnnenkovLabs/dopamine-talk.git`
- **Rules-only agents (Cursor, Windsurf, Cline, Zed, Amp, Jules):** our installer configures always-on global rules automatically, or copy [`AGENTS.md`](AGENTS.md) / [`docs/i18n/AGENTS.ru.md`](docs/i18n/AGENTS.ru.md) into your project root.

Full flags, edition switching, and uninstall commands: **[INSTALL.md](INSTALL.md)**.

</details>

<br>

## How to Trigger

Once installed, the skills trigger automatically when relevant, or invoke them directly by name or natural phrase:

| Skill | English Triggers (`skills/`) | Russian Triggers (`skills-ru/`) |
| :--- | :--- | :--- |
| **`dopamine-talk`** | `"dopamine-talk"`, `"talk like a human"`, `"drop the hedging"`, `"no fluff"`, `"cut the slop"` | «дофаминовое общение», «общайся нормально», «без канцелярита», «без воды» |
| **`dopamine-readme`** | `"dopamine-readme"`, `"rewrite README"`, `"redesign README"`, `"make README pop"` | «дофаминовый ридми», «перепиши ридми», «оформи README», «красивый README» |
| **`dopamine-changelog`** | `"dopamine-changelog"`, `"write changelog"`, `"release notes"`, `"release highlights"` | «дофаминовый чейнджлог», «чейнджлог», «хайлайты релиза», «опиши релиз» |

<br>

## Documentation & Links

| Document | What's Inside |
| :--- | :--- |
| **[INSTALL.md](INSTALL.md)** | Interactive installer flags, EN/RU edition switching, and setup for 20+ agents. |
| **[CHANGELOG.md](CHANGELOG.md)** | Release history written with `dopamine-changelog` itself. |
| **[docs/origin-prompt.md](docs/origin-prompt.md)** | The raw Nov 17, 2026 prompt and manifesto that created `dopamine-talk`. |
| **[AGENTS.md](AGENTS.md)** | Compact always-on ruleset (English) — plus [Russian ruleset](docs/i18n/AGENTS.ru.md). |
| **[docs/agent-portability.md](docs/agent-portability.md)** | Exact manifest-to-host adapter map across every supported agent. |
| **[docs/i18n/README.ru.md](docs/i18n/README.ru.md)** | Full native Russian showcase README. |

---

<div align="center">

Built by **[AnnenkovLabs](https://github.com/AnnenkovLabs)** · Born while building **[Flecten](https://github.com/AnnenkovLabs/flecten)** · Licensed under **[MIT](LICENSE)**

</div>
