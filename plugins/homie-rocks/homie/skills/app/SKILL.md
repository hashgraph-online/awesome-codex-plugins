---
name: app
description: "Make or change a Homie app: one morphing screen, roles and reusable parts, live across phones, wall screens, kiosks and staff tablets. Use for customer apps, venue screens, queues, workshop boards and cause dashboards in a studio with studio.json. Apps use the same engines, rooms, parts and standalone builds as games, without compulsory rounds, scores, bots or players."
compatibility: Node 22 and Chrome; the studio's pinned toolkit and Wrangler.
---

# Make an app

For place-based builds, read [the six-build patterns](../app/PLACES.md): owner words to needs, records as objects, a local scene and ambience, one trusted operation for screens and AI, graceful graphics, and adversarial proof. Apply the same authority and honest-evidence rules to game economies and tickets.


For the installed version’s payment, records and local-check contracts, start with
`node_modules/@homie-rocks/studio/apps/APPS.md`. Its “Real Stripe test checkout on
this computer” section is the supported offline-hosting path: real Stripe test
checkout, CLI webhook forwarding, root `.dev.vars`, Wi-Fi return pages and named
checkout popups. Use an existing approved sandbox profile; no deploy is needed.

An app is **one screen, its roles, and its parts**. The screen transforms with the person and the work: a camera moves, a ticket unfolds, controls appear in context. Do not build page-to-page navigation, a sidebar of links, or a conventional admin website inside it. A studio's public website can still have pages around the app.

Read the person's brief and existing `apps/<id>/` first. Choose sensible engineering defaults from the brief; never ask the person how to implement shared state. A business or cause needs no game demo, mandatory entertainment, invented customers, scores or rounds. Never impose a shop, directory listing, sign-in for public visitors, or paid media. Make the fewest human steps possible; run commands yourself.

## The person's dream is the brief

Before scaffolding the app, read the shared `plan` skill. Run `codex new <id> --kind app --name "<Name>"` and fill `apps/<id>/CODEX.md` from their request. This is the same Codex mechanism as games, with the sections an app needs. Draw its page with `codex <id>`. Keep it open as the person's way to steer the work. A request to decide and continue authorizes you to make sensible decisions; do not wait for approval of a plan they did not ask to approve.

Capture these before implementation:

- **Their words:** quote the request, including its scene and emotional intent. Do not replace “my skis moving through the workshop” with “a kanban dashboard.”
- **Scene:** describe walking into the place. What occupies the wall? What moves, arrives, fills or lights up? What can someone understand from across the room? What feels different about this place?
- **People and surfaces:** owner, staff, customer, visitor, volunteer or donor as appropriate. For each: what they need to accomplish and where. Include the person who arrives with no account and the person returning to their own work.
- **Offers:** names, prices, currency, once/monthly, what is included, and what purchase or gift pays for. Preserve “from” prices; a base repair estimate is not a fixed final charge. Record assumptions plainly.
- **Needs:** short statements that can be shown true or false on every screen the owner names. Give each a stable ID. A request to book, follow, give monthly or log a send is a separate need. The app existing is not a need.

The AI chooses records, room structure, packages, camera, interaction, animation and build strategy. Never interview a nontechnical owner about hosting, databases, engines or synchronization. Ask only for indispensable real-world information; continue independent work. If a request names their *actual* place and there is no layout/photo, build an editable, clearly labelled provisional layout and report that exact need as partly met until it is supplied. Never invent a real floor plan and call it actual.

## Turn the work into a living scene

A starter is plumbing: role permissions, records, room connection and a real check action. Nobody is commissioning the starter. Choose the closest plumbing, install its reported dependencies, then replace its scene and workflow with the Codex. A starter painted in brand colours is not completion.

Design a spatial or pictorial model of the business process. Make the things the owner cares about the largest objects, not equal-sized cards with labels. A service has physical objects, locations and transitions; a cause has a visible shared outcome; a venue has an actual place and people doing things there. Stages belong in the scene as destinations, work areas or changes to the objects. They are not automatically columns. Compose the wall first in a sketch, then implement a useful phone view of the same world.

For example, a workshop may have recognisable skis and snowboards riding a rail between a wax bench, an edge station and a repair press. Wax can shine, repair marks can disappear, and completed gear can settle into a collection rack. A kitchen may lay places at a long communal table as verified gifts fund meals; an unconfirmed pledge must look distinct. A climbing wall may carry routes in their real positions; completion switches their lighting, while a climber's send briefly traces that route. These are examples of translating verbs into pictures, not new templates to copy.

Use scene geometry, illustration or layered SVG when it serves the request; 3D is available, not compulsory. A beautifully composed 2D place can work. A flat board of boxes with counters does not satisfy a request for things moving through a place. Avoid generic dashboards, stock admin layouts and navigation as the primary experience. Native controls, readable text and clear labels remain essential.

Before writing scene components:

1. Run `style init <id> --prompt "<the person's own scene words>"`. Record the direction in the Codex: composition, camera, materials, colour, typography and motion. Use the same style machinery as games, not the starter's default theme.
2. Inspect the installed `@homie-rocks/*` packages for mechanisms. `geom`, `props`, `render`, `camera`, `postfx` and `fx` can make the place; `input`, `ui`, `ui-world`, `device`, `audio` and `loop` make it usable. Read the package exports and examples rather than guessing imports. Install every dependency reported by the starter or parts before building.
3. Search the local toolkit MCP `parts_find` for each meaningful piece (the hosted connector may not expose it); shell equivalent: `homie-studio parts find "<piece>"`. Read its contract, source studio and licence. Add fitting pieces with `part_add` / `parts add`; write the missing parts yourself. The example studios share real app pieces: search for venue, workshop, giving, arrivals, scene, queue and sound, not just game characters. If local example studios are available, read their shared `parts/` and manifests without modifying the source studios. A failed catalogue request is not proof that nothing exists.
4. Use the art/models/sound/music skills with connected providers and an authorized budget. Generate distinctive assets when useful. If no provider is connected, continue with original geometry, locally drawn SVG, CC0 assets and local synthesized sound. Report the means honestly. Provider absence never justifies replacing the scene with a board.
5. Record packages, parts with attribution, original work and media routes under **Built from**. Keep costs and provenance visible.

Make a small vertical slice before dressing every corner: a customer performs one real action; its durable record appears as a recognisable object in the wall scene; staff can advance it; the customer's own view updates. Then complete the remaining needs. If an engine import, type check or function build fails, repair the dependency or source error. Do not remove the designed scene, permissions or durable workflow to make a build pass. Diagnose the reported error, read the package contract, and build again.

## Records are the scene's truth

Write a mapping from each durable entity to its visual representation. Use a stable record ID as the object key. Its stage, progress, position, amount or completion time drives the picture; an animation interpolates from the last confirmed state to the next. Reloading reconstructs the same scene from records. A customer action shows a pending acknowledgement immediately, then confirmed state or an actionable failure. Do not animate a successful booking, paid gift or staff transition before it is confirmed.

Choose a coherent transition vocabulary for that place. An arrival enters the scene, stage changes move an object, completion changes material/light, and removal retires it. Use elapsed time for local easing, not frame-count increments. A late subscriber goes directly to current truth rather than replaying every historical event. Prevent a reconnect from duplicating objects or counting the same gift twice. Reduced motion preserves the information with a quiet state change.

Separate records by who may read them. Public wall records contain safe display information and stable IDs. Contact details, private booking notes and staff-only operations belong in protected collections. UI filtering is not access control. Never put a customer email or private token on the wall. Read `apps/APPS.md` for collection permissions and versioned updates. Do not weaken permissions to make a local staff demo easy.

Keep scene state derived from the records service. Rooms may relay transient effects and live presence, but a room emptying must not erase bookings, gifts, routes or shifts. On a version conflict, reload the record and show the current state; do not silently overwrite another staff member. Validate allowed transitions and meaningful inputs. No invented capacity guarantee: a booking request is a request unless an implemented reservation system confirms capacity.

## Let each person find their own thing

On submission, give the customer a stable receipt or tracking URL for the exact created record. Use `randomId`, `appLink` and `qrSvg` from the links package. Keep the link on the success screen, with an explicit copy/save action and meaningful short reference. Persist their own reference locally so reloads return to it; also allow entering a reference or opening the saved link. Another phone using that link should follow the same public-safe item. Never make the customer search a wall full of other people's work to discover whether their booking succeeded.

A public tracking ID identifies a public-safe record; it is not an authorization secret. Private customer information needs authenticated access. Use clean public URLs, never staff links. Test returning later, unknown reference, an empty workshop, a failed submission and a reconnect. Clearly distinguish pending payment, paid, in progress and ready to collect where those states matter.

Design each surface intentionally:

| Surface | The job of the scene and controls |
| --- | --- |
| Wall | Legible across the room; the whole place and its changing work; little prose; no personal data; no dependence on hovering or tapping; a clear QR to the public phone action. |
| Phone | A close view of *my* booking, gift, route or shift; one obvious next action, native fields, receipt and return link; responsive portrait and landscape. |
| Staff tablet | Operational controls at the thing being worked on, current record/version, failure and conflict recovery; authenticated privilege. |
| Kiosk | Large touch targets, public actions, a clear finish/reset, no previous person's private details left behind. |

These can share a renderer and records while changing framing and controls. Do not shrink the wall to a phone or show staff controls to customers. Test touch, keyboard focus, text contrast, 44 px targets and reduced motion. A QR is only useful if its address is reachable from the phone: use the printed LAN address for a physical phone. Capture at actual viewport sizes in Chrome, not resized desktop screenshots.

## Acceptance belongs to the owner

The Codex's `needs` fenced block is a JSON array, one entry per need from the request. It is the check's source, not a second parallel list in app.json. Example (replace selectors and actions with this app's actual workflow):

```needs
[
  {
    "id": "track-gear",
    "statement": "Customers book a tune from their phone and watch their own gear on the workshop wall and their phone.",
    "steps": [
      {"surface":"phone", "selector":"#gear-name", "fill":"Blue board"},
      {"surface":"phone", "selector":"#book-tune", "click":true}
    ],
    "assertions": [
      {"surface":"phone", "selector":"#my-ticket", "text":"Blue board"},
      {"surface":"wall", "selector":"[data-gear]", "text":"Blue board"}
    ]
  }
]
```

Steps support `fill`, `select`, `click: true` and `reload: true`; surfaces are `wall`, `phone`, `phone-two`, `tablet`, `kiosk` and `staff` (a tablet viewport). Set a need’s `role` to the declared role to prove. Each assertion names its surface; only the named screens are required. Assertions use a visible selector with optional contained text, or an observed effect. An honestly unavailable capability remains in the block with no assertions and a plain explanation in the prose; check reports it pending (a placeholder, not a failure or proof). Do not delete, weaken or replace a need to get green. Static needs such as accurate prices may have no action steps. Use semantic attributes on real visible scene elements for testability, never hidden QA-only counters.

Run build and the shared-action check, then the needs step runs on those real browsers. Save captures with `--shots .checks`. The result contains each statement, met/partly/not/pending, the assertion result and available captures of named surfaces; `.studio/checks/<id>-needs.json` drives the Codex's Needs status. Redraw `codex <id>` after checking. Passing a selector assertion is evidence, not a visual judgement: read every capture and perform the full flows as owner and customer using the playtest skill. If the picture fails the words, it is not done even with green assertions.

For staff flows, sign in through the existing local owner link and prove the transition in real Chrome. Keep evidence in the Codex alongside the automated flows. Confirm unauthorized writes are refused and records remain after all screens close. Never call an untested privileged path passed. Before final handover, show the need table with evidence and explicit remaining gaps. If the starter or a board of boxes is still visible, return to the scene design and build it.

## Tie payment to the work

Create the booking, gift intention or ticket first and pass its ID as the application's reference:

```ts
await shop.buy('full-tune', 1, undefined, { reference: booking.id });
// Or a cart:
await shop.checkout({ reference: booking.id });
```

On the default keyless connection, `shop.checkout({ reference: 'table-7' })` opens the studio's synced Stripe menu: the guest sets quantities on Stripe's page and `order.paid.data.lines` carries what was actually paid. A slot with capacity uses `shop.book` (see below), not `shop.buy`. Monthly gifts and memberships are recurring items on their own links. None of these needs a key.

These retain their existing boolean result: true means checkout opened, not payment received. The durable `order.paid` function event includes `data.order` (the order ID), `data.reference` (your reference or null), and `data.app` (the app ID). A verified provider payment emits it. Validate the referenced record, expected amount/currency and app, deduplicate by event/order ID, then fulfil that booking or add that gift to the confirmed meal table. A buyer supplies the reference: it is correlation, never proof they own a private record or paid the expected price. Do not put personal data in it.

For each offer, build the promised action and fulfilment, not just a price label: a naming purchase needs the proposed name and the staff/customer outcome; a ticket needs its receipt. Keep an unpaid request distinct when charging is unavailable.

When selling or giving is a stated need, implement and locally exercise the reference-to-record `order.paid` handler before calling payment provider-blocked. A disconnected provider blocks charging; it is not a reason to omit fulfilment code. Use `function fire` with an explicitly simulated event and a separate test record, confirm the right record changes once, and keep test money out of real totals.

Without Stripe, keep real services and prices visible and say payment is not connected; allow a clearly labelled unpaid request/intention if useful. Never mark it paid or add it to the paid total. Test event handlers locally with explicit test events, labelled as simulations. Report actual charging and recurring collection as not yet met until connected and verified. Do not build a new payment sandbox or pretend recurring intentions are subscriptions.

## Start and compose

- Run `homie-studio app new <id> --from <starter> --name "<Name>"`, or `app_make`. Starters: `welcome` (queue), `gathering` (check-in/task choice), `giving` (goal and giving intentions linked to the shop), `quiz` (casual quiz night), `jobs` (service booking requests). The welcome starter is one 3D scene with customer, wall and staff roles. Install its reported `needsAdded`, then build.
- `apps/<id>/app.json` describes roles (`signIn`, `can`), surfaces (`phone`, `wall`, `kiosk`, `tablet`), wording, record collections, parts and the real UI action used by check. The app's entry and assets live beside it, just like a game.
- Before inventing each component, inspect engine packages for the mechanism and `parts_find` for the piece. A queue, quiz, menu board, live total, music loop or video intro can be a part. Record its licence and credit. Sharing happens only when requested; selling parts is not part of this workflow.
- Use the same engine packages as a game: `@homie-rocks/geom` and `props` for original scenery; `render`, `camera`, `postfx`, `fx` for light, composition and motion; `input`, `ui`, `ui-world`, `audio`, `device`, `loop` for interaction and feel. An app can be fully 3D and wild. Legibility and the actual task come first.
- Use the `style`, `art`, `models`, `animate`, `sound`, `music`, `video` and `perf` skills where they help. Give the organisation a coherent scene with readable controls and purposeful motion. Media cost and licensing decisions remain the person's.
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

Do not add rules or a placeholder map to an app that only needs the records service and local UI. Omit `room` and use the records bridge. Its shell loads one frame and reports readiness after loading; it needs no simulated participants.
The welcome starter demonstrates authorized records plus a server-rules scene with
stationary participants, change effects and a shared revision. Existing apps keep working. Use the manual extraction steps in [REWRITE.md](../game/REWRITE.md)
for existing live state, adapting game-only tests to the app's workflow.

Transport host/replica/screen roles are not staff permission. Never trust a role
parameter or hidden button to authorize an operational change. Rules snapshots
are public, rooms have at most 32 seats, and end after the last person leaves;
they are neither private business storage nor an authorization service.

Use `createAppRecords` from `@homie-rocks/studio/apps` for lasting records. Declare each collection's fields and every role's read/create/update/delete capabilities. The Worker validates writes and checks the signed-in account on every privileged request. Updates use a version; reload and resolve a conflict instead of overwriting somebody else's edit. A room may empty without deleting these records. Transient effects and camera state remain in netplay.

Public collections reach everyone allowed to read them. A ticket number or filtering the HUD is not privacy. Keep personal/private records in a different collection whose read permission excludes customers and walls. Do not put contact details in the starter's public queue.

`homie-studio app role <id> staff --player <account-id> --url <site>` grants an existing signed-in account and returns its private role address. Without `--player` it returns the owner's role address. The existing owner check protects issuance; the link alone grants nothing. `--revoke` removes a named account's grant. `--list` lists links, `--revoke-link` deletes one, and `--expires 7d` (or a unix millisecond time) sets an expiry within 366 days. A signed-in studio owner opens their own private roles without a link. Staff use the studio's existing account/passkey sign-in. Keep these links private.

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

## Public pages and giving

Scaffold businesses with `new <folder> --kind business`; causes with `--kind cause` (MCP `studio_scaffold` uses `kind`). The header links custom `site/pages/<slug>/index.html` pages and an existing Shop. A page at `site/pages/<app-id>/index.html` takes over only the landing: use `/<id>/open` for phones and `/<id>/tv` for the wall. Build says when this happens. In-app links to public pages should use `target="_blank" rel="noopener"` because the app is sandboxed. App assets and hero files belong under `apps/<id>/`, including `apps/<id>/hero/`.

For giving, set the studio currency and run `shop init --giving --currency CAD` (use the organisation’s currency). It creates one-time/monthly suggested gifts. The owner supplies `giving.receiptText` in shop.json; Homie supplies no legal or tax text. Before Stripe is connected, local /shop/ previews items and prices with checkout disabled. Run the connection step yourself; the owner approves their Stripe account in the browser.

Use `shop.book` and the booking collection declaration in SHOP.md. Default keyless booking links show pending while paying; an unpaid guest does not block others. Stripe limits completed sessions to capacity. The owner’s AI syncs published/changed slots with `stripe_shop_plan` and the complete slot manifest. Say “Pay to secure your seat.” Exclusive unpaid holds require the explicitly selected optional keyed connection.


## Tell my AI when a booking comes in

Read `node_modules/@homie-rocks/studio/functions/FUNCTIONS.md` for the worked
booking example and delivery expectations. Opt in with
`mcp.events.bookings: {event:"record.changed", app:"cafe", collection:"bookings", audience:"owner"}`
in `studio.json` (use the studio's real app and collection), then build. The owner's
AI connects to the studio's `/mcp` with explicit OAuth browser approval, calls
`resources/subscribe` for `studio://events/bookings`, and holds the authenticated
Streamable HTTP SSE GET. Notifications use `notifications/resources/updated`;
`params._meta["studio/event"]` carries untrusted event data. Filter booking inserts,
deduplicate by event ID, and resume with `Last-Event-ID`. No polling or Homie relay.
Nothing is enabled by default; a declared feed retains its events without a Homie
count or retention cap.

For an AI that cannot hold a stream, use the signed webhook worked example in
`functions/FUNCTIONS.md`. Run `homie-studio events webhook add bookings <https-url>`
(or local MCP `studio_events_webhook` with `action:"add",feed:"bookings",url`).
It provisions the Worker signing secret and reveals it once for the receiver;
never put it in source or job logs. Build, commit and deploy the declaration through
the usual authorized workflow. `events webhook test bookings` sends a synthetic
signed event; `events webhook status bookings` shows attempts and safe errors via
owner OAuth. Remote MCP provides `studio_events_webhook_test` and
`studio_events_webhook_status`. Use local `rotate`/`remove` for key lifecycle.
The receiver verifies with a Standard Webhooks library and deduplicates IDs.
Delivery retries durably with backoff and rechecks the feed's audience. The owner's
AI then uses the services' own email/SMS or Stripe tools; Homie builds no messaging.

Use owner tool `app_role` to grant/revoke staff by verified email or exact sign-in
name (`signIn`, `app`, `role`, `revoke`); the person signs in first. Staff event
feeds need the explicit app/role audience and collection read permission. Grants
are checked again for live delivery and replay. `app_records` supports deletion
with `operation:"delete"` and the current `version` where the role allows it.
Reload on the returned conflict message. An office owner session and an
owner-marked player account both authorize owner MCP access.

## Local acceptance and operations

`check` uses fresh isolated records by default and prints that choice. Run `dev`,
then check its **localhost** URL with the studio root available. All screens in a
run share its isolated records; later runs start empty. `--no-isolate` explicitly
uses existing records (including when checking a live URL). Do not assume existing
bookings are fixtures: create the needed records through the flow. The baseline
`app.json check` action is optional when the Codex contains executable needs.

`dev` creates a private local test credential. The checker signs each screen into
the role the need names without a passkey ceremony, and still enforces that role’s
record capabilities. This credential only works on loopback with the dev-only
Worker binding; production account sign-in is unchanged. Use `app role <id> staff
--player <account> --studio` for a studio-wide grant; omit `--studio` for one app.
Staff links printed locally use localhost. A grant can be revoked at either scope.

Example: `{"id":"fit","statement":"My crew fits boards from a tablet","role":"staff",
"steps":[{"surface":"tablet","selector":"[data-fit]","click":true}],
"assertions":[{"surface":"tablet","selector":"[data-state]","text":"Fitted"},
{"surface":"tablet","effect":"sound","name":"audio"}]}`.

Nonvisual assertions observe actual platform calls: `sound` (`audio` for Web Audio
source starts, including the audio package, or `media` for media play), `haptic`
(`vibrate`), and `notification` (the notification title). Omit `name` to accept any
request of that type. An app-specific adapter may emit `homie-effect` with
`{effect,name}` at its real trigger. These prove requests, not that an OS delivered
a notification or a person heard audio. Observations reset before each need.

After reloads and rebuilt frames, check waits for online state, completed arrival,
a hidden loading cover and two frames before assertions/captures. Timeout evidence
names the surface and selector/effect it awaited. Dialogs are automatically accepted
and reported. Read retries recover detached frames. Click/fill/select retry detached elements by
re-querying for up to ten seconds; other dispatched action failures are not replayed. `dev` rebuilds root HTML, CSS and JS as well as source and map
changes. Unavailable sandbox Web Storage uses frame-local memory; use app records
or `net.prefs` for persistence across reloads.

Record fields start with a lowercase letter and use lowercase letters, digits and
underscore. Record IDs use 1–64 letters, digits, underscores or hyphens. `app_schema`
and the `app_records` tool schema explain the contract; validation errors name it.

Live and local unconnected shop/giving pages display the declared items and amounts
with disabled payment controls. They say they are not taking payments yet. A fresh
`/shop/` has an empty preview; an authored shop page still takes precedence.

The giving starter now reads the actual shop donation options with `shop.catalog()`.
`shop init --giving --currency CAD` includes $20 monthly; `app new giving --from giving`
opens Checkout for the selected amount and frequency. A disconnected shop displays
a disabled preview. No intention record or unverified collected total is created.
Use the Manage my gifts link for the buyer-owned Stripe portal in the shop.

For a records-only booking app, use `createShop({target: parent})` inside its
sandboxed view. The shell includes the authenticated shop bridge; do not add a
room simulation merely to make a payment button work.

## Frames and upgrades (0.51.1)

App frames permit Web Share and downloads, while keeping their opaque-origin
sandbox. Share still requires the guest’s click and browser support; offer a download
or copy link too. Both the iframe permissions and the served frame’s CSP matter.
Use `.hero-media` for a decorative iframe in a site hero: it lets scroll gestures
reach the page. An intentionally interactive hero frame opts in with `data-interactive`.
App shells allow normal touch scrolling and selection.

Upgrade compares copied app presets with recorded toolkit versions. Unchanged
preset files and default values take the new version; custom scene files, names and
edited labels remain the studio’s. An app wall uses its join label rather than game
instructions. Rebuild after upgrade and inspect both the wall and giving page.

## Experimental MCP Events

For an owner's AI that should hear a studio's declared events, read
`node_modules/@homie-rocks/studio/docs/mcp-events.md`. Connect the client to
`<site>/mcp/auth` through the person's existing studio approval, discover feeds
with `events/list`, and use `events/poll`, an SSE `events/stream`, or
`events/subscribe` with a client-generated `whsec_` secret and an exact
owner-declared `mcp.events.<feed>.receivers` URL. Refresh before `refreshBefore`,
persist cursors, verify Standard Webhooks signatures, deduplicate event IDs, and
use `events/unsubscribe` to stop a webhook. The feeds keep their current roles;
resources/subscribe and the cursor tool still work. This follows the experimental
Triggers & Events working-group draft, with the Workers DNS-pinning limitation
and receiver allowlist explained in that guide. Inspect Functions in the office
and refresh's `deliveryStatus` for failed deliveries; never put secrets in logs.

For production failures, the owner's AI can also use the person's existing
Cloudflare connection to `https://mcp.cloudflare.com/mcp`, discover
`cloudflare.alert.workers_observability_real_time_issue` with `events/list`, and
subscribe with `events/subscribe` scoped to the studio's Worker. Enable Workers
Issues and grant Notifications Write and Workers Observability Write. Cloudflare
posts signed events to the client's webhook so new or recurring reliability
problems reach the AI without polling; Homie hosts nothing for this. See
[Cloudflare's announcement](https://developers.cloudflare.com/changelog/post/2026-10-13-cloudflare-mcp-events/).

## Every need has a check

Read [NEEDS.md](NEEDS.md) for the complete executable format and examples for UI,
customer/staff MCP tools, owner event feeds and MCP Events, webhook delivery,
simulated scheduled functions, records/results and handover files. Keep existing
UI steps. Headless steps use an explicit named role and the local dev credential;
assertions check actual returned values and effects. Missing capabilities stay
not met with their reason. Passing assertions are met even without captures;
missing evidence names each surface, its error and the `--shots .checks` remedy.

Keep interactive DOM nodes connected across delayed refreshes. Update a button's
text and attributes in place; never replace a button under a press. The short
example in NEEDS.md preserves its click listener and focus. A stale-element retry
helps a replaced handle before dispatch; it cannot recover a silently cancelled
press. Assert the resulting navigation as well as the button's presence.


## Selling and operational checks over MCP

Use Stripe's official plugin and the shop skill's batched `stripe_shop_plan` flow.
Retain write responses, verify, then deploy the compact public links. Until the
private `stripe_webhook` step completes, checkout names that one remaining step.
The AI starts the tool; the owner approves Stripe CLI once if needed. No secrets
or API keys pass through chat. Deploy distinguishes **claimed, not listed** from
an actual directory listing; publishing is a separate action.

On the existing signed-in studio connector (`<site>/mcp/auth`), call
`studio_function_runs` with optional `name`, `errors`, `before` for actual attempts,
redacted errors and next due times. Owners and studio-wide `staff` grants can read
this operational history; per-app staff grants do not expose other apps' runs.
Do not start `functions runs --url` in a headless shell with no CLI OAuth session:
that is a different client and would need its own initial browser approval.

`app_records` without `role` selects the highest available declared role: signed-in
roles first, then the largest permission set, with role name as a stable tie-break.
Each response reports `role`; an explicit role stays explicit. Inspect `app_schema`
and pass a role when deliberately testing the customer experience.

`check --shots` may capture outside the studio, but persistent needs evidence copies
those pictures into `.studio/checks` and stores studio-relative paths. Keep that
folder with the Codex evidence. Deploy can render it without outside-path warnings.

### Places: capacity, TV space and failed graphics

Authoritative bookings/inventory are server-side `defineTool` actions with strict schemas and atomic versioned writes, never a client-writable generic ledger. Use [the capacity example](examples/reserve.mjs): seed one place through an owner action; six simultaneous reservation requests must yield exactly one winner. Derive identity from the caller; expose neither inventory totals nor the authoritative namespace as client mutations.

Initialise text controls and navigation before 3D rendering. Catch renderer creation failures inside the scene section; keep fallback text in normal flow, never over navigation. Add a navigation need and run `homie-studio check <id> --webgl-failure --shots .checks/no-webgl` to prove the controls work without WebGL.

On TV, reserve `--homie-join-inset-bottom/right` (or the configured corner's top/left) plus a gap; `body.homie-join-visible` and `--homie-join-x/y/width/height` describe the shell card in the app frame too. See `node_modules/@homie-rocks/studio/docs/toolkit-place-patterns.md` for layout and text-first examples, connector setup and diagnostics.

For studio-owned HTTP routes, read
`node_modules/@homie-rocks/studio/docs/custom-routes.md`. Register with `useRoutes`
and use `/api/custom/*` (game/app IDs cannot claim `api`). App handoff cookies are
scoped to `/<app>/` and do not reach `/custom-api/...`; use built-in app record
endpoints or app tools for role-authorized mutations. Use direct `/api/` endpoints
for function `self` calls, which use `redirect:'error'`.
