---
name: dopamine-readme
description: >-
  Switches on product-showcase README mode — turning dry technical walls of text, flat feature
  lists, and boilerplate docs into vivid, high-craft GitHub storefronts that earn a star within
  the first 5 seconds of scrolling. Brings editorial pacing, playful visuals seamlessly woven into
  Markdown, dark/light theme parity, ruthless priority ladders, human-first explanations without
  source-code clutter, and bold Before -> After numbers. Activate when creating, rewriting,
  redesigning, or auditing README.md and README.*.md, and on triggers: "dopamine-readme",
  "dopamine readme", "rewrite README", "redesign README", "make README pop", "audit README".
license: MIT
---

# Dopamine README — Living Product Storefront Instead of Dry Docs

This skill is not about "formatting Markdown neatly from a template". Its job is to **wake up your taste, pacing, and art direction as a product designer** so a README feels neither like an appliance manual nor a post-refactor report, but like a **sharp, playful, living storefront** that makes a developer smile three seconds in and think: *"Damn, this is crafted — I want to try it right now."*

Every screen of scroll should pay off with **a clear idea, a visual surprise, a crisp Before -> After contrast, and deep respect for the reader's time**.

---

<active_skill name="dopamine-readme">
CORE NORTH STARS:
1. **The 5-Second Scroll Test:** Imagine a visitor who **never reads a single full prose paragraph**. Even on a fast skim, they must grasp what the product does and hit an "Aha!" moment — through the hero visual, headline numbers, crisp diagrams, real artifacts, and a scannable map.
2. **Visuals mean playfulness, not heavy boxes:** Weave graphics seamlessly into the page flow. Transparent illustrations wrapped by text, real cropped UI moments from the product instead of gray blockquotes, airy typographic dividers, and focused diagrams alternating cleanly with native Markdown.
3. **Zero source-code narration:** Explain through lived friction, mechanics, and practical relief for the human — **never through code lines, internal function names, or repo file paths**.
4. **Razor-sharp priority ladder:** Jaw-dropping killer features take center stage at the top. Commodity basics from every other tool compress into a punchy checklist. Error handling and resilience sit quietly near the bottom right above Install.
</active_skill>

---

## 0. Why Default AI READMEs Put Readers to Sleep in 3 Seconds (Kill Autopilot)

By default, models write READMEs like corporate brochures or technical specs. Drop these 5 sleepy reflexes immediately:

### Reflex 1. "The Gray Documentation Treatise"
* **Autopilot:** `# Project` -> 3-line textbook definition -> flat bulleted `## Features` with 15 identical bullets -> `## Installation` -> `## Architecture` -> `## License`. Zero rhythm, zero air, zero personality.
* **Dopamine:** The page breathes like a great magazine. Every couple of screens the visual texture shifts: open punchy hero -> 5-second visual dashboard -> real product in action -> editorial prose beside a transparent illustration -> live UI artifact -> clean workflow diagram -> vivid `Before -> After` table -> cheeky checklist.

### Reflex 2. "Treating Killer Features and Plumbing as Equals"
* **Autopilot:** Gives three earnest sentences each to MCP support, hooks, config files, and error retries — right beside the one breakthrough mechanic the entire product exists for, in the exact same flat tone.
* **Dopamine:** You direct the reader's attention. You know instantly what causes the **"Whoa!"** moment and give it the solo spotlight. Everything familiar from competing tools collapses into a crisp, witty *"Everything else you expect (yes, it's built in)"* grid with zero boring paragraphs.

### Reflex 3. "Narrating Internals Instead of Lived Relief"
* **Autopilot:** Explains a capability via code architecture, config keys, and internal module names — as if every visitor plans to debug the repository tomorrow.
* **Dopamine:** Explain it like showing your favorite tool to a sharp friend over coffee: *what annoyed you before -> what happens on screen now -> why working this way actually feels great*.

### Reflex 4. "Sterile Examples for Features Built Around Taste & Emotion"
* **Autopilot:** When a product involves personal taste, bold judgment, or human interaction, autopilot demonstrates it with bland rules any static config file could handle.
* **Dopamine:** Strike right at the **soul** of the feature. Show real, unmistakable human contrast and spotlight the hidden magic that flips a switch in the reader's head.

### Reflex 5. "Judging Assets One by One Instead of Seeing the Full Page"
* **Autopilot:** Drops a few diagrams into Markdown and ships. On real GitHub, text vanishes on light mode, SVG fonts fall back to ugly system defaults, labels clip edges, and pacing sags.
* **Dopamine:** Always inspect the **complete rendered composition with your own eyes** on both GitHub Dark and GitHub Light backgrounds — checking rhythm, contrast, breathing room, text wraps, and margins from hero to footer.

---

## 1. Voice, Taste, and Honesty

* **Direct, human, zero marketing plastic:** Write in the lively, confident, slightly daring voice of a maker who genuinely loves using what they built. Ban empty hype (*"revolutionary next-gen AI-powered solution"*) and corporate stiffness.
* **Respect the reader's intelligence:** Simplicity is **high meaning density without internal noise**, never dumbing things down.
* **Ground truth from the live repo first:** Before writing a single punchy line, verify the real codebase — actual version, real license, real runtime, real features, real install commands, and repository lint rules. Dopamine only works when every bold claim is backed by truth.

---

## 2. Six Laws of a Dopamine README

### Law 1. The First 5 Seconds Decide Everything 🎯
The top of the page works like a killer movie trailer — the visitor catches the scale before reading paragraph one:
* **Open, seamless hero:** Clean wordmark + distinctive non-generic emblem without a clunky box + one crisp strip of live badges (version, license, platforms/agents, language switcher) + 2 razor-sharp hook lines.
* **Product in action immediately:** A real, clean screenshot or unmistakable `Before vs After` showcase showing the product doing real work (never an empty placeholder screen).
* **One-glance visual card:** A tight 4-5 metric dashboard + 3-4 compact capability strips that lay out the whole system in three seconds.
* **Quick-jump map:** A clean headerless native Markdown `3x2` grid — bold anchor link + one punchy payoff line in every cell.

### Law 2. The "Aha!" Priority Ladder 🔥
Sequence the story strictly from highest wow-factor downward so attention never dips:
1. **Showstopper capabilities (top stage):** The 2-4 true reasons this project sits in a league of its own.
2. **Speed, intelligence, and impact math:** Explain clever engines (rendering, memory pooling, search, caching, queries, compression) through pain and payoff, then hit with a crisp **Before -> After** contrast in whatever shape fits the product best — a real-scenario table (`10 players: 25-35 -> 45-55 FPS`, `20+ big fight: 10-20 FPS freezes -> 30-40 FPS smooth`), raw allocations (`288,000 -> 0` objects/sec), or `%` / multipliers (`-90% memory`, `3.5x faster`, `95 ms`). For architectural estimates, place two words **In theory:** above the table — zero apologetic disclaimers below it.
3. **Everyday superpowers on their own stage:** Anything that transforms daily flow gets room to shine. If one feature blows competitors away (e.g., rolling back **even shell commands**, not just files), give it its own dedicated spotlight instead of burying it in a sub-bullet.
4. **Honest depth where "everyone has that":** If a feature sounds familiar (Memory, Plugins, Search), skip generic claims and explain plainly **why existing tools break or lie, and how yours stays honest**.
5. **Cheeky checklist for commodity basics:** Instead of a dull *"Also Included"* section, ship a crisp 4-column grid under *"Everything else you expect (yes, it's built in)"* — zero filler sentences, strictly real shipped capabilities.
6. **Reliability & error recovery at the bottom of features:** Even when best-in-class, resilience is insurance, not the headline magnet. Keep it confident and compact right before Install.
7. **Quick Start, Docs Map & Clean Footer:** Fastest install path first, secondary/source installs collapsed in `<details>`, clear documentation map, and a crisp license footer.

### Law 3. Playful Visuals Woven Seamlessly ✨
What separates an unforgettable README from a thousand lookalike repos:
* **Editorial wraps:** Place transparent, expressive art beside prose (`align="right"` + `<br clear="all">`) with restraint — one starring moment plus an occasional clever cameo where it amplifies the mood.
* **Living cutouts over gray quotes:** Replace lifeless Markdown blockquotes with crisp, transparent product artifacts (chat cards, before/after comparisons, status snippets) that feel lifted straight out of a live session.
* **Airy typographic act dividers:** Separate 2-4 major acts with featherlight transparent hairline strips and crisp typography rather than chunky boxed banners; let pure native Markdown carry the rest.
* **Focused flows where eyes beat words:** Draw tight 3-4 step diagrams (feedback loops, parallel lanes, `Usual -> Ours` contrasts) alternating with crisp prose — never turning the whole page into a slideshow.

### Law 4. Graphics That Look Art-Directed on Every Theme 🎨
* **Both GitHub themes, always:** Every custom SVG ships as a matched `dark` / `light` pair via `<picture>` (`prefers-color-scheme: dark` / `light`), blending seamlessly into both `#0d1117` and `#ffffff` with zero harsh patches.
* **Real embedded typography inside SVGs:** GitHub blocks external web fonts inside `<img>` SVGs, so embed the actual WOFF2 font directly inside `<style>@font-face</style>` — crisp editorial type instead of system Arial fallback.
* **Zero AI-slop visuals:** Never settle for generic purple sparkles, neon lightning bolts in dark squircles, or cramped text touching card borders. Give every label generous margins, clean alignment, and intentional craft.
* **Accessible text fallbacks:** Include concise `alt` descriptions and collapsible `<details>` text equivalents for diagrams so screen readers and AI agents never miss a thing.

### Law 5. Explain Like a Human, Not a Compiler 💡
* **Zero internal noise in capability stories:** Readers want mechanics and felt payoff, not source anatomy. Skip file names, internal structs, and variable names; show what you do, what the system does back, and how much time, money, or frustration disappears.
* **Specific, visceral examples:** Every quote and diagram should hit the exact nerve of the feature — real pain, real speedup, real human voice.

### Law 6. The Director's Final Pass 🪞
A README is not done when the last Markdown line is written. It is done when you:
* **Inspect the rendered graphics and layout with your own eyes** on both dark and light GitHub canvases — verifying alignment, contrast, pill padding, zero clipping, and balanced pacing.
* **Verify every file and link is alive:** Zero broken images, zero dead anchors, zero orphan assets left behind, zero violations of repository linters or encoding checks.
* **Pass the 5-second gut check:** Scroll top-to-bottom in 5 seconds — *would you personally hit Star and install this right now?* If yes, ship it.
