# The port recipe

How a single-player web game becomes a netplay game in a studio. The contract
behind all of it is `node_modules/@homie-rocks/studio/netplay/NETPLAY.md`; the toolkit
is `@homie-rocks/studio/port` (bundled games) or `window.HomiePort` (static games,
from `homie-port.js`). Read [LESSONS.md](LESSONS.md) too: every rule here has a
bug behind it.

## Contents

1. The shape (who owns what)
2. The toolkit in one screen
3. Worked example: a static canvas game (owner movement)
4. Bundled and three.js games
5. Patterns by kind of game: turn-based and puzzle · 2D action · platformer and physics · 3D and first person
6. Snapshots, keyed state, checkpoints
7. Bots
8. The big screen
9. The probe (what the checks read)

## 1. The shape

Every browser loads the whole game and renders it with its own camera. One
browser is the **host**: it runs the rules (pickups, scoring, the clock, hits,
enemies, bots, round end) and sends a compact snapshot 20 times a second through
the room's relay. Everyone else is a **replica**:

- **owner movement** (action games): the replica moves its own body at once with
  the game's own movement code and sends it to the host; the host bounds it
  (`room.bound`, a claim faster than the rules allow is reset) and draws everyone
  else from snapshots.
- **host movement** (turn-based, grid, rule-heavy): the replica sends intents
  (`room.input([...])`, `room.press('drop')`); the host's rules move the body; the
  replica predicts or simply shows the result.

The host can **take** a body for a knockback or a stun (`net.take(seat, ms)`) and
simulate it itself; the body comes back to its owner afterwards. If the host
leaves, another browser is promoted and restores the checkpoint.

## 2. The toolkit in one screen

```js
const P = window.HomiePort;                 // static game; bundled: import * as P from '@homie-rocks/studio/port'
const room = P.createRoom({
  game: 'my-game', maxPlayers: 8, minBodies: 4, movement: 'owner', roundSeconds: 90, breakSeconds: 6,
  spawn(slot, i) { return { slot: slot.slot, seat: slot.seat, name: slot.name, bot: slot.bot, score: 0, x, y }; },
  pack(b)  { return [P.q(b.x, 1), P.q(b.y, 1), P.q(b.angle, 2), b.flags]; },   // numbers only, after slot/seat/score
  unpack(f, b) { b.x = f[0]; b.y = f[1]; b.angle = f[2]; b.flags = f[3]; },
  angles: [2], discrete: [3],               // interpolate f[2] the short way round; never interpolate f[3]
  onRoundStart(n) { /* reset the world: enemies, pickups, level */ },
  fastWorld() { return /* projectiles, pickups: small arrays */; },
  saveWorld() { return /* everything else the rules need */; },
  loadWorld(world, fast) { /* a promoted host puts it back */ },
  onTakeover(b, info) { b.score = 0; /* a person took this bot's body: a join, a restored room, a new host (info.why); info.back: they held it before */ },
  admit(bots, who) { return bots.find((b) => b.alive); /* optional: WHICH bot a new arrival takes (default: the lowest) */ },
  ties: 'shared',                           // optional: equal scores share a place (default 'order': people before bots, then the lower slot)
  adopt(b) { /* the host placed MY body (round start, takeover): stand there */ },
  local() { return /* my body as I see it now (owner movement) */; },
});
room.hosting            // true while this browser runs the rules
room.bodies             // host: Map slot → body (people and bots)
room.mySeat()           // my seat, or null for the big screen
room.viewSeat()         // whose view to draw: my seat; for a watcher, the player it follows; null: the overview
room.viewBody()         // that player's body as everyone draws it (or null)
room.avatar(b)          // host: the owner's last input frame for body b (owner movement)
room.bound(b, claim, maxSpeed, dt)   // host: accept a plausible claimed position, reset a teleport
room.presses(b)         // host: button presses from that seat since last call ({ fire: 1 })
room.input(frame, held) // replica: my body / intents every frame
room.press('fire')      // replica: a press the host must not miss
room.update()           // host, every frame, AFTER the rules: the round clock + the snapshot
room.view()             // everyone: the bodies to draw (host: real; replica: interpolated)
room.fast()             // everyone: the fast world (host: yours; replica: the host's newest)
room.clock()            // { n, phase: 'live'|'over', secondsLeft }
room.send('boom', data) // host: a one-shot event to everyone (sounds, effects); room.on('event', e => …)

const input = P.createControls({ actions: { fire: ['Space'] }, touch: { buttons: [{ id: 'fire', label: 'FIRE' }] } });
input.move()            // x right, y DOWN, ≤ 1, from WASD/arrows or the stick — screen axes
input.pressed('fire')   // once per press, key or touch button
P.createTouchControls({ stick: { keys: { left: 'ArrowLeft', right: 'ArrowRight', up: 'ArrowUp', down: 'ArrowDown' } },
                        buttons: [{ id: 'jump', label: 'JUMP', key: 'Space' }] })   // an old keyboard game: touch presses its keys
P.createHud(room, { unit: 'coins', hint: { phone: 'Drag to move', desk: 'Arrows to move' } })   // clock, scores, results
P.exposePort(room.net, { view: 'top', size: R, self: () => ({ x: me.x, y: me.y }) })          // required: the checks read it
P.groundBasis(camera), P.screenToGround(input.move(), basis), new P.PlayerYaw()                // 3D camera rules
new P.BotBrain({ reactionMs: 250 }), P.nearest(from, items), P.seek(from, to)                   // bots
```

## 3. Worked example: a static canvas game

The original: a canvas, arrow keys move a dot, coins score, 60 s, a title screen,
"game over", a best score in `localStorage`. After `port import` the page loads
`homie-port.js` first. The port rewrites the game script like this (whole file):

```js
(function () {
  var P = window.HomiePort;
  var canvas = document.getElementById('game');
  var ctx = canvas.getContext('2d');
  var W = 800, H = 600, R = 14, SPEED = 240, COIN_R = 10, COINS = 10;
  var coins = [];
  var brains = {};
  var me = { x: W / 2, y: H / 2, has: false };          // MY dot: moved here, never waits for the host
  function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }
  function spawnCoin() { return { x: 40 + Math.random() * (W - 80), y: 40 + Math.random() * (H - 80) }; }

  var room = P.createRoom({
    game: 'coin-dash', maxPlayers: 8, minBodies: 4, movement: 'owner', roundSeconds: 60, breakSeconds: 6,
    spawn: function (slot, i) { var a = (i / 8) * Math.PI * 2; return { slot: slot.slot, seat: slot.seat, name: slot.name, bot: slot.bot, score: 0, x: W / 2 + Math.cos(a) * 220, y: H / 2 + Math.sin(a) * 160 }; },
    pack: function (b) { return [P.q(b.x, 1), P.q(b.y, 1)]; },
    unpack: function (f, b) { b.x = f[0]; b.y = f[1]; },
    onRoundStart: function () { coins = []; for (var i = 0; i < COINS; i++) coins.push(spawnCoin()); brains = {}; },
    fastWorld: function () { return coins.map(function (c) { return [P.q(c.x, 0), P.q(c.y, 0)]; }); },
    saveWorld: function () { return { coins: coins }; },
    loadWorld: function (w, fast) { coins = fast ? fast.map(function (c) { return { x: c[0], y: c[1] }; }) : (w ? w.coins : []); },
    adopt: function (b) { me.x = b.x; me.y = b.y; me.has = true; },
    local: function () { return me.has ? { x: me.x, y: me.y } : null; },
  });
  var input = P.createControls();
  P.createHud(room, { unit: 'coins', hint: { phone: 'Drag low-left to move', desk: 'Arrows or WASD to move' } });
  P.exposePort(room.net, { view: 'top', size: R, self: function () { return me.has && room.mySeat() !== null ? { x: me.x, y: me.y } : null; } });

  function stepBot(b, dt, now) {
    var brain = brains[b.slot] || (brains[b.slot] = new P.BotBrain({ reactionMs: 220, commitMs: 1800 }));
    var v = brain.think(now, b, function () { return P.nearest(b, coins); });
    b.x = clamp(b.x + v.x * SPEED * 0.8 * dt, R, W - R);             // the same speed rule a person has (a bit slower)
    b.y = clamp(b.y + v.y * SPEED * 0.8 * dt, R, H - R);
  }

  var last = performance.now();
  function frame(t) {
    var dt = Math.min(0.05, (t - last) / 1000); last = t;
    var seat = room.mySeat();
    var live = room.round && room.round.phase === 'live';
    if (seat !== null && me.has) {                                      // 1. my own body, at once
      var m = input.move();
      me.x = clamp(me.x + m.x * SPEED * dt, R, W - R);
      me.y = clamp(me.y + m.y * SPEED * dt, R, H - R);
    }
    if (room.hosting) {                                                 // 2. the host runs the rules
      room.bodies.forEach(function (b) {
        if (b.bot) stepBot(b, dt, t);
        else if (b.seat === seat) { b.x = me.x; b.y = me.y; }
        else { var a = room.avatar(b); if (a) room.bound(b, { x: +a[0], y: +a[1] }, SPEED, dt); }
        if (!live) return;
        for (var i = 0; i < coins.length; i++) {
          if (Math.hypot(coins[i].x - b.x, coins[i].y - b.y) < R + COIN_R) { b.score += 1; coins[i] = spawnCoin(); room.send('coin', { slot: b.slot }); }
        }
      });
      room.update();                                                    // round clock + snapshot
    } else if (seat !== null && me.has) {
      room.input([P.q(me.x, 1), P.q(me.y, 1)]);                         // 3. replicas send their body
    }
    draw();
    requestAnimationFrame(frame);
  }
  function draw() { /* coins from room.hosting ? coins : room.fast(); bodies from room.view(), mine at me.x/me.y */ }
  requestAnimationFrame(frame);
})();
```

What changed and why: the title screen and "game over" are gone (rounds instead);
the one `player` became `room.bodies` plus my local `me`; `Math.random()` for coins
runs on the host only; the host's loop runs bots and scoring; the canvas is scaled
to fit any screen (`width:100vw;height:100vh;object-fit:contain`); the probe is
exposed. It passes every check row.

## 4. Bundled and three.js games

- `game.json` `"build": { "mode": "bundle" }` with `"entry": "src/main.ts"` (or `.js`).
  The first line of the entry is `import '@homie-rocks/studio/port/early';` so the sandbox
  shims and the audio unlock are in place before three.js or the game runs.
- `three` from npm: `npm install three` in the studio (it resolves from the studio's
  `node_modules`). A game that vendors `three.module.js` and an import map can stay
  `static`: the relative paths work under `/<id>/__game/`.
- A Vite game can use `"mode": "command"` (its own build, `base: './'`), or move its
  entry to `bundle` (esbuild handles TS and ES modules; `import.meta.env` does not exist).
- Every URL in the game must be relative (`./models/x.glb`, never `/models/x.glb`).

## 5. Patterns by kind of game

### Turn-based and puzzle (2048, match-3, sokoban, cards, word games)

Pick the multiplayer shape that keeps the game's feel:

- **A race on the same puzzle** (most solo puzzles): everyone plays their own board
  from the same seed the host deals at the round start (keyed state `seed`); the
  round is a clock; the score is the game's own. Each browser owns its board
  (`movement: 'owner'`) and sends `[score, bestTile, moves]` as its body fields;
  the host bounds them (a score can only rise by what one move can give) and ranks.
  Bots play their own boards on the host with a simple policy and a human pace
  (one move every 0.6–1.2 s). Show the others as a live leaderboard and small
  mini-boards or progress bars; a surge by a rival is the tension.
- **One shared board** (chess, checkers, tic-tac-toe, board games with seats):
  `movement: 'host'`; the host holds the board and whose turn it is; a move is a
  press (`room.press('move:e2e4')` or `room.input([from, to])`); the host validates
  and applies; the board is keyed state (`net.state('board', …)`, sent on change);
  a turn clock keeps a round moving; bots take a seat's turn when it is theirs.
- Keep the game's own look: a DOM board stays DOM (name it with `world: '.board'` in the
  probe, so the UI check reads it as the world, not as UI).
- Board probe: `exposePort(net, { view: 'board', world: '.game-container', lastMove: () => lastDir, moves: () => moveCount })`
  where `lastDir` is the direction the game RECEIVED and acted on ('left'…), even if
  nothing slid, and `moveCount` increases on every such input. Swipes: the touch kit
  `swipe: { keys: { left: 'ArrowLeft', right: 'ArrowRight', up: 'ArrowUp', down: 'ArrowDown' } }`
  presses the game's own keys.

### 2D action and arcade (shooters, asteroids-likes, arena games, maze chases)

- `movement: 'owner'`; each ship/avatar is simulated by its owner with the game's
  own movement code; the host runs enemies, asteroids, pickups and every hit.
- **Rotate-and-thrust (tank) controls become screen-relative**: the held direction
  (keys or stick) is where the ship turns and goes on screen; the fire button fires
  where it faces. Classic rotate keys can stay as an option, never the default: the
  owner tests hold one direction and expect one straight line.
- Projectiles: fired by the host (a replica's `room.press('fire')` arrives with its
  body's position and angle in the next frame); they ride `fastWorld()` as
  `[x, y, vx, vy]` rows; replicas draw them extrapolated from the newest snapshot.
- Hits and deaths: the host decides; a dead player respawns after a second or two
  with brief invulnerability — never out of the round.
- Wrap-around worlds: interpolate the short way across the edge (unpack, then fix a
  jump bigger than half the world).
- Grid movement (maze games): keep the game's own grid step for the owner; the host
  checks the claimed cell is adjacent to the last one. Keep its buffered turns (a turn
  pressed into a wall waits for the next opening) and say so with `view: 'maze'` in
  the probe; the checks then accept a queued turn and still require every reversal
  to answer at once.

### Platformer and 2D physics

- `movement: 'owner'`: the owner runs the game's own physics for its own body
  (jumps and landings must feel exact, so they never wait for the network); the host
  bounds the claim (horizontal speed, and a fall no faster than gravity allows).
- The host owns everything else: enemies, moving platforms, collectibles, doors,
  and anything two players can touch. A stomp or a pickup is the host's decision
  from the bodies it has (or a claim it checks: "I landed on monster 3").
- A physics engine world (Matter, Planck, Cannon, Rapier) runs on the host only;
  replicas draw it from snapshots. The owner's own body is kinematic on the host.
- Probe: `view: 'side'`; the checks hold left and right (gravity owns y).
- Camera: a side-scroller follows its own player horizontally; never rotate it.

### 3D and first person (three.js)

- `movement: 'owner'`; the owner moves its own capsule/character with the game's own
  controller and collisions; the host bounds it and runs projectiles, enemies,
  pickups and hits (a shooter's claim is checked against the victim's recent
  positions).
- **Camera rules** (the owner's tests are about these):
  - input is read on the camera's screen axes: `P.screenToGround(input.move(), P.groundBasis(camera))`
    or `yaw.toGround(input.move())` with a `P.PlayerYaw`;
  - the yaw changes only for a look input (mouse, look-drag on the right half of a
    phone) or at a round start — never to follow the character's heading;
  - third person: a close chase camera (the character about 14% of a phone's
    height), obstacles between lens and character fade instead of the camera jumping;
  - first person: pointer lock on a computer is fine; on a phone use
    `createTouchControls({ look: { zone: [0.45, 0, 1, 1] }, buttons: [...] })` and
    apply `touch.look()` deltas to the yaw/pitch.
- Probe: `view: 'first-person'` (WASD strafes on the camera's axes) or `'top'` for a
  third-person/overhead game, with `self: () => ({ x: pos.x, y: pos.z })` and
  `basis: () => { const g = P.groundBasis(camera); return { right: g.right, up: g.up }; }`.
- WebKit: `antialias: true` (MSAA) with post-processing drew a black world on
  iPhone; turn MSAA off on WebKit. Keep the pixel ratio at most 2 on phones.
- Other players are simple, readable meshes with a name tag; your own body is never
  drawn from snapshots.

## 6. Snapshots, keyed state, checkpoints

- **Snapshot** (20 Hz, under ~2 KB): one row per body (createRoom's `pack`), plus
  `fastWorld()`: projectiles, moving enemies, pickups. Quantise with `P.q(x, 1)`.
  Never send idle or static things.
- **Keyed state** (`room.net.state('level', …)`, sent only when it changes, handed to
  every joiner): the level, the seed, doors, a shared board, the leaderboard of a
  race. Up to 64 keys, 8 KB each.
- **Checkpoint** (1 Hz, under ~32 KB): everything the rules need that is in neither:
  `saveWorld()`. A promoted host gets checkpoint + newest snapshot + keyed state.
- One-shot moments (a hit, a coin, a sound): `room.send(kind, data)` from the host.

## 7. Bots

- The bot uses the same speed, the same rules, and the same actions as a person
  (never a shortcut), with a reaction delay and a little aim error (`P.BotBrain`).
- It commits to a target for seconds, gives up an unreachable one, and gets unstuck
  (BotBrain does both).
- It is beatable and kind: no bot hunts, hits or throws at a person in their first
  ~15 s (`P.protectedNewcomer`), and bots ease off when they lead the people
  (`P.rubberBand`). A stranger knocked about before they have found the controls
  leaves; so does one who never scores.
- A body a person leaves keeps playing as a bot where it stands.
- Tactics that change with the fight (rush, flank, regroup, a wave now) can come from the
  studio's AI: `room.net.decide(state, questions, { floor })` on the host every few
  seconds (NETPLAY.md section 20; game.json `"decide": true`). The hands stay
  BotBrain's, at the party's dial; the floor is the tactic the game always played.

## 8. The big screen

Its join card (QR and address) sits bottom-right; if that covers the game's own HUD,
move it with `game.json` `"screen": { "join": "top-left" }` (any corner). Room chat's
lines sit in a corner the card leaves free; `"screen": { "chat": { "tv": { "at": "top-right" } } }`
moves them (and `"phone"` / `"desk"` move the play page's strip of new lines: `chat/CHAT.md`).


`/<id>/tv` opens the room as a spectator (`room.mySeat()` is null) with a QR code
phones scan to join that room. When there is no seat:

- no body, no controls, no personal prompts ("press X", "you died", "your score");
- an overview camera that shows the whole arena, or a director that follows the most
  interesting person (a person before a bot) and cuts cleanly, never swinging;
- type big enough for a room: the clock and the board at least 2.2vmin.

**Watchers** (`/<id>/watch?room=`, NETPLAY.md section 16) are spectators who choose a
player to follow (a strip of names, keys 1-9, Auto). Make the camera follow
`room.viewBody()` exactly as that player's own browser frames them, mark their row in
the board (createHud does), and keep the overview for `null`:

```js
const view = room.viewBody();                       // the followed player (a watcher), my own seat (a player), or null
const target = view && view.seat === room.mySeat() && !room.net.watching ? me : view;
if (target) camera.follow(target.x, target.y); else camera.overview();
room.on('event', (e) => { if (e.k === 'hit') room.net.spotlight(e.d.by); });   // Auto cuts to the action
room.net.expose({ scores: () => room.view().map((b) => ({ seat: b.seat, score: b.score })) });   // the strip's scores, Auto's leader
```

A port that never reads `viewSeat` is still watchable: its watchers see the overview. A
game with hidden hands or roles says `game.json` `"watch": "overview"` or `false`.

## 9. The probe

Call once, after `createRoom`:

```js
P.exposePort(room.net, {
  view: 'top',                      // 'top' | 'side' | 'first-person' | 'board' | 'maze'
  size: R,                          // about a body's radius, in world units
  self: () => (me.has && room.mySeat() !== null ? { x: me.x, y: me.y } : null),   // 3D: { x: pos.x, y: pos.z }
  basis: undefined,                 // 3D: () => { const g = P.groundBasis(camera); return { right: g.right, up: g.up }; }
  keys: undefined,                  // the codes that move you, if not the arrows (first-person default: WASD)
  lastMove: undefined, moves: undefined,   // board games (section 5)
  world: undefined,                 // a game drawn in HTML: the selector of its board/world (not UI)
  busy: undefined,                  // () => true while a knockback, stun or respawn has my body (not judged)
});
```

The checks drive real keys and real touches and read `self`/`basis` every frame, so
they judge motion on the screen the person sees.
