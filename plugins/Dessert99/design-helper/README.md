# design-helper

[![last commit](https://img.shields.io/github/last-commit/Dessert99/design-helper)](https://github.com/Dessert99/design-helper/commits/main)
[![release](https://img.shields.io/github/v/release/Dessert99/design-helper)](https://github.com/Dessert99/design-helper/releases)

[English](README.md) | [한국어](README.ko.md)

> A Claude Code skill for picking CSS values, layout and motion by looking at them.

> [!NOTE]
> Replies and every string on the comparison sheet are in **Korean**. See [Language](#language) to change that.

<!-- screenshot of a specimen sheet goes here -->

## Why

Asked in chat, "12px or 16px padding?" is hard to answer. Few people can picture a
shape from a number, so you end up putting one in the code, reloading, and trying again.

design-helper draws every candidate instead and puts them side by side in your browser.
You look and pick.

Use it when, for example:

- you want to try a component with a few different borders
- you want to settle the base layout of a page

## What it does

A typical round:

```
you   Show me the card's shadow blur in 5 versions

      → reads the project's style system and the card's current values
      → draws cards A–E with only the blur changed: 4 · 8 · 12 · 16 · 24px
        (color, opacity, offset and the rest stay as they are)
      → labels each specimen with its value and cost:
        토큰 그대로 · --shadow-md 고침 (23곳) · 새 토큰
        (token as-is · edits --shadow-md in 23 places · new token)
      → under the cards, notes where the differences stop showing and which
        one it recommends, and why

you   C is better, but a bit darker

      → adds an opacity ladder below, starting from C (F · G · H …)

you   Go with G

      → checks what else it touches, applies it to the real card, checks the
        computed style and a screenshot, and reports back

you   Done

      → stops the server and deletes the temporary files
```

Only one property changes at a time and everything else stays put, so any difference
you see comes from that property. Each value you pick carries into the next comparison.

- **You don't copy values.** Say a letter in chat and the skill edits the code.
- **The sheet explains itself.** Each section starts with what to decide, where to look
  and how to answer. Each specimen shows its value and cost, plus what it gains and
  loses when that matters. A table of contents on the left lists every request, so you
  can jump back to an earlier comparison.
- **You don't refresh.** When the sheet changes, the skill reloads the tab and brings it
  to the front. If the agent can't control a browser, it says so and gives you the URL.
- **Your project stays clean.** The sheet, server, notes and screenshots live in a
  temporary folder outside the project. The only thing left behind is the code for the
  values you chose.
- **It draws in your style system.** Tailwind and CSS variables are drawn with your real
  classes and tokens. The browser can't read SCSS variables or CSS-in-JS themes, so their
  values are copied into the sheet as CSS variables. With no style system, it writes
  values directly.

## What it doesn't do

- **It doesn't make up a design.** It shows a range of values to compare, not a finished
  look. It recommends one option and says why, and notes what each option gives up,
  but you make the pick.
- **It doesn't plan your next step.** No "let's look at color next" and no list of
  remaining steps. You decide what to look at next.
- **It can't check behavior.** Focus traps, keyboard handling and screen readers can't
  be judged by eye, so they're out of scope.
- **You judge motion.** Screenshots only capture a still frame, so animation is settled
  by what you see in the browser and tell it.

## Requirements

- [Claude Code](https://claude.com/claude-code) or Codex
- A browser
- `python3` to run the local server that serves and auto-reloads the sheet. Without it
  the sheet opens over `file://`, with no auto-reload and no automatic cleanup of the
  temporary folder after two idle minutes.
- Playwright (optional) to read computed styles and take screenshots. Without it that
  check is skipped.

## Install

### As a plugin (recommended)

This repository is a plugin marketplace for both agents.

```sh
# Claude Code: inside a session
/plugin marketplace add Dessert99/design-helper
/plugin install design-helper@design-helper

# Codex: from the shell
codex plugin marketplace add Dessert99/design-helper
codex plugin add design-helper@design-helper
```

Start a new session afterwards so the skill loads. To update, refresh the marketplace
(`/plugin marketplace update design-helper` in Claude Code,
`codex plugin marketplace upgrade` in Codex) and install again.

### From a clone

Use this if you want to edit the skill, for example to [change its language](#language).
Clone it anywhere and symlink the skill folder into your agent's skills directory. The
symlink points at the clone, so your edits take effect right away and there's no copy to
keep in sync.

```sh
git clone https://github.com/Dessert99/design-helper.git ~/src/design-helper

ln -sfn ~/src/design-helper/skills/design-helper ~/.claude/skills/design-helper   # Claude Code
ln -sfn ~/src/design-helper/skills/design-helper ~/.codex/skills/design-helper    # Codex
```

Both agents read the `description` in `SKILL.md` when a session starts, and the body and
`references/` when the skill runs. Edits to the body apply immediately; a changed
`description` needs a new session.

To remove it, delete the symlink (`rm ~/.claude/skills/design-helper`). The clone stays.

## Usage

Talk as you normally would while building or changing UI. Requests like these trigger it:

- "Show me 5 versions of the button radius"
- "Which is better, A or B?"
- "Compare the card padding"
- "This header feels off, what should I do?" If it isn't clear what to change, it asks
  one question at a time.
- "Lay out the dashboard." With no design yet, it starts with a few very different
  combinations. The one you pick isn't written to code; it's noted as a starting point,
  and properties are then settled one at a time.

Specimens in the browser are lettered A · B · C. You answer in chat.

| You say | It does |
|---|---|
| "Go with C" · "I like B" | Takes it as your pick, applies it to the code and checks it. A combination picked on a blank slate is only noted as a starting point |
| "C is better, but darker" | Takes it as a request to compare more and adds a ladder below |
| "Nice" | Asks which specimen you mean |
| "Done" | Stops the server and cleans up the temporary files |

Example conversations are in the [usage flows](docs/flows.ko.md) (Korean only). They
cover 11 situations, including not knowing what to change, comparing hover and focus
states, comparing animation, and changing a value you already picked.

## Compared with similar skills

Checked in September 2026 against the commits linked below. Most of these skills help
you decide **what to make**; design-helper helps you decide **what value a thing you've
already decided on should have**. They work well together.

**[frontend-design](https://github.com/anthropics/skills/tree/33375500bcea98d610eb30ce10ac4e59b89c390d/skills/frontend-design)** (Anthropic, official)
- What it does: has the agent think like a design lead and pick bold, deliberate styling over the usual AI look.
- Difference: it doesn't draw candidates to compare; the agent sets the taste. design-helper draws candidates and recommends one, and you pick.
- Use it when: you want a polished first design from a blank page in one go. design-helper won't come up with a direction for you.

**[playground](https://github.com/anthropics/claude-plugins-official/tree/aecd4c852f10b466245f18383fa6aad8c0b10d57/plugins/playground)** (Anthropic, official plugin)
- What it does: builds a single HTML file with controls on one side and a live preview on the other, and you copy the result out as a prompt to paste back into Claude. Besides design, it has templates for data, code structure, and document review.
- Difference: one preview carries sliders for several properties, so you see one state at a time. design-helper fixes candidates that change one property and puts them side by side, then applies your pick to the code and checks it instead of handing back a prompt.
- Use it when: you want to get a feel for a combination by playing with it, with no single right answer, or you need an explorer for something that isn't design.

**[impeccable](https://github.com/pbakaus/impeccable/tree/9d715cc4f5564a990ca8345abfdd5df6dc9b41c8)** (pbakaus)
- What it does: a design vocabulary, anti-pattern rules, and commands like `audit` · `polish` · `typeset` · `layout`. In live mode you pick an element in the running app, flip through variants in the browser, and the one you accept is written to source. It reads your CSS tokens and computed styles, and variants can have tuning sliders.
- Difference: the closest match. Its variants rebuild the whole element, so several properties change at once, and you see them one at a time. design-helper puts a ladder that changes one property on one screen, side by side, and labels each specimen with its token impact.
- Use it when: you want to pick directly in the real app, or run a design audit and polish with one command.

**[visual companion](https://github.com/obra/superpowers/blob/8ca22dba9a94f28898bbce59f2537ff4d87c747d/skills/brainstorming/visual-companion.md)** (part of the brainstorming skill in obra/superpowers)
- What it does: while you brainstorm before building, it shows mockups, diagrams and side-by-side comparisons in the browser, and you click to pick. It also helps with spacing and visual hierarchy.
- Difference: it doesn't make one-property ladders, applying the pick to code, or checking it afterwards part of the process. In design-helper those are the default.
- Use it when: you need visuals that aren't UI, like architecture diagrams, or you're setting direction before building.

**[design-shotgun](https://github.com/garrytan/gstack/blob/2a113ae7e623f590095bcaaa0cc581c9a10a6632/design-shotgun/SKILL.md.tmpl)** (garrytan/gstack)
- What it does: generates 3–8 different mockups as images, shows them on a comparison board, collects ratings and notes, and generates again. It remembers the taste you approved.
- Difference: the output is images (PNG), not code, so another skill has to apply it, and it needs an image-generation tool. design-helper draws in CSS with no extra tools.
- Use it when: you don't know yet what you want and want to see many directions.

**What design-helper does differently**: one-property ladders side by side, the impact of each specimen written next to it, trade-offs and a recommendation under the specimens, the pick applied to code and checked, and working files kept outside the project.

**Where design-helper falls short**: it doesn't propose a finished design direction, doesn't detect anti-patterns, compares on a separate sheet rather than in the live app, and replies only in Korean by default.

## Language

The instructions are in English, but chat replies and everything on the comparison
sheet are in Korean. Code, class names, file names and commit messages stay in English.

To change it, install [from a clone](#from-a-clone) and edit the `## Language` section in
`skills/design-helper/SKILL.md`. A plugin install is replaced on every update, so edits
there don't last. The Korean phrases quoted in the instructions (`토큰 그대로`, `끝났어`
and so on) need to change too.

## Docs

- [`SKILL.md`](skills/design-helper/SKILL.md): the skill itself. The work unit, drawing rules, reading replies, checking, finishing
- [`references/`](skills/design-helper/references/): detailed instructions the skill reads when needed
  - [`clarification.md`](skills/design-helper/references/clarification.md): asking about a vague request
  - [`sweeping.md`](skills/design-helper/references/sweeping.md): candidate values, captions and the recommendation, background and size, starting from a blank slate, wireframes
  - [`sheet.md`](skills/design-helper/references/sheet.md): the sheet page's section guide, request dividers, table of contents, layout and style
  - [`stylesystems.md`](skills/design-helper/references/stylesystems.md): detecting the style system and drawing in each one
  - [`controls.md`](skills/design-helper/references/controls.md): optional sliders and their engine
  - [`motion.md`](skills/design-helper/references/motion.md): comparing animation
  - [`liveview.md`](skills/design-helper/references/liveview.md): the temporary folder, local server, browser tabs, cleanup
- [`docs/flows.ko.md`](docs/flows.ko.md): usage flows by situation (Korean)
- [`scripts/bump-version.sh`](scripts/bump-version.sh): sets the version in every plugin manifest, then commits and tags the release

## License

[MIT](LICENSE)
