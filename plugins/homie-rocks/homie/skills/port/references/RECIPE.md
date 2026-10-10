# Port recipe: one rules and view contract

Read [RULES.md](../../game/RULES.md) and [REWRITE.md](../../game/REWRITE.md).
Keep the imported renderer, art, feel and controls. Move authoritative state to
`src/rules.ts`, movement to `src/move.ts`, and rendering/input to `src/view.ts`.
Declare `room.host: "server"` and the view entry in game.json. A browser or
offline build runs these same rules with `room.host: "browser"`.

Use `openRoom` from `@homie-rocks/studio/rules/view`. The view reads declared
entities, sends input and commands, and draws the room's round and roster.
Controls, camera math, audio unlock and view helpers remain available from
`@homie-rocks/studio/port`; the old `createRoom` and its host HUD are removed.
There is no static/command game build fallback or port-owned host loop.

1. Match movement against the original game using seeded input and virtual time.
2. Preserve player identity across join, leave, reconnect and server recovery.
3. Put score changes, collisions, spawns, turns and bot decisions in rules.
4. Use the existing phone controls and camera in the view.
5. Build, run two browsers through a round, and exercise real touch controls.
6. For hundreds of players, choose `players.max` and suitable interest/visual
   settings as described in RULES.md. Dispose of meshes on view exit and recreate
   them on entry. Do not confuse spatial delivery with private information.
