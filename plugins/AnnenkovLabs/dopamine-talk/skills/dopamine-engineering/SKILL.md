---
name: dopamine-engineering
description: >-
  Activates sharp, adaptive engineering with zero hardcode, zero regex crutches,
  zero dead abstractions, zero mock-only theater, and genuinely intuitive UI
  craft. Combines flexible zero-regex architecture, the simplicity ladder
  (ponytail), single-pass recon and real-run verification (benjamin-plus),
  visual restraint and micro-interactions (taste-skill), purpose-built tactile
  controls over lazy inputs and buttons, minimal on-screen decisions, and clear
  human UI copy free of both AI fluff and cryptic fragments (bro-skill, unslop,
  better-writing, Dopamine Talk). Triggers: "dopamine-engineering",
  "dopamine engineering", "build it clean", "no hardcode", "no regex hacks".
license: MIT
---

# Dopamine Engineering — Adaptive Code, Clean Roots & Tactile Craft

Default coding agents fail at both ends at once: in backend and agent code they pile up brittle regexes, hardcoded branches, dead factories, and 40 mocked unit tests for show — while in the frontend they dump walls of generic inputs, a button for every minor action, and bloated AI copy (which turns into cryptic chopped fragments the moment you ask them to shorten it).

This skill switches on **sharp systems and product engineering**: minimal clean code at the foundation, zero silent downgrades, real-run verification, and interfaces that feel effortless and purpose-built on first touch.

---

<active_skill name="dopamine-engineering">
CORE MODE DIRECTIVES:
1. **Zero hardcode, zero regexes in logic:** Never use regexes for semantics, business logic, parsing live text/code, or papering over bugs. Build universal, adaptive mechanisms (real parsers, `AST`, clean contracts, composition, and the model's own intelligence).
2. **Simplicity ladder in code, zero laziness in UX:** In architecture, stop at the simplest rung that holds (reuse existing repo helpers, stdlib, native platform features — zero single-implementation abstractions). In **user-facing UI**, never be lazy: prefer purpose-built tactile controls (sliders, scrubbers, swatches, direct manipulation) over generic text inputs and buttons — even when you have to build them custom.
3. **Single-pass recon, green means the live check:** Batch independent lookups in one pass, probe the environment once, and verify with a real live run instead of mocked theater. Two failures on the same approach means the approach is wrong — switch strategy, never glue a third patch on top.
4. **Minimal decisions and crystal UI copy:** Never slap a button on every action — hide, simplify, default smartly, and keep one primary action in focus. Cut AI fluff, but never mutilate useful labels into cryptic stubs.
</active_skill>

---

## 1. Adaptive Core: Zero Hardcode, Zero Regex & The Simplicity Ladder 🧠

### Ban Brittle Logic and Regex Crutches
* **Regexes in engineering logic are a smell.** They shatter on the first unexpected input. For code and structured formats, use real parsers, `AST`, and typed schemas. For live text, user intent, and agent routing, rely on structured outputs and the model's own reasoning instead of `if (text.includes(...))` tables or regex hacks. *(Reserve regex strictly for fixed-standard formats like hashes or identifier validation.)*
* **Tight strong core over 7-layer over-orchestration:** never split a living workflow into routers, classifiers, validators, and critic layers when one clean, transparent loop runs faster, preserves full context, and adapts naturally.

### The Simplicity Ladder (from `ponytail`)
**Understand the full flow first** — minimalism shortens the solution, never the reading. Then stop at the highest rung that genuinely holds:
1. **Does this need to exist at all?** Speculative "just in case" need -> skip it.
2. **Already in this codebase?** Reuse the neighbor helper instead of re-implementing it two files away.
3. **Stdlib solves it?** Use stdlib.
4. **Native platform feature covers it?** Plain CSS over a JS widget library, DB constraint over app code, native engine/OS API over a wrapper.
5. **Already-installed dependency covers it?** Use it — never pull a new package for 15 lines of work.
6. **Only then, the cleanest minimal code:** no interface with one implementation, no factory for one class, no config knob for a constant.

### Clean-Root Rule & Zero Quiet Downgrades
* **Bug fix = root cause once.** Grep callers before editing: one clean fix at the shared root beats five symptom guards.
* **No patch-on-patch decay:** if a bug demands a second workaround in a row, stop — rip out the broken root and rebuild cleanly so the bug disappears structurally.
* **No quiet downgrades or stubs:** when the plan commits to a cutting-edge method or zero-alloc optimization, ship the full working implementation using native stack power. If you hit a real hardware or `API` ceiling, report it upfront with a strong alternative — never silently swap in a toy stub.
* **When never to cut corners:** trust-boundary validation, data-loss prevention, security, core accessibility, and anything explicitly requested.

---

## 2. Execution Tempo, Recon & Live Verification (from `benjamin-plus`) ⚡

Every wasted step and giant log dump gets re-read on every turn. Work cleanly and decisively:
1. **Recon in one pass:** gather all independent facts in a single turn (parallel reads or one chained probe). Copying a local convention or DSL? Sample **two live examples**, not one.
2. **Keyhole reads:** inspect with limiters (`head`, `grep -m`, line ranges). Read a file whole only when editing or transforming it verbatim.
3. **Probe the environment once:** check every needed package/binary in one command and install missing items together instead of stepping through five tracebacks one by one.
4. **Green means the task's own live check:** skip 40 mocked unit tests built purely for a green report. Leave **one runnable check** for non-trivial logic that actually fails when broken, and verify with a **real build, live launch, or real-data run**.
5. **Two-strike strategy switch & stop when green:** if the same check fails twice on the same approach, the approach is wrong — switch strategy instead of patching symptoms. Once the live check passes, **stop**: no victory laps, no re-reading files you just wrote, no 1-second busy-polling loops.
6. **Last-centimeter polish:** before handing off, look with the user's eyes — eliminate any obvious stutter, N+1 query, or extra click right next to your change (without sprawling into an unrelated repo-wide refactor), then close concisely with what now works and the payoff.

---

## 3. Product UX & UI Craft: Tactile Controls, Clarity & Taste 🎨

Whenever you build frontend or user-facing software, **never take the lazy shortcut**:

### 3.1. Purpose-Built Tactile Controls Over Lazy Inputs & Buttons
Stop defaulting to `<input type="text">`, bare `<select>`, and rows of identical buttons. Pick the **most physically natural control for the data** — even when no built-in component exists and you need to craft a clean custom one:
* **Numbers, ranges, intensity, scale, volume, time:** live responsive slider, dual-thumb range, or click-and-drag number scrubber.
* **Color, theme, accents:** tactile swatches and live picker with instant preview.
* **2-4 mutually exclusive modes:** segmented control or visual cards instead of a buried dropdown.
* **Position, order, curves, regions:** direct dragging, canvas handles, and live manipulation.
* **Dates & schedules:** instant presets ("Today", "Tomorrow", "Next week") + visual picker instead of typing `YYYY-MM-DD`.

### 3.2. Effortless Intuition & Minimal Decisions On Screen
* **Never put a button on every action.** A screen bristling with 12 buttons, 6 filters, and 4 toggles freezes the user.
* **One primary action per screen or focal region.** Hide, simplify, automate, or progressively disclose secondary and advanced actions (contextual controls on hover/selection, clean overflow menus, smart defaults).
* **Eliminate the choice first:** if the system knows the right answer 90% of the time, apply it automatically instead of asking the user to micromanage it.

### 3.3. Visual Taste (from `taste-skill`)
* **One coherent system:** one button family, one spacing and radius scale, equal left/right edges, **at most two nested container levels**.
* **Show the real thing:** no empty decorative filler cards, no apologetic captions under visuals, no default purple/violet AI gradients.
* **Quiet, crisp micro-interactions:** every interactive control visibly responds to hover and press using `transform` and `opacity` (~150 ms hover, ~90 ms press; never animate `width`/`height`, never fade-in every card on scroll).
* **Inspect the real render:** check desktop and mobile viewports with your eyes — zero clipping, zero collisions, zero broken alignment.

---

## 4. Frontend Copy: Clear at First Glance, Zero Fluff, Zero Cryptic Stubs ✍️

Synthesizing `bro-skill`, `unslop`, `better-writing`, and `Dopamine Talk`. AI frontends oscillate between two bad extremes: drowning screens in wordy slop, and — the moment you ask to trim — deleting vital meaning and chopping labels into ugly abbreviations (`Cfg.`, `Sett.`, `Sys. Prm.`, `Err 400`, `OK`).

### Clarity Over Arbitrary Word Count (`bro-skill` + `Dopamine Talk`)
* **Simpler does not mean shorter at any cost.** The target is **"impossible to misunderstand on first glance"**, never fewest letters.
* **Delete filler and obviousness, keep full meaning:** cut intro paragraphs, repetitive eyebrow labels, picture captions, and text explaining what the UI already shows visually. When four plain words make an action unmistakable, keep all four — never chop them into stubs.
* **Human outcome over machine jargon:** write `Refresh list`, not `Flush DOM index cache`; `Save draft`, not `Commit state snapshot`.

### Anti-Slop Copy Filter (`unslop`)
Cut on sight from every screen:
* **AI hype words & frames:** *seamless, robust, powerful, elevate, unlock, comprehensive, cutting-edge, next-generation, "not just X, but Y"*. Replace with concrete action or numbers.
* **UI talking about itself:** *"In this section you can configure..."*, *"Below you'll find..."*.
* **Restating labels:** never `Speed: Speed improved...`.
* **One name per concept:** if the menu says `Archive`, the toast says `Archived`, never `Moved to storage`.

### Sharp Microcopy (`better-writing`)
* **Verb-first buttons naming the object:** `Delete project`, `Save draft`, `Export CSV` — never `OK`, `Yes`, `Let's go!`, or bare `Learn more`. Destructive confirmations repeat the consequence (`Delete project` / `Cancel`).
* **Toggles describe the ON state:** `Send read receipts`, never `Don't send read receipts` (zero double negatives).
* **Errors say how to fix, right beside the field:** `Use at least 8 characters`, never `Invalid input` or `Oops! Something went wrong!`. Better yet, redesign the control so the error cannot happen.
* **Empty states point forward:** state what lives here plus **one clear next action** (`Create a project`), never a bare `No data`.
* **Placeholders show format examples** (`name@example.com`), never replace a visible label.

> **Fail (bloated):** "In this settings panel you can seamlessly configure rendering quality parameters for an elevated experience" + text box `Enter value 0-100` + `OK` button.
> **Fail (after "shorten it"):** "Rend. Cfg." + box `0-100` + `App.` button.
> **Dopamine Engineering:** Label `Render quality` + live tactile slider showing `75%` with instant preview (zero redundant `Apply` button).

---

## 5. One-Second Pre-Ship Tuning Fork

1. Stripped hardcode, regex logic, dead wrappers, and patch-on-patch hacks?
2. Verified via a **real live run** (not mock theater) and stopped cleanly once green?
3. Used purpose-built tactile UI controls, trimmed screen choices, and kept copy crystal clear with zero fluff and zero chopped stubs?
4. Reported the live result and real payoff concisely — no file-path dump?
