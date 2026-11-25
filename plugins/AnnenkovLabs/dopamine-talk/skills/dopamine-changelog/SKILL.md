---
name: dopamine-changelog
description: >-
  Writes and rewrites changelogs, mod updates, and GitHub release notes so they spark genuine
  excitement, sell the real power of a release, and read cleanly in one breath. Translates raw
  git diffs, optimizations, and dependency upgrades into the user-impact derivative f'(x): vivid
  before/after storytelling, domain-native impact contrasts (FPS, freezes, RAM, latency, queries,
  build time, cost, or tokens), and exact CVE/version clarity. Works for any software: games,
  Minecraft mods, web/mobile apps, desktop tools, libraries, or AI agents. Triggers:
  "dopamine-changelog", "changelog", "release notes", "release highlights", "summarize release".
license: MIT
---

# Dopamine Changelog: User Impact (`f'(x)`) Instead of Diff Narration

A changelog answers one and only one question: **"What just got better in my life after updating, and why should I upgrade right now?"**

Default coding agents write terrible changelogs because they stare at `git diff` and narrate the code change (`f(x)`), while readers care about **the derivative (`f'(x)`)**: smoother FPS, vanished stutters, faster loads, lower memory, saved money, closed security holes, and new superpowers.

This works identically for **a Minecraft mod, an indie game, a SaaS backend, a mobile app, a desktop app, a CLI, or an AI harness** — always adapt the metrics, tone, and table shape to what real users of *this* project actually feel.

---

## 0. Five Deadly Sins of AI Changelogs (Kill on Sight)

1. **Narrating code instead of the derivative (`f(x)` instead of `f'(x)`):**
   - *Garbage:* "Refactored `WeaponRenderer.java` to reuse `MatrixStack` buffers, added LOD threshold at 16 blocks, reduced bullet decal TTL from 400 to 200 ticks."
   - *Dopamine:* "Up to 90% less memory pressure! Before, every single frame the mod created thousands of throwaway objects just to draw one gun — holding an AK meant 60 times a second Java created and threw away ~5,000 objects, sending the garbage collector into freezes and FPS drops. Now we reuse memory instead of allocating (**288,000 new objects/sec -> 0**), distant players past 16 blocks switch to smart LOD automatically, and bullet holes clear in 10s instead of 20s — turning 20+ player firefights from **10-20 FPS with freezes** into **30-40 FPS smooth**."
2. **Invented marketing brands and fake versions ("v2", "2.0", "Next-Gen"):**
   - *Garbage:* Calling a normal release `App v2` only because an internal test file was named `engine-v2.test.ts`.
   - *Rule:* Never fabricate marketing labels (`v2`, `2.0`, `Pro`, `Next-Gen`) from internal branch or test names. Stick to real release versions: **Before -> After (1.4.2)**.
3. **Inverting importance (burying the elephant):**
   - Agents judge significance by how many files changed — so moving a button gets a full paragraph while cutting memory allocations from `288,000/s -> 0` or making the core 3.5x cheaper gets buried as *"Optimized internal rendering pipeline"*.
   - *Rule:* Any breakthrough in FPS, smoothness, memory, latency, cost, reliability, or security goes straight to the top under **Highlights** and **Before -> After**.
4. **Back-kitchen AST & test-count dumps:**
   - Zero internal file paths (`src/render/WeaponRenderer.java`, `src/core/loop.ts`), private method names, line numbers, or *"added 42 unit tests and fixed flaky CI"*. The reader is opening a product or loading a game, not reviewing your pull request.
5. **Faceless corporate filler without concrete numbers or CVE specifics:**
   - Phrases like *"improved performance"*, *"enhanced security"*, and *"updated dependencies"* are banned. Performance wins need real felt contrasts (FPS, freezes, ms, MB, queries, allocations, or tokens). Security/runtime bumps must state **exact `Old -> New` versions**, **exact CVE/GHSA IDs and attack vectors closed**, and **whether end users need to install anything manually**.

---

## 1. Gold-Standard Example (Game / Minecraft Mod Update)

Notice how this hits maximum dopamine **without a single token count, line number, or artificial `%` column** — just a vivid human picture, crisp 2-line `Before -> After` punchlines, and an honest real-scenario table (even keeping `~60 FPS -> ~60 FPS` for solo play so the player trusts every single number!):

> ### Update — Up to 90% less memory pressure!
>
> **What happened before?**  
> Every single frame the mod created **thousands of throwaway objects** just to draw one weapon. Picture holding an AK while 60 times a second the game creates and throws away **~5,000 objects**. Java's garbage collector went crazy — freezes, microstutters, FPS drops.
>
> **What changed?**
>
> ⚡ **Rendering optimization**  
> **Before:** 288,000 new objects per second for one gun  
> **After:** 0  
> We reuse memory instead of constantly allocating and throwing it away.
>
> 📉 **Smart LOD by default**  
> Before, the game rendered full-detail models even for players across the map. Past 16 blocks, simplified models now kick in automatically.
>
> 💨 **Less bullet clutter**  
> Bullet holes now last 10 seconds instead of 20. Fewer particles = lighter fights.
>
> **What players actually feel**
>
> | Scenario | Before | After |
> | :--- | :--- | :--- |
> | 1 player with a weapon | ~60 FPS | ~60 FPS |
> | 10 players firing | 25-35 FPS | 45-55 FPS |
> | Big 20+ player firefight | 10-20 FPS, freezes | 30-40 FPS, smooth |
> | GC pauses | every 2-3 sec | almost gone |

---

## 2. Translation Formula Across Domains: Code -> Mechanics -> User Win

Build every single changelog item through this three-step chain, adapting naturally to the project's domain:

| Engineering change (`f(x)`) | What happens in real life (Mechanics) | What the human feels (`f'(x)`) |
| --- | --- | --- |
| Replaced per-frame object allocations with pooled reuse + LOD at 16+ blocks | Rendering a weapon no longer creates 288,000 throwaway Java objects every second; distant models simplify automatically | **Up to 90% less memory pressure**: 20+ player fights jump from **10-20 FPS with freezes** to **30-40 FPS smooth**, GC stutters nearly gone |
| Batched SQL joins + added composite index on order history | Checkout and dashboard fetch everything in 3 tight queries instead of 140 sequential round-trips | **Page loads in 95 ms instead of 1.8 s** — zero spinner lag even during peak traffic |
| Upgraded bundled runtime (`Old -> New`) with CVE/GHSA patches | Embedded engine runs on a faster, hardened release closing specific RCE / memory bugs | **Lower attack surface and snappier startup** — desktop users install normally with zero extra runtime setup |
| Enabled parallel reads + stable prompt prefix caching | Agent reads batches of files in one turn while the prompt prefix stays locked in cache | **3.5x less spend on fresh tokens**; repo exploration shrinks from 16 sluggish steps to 2 turns |

---

## 3. Adaptive Anatomy of a Great Release (`## <version>`)

Pick the exact level of structure the release deserves — tight and punchy for a mod/app patch, structured for a major version:

1. **Header & Hero Hook:** Date/channel + **1-2 bold sentences selling the single biggest lived shift** (e.g., *"Up to 90% less memory pressure!"*, *"Checkout loads 18x faster under peak load"*).
2. **What hurt before (optional 2-3 line scene-setter):** When fixing a painful bottleneck (stutters, slow startup, freezes), paint the exact pain in plain human terms first so the fix lands twice as hard.
3. **🔥 Highlights (1-4 concrete breakthroughs):** Bold action title + lived `Before -> After` contrast. Simple 2-line `Before: X / After: Y` punches work brilliantly here.
4. **📈 Before -> After Impact Table (flexible shape!):** Choose whichever table fits the domain best:
   - **Real-life scenario table (`Scenario | Before | After`)** — ideal for games, mods, UI responsiveness, and everyday workflows.
   - **Metric table (`Metric | Before | After | Net Gain / Multiplier`)** — ideal when raw ratios (`-71%`, `3.5x`, `18x`) tell the cleanest story.
   - For architectural estimates without a live benchmark, place two words **In theory:** above the table and zero apologetic disclaimers below it.
5. **⚡ Under the Hood & Runtime/Security:** Ergonomics, polish, and exact `Old -> New` runtime/CVE upgrades translated into plain user benefit.
6. **🛠 Fixes (`Symptom -> Outcome`):** Describe the bug the way a user actually ran into it, then how cleanly it behaves now.
7. **📦 Before You Upgrade:** Honest 1-2 lines on auto-update vs manual download + full diff link (when applicable).

---

## 4. Style & Repo Hygiene Rules

1. **Native language purity:** Match the requested or repository language cleanly with crisp, natural prose and zero corporate filler.
2. **Always check repo-specific rules:**
   - Check whether the repository forbids em-dashes `U+2014` (e.g., in `AGENTS.md` or a lint script). When forbidden, use `:`, `-`, `->`, or a period instead.
   - Keep a single version heading formatted as `## <version>` (e.g., `## 1.4.0`) when release scripts extract sections for GitHub Releases.
3. **Pre-publish litmus test:**
   Read every bullet as a real player or user opening the update. If a line answers *"which file or class did the programmer refactor?"*, rewrite it until it answers *"why does this feel faster, smoother, cheaper, safer, or more fun now?"*.
