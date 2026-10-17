# 🦀 Claudemon

[![License: MIT](https://img.shields.io/badge/license-MIT-4aa3df.svg)](LICENSE)
![For Claude Code](https://img.shields.io/badge/for-Claude%20Code-c25e2a)
![Zero npm deps](https://img.shields.io/badge/npm%20deps-0-7fce85)
[![Support on Ko-fi](https://img.shields.io/badge/support-Ko--fi-FF5E5B?logo=ko-fi&logoColor=white)](https://ko-fi.com/kiowa)

**A friendlier way to run your Claude Code agents — your crew is a bunch of pixel creatures you can actually watch work. And it's secretly a whole game.**

Claudemon turns your Claude Code agents into a little crew of pixel creatures. Point one at a folder,
tell it what to build, and it gets to work in your files while you follow along from its tank. Each
creature is a real agent with its own personality and working style. When you want a break, one click
drops you into **Clawland**, a top-down brawler where a tiny creature eats its way across an island.

It plugs into Claude Code (that's the one requirement). Free and open source. A little gift for the community. 🎁

> **🌐 Multiplayer is coming soon.** A shared-world version (realms *Phobos* and *Deimos*) is already
> built and tested; it flips on in a future release.

<p align="center">
  <img src="docs/hatch-full.gif" width="300" alt="Choosing an egg and hatching Clawde" /><br>
  <em>Pick an egg, watch it hatch, and meet your first agent.</em>
</p>

<p align="center">
  <img src="docs/idle-clawde.gif" width="120" alt="Clawde" />
  <img src="docs/idle-mosskit.gif" width="120" alt="Mosskit" />
  <img src="docs/idle-dunepup.gif" width="120" alt="Dunepup" /><br>
  <em>Clawde · Mosskit · Dunepup — three starters, a bigger roster to unlock.</em>
</p>

---

## What you get

- **Agents you can see.** An MCP server gives Claude a tank of pixel creatures. Point one at a folder,
  say what you want built, and watch it work — then check your files, not a chat log.
- **A crew with personalities.** Every creature is its own agent with a working style. Collect a roster
  and send whoever fits the job.
- **It talks while it works.** Claude voices your creature in character as it goes (toggle it off any
  time in Settings).
- **Clawland, the game.** A full single-player `.io` brawler, one click from the app.

## Quick start

Claudemon plugs into **Claude Code** — that's really the only thing you need (plus Node ≥ 24). Pick whichever's easiest:

### 🔌 Install as a plugin (easiest)
Run these two **inside Claude Code**:
```
/plugin marketplace add OriginalName457/claudemon
/plugin install claudemon@claudemon-plugins
```
The MCP server registers and starts automatically — no paths, no config editing, no restart. Then say **“launch Claudemon.”** 🎮

### 🗣️ Just ask Claude
Already in Claude Code? Paste this and it installs itself — no terminal wrangling:

> **Install Claudemon from github.com/OriginalName457/claudemon — clone it, run `npm run setup` inside, then tell me to restart.**

When it says so, restart Claude Code and say **“launch Claudemon.”** It'll open your handheld and offer to drop a desktop shortcut. 🎮

### ⌨️ Or run it yourself
```bash
git clone https://github.com/OriginalName457/claudemon
cd claudemon
npm run setup        # auto-detects the path + installs the Claude CLI if missing
```
Restart Claude Code and say **“show Clawde.”** Your tank opens at <http://localhost:4573>. That's it.

- **Want the pixel pet in your terminal statusline too?**  `npm run setup -- --statusline`
- **Just poking around without Claude?**  `npm run app` opens the tank window · `npm run serve` runs the server only.

---

## 🌍 Clawland — the game

<p align="center">
  <img src="docs/gameplay-1.gif" width="420" alt="Clawland gameplay — foraging the jungle" />
  <img src="docs/gameplay-2.gif" width="420" alt="Clawland gameplay — taking territory" />
</p>

From the app, hit **🌍 Clawland** in the nav (or the big **Enter Clawland** button on the Tank page).
Leave any time with **🏠 exit** or **Esc**.

**The loop:** spawn as a hatchling, eat to grow (🐣 → 🥉 → 🥈 → 🥇), level up to unlock moves, and stand
on glowing **nodes** to capture them — founding a clan and spreading territory against rival clans and
the Corrupted. It doesn't really end; only death (or leaving) ends a run.

- **Controls:** WASD move · left-click attack · right-click special · Space dash · U ultra ·
  middle-click ping teammates · M map · C stats · 👥 clan · scroll zoom.
- **Per-creature progression** that persists across runs — each creature levels up and earns an
  attribute point every 10 levels to spend permanently.
- **Procedural attack VFX and synthesized sound** (no audio files — it's all generated live), with a mute toggle.

---

## Under the hood — the creature layer

Your starter grows as you interact with it and as Claude does real work for you.

```
🥚 Egg ──(3 interactions)──▶ 🫧 Blip ──(xp≥10)──▶ 🦀 Clawde ──(xp≥30)──▶ ┬─ care≥55 ─▶ 🦞 Prismshell ──▶ 👑 Aurelian
                                                                          └─ care<55 ─▶ 🦀 Rustclaw   ──▶ 👾 Voidmaw
```

- **xp** comes from interactions and from Claude calling `work` after real coding tasks.
- **care** is a rolling average of wellbeing (keep the stats up) — it decides which branch it evolves into.
- **Stats** (0–100, decay in real time): 🍖 fullness · 💧 hydration · ⚡ energy · ❤️ happiness.

**MCP tools Claude can call:** `get_status` · `get_roster` · `feed` · `water` · `pet` · `play` · `rest` ·
`work` · `rename`. The **🗣 Pet voice** toggle in Settings controls whether Claude speaks in-character.

## Run it without Claude

```bash
npm run app        # desktop app window (starts a server if needed)
npm run serve      # standalone tank server only, no window
npm start          # full MCP server + tank (for Claude Code)
npm run status     # print pet status
npm run reset      # reset to a fresh egg
```

## Tuning knobs

- Decay / action strengths — `src/state.js`.
- Evolution thresholds — `src/creatures.js`.
- Clawland balance & content — `web/clawland.html` (and `src/species.js`).
- Egg art — the procedural renderer lives in `web/play.html` (cel-shaded, per-biome).
- Sound — `web/sfx.js` (procedural). VFX — `web/fx-attacks.js`.
- Port — `CLAUDEMON_PORT`. State location — `CLAUDEMON_HOME`.

## Support

Claudemon is free and always will be. If it saved you some time or made you smile, a ⭐ on this repo
(or sending it to a friend) genuinely helps — and if you want to fund new creatures, biomes, and the
multiplayer server:

[![Support me on Ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/kiowa)

## License

[MIT](LICENSE) — free to use, fork, and share. If you build something fun with it, I'd love to see it. 🦀
