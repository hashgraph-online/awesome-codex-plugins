# Rules reference (contract 2)

A rules game has `src/rules.ts`, `src/move.ts`, `src/view.ts`, `game.json`,
`tunables.json`, `index.html` and `map/main.json`. The rules default-export `defineRules` from
`@homie-rocks/studio/rules`. The movement file exports `move = defineMove({...})`
from the same package. Import `move` into the rules. Pictures and controls belong in
view.ts; shared movement belongs in move.ts; all game decisions belong in rules.ts.

```ts
import { defineRules, f } from '@homie-rocks/studio/rules';
import { move } from './move';
export default defineRules({
  contract: 2, space: { dims: 2 }, move,
  shared: { total: f.u32() },
  shapes: { events: { point: {} }, commands: {}, effects: {} },
  entities: {
    runner: {
      player: { away: 'think', leave: 'bot' },
      fields: { score: f.u16({ score: true }) },
      input: { ax: f.i8(), ay: f.i8() },
      body: { shape: 'circle', radius: 0.5, maxSpeed: 6 },
      think() { return { ax: 0, ay: 0 }; },
      on: { point(world, self) { self.score += 1; } },
      onRoom: { roundStart(world, self) { self.score = 0; } },
    },
  },
  room: {
    rounds: { seconds: 60, breakSeconds: 3 }, bots: { keep: 4 },
    join(ctx, player) {
      const spots = ctx.map.spots('start');
      return { kind: 'runner', at: spots[player.seat % spots.length] };
    },
  },
});
```

The map must contain a nonempty `spots.start` list for that example:
`{"bounds":{"min":[-12,-7],"max":[12,7]},"boxes":[],"spots":{"start":[[-5,0],[5,0]]}}`.
Declare `players.max` in game.json (a positive integer, including hundreds); use `entry: "src/view.ts"` and
`room: { host: "server" }`. Only public tunables are visible in move.ts.

`index.html` is the browser entry document; include `<script type="module" src="./assets/main.js"></script>`. The manifest names the source, but HTML loads this relative built bundle. Never point HTML at /src/view.ts: that URL is not served. The build rewrites assets/main.js to its hashed bundle. A minimal manifest is:

```json
{"id":"keepers","name":"Keepers","entry":"src/view.ts","players":{"min":1,"max":4},"room":{"host":"server"}}
```

`id` is the folder identifier and `name` is the displayed name, `players.min` the advertised minimum and `players.max` the seat cap. `entry` names the browser source. Optional `blurb`, `tags` and `cover` describe the game on its page. `room` sets server hosting and optional `tickHz` (the default is 20). `room.bots: { keep: 4 }` in **rules.ts** asks the host to maintain four total occupied bodies when its policy allows bots; it is not four extra bots. Companion policies belong to the server's room/server configuration, not a player's frame or the game manifest. Set the server policy to `hybrid` with `aiSeats`, or `beginner` with `guides`; these reserve server-owned AI bodies, and `bots: 'off'` disables ordinary fill bots.

For example, `homie-studio servers new keepers "Practice" --policy beginner --guides 1` creates a beginner server with one guide. Use `homie-studio servers set keepers <server> --policy hybrid --ai 1` to change an existing server through its owner controls.

Server movement is the default and predicts immediately in the local browser using
its guarded `move`. Bots, AI and away people are always moved on the server.
`body.move: 'owner'` is an existing compatibility option that accepts bounded position
claims and cannot enforce walls against a modified browser; do not use it for new games.
A non-player entity may use `world.sweep(self, delta)` instead of a move function.
Bodies require radius and maxSpeed. In 2D use circle or box (radius is its half-width); in 3D use sphere, capsule or
axis-aligned box, with full height for capsule/box. `sweep: true` adds automatic map
collision; explicit `ctx.map.sweep` moves and returns a contact for sliding.

### Level data and three dimensions

Declare `map: './map'` in rules and put static geometry in `map/main.json`. Both
host and predictor compile the same data; the view reads it as `room.map`.
Coordinates in JSON are arrays; runtime Vec3 values have x/y/z. Bounds have finite,
increasing min/max. Named spots are lists; test length before indexing or modulo.
Rules use `world.map.spot(name)` / `spots(name)`; the view uses `room.map.spots[name]`.

With `space: { dims: 3 }`, z is up and pos is the body's feet. Three.js renders
`(x,z,y)`. Gravity, jumping and facing belong in move, animation in the view.
Use continuous sweeps, then slide the remainder along the contact tangent.
`world.sweep` includes entity bodies. Movement sees the map plus declared live colliders through `ctx.world` (also exposed on `ctx.map`).

| Map list (at most 100,000 shapes in all) | JSON shape |
| --- | --- |
| boxes | `{ "min": [0,0,0], "max": [2,2,1] }` |
| circles (vertical columns in 3D) | `{ "at": [4,0,0], "r": 1 }` |
| spheres | `{ "at": [0,0,2], "r": 1 }` |
| capsules | `{ "at": [0,0,0], "r": 0.5, "height": 2 }` |
| heightTiles | `{ "at": [0,0,0], "size": [2,2], "heights": [0,1,0,1] }` |

Height tiles without `base` retain their open, foot-point top surface. Add `base`
(a height offset from `at.z`, at or below all four samples) for a closed solid:
vertical sides, the sampled top and a flat underside. For example the relay ramp
is `{ "at": [-2.5,5,0], "size": [5,12], "heights": [4,4,0,0], "base": 0 }`.
Raise `at.z` or `base` for roofs and underpasses. `diagonal` defaults to `"00-11"`;
`"10-01"` preserves meshes split the other way. Row order is 00,10,01,11.
Noncoplanar cells are two triangular prisms, never a convex hull or bilinear patch.
Solid tiles use the whole declared body for sweeps, support and overlap; rays hit
sides and undersides as well as tops. Capsules sit above slopes by their rounded
foot's clearance, rather than embedding their lower sphere in a foot-point surface.

`compileMap` builds an immutable spatial index, shared in meaning by authority and
prediction. Queries charge visited bounds and actual geometry tests, not every
shape in the map; live colliders remain a separate overlay. A 100,000-shape map is
supported without decimation or a larger tick budget. Dense local geometry still
costs work. Walk slopes by projecting the remaining sweep onto a walkable contact
normal. For a step, sweep upward for head clearance, sweep across, then support
and sweep down; never teleport upward through a ceiling. Keep jump and snap-down
limits in the shared move function. A rendered mesh is not a collider. Draw solid geometry
from room.map, including spheres/capsules/heightTiles. Changing the map changes
state compatibility; it is static build data, not a per-room saved copy.

`tunables.json` contains public movement/view values under `public`; other keys are
private rules values. Both a plain value and a record with `value` are accepted:
```json
{"public":{"speed":{"value":6}},"enemyHealth":{"value":3}}
```
Rules read `world.tune.speed` and `world.tune.enemyHealth`; movement reads
`ctx.tune.speed`. Do not put secrets in public values.

Maps use metres. Boxes have `min`/`max`, circles have `at`/`r`, and spots are named
lists of coordinates: `{"boxes":[{"min":[-1,-1],"max":[1,1]}],
"circles":[{"at":[4,0],"r":1}],"spots":{"start":[[-5,0],[5,0]]}}`.
Include bounds as above. A missing spot name returns an empty list, so check its
length before taking an entry or using modulo.

## Stationary games and live apps

A player's kind currently requires a body and a named move handler even when the
interface is a board, quiz or poll. Use `body: { shape: 'circle', radius: 0.1,
maxSpeed: 0 }` and `defineMove({ participant() {} })` for a `participant` kind.
The anchor need not be drawn. Use commands for choices; validate whose turn it is,
then send an event to a room handler to update shared state. Do not fabricate movement
or a score to satisfy a test.
The toolkit derives the stationary movement probe from all declared player kinds
having maxSpeed 0. Movement checks then say N/A; prove actual command feedback,
turns and shared results yourself. This is not a pass for the game's controls.
Native DOM buttons can use `onclick`. Keep them outside `guardGestures`' `touch`
selector (its default is `canvas`): that selector suppresses native touch clicks.
If a gameplay button must be inside that surface, handle its touch pointer
explicitly as well as mouse/keyboard activation, without firing twice. Prove it
with a real touchscreen tap in Chrome; calling `element.click()` does not test
touch delivery.
Use `rounds: { seconds: 0, breakSeconds: 0 }` for manual rounds, and no fill bots
for an app. A wall/TV watches without taking a seat. Each interactive phone
takes one of the room's declared seats; shared state is replicated, public and transient. An app's
lasting, authorized business data belongs in `createAppRecords`, not in room fields.

## Lasting worlds and account characters

For a world that should still exist tomorrow, set game.json:

```json
{"room":{"host":"server","lifetime":"persistent","characters":true}}
```

Lasting worlds default to `offline: false`: wait for the durable server. A studio
may explicitly set `offline: true` for separate local practice, whose progress
is not saved to the world or account. Never count that as proof of persistence.

`characters` is optional: `lifetime` alone keeps the world. Account characters
require the existing studio sign-in/passkey. Play redirects to the account page
when needed. In `room.join(ctx, player)`, return
`player.character ?? { kind: 'runner', at: spawn }`. Keep inventory in that player
kind's declared fields and change it only in rules. Mark inventory/currency and
collectible-ID sets with `{durable: true, visibility: 'owner'}`; use `durable: true`
for world changes and public progress too, omitting visibility only when public.
Durability and recipient visibility are separate declarations. The runtime returns its kind,
position, heading, fields and motion to the account when it leaves. Use
`player: true` or `leave: 'despawn'`; a returned character cannot also become a bot.
Do not reset inventory in `arrive`, round-start handlers or `world.finish`.

The public world has a stable room name; `?room=<name>` chooses another world.
Every durable change commits before publishing its results. An empty world sleeps and
retains state. A failed write stops play with the last good save intact. Another
room waits for the current holder to return the character; no timeout grants a
stale copy. No database or IDs are set up by hand. Ordinary games keep their
existing save frequency and behavior.

Write idempotent pickups using a saved collectible ID/set; duplicate commands
must not mint again. Events arrive later and can become `undeliverable` when a
recipient leaves; do not treat sending one as an atomic inventory transfer.
Trading and shop-grant consumption need the later economy slice. Browser saves
remain player-owned and are not an authoritative inventory.

Durable fields, entity lifecycle, pending events and character leases use an
atomic incremental journal. The rest is checkpointed every 30 seconds by default
(`room.durability.movementSeconds`, 1–60), and on pause/shutdown. Unchanged rooms
write nothing. A crash can rewind movement, but committed value and consumed
inputs replay together exactly once. Declare every fact needed to prevent a
repeat reward durable, including pickup IDs and cooldowns that protect value.
Compatible deploys still restart/reload and then restore the world.
A state-schema change is refused on restore with data retained; keep the previous
compatible build until migrations ship. Offline play has no account authority.

For proof, build normally, then sign two players in and test movement, pickup,
restart mid-pickup, a compatible rebuild, and a fresh profile signing in as the
same player. Verify actual inventory and world state. A lasting world need not
finish a round: its browser proof replaces the match check's round requirement.

## State and field types

`f` declares state, event/command/effect payloads, ask state and guide views.
Each field starts at its zero value unless supplied `{ init: value }`.
`{ score: true }` marks one integer field on a player's kind for round ranking.
State belongs only in `fields`, `motion`, or `shared`; never a changing module variable.

| Declaration | Value, range and example |
| --- | --- |
| `f.u8()` | Integer 0–255; `hp: f.u8({ init: 100 })` |
| `f.u16()` | Integer 0–65535; `score: f.u16({ score: true })` |
| `f.u32()` | Integer 0–4294967295; `total: f.u32()` |
| `f.i8()` | Integer -128–127; `ax: f.i8()` |
| `f.i16()` | Integer -32768–32767; `points: f.i16()` |
| `f.i32()` | Integer -2147483648–2147483647; `balance: f.i32()` |
| `f.fix()` | Multiples of 1/4096, ±2147483648; `fuel: f.fix({ init: 1 })` |
| `f.bit()` | Boolean; `alive: f.bit({ init: true })` |
| `f.press()` | Input-only one-shot boolean button; `fire: f.press()` |
| `f.held()` | Input-only number averaged over the tick (0.46.3); `ax: f.held()` |
| `f.tick()` | Absolute tick, 0–4294967295; `until: f.tick()` |
| `f.ticks()` | Tick duration, same range; `cooldown: f.ticks()` |
| `f.vec3()` | Float32 vector `{x,y,z}`; `target: f.vec3()` |
| `f.dir()` | Normalized ground direction; `aim: f.dir()` |
| `f.ref()` | Entity ID text, at most 24 characters; `victim: f.ref()` |
| `f.text(40)` | Text, declared maximum 1–4096 characters; `label: f.text(40)` |
| `f.list(f.u8(), 8)` | Ordered list, readonly on read: copy and assign to edit; maximum 1–1024; `cards: f.list(f.u8(), 8)` |
| `f.map(f.u16(), 32)` | Text-keyed map, maximum 1–1024 entries; `scores: f.map(f.u16(), 32)` |
| `f.struct({ hp: f.u8() })` | Fixed named fields; `status: f.struct({ hp: f.u8() })` |

Vector writes may omit z (it becomes zero); reads contain all three coordinates.
Integer writes round and clamp, not wrap. Guard against underflow explicitly:
`self.hp = Math.max(0, self.hp - damage)`. Inputs may contain only integer types,
fix, held, bit and press. Each field may hold at most 16,384 cells and a kind 65,536.
A scalar is one cell; a vector four; a text is `1 + ceil(max/64)`;
a list is `1 + max * itemCells`; a map is `1 + max * (1 + itemCells)`;
a struct is one plus the cells of its fields. Map keys are at most 32 characters.

A field holds only what its type can hold. A live room never stops for a value
that does not fit: it stores the nearest thing the type holds, says nothing, and
the game plays on. The build's play watches the same writes, and refuses the
build for the ones that lose what the handler wrote, naming the file and line of
the write.

| Written by a handler | A live room stores | The build |
| --- | --- | --- |
| A whole number outside its range, a fraction in a whole-number field | The value rounded and held to the nearest end of the range. `Infinity` is the top of the range and `-Infinity` the bottom, so `Infinity` may stand for "never" in a whole-number field | Builds. One `info:` line a field says how often it was held to its range |
| `NaN` in any number or vector | `0` | Refused: `runner.fields.score was written NaN`. Check the divisor before dividing, and that what is read exists |
| `Infinity` or `-Infinity` in a `fix` or a vector; a number past 3e38 in a vector | `0` | Refused |
| A list or a map with more entries than declared, a text longer than declared | The first entries, the first keys, the first characters: the rest is dropped | Refused: `shared.history was written a map of 9 keys for a size of 8`. Remove old entries first, or declare the size the game needs |
| A map key longer than 32 characters, or `constructor`, `prototype`, `__proto__` | The map without that entry | Refused |
| A `Map`, a `Set`, or anything else that is not a list where a list is declared, or not a plain object where a map or a struct is | An empty list, map or struct | Refused. Use `Map` and `Set` inside a handler, and copy their entries into a list or a plain object before storing them |
| A 257th effect in one tick | Nothing: the effect is dropped | Refused |
| A key returned by `think` that is not one of the kind's inputs | Nothing: the key is ignored | Refused |
| `undefined` (an absent list entry, a field left out of `spawn`, `join` or `think`) | The zero of the type: `0`, `''`, `false`, an empty list | Builds |
| `-0` | `0`. There is one zero, so `1 / self.speed` has the same sign before and after a restart | Builds |
| An object with properties the struct does not declare | The declared fields; the others are dropped | Builds |
| A number a 32-bit float cannot hold exactly, in a vector | The nearest 32-bit float | Builds |

A list, map or struct may also be changed in place (`self.cards.push(2)`,
`world.shared.seen[key] = 1`). The handler runs on, and the field is held to its
type when the handler ends, by the same rules: a live room cuts a list that grew
past its size then, and keeps every other change the handler made. The build
names the handler and says the field was changed in place, because there is no
single line that wrote it.

A browser runs `move` for its own body and holds what `move` leaves by the same
rules, in silence. The build plays that step too and refuses `NaN` in a position
or a velocity.

Everything a field holds is saved and restored exactly, including the order of a
map's keys.

Reading an absent map key throws, even with `??` afterward. Test membership first:
`const score = key in self.scores ? self.scores[key] : 0;`.
Query and event lists are readonly. Assignment into declared state copies them:
`self.cards = event.cards;`. To edit a readonly list, copy first:
`const cards = [...event.cards]; cards.push(2); self.cards = cards;`.
The compiler treats declared lists as readonly on read; use the same copy-and-assign
pattern for changes to your own lists.

Every entity has readonly `id`, `kind`, `pos`, `grounded`, and `input`; writable
`vel`, `heading` and its declared fields; and a `motion` record containing writable
movement state. Players also have readonly `seat`, `owner`, `driver`
(`person`, `bot`, `ai`), `away`, and `goal`. These facts come from the server.
Do not add a role, policy, owner or guide field to client input as a source of authority.

## Handler slots

| Slot | Arguments and purpose |
| --- | --- |
| `room.start` | `(world)` once when a match starts; initialize shared state or spawn objects |
| `room.join` | `(ctx, player)` returns `{kind, at, heading?, fields?, motion?}` for a player body |
| `room.on.name` | `(world, event)` room event, including built-ins below |
| `entities.kind.tick` | `(world, self)` each tick for each such entity |
| `entities.kind.think` | `(world, self)` returns partial input for bots or away players; missing values become zero |
| `entities.kind.on.name` | `(world, self, event)` a targeted event |
| `entities.kind.commands.name` | `(world, self, data)` a command declared in `shapes.commands` |
| `entities.kind.onRoom.name` | `(world, self, event)` an announcement or round event |
| `entities.kind.guide.view` | `(world, readonlySelf)` returns the declared `shapes.view` data |
| `entities.kind.guide.floor` | `(world, self, readonlyView)` returns local guide decisions; may write declared self state |
| `asks.name.floor` | `(readonlyState)` returns picks for that ask |
| `move.kind` | `(body, input, ctx)` writes the body and returns nothing |

For example `commands: { vote(world, self, e) { self.choice = e.choice; } }`
requires `shapes.commands.vote: { choice: f.u8() }` and `fields.choice`.
A non-player body may use tick plus `world.sweep` without declaring a move function.
A player's body requires its named move function. Player bodies come from room.join,
never world.spawn, and leave through seat changes, never world.despawn.

`room.join` can read only `map`, `shared`, `tune`, `math`, and `round`.
Entity handlers can change only their own state. Room handlers alone change shared
state, announce, end rounds and finish matches. Guide views read query capabilities;
movement cannot query entities, roll dice, send events or read fields/shared state.

## Built-in events

These names need no declaration in shapes. Event data is readonly.

| Event | Where | Data and example |
| --- | --- | --- |
| `arrive` | entity `on` | `{why: 'join' | 'spawn'}`; `arrive(world, self) { self.hp = 100; }` |
| `leave` | entity `on` | Only for `leave: 'despawn'`; `{}`; `leave(world, self) { world.sendRoom('departed', { id: self.id }); }` |
| `takeover` | entity `on` | `{}`; `takeover(world, self) { self.motion.frozen = false; }` |
| `seatJoined` | room `on` | `{seat,id,driver,owner,took}`; `seatJoined(world, e) { world.shared.lastSeat = e.seat; }` |
| `seatAway` | room `on` | `{seat,id,away}`; `seatAway(world, e) { world.shared.absent = e.away; }` |
| `seatLeft` | room `on` | `{seat,id}`; `seatLeft(world, e) { world.shared.lastSeat = e.seat; }` |
| `roundStart` | room `on`, entity `onRoom` | `{n}`; `roundStart(world, self) { self.score = 0; }` in entity scope |
| `roundOver` | room `on`, entity `onRoom` | `{n,results}`; results have `seat,id,driver,score,place` |
| `undeliverable` | sender's entity `on` or room `on` | `{to,event,data}`; `undeliverable(world, self) { self.target = ''; }` |
| `answer` | ask caller's entity `on` or room `on` | `{ask,by,picks,why}`; a union discriminated by `ask`; check `e.ask` to get that ask's typed `picks` (choice names, booleans or numbers) |

`onRoom` receives declared announcements and round events, not seat events.
An event sent this tick arrives on a later tick. A removed target causes
undeliverable to return to the sender. A room event handler is `(world,e)`,
not `(world,self,e)`.

## World calls, costs and limits

Costs are step-budget units, plus the guard's call/argument costs. Each handler
gets one quarter of `room.budget.tick`; loops and calls consume budget too.
Let `N` be the number of entities, `S` the map's boxes + circles + four boundaries,
`C` the cells copied in a payload, and `Q` pending events/timers. Copy cost is `6C`.
Snapshot output costs four units per cell each tick. A scalar field write costs
three; a vector write costs 24; copying a collection costs six per copied cell.
These costs bound work, not elapsed wall time.

| Call | Scope, cost, limits | Correct example |
| --- | --- | --- |
| `ticks(seconds)` | All clocks; 1; positive seconds round to at least one tick, otherwise zero | `world.after(world.ticks(2), 'ready', {})` |
| `random()` | Entity/room; 1; seeded and saved, [0,1) | `const n = Math.floor(world.random() * 6);` |
| `send(id,event,data?)` | Entity/room; 16 + 6C; declared events only | `world.send(other.id, 'hit', { damage: 1 })` |
| `sendRoom(event,data?)` | Entity/room; 16 + 6C | `world.sendRoom('finished', { by: self.id })` |
| `announce(event,data?)` | Room only; 16 + 6C, delivery visits entities | `world.announce('reset', {})` |
| `sendArea(area,event,data?)` | Entity/room; 20 + 2N + 6C; 64 areas/tick, reach 64m | `world.sendArea({sphere:{at:self.pos,r:2}}, 'hit', {damage:1})` |
| `after(ticks,event,data?)` | Entity/room; 16 + 6C; wait clamped 1–2147483647; targets caller | `world.after(20, 'ready', {})` |
| `emit(effect,at,data?)` | Declared effect; 10 + 6C; at is position or ID; 256 effects a tick, and the next one throws | `world.emit('spark', self.pos, {})` |
| `emit(effect,at,data,audience)` | The same, plus 8, for who may perceive it (0.46.3): `{within: metres}`, `{to: id}` or `{to: [ids]}` (32 at most), or both | `world.emit('grunt', self.id, {}, {within: 45})` |
| `spawn(kind,at,fields?)` | Entity/room; 10 + copy cost; 2048 entities, non-player kinds only | `world.spawn('coin', self.pos, { value: 2 })` |
| `despawn(self)` | Own non-player entity; constant guard cost | `world.despawn(self)` |
| `place(self,at,options?)` | Own entity; 82; options vel/heading; clamps to bounds, changes movement revision | `world.place(self, world.map.spots('start')[0])` |
| `near(at,r,kind?)` | Entity/room/guide; 20 + 2N + returned views; radius ≤64 | `const coins = world.near(self.pos, 2, 'coin');` |
| `inBox({min,max},kind?)` | Entity/room/guide; 20 + 2N + returned views; width/height ≤128 | `world.inBox({min:{x:0,y:0,z:0},max:{x:2,y:2,z:0}}, 'coin')` |
| `ray(from,dir,max)` | Entity/room/guide; 20 + 4(S+N); max ≤64; optional hit | `const hit = world.ray(self.pos, self.heading, 10);` |
| `sweep(self,delta,options?)` | Own entity; 20 + 4(S+N); ignore up to 16 entity IDs | `world.sweep(self, world.math.scale(self.vel, world.dt))` |
| `ask(name,state)` | Entity/room; 522 + floor(Q/4) + 6C; same pending ask name returns false | `world.ask('route', { target: self.pos })` |
| `goalDone(ok?)` | Entity; constant guard cost; clears goal | `world.goalDone(true)` |
| `finish()` | Room only; constant guard cost; ends match | `world.finish()` |
| `round.end()` | Room only; constant guard cost; requests end-of-round transition | `world.round.end()` |
| `map.spot(name)` | Readonly map; constant guard cost; undefined if absent | `const p = world.map.spot('home'); if (p) world.place(self, p);` |
| `map.spots(name)` | Readonly map; constant guard cost; empty list if absent | `const starts = world.map.spots('start');` |

Events and timers share a 16,384-entry queue. Avoid setting the same distant timer
every tick: use a saved `until` field or set the next timer when the last fires.
Area forms are `{sphere:{at,r}}`, `{box:{min,max}}`, `{cone:{at,dir,r,angle}}`.
A hit has `at`, `normal`, optionally `entity`; ray also has `dist`.
A returned view costs `16 + number of fields + number of motion fields`.
world.near returns nearest first and includes self when self matches the kind and radius.
Bots and away players do not send commands: implement their actions in tick using think input.
Queries return readonly views; send events to make recipients change themselves.
Math vectors are readonly too: replace `d.x += n` with
`d = { ...d, x: d.x + n }`, or use `world.math.add`/`scale`.

World properties: `tick`, `dt`, `unitsLeft` (0.46.3: budget units the running
handler may still spend, so a planner can stop early), `tune`, `shared`, `map`, `math`, `stage`, `level`,
`levelMax`, `round: {n,phase,endsAt}`. Phase is `live` or `over`.
`rounds.seconds: 0` means no automatic deadline: your room must call round.end.
A positive duration ends automatically. Round results arrive two ticks after the
ending transition, then the declared break permits a new round.

`world.math` supplies deterministic sin/cos/tan/atan/atan2/asin/acos/exp/log/pow/hypot,
rad/deg/clamp/lerp, vector vec/add/sub/scale/dot/cross,
len/dist/norm/clampLen/lerpVec/dir/angle, and constants PI/TAU.
Each math call costs four units plus guard costs. Use Math.abs/min/max/floor/ceil/round/sqrt for those elementary operations; use world.math for transcendental functions.
Do not use `**`, `Date`, timers, async/await, network, global randomness or loose `==`.
Use `===`, `world.tick`, `world.after`, `world.random` and `world.math.pow`.

## Movement

```ts
import { defineMove } from '@homie-rocks/studio/rules';
export const move = defineMove({
  runner(body, input, ctx) {
    const M = ctx.math;
    const stick = M.clampLen({ x: input.ax / 127, y: input.ay / 127, z: 0 }, 1);
    body.vel = M.scale(stick, 6);
    ctx.map.sweep(body, M.scale(body.vel, ctx.dt));
  },
});
```

Movement's `ctx` has tick, dt, ticks, math, public tune, map.name, map.spot,
map.spots, and `world.sweep/support/overlaps` (also on map). Sweeps test static shapes plus declared live colliders, cost
`20 + 4S` plus copying, writes body.pos, and returns an optional hit.
Movement may write pos, vel, heading, grounded and declared motion; never return
an updated body. Normalize diagonals and respect maxSpeed. Collision movement needs a sweep; setting velocity alone does not move a body.

### Integrating at the game's own rate

Opt in from `move` with `ctx.substeps(body, hz, step)`. For a 20 Hz room,
300 Hz runs fifteen integrations inside each tick; 60 Hz runs three. The rate
must be a positive integer multiple of the room rate. Existing movement is
unchanged unless it calls this method.

```ts
export const move = defineMove({
  runner(body, input, ctx) {
    ctx.substeps(body, 300, step => {
      if (step.first && input.jump && body.grounded)
        body.vel = { ...body.vel, z: 8 };
      body.vel = { ...body.vel, z: body.vel.z - 30 * step.dt };
      ctx.map.sweep(body, ctx.math.scale(body.vel, step.dt));
    });
  }
});
```

The callback receives `dt` (seconds), zero-based `index`, `count`, `first`
and end-of-step `fraction`. Use `step.dt` for integration; `ctx.dt` remains
the full tick. A pulse belongs to the tick: consume it on `step.first` when
it should act once. Held inputs retain their existing tick-mean semantics;
this API does not recover the timestamp of changes within a tick. A game
that already reconstructs held transitions can keep that policy in the
callback. It does not change Stormbreak's existing integration.

One body may be integrated once per move. The call charges 8 units plus
64 per pose (the initial pose and each completed substep), before allocating
the trace. Guarded callback operations and collision queries charge the
same movement-handler budget as usual. There is no separate quota or
implicit rate cap.

The browser predicts the identical callback and draws between the recorded
substep poses, including a path that leaves and returns to the same tick
endpoint. The trace is temporary drawing data: it adds no wire fields or
save fields. The final body and declared motion fields are saved as before.
This helper does not add triangle collision or a physics world.
Put freezes, boost expiry and knockback in declared motion. Initialize a late arrival
in on.arrive too: onRoom.roundStart already happened before it joined.

## The view

```ts
import { openRoom } from '@homie-rocks/studio/rules/view';
const room = openRoom();
room.on('spark', effect => {
  // Effect fields are flat: effect.at, effect.id, effect.tick, effect.damage.
  // Use fields actually declared in shapes.effects.spark.
});
function draw() {
  room.each('runner', entity => {
    // Own entity.pos is predicted; remote poses are interpolated. entity.mine marks yours.
    // Draw entity.score and other declared fields here.
  });
  const me = room.me; // your entity, or null while waiting / watching
  const shared = room.shared;
  requestAnimationFrame(draw);
}
draw();
room.input({ ax: 127, ay: 0 }); // held movement; send new values on control changes
// room.command('vote', { choice: 2 }); // only if shapes.commands declares vote
```

The testing probe assumes world X points right and world Y points up. If the canvas draws positive Y downward, use `openRoom({ screenBasis: () => ({ right: [1, 0], up: [0, -1] }) })`, as Gem Rush does. A moving camera can return its current axes; the controls check uses those axes to judge movement on screen.

`room.me` and `room.shared` are properties. `room.each(kind, callback)` visits that
kind. `room.on(effectName, callback)` returns an unsubscribe function. The payload
has the declared fields at top level and `tick`; `at` and `id` are optional: an
effect names a position or an entity. Check `if (effect.at)` before reading coordinates,
or resolve `effect.id` through room.get. There is no `data` wrapper. `room.command(name, data)` addresses the person's own entity. Use
`room.round`, `room.roster`, and `room.status` for UI. `room.round?.secondsLeft` is the displayed countdown. `room.tune` holds public tunables, and `room.map` holds the map bounds, boxes, circles and named spots. Always handle a null `me`.

Roster rows are `{ seat, name, driver, score, me }`, where driver is `'person'`,
`'bot'` or `'ai'`; there is no roster `bot` boolean. Keep AI visibly labelled.

For each companion entity, `room.askButtons(entity.id)` returns `{k,args,text}` buttons from its vocabulary and offered view. Draw their text, then call `room.ask(entity.id, button.k, button.args)` when pressed. The server validates the request and passes it to that companion's floor as `view.asks`; an accepted goal reaches its `think` handler.

## Check and repair

Run `homie-studio build <id>`. Static checks run first; declaration-derived strict
TypeScript checks rules/move/view before the game is played. Read all continuation lines.
The generated compiler project is `.studio/types/<id>/tsconfig.json`.
Import `GameWorld` and `GameSelf<'runner'>` as types for checked helper parameters.

Then the build plays the game. It joins people to a room on the real server
runtime, has them steer at random, hold every control at one end and then the
other, send every declared command with values its shape allows, and send nothing
at all (seat 1 never presses anything). People go away and come back, give up
seats and take them again, bots are switched off and on, the room is full for one
round and small for the next, and every 40 seconds the room restarts as a deploy
restarts it. A game with companions is then played a second, shorter time with
AI companions seated and people asking them for what the vocabulary offers. Bots,
companions and people who are away use the game's own `think`; a person who is
present has their body stepped by the game's `move`, as their browser steps it.

The build is refused only for something the runtime proved during that play:

| Proven | The message names |
| --- | --- |
| A handler threw, including a passed limit of the room | File, line, handler, and the tick of the play |
| A handler wrote a value the room had to change and lose (the table under State and field types: `NaN`, a list past its size) | File and line of the write, handler, field, what a live room stores instead, and the tick |
| A tick used its whole budget | The handler that used the most |
| The server held a body back because its `move` outran `body.maxSpeed` | The kind's `move` |
| A room rebuilt from its save did not save or play the same | The first field that differed |

Everything else is an `info:` line and never fails the build. One line says how
much was played: ticks, seconds of the room's clock, rounds finished, how often
the room was rebuilt from its save, and what the room held at the end (watch the
entity and waiting-event counts for a leak). A handler that never ran is named
with its line; that is information, not proof that play cannot reach it.

The play is the same on every computer: it is counted, and no clock is read. The
first room is played for 18,000 ticks (fifteen minutes of the room's clock at 20
ticks a second; to the end of one round if a round is longer, up to 36,000), or
until the room has used 280,000,000 budget units, whichever comes first. The
units are the ones a tick's budget is counted in. The second room of a game with
companions is played for 2,400 ticks, or an eighth as many units. What each person's browser uses running `move` is counted too. A
light game uses its ticks; a heavy game uses its units and so covers fewer
seconds, which the line says. `homie-studio build <id> --long-check` plays eight
times as much. Play that was not reached is not checked: a fault that needs an
hour of play is found by the long check or by playing.

Timers have no cancellation call: guard a stale timer with its round number, or
use one recurring timer.

Fix the named field or handler. Declare missing fields; copy readonly lists; check
map and key presence before reading; bound repeated queries; keep state in fields;
clamp the stick's length or declare the body's real top speed. If a message says
the check itself stopped, or that the fault is in Homie's save, the game is not at
fault: report it.

Then run local dev and `homie-studio check <id> --url <preview>` and inspect the
requested behavior. Two real browsers must join the same room and finish a round.
The generated check is finite testing, not a proof of every possible future input.

## Server companions and decisions

Declare `guide.view` and `think` on a player kind and the vocabulary in
`agents.json`. The server reserves the highest seats for AI companions under hybrid
and beginner policies, including with ordinary bots off. One seat remains available
for a person. Those bodies run `think`; input cannot grant guide authority.

`guide.view` reads the world and returns `shapes.view`. It cannot mutate state.
`guide.floor` can use entity-handler operations and write its own fields. Its third
argument includes the declared view, `goal` (or null), and `asks`, up to four
validated requests with `k`, `args`, `from` and `at`. Return `{goal, args, say, sayArgs}` (every field is optional, so `{}` declines to act)
using names from the vocabulary. The compiler checks the returned `goal` and `say` names and the exact `args` and `sayArgs` each declares against `agents.json`; a request forwards unchanged as `{ goal: ask.k, args: ask.args }`. Goals and arguments are also validated at run time against that
vocabulary, current offered choices and present players, including after restore. A floor decision outside them is discarded whole in live play, before rules can receive a goal; the build refuses it with the floor's line, the rejected name and the allowed arguments.
`self.goal` is null or `{goal,args,from,at,asked,state}`; `world.goalDone(ok)` clears it.
Views refresh at most every two seconds; active goals and companion pacing prevent
repeated floor calls on every tick. Requests can interrupt an active goal.

A game's own `asks` declare state, decision questions and a mandatory local
`floor(state)`. `world.ask` queues an answer for the calling entity or room.
Only one request per declared ask name can be pending. A valid remote answer wins;
a missing answer falls back after five seconds. Every floor must answer all the
questions with their declared types: booleans for yes/no, declared option names
for choices, and integer indices from zero through the last score level. `answer` carries `ask`, `by`, `picks` and an
optional fallback `why`. The build's generated play uses local floors on the next
tick, without a network request. With guides or a vocabulary declared, it plays a
second room with AI bodies reserved, which runs guide views, floors and validated
goals beside people, and rebuilds that room from its save as it does the first.


### Questions and answers

`asks` belongs at the top level of `defineRules`, beside `entities` and `room`.
Every ask has declared `state`, `questions` and a required local `floor(state)`.
Questions have these shapes:

| Type | Required properties | Answer |
| --- | --- | --- |
| `choice` | `instructions`, `criteria: ['hold', 'rush']` or `{hold: 'Stay', rush: 'Advance'}` | One declared option name |
| `noul` (yes/no) | `instructions`; `yes-no` is also accepted | `true` or `false` |
| `score` | `instructions`, `criteria: ['calm', 'brisk', 'wild']` | Integer `0` through `criteria.length - 1` |

`instructions` is a nonempty sentence saying what to decide. The floor must return
one pick for every question, including a score within its declared levels. Answers
return only to their caller: room asks to room `on.answer`, entity asks to that
entity's `on.answer`. A handler receiving several asks checks `e.ask` before
reading ask-specific picks; no cast is needed. Literal calls in each scope narrow
its answer union; shared helpers conservatively contribute their asks to each scope.

### A complete companion and decision example

This example uses a server room with up to four seats. Put the following vocabulary
in `agents.json`. `v` is 1; `persona` is optional. `goals` entries have `about` and
optional `args`; `lines` have `text` and optional `args`; `asks` have button `text`
and optional `goal`, `say`, `args` or `leave: true`. Arguments are `'player'` (a
present person's seat), `'view.<field>'` (one offered value or object id from that
view field), or an explicit list of allowed strings. Text placeholders use argument
names. The game never chooses identities or policy from input.

<!-- companion-example:agents -->
```json
{
  "v": 1,
  "persona": "A helpful companion.",
  "goals": {
    "guard": { "about": "Wait here" },
    "follow": { "about": "Follow a person", "args": { "seat": "player" } },
    "visit": { "about": "Visit a place", "args": { "place": "view.places" } }
  },
  "lines": { "ready": { "text": "Ready!" } },
  "asks": {
    "follow": { "text": "Follow me", "goal": "follow", "args": { "seat": "player" } },
    "visit": { "text": "Visit {place}", "goal": "visit", "args": { "place": "view.places" } }
  }
}
```

Put this in `src/rules.ts`. It includes movement, so no separate `move.ts` is needed.

<!-- companion-example:rules -->
```ts
import { defineRules, defineMove, f } from '@homie-rocks/studio/rules';

export default defineRules({
  contract: 2,
  space: { dims: 2 },
  move: defineMove({
    walker(body, input, ctx) {
      const stick = ctx.math.clampLen({ x: input.ax / 127, y: input.ay / 127, z: 0 }, 1);
      body.vel = ctx.math.scale(stick, 2);
      ctx.map.sweep(body, ctx.math.scale(body.vel, ctx.dt));
    },
  }),
  shapes: { view: { places: f.list(f.text(12), 2) } },
  shared: { tactic: f.text(8), pace: f.u8(), advance: f.bit() },
  asks: {
    plan: {
      state: { round: f.u16() },
      questions: {
        tactic: { type: 'choice', instructions: 'Choose a tactic.', criteria: ['hold', 'rush'] },
        pace: { type: 'score', instructions: 'Choose a pace.', criteria: ['calm', 'brisk', 'wild'] },
        advance: { type: 'noul', instructions: 'Should the party advance?' },
      },
      floor(state) {
        return { tactic: 'hold', pace: 1, advance: state.round > 1 };
      },
    },
  },
  entities: {
    walker: {
      player: { away: 'think', leave: 'bot' },
      input: { ax: f.i8(), ay: f.i8() },
      body: { shape: 'circle', radius: 0.3, maxSpeed: 2 },
      guide: {
        view() { return { places: ['camp'] }; },
        floor(world, self, view) {
          const ask = view.asks[0];
          if (ask) return { goal: ask.k, args: ask.args, say: 'ready' };
          return { goal: 'guard' };
        },
      },
      think(world, self) {
        const goal = self.goal;
        if (!goal || goal.goal === 'guard') return { ax: 0, ay: 0 };
        const target = goal.goal === 'follow'
          ? world.near(self.pos, 64, 'walker').find(p => p.seat === goal.args.seat)?.pos
          : world.map.spot(goal.args.place);
        if (!target) { world.goalDone(false); return { ax: 0, ay: 0 }; }
        if (world.math.dist(self.pos, target) < 0.5) {
          world.goalDone(true);
          return { ax: 0, ay: 0 };
        }
        const step = world.math.clampLen(world.math.sub(target, self.pos), 1);
        return { ax: Math.round(step.x * 127), ay: Math.round(step.y * 127) };
      },
    },
  },
  room: {
    rounds: { seconds: 30, breakSeconds: 5 },
    join(ctx) { return { kind: 'walker', at: ctx.map.spots('start')[0] }; },
    on: {
      roundStart(world) { world.ask('plan', { round: world.round.n }); },
      answer(world, e) {
        if (e.ask === 'plan') {
          world.shared.tactic = e.picks.tactic;
          world.shared.pace = e.picks.pace;
          world.shared.advance = e.picks.advance;
        }
      },
    },
  },
});
```

Use a map with a `start` and `camp` spot. For example, `map/main.json`:

<!-- companion-example:map -->
```json
{
  "bounds": { "min": [-12, -8], "max": [12, 8] },
  "boxes": [], "circles": [],
  "spots": { "start": [[0, 0]], "camp": [[4, 0]] }
}
```

Set `players.max` to 4 and `entry` to `src/view.ts` in `game.json`. Draw walkers
with `room.each('walker', ...)`, and their buttons with `room.askButtons(id)` as
above. Select a beginner policy with one guide or a hybrid policy with an AI seat
in the server configuration. A person remains a person; the server alone assigns
companions and admits their goals. For an enum argument, for example,
`"style": ["quiet", "bold"]`, both its goal and ask declare the same argument.

Map fields use insertion order, kept across saves. They follow plain JavaScript:
integer-index keys enumerate first in numeric order; other keys keep insertion
order. The save writes the live order and restores it in that order, so the server,
browser and restored room agree, including when reading the first key.
To remove a key, assign a replacement map without it: `const next: Record<string, number> = {}; for
(const key of Object.keys(world.shared.items)) { if (key !== removed)
next[key] = world.shared.items[key]; } world.shared.items = next;` In-place
`delete` is not supported.

An `undeliverable` handler receives a discriminated union of the declared events:
a check such as `e.event === 'give'` narrows `e.data` to the `give` payload. Views
read the same typed companion goal from player entities. The view's `goal` event
retains its runtime envelope `{slot, goal, prev, askAt}`; `goal` and `prev` contain
the vocabulary's typed arguments and a completion `state`.

The goal on an entity and on a `goal` event has the same declared goal and arguments,
and always has a boolean `asked` and a completion `state`. Entity goals are active;
completion clears them. Event and floor goals can also describe a completed goal. The entity's and floor view's `at` is a simulation tick;
the event's `at` and `askAt` use the companion clock in milliseconds.

`room.on('say', e => ...)` supplies `text: string`, `seat: number | null` and
`slot: number` (the companion slot, or -1 for legacy player speech). Companion
speech also supplies its vocabulary `line` and `args`. `room.on('ask', e => ...)`
supplies `slot`, `k`, `args`, `from` and `at`; legacy requests also have `ask`.
Speech text is safe to assign to `textContent`; it is not HTML.
`room.askButtons(id)` returns a union of the vocabulary's requests plus `text`.
Narrow `button.k` before reading an argument that only that request declares.
`room.ask(id, k, args)` is checked against the same requests: an unknown name or missing or wrongly typed arguments do not compile, and `room.ask(id, button.k, button.args)` needs no narrowing.


## Message guide: repair the cause

Read the full message, including file/line, handler, tick, seed and measured values.
Never patch node_modules, the guard, generated declarations or a probe to make a
check green. Never rename rules.ts away or fall back to old-style hosting.

| Message family | Next action |
| --- | --- |
| index.html: load the built view | Use `<script type="module" src="./assets/main.js"></script>`; game/app.json entry remains src/view.ts. |
| Syntax/global/import/load-time guard | Move DOM, audio, clocks, network and dependencies into view. Use local pure helpers, world math/random/timers in handlers, literal module constants and declared state. No mutable module closures, classes, try/catch or computed prototype access. |
| Linked module has an uncounted function or unchecked operation | This is the final verification of the built artifact. Preserve the source and full diagnostic as a toolkit reproduction; never remove that verification or patch its output. Check that the installed toolkit and build are current and consistent. |
| Unknown field/handler/payload or TypeScript | Read generated types and the declaration; fix spelling, declare the bounded shape, narrow kind/event/ask before using its fields. Do not cast away capability errors. |
| Missing key/property | Test `key in object` or list length before reading; `??` does not guard the read. |
| Readonly/entity/shared capability | Copy and reassign own collections; send a declared event to another entity; sendRoom for a room handler to change shared. |
| Handler threw / invalid return / companion decision | Fix the named handler's argument or vocabulary name. Use only declared options and available player/quest values; handle empty queries. |
| Value lost / NaN / list, map, text or effect overflow | Check divisor and absent inputs; bound/splice collections before storing, or declare their actual bounded size. Emit fewer effects. Integer rounding/clamping info alone is not failure. |
| Budget exhausted | Reduce repeated scans, range, per-tick work and growth; schedule bounded work over ticks. Inspect the most expensive named handler. Keep the default budget unless actual game requirements justify measured tuning. |
| maxSpeed held movement | Normalize stick and diagonal input; check metres/seconds and acceleration. Declare normal maximum running speed accurately. Knocks/dashes use motion; don't multiply the limit to hide a broken step. |
| Save/replay differs | Eliminate undeclared state and nondeterministic operations. If explicitly a Homie save or check-internal fault, preserve the reproduction and report it; don't rewrite correct game state to evade it. |
| info: coverage, clamps, unreached handler, counts | Not a failure. Exercise important unreached behavior yourself; growing entity/event counts suggest a leak. `--long-check` extends deterministic play. No claim that finite smoke proves every future input. |
| Browser wire allowance / oversized frame | Reduce declared state/payloads or rate. Browser-hosted excess fails; server-only warnings still deserve inspection. No hand-packed replacement transport. |
| host-failed | Rules did not start: read its reason and server log, rebuild the complete site with this game's rules and view from the same build. No silent browser fallback. |
| host-fault / tick-failed / room-over (budget, fault, overrun) | Inspect the named build/kind/handler and tick counters. Repair bounded work or the fault; overrun may be runner load and is not itself evidence of nondeterministic game code. The ended room stays ended; use a fresh room after fixing. |
| restore loop | Inspect repeated host restarts and other rooms sharing the isolate. The third restored failure ends the match; do not keep retrying the saved failure. |
| stale / room-stale / changed state, rematch | Reload into the current build. Same state shape restores; incompatible state starts a fresh match. Rules builds use automatic hashes, not manual netplay.version. |
| connecting / reconnecting / offline / full / closed | Display the helper's true link/standing. Test the actual URL and running dev server; offline practice is not evidence of a shared room. A full room watches/waits; closed errors show their reason. |
| kicked, muted, room-closed, agents-off, agent-pace | Respect the owner/server policy and retry delay. Never change identity or bypass policy to make testing pass. |
| Two-browser check failed / no round | Read screenshots, console and room facts. Verify same server room and real win/round transition. A turn game needs its actual inputs exercised, not dummy motion/rounds. App checks exercise their declared action and reconnect, without rounds. |

`room.probe` adds truthful frame/mechanic/render counters to the built-in rules probe.
Use the normal build, local dev and two-browser check, then play the requested mechanic
for a minute with delay. Movement should respond before the authoritative response;
score and other shared outcomes still arrive with the network. The studio chooses `players.max`; neither frame rate nor feel is guaranteed by a passing build.

Room state is saved automatically (default movementSeconds: 1, plus round end,
pause and finish; a lasting world instead journals its durable fields at once and
checkpoints the rest every 30 seconds). After 60 seconds with no person the room ends even if screens or
AI remain. A room whose people have all stopped playing rests: its clock stops with everybody still
connected and the room hibernates, so it is not charged for duration while it sleeps. It still wakes about once a
minute for a liveness alarm (one request, and the CPU of that short wake). A deliberate rest is restored as the same
world, under the same epoch, without rewriting the save. The first input, command, AI command, returning page
or new arrival starts it again on the tick it rested on. "Stopped playing" is nothing held, pressed or sent for
`room.restSeconds` (default 60), or ten seconds with every page in the background. An AI command counts as playing
and wakes a room that is already resting. `room.rest` says what else must be true. `"quiet"` (the default): the
world has nothing of its own to do, meaning no round clock running, no event, timer, spawn or ask waiting, nothing
moving, and no AI command for `restSeconds`. `"idle"`: rest anyway, pausing round clocks, timers, bots and AI with
it; Coin Dash, Ember Vale, Gem Rush, Gem Rush 3D and Hero Rush 3D use it, as an away-from-keyboard pause.
`"never"` (or `restSeconds: 0`): never while somebody is here, for a world that must keep going untouched, such as a
turn timer that skips an absent player or a show people watch. A lasting world never rests. A spectator or agent on
an older build keeps pinging the room itself, so the object stays in memory while that socket is open. Browser-hosted
rules games rest the same way. A resting host's silence is not a stall. If its tab is hidden, another browser takes
the same rest and stays asleep until somebody plays. Use browser createSaves for player-owned character progress; it is not
server-verified money. Entity fields default to public. Declare visibility explicitly for private information (below); shared state and motion remain public. Use declared server round records for verified match history.


## Spatial delivery (0.45.0; milestone 2 slice 2)

For a server game with a larger map, the studio's AI can set
`"room": { "view": { "radiusM": 32 } }` in game.json to send each player only
entities within that many metres of its body (3D includes height). This is the
studio's choice: omit it or use null for the whole room. Rules and move do not
change. The player's own body is always sent. Before a body exists, its view has
no entities. Watchers still receive the whole room.

`room.each` visits visible entities; `enter`/`leave` mean coming into or out of
view, not spawning or despawning. Remove departed meshes and recreate returning
ones. Prediction and compact snapshot recovery are handled by the runtime. Live
collision geometry bypasses visual interest filtering, so a sweep or dash can
reach a collider beyond the view radius without predicting through it. Its entity
may be absent from room.each while its geometry still blocks movement.
Shared state, effects, rosters and watcher state are still public: this is not a
hidden-information feature. Browser hosting sends the whole room.

Set the room size in `players.max`. The same setting feeds rules compilation,
public admission and the automatic Gate layout; there is no 32-seat clamp.
For example, in game.json:

```json
{
  "players": { "min": 1, "max": 300 },
  "room": {
    "host": "server",
    "view": { "radiusM": 12, "precisionM": 0.01, "nearM": 4, "farHz": 5 }
  }
}
```

These are example visual settings, not defaults. `precisionM` rounds remote
positions and velocities in the delivered view; controlled bodies stay exact.
Remote bodies outside `nearM` update at `farHz`; visibility exits are immediate.
Rules, collision, saves and shared state stay authoritative and unchanged.
Views must interpolate distant motion and dispose/recreate entities on view exit
and entry. Omit the settings for full precision and the room's normal tick rate.

A small room embeds delivery in its Table. Larger rooms open Gate connections, one channel
from each Gate to the room: the room runs the rules and hands each Gate one world a tick, and
the Gate selects, encodes and paces each player's view. A player on a slow connection is sent
fewer, fresher frames, never a growing backlog; draw from the newest snapshot and interpolate.
A body that keeps its course is not sent every tick: the view library moves it along its last
velocity, and it is sent again when that has drifted past `view.precisionM` (near bodies) or half
the distance it covers between `view.farHz` refreshes (far ones). `precisionM` is what a crowd
costs a player's connection: 0.01 is a centimetre; 0.05 sends about a sixth fewer bytes.
Homie sets no pace on what a player sends a server-hosted game. To set your own, add
`"rates": { "in": 60 }` to `room` in game.json: messages a second per player, by frame kind.
The studio template supplies the Gate exports, bindings and
migration; upgrade the template before deploying an existing studio. No infrastructure naming or studio admission ceiling is required.
Read the local measurements and their limitations in
`docs/rooms-milestone-2-notes.md` before making a capacity claim.

## Live collision geometry (0.44.1)

```ts
cover: {
  fields: { size: f.vec3({init: {x: 3, y: .3, z: 2.6}}), solid: f.bit({init: true}) },
  body: {shape: 'box', radius: .5, height: 2.6, maxSpeed: 0},
  collider: {size: 'size', enabled: 'solid'},
  // Handlers change self.size/self.solid, world.place(self, at), or despawn.
}
```

`collider: true` uses the body's shape and dimensions. The optional `size` field
supplies full axis-aligned box dimensions in metres, including rectangular 2D
walls (use a circle body with a size field). Nonpositive width/depth disables it.
`enabled` names a bit field; false removes it from movement collision. Collider
entities are non-player bodies; players use server movement (omit `body.move: 'owner'`). Their declared state and position save and restore
with the room; their refs stay opaque. Collision geometry is sent to all players
in the room, independently of visual interpolation and spatial interest, including in compact
updates and on reload/rejoin. This includes all live geometry, rather than a
speed-based margin that could miss an authored dash or sweep.

`ctx.world.sweep(body, delta)` moves and updates grounded, returning an optional
hit with at/normal and the collider's entity ref. `support(body, distance=.002)`
queries downwards without moving, returning at/normal/dist/entity, or undefined.
Use a longer distance for dive height and a short one before jumping. `overlaps(body)`
checks whether the body is inside geometry (for example, whether a pad is blocked).
2D support is the ground plane. All calls charge the movement budget; convex casts
have a bounded iteration count. The number of colliders is bounded by the room's
entity and snapshot budgets. Games without colliders send no extra snapshot data.

Every movement phase freezes one world for all movers; edits from handlers take
effect on the next movement tick. A snapshot carries a tick-stamped collision
revision for that next tick. Prediction selects revisions by effective tick, and
replays pending input after rebasing to the authoritative pose. It holds the latest
known geometry beyond received ticks: a client cannot predict an unseen remote
build/destruction. Once that update arrives, replay uses its geometry immediately.
Moving platforms use world.place in their handlers; sweep/support see each tick's
position. Passenger carrying is explicit movement logic, not automatic physics.

## Filtered combat and camera queries

`world.ray(from, direction, metres, options?)` returns the nearest hit or undefined.
`world.rayAll` returns all entry hits in distance order (one per shape or named
part, not exit faces). Static geometry wins equal-distance ties; entity and part
insertion order break remaining ties. Both queries charge their scans, geometry,
filtering and output to the normal handler budget. The maximum ray distance is 10,000 metres; radius queries keep their 64 m bound; no query raises the game's budget.

```ts
runner: {
  // Movement remains a capsule; these boxes apply only to ray queries.
  body: {shape: 'capsule', radius: .42, height: 1.8, maxSpeed: 22},
  query: {layer: 'fighters', tags: ['damageable'], parts: {
    body: {shape: 'box', radius: .42, height: 1.5},
    head: {shape: 'box', radius: .24, height: .4, offset: {x: 0, y: 0, z: 1.5}},
  }},
  fields: {hp: f.fix({init: 100})},
  // ...player, inputs, movement and handlers...
}
```

Parts are axis-aligned, feet-relative shapes, at most 16 per kind. `hit.part`
is their declared name. A kind without parts uses its normal body or enabled
collider. Parts do not resize movement bodies. Optional `query.profiles` holds up to eight named part sets; `profile` in ray options selects one, falling back to the default parts when that kind has no matching profile. For example, projectile travel may use a full-height box while bullets use separate body/head boxes. Geometry-only rays always use collision shapes. Query layers and tags are static
kind declarations. A live collider's `enabled` and `size` fields still control
its presence and dimensions.

Options are plain data, never callbacks:

- `kind`, `tag`, `layer`: exact entity-kind, declared-tag and layer matches.
  Undeclared layers default to `geometry` for live colliders and `body` otherwise.
  Static map shapes use `geometry` and are not subject to kind/tag/field filters.
- `where: {hp: {gt: 0}}`: filter declared entity fields. Values may be exact
  numbers, strings or booleans; numeric tests are `gt`, `gte`, `lt`, `lte`, plus
  `eq`. All tests must match. Missing fields do not match. At most 16 fields.
- `ignore: [ref]`: at most 16 opaque entity refs. Entity-handler and movement rays ignore their own entity
  by default; `ignoreSelf: false` includes it. This also applies when a moving
  non-player entity is itself a live collider. Local view rays use the own player
  as caller; room-handler rays have no implicit caller. Rocket travel can ignore its owner explicitly; blast damage
  may include the owner.
- `geometryOnly: true`: map plus enabled live colliders, using their collision
  shape rather than hit parts. Fighters do not shield other fighters. Use an
  exclusion when testing the visibility of the cover being damaged. Evaluate
  every visibility ray before sending damage events to preserve pre-blast cover.
- `entitiesOnly: true`: omit the static map. Combine with the filters above.
- `radius` and `shape`: cast a sphere (default) or axis-aligned box with this
  half-size around the ray centre, useful for camera clearance. Radius defaults
  to zero and is at most 100 metres. A point ray beginning inside a solid reports
  an immediate hit; movement sweeps continue to allow escape from overlap.

`room.ray` and `room.rayAll` use the same implementation for local aiming and
cosmetic feedback. They use the drawn entity poses and latest known live geometry;
only server results award damage. Spatially absent non-collider entities cannot
be targeted by the view. Unknown remote edits are not predicted.

Movement's `ctx.world.ray/rayAll` (also on `ctx.map`) query its tick's frozen static
and live collision geometry with these same options. Collider kind, layer, tags
and scalar fields accompany collision revisions, including outside visual
interest, so a predicted geometry filter has the same data as authority.
Movement cannot query fighters or award damage. These APIs do not implement lag
compensation: they query the current authoritative or presented world.

### Consent before driving an inherited bot

A player's declaration may set `control: 'accepted'`, naming a declared bit in
`motion`. When false, authority calls `think` even for a present person, and the
view draws the authoritative body without predicting that person's movement.
Commands remain available: validate an explicit consent command and set the bit
true. Initialize it on arrival and reset it in `on.takeover` when appropriate.
The server still owns driver/seat identity; this flag only controls input.

Set `takeover: 'fitness'` to name a numeric field used when selecting a fill bot.
The highest value wins (equal values use the highest seat). Update it in rules
from health, position or whatever makes a body suitable. Reserved companions
never yield. The selected entity keeps its ID, inventory and all state; only its
seat and driver change. A displaced bot retains its own state at the donor's old
seat. Without this declaration, existing seat-based selection is unchanged.

Movement queries reject distant live colliders by swept bounds before detailed
intersection, just as static map queries do. Bounds include capsule radius and
height, vertical columns and the full sweep, preserving fast travel and support.

### Ordered same-tick interactions

`world.dispatch(id, event, payload)` delivers a declared event immediately and
returns whether a live receiver had a handler. The receiver changes only its own
state; after it returns, later queries see those changes. Use it for ordered
pellets, where destroying a wall or killing a fighter changes the next ray.
Ordinary `send` retains next-tick delivery. For a blast, collect every visibility
decision before dispatching damage so one broken wall still shields that blast.

Dispatch consumes the caller's remaining handler budget, including receiver work,
and permits at most eight nested deliveries. It does not grant writes to another
entity or shared state. It is not a transaction: mutations before an error remain
subject to ordinary field coercion. Missing targets return false; there is no
queued undeliverable event for immediate delivery. Movement cannot dispatch.

Solid-terrain capsule distance queries reject triangle faces whose bounds cannot
beat the closest feature already found. This preserves exact sampled geometry,
including both source triangles and the solid sides and underside.

### Bounded actor-pose rewind

Declare `room.historySeconds: 1` (maximum two seconds). The server retains and
saves non-collider body positions and placement revisions on its virtual clock.
The view's `room.viewTick` is the tick used to interpolate remote bodies. Send it
with an action, then use `world.ray(..., {atTick, ...filters})`. Fractional ticks
interpolate saved poses. A player's request is clamped to: the relay's own
measurement of that connection's round trip, plus 150 ms of presentation delay,
plus the whole ticks the input waited between arriving and running (at least one,
at most a quarter of a second). Without a measurement only that margin is allowed.

The measurement (0.46.3) is a low percentile of the last ten seconds of round
trips timed on the input frames themselves: each frame names the newest snapshot
its browser had, and the relay knows when that snapshot left. A client cannot
make it shorter than its real latency, and holding back a separate answer no
longer raises it. A modified client can still pretend to be further away than it
is, as it could by really being so; what that buys is bounded by the game's cap.
Set `room.rewindSeconds` (from 0 to `historySeconds`): the most any shot is
rewound, whatever the connection reports. `0.25` suits a shooter: a round trip
up to about 100 ms is compensated in full and a slower player leads the target a
little. Without it the cap is `historySeconds`, as before. Client-supplied
latency figures are ignored.
A placement or new round prevents rewinding through a teleport or reset.

Rewind changes actor poses only. Eligibility filters use current fields, so a
corpse or a fighter killed by an earlier pellet cannot absorb later pellets.
Static terrain and live cover stay current: new cover blocks an old shot, and
destroyed cover no longer blocks. This conservative cover policy is explicit;
it is not a historical replay of world destruction. Rewind does not move actors,
change movement prediction, roll back damage or rewind projectiles. Choose the
window in game rules and validate actions normally; the client's tick is a claim.

Vertical capsule sweeps against solid terrain use an exact swept sphere against
the prism extended by the capsule centreline. Face, edge and vertex contacts
replace iterative grazing convergence; geometry and handler budgets stay intact.

For many related visibility or navigation queries in one handler, use
`const scene = world.rays(options)`, then `scene.ray(from, direction, metres)`
or `scene.rayAll(...)`. It captures actor poses, live geometry and filter fields
once; later damage or placement does not change that scene. Each ray is still
budgeted. Keep it local to the handler. Use ordinary `world.ray` when subsequent
hits must see mutations, such as sequential pellets. Predicted movement exposes
`ctx.world.rays` for its current geometry, too.

`world.label(playerRef)` reads the relay's current display name (including bot
names), at most 40 characters, or an empty string for a missing/non-player ref.
Copy it into a declared field when a historical message must survive departures
or seat exchanges. Names are presentation text, never proof of player identity;
use the existing owner/ref for identity. The host restores labels with its save.

For a body's planned route, capture `world.rays({geometryOnly:true,
shape:'capsule', radius:.4, height:1.8})`. A capsule ray starts at its centre;
`scene.sweep(scratchBody, delta)` and `scene.support(scratchBody, distance)` use
its foot position instead, like shared movement. A scratch body has plain `pos`
and `grounded` fields. These bounded queries change only that local copy, never
a player or the captured scene. Use the same movement helper to evaluate a
jump or dive without granting an action to the real body. Height is at least
twice the radius, at most 200 metres; spherical casts retain their diameter.

`world.round.restart()` is room-only. It abandons the current attempt and starts the
next round on the next tick, keeping seats and entities and running the normal
`roundStart` handlers. It publishes no completed results or `roundOver` event and
skips the intermission. Use it for an authorized retry; validate eligibility in
your room handler. Pending restart intent survives save/restore.


### Held input: a tap moves for the time it was down (0.46.3)

An ordinary input field is read once a tick, at the tick's edge. A key held for
60 ms of a 50 ms tick therefore moves the body for one tick or for two, by where
the edges happened to fall: short taps travel too far and vary. Declare a
movement axis `ax: f.held()` instead. The browser then sends the average of what
the control read over each tick (a key down for a third of the tick reads a
third of its value; an analogue stick reads its mean), prediction uses the same
number, and `move` multiplies speed by it as before, so the body moves for the
part of the tick the key was down. `room.input({ax: 1})` is called as usual,
every frame or on change; a boolean counts as 1. `think` returns a plain number.
Use it for movement axes, not for buttons: a button is `f.press()` or `f.pulse()`.
Keep its values in -1 to 1. An entry that reaches the server after its tick is
not counted twice: the tick it missed ran on the value before it, and the server
settles the difference on the next ticks, so the body ends where the browser
predicted.

### Effects with an audience: what a player may perceive (0.46.3)

Everything in a snapshot's public fields and every plain `world.emit` reaches
every player. A sound or a flash must not be drawn from state a rival should not
have (another player's exact health), and need not be sent to someone who could
not perceive it. Emit the event instead, and say who perceives it:

```ts
world.emit('grunt', self.id, {}, { within: 45 });            // earshot of where self stands
world.emit('hitConfirm', target.id, { damage }, { to: shooter.id }); // the shooter alone
world.emit('alarm', self.pos, {}, { within: 30, to: allies }); // either is enough
```

`within` is metres from the effect's place (the named entity's position at that
moment) to the listener's own body; `to` names entities, and the people driving
them receive it. A watcher, and a seat with no body yet, perceive the room: they
receive every effect with a `within`, and never one addressed only `to` somebody.
An effect with no audience is public, exactly as before. Delivery costs one
frame a listener on ticks that have such effects and nothing on ticks that do
not. Send what is perceivable (a hit landed, roughly how hard); send exact
numbers only `to` the player entitled to them.

### Predicting the player's own actions (0.46.3)

The own position is predicted by `move`. Other own actions (a weapon swap, a
build, a reload, a hit marker) otherwise wait for the server's round trip. Give
the view a predictor for the kind:

```ts
const room = openRoom<typeof rules>({ predict: { runner(me, input, ctx) {
  if (input.select) swap(me, input.select, ctx.tick * ctx.dt);        // the rules' own pure helper
  if (input.build && me.builds > 0) { me.builds--; ctx.ghost('cover', spot(me), { size }); }
  if (input.fire && aimHits(ctx, me)) ctx.effect('hit', me.id, {});
} } });
```

The room runs it for the own body once a predicted tick, after `move`, with that
tick's input, and on a copy between ticks, so a press answers on the next drawn
frame. `me` holds the body's declared fields (and readonly `id`, `pos`, `vel`,
`heading`, `grounded`, `motion`); what it writes is held to the declared types
and read back through `room.me`. Every snapshot puts the server's values back
and runs the still-pending inputs again, exactly as it does for the position, so
a wrong guess corrects itself. Share pure helpers with the rules (no `world`):
the server's handler remains the authority and the only place a result counts.

`ctx.ghost(kind, at, fields?, {match?, seconds?})` draws a provisional entity:
`room.each` yields it with `provisional: true` until an entity of that kind that
`match(entity)` accepts (default: within a metre) arrives, and then until that
one is drawn, so there is never a gap or a double. `ctx.effect(name, at, data?,
{match?})` fires the effect's listeners now with `predicted: true`; the server's
own effect of that name then arrives with `confirms: true` (use its exact data,
do not replay the sound). If the server ran the tick without confirming, the
room emits `retract` (`{ghost, kind}` or `{effect, ...data}`) and the ghost
leaves: take the marker down quietly. `ctx.ray/rays/rayAll` query what the
player sees (`ctx.viewTick`); `ctx.preview` says the run is between ticks. A
predictor runs often: keep it cheap, and keep per-entity state in `me`.

`ctx.each(kind, fn)` reads frozen entities from the authoritative snapshot this
prediction started from. Use it for pickups and other snapshot-based decisions;
it excludes provisional ghosts. Reading `room.each`, `room.get`, `room.me` or
ray queries inside a predictor cannot advance the clock or start a nested
preview. Other room entities retain their normal drawn poses; `room.me` reads
the authoritative own entity during the callback. Use the callback's `me` for
the predicted own state. Snapshot reconciliation also prevents clock pumping
through event listeners until replay finishes.

To guess a shot the server will judge with rewind, ask for what the server
will use (0.46.5). `ctx.judgedTick(aimTick)` is the tick it will pose the others
at: the `aimTick` the input carries, held to how far back this seat may look
right now (the server says so in every snapshot) and to this tick. Pass it on:
`ctx.ray(from, dir, max, { atTick: ctx.judgedTick(input.aimTick), ...filters })`
poses the other bodies as the server will, from the snapshots this browser
holds (between two of them, or carried on from the newest along its velocity).
Inside the allowance that is the drawn target; past the game's cap it is a newer
pose, and the predictor then shows no hit where the server will see none.
`room.poseAt(id, tick)` gives `{pos, vel, known}` for the game's own tests
(`known: false` is a guess past the newest snapshot). `ctx.math` is the rules'
own `math`, and the context is accepted by guarded rules code as a world is for
what the two share (`tick`, `dt`, `math`, `ray`, `rays`, `rayAll`, and a scene's
`ray`, `rayAll`, `sweep`, `support`), so an aiming helper written for the rules
can be called with `ctx` instead of being restated in the view. It has no
`near`, `inBox`, `send` or `emit`: a helper that needs those is the server's.

A tick's prediction runs more than once (between ticks, again when the input
changes, then the tick itself) and shows each thing once. Things are told apart
by their name and `key`: give two effects of one name that mean different things
(`ctx.effect('audio', me.id, {name: 'jump'}, {key: 'jump'})` beside a `reload`)
a `key` each, and the same for two ghosts of a kind. Read `me.id` into a constant
before using it in a `match` closure: `me` is reused. A valued pulse
(`f.pulse()`) carries the tick it was predicted on, and the server acts on it in
that tick, so a predicted swap is in the snapshot of the tick it was drawn for.

### Naming the bots (0.46.5)

`room.bots: { keep: 4, names: ['Vex', 'Moth', 'Kilo'] }` gives the game's bots its own names, by seat (the list
wraps). The roster, the round's results and `world.label(id)` all say the same name, and a restore keeps it.
Without `names` the toolkit's own list is used. A name is 1 to 24 characters on one line.

### Discrete actions with a value

Use `select: f.pulse()` for a weapon slot or other byte-valued action. Call
`room.input({select: 2})` on the press and return to zero on release. A nonzero
value is queued once, including a pulse shorter than a simulation tick; held
samples do not create repeated actions. Zero is neutral. The reliable event
channel carries these actions, with at most 16 pending per seat and one consumed
per tick. Epoch changes discard old-round actions. `f.press()` remains the
boolean equivalent; `f.u8()` is sampled state and can miss a one-frame pulse.

### Private entity fields and verified round history

Declare an entity field with `{visibility: 'server'}` for bot brains or secrets,
`{visibility: 'owner'}` for private inventory, or `{visibility: 'results'}` for
statistics revealed during intermission. Nested contents follow their top-level
field. Hidden values become neutral on the client; never depend on them in shared
movement. Server rules still read full state. Watchers receive public fields and
results only. Entity positions, driver information, shared state and motion are
public. This is field visibility, not fog-of-war entity hiding.

A collider transmits only geometry plus explicitly named public scalar fields:
`collider: {size: 'size', enabled: 'solid', fields: ['material']}`. Do not put
private fields in that list. Unchanged collision rows are inherited from the
snapshot baseline; keyframes and reconnects remain complete.

For verified history declare
`room.records: {key: 'server:career-v1', identity: 'matchKey', eligible: 'ready',
fields: {kills: 'earnedKills', damage: 'earnedDamage'}}`. The identity names a
shared text field that rules make unique for each round. The optional eligibility
names a player boolean field; result fields name numeric player fields. The
Worker associates the participant with its authenticated player ID and stores
`id`, `endedAt`, `place`, `won` and the declared totals when the round completes.
A durable outbox retries failed writes; duplicate round IDs are ignored. Read
with `createSaves().get(key)`. Browser writes, deletes and save resets cannot
change `server:` records. Keep guest/authentication setup active before playing.

### Opt-in exact terrain and baked navigation

Legacy three-argument rays keep their historical result and cost. Supplying ray
options enables the richer query policy, including hits at distance zero when
starting inside solids. Terrain changes are separate: set `terrain: 'exact'` in
ray options or the entity body declaration to use exact face/edge/vertex terrain
casts. Existing terrain behavior is retained when omitted. Test your map's
slopes, ledges and movement when opting in.

Declare static graphs once with `navigation: {walk: graph}` in `defineRules`, then
call `world.route('walk', from, to, {radius, height})`. Compilation validates and
copies the graph once; handlers pay for the live search, not graph validation.
At most eight named graphs with 8192 nodes total are accepted. Unknown names fail.
The array form remains available for occasional dynamic graphs.

`world.route(graph, from, to, {radius, height})` searches an immutable authored
walking graph. Nodes are `[x, y, z, neighbourIndices]`; endpoints are node indices.
The graph has at most 8192 nodes and 16 neighbours per node. Edges must already
encode static terrain walkability. The runtime checks live colliders, returns
all node indices of a route or an empty list, and charges the search to the
handler budget. It never substitutes a partial route at an expansion cap.
Replan when the goal changes and when live geometry changes. Bake invalid or
occupied terrain nodes out of the graph, and choose reachable endpoints.
`@homie-rocks/nav` is the richer mesh/crowd API for applications that own that
runtime; rules graphs avoid importing mutable navigation state into handlers.

Small reconciliation offsets expire even while stationary; see “Input during loss
and stalls” below for the visual correction settings.

For multi-cast movement or scratch trajectory checks, `ctx.world.sweep(body, delta, {ground:false})` (also captured-scene `sweep`) moves and returns the same collision but leaves `body.grounded` unchanged. Use it only when your mover computes support explicitly. Omitting the option retains the existing support query and grounding behavior. This avoids paying for identical support checks after horizontal and upward probes.


## Wrapped worlds and generated levels (0.47.0)

Declare wrapping in the map, independently per axis. The period is the bounds'
extent; an omitted axis keeps its existing bounded behaviour:

```json
{"bounds":{"min":[0,0,0],"max":[25,25,10]},"wrap":{"x":true}}
```

Bodies and hit positions use canonical coordinates in `[min,max)`. Sweeps and rays
follow the supplied displacement through periodic copies of the geometry; they can
cross more than one period and pay for each visited image. Near/box queries, area
events, effect ranges, spatial delivery, rewind and drawing interpolation use the
short way around. Exactly half a period chooses the negative direction. A renderer
can read `room.map.wrap.x` (the pair `[min,max]`) to draw copies at the viewport's
edges. The server does not duplicate entities. In a maze with one tunnel, keep
solid border cells on every other row; wrapping itself is per axis, not per row.

For a generated maze, replace the room's current map in `room.start` or a room
handler. Build its data using the rules' seeded random source, then publish once:

```ts
world.map.replace({
  bounds: { min: [0, 0], max: [25, 25] },
  wrap: { x: true },
  tiles: { width: 25, height: 25, size: 1, data: cells,
    flows: { exit: [312] } },
  spots: { start: [[12.5, 19.5]] },
});
```

`replace` preserves the original bounds and wrapping. It validates, bakes cardinal
navigation fields and compiles the spatial index before publishing anything. A
failed bake leaves the previous revision intact. The last successful replacement
in a tick becomes current at the next tick; all bodies use the same revision.
The compact map data and activation tick travel with collision revisions and saves,
including both current and pending maps. Prediction replays against that tick's
compiled geometry. Late knowledge is corrected by the normal reconciliation path.

Tiles are row-major integers: zero is open, nonzero is solid. `at` defaults to
`[0,0,0]`, `size` and `solidHeight` to 1. Horizontal runs become indexed boxes,
including in 3D. On a wrapped axis the grid must span the full map. Authored boxes,
round shapes, terrain and spots can be included in the same replacement. The view
reads `room.map.tiles`; rules and movement read `world.map.tile(x,y)` and
`ctx.map.tile(x,y)`. Cell coordinates are integers, not metres. Outside an unwrapped
grid is solid. A custom tile mover may read these cells instead of using sweeps.

`flows` names lists of open destination cell indices. `map.distance(name,x,y)` gives
cardinal hops to the nearest destination, or -1 when unreachable/unknown;
`map.flow(name,x,y)` gives the next unit direction, zero at a destination, or
undefined when unreachable/unknown. Each lookup is constant work (4 or 8 budget
units). Baking uses `@homie-rocks/nav`'s shared cardinal flow implementation;
left/up/right/down resolves ties, including tunnels. Change destinations by
publishing new flow declarations with the map. This is a bake, not an unmetered
path search: budget for every field and regenerate only when its goals change.

Room replacement charges copying, grid scanning, index construction and each flow
bake to the calling handler. Snapshots charge for the compact data. Existing static
maps need no replacement and retain their previous budget charges. A few thousand
cells regenerated a few times a round belong in one map revision; live collider
entities remain suitable for independently moving doors, cover and platforms.

`spawn` exposes a new entity before its deferred `on.arrive` handler. Pass every
field that must be valid immediately in the spawn data; use `arrive` for subsequent
work, not for mandatory initialization.

## Physics

Use the opt-in `@homie-rocks/physics` bridge when the level is an arbitrary triangle
mesh: caves, ramps, stairs and the static environment of a game such as Octree
Arena. Keep `ctx.map` for the kernel's boxes, circles, capsules and height tiles.
Install `@homie-rocks/physics` 0.1.2 in the studio. A game that does not
ask for physics loads no physics engine and pays no physics units.

In `map/main.json`, name a static GLB relative to the game directory:

```json
{
  "bounds": { "min": [-100, -100, -100], "max": [100, 100, 100] },
  "physics": { "level": "assets/level.glb" }
}
```

The build bakes the default scene's node transforms and triangles into the
physics package's indexed mesh format. It converts glTF Y-up to rules Z-up
(`x, -z, y`), preserves reflected winding, and ships the baked mesh with the
server rules and the browser movement bundle. Skins, animations and morph targets
need a separate static collision GLB. The server never loads or parses a GLB.

The smallest moving capsule uses the same guarded movement on both sides:

```ts
// src/move.ts
import { defineMove } from '@homie-rocks/studio/rules';
export const move = defineMove({ runner(body, input, ctx) {
  ctx.substeps(body, 300, step => {
    if (step.first && input.jump && body.grounded)
      body.vel = { x: body.vel.x, y: body.vel.y, z: 10 };
    body.vel = { x: input.ax * 5, y: 0, z: body.vel.z - 30 * step.dt };
    ctx.physics.sweep(body, ctx.math.scale(body.vel, step.dt), .35, 1.35);
  });
} });

// src/rules.ts
import { defineRules, f } from '@homie-rocks/studio/rules';
import { move } from './move';
export default defineRules({
  contract: 2, space: { dims: 3 }, move,
  entities: { runner: {
    player: true,
    input: { ax: f.held(), jump: f.press() },
    body: { shape: 'capsule', radius: .35, height: 1.35, maxSpeed: 30 }
  } },
  room: { bots: { keep: 0 }, join() {
    return { kind: 'runner', at: { x: 0, y: 0, z: 8 } };
  } }
});
```

Use `"room": {"host":"server","offline":false}` in `game.json`. Physics
initialization is awaited once per isolate before any room can tick; calls inside
a handler are synchronous. `sweep(body, delta, radius, height)` sweeps and slides
an upright capsule whose `body.pos` is its centre and whose height includes its
caps. It writes position, velocity and grounded state. `ctx.physics.cast`,
`ray`, and `overlap` expose the package's convex shape cast, raycast and overlap
queries; query shapes are boxes, spheres or capsules. Room/entity handlers have
these operations at `world.physics` and can call `world.physics.step(seconds)`
to advance the collision world's solver clock. Movement owns capsule integration;
its queries do not create persistent physics bodies or advance another player's
world. This bridge exposes the baked collision world, not rigid-body ownership or
predicted dynamic-body interactions.

Every operation is charged before its engine work. On a 1,754-triangle level:

| Operation | Budget units |
| --- | ---: |
| Capsule/convex cast | 768 |
| Ray | 640 |
| Overlap | 640 |
| Solver step | 8 + 2,400 per 1/300 second |
| Capsule sweep and slide | 64 + 768 per cast, at most four casts |

Mesh-query and solver charges scale by `ceil(triangles / 1754)`, at least one.
Substeps retain their usual pose and guarded callback charges. There is no new
room budget, player cap or rate quota. The reproducible calibration is
`scripts/calibrate-rules-physics.mjs`; its receipt compares physics on the real
mesh with kernel operations on a box, since the kernel has no arbitrary-mesh
or solver-step equivalent.

A room save includes the package's complete binary world snapshot as JSON bytes,
including solver state and its time remainder. The capsule's position, velocity,
grounded flag and declared motion are saved by rules as usual. Browser prediction
creates the same baked world and replays pending guarded movement against it;
substep drawing traces remain temporary. Physics worlds are disposed when their
host or view closes. A full solver save can exceed browser-host checkpoint caps;
the build measures this, and server-hosted rooms retain the full save.

## Input during loss and stalls (0.48.1)

Rules views resend recent input automatically: a 4–64 tick history follows the
measured round trip, jitter and missing application receipts (loss or recovery
delay). Each tick entry carries a sequence number; each
control change carries a field index, sequence and fraction of the predicted tick.
Duplicates neither execute again nor count as fresh latency measurements. Both
missing application frames and ordered TCP stalls are covered.

The server retains up to one second of movement history and replays late movement
against the geometry of those ticks. It never repeats commands or effects. An
external body/motion write or placement fences that history. Beyond a fence or
the retained history, input applies on the next tick instead. Entries carrying
press handlers also apply next tick: world actions are never rerun as movement. Snapshot control
rows report the application tick and the view uses it for replay. Within the
replay window a snapshot still missing a predicted input does not replace live
movement; an explicit placement always does. Legacy wire
entries retain their old compensation; current views do not receive negative
held values to repay late releases.

Held controls integrate their duration, sampled controls coalesce to the latest
value per tick, presses coalesce per field per tick, and valued pulses execute
in order, one per tick. More sampled input never buys extra simulation steps.
The clock resets before a fresh control after a long browser stall, so the press
cannot inherit ten seconds of elapsed time. The prediction clock slews by at
most 0.5%, preserving the cadence for fixed-step renderers.

`room.input(sample, {at: event.timeStamp})` accepts the event's monotonic time
(same origin as `performance.now()`), clamped to this predicted tick and now.
Omit it to use the call time. A player can declare
`player: {control: 'canMove', pulses: 'hold'}` to keep pulses during a knock or
stun and deliver them when control returns. The default `'drop'` preserves the
previous behaviour. The game's action handler still decides its cooldown.

In 2D, own-body interpolation and correction are swept against the declared solid map.
Keep that map consistent with custom movement and declare a square 2D runner as
`body.shape: 'box'`. A blocked visual correction stops at contact; it never
changes authoritative movement. Use `ctx.substeps` for custom integration so
the toolkit draws the same path, without a second view-side displacement.
Substep previews include the remaining duration of controls currently held.

Residual drawing corrections use `room.predict.blendMs` (100 ms by default),
slowed on each moving axis to avoid reversing movement (jumping cannot spend
horizontal correction faster), with a one-second maximum
(or the explicitly longer blendMs). Any remainder drains over the final 250 ms
rather than disappearing on the deadline. `snapM` selects the large-error threshold;
placements still snap. A placement keeps the established clock phase and
projects the new body from the snapshot tick to the own tick; it never labels an
old pose as a future one. Projection is bounded to one second and sends the
controls it used. Queued held state from an earlier placement cannot later
change the new body. Newly received discrete presses still belong to the player
when the browser has not yet learned of that placement. `idleHold` no longer keeps a stopped body displaced
indefinitely. These drawing settings never alter server truth.

A fresh discrete movement action (press or pulse) exits the own body's historical
catch-up path. It resumes live prediction at once and carries the drawn pose into
the normal correction blend, so a counter-dash or jump does not wait for the
unseen impulse's history to finish. This changes drawing only; authority, input
timestamps, cooldowns and replay rules are unchanged.

Own box-bodied 2D presentation also sweeps from its last displayed position. Reconciliation
cannot switch sides of a solid merely because the new predicted origin is on
the other side. Travel is limited by elapsed time plus a body-sized blend. Horizontal travel uses the adjacent
actual velocities; vertical travel uses the recorded substeps with interpolation headroom, so an apex or landing is not trimmed.
A stationary correction spends only blend speed, not the declared terminal falling speed.
A large falling-speed limit cannot accelerate a horizontal correction. If sliding cannot reach a correction, a bounded
incremental route searches collision-tested edges around the obstruction. No
route means holding the last valid position, never crossing a solid. Explicit
placements and epoch changes reset presentation immediately. These positions
never feed movement, hits, scoring, input timestamps, or authority.

A platformer can supply `openRoom({ correctionDirection: input => Number(input.r || 0) - Number(input.l || 0) })`
for box-bodied 2D presentation. This is horizontal control intent (-1, 0, +1), not authority or a second movement loop.
It prevents a visual correction from reversing held controls even when contact sets velocity to zero; neutral input
allows convergence in either direction. Actual predicted braking against a newly reversed control remains allowed.

After a delayed render, box-bodied 2D presentation spends at most 1.4 body widths per drawn frame,
then continues toward prediction. This affects drawing only; an explicit placement remains immediate.

When a player's connection comes back, the server hands the body back where it has it, with a new placement
revision. Within three seconds of the link coming back online, box-bodied 2D presentation treats that revision as the
same body and draws on from where it was shown, gliding and routing around solids as for any correction. A body that
was really placed while the player was away (a respawn, a new round) should still be drawn at once: say so with
`openRoom({ respawned: (before, after) => after.diedAt !== before.diedAt })`, where `before` and `after` are the own
body as the server last had it before and after the outage.
