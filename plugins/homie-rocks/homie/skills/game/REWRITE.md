# Rewrite a browser-hosted game as rules plus view

Use this path when the owner asks to move an old game's rules onto the server.
There is no automatic converter yet. Version 0.45.0 keeps existing netplay games
and their port host helpers working, with their original 32-seat limit. Larger
rooms require this rewrite. Keep a baseline copy and preserve the game throughout.
Read RULES.md before starting.

1. Read this game's codex, manifest, entry, host loop, input, packing/checkpoint
   code, bots, saves and tests. Record what players must keep: controls, timings,
   movement curve, camera, art, sound, collisions, scoring, rounds and joining.
   Play a baseline on computer and phone and capture the same short actions and
   screenshots you will repeat later. Keep a commit or separate copy to compare.
   Do not change other games, shared studio configuration or their tests to make
   this game pass. Install the studio's pinned dependencies; upgrade the toolkit
   only when needed for the requested rewrite, preserving unrelated dependencies.
   An old file named rules.ts may already export pure helpers that tests import.
   Preserve that public test API and every existing test file byte-for-byte,
   including imports. Re-export the old helpers from rules.ts if extracted into
   another module; do not redirect tests to that module. Record test-file hashes
   before editing and compare them at the end. The filename alone does not
   mean it is a rules-plus-view game. If tests now load toolkit TypeScript under
   Node, use a narrowly scoped TypeScript loader and keep the normal test command
   working. Do not count a special test invocation while `npm test` is broken.
2. Keep the renderer, assets, camera, UI and audio as the view. Make an inventory
   of every value that can change play. Put each on the entity that owns it with
   declared fields; put room-wide facts in shared. Replace packed rows with named
   fields, numeric IDs with opaque refs, and remembered module state with fields.
3. Extract the existing movement curve into defineMove. Keep its units and timing
   by converting to metres and seconds at one boundary. Use ctx.math and the
   compiled map; encode knockback, cooldowns and freezes in motion. The view must
   draw room.me/room.each, not integrate a second body. The same movement now runs
   on the server and predicts on the player's screen. Preserve feel by measuring
   acceleration, jump apex, duration, stop distance and knock distance against baseline.
4. Move hits, pickups, spawns, scores and victory into rules. An entity writes only
   itself; requests to other entities become declared events. The receiver validates
   the request and changes itself, then sends a result. Shared writes and round ends
   belong to room handlers. Replace clocks and random calls with world ticks/math/RNG.
   Replace direct model calls with declared asks and a deterministic floor. Bots
   produce inputs in think. Companions use guide/view/floor and vocabulary goals.
5. Write map/main.json from the existing collision geometry. Use it for the view
   too; keep purely decorative art out of collisions. In 3D z is up in rules, feet
   locate a body, and Three.js maps x,y,z to x,z,y. Preserve spawn locations and
   arrival/reset behavior, including arrivals during the results break.
6. Replace view-side networking with openRoom<typeof rules>(). Send input and
   declared commands, listen for declared effects, retain chat/watch/prefs through
   room.net. Remove the old host loop, Roster, packing, snapshots and checkpoint
   callbacks from this game's entry. Keep cloud character saves and their key/schema;
   they remain separate from automatic room saves and are not verified currency.
   Set manifest entry to src/view.ts, index.html to the relative ./assets/main.js
   module script, and room.host to server.
   Retain the game's ID and public URLs. Do not change to browser hosting to pass.
   In a studio made before server rules, compare site/src/worker.mjs with the
   installed toolkit's Worker template: it must import the generated
   ./rules/index.mjs registry and call hostRules(rules). Add that small hookup
   while retaining the studio's existing routes and configuration. Confirm both
   browsers report hosted=server and role=replica; a successful build alone cannot
   prove an older custom Worker registered the rules.
7. Build early and after each coherent extraction. Read every diagnostic and repair
   its source using RULES.md's message guide; never edit the toolkit/guard or remove
   tests to escape a restriction. Type errors often name a capability moved to the
   wrong half. A save/checker internal failure must be reported as such.
8. Repeat the baseline in two real browsers with 150 ms delay: same controls, art,
   camera, first minute, win/loss and next round; both browsers must be replicas of
   the server. Check late join, reload, reconnect and a player leaving. Run check,
   this game's existing tests and the studio's other tests unchanged. Compare files
   outside this game against baseline and explain any necessary shared-file change.
   Report observed differences and limits rather than claiming equivalence from a build.

Do the engineering yourself. Tell the owner what changed for their game, what was
preserved and how you checked it. Never promise larger rooms, private per-seat
state, perfect latency or automatic conversion.

For buildable/destructible worlds, declare non-player entities with `collider: true`
or `collider: {size: 'size', enabled: 'solid'}` (declared vec3 and bit fields).
Move uses `ctx.world.sweep/support/overlaps`; `ctx.map` exposes these same queries
for existing movement code. Keep build/damage/door logic in entity handlers.
Never copy collision lists into player motion or implement a second replay loop.
Test visible prediction at 300 ms with loss, rejoin and saved-room restore.
The installed toolkit's `guides/game/` is the version-matched source for this guide.


### Solid terrain and query cost

Preserve each source height triangle and its diagonal. Declare height tiles with
`base` for solid ramps, terraces, roofs and underpasses; omitting it deliberately
means an open top surface. Do not replace slopes with boxes, invisible walls or
coarser sampling. Test both sides, tall end, ascent/descent, jump, dash, underside,
step head clearance, overlap and weapon/camera/blast rays. A discrete reference
mover may stop one input increment before the continuous capsule contact; report
both numbers instead of changing its body radius to make them match.

Map compilation indexes up to 100,000 shapes. Measure the default-budget guarded
spawn, six initial bodies/eight seats and traversal/combat with live cover. Repeat
on seeded virtual time with 300 ms/loss, rejoin and saved-room restore, then smoke
test real browser sockets. Geometry passing alone does not complete a game rewrite.
