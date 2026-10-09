---
name: plan
description: Plan a game with the person before building it — a short, natural interview (game type and genre, style and art direction, devices, players and rooms, progress that lasts (cloud saves, player accounts), art and film, music and sound, scope) that ends in the game's Game Codex, games/<id>/CODEX.md, drawn as a page in the game's own palette, fonts and art that anyone can read and steer (a Claude artifact where the app has artifacts, else a page in their browser, and a private page on the studio's site), kept true as decisions change, with the build's progress on it. Use for step 4 of a new studio, or when someone says "let's plan my game", "what should my game be", "make a design doc, a game bible or a codex", "show me the plan", or before a big change to a game.
---

**Apps:** For a business, venue, cause or customer app, follow the `app` skill: `apps/<id>/app.json`, one morphing screen, roles and parts. Reuse these engines and workflows; do not impose game rounds, scores, bots, a game demo or page navigation. The app check proves shared actions and reconnect; app stores use the same standalone command.


# Plan a game: the interview and its Game Codex

You are in a Homie studio (a folder with `studio.json`) with a game in `games/<id>/`. The plan
comes out as the game's **Game Codex**: `games/<id>/CODEX.md` (the source of truth, in the studio's
repository) and a page drawn from it in the game's own look, with cards, tables and a Build status
tab. People who never read code see the game in it and steer it; you keep it true.

## 1. The interview: natural, not a form

Collect all eight topics, in whatever order the conversation goes:

1. **Game type and genre**: what kind of game, what a player does in the first ten seconds, how a round
   is won. Why it is fun with strangers who just pressed Play.
2. **Style and art direction** (the Style phase): pixel, painterly, low-poly, neon, hand-drawn; mood; two or
   three games, films or pictures it should feel like; the palette. Ask once whether they want to steer the
   look closely (the style board) or have you pick, and the art budget (free only, a small budget on their own
   fal account, or their number). Then the decisions: `npx --no-install homie-studio style init <id> --prompt
   "<their words>"` (add `--hands-on` and `--budget <usd>` from their answers) fills every look decision with a
   pick and a why, which the codex's Art direction tab draws; the `style` skill has the rest.
3. **Devices**: phone, computer, TV with phones as pads. Every Homie game plays on phones and computers;
   say what changes on each (touch on the lower left, keys, the big screen).
4. **Players and rooms**: how many in a room (up to 32), teams or free-for-all, round length, what bots do
   in empty seats, what a player who arrives mid-round gets.
5. **Progress and saves**: always ask it plainly: "Does progress need to persist across sessions or devices?"
   A round that is all there is (a brawl, a race) needs nothing. A character that levels up for days, unlocks,
   a collection, a hardcore mode with one life: yes. Then the game keeps it in **cloud saves** (player accounts
   with passkeys, a guest's progress kept until they make one), never in the room, which forgets everything 60 s
   after its last player leaves. Ask what is kept (the hero, the inventory, unlocks), what lifetime stats count
   (kills, gold, time played), and whether a death can be forever (hardcore: a wipe and a memorial in the hall of
   the fallen). Write it into the codex under **Rooms and players** as "Progress that lasts", with a dated line
   under Latest; the `game` skill wires it in.
6. **Art and film**: characters, creatures, places; the cover; a trailer or a cutscene; what is made
   from the game itself (free) and what is painted or generated (the `art` and `video` skills, on their
   own accounts, under a budget).
7. **Music and sound**: the theme's mood and tempo; the sounds that matter (a pick-up, a hit, a win);
   synthesized here for free (the `sound` skill) or songs from ElevenLabs (the `music` skill).
8. **Scope**: what the first playable version has, what comes later, and the milestones between.

How to ask:

- **Two or three questions a message**, never all seven at once. Start from what you know: the starter
  they saw, the change they asked for, the studio's name.
- **Each question offers concrete options and your pick**, so "yes" is an answer: "Pixel art, painterly,
  or clean vector shapes? For a fast arcade game I'd go pixel: it reads well small on a phone."
- **Say back what you heard** in one line before the next questions ("So: a relay race in a burning
  valley, two teams, 90-second rounds.").
- **"You pick"** means pick, say it in one line, and move on.
- **Stop when every topic has an answer or a default**, usually after three or four messages. If they
  say "just build it", fill the rest with your own choices and list them under Open questions.
- `references/INTERVIEW.md` has questions with options for each topic and genre.

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
"<Name>"` starts the game's folder with only the codex in it, and once the plan is agreed, `game new <id> --from
gem-rush --name "<Name>"` makes the game around it (the codex stays).

Never replace an existing codex: change it. Fill every section from the interview (the format, with an
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

In the chat, say what is in it in three to five lines and ask what to change. Change, redraw, show
again, until they are happy. Then tick step 4 of the new-studio checklist.

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

Offer the choice in the `parallel` skill (one agent, or several at once), then build with the `game`
skill, a milestone at a time.
