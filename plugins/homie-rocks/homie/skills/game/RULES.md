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
      body: { shape: 'circle', radius: 0.5, maxSpeed: 6, move: 'owner' },
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
Declare `players.max` in game.json (1–32); use `entry: "src/view.ts"` and
`room: { host: "server" }`. Only public tunables are visible in move.ts.

`index.html` is the browser entry document; include `<script type="module" src="/src/view.ts"></script>`. The build rewrites that entry to its bundle. A minimal manifest is:

```json
{"id":"keepers","name":"Keepers","entry":"src/view.ts","players":{"min":1,"max":4},"room":{"host":"server"}}
```

`id` is the folder identifier and `name` is the displayed name, `players.min` the advertised minimum and `players.max` the seat cap. `entry` names the browser source. Optional `blurb`, `tags` and `cover` describe the game on its page. `room` sets server hosting and optional `tickHz` (the default is 20). `room.bots: { keep: 4 }` in **rules.ts** asks the host to maintain four total occupied bodies when its policy allows bots; it is not four extra bots. Companion policies belong to the server's room/server configuration, not a player's frame or the game manifest. Set the server policy to `hybrid` with `aiSeats`, or `beginner` with `guides`; these reserve server-owned AI bodies, and `bots: 'off'` disables ordinary fill bots.

For example, `homie-studio servers new keepers "Practice" --policy beginner --guides 1` creates a beginner server with one guide. Use `homie-studio servers set keepers <server> --policy hybrid --ai 1` to change an existing server through its owner controls.

`body.move: 'owner'` lets an active person's browser predict and claim movement; the server bounds claims by `maxSpeed`. Without it the server runs movement from input. Bots, AI and away people are always moved on the server. A non-player entity may declare the same `body` and use `world.sweep(self, delta)`; `radius` and `maxSpeed` are required. In two dimensions `shape` is `circle`; in three dimensions the declarations also accept `sphere`, `capsule` and `box`. Map collision currently uses the ground projection and radius. `sweep: true` enables automatic map collision for movement; `world.sweep` explicitly tests a displacement and returns a hit when blocked.

The view's `room.map` contains `bounds: {min: Vec3, max: Vec3}`, `boxes: readonly {min: Vec3, max: Vec3}[]`, `circles: readonly {at: Vec3, r: number}[]` and `spots: Readonly<Record<string, readonly Vec3[]>>`. Here `Vec3` has numeric `x`, `y`, `z`. Check a named spot exists before indexing. Rules instead use `world.map.spot(name)` or `spots(name)`.

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
fix, bit and press. Each field may hold at most 16,384 cells and a kind 65,536.
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

World properties: `tick`, `dt`, `tune`, `shared`, `map`, `math`, `stage`, `level`,
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
map.spots and map.sweep. `ctx.map.sweep` tests static shapes, costs
`20 + 4S` plus copying, writes body.pos, and returns an optional hit.
Movement may write pos, vel, heading, grounded and declared motion; never return
an updated body. Normalize diagonals and respect maxSpeed. Collision movement
needs a sweep; setting velocity alone does not provide wall collision in owner mode.

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
    // entity.pos is interpolated; entity.mine marks your own body.
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
has the declared fields at top level, with `at`, `id`, and `tick`; there is no `data`
wrapper. `room.command(name, data)` addresses the person's own entity. Use
`room.round`, `room.roster`, and `room.status` for UI. `room.round?.secondsLeft` is the displayed countdown. `room.tune` holds public tunables, and `room.map` holds the map bounds, boxes, circles and named spots. Always handle a null `me`.

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
      body.pos = ctx.math.add(body.pos, ctx.math.scale(body.vel, ctx.dt));
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
