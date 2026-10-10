---
name: parts
description: Studios build on each other with parts from games, apps, music and video that their owners choose to share or sell (a creature, a level generator, a chase camera, a bot brain, a pickup mechanic, an audio pack). Use this when planning or making games, apps, music or video (look for pieces before writing one from scratch), when the person asks what parts exist, says "use the X from that game", "make this reusable" or "share this", and before a game that uses parts goes online.
compatibility: Node 22. Paid purchases need @homie-rocks/studio 0.37.2 or later. A studio made with @homie-rocks/studio; npm installs the packages a part builds on.
---

**Apps:** For a business, venue, cause or customer app, follow the `app` skill: `apps/<id>/app.json`, one morphing screen, roles and parts. Reuse these engines and workflows; do not impose game rounds, scores, bots, a game demo or page navigation. The app check proves shared actions and reconnect; app stores use the same standalone command.


# Studio parts: games, apps, music and video

A studio is the folder with `studio.json`. Studios build on each other with **parts**: reusable pieces of games, apps, music and video that their owners choose to share or sell. A creature from one game, a level from
another, a bot brain from a third. Without parts you would have to come up with everything on your own.

The rules, in full in `node_modules/@homie-rocks/studio/parts/PARTS.md`:

1. Game and app lifting extracts a piece, **never the whole experience**. App components can also be lifted from `apps/<id>/`; music loops or tracks and video may be authored directly in `parts/<id>/`; their licence controls permitted use, including venue use.
2. A part can take **any form** that suits the piece: code, assets, data, a JSON description, a tuned config, a mix.
3. **Private until shared**: on purpose, with a licence (an SPDX identifier) and an attribution. A part records the
   game and studio it came from.
4. **Homie packages are not parts.** `@homie-rocks/*` packages are general mechanisms from npm. A part may say
   which packages it builds on; npm installs them.
5. **The person works in chat** and never types a command. Four tools: `parts_find`, `part_add`, `part_new`,
   `part_share`.
6. **You look for parts first.**

There is no mash-up command: mashing up is making a game with parts from several games.

## 1. Look first

When planning or making a game, app, music or video, for each system it needs (camera, movement, bots, pickups, effects, sound, UI,
environment, characters), before writing it from scratch:

1. Check the `@homie-rocks/*` packages the studio has for the general mechanism.
2. `parts_find` with the words for the piece (`"chase camera"`, `"cave"`, `"pickups"`), and `kind`, `tag`,
   `license` or `builds` (a package or a skeleton it builds on) to narrow it.
3. Tell the person what you found, a line each, **naming the source work and studio each piece is from**, with your pick.

If the catalogue cannot be reached, the tool says so. That is not "nothing exists": say it could not be read, go on
with what the studio has, and look again later. If it answered and nothing fits, write the piece.

Record in the project notes or CODEX, under **Built from**, what came from where: the packages, each part with its game,
studio and licence, and what you wrote from scratch and why.

## 2. Use a part

`part_add` with `"<studio site>/<part id>"` (as `parts_find` gave it; `@1.2.0` for one version) and the `game` option (a game or app id; omit it for standalone media). It
fetches one exact version, checks every file's integrity before anything is written, copies it into the studio
(the studio's to tune from then on), records where it came from, adds the credit to the game, and lets npm install
the packages it builds on. Read what it answers:

- **The import line**: `import … from '@parts/<studio site>/<part id>'`. Its `part.json` says what the piece takes
  (`contract`) and who decides in a room; its `tuning.json` holds the values to tune.
- **Packages**: npm's own words. If a package the studio already names does not fit, nothing was changed: tell the
  person which part wants what.
- **Other parts it names**: each with what adds it.
- **Licences that cannot be combined** are said plainly. Tell the person before building on it.
- **The credit** in the game's `credits.json`: keep it, whatever else changes.

Adding the same part again later brings the newer version: it shows what changed and keeps `tuning.json`. A file
the studio edited is not replaced unless you pass `overwrite`: ask the person first.

Then build, and try it on two devices.

## 3. Make a part

After building a piece another game could use, offer it in one line: "The chase camera turned out reusable. Shall
I make it a part, so your next game can use it? It stays private unless you ask to share it."

`part_new` with `id`, `from` (the game or app) and `files` (the module or folder of that piece). The files are lifted out
into `parts/<id>/`, the game imports them from there, and **the game still builds and plays the same**: build it
and check. A file that reaches into the rest of the game is refused by name: pass what it needs in as an argument
(a collision function, a palette, the room), then lift it. The game's own entry cannot be lifted: a part is never
the whole game.

Then fill `parts/<id>/part.json`: a one-sentence `summary`, tags, what it takes from a game (`contract`), the
packages it builds on (`requires.packages`), its scale and skeleton if it has them, costs only if measured, a small
`preview/index.html` that shows it, and its tunables in `tuning.json`.

When the preview is something to play with, declare its shape in `preview`: `"aspect": "4:3"` and
`"phoneAspect": "3:4"` (whole numbers 1 to 32, no flatter than 3:1, no taller than 1:2). The default is 16:9, which
on a 390 px phone is a frame about 197 px tall: the controls fit and the demo under them is cut off, with no error.

## 4. Share a part, only when the person asks

Ask which licence (`CC-BY-4.0` for "use it, credit me", `CC0-1.0` for "no strings", `MIT` for code) and who to
credit. `part_share` with `share: true`, `license` and `attribution`. It refuses in plain words when there is no
SPDX licence, credit is owed and nobody is named, the part does not say where it came from, or the rights to a
file are unknown (for example a model the studio bought): leave that file out or replace it, never work around it.
`part_share` with no `share` only checks.

It is **live after the studio's next deploy** (`studio_deploy`), not before: say so. Then the studio's site lists
it and the catalogue on homie.rocks shows it if the studio is listed there. `share: false` stops it at the next
deploy. A shared version never changes: a change needs a new `version`, then share again.

## 5. Before a game that uses parts goes online

The deploy plan (`studio_deploy` with `plan: true`) and the listing (`studio_publish`, and its `before: true`)
show each part's licence and attribution and say plainly
when licences cannot be combined: two share-alike licences in one game, a non-commercial part in a studio with a
shop, a no-derivatives part that was edited. Tell the person, and settle it before deploying.

## Never

- Share a part the person did not ask to share, or pick its licence for them.
- Copy a piece from another studio by hand: `part_add` is what checks it and writes the credit.
- Remove or reword a credit a part wrote.
- Treat a package as a part, or a whole game as one.

## Paid parts: use the person's wallet

Needs studio **0.36.0** or later. Read the full settings and recovery procedure in
`node_modules/@homie-rocks/studio/parts/PARTS.md`.

Show the exact quote, currency, quantity, recurring interval, licence, refund and update
terms from `part_add`. Ask first. Spending authority means the person's yes to this price in this conversation,
or a standing instruction that names a spending limit and covers these terms. A quote for a new release must show its new price. Never approve a
hash beside an earlier purchase's price.

Use the person's installed open wallet client: `HOMIE_PARTS_WALLET=link-cli` or `purl`. `part_add` invokes it after exact-quote approval. Money goes directly to the
selling studio's Stripe account. Wallet authority and limits belong to that wallet;
never create another spending mechanism or disable its controls. Link currently requires
the person to approve each card spend in their wallet app. Give them the returned wallet
approval link, then retry `part_add` after approval. This is not a seller checkout page.

Checkout is the fallback when there is no compatible wallet, for recurring purchases,
and where the protocol cannot quote the final total. On this fallback the person must
accept the licence and operate Pay themselves. Never submit licence acceptance through
a browser tool. A base price before tax is not Stripe's final total.

Keep private purchase records and verified backups private. Never give a catalogue the
claim or download token. A proof is evidence, not a download credential. First delivery
and updates depend on the seller; an existing verified backup restores offline.

Use `parts refund` only when requested. Never pass `--receipt-verified` on the assistant's
own word: the seller must confirm matching the Stripe receipt and payer to the order.
Never approve an unknown buyer's test order. Test downloads require owner approval of
the exact claim, and do not become paid licences when the shop goes live.


Machine purchases use the seller's Stripe account. Only studios with paid releases need the
additional payment permissions. Connect and scheduled readiness use read-only provider calls;
readiness does not prove a funded settlement. Tempo is disabled; the offered methods are card
shared payment tokens and Base, subject to the seller's configuration and Stripe eligibility.
Respect the wallet owner's limits, including x402's default payment cap. A decline can use a
fresh approved token or the hosted fallback. An uncertain outcome must be reconciled first.

The office lists unresolved orders and their provider identifiers. Use Reconcile payments now;
a five-minute scheduled job also reads existing payments. After 23 hours it stops replaying
charges but continues reading. If paid files cannot be restored, the owner must refund manually.
For an unrecorded Base payment, send the exact refund from the seller address to the original
payer after the purchase, then record its hash with `shop refund <order> --manual-transaction
<hash>`. The chain must confirm the sender, recipient, amount and time before access ends.


For app, music and video parts, use `part_new` without `from`, choose any suitable kind label, put the licensed files in its folder, and supply the source as `{kind, id, studio}` in `from`. Preserve existing game manifests and imports. Hash and share through the usual tools. No new app build framework is implied.

Selling defaults to the keyless shop: `shop connect` uses the official Stripe CLI approval, creates Payment Links and the webhook, and installs the signing key privately. One approval if needed, zero for an already connected profile. Machine MPP/SPT and MCP charges and the Stripe-recorded x402 path need the fuller Worker credential. Read the payment-path table in PARTS.md before setup. With browser access, operate Stripe's key page for the owner, let them complete only provider verification prompts, click Copy, and run `shop connect --from-clipboard`. Never ask the owner to find or paste a key when this alternative is available. The command reads and clears the clipboard privately. Do not print its contents. No real-account verification is claimed by the release's stand-in tests.
