---
name: game
description: Make a multiplayer web game inside a Homie studio — every browser renders the game, strangers meet in public rooms, bots fill empty seats, rounds end and restart — prove it with two browsers finishing a round, and give it an epic landing page (a full-bleed hero from its own footage or art, the pitch, Play, phone / computer / TV, live rooms, how to play, credits). Use when someone in a Homie studio (a folder with studio.json) asks for a new game, a change to a game, a game whose own AI decides (opponents picking tactics, an NPC's reaction, a director's call, a turn's move), or a better page for a game ("make my game's landing page epic").
compatibility: Node 22 and Chrome. The studio's pinned Wrangler runs the dev site; the GitHub CLI (gh) opens a pull request when the studio publishes that way; Ollama with clef-flash, optional, answers a game's AI decisions on this computer under dev (downloaded only after the person's yes).
metadata:
  providers: cloudflare github ollama
---

# Make a game

You are in a Homie studio when the folder (or one above it) has `studio.json`. If there
is none, use the `studio-setup` skill first.

## Start it

- **Look for pieces before writing them.** Games build on each other by sharing parts: a creature from one game,
  a level from another, a bot brain from a third. For each system the game needs (camera, movement, bots, pickups,
  effects, sound, UI, environment), before writing it from scratch:
  - check the `@homie-rocks/*` packages (npm) for the general mechanism: camera, input, audio, effects;
  - run `parts_find` for pieces other studios shared, and bring one in with `part_add`.

  Record both in the game's CODEX (Built from) and its credits: what came from where, and what you wrote here and
  why. After building a piece another game could use, offer to make it a part (`part_new`) and, only if the person
  asks, to share it (`part_share`). The `parts` skill has the method.
- **A new studio's first game** follows the `studio-setup` checklist: a live game to try first
  (`npx --no-install homie-studio demo`; a starter is copied into the studio only when the person asks),
  one small change, then the plan (the `plan` skill) before anything big. Never jump ahead of it.
- **A game with a Game Codex** (`games/<id>/CODEX.md`): read it first; it is the plan. Every decision that
  changes it goes into it in the same change, with a dated line under Latest, and the page is redrawn
  (`npx --no-install homie-studio codex <id>`). A big change to a game without one: plan it first.
- **Other studios** beside this one (a neighbouring folder with its own `studio.json`) are other people's
  work: never read their games or copy from them, not even as a model for this one, unless the person asks.
  What you may read is this studio and the toolkit in its `node_modules/@homie-rocks/studio/`.
- **New game:** call the Homie MCP tool `game_make` (id, name) for the exact command
  and rules (without the connector, go on: the command is here and the rules are this skill's), then run
  `npx --no-install homie-studio game new <id> --from gem-rush --name "<Name>"`
  (`--from gem-rush-3d` for a 3D game: three.js with free library models; `--from hero-rush-3d` for a 3D game with
  animated characters that run, jump and swing). The id becomes the game's
  address (`/<id>/`); lowercase, digits, hyphens.
- **Make an existing single-player web game multiplayer:** use the `port` skill (it
  grades the port, brings the game in, and proves it with the owner tests).
- **Build on another studio's game:** through parts, never the whole game (remix was
  retired; `game remix` answers with a sentence that says so). `parts_find` searches the pieces
  other studios shared (a creature, a level, a bot brain) and `part_add` brings one in with its
  licence and credit: the `parts` skill has the method. When someone asks to copy or remix a
  whole game, say that plainly and offer to make a game of their own like it, with parts where
  some fit.
- **A game's own licence** is game.json `"license"`: an SPDX identifier (`"MIT"`), said on its
  page; a game that names none says nothing. A game.json with `"remixOf"` was made from another
  studio's game: keep the key, whatever else changes (its landing says "Based on <game> by
  <studio>").
- Some names are protected (the homie.rocks house games): `game_make` and
  `studio_publish` refuse them. Pick your own name, or ask the name's owner
  with `studio_request_grant` (only the owner can approve, in their browser).

## Change it

The game is `games/<id>/`: `game.json` (name, blurb, players, round length),
`index.html`, `src/main.ts`. The starter (Gem Rush) is a complete netplay game in one
readable file: rules, bots, snapshots, rendering on a canvas, keys and touch.

Make it the game the person asked for, one milestone at a time. Within a milestone, work in few, large
edits: read a file once, decide every change it needs, and make them together (one edit that carries several
replacements, or one write of a new or short file), never a tool call per change. Twenty single edits to one
file use up a turn before the game is built and checked, and the person has to say "keep going". As you go:

- Keep `createNetplay` from `@homie-rocks/studio/netplay` and its shape (host runs the rules
  and bots; replicas move their own body and render snapshots; checkpoint everything a
  promoted host needs). The contract is `node_modules/@homie-rocks/studio/netplay/NETPLAY.md`.
- Keep rounds: they start the moment the first visitor arrives (bots in empty seats),
  arrivals take a bot's place mid-round, the host calls the round over with results,
  and a new round starts by itself. Keep the round length in `game.json`
  (`roundSeconds`) and the code in agreement.
- Phones get touch (the drag from the lower left), computers get keys; keep the centre
  of the screen clear during play; names people type are drawn as text only.
- **Watch any player.** Anyone can watch a live room at `/<id>/watch?room=<room>` and switch
  between the players' views (a strip of names, keys 1-9, Auto). Draw the camera and HUD
  from `net.viewSeat` (your own seat when playing; the followed player when watching; `null`:
  the overview), call `net.spotlight(seat)` on a hit, a kill or a goal so Auto cuts to it,
  and expose `scores` (`[{ seat, score }]`) for the strip and the leader. Gem Rush does all
  three. A game that never reads `viewSeat` is watched as its overview. Hidden hands or
  roles: `game.json` `"watch": "overview"` (the whole room only), or `false` (no watch
  door). NETPLAY.md section 16.

  ```ts
  const view = net.offline ? 0 : net.viewSeat;           // whose camera and HUD this browser draws
  const body = view === null ? null : bodyOfSeat(view);   // the followed body, sampled like every other
  camera.follow(body ?? arenaCentre);                     // null: the overview camera
  hud.mark(view);                                         // their row, their score; "You" only when it is you
  ```
- **Make your bots honour the skill dial** (servers, NETPLAY.md section 17). A studio's servers
  can keep AI seats in every room (hybrid), and the party votes how strong the AI plays: 1
  Rookie to 5 Maxed, each `{ reactionMs, aimNoise, aggression, positioning }`. Read it per
  bot with `net.skillOf(slot)` (Fair when nobody voted) and declare what the game does:
  `createNetplay({ …, caps: ['skill', 'agents'] })`, with a `Roster({ …, policy: () =>
  net.policy })` whose join passes `p.agent` (a game on `createRoom` has all of it). Gem
  Rush's `stepBots` is the worked example:

  ```ts
  const s = net.skillOf(b.slot);                      // the room's dial for this bot
  if (now - eye.at >= s.reactionMs) eye = aimAt(pick(b, s), 200 * s.aimNoise);   // reaction, aim (a miss costs it again)
  if (rivalNear && Math.random() < s.aggression * 0.8 * dt) bump(b);              // aggression
  // positioning: weight the hot spot's targets by (1.5 - s.positioning): 0 leaves it to people, 1 fights for it
  ```
  Never let a bot's name pass for a person's: an AI's name already ends in " · AI".
- **Write the guide vocabulary** (AI guides that talk, NETPLAY.md section 18), when the game has a beginner
  server or the person wants guides: `games/<id>/agents.json` is the only words a guide has. Write it WITH the
  person, in the game's own voice: a `persona` (two short sentences), 3 `names`, 4 to 6 `goals` the bot code can
  actually carry out (`follow` a `"player"`, a `quest` from `"view.quests"`, `lead` to a list of places, `guard`,
  `back`), 6 to 10 short `lines` (120 characters, kind, never sarcastic, never about a person), and 2 or 3 `asks`
  a player taps (one with `"leave": true`: "No thanks"), each with the `goal` and `say` that answer it. A goal is
  something done WITH players, never to one (the build refuses one that reads as acting against a player). Then
  `useAgents(room.net, vocab, { view, decide })` from `@homie-rocks/studio/agents`: `view(slot)` is game state
  only (seats, never names; under 2 KB), `decide(view)` is the scripted floor, the hands read
  `agents.goalOf(slot)` and call `agents.done(slot)`, and lines are bubbles from `agents.on('say')`. Ember Vale
  (`--from ember-vale`) is the worked example. The brain itself is the owner's switch (the `servers` skill);
  `homie-studio agents try <id> --view view.json --ask <ask>` shows what it would decide in one moment.
- **Let the game decide with AI** (NETPLAY.md section 20), when its opponents pick a tactic, an NPC reacts from a
  fixed set, a director calls a wave or the pressure, or a turn needs a move: `"decide": true` in game.json (opt-in;
  the deploy binds Workers AI), then on the host `net.decide(state, questions, { floor })` (from
  `@homie-rocks/studio/netplay`, or `room.net` with the port kit). Cloudflare's Clef answers in the room with option
  ids, yes or no, and levels, never text: Choice (2 to 26 ids), yes/no (`noul`), Score (2 to 10 levels). It always
  resolves: the game's synchronous `floor` answers whenever the model cannot (no AI, not opted in, over the day's
  budget, paced, slow, not the host), so the floor must play well by itself.

  ```ts
  const d = await net.decide({ heroes: heroes.map((h) => ({ hp: h.hp, down: h.down })) }, {   // game state and seats, never names; < 2 KB
    tactic: { type: 'choice', instructions: 'How should the slimes hunt?', criteria: { chase: 'Rush the nearest hero', regroup: 'Gather round the King' } },
    wave: { type: 'noul', instructions: 'Should a wave come now?' },
  }, { floor: () => ({ tactic: 'chase', wave: false }) });
  apply(d.picks);                                          // d.by: 'ai' | 'local' (Clef on this computer, dev) | 'floor'
  ```
  Ask per beat (every 5 to 10 s), per turn or on an event, never per frame: about a quarter of a second a round
  trip and about 4 neurons for three questions, from the AI brains' day the guides share (8,000 by default; one room
  asking every second would spend about 15,000 an hour). The room allows one ask every 3 s and 20 a minute. On a
  kids server (`net.policy.kids`) keep it gentle: offer no cruel option and cap the pressure. A decision moves the
  game's own world, never a person and never the party's skill dial. Ember Vale's slimes' director is the worked
  example (it ships `"decide": false`). Under `npm run dev` it answers with Clef on this computer when Ollama has
  `clef-flash`, else from the floor; downloading `clef-flash` (about 11 GB) is the person's yes, never yours.
- **Room chat and speech bubbles** (NETPLAY.md section 19; `chat/CHAT.md`). Every game has room chat on its
  play page with no code: reactions that float up every screen, quick lines, and typing where the rules allow.
  Give it the game's own voice in `game.json` `"chat"`: `"lines"` (up to 12 quick lines, short and kind:
  `{ "gg": "Good game!", "gem": "Grab that gem!" }`), up to 3 extra `"emoji"` (`{ "gem": "💎" }`), and the
  defaults that suit its players (`"mode": "lines"` for a game for children; the owner can change any of it).
  Draw what players say over their characters with the port kit, after the name labels:

  ```ts
  const bubbles = createBubbles({ measure: (t) => { ctx.font = BUBBLE_FONT; return ctx.measureText(t).width; } });
  net.on('say', (s) => bubbles.say(s.seat, s.text, { id: s.id, kind: s.kind }));
  net.on('unchat', (e) => e.ids.forEach((id) => bubbles.remove(id)));
  paintBubbles(ctx, bubbles.place(speakers.map((p) => ({ key: p.seat, x: p.labelX, y: p.labelTop, self: p.mine }))));
  ```
  A game's own chat keys (a quick-line wheel): `net.sayLine('gg')`, `net.react('fire')`. Never draw a name or a
  message as markup. **Where chat sits:** the Chat pill rides the room button's band (`screen.share` below; a
  round icon on a phone), and the strip of new lines shows for a moment at the bottom left. If the game's HUD or
  controls are there, put the strip where it has room in `game.json` `"screen": { "chat": { "at": "top-right",
  "y": 110 } }` (a corner, `top-center` or `bottom-center`; `x` / `y` in pixels; per device: `desk`, `phone`,
  `sideways`, `tv`), or keep new lines in the Chat sheet with `"lines": "sheet-only"` (the pill counts them).
  Never turn typing off to make room: place the strip instead (`chat/CHAT.md` has every field).
- Update `game.json` `name` and `blurb`, and the `<title>`.

## Progress that lasts: cloud saves

When the plan says progress persists across sessions or devices (the codex's "Progress that lasts", or the person
asks for a character, levels, unlocks, a collection, hardcore), wire in saves. Never keep it in the room: a room
forgets everything 60 s after its last player leaves.

- `game.json`: `"saves": true`. A new game of that kind can start from the starter:
  `npx --no-install homie-studio game new <id> --from ember-vale --name "<Name>"` (a hero that lasts, lifetime
  stats, a hardcore mode with a hall of the fallen, on the same rooms as any game).
- In the game: `import { createSaves } from '@homie-rocks/studio/saves'`; `const saves = createSaves({ game: '<id>' })`.
  Load on arrival (`await saves.get('hero')`), save when it changes (`saves.set('hero', hero)`, at most about once a
  second), and reload on `saves.on('player', ...)` (the player signed in on this device). Keep one character in ONE
  key. Lifetime numbers: `saves.stats.add({ kills: 1 })`. Hardcore: `saves.fall({ character, summary, wipe: true })`.
- The host decides what happened and tells the player's own browser (a netplay event to its seat); only that
  browser changes and saves the player's progress.
- A character's name is the save's, not the room's: the room knows a person by their account's name or a two-word
  handle. Draw the character's name over its body and in the ranking (the browser tells the host, the host keeps
  every seat's in keyed state), except on a kids server, where the others stay handles. Ember Vale does it.
- Show who is playing (`saves.player.name`, guest or signed in) and a small "Keep my progress" button that calls
  `saves.signIn()`; the play page shows its passkey sheet. Pressing Play never needs an account.
- Prove it: build, `npm run dev`, open `http://localhost:8787/<id>/play` (passkeys need `localhost`, not
  `127.0.0.1`), play, reload: the progress is still there. The whole guide is
  `node_modules/@homie-rocks/studio/saves/SAVES.md` (the limits, offline and conflicts, what is stored, privacy).

## Prove it

Open a progress feed for every build, titled with what it does (the codex's milestone); the codex
page's Build status tab and Claude Code's status line follow it by themselves (in Codex and Grok Build
the codex page is the view: `npx --no-install homie-studio codex <id> --open`). When the person is
following along in the Claude app (or anywhere they cannot see your terminal), share it and show it:

```sh
npx --no-install homie-studio progress start <id> --share --title "<what this build does>" [--budget <dollars>]
npx --no-install homie-studio progress stage plan done --note "<the plan in one line>"
```

It prints a build id: call the Homie MCP tool `build_progress` with it once, and where the app
draws cards (the Claude app) the card follows the build by itself (stages, each check going green, a
preview, spend, Stop). The commands below report into it. If a command answers `stopped`, the person pressed Stop:
end there and ask before starting again.

**Started from the Claude app** (a Claude Code session whose prompt came from a "Build it"
card, naming a build `hb_...` and maybe a setup `hs_...`): the chat already opened the build, so
take it instead of starting one, then work on a branch and publish as a pull request. The
prompt names the studio's repository: first check this session is in it
(`git remote get-url origin`). If it is in another one (`homie-rocks/homie` is Homie's
engine and template, never a studio), stop and say so; never attach from it.

```sh
npm install                                            # the studio's pinned toolkit, from registry.npmjs.org
npx --no-install homie-studio setup attach hs_...        # only when the prompt names a setup: once, first
npx --no-install homie-studio progress attach hb_...     # this session takes the chat's build (once)
npx --no-install homie-studio chrome install           # Linux without Chrome: Chrome for Testing, once
# ... make the game, build, dev, check (below) ...
npx --no-install homie-studio progress change "<what the change does, one line>"
git switch -c <short-branch> && git add -A && git commit -m "<what it does>" && git push -u origin HEAD
gh pr create --fill
npx --no-install homie-studio progress pr --url <the pull request's address>
```

The card's Publish button opens the pull request for the person; their merge in GitHub is
the approval. Workers Builds deploys the branch as a Preview (run `check --url <the Preview
URL>` when the pull request shows it, and pass it as `progress pr --preview`) and `main`
after the merge; the card says Live by itself. Never merge the pull request yourself. If an
attach fails, quote the toolkit's message as it is: it names the directory's status and its
own words, or the connection error and whether this machine's proxy was used. Never guess at
the cause. Only when it says the network proxy refused homie.rocks, pass on the setting it
names; then go on, since the build works with its local feed. On Linux without a GPU,
`check` measures seats, rooms and rounds; its frame rate is SwiftShader's, not a person's:
say so rather than calling the game slow.

```sh
npm run build                                          # fix every error it names (a game that does not build fails it)
npx --no-install homie-studio build --types            # the same, with the TypeScript checked first: run it before a deploy
npm run dev                                            # in the background: http://127.0.0.1:8787/<id>/play
npx --no-install homie-studio check <id> --url http://127.0.0.1:8787 --shots ./.checks
npx --no-install homie-studio shoot <id> --preview     # pictures of the built game on a stepped clock, no site needed (a 3D game where there is no GPU)
npx --no-install homie-studio preview <id>             # only that game's built files at an address (alone, offline): for a capture script
```

`npx --no-install homie-studio dev --timestamps` puts a time on every line the site prints (room
sockets and errors always have one): use it to lay a connection loss beside a check's report.
`shoot <id> --url http://127.0.0.1:8787` adds a two-client seat smoke check in a private room.
Where there is no terminal, the same commands go through the `studio_run` tool, by their words.

`check` passes only when two fresh browsers (a computer and a phone) press Play, land
in the same room, and both see a round finish with both of them in the results. Look
at the screenshots it saves. Never say a game works without a passing `check`.
Start `npm run dev` as a background task your app keeps alive (Claude Code: the Bash
tool's `run_in_background`), and when you are done with it: stop it with `npx --no-install homie-studio dev --stop`, which stops exactly this studio's dev server (and its Wrangler) and nothing else. Never `pkill`, `killall` or `lsof ... | xargs kill` by name or port: other projects on this machine may run their own `wrangler dev`, and a pattern stops theirs too.

Then make it good, not just working:

- **Sound**: the `sound` skill makes the game's effects and a synthesized theme for free and wires
  them in (`sound.play('coin')` where it happens, in every browser). A silent game is not finished.
- **Look**: first the decisions (the `style` skill: render style, palette, light, camera, fonts, budgets; automatic
  from the person's words, drawn in the codex), then the models (the `models` skill: the engine and the free CC0
  starter library first, the person's own files with their licence, generated props and characters only on their own
  fal account under a budget), the characters' rigs and clips (the `animate` skill), then the `art` skill's cover from a real frame and, with a budget, painted backdrops and
  textures. "Make the look better" goes through `style` and `models` before any painting.
- **Match the brief's tone**: a cozy, calm or gentle brief is not a fight. Score together (in `gem-rush-3d`,
  game.json `"scoring": "together"`: one total the room fills, no places), make contact gentle or none, and give the
  bots friendly names; keep rivals, rankings and knocks for briefs that ask for competition.
- **A place, not a board**: a 3D game's play area reads as somewhere. Give it a heart the theme names (a den, a
  campfire, a well, a market stall) built in the game's style, a few solid features players move round, and
  something to do within a few steps of any spot, so a phone's close view is never bare ground. Look at the computer
  and phone frames before you call it done.
- **Models in code**: a three.js game loads every model through `@homie-rocks/studio/assets` (`createModels()`,
  `instance(url)`, `placeholder(size)`): it refuses unsafe or oversized files and decodes the phone-sized format
  `assets add` writes. Its development warnings use a small prop's budget (1,500 triangles, 300 KB a model); a game
  whose models are bigger on purpose sets its own once in game.json, `"assets": { "budgets": { "triangles": 8000,
  "bytes": 1500000 } }`, instead of living with a warning per model. Code a round does not need at once
  (a later level, an editor) can load later: `await import('./level-2')` becomes a file of its own in the build. Read colours and fonts from the game's `style.json` instead of hard-coding them, so the
  locked palette reaches the world and the HUD. `games/<id>/assets/manifest.json` records every model's origin and
  licence; keep it true (`assets add` and `assets remove`, never a hand-copied .glb), and `assets check <id>`
  before a deploy. The `gem-rush-3d` starter (`game new <id> --from gem-rush-3d`) is Gem Rush in 3D with library
  models: start a 3D game from it. With characters that move (people, heroes, fighters, creatures), start from
  `hero-rush-3d` instead: animated CC0 heroes through `@homie-rocks/studio/animate` (idle, walk, run, jump, a swing,
  hits, a cheer), one shared clip library per skeleton, a jump and a swing tuned in the Game Lab. The `animate` skill
  has rigs, clips, retargeting and feel.
- **Playtest**: the `playtest` skill plays it on a computer and a phone held both ways, measures the
  first ten seconds, the look, the UI, the real sound and a round, runs the owner tests, and hands a
  blind review to a fresh reviewer. Fix what it ranks first; run it again.
- **Speed**: when it stutters, loads slowly or a phone struggles, the `perf` skill measures it (frame
  times, CPU per frame for the host and a replica, time to playable, downloads, memory, netplay) and
  keeps a change only when it is faster beyond the noise and two browsers still finish a round.
- **Feel**: when a move feels floaty, stiff, weak or unclear ("the jump", "the hit", "the drift"), the `lab` skill
  builds a Game Lab for it: one take in the new build beside the last commit, frame by frame, with named phases,
  graphs and sliders that write kept values into the game's `tunables.json`.

Then give it its landing (below), `npm run deploy` and `studio_publish` (see `publish`), and
check again on the live site.

## Its landing page: `/<id>/`

Every game gets a landing page from the studio template, made from the game's own files
(`node_modules/@homie-rocks/studio/site/SITE.md` has every field): a full-bleed hero, the pitch, a big
Play button that drops a visitor into a public room, how to play on a phone, a computer and a TV (with
the join code), the live rooms, how to play and credits. It is as good as what you give it. "Make the landing
page epic" means all of this, in this order:

1. **Footage in the hero.** The biggest single difference. Capture the game running with the `video`
   skill (`capture <slug> --game <id> --url http://127.0.0.1:8787 --seconds 30`), pick 8 to 12 s where a
   lot happens, and cut two silent loops into `games/<id>/hero/`: `wide.mp4` (16:9) and `tall.mp4`
   (9:16, the phone's). Under 3 MB each, so a phone starts it at once:

   ```sh
   C=videos/<slug>/work/capture/capture.mp4
   ffmpeg -y -ss <start> -t 10 -i $C -an -vf "scale=1600:-2,fps=30" -c:v libx264 -crf 27 -preset slow -pix_fmt yuv420p -movflags +faststart games/<id>/hero/wide.mp4
   ffmpeg -y -ss <start> -t 10 -i $C -an -vf "crop=ih*9/16:ih,scale=720:-2,fps=30" -c:v libx264 -crf 27 -preset slow -pix_fmt yuv420p -movflags +faststart games/<id>/hero/tall.mp4
   ffmpeg -y -ss <start+2> -i $C -frames:v 1 -q:v 3 games/<id>/hero/wide.jpg
   ```

   Look at them (`ffprobe`, and a frame or two): the game, not a menu, a QR code or a black frame. A
   finished trailer in `videos/` with `"for": { "game": "<id>" }` is used when there is no `hero/`.
   No footage at all: the cover (the `art` skill's `cover`, from a real frame) moves slowly instead.
2. **The words**, in game.json's `landing` block: `pitch` (one line a stranger gets at once), `about`
   (a short paragraph), `howToPlay` (three to five short lines), `controls` for `phone`, `computer`
   (and `tv` if it differs), `players` (what a player is called: `{ "one": "pilot", "many": "pilots" }`),
   `hero.alt` (what the footage shows, for a screen reader), `hero.focus` (`"50% 35%"` keeps the action
   in frame on a phone), `hero.tint` (0 to 80: more when the art is bright and the title hard to read).
   A game with a `style.json` gets its landing in that palette by itself (its paper, ink and accents,
   light or dark as its paper is), so a bright game is not shown on the studio's dark page; leave
   `scheme` and `theme` out unless the person wants something else. A game without one whose picture is
   white or cream (a light arena) takes `"scheme": "light"`: its landing is drawn light, where the studio's
   dark tint would turn the picture grey. `hero/wide.jpg` is also the game's picture on every card and in
   the directory, and the play page's arrival card while the game loads, so pick a frame that reads small.
   game.json `"genre"` (a word, or up to three: `["Racing", "Party"]`) and pictures of real play in
   `games/<id>/screenshots/` (at most eight) go on the landing and into its structured data for search
   engines; say what the game is, never invent a rating or a review.
3. **Credits**: `landing.credits` names who made what (`[{ "role": "Music", "name": "..." }]`). A port
   keeps its `credits.json` (the original, its author and licence, every part inside); a game that has
   game.json `remixOf` keeps it; never drop either.
4. **The look**: the studio's `site/theme.json` colours; `landing.theme` gives this game its own
   `accent` and `glow` on its page, when two games of one studio should not look alike.
5. **A band of its own**, when the game has something to say that the template does not (a soundtrack, a
   mode, a season): `site/partials/game-<id>.html`, a short section in the page's own classes
   (`<p class="kicker">`, `<h2>`, `<p class="lead">`, `<a class="ghost">`).

**The play page's first seconds**: from the first paint it shows the game's arrival card (its title, pitch,
hero still, a progress line and `landing.controls` for the device) until the game says it is playable, never a
blank screen (`SITE.md`, "The play page"). Its words and picture are the landing's, so give the landing its
`pitch`, `controls` and a hero still. A game that keeps loading after the room's first state (models,
textures, a baked world) passes `arrival: 'game'` to `createNetplay`, calls `net.loading(p, 'the heroes')`
while it loads and `net.playable()` once its world and the player's own body are drawn, so nobody sees
stand-ins (NETPLAY.md section 21); the starters do. `perf` measures it: `load.look` (the first meaningful
frame), `load.playable` (control-ready: seated, a body, the card gone) and `load.ready` (the game's own
`net.playable()`), with the arrival mode beside them. `check` says seated, ready (the card lifted) and connected
apart: a seat is not ready, and a finished round is not an uninterrupted one.

**The play page's room button** (Invite, Big screen, the room code) sits top right, with the Chat pill
beside it. If the game draws a score, a timer or a bar there, move them in game.json: `"screen": { "share":
{ "desk": "bottom-left", "phone": { "at": "top-left", "y": 56 } } }` (a corner or `top-center`, per device:
`desk`, `phone`, `sideways`; `x` / `y` move it in, in pixels; `"label": false` keeps both small icons). Room
chat's strip of new lines moves with `"screen": { "chat": … }` (above). Look at `/<id>/play` on a computer and
a phone, both ways up, while a round is on and somebody says something in chat.

Then `npm run build`, `npm run dev`, and look at `http://127.0.0.1:8787/<id>/` as a stranger would:
a computer (1440 wide) and a phone (390 wide, and turned sideways), from the top, scrolling to the end.
The `playtest` skill takes the screenshots. The hero reads at a glance, Play is above the fold on a phone,
nothing is cut off or runs off the side. Fix what you see; build again.

A whole landing of the studio's own (`site/pages/<id>/index.html`) replaces the generated one: only when
the person asks for a hand-made page, and start from the generated one's HTML so Play, the TV road and
"Made with Homie" stay.
