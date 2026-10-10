---
name: game
description: Make or change a rules-plus-view multiplayer web game inside a Homie studio — the server runs the rules, each browser predicts its own movement and renders the game, strangers meet in public rooms, bots fill empty seats, rounds end and restart — prove it with two browsers finishing a round, and give it an epic landing page (a full-bleed hero from its own footage or art, the pitch, Play, phone / computer / TV, live rooms, how to play, credits). Use when someone in a Homie studio (a folder with studio.json) asks for a new game, a change to a game, a game whose own AI decides (opponents picking tactics, an NPC's reaction, a director's call, a turn's move), or a better page for a game ("make my game's landing page epic").
compatibility: Node 22 and Chrome. The studio's pinned Wrangler runs the dev site; the GitHub CLI (gh) opens a pull request when the studio publishes that way; Ollama with clef-flash, optional, answers a game's AI decisions on this computer under dev (downloaded only after the person's yes).
metadata:
  providers: cloudflare github ollama
---

Read the installed toolkit's `node_modules/@homie-rocks/studio/guides/game/{RULES,REWRITE}.md`
before authoring: these match its runtime even when this plugin is older. Toolkit
check/build report stale installed plugin copies and the update step. For solid slopes and terrain, use heightTiles with `base` and the source
`diagonal`; test sides, underside, step clearance and rays. Maps are indexed at
compile time up to 100,000 shapes; measure default-budget spawn and traversal. For live
cover, doors and platforms, use declared entity `collider` state and movement's
`ctx.world.sweep/support/overlaps`; test prediction, loss, rejoin and restore.


**Apps:** For a business, venue, cause or customer app, follow the `app` skill: `apps/<id>/app.json`, one morphing screen, roles and parts. Reuse these engines and workflows; do not impose game rounds, scores, bots, a game demo or page navigation. The app check proves shared actions and reconnect; app stores use the same standalone command.


# Make a game

You are in a Homie studio when the folder (or one above it) has `studio.json`. If there
is none, use the `studio-setup` skill first.

**Asked to rewrite an existing browser-hosted game for the server? Read
[REWRITE.md](REWRITE.md) in full before editing.** Preserve the renderer, feel,
other games and every existing test file, including its import paths. If an old
`rules.ts` exports tested helpers, keep those exports when adding defineRules;
do not redirect the tests to a new helper file. Run the original test command.

For a request involving a larger room or map, read RULES.md's **Spatial delivery**
section. `players.max` chooses the room size and Gate layout. Choose `room.view.radiusM`
for the playable neighbourhood, and visual precision and far update rates to fit
the game. Local measurements are in docs/rooms-milestone-2-notes.md; they are not
Cloudflare or physical-phone capacity guarantees.

## Start it

- **Look for pieces before writing them.** Games build on each other by sharing parts: a creature from one game,
  a level from another, a bot brain from a third. For each system the game needs (camera, movement, bots, pickups,
  effects, sound, UI, environment), before writing it from scratch:
  - check the `@homie-rocks/*` packages (npm) for the general mechanism: camera, input, audio, effects;
  - run `parts_find` for pieces other studios shared, and bring one in with `part_add`.

  Record both in the game's CODEX (Built from) and its credits: what came from where, and what you wrote here and
  why. After building a piece another game could use, offer to make it a part (`part_new`) and, only if the person
  asks, to share it (`part_share`). The `parts` skill has the method.
- **A new studio's first game:** follow `studio-setup`, choose sensible defaults from the request,
  write the plan and build it. The live demo is optional; never require a detour or an interview.
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

## Write and change rules plus view

**Read [RULES.md](RULES.md) before writing code.** All five starters use this contract.
Work in few, large edits: read each source file once, decide its changes, then
make every change it needs in ONE file_edit with an edits list. Build after each
coherent change across rules, movement and view; use diagnostics to guide the next edit.

New games use `game.json` `"entry": "src/view.ts"`, `"room": { "host": "server" }`,
and a studio-chosen `players.max`. HTML loads `<script type="module"
src="./assets/main.js"></script>`, not the source-file URL. Choose seats, tick rate (20 by default), dimensions and
starter yourself from the request; never ask the person an engineering question.
`coin-dash` is the smallest reference; `gem-rush` adds bumps; `ember-vale` adds
companions, decisions and character saves; the two 3D starters add models and jumps.
A starter is a starting point: implement the requested mechanic, not a renamed gem collector.
The build refuses a game with neither rules plus view nor a browser-hosted netplay contract;
a plain browser bundle is not a multiplayer game.

- **Truth: `src/rules.ts`.** Default-export `defineRules({ contract: 2, ... })`.
  Declare every lasting value in entity `fields`, movement `motion`, or room `shared`,
  and payloads in `shapes`. An entity handler changes only `self`; room handlers alone
  change shared state. Affect others with declared events, delivered on a later tick.
  Validate commands against current turn, cooldown, distance and ownership in rules.
  IDs are opaque `f.ref()` strings; compare them, never parse or sort them as numbers.
- **Movement: `src/move.ts`.** Export `move = defineMove(...)`, import it in rules.
  The server and local prediction run the same step. Read only body pose/motion,
  input, public tune, map plus declared live colliders and `ctx` clock/math. Sweep against the world, normalize
  diagonals, and declare the normal running `maxSpeed`. Put jumps, dashes and knocks
  here, with rule decisions encoded in `motion`. Do not add `body.move: 'owner'`:
  authoritative movement already predicts immediately and keeps the wall solid.
- **View: `src/view.ts`.** `import type rules from './rules'` and
  `openRoom<typeof rules>()`; send `room.input` and `room.command`, draw `room.me`,
  `room.each`, `room.shared`, `room.round` and `room.roster`. Handle a null own body.
  Camera, models, DOM, audio and particles stay here. The local pose is predicted;
  other poses are interpolated. A button or swing can animate on press, but damage,
  pickups and scores wait for the server. No second physics loop or local score authority.
- **Determinism and budget.** Use `world.tick`, `world.dt`, `world.ticks`, `world.after`,
  `world.random` and `world.math` (movement: `ctx`). No clocks, timers, async, network,
  `Math.random`, transcendental `Math` functions, `**`, changing module state or
  load-time computation in rules. Bounded local queries, bounded collections and
  declared fields keep work under the deterministic budget. Read all build messages
  and repair the named handler; never evade the guard or raise budgets to hide a bug.
- **Levels:** declare `map: './map'` and put bounds, solids and named spots in
  `map/main.json`. Draw from the same map. In 3D rules use metres, z up and feet
  positions; Three.js draws `(x,z,y)`. Height tiles are terrain; boxes are solid
  platforms. Decorative hills or meshes do not collide unless represented in the map.
- **Rounds and arrivals:** use automatic rounds or `rounds.seconds: 0` plus a room
  handler that calls `world.round.end()` for turn games. Never give a quiz or word
  game fake movement just to satisfy a test. Initialize late arrivals in `on.arrive`
  as well as existing bodies in `onRoom.roundStart`. `think` returns inputs, not commands;
  bot actions go through the same rules as a person's. Show the actual goal and result.
- **Companions:** `guide.view` returns declared `shapes.view`; `guide.floor` chooses
  a vocabulary goal without a model; `think` follows `self.goal` and calls
  `world.goalDone`. Write `agents.json` goals, lines and asks in the game's voice.
  Draw `room.askButtons(id)` and call `room.ask`. Server policies reserve companion
  seats; input never grants a role. Use `world.level`, `world.guideLevel`,
  `world.guideSeats` and `world.kids`. Preserve visible AI labels.
- **Game decisions:** declare `asks` with state, questions and a synchronous floor;
  call `world.ask` per beat or turn and handle `on.answer` once (`ai`, `local`, or
  `floor`). No promise/await or `net.decide` in rules. The floor must play well alone.
- **Hosting and saving:** server hosting is the default. Browser hosting is for
  offline play, local experiments or private friends games, using the same rules;
  it is not a fix for a failed build. Room state saves automatically and restores
  as a whole, but the room ends 60 seconds after its last person leaves. Character
  progress uses the separate saves API below. No secrets in entity/shared state:
  every replica receives it. A prop disguise is a visual mechanic, not secure hidden
  information. Private per-seat information and bigger rooms belong to milestone 2.
- **Changing a rules game:** read its codex, declarations, move and view; change the
  responsible half, preserve unrelated play, and rebuild. The build/state hashes
  manage compatibility automatically; do not hand-pack snapshots or bump netplay.version.
  Recheck the changed mechanic, a late join and a reload in two browsers.
- **Changing an old-style game:** existing netplay games keep working on 0.45.0
  with their original 32-seat limit. Preserve their behavior on ordinary edits.
  For a server migration or larger room, follow [REWRITE.md](REWRITE.md).
  New games use rules plus view; there is no automatic converter yet.
- Phones get touch, computers get keys; typed names and chat are text only.
  Keep native DOM buttons outside `guardGestures`' touch-drag selector; otherwise bind
  touch pointers explicitly. Verify actual touchscreen taps, not only `.click()`.
  Keep controls clear of the shell's pills (`room.net.shell`). Watchers use
  `room.net.viewSeat` for their camera and HUD, and `room.net.spotlight` for action.
  `watch: 'overview'` or `false` changes the offered UI, not secrecy of snapshots.

Make it the requested game, one milestone at a time. Read each file, make coherent
edits, build, act on the diagnostics and test the actual play before declaring it done.

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
- Rules emit declared effects; the view checks the effect's entity ID against `room.me?.id` before
  changing its own character save. These browser-written saves are player-owned progress, not a
  server-verified economy or authority for purchases. Room durability is separate and automatic.
- A character's name is the save's, not the room's: the room knows a person by their account's name or a two-word
  handle. Draw the character's name over its body and in the ranking (a declared command requests it; rules validate and keep it in the player entity), except on a kids server, where the others stay handles. Ember Vale does it.
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
Before giving a live preview link, fetch it and confirm its server will outlive the
task. A terminal session may end with a headless agent. If you stopped the server
or cannot keep it alive, say the game is built and give `npm run dev` and the local
path; do not describe a stopped preview as running.
In a headless authoring task, always include the start command and game path in
the handoff: a successful curl proves the link works now, not after the agent exits.

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
  first ten seconds, the look, the UI, the real sound and a round, and runs the owner tests.
  Read the pictures and save an honest local verdict; use a fresh outside reviewer when requested.
  Fix the most important finding and repeat the affected checks.
- **Speed**: when it stutters, loads slowly or a phone struggles, the `perf` skill measures it (frame
  times, CPU per frame on player browsers, time to playable, downloads, memory, netplay; server
  tick work is a separate measurement) and
  keeps a change only when it is faster beyond the noise and two browsers still finish a round.
- **Feel**: when a move feels floaty, stiff, weak or unclear ("the jump", "the hit", "the drift"), the `lab` skill
  builds a Game Lab for it: one take in the new build beside the last commit, frame by frame, with named phases,
  graphs and sliders that write kept values into the game's `tunables.json`.

Then give it its landing (below) and a working local result. Publish with `npm run
deploy` and `studio_publish` (see `publish`) when publishing is in the owner's
requested scope, then check again on the live site. A build-only request needs no
Cloudflare setup or release question. Honor a local-only or no-deploy instruction.

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
textures, a baked world) passes `arrival: 'game'` to `openRoom`, calls `net.loading(p, 'the heroes')`
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
