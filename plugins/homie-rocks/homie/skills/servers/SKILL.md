---
name: servers
description: Give a Homie studio game lasting servers - named communities with their own rooms and rules - humans-only, hybrid (seats reserved for AI companions), beginner (new players, AI guides, kids-safe) - plus agent passes, the AI skill dial, the party's level vote, and AI guides that talk (a game vocabulary; Cloudflare's Clef decision model on the studio's Workers AI by default, Llama or the owner's key instead, Clef on the person's own computer under dev, or the owner's own Claude in a seat). Use when someone asks for servers, realms or shards, human-only play, AI party members or companions, guides or helpers for new players or kids, guides that answer "help me with this quest", "fill empty spots with AI", letting Claude play as a guide, which model the guides think with, testing an agents.json, free local AI guides, or how strong the bots should be.
compatibility: The studio's own Cloudflare account, with Workers AI through its Worker (Clef by default), Wrangler for the model catalogue and the doctor's probe; optionally Ollama with clef-flash on the person's own computer, downloaded only after their yes.
metadata:
  providers: cloudflare ollama
---

# Servers and AI seats

Needs `@homie-rocks/studio` 0.16.0 or later (`npx --no-install homie-studio upgrade --apply`, then deploy); guides
that talk need 0.17.0; Clef, `agents try` and Clef on the person's own computer need 0.24.4.
Everything lives in the studio's own Worker and D1; homie.rocks stores none of it. **AI is ALWAYS marked AI**:
the relay names every agent "<label> · AI" and marks it in every roster and result. Never name an agent so it looks
human, and never try to get an agent into a humans-only server.

A **server** is a named, lasting pool of rooms for one game: strangers are matched only inside one server. Every
game already has one, **Quick play** (its public rooms). A server's page is `/<game>/s/<id>/`; `/<game>/servers/`
lists them; the landing gets a Servers band.

## Do

| The person says | Run (or the MCP tool) | What happens |
|---|---|---|
| "Make a beginner server with two guide agents" | `npx --no-install homie-studio servers new <game> "<Name>" --policy beginner --guides 2` (`server_create`) | At once: the server and its page link. Two AI guide seats in every room, marked AI, at a gentle level, for accounts under 30 days (`--beginner-days`); chat is quick lines only. `--kids` adds handles only and keeps the AI's level at most 3. With no brain the guides play from the game's script, silent; to make them talk see **Guides that talk** below. |
| "A server with no AI at all" | `servers new <game> "<Name>" --policy humans-only` | No agent can join (the site refuses it, and so does the room); the game's practice bots are off (`--bots fill` turns them on, still marked AI). |
| "Keep two AI seats in every party" | `servers new <game> "<Name>" --policy hybrid --ai 2` | The top two seats of every room are AI companions; the party votes their level. A room of 8 holds 6 people. |
| "Make the bots easier / harder" | `servers set <game> <server> --level 2` (the server's default), `servers level <game> <room> 1-5` (one room now; `room_level`) | The dial: 1 Rookie, 2 Steady, 3 Fair, 4 Strong, 5 Maxed. Only games whose bots read it change; `servers` says which builds predate servers. `--level-max` caps what the party may vote. |
| "Only players with an account" / "invite-only server" | `servers set <game> <server> --door accounts` / `--door invite`, then `office invite <game> --server <server>` | A stricter door is an ASK (one tap). Invite codes and links for that server. |
| "Close that server" | `servers close <game> <server>` (`server_close`) | ASKED; its rooms finish their round, then everyone leaves with a thank-you. `--reopen` opens it again at once. Closing `public` hides Quick play: Play then shows the servers to pick from. |
| "Make <player> a mentor" | `servers member <game> <server> <player id> --role mentor` (`server_member`) | At once: a mentor gets into a beginner server, with a badge. `--remove` is an ASK. |
| "Can we sell things on this server?" / "a shop for the kids server" | nothing to run: the shop skill (`shop.json`) | A kids server (`--kids`) never shows a shop, takes no purchase and shows no supporter badges; a beginner server never offers, or counts as owned, an item with `"advantage": true`. Every other server shows the studio's shop sheet from the room button and the game's `shop.open()`. These are the protective shop preset defaults; the studio can edit policy in shop.json. |
| "Let my Claude play" | `agents pass <game> --label Claude [--server <id>]` (`agent_pass`) | At once: a pass shown ONCE (give it to the AI only; never write it into the repository or a chat). The AI sits with `POST /<game>/api/agent` (`Authorization: Bearer <pass>`), only in a room with people in it, as "Claude · AI", on an open, hybrid or beginner server. `agents revoke <id>` ends it (the AI leaves at once). |

## Guides that talk (0.17.0)

A beginner server's guides get a **brain** that picks a goal every few seconds and, when the owner allows it, a
line to say: only the game's own goals and lines, from `games/<game>/agents.json` (its **vocabulary**). The game's
bot code is the guides' **hands**: they carry the goal out every frame at the party's dial. The AI never types.
A person's ask is always answered the way agents.json says, with the values they asked for (a fixed rule overrules
any other goal or value), and a house guide greets a newcomer once and otherwise stays quiet.

| The person says | Do | What happens |
|---|---|---|
| "Make the guides talk" / "guides that help with quests" | 1. If `games/<game>/agents.json` is missing, write it with the person, in the game's own voice (the game skill's "Write the guide vocabulary"; `NETPLAY.md` section 18), and the game's `useAgents` (Ember Vale is the reference); build. 2. `agents brain <game> <server> workers-ai` (`agents_brain`) | The first time talk is turned on it is an ASK: give the owner the link. Then `npm run deploy` once (it binds Workers AI), and `npx --no-install homie-studio doctor`: its Workers AI row checks the model answers on the account (one tiny call), and names a model Cloudflare moved to Workers Paid or retired, with the fix. Guides think with Cloudflare's Clef decision model on the studio's own Workers AI (`@cf/cloudflare/clef-flash`, about 9 neurons a decision), at most 8,000 neurons a day for the whole studio (about 900 decisions; the free allocation is 10,000 an account; `--budget <neurons>`), then the game's script until 00:00 UTC. |
| "Use my own Claude key for the guides" | `agents brain <game> <server> owner-key --budget 1`, only when a key is already configured; otherwise use the Cloudflare brain through the existing sign-in | Never ask the person to find or type a key; **never ask for a key in the chat**. claude-haiku-4-5, about $0.30 a busy guide-hour, capped by `--budget` dollars a day (raising the cap is an ASK). |
| "Guides should just play, quietly" / "AI talk off" | `agents brain <game> <server> script` | At once: every AI on the server is silent; the guides play from the game's script. |
| "Let my Claude be a guide" | the local MCP's `agent_sit { game, server }` (or `homie-studio agents sit <game> --server <id>` in a terminal) | Claude takes a guide's seat as "Claude · AI" in a room with people in it, makes way for nobody (a house guide yields to it), and decides with `agent_look` / `agent_do` about every 30 s while the game's hands play. `agent_stand` leaves; its one-day pass is revoked. |
| "A guide that thinks on my computer" / "free AI guide" | `agent_sit { game, server, brain: "local" }` (or `agents sit <game> --server <id> --brain local`) | Clef on this computer (Ollama with `clef-flash`) decides every few seconds, free, nothing sent to Cloudflare; `agent_look` shows its last decisions and `agent_do` overrides one. With no `clef-flash` it says what the download is: ask first (below). |
| "Does my agents.json work?" / "which model is better?" | `agents try <game> --view <file.json> [--ask <ask>[:<arg>=<value>] --from <seat>] [--model <id>]` | The studio's guide brain on one moment, no seat taken: the decision, the brain's own pick before the fixed rules, Clef's probabilities, the model's ms and the neurons, spent from the guides' day. `--model` compares one (Llama, the 27B Clef) before setting it. |
| "What are the guides doing?" / "how much AI did we use?" | `servers`, the office (`/_studio/office`) | Today's neurons or dollars against the budget, why a guide is scripted (no binding, no key, budget spent), and each room's last decisions (the model, how sure Clef was, and the brain's own pick when a rule overruled it). |

**The model.** Clef is the default because it answers each decision as typed Choices (a goal, its values, a line or
none) and never writes text: on 64 recorded Ember Vale moments it answered 36 of 40 open asks itself (Llama 3.1 8B: 0),
and blind judges preferred it 51 to 0 (13 ties), at about 9 neurons a decision to Llama's 4. `HOMIE_BRAIN_MODEL` in
`wrangler.jsonc` vars picks `@cf/cloudflare/clef` (the 27B) or `@cf/meta/llama-3.1-8b-instruct-fp8-fast` (the old
default); try one with `agents try --model` first. **Which Workers AI models exist now** is Cloudflare's to say, not
memory: `npx wrangler ai models list --json` and `npx wrangler ai models schema <model>` (free; the studio's Wrangler,
signed in). Pick one that is not marked Workers Paid; the doctor's Workers AI row then proves it answers on this account.
**Under `homie-studio dev`** guides, chat review and game decisions think with Clef on this computer when Ollama (0.35.1 or
later) has `clef-flash` (free, nothing sent to Cloudflare; `dev --no-local-ai` turns it off), else from the script;
`dev --remote-ai` uses the real Workers AI (billed). The doctor's "Clef on this computer" row says what is there.
**Ask first.** Nothing downloads a model by itself: before `ollama pull clef-flash`, tell the person it downloads about
11 GB (`clef`, the 27B, about 18 GB) and wait for their yes. Never pull it to make a test pass; the Homie mod (Claude Code) and
Homie's hooks (Codex) hold the pull until they say Proceed.
**Adopting guides in an existing RPG** (zones, quests, a party): `node_modules/@homie-rocks/studio/agents/GUIDES.md`
is the short path, in the game's own repository and with its owner's say.

**Asks.** Making a server, a widening change, a pass, a mentor and a room's level happen at once. A change that
narrows who may come in (humans-only, a stricter door, fewer rooms), closing a server, removing a member, and the
first time AI guides may talk only ASK: the command prints a one-time link the owner opens; one tap does it. You
cannot confirm it.

**Tell the person plainly** which builds predate servers (`servers` and the office say "This build predates
servers"): such a game still plays on every server (doors, the people's cap, speech rules and AI names work), but
it keeps no AI seats and its bots ignore the dial until it is rebuilt with 0.16.0. A game whose bots are its own
code needs a few lines: the dial snippet in `node_modules/@homie-rocks/studio/netplay/NETPLAY.md` section 17
(`net.skillOf(slot)`, and `caps: ['skill', 'agents']`); a port on `BotBrain` gets it with `skill: () =>
room.skillOf(body)`.

**Money.** A paid "fill a spot" service (an AI seated in an empty spot for a price) is not offered: the office shows
it as coming later, and nothing issues its passes. Pricing it is the studio owner's own decision, never yours.
