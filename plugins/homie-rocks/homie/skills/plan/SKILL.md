---
name: plan
description: Plan a game with the person before building it — sensible defaults from their request, with an interview only when requested that ends in the game's Game Codex, games/<id>/CODEX.md, drawn as a page in the game's own palette, fonts and art that anyone can read and steer (a Claude artifact where the app has artifacts, else a page in their browser, and a private page on the studio's site), kept true as decisions change, with the build's progress on it. Use for step 4 of a new studio, or when someone says "let's plan my game", "what should my game be", "make a design doc, a game bible or a codex", "show me the plan", or before a big change to a game.
---

**Apps:** For a business, venue, cause or customer app, follow the `app` skill: `apps/<id>/app.json`, one morphing screen, roles and parts. Reuse these engines and workflows; do not impose game rounds, scores, bots, a game demo or page navigation. The app check proves shared actions and reconnect; app stores use the same standalone command.


# Plan a game: defaults and its Game Codex

You are in a Homie studio (a folder with `studio.json`) with a game in `games/<id>/`. The plan
comes out as the game's **Game Codex**: `games/<id>/CODEX.md` (the source of truth, in the studio's
repository) and a page drawn from it in the game's own look, with cards, tables and a Build status
tab. People who never read code see the game in it and steer it; you keep it true.

The implementation default is rules plus view on a server room, up to 32 seats.
Choose engineering details yourself; never ask the person to choose hosting, ownership,
tick rate or serialization. Capture the requested mechanic, controls, outcomes and visual
identity in the Codex. Read the game skill's RULES.md before implementing. A live app uses
the same transient rooms, without mandatory scores/bots/rounds, plus authorized records.

## 1. Decide from the request

Default to doing the planning yourself. Choose genre, controls, camera, palette, room size,
round length, bots and scope from the person's premise. Use phones and computers, a small first
version, CC0 art and local sound. Infer cloud saves for persistent characters and collections;
short standalone rounds need none. Record decisions in the codex and continue building.
Never route engineering or design questions to the person. A pub or charity may want an app;
do not force a game interview onto it. Ask only when the intended outcome is missing.

When the person explicitly asks to plan together, use references/INTERVIEW.md as an optional
conversation aid. Their earlier answers count. Paid media needs a budget; use local assets until then.
Run `style init <id> --prompt "<their words>"` with automatic defaults unless they requested hands-on styling.

### While planning: what already exists

Before the scope is fixed, look for what the game can be built from, two different things, and tell the person in a
line each:

- the `@homie-rocks/*` packages (npm) for the general mechanism: camera, input, audio, effects;
- `parts_find` for pieces other studios shared: a creature, a level generator, a bot brain. (With a shell and no
  chat tools: `npx --no-install homie-studio parts find "<words>"`.)

Both go in the codex under **Built from**, with the game and studio each part came from and what will be written
from scratch (the `parts` skill).

## 2. Write the codex

```sh
npx --no-install homie-studio codex new <id>      # games/<id>/CODEX.md with every section, in the studio's colours
```

A new studio has no game yet: its game is planned before it is made. With no game `<id>`, `codex new <id> --name
"<Name>"` starts the game's folder with only the codex in it, and once you have recorded the plan, `game new <id> --from
gem-rush --name "<Name>"` makes the game around it (the codex stays).

Never replace an existing codex: change it. Fill every section from the request and your defaults (the format, with an
example: `references/CODEX.md`):

- **The look in the frontmatter**: the game's own `palette` (`bg`, `ink`, `accent` for headings,
  `accent2`, `danger`, `good`), `fonts` (a Google Fonts family that fits: "Press Start 2P" or "Silkscreen"
  for pixel games, a font file from the game's folder, or none), `pixel: true` for pixel art, a `cover`
  from the game's folder, an `eyebrow` and a `tagline`.
- **Cards, not prose**, wherever there are several of a thing: characters, creatures, classes, items,
  places, levels. Each `### Name` has its picture, a chip line (`` `C-01` `good: Ally` `danger: Boss` ``),
  an italic one-line subtitle, a sentence, and `**Key:** value` stats.
- **Controls** as a table with a column per device; **Milestones** as a checklist (`- [x]` done) that
  matches the scope; **Latest** as dated decisions (`- 2026-10-01: ...`); **Open questions** as a list.
- **Pictures** only from the studio's folder (a real frame of the game, its sprites, its cover, art the
  `art` skill made). Until the game has art, a card without a picture is fine; never present a mock-up
  as the game.

## 3. Draw it and show it

```sh
npx --no-install homie-studio codex <id>          # .studio/codex/<id>.html; says what is not decided yet
```

It reports the sections still empty (`missing`), the open questions and any picture it could not use.
Then show it where the person is:

- **An app with artifacts** (Claude Code's Artifact tool, the Claude app): `codex <id> --artifact`
  writes `.studio/codex/<id>.artifact.html`, one self-contained page made to be published as an
  artifact. Publish it (private to the person until they share it), and update the same artifact each
  time the codex changes.
- **Otherwise**: `codex <id> --open` opens the page in their browser. It redraws itself whenever the
  build's progress changes, and refreshes by itself while a build runs.
- **On their phone or anywhere else**, after a deploy: the site has it at `/_studio/codex/<id>/` for the
  owner only, never listed; `npx --no-install homie-studio codex link <id>` gives a one-time link.

In the chat, say what you chose in one line, show the page, and continue. They can change it by asking.

## 4. Keep it true

- **Every decision that changes the plan goes into CODEX.md in the same change**, with a dated line
  under Latest, and the page is redrawn (and the artifact updated).
- Tick milestones as they land; move answered open questions into their section.
- "Where are we?" or "how far along is it?": the codex's Build status tab (or
  `npx --no-install homie-studio progress show`), in a line or two.

## 5. Progress, baked in

Open a progress feed for every build, titled with the milestone it works on:

```sh
npx --no-install homie-studio progress start <id> --title "Milestone 2: the valley and hand-offs"
npx --no-install homie-studio progress stage plan done --note "<the plan in one line>"
```

`build`, `check` and `deploy` report into it; mark what only you know with `progress check`,
`progress spend` and `progress log`; end it with `progress end passed|failed|stopped`. The codex's
**Build status** tab shows it: a percentage, each step and check going green, a "Ready to try" box (the
address and the codex's `try:` line), and what was spent. In Claude Code the status line shows one line
of it (offered in the setup step: `homie-studio statusline --install`). Codex CLI has no command status
line (its `tui.status_line` takes only built-in items), and Homie installs none in Grok Build, so in both the
codex page is the progress view.

## 6. The look, before the first model

Before anything is made for the game's look, its decisions exist (`style init`, above): the automatic path says
one line ("Look: flat low-poly, autumn grove palette, golden hour, high three-quarter camera; open the codex to
change anything"); the hands-on path shows the style board (`style_explore`, or `style board <id>`) and lets them
pick, mix, steer and lock. Models then come from the `models` skill, free routes first.

## 7. Then build

Build with the `game` skill, one agent by default. Use parallel agents when the person requested them.
