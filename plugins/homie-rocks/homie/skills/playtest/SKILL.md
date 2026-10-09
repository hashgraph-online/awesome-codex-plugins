---
name: playtest
description: Playtest a studio's game the way Homie holds its own games to a bar — real browsers on a computer and a phone held both ways, the first ten seconds timed, the look measured (black or flat frames, contrast, detail), how much of the screen the UI covers, the game's real sound captured and measured, a round played with one person trying and one doing nothing, the owner control tests and two strangers finishing a round — then a blind review by a fresh reviewer that never saw the code, and a ranked list of what is weak. Use when someone asks to playtest, test, review, critique or judge a game, asks what is weak or what to fix next, before calling a game finished or publishing it, and after every change that should make it better.
---

**Apps:** For a business, venue, cause or customer app, follow the `app` skill: `apps/<id>/app.json`, one morphing screen, roles and parts. Reuse these engines and workflows; do not impose game rounds, scores, bots, a game demo or page navigation. The app check proves shared actions and reconnect; app stores use the same standalone command.


# Playtest a game

The question is never "does it run". It is: **would a stranger who pressed Play stay for a whole
round, and come back?** Instruments measure what can be measured; a fresh reviewer who never saw
the code answers the rest. A builder never grades its own work.

One script: `scripts/playtest.mjs` in this skill's folder (Claude Code:
`node "${CLAUDE_PLUGIN_ROOT}/skills/playtest/scripts/playtest.mjs" <command>`), run from inside the
studio. It needs Node 22, Chrome and the studio's `@homie-rocks/studio` (for puppeteer-core and its
checks). It opens at most two browsers at a time, all muted: nothing plays out loud.

## 1. Run the site and the instruments

Start the site as a background task that outlives the command (Claude Code: the Bash tool's
`run_in_background`), wait until the play page answers, then:

```sh
npm run dev                                     # background: http://127.0.0.1:8787 (another port: npx --no-install homie-studio dev --port <n>)
node <playtest.mjs> run <game id> --url http://127.0.0.1:8787
```

It takes five to ten minutes; poll its output, never end your turn while it runs, and do not rebuild
while it runs (a rebuild under `npm run dev` can stop the dev server). `--only first,look,ui,sound`
runs some rows; `--seconds 30` plays longer. The live site works too (`--url` the studio's address).
Stop the site afterwards with `npx --no-install homie-studio dev --stop`.

| row | what it does | fails when |
| --- | --- | --- |
| `first <device>` | opens the play page like a stranger on a computer, a phone, a phone on its side, and times four separate things: a seat, the page's first paint (the loading card, not the game), the loading cover lifting, and the first picture of the game itself (cover gone, the game's own frames advancing); frames per second; the GPU | no seat, a cover that never lifts, or no picture of the game in 10 s |
| `move <device>` | waits for a live round and a body that is the player's, then presses right and times the body moving; when nothing moves it presses left too and reports both, with the position, round phase and time left at each press | the body answers after 1.5 s, or neither way moves it in a live round. WARN when only the opposite way moved (a wall on that side looks like this). BLOCKED when no press fit inside a live round with a free body |
| `look <device>` | plays like a person (holds a direction most of a second, sometimes the action, changes its mind) and shoots the screen: brightness, contrast, colour, visible detail, black or one-colour frames, holes where nothing drew, frames that did not change | a black or one-colour frame, pure-black holes; WARN for dark, flat, featureless or still frames |
| `ui <phone>` | waits for active play, holds the thumb on the stick, hides the world, paints the page black then white, and counts what stays: the share of the screen the DOM UI covers and what is opaque in the middle third. Both frames are saved with the game's state at each | over 12% covered, or anything opaque in the middle, during active play. N/A when the screen was the results card, a spectator view, the loading cover or a browser cut off from its room (measured, labelled, not judged by that bar). BLOCKED when the game changed state between the two frames. WARN when it would pass and a DOM HUD element sits under one of the play page's own controls (the room button, the server or chat pill, the banner): the row names the element and the control |
| `sound` | copies what the game sends to its speaker while it is played (no autoplay flag: the real first-touch rule); loudness overall and through a phone speaker, true peak, clipping, gaps, whether each action press answers with a sound, whether music started | silence, clipping; WARN for quiet, gaps, actions without sound, what a phone loses |
| `play` | a computer plays (direction holds and the game's primary action) and a phone does nothing, in the same public room, for a round that starts after both are in: places, scores, round length against `game.json`, lead changes, and which inputs the script really pressed | no round finishes; WARN when doing nothing scores as well as playing, everyone ties, or a bot is far ahead (a measured gap in one scripted round, never "people cannot win") |
| `controls` | the owner tests from `homie-studio port check`: hold a direction 5 s (one straight line, the camera's yaw moves under 10°), alternate directions 10 s (every press goes the pressed way), real touch on Android Chrome (and iPhone WebKit when Playwright's WebKit is installed; otherwise that row says skip), a killed host, a late joiner, the big screen, audio unlock, errors | any of them (`port` skill: `references/CHECKS.md` says what each failure usually means) |
| `round` | `homie-studio check`: two fresh browsers press Play, meet in one room and both see a round finish with both of them in the results; reconnects are reported beside completion | they do not. WARN when the round finished and a browser reconnected on the way |
| `errors` | uncaught errors and failed requests seen along the way | any uncaught error |

**BLOCKED is never PASS.** A browser rendering at a few frames a second (a software renderer, a
machine under heavy load) makes any game look stuck: the rows say BLOCKED and judge nothing. Run
again on a quieter machine. "Could not test" and "tested and fine" must never sound the same.
The same goes for the instrument's own faults: a screenshot decoder that does not finish in 20 s
is stopped, that device's rows say BLOCKED, the browser is closed and the run exits non-zero; a
site address this computer's Node.js cannot look up (a browser may still open it) stops the run as
BLOCKED, "network preflight failed, before any page or game was opened" (the words `check`, `perf`
and `port check` use for it too), and offers the local site. **N/A** means the row did not apply to what
was on screen. One scripted run is one run: report a gap as measured once, and repeat before
concluding.

### What the game tells the instruments

Every press and every picture is recorded with the game's state, read from its port probe
(`exposePort`, the `port` skill) and the play page: round phase and time left, whether the body is
the player's to steer (`busy`), where it is. A game with no probe still runs, and its rows say the
phase was unknown. Three optional things make the rows sharper; none is required:

- In `exposePort(net, { extra: { ... } })`: `alive: () => boolean` (false: spectating until the
  next round), `mode: () => string` (the control mode on screen), `loadout: () => string` (what
  the player holds, when it changes which controls show), `touchHeld: () => boolean`, and
  `drawCalls` / `triangles` (`renderer.info.render.calls` / `.triangles`: the look row then
  reports measured runtime scene cost, which is not the asset inventory's estimate).
- In `game.json`, the primary action, so a shooter is played by firing and not by the space bar:

  ```json
  "playtest": { "primary": { "label": "fire",
    "computer": { "mouse": "left" },
    "phone": { "selector": "[data-action=fire]" } } }
  ```

  `computer` is `{ "key": "<KeyboardEvent.code>" }` or `{ "mouse": "left|right|middle", "at": [x, y] }`;
  `phone` is `{ "selector": "<css, in the game's frame>" }` or `{ "region": [x, y, w, h] }`
  (fractions of the screen). Undeclared, the script presses the space bar and taps a fixed spot,
  says that was a guess, and qualifies anything it concludes from the scores. It does not aim.
- In `game.json`, `"scoring": "together"`: every result row carries the room's one shared total,
  so the play row marks the active-against-idle comparison not applicable.

The UI row measures DOM coverage only. A HUD, labels or hints drawn inside the canvas are hidden
with the world and are not checked for coverage or overlap; REPORT.md says so beside the result.

The UI row also lays the game's visible DOM HUD against the play page's own controls, which the
page draws over the game's frame and reports as `window.__shell.rects` (the game reads the same as
`net.shell` / `net.on('shell')`). A HUD element under a control that stays is a WARN with both
named; under the "N playing" chip, which fades, it is a note. Fix it by laying the HUD out around
`net.shell`'s rectangles, or by moving the page's controls (`game.json` `screen.share`,
`screen.chat`). A page that reports no layout (an older studio) is said to be unchecked.

A reading taken while the browser was not in its room is labelled, never judged as play: the
helper's link (`window.__homieNet.link`, and `window.__shell.link.state`) says `reconnecting`,
`alone` (the room never answered and the browser hosts by itself), `offline` or `closed`, and a
press, a picture or a UI frame sampled then is BLOCKED or N/A with "CUT OFF from its room" in its
state. The round row says a browser "was seen cut off" beside completion.

The run writes `.playtest/<game>/<time>/` in the studio (added to `.gitignore`): `REPORT.md`,
`report.json`, contact sheets (`sheet-desk.png`, `sheet-phone.png`, `sheet-phone-landscape.png`),
every screenshot (the UI row's pair as `*-ui-on-black.png` and `*-ui-on-white.png`), `sound-capture.wav` and its spectrogram, and the owner-test receipts.
**Open the contact sheets and look at every picture before believing any number.**

## 2. The blind review

```sh
node <playtest.mjs> review .playtest/<game>/<time>
```

It writes `REVIEW.md` in that folder: a brief for a FRESH reviewer, with the pictures, the numbers and
a rubric.

**The review hands the game's screenshots to someone outside this session, so ask first, once.**
The command prints `approval`: one self-contained question naming every file it sends (REVIEW.md,
report.json and the listed pictures), the report folder they come from, and the destination (name
it with `--to "<the reviewer>"`: a subagent in this session, or an external command such as a
second coding agent). Ask the person that question word for word. One yes covers that report
folder and that reviewer; another folder or reviewer is a new question. `review-request.json` in
the folder keeps the same list. A host that reviews what an agent sends may still refuse the
transfer: that is the host's decision. Do not rephrase and retry it, and do not send the pictures
another way. Then one of:

- `node <playtest.mjs> review <folder> --local` writes `REVIEW-LOCAL.md`: the same rubric for
  this session to score the contact sheets itself. Nothing leaves the session. It is the builder
  grading its own build, so it is labelled **not independent** everywhere, and you say so in the
  first sentence when you report it.
- Record what happened, always: `node <playtest.mjs> reviewed <folder> --kind independent --by
  "<who>"`, `--kind local --reason "<why>"`, or `--kind none --reason "<why>"`. REPORT.md and
  `report <folder>` then say which review this run had. With no record, or `none`, the review line
  is BLOCKED: a missing review never reads as a passed one. Hand its WHOLE TEXT, unchanged, to a reviewer that has not seen the code, the plan or your
summary (Claude Code: the Agent tool with the file's full contents as the prompt, never just its path
or your summary of it; Codex: a new session). Add nothing about what you built or changed. It plays the game itself, scores it
0-100 in eight parts, and returns gaps ranked by impact, each with evidence it saw and one concrete
fix. Its verdict outranks yours. Put it in the run folder as `VERDICT.json`.

Comparing against other games (the person's references, the studio's last version, a game they
admire): give the reviewer frames of each under shuffled labels, scored before the labels are revealed.
A reference is a bar ("is it as good as that"), never a template ("make it look like that").

A game with models: give the reviewer the style board, the golden images and the lineup pictures
(`homie-studio assets lineup <id>`, in `.studio/art/<id>/`) beside the frames, and add one question: "does every
frame look like ONE game?" (1-10, naming outliers). Record it with `homie-studio assets review <id> --score <n>
--outliers <ids>`.

## 3. Say what is weak

Lead with the numbers and the review, most important first: what fails, then what the reviewer would
fix first. Group findings by cause before proposing work (five complaints about flat shapes are one
missing lighting model, not five jobs). Name the one change that would matter most. Then, if the
person wants, fix it and run the same instruments again; a change that does not measure better than
the version before it is a regression, not progress. When the weak thing is speed (a low frame rate in
`first`, a slow first ten seconds, a phone that struggles), the `perf` skill measures it properly: frame
times and CPU per frame for the host and a replica, alternating runs, and only changes that beat the noise.
When the weak thing is how a move feels (a hit that does not land, a floaty jump), the `lab` skill compares the
change with the last commit frame by frame, with the person.

`references/METHOD.md` has the method behind the rows: playing like a person, the five numbers a
round owes you, the scenarios, seats with different strategies, the do-nothing test, the ten-second
test, and the traps that make an instrument lie.

## Never

- Never call a game good, fixed or finished from the code, a build that passed, or your own look at it.
- Never report a local review as a blind one, and never read a BLOCKED or N/A row, or a missing review, as a pass.
- Never turn one scripted round into a rule ("people cannot win", "input does not matter"): say what was measured, and run it again.
- Never let the builder grade the build: the reviewer is fresh, every time.
- Never script a player to make a number look good; the instruments play like a person on purpose.
- Never leave a room open on a live site: the playtest's browsers leave when it ends; do not start
  more than two browsers of your own beside it.
