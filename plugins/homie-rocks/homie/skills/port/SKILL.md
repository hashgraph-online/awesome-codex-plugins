---
name: port
description: Make an existing single-player web game multiplayer in a Homie studio. Reads the game (loop, input, state, camera), grades the port easy, medium, hard or not a fit and says why, adds netplay public rooms (bots in empty seats, join in progress, host handoff, rounds), phone touch controls, a stable camera and the big-screen view, proves it with the owner tests (held and alternating directions, real touch on iPhone WebKit and Android Chrome, a late joiner, a killed host, two fresh browsers finishing a round), then deploys it to the studio's own Cloudflare and lists it. Use when someone says "make this multiplayer", "make my game multiplayer on Homie", "port this game to my studio", or points at a single-player web game.
---

# Make a game multiplayer (port)

A port is done when strangers who press Play land in the same live room, each
browser renders the game itself, bots fill the empty seats, rounds end and restart,
the controls mean the same thing every second on a phone and a computer, and the
checks below pass on the live site. Take as long as it needs; quality is the bar,
not speed. Never call it done on a guess: the checks say, or you say plainly what
still fails.

The person should not have to type anything after asking. Find what you need,
decide, and keep going. Stop only for something only they can give: the one
Cloudflare approval, a licence question, or a game that is not a fit.

**Finish in this turn.** A port takes a long time; stay with it until it is live and
checked. Never end your turn, schedule a wake-up, or hand back "it is running" while
a check, a build or a deploy is still going: wait for it by polling (a short `sleep`
then `tail` of its log, repeated) and keep working. When your turn ends, the
processes you started (the dev server, a running check) end with it, and a
half-ported game is left behind.

## 0. Find the game and the studio

- **The game** is the folder they named, or the current folder if it holds an
  `index.html`. Otherwise look one level down for the only folder with one.
- **The studio** is the folder with `studio.json`: here or above, else next to the
  game (`find .. -maxdepth 2 -name studio.json`). One found: use it. None: set one
  up first with the `studio-setup` skill (name it after the person's game), then
  come back. Several: use the one the person named, or ask which.
- **The toolkit.** In the studio, `npx --no-install homie-studio port plan <game>`
  must work. If it says unknown command, the studio's `@homie-rocks/studio` is older than
  the port toolkit: call the Homie MCP tool `game_port` for the pinned package and
  install it exactly as it says, then run `npm install`. Without the connector,
  `npx -y @homie-rocks/studio@latest upgrade` says what to change (the `studio-setup` skill, "An existing
  studio that is behind").

## 1. Read it and grade it (before changing anything)

```sh
npx --no-install homie-studio port plan <game folder>
```

The plan is a draft from reading files: engine, loop, input, camera, physics,
storage, audio, size, licence, risks, and a grade. Now read the code yourself: the
main loop, where input is read, what the state is (player, enemies, pickups, level,
score), how the camera moves, what "game over" is. Then write `PORT.md` in the game
(template: [references/PORT-TEMPLATE.md](references/PORT-TEMPLATE.md)) with:

- **the grade** — easy, medium, hard (fast physics, precise timing, huge state), or
  **not a fit** — and one paragraph of why, in plain words;
- the multiplayer design: what a round is, what the host owns, what each browser
  owns, what bots do, how a late joiner comes in, what the big screen shows;
- the movement mode: **owner** for action games (each browser moves its own body
  at once, the host bounds it), **host** for turn-based and grid games (the host's
  rules move bodies from intents);
- controls on keys and on touch, and the camera rule (below).

Tell the person the grade and why in two or three lines, then go on. If it is
**not a fit** (it needs its own server, WebAssembly threads, or its licence forbids
it), stop there and explain what would make it portable. The port toolkit is in beta:
a game that is not a fit today, or a port the checks cannot judge, is worth a port
request at https://github.com/homie-rocks/homie/issues/new/choose (the game's public
address and licence, the grade and why; no keys or private addresses).

Licence: a game you did not make must carry a licence that allows changing and
publishing it (MIT, Apache-2.0, BSD, ISC...). Keep the licence file with the game.
No licence, or a licence that forbids it: port it for private testing only and say so.

## 2. Bring it into the studio

```sh
npx --no-install homie-studio port import <game folder> --id <id> [--name "<Name>"]
```

It copies the game to `games/<id>/` untouched except: the port toolkit loads first
in `<head>` (sandbox shims, first-touch audio, `window.HomiePort`) and the viewport
is phone-safe. `game.json` says how it builds: `static` (the folder as it is, for
plain `<script>` games), `bundle` (an ES-module entry bundled by esbuild), or
`command` (its own Vite/webpack build; set its base to `./`). The id is the
game's address: lowercase, digits, hyphens.

## 3. Port it

Follow [references/RECIPE.md](references/RECIPE.md): it has the worked example
(a single-player canvas game turned multiplayer with `createRoom`), the patterns
for turn-based, 2D action, platformer/physics and 3D games, and what goes in
snapshots, keyed state and checkpoints. The rules that people's hands and real
phones taught, with the bugs behind them, are in
[references/LESSONS.md](references/LESSONS.md). Read both before writing code.

Non-negotiable, every port:

1. **Instant start.** The first visitor is playing within seconds, with bots.
   No title screen, no "press Space", no waiting for players, no "tap for sound".
2. **Rounds.** A single-player "game over" becomes a round: a clock (60–180 s), a
   score race or a goal, results for a few seconds, then the next round by itself.
   Death respawns; it never ends a person's round.
3. **Bots** fill every empty seat, play by the same rules through the same inputs,
   and are beatable. An arriving person takes a bot's body where it stands.
   **Make your bots honour the skill dial** (servers, NETPLAY.md section 17): give
   `BotBrain` `skill: () => room.skillOf(body)` (reaction, aim and commitment follow
   the party's vote) and use `jitter`, `engages` and `standoff` for the rest of a
   bot's choices. `createRoom` keeps a hybrid server's AI seats and labels them AI.
   For guides that talk (a beginner server), give the game a vocabulary and `useAgents`
   (the game skill's "Write the guide vocabulary"; NETPLAY.md section 18). For AI that
   picks the bots' tactics or a director's call, `room.net.decide` per beat, never per
   frame, opt-in and with the game's own floor (the game skill's "Let the game decide
   with AI"; NETPLAY.md section 20).
   Room chat needs nothing from a port (the play page has it); draw speech bubbles over
   characters with `createBubbles` / `paintBubbles` from `net.on('say')` (NETPLAY.md section 19).
4. **Host handoff.** Everything the rules need is in the checkpoint; a promoted
   browser continues the SAME round (clock, scores, world).
5. **Controls mean the same thing every second.** Input is read on the camera's
   screen axes, never the character's facing. Tank/rotate controls become
   screen-relative (a direction held = go that way on screen). The camera never
   turns by itself while a direction is held.
6. **Phones.** A floating stick where the thumb lands, a few small see-through
   buttons at the edge shown only when useful, nothing opaque in the middle, UI
   under 12% of the screen, no touch UI on computers. Use the touch kit; do not
   write your own touch code.
   The world fills a phone held upright: a fixed arena letterboxed into a strip
   of a portrait screen looks broken. Follow your own body with a camera (your
   body about 14% of the screen's height) or lay the arena out for portrait.
   For a flat (top-down) world the kit's `fitView` does it: the whole world where
   it reads, else the world fills the screen and follows your body, never past
   its edge but for the HUD's margins. Names drawn over bodies pile up when they
   crowd: place them with `createLabels` (yours first, never covered; the rest
   move or fade). Both starters show the pattern.
   Your own body is unmistakable at a glance (a ring or highlight plus "You").
7. **The big screen** (`/<id>/tv`) is a spectator: no body, no personal prompts,
   an overview or director camera, readable from across a room. **A watcher**
   (`/<id>/watch`) follows one player: point the camera at `room.viewBody()` (your
   own local body when it is your seat) and the HUD at its numbers, and fall back to
   the overview when it is null (the recipe's section 8).
8. **The probe.** Call `exposePort` (see the recipe): the checks cannot judge a
   game that does not report where its player is. In its `extra`, set the state hooks the
   playtest and `perf` read by name, whichever the game has (`PortExtra` in the port
   kit types them): `alive`, `mode`, `loadout`, `touchHeld`, and in a 3D game
   `drawCalls` and `triangles` from `renderer.info.render`. The round needs no hook
   (`createRoom` gives it).
9. Randomness that changes the world happens on the host only. Names people type
   are drawn as text, never as HTML.
10. It is still their game: keep its look, its renderer, its feel and its name
    (add "Race", "Arena", "Party" if you like). The port adds multiplayer; it does not
    remake the game, and never rewrites something only to pass a check.

## 4. Prove it (and keep going until it passes)

In the studio, start the site locally and run the checks. Both are long-running:
start each as a **background task your app keeps alive** (Claude Code: the Bash
tool's `run_in_background`; a `nohup ... &` inside an ordinary command can be killed
when that command returns, and a dev server that dies mid-check fails every later
row). The full check takes 3–6 minutes; poll its log with short commands.

```sh
npm run dev > .dev.log 2>&1                                                  # background task: http://127.0.0.1:8787
npx --no-install homie-studio port check <id> --url http://127.0.0.1:8787 > .port-check.log 2>&1   # background task
tail -5 .port-check.log                            # poll until it prints PASS or NOT YET
```

The check says so when the site stops answering; restart the dev server as a
background task and rerun.

`--only owner-desk,owner-phone,...` reruns single rows while you fix. Each row, what
it measures and how to fix a failure: [references/CHECKS.md](references/CHECKS.md).

- **owner-desk / owner-phone / owner-iphone**: hold a direction 5 s → one straight
  line the pressed way, camera yaw change under 10°; alternate directions for 10 s
  → every press goes the pressed way. Board games: every key and swipe is the move
  the game applies. Keys on a computer; real touch on Android Chrome and iPhone
  WebKit (first time: `npm i -D playwright-core@1.58.2 && npx playwright-core install webkit`).
- **ui-cover**: the UI covers at most 12% of a phone, nothing opaque in the middle.
- **round**: two fresh browsers (a computer and a phone) meet through Play and both
  see a round finish with both of them in the results.
- **host-kill / late-join**: the host's browser is killed mid-round; the other
  takes over the same round within 5 s; a late joiner is seated in a bot's place
  with the world and the right clock at once.
- **tv**, **audio**, **errors**: the big screen, sound after the first input, no
  uncaught errors.

Look at the screenshots in `games/<id>/.port/check-*/` yourself: is your own
body easy to find, does the world fill an upright phone, is the text readable,
does the big screen show the game? A passing check with an ugly, tiny or
confusing picture is not done. When you debug in a browser of your own, open one
at a time (the check already runs two). Fix, rebuild
(`npm run build`; the dev server serves the new files), check again. When you are
done, stop the dev server: stop it with `npx --no-install homie-studio dev --stop`, which stops exactly this studio's dev server (and its Wrangler) and nothing else. Never `pkill`, `killall` or `lsof ... | xargs kill` by name or port: other projects on this machine may run their own `wrangler dev`, and a pattern stops theirs too.

If something still fails after real effort, say exactly which row, what you saw,
and why — never hide it.

When the rows pass, the port works; whether it is good is the `playtest` skill's question: it adds a
phone held sideways, the look while playing, the UI in landscape, the game's real sound, a round with
one player trying and one idle, and a blind review by a fresh reviewer. A port that went silent or
never had sound: the `sound` skill makes and wires effects and a theme for free.

## 5. Put it online and list it

Follow the `publish` skill: `npm run deploy` (the person approves Cloudflare once
if Wrangler is not signed in), then run the full check against the live site:

```sh
npx --no-install homie-studio port check <id> --url <the live site> > .port-check-live.log 2>&1   # background task
```

Then list it with the Homie MCP tool `studio_publish` { site } (without the connector,
`npx --no-install homie-studio publish`). Commit the studio
(`git add -A && git commit -m "Port <Name> to multiplayer"` inside the studio).

## 6. Tell the person

Five to eight lines: the grade and why; what multiplayer means in their game now
(rounds, bots, what the host decides); the check table (each row pass/fail, with
the numbers that matter); the Play link, the big-screen link and the directory
listing; and anything still weak, plainly. If something in Homie itself got in the
way, say it can be reported at https://github.com/homie-rocks/homie/issues/new/choose.

## Never

- Never skip a check or weaken it to pass; never call a failing row "fine".
- Never publish a game whose licence does not allow it.
- Never put a key, token or password in the studio or in chat.
- Never touch a Cloudflare resource the studio did not create.
- Never ask the person to run a command.
