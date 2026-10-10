---
name: app
description: "Make or change a Homie app: one morphing screen, roles and reusable parts, live across phones, wall screens, kiosks and staff tablets. Use for customer apps, venue screens, queues, workshop boards and cause dashboards in a studio with studio.json. Apps use the same engines, rooms, parts and standalone builds as games, without compulsory rounds, scores, bots or players."
compatibility: Node 22 and Chrome; the studio's pinned toolkit and Wrangler.
---

# Make an app

An app is **one screen, its roles, and its parts**. The screen transforms with the person and the work: a camera moves, a ticket unfolds, controls appear in context. Do not build page-to-page navigation, a sidebar of links, or a conventional admin website inside it. A studio's public website can still have pages around the app.

Read the person's brief and existing `apps/<id>/` first. Choose sensible engineering defaults from the brief; never ask the person how to implement shared state. A business or cause needs no game demo, mandatory entertainment, invented customers, scores or rounds. Never impose a shop, directory listing, sign-in for public visitors, or paid media. Make the fewest human steps possible; run commands yourself.

## Start and compose

- Run `homie-studio app new <id> --name "<Name>"`, or `app_make`. The welcome starter is one 3D scene with customer, wall and staff roles. Install its reported `needsAdded`, then build.
- `apps/<id>/app.json` describes roles (`signIn`, `can`), surfaces (`phone`, `wall`, `kiosk`, `tablet`), wording, record collections, parts and the real UI action used by check. The app's entry and assets live beside it, just like a game.
- Before inventing each component, inspect engine packages for the mechanism and `parts_find` for the piece. A queue, quiz, menu board, live total, music loop or video intro can be a part. Record its licence and credit. Sharing happens only when requested; selling parts is not part of this workflow.
- Use the same engine packages as a game: `@homie-rocks/geom` and `props` for original scenery; `render`, `camera`, `postfx`, `fx` for light, composition and motion; `input`, `ui`, `ui-world`, `audio`, `device`, `loop` for interaction and feel. An app can be fully 3D and wild. Legibility and the actual task come first.
- Reach for the `style`, `art`, `models`, `animate`, `sound`, `music`, `video` and `perf` skills where they help. It should look like a game studio made it: a coherent world with a useful HUD, not generic cards and navigation. Media cost and licensing decisions remain the person's.
- Keep native buttons at least 44 px, keyboard focus visible, text as text, motion reducible, and the wall QR clear of useful information. Pointer gesture guards belong on the canvas, not native click buttons.

## Roles and records

For transient shared live state, use the same server rules rooms as games. Read
[the rules reference](../game/RULES.md). Declare `src/rules.ts`, `src/move.ts`, `src/view.ts`, and app.json `room: { host: 'server' }`
with `entry: 'src/view.ts'`. Each interactive visitor has a player entity containing
its cursor/selection; commands validate actions in that entity, then sendRoom to
update shared bounded board/poll/scene state. Walls watch without a seat. Omit bots,
scores and automatic rounds; use `rounds: { seconds: 0, breakSeconds: 0 }`. The current contract requires a body for each participant: use a circle with radius 0.1,
maxSpeed 0 and a no-op defineMove handler for a stationary board or poll. This is a
logical seat anchor, not a visible avatar; never add fake movement to pass a test. Include a small map/main.json with bounds even for stationary seats. Draw through openRoom, and acknowledge a button
locally while waiting for shared outcomes. Keep animations and camera in the view.

Do not add rules to an app that only needs the records service and local UI.
The welcome starter demonstrates authorized records plus a server-rules scene with
stationary participants, change effects and a shared revision. Existing apps keep working. Use the manual extraction steps in [REWRITE.md](../game/REWRITE.md)
for existing live state, adapting game-only tests to the app's workflow.

Transport host/replica/screen roles are not staff permission. Never trust a role
parameter or hidden button to authorize an operational change. Rules snapshots
are public, rooms have at most 32 seats, and end after the last person leaves;
they are neither private business storage nor an authorization service.

Use `createAppRecords` from `@homie-rocks/studio/apps` for lasting records. Declare each collection's fields and every role's read/create/update/delete capabilities. The Worker validates writes and checks the signed-in account on every privileged request. Updates use a version; reload and resolve a conflict instead of overwriting somebody else's edit. A room may empty without deleting these records. Transient effects and camera state remain in netplay.

Public collections reach everyone allowed to read them. A ticket number or filtering the HUD is not privacy. Keep personal/private records in a different collection whose read permission excludes customers and walls. Do not put contact details in the starter's public queue.

`homie-studio app role <id> staff --player <account-id> --url <site>` grants an existing signed-in account and returns its private role address. Without `--player` it returns the owner's role address. The existing owner check protects issuance; the link alone grants nothing. `--revoke` removes a named account's grant. Staff use the studio's existing account/passkey sign-in. Keep these links private.

The complete helper and limits are in `node_modules/@homie-rocks/studio/apps/APPS.md`. Import `appLink`, `qrSvg`, and `randomId` from `@homie-rocks/studio/links` for a ticket URL with parameters. Build customer links from a clean public address, never by copying a staff URL. `randomId` works on plain HTTP.

## Prove and deliver

1. `homie-studio build --types` and `homie-studio dev --lan`. Open the printed Wi-Fi address for phones and the wall. Localhost QR codes cannot reach a phone. Passkeys need HTTPS or localhost; do not bypass staff authorization for HTTP.
2. `homie-studio check <id> --url <origin> --shots .checks`: a wall and two phones connect, a declared real UI action changes all screens, and a reload retains it. In `app.json`, `check.action` is its CSS selector and `check.observe` is a shared text value that changes as a consequence. Use an actual workflow, no fake QA-only action.
3. Also prove the app's own role workflow with staff signed in, unauthorized writes refused, records after all screens close, and layout in phone portrait/landscape, tablet and wall. Use the `playtest` skill for visual and interaction review, adapting game-only criteria to the app's purpose.
4. Customer store builds use the existing `standalone` skill/command with the app id. The same bundle and public records work through the wrapper; its existing account, billing and store-upload limitations still apply. Never promise store approval.
5. Give the person `/<id>/open`, `/<id>/tv`, a real screenshot and the measured proof. Publish only within their authorization through the existing publish workflow. Do not turn a request for an app into an unwanted deployment or directory listing.

## Connect an AI to this studio

Use Studio functions (`functions/FUNCTIONS.md` in the toolkit) for durable reactions to `record.changed`, `order.paid`, refunds, schedules and tool calls. `homie-studio function new <name> --event <type>` creates a plain TypeScript file; local `function fire` and the office delivery table make it testable. Deduplicate external effects by event ID. Public or priced tools can expose app services to customer AIs using the same purchase engine.

Every studio serves its own MCP at `<site>/mcp`. Use the `tools` skill for studio-defined business actions, signed integrations and staff AI access. Reuse office and app-record built-ins first. After an authorized deploy, hand over the MCP address and `<site>/_studio/office/connections`: the person approves with the studio account they already have, with no key to copy. Staff connect their own account and retain only their app grants. Client connector setup is separate from the studio approval. Never deploy merely to set up a local tool test.
