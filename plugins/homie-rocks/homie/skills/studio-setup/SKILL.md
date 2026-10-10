---
name: studio-setup
description: "Set up a Homie studio (one repository with games/, apps/, music/, videos/ and posts/, and a site with public game rooms on the studio's own Cloudflare) with the AI handling setup and defaults: setup status first (accounts and tools, what each unlocks, the exact fix), choose editable defaults, plan the requested game or app, build it with progress the person can watch, playtest, put it online and list it in the homie.rocks directory. Use when someone asks to set up, create or start a studio or a game studio, asks what they need or whether they are set up, or says \"set up a game studio called X\" (with or without \"and make a multiplayer game\")."
compatibility: Node 22. Reads, and offers only when a feature needs them, each provider's own tools (Wrangler (Cloudflare, pinned in the studio), the GitHub CLI, the ElevenLabs CLI, a fal key, Ollama for Clef on this computer, and as an option the stripe CLI's Stripe Projects). The plugin's providers.json lists them.
metadata:
  providers: cloudflare github elevenlabs fal stripe ollama
---

**Apps:** For a business, venue, cause or customer app, follow the `app` skill: `apps/<id>/app.json`, one morphing screen, roles and parts. Reuse these engines and workflows; do not impose game rounds, scores, bots, a game demo or page navigation. The app check proves shared actions and reconnect; app stores use the same standalone command.


# Set up a studio

A Homie studio is ONE folder the person can see and open: `AGENTS.md` (+ `CLAUDE.md`
importing it), `games/`, `apps/`, `music/`, `videos/`, `posts/`, and a site: a Cloudflare Worker with a
D1 database and the Table/Lobby Durable Objects that serve the studio's pages and its public
game rooms from the studio's **own** Cloudflare account, on Cloudflare. The
code comes from `@homie-rocks/studio`, pinned in the studio's `package.json`. The person never
types a command: you run everything, and they approve what matters (Cloudflare, once, in their
browser). Homie for studios is in **beta**.

## The new-studio checklist

Carry the request through without waiting between setup, planning, building and checking.
Show brief progress, not a form. Choose the name from the request, otherwise "My Studio".
The demo and small-change lesson below are optional, only for someone who asks for a tutorial.
Plan from the premise with sensible engineering and design defaults; the person changes them later
by asking. A business or non-profit may need an app or site: do not force a game or game interview.
Use phone and computer controls, a small first version, local sound and CC0 art. Build with one agent
unless parallel work was requested. Keep provider approvals, paid budgets and required host holds.
An existing request to go live or list is authorization; do not ask again outside those holds.

**An app first:** For an app request, run `app new <id>` in the empty studio, build the requested roles and shared action, and run its app check. Give the `/<id>/open` link as soon as it passes; continue to the requested publish flow without a game demo or interview. The same keyless shop is optional, with its visible Shop control when something is for sale.

**A Play link first.** Build the game to the point where it plays, run the two-browser `check`, and the moment
it passes tell the person, with the link they can open now (`http://127.0.0.1:8787/<id>/play`, two tabs for two
players): a first run should have someone playing in minutes, not after an hour of polish. Only then go on
to sound, art, the playtest's fixes and the landing page, saying in a line what you are doing next.

## 0. Setup status, first

Before anything is made, and whenever the person asks what they need, whether they are set up, or
is waiting (a usage limit resetting is a good time), run the setup status. It only reads, takes a
few seconds, and never prints a key:

1. With the Homie connector (the Homie MCP tool `studio_scaffold` is in your tool list), call it with the
   studio's name (if they have not named it yet, use "My Studio" for now; it only reads). It returns the
   exact pinned command, like
   `npx -y @homie-rocks/studio@<version> new "<folder>" --name "<Name>" --homie https://homie.rocks`,
   and a numbered list of next steps: this checklist decides the order, not that list. **Without the
   connector, go on** ("Without the connector" below): the toolkit is `@homie-rocks/studio` on npm, and
   `@latest` is its version here.
2. Run that same package with `setup status` instead of `new ...`:
   `npx -y @homie-rocks/studio@<version> setup status --connector yes --json` (inside a studio:
   `npx --no-install homie-studio setup status --connector yes --json`). If it does not know
   `setup status` (a toolkit older than 0.11.0 calls it unknown, or asks for a studio first), run `npx -y @homie-rocks/studio@latest setup status
   --connector yes --json` for the status only (it only reads). `--connector yes` because
   the Homie tools are in your tool list; if `studio_scaffold` is not there, say `--connector no`
   and run it from `@latest`. In Codex add `--client codex`, in Grok Build `--client grok`: the status then
   says whether Homie's holds are on (item 6), and when another MCP server has taken the connector's name.
3. Use the status internally. Report the current work in plain words and only the single next
   action that actually needs the person. You run `fix.run`; a provider sign-in is their browser
   approval. Do not make them understand runtimes, connectors, ids or optional providers.

4. **Never block on an optional row.** Say what it unlocks and that it can wait until that feature is
   wanted; the skill that needs it (`music`, `art`, `video`) offers it then. A "do this now" row you can
   do (`fix.run`, like `npx wrangler login` or `brew install ffmpeg`): run it yourself as part of setup. A row the person does on their own (`fix.open`) can be done any time, even while they wait
   for something else: give them the link. The optional "Clef on this computer" row is a large download:
   say its size first (`ollama pull clef-flash`, about 11 GB) and run it only after their yes.
5. Run it again whenever they say they did something, and tick the row.
6. **Homie's holds (Codex, Grok Build).** With `--client` the status has a `holds` row: whether Homie's
   hooks ran just now in this app (`"on": true`). When it is off, say so in one sentence in this first reply,
   with the row's fix. In Codex: "Homie's holds are off in this session: open `/hooks` and trust Homie's
   three hooks. Until then I'll ask you before a deploy, a Cloudflare change, a paid call or a model
   download." In Grok Build: "Homie's holds are off in this session: install the Homie plugin again with
   `--trust` and start a new session. Until then I'll ask you before a deploy, a Cloudflare change, a paid
   call or a model download." Then
   do ask, every time, also when the app approves commands for you. When it is on, say nothing about it and
   change nothing: the hooks hold what they hold. A status with no `holds` row in Codex or Grok (a toolkit
   before 0.30.2) cannot tell: say the sentence anyway.

**Without the connector, with a shell: go on.** A studio is made, checked, put online and listed with the
studio's own commands; the connector is not needed for any of it. When the Homie tools are not in your tool
list and you can run commands:

- Say it once, in one line: "The Homie connector is not connected in this app, so I'm making the studio with
  its own commands. Connected, it adds the homie.rocks directory search, the cards
  where an app draws them, and notes to Homie."
- The status is `npx -y @homie-rocks/studio@latest setup status --connector no --json`. Its connector row
  says why when it can tell: another MCP server named `homie` is set up in this app and has taken the name
  the plugin's connector uses. Its `fix.run` adds Homie's connector under its own name: run it yourself and never wait for it.
- The studio is `npx -y @homie-rocks/studio@latest new <folder> --name "<Name>"` (step 1), and from then on
  `npx --no-install homie-studio …` inside it.
- Where a step names a Homie MCP tool, run the command the same step names beside it (`game new`,
  `deploy`, `publish`, `stats`). Tell Homie is the connector's `homie_feedback` (in Claude Code also
  `/feedback`): where neither is here, make no offer.

**Stop only when there is neither** the Homie tools nor a way to run a command. Then say exactly how to add
the connector in that app, and stop: Claude Code, `/plugin`, install or enable "homie" (marketplace
`homie-rocks/homie`), and `/mcp` shows it connected; Codex, `codex plugin marketplace add homie-rocks/homie`
then `codex plugin add homie@homie` and a new session; Grok Build, `grok plugin install
homie-rocks/homie#plugins/homie` and a new session; the Claude app, Grok chat or another app with connectors,
a custom connector at `https://homie.rocks/mcp`.

**Each provider's own tools, lazily.** Homie works through each provider's own CLI, plugin or MCP
server (Wrangler for Cloudflare, the GitHub CLI, ElevenLabs' CLI, fal's MCP server), never a copy of
their code: the plugin's `providers.json` lists them, with what stays Homie's (budgets and receipts,
the kids rules, the owner's one-tap asks, secrets never in the chat, the rights notes). Offer one only
when the person wants what it unlocks, in the skill that needs it; you install required tools and they sign in on the provider's own page.

**The status line (Claude Code only).** When requested: `npx --no-install homie-studio statusline --install` (`--remove` takes it away). Claude Code
reads the setting from the folder it was started in: if that is the folder above the studio (you made the
studio as a subfolder), add `--project <that folder>`. It never replaces a status line they already have;
if it says so, leave theirs. Never turn it on unasked. In Claude Code 2.1.287 or later the Homie mod (part
of this plugin) already draws the studio's band above the prompt and the Studio pane (`/studio`), so offer
the status line only to someone who wants the line under the prompt as well.

**Homie's holds in Codex.** In Codex, Homie's hooks hold what the mod holds in Claude Code: an edit to a
file `studio.json` `"protect"` lists, a production deploy, a change to the studio's Cloudflare account
outside its deploy, a paid call past the budget or whose cost cannot be read first, and a Clef model
download; they refuse what the mod refuses, and take secrets out of what you read. Codex runs a plugin's
hooks only after the person trusts them once: after installing Homie, tell them to open `/hooks` and
trust Homie's three (until then nothing is held, so ask before each of those yourself). Never assume they
are on: the setup status says which it is (item 6 above). A held call comes
back refused with a code, and the person sees what it holds: say in a sentence what it would do and ask.
They answer in their own message, `proceed <code>` (that exact call goes through once) or `cancel
<code>`; then run exactly the same call again, or not at all. Never write that answer yourself, in a
command or a file: only the person's own message counts. `node <this plugin's folder>/hooks/codex.mjs check
-- <command>` (the folder above `skills/`) says what Homie would do with a command, and runs nothing.

**Homie's holds in Grok.** In Grok Build, Homie's hooks (`hooks/grok.json`, deciding with the module the mod
and the Codex hooks ask, `hooks/lib/holds.mjs`) hold and refuse the same calls as in Codex, and take secrets out
of what you read. Grok runs a plugin's hooks only once the person has trusted the plugin (`grok plugin install
homie-rocks/homie#plugins/homie --trust`, then a new session; `/hooks` lists them). Never assume they are on:
the setup status with `--client grok` says which it is (item 6 above), and while it says off, before a
production deploy, a Cloudflare change outside that deploy, a paid call, a model download or an edit to a file
`studio.json` `"protect"` lists, say what it would do in one sentence and wait for the person's yes, also when
Grok approves commands by itself; and never repeat a key or a token you read. A held call comes back denied
with a code, and the person answers `proceed <code>` or `cancel <code>` in their own message, as in Codex; then
run exactly the same call again, or not at all. Never write that answer yourself. In Grok chat (the connector
only, no plugin) there are no hooks: ask, every time. `node <this plugin's folder>/hooks/grok.mjs check --
<command>` says what Homie would hold, and runs nothing.

## Grok and Grok Bot

In Grok Build the Homie plugin brings the connector (its tools read `homie__studio_scaffold` and the like);
its hooks hold once the plugin is trusted (above). Say `--client grok` to the setup status. In Grok chat the connector is
`https://homie.rocks/mcp`, once the person has added it. Use the one that is here; with neither, and a shell,
go on without it (step 0). Do not send the person to Claude's GitHub app, to claude.ai/code, or to a button
that only says "Connect to Claude". The studio's first-run band says **Connect this chat**.

- **Cloudflare** stays one tap on Cloudflare's own page. Grok has no Cloudflare connector and must never
  ask for a token. On a phone, the setup card's "Make the studio on Cloudflare" is that tap. On a computer,
  `npx wrangler login` opens the same approval.
- **This computer** is a Grok Bot, or Grok Build with a folder. Run the checklist here. When the chat has a
  setup id `hs_…`, check in once from the studio's own repository:
  `npx --no-install homie-studio setup attach <hs_…> --client grok`. That tells the directory Grok works in
  this repository. It does not need Claude's GitHub app. GitHub, when this chat already has it, is enough
  to push the branch and open the pull request.
- **A build** the chat opened (`hb_…`): `npx --no-install homie-studio handoff <hb_…> --client grok`. The
  session fetches the brief itself. There is no Claude Code window to open, and no second session to start.

## 1. The studio

Use the requested name, their business name, or "My Studio"; it can change later.
Then say in two or three lines what will happen, and go on: you make the studio folder here (no game
in it yet: its home page says "First game coming soon" until the first one is made); later, when it goes online, Cloudflare opens in their browser **once** to approve (a free
account); on their account you will create one Worker, one D1 database and two
Durable Objects, all free on the Workers Free plan; the homie.rocks directory lists the games (only the
site's address, the studio's name, each game's name, blurb and Play link).

1. Call `studio_scaffold` with the name (and a folder if the person named one) and run the command it
   returns; without the connector, run `npx -y @homie-rocks/studio@latest new <folder> --name "<Name>"`.
   Either lists every file it writes and installs the pinned toolkit and `wrangler` (about 20 s).
2. Folder: the one the person named; otherwise a NEW folder named after the studio's slug inside the
   current directory (e.g. `./night-owls`). Never in a folder that already holds other files, never in
   the home folder, never outside the current directory.
   **Other studios in the same folder** (a folder beside this one with its own `studio.json`) are other
   people's work: never read them or copy from them, not even as a model for this studio or its game,
   unless the person asks.
   **An earlier attempt:** if a folder of this name already exists and is not a studio (notes, a plan, a
   charter from before), say so and ASK whether to fold its premise in: with a yes, copy its notes into the
   studio's `notes/earlier/<folder>/` and use them in the plan; remove the old folder only with a second yes
   (to the Trash, so it can come back). Never delete or overwrite it unasked.
3. From here on run the studio's own copy: `npm run <script>` or `npx --no-install homie-studio <command>`
   (`--no-install` never fetches a package by that bare name).
4. Continue with the requested build.

A missing connector is no reason to stop: with a shell, make the studio with the command above and say in
one line that the connector is not connected ("Without the connector", step 0). Never invent the package
address: it is `@homie-rocks/studio`, and this skill is where it is written down.

## 2. See a working game (optional tutorial)

**Show a live one; copy nothing.** A new studio has no game, and it gets none it did not ask for.
`npx --no-install homie-studio demo` names a live multiplayer game on Homie Arcade (made with this same
toolkit) with its Play link: give them the link and say to open it in two browser tabs, or on a phone and
a computer, and they are two players in the same public room, with bots in the empty seats. Then ask:
"Want a copy of a working starter in your own studio to change, or shall we go straight to planning your
game?"

It always names one. Where your commands have no network (Codex runs them that way by default), it cannot
read the arcade and answers `"reached": false` with the arcade's standing first pick, Asteroids Arena:
https://arcade.homie.rocks/asteroids-arena/play. That link opens in the person's own browser, not in your
session, so give it as the live game it is and say nothing about the lookup. The same address serves when
the command cannot be run at all.

**Only when they ask for a copy** (now, or in their first message): the Gem Rush starter (grab gems, knock
rivals away; bots fill the empty seats), or Ember Vale (`--from ember-vale`: a hero who lasts for days, with
cloud saves) when they want a persistent game. Another studio's whole game cannot be copied; pieces
of one that its studio shared can (the `parts` skill).

```sh
npx --no-install homie-studio game new <id> --from gem-rush --name "<Name>"
npm run dev                                             # in the background: http://127.0.0.1:8787/<id>/play
npx --no-install homie-studio check <id> --url http://127.0.0.1:8787 --shots ./.checks
```

`check` proves it first: two fresh browsers press Play, share a room and see a round finish (about 70 s).
Show one of its pictures. Start `npm run dev` as a background task your app keeps alive (Claude Code: the
Bash tool's `run_in_background`); stop it with `npx --no-install homie-studio dev --stop`, which stops
exactly this studio's dev server and nothing else. Never `pkill`, `killall` or `lsof ... | xargs kill`: other
projects on this machine may run their own `wrangler dev`. Without a game, `npm run dev` shows the studio's
own home page ("First game coming soon") at http://127.0.0.1:8787/.

## 3. One small change (optional tutorial)

"Now tell me one thing to change, in your own words." With a copied starter, it is the game: a colour, the
speed, what you collect, the name (in `games/<id>/`). Without one, it is the studio's own home page: its
colours (`site/theme.json`), a tagline (`studio.json` `"tagline"`), or a first post ("we're making our first
game"; `posts/README.md`). Make exactly that, `npm run build`, and tell them to reload. If they say "you
pick", make one visible change (the colours, or the name and its colours) and say what it was. This is the
whole loop in a minute: they say it, they see it. Keep the change small; the big ideas go into the plan.

## 4. Plan your game: the Game Codex

Follow the `plan` skill: record your defaults in CODEX.md, show it and continue. No interview
unless requested. Engineering and design choices are yours; the person can steer at any time.

## 5. Build it

Use one agent by default and the `game` skill for a game. Give the Play link when checks pass.
Open a progress feed for every build so they can watch it:

```sh
npx --no-install homie-studio progress start <id> --title "<this milestone, from the codex>"
npx --no-install homie-studio progress stage plan done --note "<the plan in one line>"
```

`build`, `check` and `deploy` report into it. The codex page's **Build status** tab shows it (a
percentage, each step and check going green, how to try it, what was spent) and redraws itself; the
status line shows one line of it in Claude Code, and the Homie mod's Studio pane (Claude Code 2.1.287 or
later) shows all of it with the latest check frame and opens by itself. In the Claude app, add `--share` and call
`build_progress` with the build id it prints: the card follows the build. In Codex and Grok Build Homie
draws no status line, pane or card, so there the codex page is the progress view (`npx --no-install homie-studio codex <id> --open`).

## 6. Playtest it, then put it online

**Playtest** with the `playtest` skill; fix what it ranks first. If it is slow on a phone, the `perf` skill
measures why and keeps only the changes that make it faster beyond the noise. If a move feels weak (the jump, the
hit), the `lab` skill tunes it with the person, New beside Today.

**The site** is made from the studio (`node_modules/@homie-rocks/studio/site/SITE.md`): Home, Games,
Music, Videos, Rooms and Posts, each once the studio has something in it, in the studio's own look, with
"Made with Homie" at the foot of every page (keep it). Before going online:

1. **Its look.** `site/theme.json`: colours that belong to the studio's name and its first game (`bg`,
   `fg`, `accent`, `glow`, or a `palette`); the codex's palette is a good start. A one-line `"tagline"`
   in `studio.json`.
2. **The game's landing** (`/<id>/`): "Its landing page" in the `game` skill. At least the words
   (game.json `landing`) and a cover from a real frame (the `art` skill's free `frame` and `cover`).
3. **A first post**: `posts/<today>-<game id>-is-live.md` with `title:`, `summary:` and `game: <id>`
   (`posts/README.md` has the format).
4. **Look at it**: `npm run build`, `npm run dev`, then `npx --no-install homie-studio look --url
   http://127.0.0.1:8787`, open the pictures, fix, again.

**Cloudflare**, checked only now (a studio that never deploys never needs it):

1. `npx wrangler whoami` in the studio folder. Not signed in: run `npx wrangler login` and tell the
   person in one line that Cloudflare opened in their browser and they should approve it (their own account). That is their only step. Never ask for or write an API key.
2. Before the first deploy, `npx --no-install homie-studio deploy --plan`, and tell them its gist in two
   or three lines: the resources (one Worker, one D1 database, two Durable Objects; no R2), the cost
   (on your account), and what the directory stores. Then go on.
3. `npm run deploy`. It creates the Worker and the D1 database named in `studio.json`, applies
   migrations, deploys, and reads the live site once, which makes the site claim itself in the
   directory. It refuses to touch anything of the same name it did not create (rename in `studio.json`
   and `wrangler.jsonc`; never delete or overwrite the other resource). If it answers with a `needs`
   step, say it in one line and wait: `cloudflare-verify-email` (the account verifies its email address
   first: the email Cloudflare sent, one tap), `workers-dev-subdomain` (the AI registers the workers.dev address
   once, on the link it gives). `setup status` remembers which.
4. `npx --no-install homie-studio check <id> --url <the live site>`: the same two-browser proof, live.

**Tell Homie, once.** At the end of a first setup (the game is online, or the person stops for the day), and at
any point the person is stuck, confused or frustrated, or after an error you could not fix, you may offer, once in
the session, to send the people who make Homie a short note about how it went: "Want me to tell Homie that the
subdomain step was confusing? This is what I'd send:". Draft it with `homie_feedback` (`offered: true`; a draft
sends nothing), in plain words from what happened, with the step it was about (`step: "studio-setup: put it
online"`). Show it exactly as it would go (in the Claude app its card has Send, Edit and Don't send) and send it
only after they say yes; in Claude Code, Claude Code itself asks them with the exact note, and in Codex
Homie's hooks hold the send for their `proceed <code>`. A no is final for the
session: say nothing was sent and carry on. Never make help wait on it, never offer twice, never put a key, a log,
a file, code or anyone's name in it, and a reply address only if they typed it. When they ask to tell Homie
something themselves, draft it with `offered: false`.

### Another way: Cloudflare (and ElevenLabs) through Stripe Projects

`npx wrangler login` stays the way. Offer this only when the person has **no Cloudflare account** (and wants songs but
has no ElevenLabs either), and would rather have both made for them in one go: Stripe Projects
(docs.stripe.com/projects), Stripe's CLI plugin, makes or links provider accounts on the person's own Stripe sign-in
and hands the credentials to the studio folder. It is a prototype in this version (`setup --via stripe-projects`).

1. Say it in two lines: Stripe signs them in; Cloudflare makes a free account for their Stripe email (or, if they
   have one, shows its own approval page once); on their own accounts; they accept Cloudflare's terms
   (and ElevenLabs': whose free plan has **no commercial licence**, so songs made on it are not for sale).
2. `npx --no-install homie-studio setup --via stripe-projects [--with elevenlabs] --dry-run`: what it would do.
3. Run it without `--dry-run`. It stops at each step that is the person's and says which, as `needs`:
   - `stripe-cli` / `projects-plugin`: run the command it names (the person approves the install);
   - `projects-init`: run `stripe projects init --yes`; Stripe opens its sign-in in their browser. It must be **their
     own** Stripe account (a new free one is fine). If the Stripe CLI on this computer is signed in to some other
     account (a work or client one), stop and ask; never use it;
   - `accept-terms`: ask the person; only after their yes, run it again with `--accept-tos`;
   - `link-cloudflare`: run `stripe projects link cloudflare`; their browser shows Cloudflare's approval page;
   - `paid`: stop. Nothing paid is ever added; this is theirs to decide in Stripe Projects, not yours.
4. When it answers ok, `npm run deploy` as usual: Wrangler deploys with the Projects token.

What it keeps where: the Cloudflare account id goes in `studio.json` (`cloudflare.auth: "stripe-projects"`); the token
stays in Projects' vault and the git-ignored `.env` it syncs, and the toolkit hands it to Wrangler itself. Follow
Projects' own rules: never print, read out or `cat` an env value (`stripe projects env --json` lists names only), never
commit `.env`, `.env.*` or `.projects/vault/` (the command checks `.gitignore`), never hand-edit `.projects/`. If a
later deploy says the token is not accepted: `stripe projects env --pull` in the studio folder, then deploy again.

The live address `deploy` prints is on `workers.dev`, which names the person's Cloudflare account;
`deploy` keeps it in `.studio/local.json` (git-ignored). Never write it into a committed file. A custom
domain is set with `studio_domain` (Desktop), or by the AI adding `cloudflare.domain` and
`{ "pattern": "<hostname>", "custom_domain": true }` to the Wrangler routes. Deploy uses the
existing Cloudflare sign-in to create DNS and TLS. Never ask the person for a zone id or DNS record. Never touch a route the studio does not own: a catch-all
or wildcard route already on that domain belongs to another site there, and the deploy's warning gives the
one line to add instead (the `publish` skill has the rest).

**The directory, only when asked.** Going online never lists a studio: listing in the homie.rocks directory
is its own step, it is public, and it is the person's to ask for. When they asked to be listed (in their first
message or now), or say yes when you offer it once the site is live, call the Homie MCP tool `studio_publish`
with the live site address (without the connector, `npx --no-install homie-studio publish`). It lists the
games with their Play links (at most 12 per studio in the beta; its owner can unlist a listing that
breaks its rules).

**Tell the person**, three to five lines: the studio folder, the live site, each game's landing
(`/<id>/`) and Play link, the directory link when it was listed (and that it is not, when it was not), that two browsers finished a round on the live site, what
runs on their Cloudflare and what it costs (free). The codex is on the site for them alone:
`npx --no-install homie-studio codex link <id>` gives a one-time link for their own browser (a phone
works). The studio keeps its own stats for them (`npx --no-install homie-studio stats`, or `stats link`).
Add: Homie for studios is in beta; bugs, port requests and questions go to
https://github.com/homie-rocks/homie/issues/new/choose. Commit the studio (`git add -A && git commit -m
"..."` inside the studio folder: it is the studio's own repository).

## An existing studio that is behind: what's new

A studio pins one `@homie-rocks/studio` version in its `package.json`. When you open a studio, or the person asks
"what's new" or to update or upgrade it, compare that pin with the newest (`npm view @homie-rocks/studio version`; in
Claude Desktop the studio card says so itself). When the studio is behind:

1. Tell the person, in a few plain lines, what's new since their version: run
   `npx -y @homie-rocks/studio@latest upgrade` in the studio (it changes nothing). It starts with "What's new since
   <their version>", one line per version from the new version's own CHANGELOG.md, then the upgrade notes: anything
   they have to do themselves. Pass those on in your own words, the upgrade notes first; never paste the whole list.
   (In Claude Desktop: `studio_run` with `["upgrade"]`.)
2. Say what the upgrade would change in the studio (the plan under "The changes"), and that nothing they wrote
   themselves is touched.
3. Only with their yes: the `--apply` command the plan names, then `npm install` (`studio_install`), `npm run build`,
   a look at the site, and one commit for the upgrade on its own.

Every version's notes are also at https://github.com/homie-rocks/homie/blob/main/CHANGELOG.md.

## Another computer or collaborator

A private GitHub backup is optional, not a first-run requirement. If requested, install gh yourself,
start its browser/device sign-in, create a private repository and push. Discover the account and
repository names; never ask for an id, token or command. In a browser-capable host you enter the
device code on https://github.com/login/device; the owner signs in and approves. In Desktop without
browser control, explain that GitHub's device code is the remaining host limitation.

On another computer, install Homie in the host, then `studio_open` with the repository clones and
installs it. Use the existing name, plan and version. Reauthorize Cloudflare or Stripe only when
needed; never copy credentials or local owner state. For an explicitly requested collaborator,
resolve the named GitHub user, invite them to the repository with the requested role, and let them
accept GitHub's link. Repository access does not require Cloudflare billing or Stripe access.

## Storage, later and only when asked

Songs, videos and other large media go to the studio's storage (an R2 bucket), not git. A studio that
makes games never needs it. When the person wants it: `npx --no-install homie-studio storage add`.
Cloudflare asks for a payment method on the account before R2 works (its first 10 GB a month are free),
so say that first and let the person decide; if R2 is not turned on, the command gives the dashboard
link and creates nothing. Then every `npm run deploy` binds it and moves the big songs and videos
there (checked by SHA-256, at the same addresses); `homie-studio media move --dry-run` says which.

## Never

- Never jump ahead of the checklist, and never copy a starter or another studio's game into the studio
  unless the person asked for it.
- Never read or copy from another studio in the same folder unless the person asks: it is somebody else's
  work.
- Never stop for a missing connector while you can run a command, and never tell the person the connector
  is needed to make a studio.
- Never put a key, token or password in the studio or in chat.
- Never touch Cloudflare resources the studio did not create.
- Never add a payment method, buy anything or turn on a paid plan for the person (in Stripe Projects too: no
  `--confirm-paid-service`, no `stripe projects billing`, no `upgrade`).
- Never use `~/.homie`; the studio needs no Homie box.
- Never ask the person to type a command.
- Never send a note to Homie (`homie_feedback`) the person has not seen word for word and said yes to, and never
  offer one more than once in a session.
