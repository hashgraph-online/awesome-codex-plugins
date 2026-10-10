---
name: publish
description: Put a Homie studio's site and games online on the studio's OWN Cloudflare account (Worker, D1 and public-room Durable Objects, with R2 storage only when added), run its site (the hub's sections in the studio's own look, a landing for every game, news posts with feeds, and what the studio's site/ folder overrides), list them in the homie.rocks directory, and read the studio's own stats (visits, plays, rooms, rounds, players, songs, videos, where people came from). Use when someone asks to deploy, publish, go live, share a studio's games, write a news post or announce a drop, change how the studio's site looks, list games in the Homie directory, or how their studio or a game is doing.
compatibility: Node 22 and the studio's own pinned Wrangler, signed in to the studio's Cloudflare account. Cloudflare's own plugin (cloudflare/skills) and docs MCP are optional helpers.
metadata:
  providers: cloudflare
---

**Apps:** For a business, venue, cause or customer app, follow the `app` skill: `apps/<id>/app.json`, one morphing screen, roles and parts. Reuse these engines and workflows; do not impose game rounds, scores, bots, a game demo or page navigation. The app check proves shared actions and reconnect; app stores use the same standalone command.


# Publish a studio

A studio's site runs on the studio's own Cloudflare account; homie.rocks only lists it.

## Game links on X

When X shows the player card, its phone apps show the game's picture with a play
button that opens the game full screen inside X's in-app browser. On X's website,
third-party games open the posted link in a new tab; post `/<id>/play/embed` to go
straight into a public room there. The same Play code serves both that top-level
player and cross-origin frames. Never promise that X will show or frame a game.

X's archived player-card reference (developer.x.com, "Cards: player card")
documents the phone behavior, but its written policy is for linear audio/video and
explicitly excludes gaming. X's [public web bundle](https://abs.twimg.com/x-web/x-web/assets/article-card-DEH89WAV.js)
observed on 2026-10-08 frames only YouTube, SoundCloud and Periscope hosts; other
hosts get a new-tab link. This is a code observation, not a signed-in test, and
account flags could differ. X decides what it shows and may change it.

The switch defaults on. Set `site.playerCard: false` in studio.json, or
`playerCard: false` in a game's game.json, to switch off. A TV-only game declares
`screen.singleScreen: false`. Tags need HTTPS and a local picture the build has
measured against what X's reference says will render: JPG/PNG/WEBP/GIF, at least
68,600 pixels, under 5 MB. A missing or refused picture produces a build warning
naming the file and the rule, and the page keeps its picture card. Any shape gets
the card (a 1200×630 social picture, a 16:9 still, a square); the player is
advertised as 480×480, Homie's choice from two live game cards; X's website draws
the picture as a small square thumbnail whatever its shape. `site.twitterSite` (an
@handle) adds `twitter:site` and is optional. Starters need a cover. Custom
landing Twitter tags remain the owner's; Open Graph pictures stay unchanged.

Preview at `/<id>/play/preview` during `homie-studio dev`, and directly at
`/<id>/play/embed` on phone and desktop. The preview uses X's observed sandbox,
including web-share and scrolling=no, on a different origin. Guest play works
without storage; opened as its own page a reload keeps the room, seat and name.
Sound waits for a press. The room button reads "Room N · Site" and the first row
of its sheet is the way to the studio's site; in a frame, account, shop, Game and
big-screen links open a tab of their own. Purchases never start in the player.
Blocked popups show an address to copy, and an opaque shell shows why it cannot
connect. `site.playerCardOrigins` replaces the embed-only ancestor list.
See `packages/studio/site/SITE.md`, “Play from a post,” for settings and evidence.

## Cloudflare (checked only when you publish)

1. In the studio folder: `npx wrangler whoami`.
2. Not signed in: run `npx wrangler login`. Tell the person in one line that Cloudflare
   opened in their browser and they approve once (their own account). Wait, then
   `whoami` again. Never ask for, paste or store an API key. Where no browser can open on
   this computer (a remote or cloud session), `npx wrangler login --device` prints a code the
   person approves on any device.
3. Several accounts: use the already named business account; if ambiguous, show account names and ask which business owns the studio. The AI resolves and puts its id in `studio.json`
   (`cloudflare.accountId`).
4. **Cloudflare's own tools**, for Cloudflare questions beyond the studio's deploy (a
   Worker's logs, a limit, what a Wrangler flag does, building on Cloudflare yourself):
   - Current facts come from Cloudflare's docs, not memory: its docs MCP server
     (`https://docs.mcp.cloudflare.com/mcp`, no sign-in) or any developers.cloudflare.com
     page with `/index.md` added for Markdown.
   - Cloudflare's plugin brings its own skills (`wrangler`, `workers-best-practices`,
     `durable-objects` and more) and its API MCP server. Offer it when the person wants that
     help, and they approve the install: in Claude Code `/plugin marketplace add
     cloudflare/skills`, then `/plugin install cloudflare@cloudflare` (it is also in Claude's
     plugin directory as `cloudflare@claude-plugins-official`); in Codex `codex plugin
     marketplace add cloudflare/skills`, then `codex plugin add cloudflare@cloudflare`.
   - **The studio's own Worker, database, storage and secrets change only through `npm run
     deploy` and `homie-studio`**, which record what they create in `studio.json` and never
     touch what they did not create. Never create, change or delete them with Cloudflare's
     MCP (its `execute`, a bindings or connector tool) or a bare `wrangler` command. The Homie
     mod (Claude Code) and Homie's hooks (Codex) hold such a change inside a studio (a
     delete, a secret, a hand rollout, a write to the live database) until the person says
     Proceed.

## A requested custom domain

Run `homie-studio domain <hostname>` (Desktop: `studio_domain`) and then deploy. The AI writes
the exact custom-domain route and Cloudflare creates DNS and TLS using the existing sign-in.
Do not ask for a zone id, DNS record or dashboard setting. Keep workers.dev until a domain is requested.
If the domain is not yet on this account, help connect it at https://dash.cloudflare.com/?to=/:account/domains.
A registrar sign-in, purchase or ownership challenge belongs to the owner; the AI handles the DNS values.

## Deploy

```sh
npm run deploy
npx --no-install homie-studio check <id> --url <the live site it printed>
```

Before the first deploy, tell the person what it creates and what it costs:
`npx --no-install homie-studio deploy --plan` prints it and changes nothing (one Worker,
one D1 database, two SQLite-backed Durable Objects; R2 only when requested).

`deploy` builds every game, creates the Worker and D1 database named in `studio.json`,
applies migrations, deploys, and reads the live site once (the site then claims itself
in the homie.rocks directory; nothing is stored by hand). It never creates R2. It refuses
to use a Worker, database or bucket of the same name that this studio did not create;
then rename it in `studio.json` and `wrangler.jsonc` (an older studio's is
`site/wrangler.jsonc`). Never
delete, rename or redeploy anything the studio did not create. When it answers with a
`needs` step (a new account verifies its email address; an account with no workers.dev
address picks one), say that step to the person and wait. The deploy itself is held for the
person's Proceed, with where it goes and what changed since the last one: by the Homie mod in
Claude Code, and by Homie's hooks in Codex and Grok Build (`studio-setup` says how a hold is answered there).
Where nothing holds it (Codex or Grok Build before the hooks are trusted: the setup status says "Homie's
holds: off"), say what the deploy would do in a sentence and wait for the person's yes.

Storage for songs and videos (`npx --no-install homie-studio storage add`, an R2 bucket) is
separate and optional: Cloudflare asks for a payment method before R2 works, so only
when the person wants it, after saying so (R2 has no egress fees; storage is free up to
10 GB-month, then US$0.015 per GB-month).

## Songs and videos

Published entries of `music/manifest.json` and `videos/manifest.json` become pages at
`/music/<slug>/` and `/videos/<slug>/` with every deploy (the `music` and `video` skills write
them and redeploy). Without storage the site serves each file itself, up to 25 MiB a file. Once
the studio has storage, big media lives in its R2 by default: every deploy moves each public file
over 1 MiB, or left out of git, into R2 (uploaded, read back, checked by SHA-256) before the site
stops carrying it, and serves it at the same address; the file stays in the studio folder.
`npx --no-install homie-studio media move --dry-run` says what would move; `media list` shows what
the site will show, where each file is served from, and why anything is left out. A studio with
songs or videos and no games can still deploy.

**An existing studio** (made before @homie-rocks/studio 0.18.0) moving its media: `upgrade` (it
lists the big media and moves nothing), `npm install`, `media move --dry-run`, `media move`, then
`npm run deploy`, then curl one moved file with a byte range: a 206 with the file's full size in
`content-range`, at the address it always had. Never delete the local files.

## The site

Every deploy builds the studio's site from the studio (`node_modules/@homie-rocks/studio/site/SITE.md` has
all of it): Home, Games, Music, Videos, Rooms and Posts, each only when the studio has something in it (a
section with nothing has no tab and answers 404), and a landing for every game (the `game` skill's "Its
landing page" makes one epic). Every page ends with "Made with Homie"; restyle it, keep it.

- **A news post** ("give my studio a news post", "announce the new game"): write
  `posts/<YYYY-MM-DD>-<slug>.md` (`posts/README.md`): frontmatter `title:`, `summary:` (one line: the
  cards and the feeds), `image:` (a `/path` on the site, like a game's cover), and `game:`, `song:` or
  `video:` to link one of the studio's own; then the body in markdown. Say something real: what is new,
  why it is fun, how to play, what is next. Posts are at `/posts/`, on Home, in `/posts/feed.xml` (Atom)
  and `/posts/feed.json` (JSON Feed), and in the directory's copy of the studio.
- **The look**: `site/theme.json` (colours, fonts, corner radius, a logo in `site/public/`) and
  `site/theme.css` for anything more. `studio.json` `"tagline"` is the studio's line; `"site": { "featured":
  "<game id>" }` picks Home's game.
- **Anything of the studio's own wins**: a whole page in `site/pages/<path>/index.html` (an About page, or a
  hand-made landing at `site/pages/<id>/index.html`), a piece of every page in `site/partials/` (`footer`,
  `header`, `home`, `game`, `game-<id>`, `post`, `head`), files in `site/public/`. `site/README.md` in the
  studio lists them.
- **Search engines and AI agents**: every page carries schema.org JSON-LD (a full VideoGame on each landing,
  the studio's Organization on Home), and the site makes `/robots.txt`, `/sitemap.xml`, `/llms.txt` and
  `/llms-full.txt` from what is public (SITE.md, "Search engines and AI agents"). The studio's links elsewhere
  go in studio.json `"site": { "schema": { "sameAs": [...] } }`; a hand-made page takes `<!-- homie:schema -->`
  in its `<head>`. Ratings, reviews and prices are never added by hand.
- **The play page** shares its room: the room is in the address, and a small button at the edge gives
  Invite, Big screen and the room code. Nothing to set up.
- Before and after a deploy, look: `npx --no-install homie-studio look --url <site>` (the local dev address,
  then the live one) shoots every page on a computer and a phone and names what is wrong.

## List in the directory

Going online never lists a studio. Listing is this separate step, public, and the person's to ask for: do it when
they asked to be listed or said yes to your offer, never as part of a deploy.

Licences first: `publish` refuses to list a studio while a public game ships an asset with no licence record, a
licence that forbids a web game, or a credit it owes but does not show (`npx --no-install homie-studio assets check
<id>` names each one and its fix; the `models` skill has the rules). Fix them, deploy, then publish.

Call the Homie MCP tool `studio_publish` with the live site (or run
`npx --no-install homie-studio publish`). It answers with each listed game's Play link, and
with anything it did not list and why. The directory is in beta: at most 12 games per
studio are listed, names and blurbs are checked (plain text, no links), and its owner can
unlist a listing. Anyone can report a listing; only the directory's owner acts on
reports, never an AI.

The beta also caps how many times a studio may publish in a day. `publish` (and `studio_publish`) says how many are
left when the directory gives the number, and before it sends, how many this computer has sent today; the local
tool's `before: true` says that without publishing. A refusal for the cap is not a broken studio: say when it ends
and stop, never retry in a loop. A deploy that closes or opens a game's source asks the directory to read an
already-listed studio again by itself (that uses one of the day's publishes); it never lists an unlisted one.

## The site's address

`deploy` prints the live address. A `workers.dev` address names the person's Cloudflare
account (often after them), so `deploy` keeps it in `.studio/local.json`, which git ignores:
never copy it into a committed file (README, posts, manifests). When the studio has its own
domain, it goes in `studio.json` as `cloudflare.domain` (e.g. `"night-owls.example"`); deploy
never replaces it, and the directory claim, `publish`, `check` and `stats` use it.

A studio's domain usually shares its Cloudflare zone with other things. **Never touch a route the studio does not
own: not in `wrangler.jsonc`, not with Wrangler, not in the Cloudflare dashboard.** `deploy` keeps the studio's own
routes in `wrangler.jsonc` (its custom domain, an exact-host route) and never changes or removes any other route. On a
custom domain the plan and the deploy read the domain's Worker routes first, and warn when another site's catch-all
(`*/*`) or wildcard covers the studio's hostname: that route answers the hostname before the studio does, and editing
or removing it takes the other site down. Say the warning to the person as it is. The one safe fix is the line it
gives, the studio's own exact-host route (`{ "pattern": "<host>/*", "zone_name": "<domain>" }` in `"routes"`), which
`npx --no-install homie-studio deploy --own-route` (`studio_deploy` with `ownRoute: true`) adds for you once the
person agrees; never a wildcard or a catch-all, which `deploy` refuses because it would take over the zone's other
sites. When it says the routes could not be read, that is unmeasured, not fine: if the domain answers as something
else after the deploy, the same one line is the fix. Only one deploy of a studio runs at a time; each prints which games changed since the last
deploy from this computer with the game's build hash (the one `build` printed, and the one the live site says in
`/.well-known/homie-studio.json` as `games[].build.hash`), so "is my build live" is a comparison of two hashes. "Network preflight failed" means this computer could not look the
site's name up (a browser may still open it): test against the local dev site, and do not report the game as broken.

## Stats (the owner's, and only the owner's)

Every studio counts, in its own Cloudflare D1 database: pages opened, Play presses,
rooms opened, the most people playing at once and right now, rounds finished, songs played,
videos watched, and which site sent each visitor (homie.rocks, another studio, search, the
web, a `?via=` link). It counts and never tracks: no cookie on a visitor, no person
identified, nothing sent anywhere; prefetches, crawlers and house QA are not counted.

- "How is my studio doing?": run `npx --no-install homie-studio stats` (add `--range 30d`,
  or `--game <id>`, `--song <slug>`, `--video <slug>`) and say the numbers plainly.
- To read them through the Homie MCP (for example from an app without the studio folder
  open): `npx --no-install homie-studio stats key` gives a read key that ends in an hour;
  pass it to `studio_stats` { site, key, range }. The key only reads; never paste it
  anywhere else, and `stats revoke` ends every key.
- For the person's own browser: `npx --no-install homie-studio stats link` gives a one-time
  link (30 minutes) to the private page `/_studio/stats`. Give it to the person to open
  themselves; it keeps that browser signed in for 30 days. It is theirs: never post it.
- `npx --no-install homie-studio stats share on` (then `npm run deploy`) lets the directory
  show "played this week" (Play presses and rounds with people, over 7 days). Only when the
  person wants it; it is off by default.
- A studio made before 0.6.0 gets its counters on the next `npm run deploy` (D1 migration
  `0002_studio_stats.sql`); nothing before then was counted.
- Who is playing right now, talking to players, kicking or muting one, an invite-only beta
  or a private game: the `office` skill (`npx --no-install homie-studio office`). An office
  key (`office key`) also reads these stats.

## Tell Homie

After a studio's first publish (its games are listed and playable), or when a deploy or a listing failed in a way
you could not fix, you may offer, once in the session, to send the people who make Homie a short note about it:
`homie_feedback` with `offered: true` and the step (`step: "publish"`). A draft sends nothing; show it exactly as it
would go and send it only after the person says yes (in Claude Code, Claude Code itself asks them with the exact
note; in Codex, Homie's hooks hold the send for their `proceed <code>`). A no is final for the session. No keys, logs, files, code, site addresses that name the account, or anyone's
name in it.

## Beta

Homie for studios is in beta. When something breaks, tell the person it can go to
https://github.com/homie-rocks/homie/issues/new/choose (bug, port request or question),
without keys, tokens or private addresses in it. Or, with their yes, send a short note
from here (`homie_feedback`, above).
