---
name: office
description: Run a Homie studio's live games from its back office - who is playing right now in every room (players, bots, round, uptime), announce a line to players in-game, kick or mute a player, close a room, set players per room, and each game's launch state (private, invite-only beta with invite links and codes, public). The owner confirms anything that takes something away with one tap. Use when someone asks who is playing, wants to talk to their players, remove or silence a player, run a closed or invite-only beta, hide or launch a game, make invite codes, or run the studio's Lounge (its community room, with play nights, moderators and kept chat).
---

# Run the studio's live games (the back office)

Everything lives in the studio's own Worker and D1 (`@homie-rocks/studio` 0.13.0 or later).
A studio whose `package.json` pins an older version than the newest is behind: say so, and what's new since its
version, before anything else. `npx -y @homie-rocks/studio@latest upgrade` in the studio prints "What's new since
<its version>" and the plan, and changes nothing (in Claude Desktop, `studio_run` with `["upgrade"]`, and the
studio card says it too). Pass on the upgrade notes in plain words; with the owner's yes, run the `--apply` command
the plan names, then `npm install` and a deploy, so the office's newer controls reach the live site.
homie.rocks stores none of it. The owner is the studio's owner: never act as if a player
or anyone else were.

## Look first

- In the studio folder: `npx --no-install homie-studio office` lists every live room of
  every game, who is in it (seat, handle, phone or computer, host, guest or invited),
  bots, the round and how long the room has been up. Say it plainly.
- From an app without the studio folder: `npx --no-install homie-studio office key`
  gives an office key (1 hour by default); pass `{ site, key }` to the Homie MCP tool
  `studio_office`, which shows a live card where the app can draw one. Never paste the key
  anywhere else; `office revoke` ends every key.
- For the person's own browser: `npx --no-install homie-studio office link` gives a
  one-time sign-in link to `/_studio/office` (live, refreshing, with every control), and
  signs that browser in as the owner: their own games then show a small Owner button
  (tap a player: Mute, Kick; Announce). Give the link to the person to open themselves.

In Claude Code (2.1.287 or later) the Homie mod's Studio pane shows the same office to the person
directly: `/rooms` lists the live rooms, and its owner view (`o`) has Mute, Kick and Announce, which run
these same commands and ask the same way. A one-time owner link in any command's output is taken out of
what you read and shown to the person in that pane: tell them it is there.

## Do

| The person says | Run (or the MCP tool) | What happens |
|---|---|---|
| "Tell everyone..." | `office announce "<one line>" [--game <id>] [--room <code>]` (`room_announce`) | At once: a banner every player sees in the game, 30 s by default (`--seconds`). |
| "Make invite codes for the beta" | `office invite <id> --label "<who>" --uses 1` (`game_launch_state` with `invites`) | At once: invite links and codes (XXXX-XXXX); each lets one browser in, or `--uses <n>` / `any`. |
| "Kick / boot that player" | `office kick <id> <room> <seat number or name>` (`room_kick`) | ASKED: the owner taps once to confirm. They are removed with a polite notice and cannot come back to that room for 10 minutes (`--minutes`). |
| "Mute that player" | `office mute <id> <room> <seat number or name>` (`--off` lifts it) | ASKED, like a kick: their chat and emotes reach nobody for 10 minutes (`--minutes`). |
| "Close that room" | `office close <id> <room>` (`room_close`) | ASKED, then everyone is sent out with a thank-you; nobody gets in for 10 minutes. |
| "What are people saying?", "take that message down", "chat rules", "emoji only", "only signed-in players can type", "slow mode", "reports" | `chat` (rules, every room's last minutes, reports, the review's day), `chat remove <id> <room> <line id>`, `chat rules <id> [--server <s>] --mode off\|emoji\|lines\|text --who anyone\|signed-in\|members --slow <s> …`, `chat budget <n>`; a mute or kick of a line's sender is in the office page (or the studio API's `mute`/`kick` with `line`) | Room chat (0.23.0, `chat/CHAT.md`). Removing a line happens at once, on every screen. A rule change that tightens chat happens at once; one that opens it up (a wider mode or audience, less slow, links or swears, the review off) and a bigger review budget are ASKED. Say what the rules mean for the game's players in plain words, and point the owner at `chat/OWNERS.md` (what is stored, children's data; not legal advice). |
| "A place for our community", "a lounge", "a play night on Friday", "keep the chat for a week", "make them a moderator", "slow mode in the Lounge" | studio.json `"lounge": true` (then build and deploy) for the page at `/lounge/`; `lounge` (its rules, play nights, moderators, last lines, reports), `lounge night "<title>" --at <ISO time with zone> [--minutes 120] [--game <id>]`, `lounge night remove <id>`, `lounge history <days>`, `lounge rules --slow <s> …`, `lounge mod <player id> [--remove]`, `lounge remove <line id>` | The Lounge (0.29.0, `chat/LOUNGE.md`): room chat in a lasting room of the studio's own, with "show what you made" cards and live rooms. Ask the owner for the play night's time in their own zone and write it with its offset. A play night, slow mode, keeping fewer days and taking a line down happen at once; keeping more days, opening chat up, a new moderator, a mute or a kick are ASKED. History is off until the owner turns it on, never on a kids Lounge: say what is kept, for how long, and that people can take their own lines down. |
| "Refund that purchase" / "how are sales?" | `shop refund <ord_…>`, `shop orders` (the shop skill) | A refund is ASKED (the owner's one tap); the owner's own page is `/_studio/office/shop`: orders, refunds, disputes, payouts and tax as links to the studio's own Stripe. |
| "Make servers", "humans only", "AI companions or guides", "guides that talk", "how strong are the bots", "let my AI play" | the `servers` skill: `servers new`, `servers set`, `servers level`, `agents pass`, `agents brain` (`server_create`, `server_set`, `room_level`, `agent_pass`, `agents_brain`; locally `agent_sit`) | Servers are named room pools with their own rules (humans-only, hybrid, beginner); see that skill. Narrowing one or closing it is ASKED, like a kick, and so is the first time AI guides may talk. |
| "Make it private / an invite-only beta / public", "players per room" | `office launch <id> private\|invite\|public [--max <n>]` (`game_launch_state`) | ASKED. Private: only the owner. Invite: invited browsers only. Public: anyone, listed. Going private or invite-only lets each live room finish its current round with a notice to the players; then everyone the new state leaves out is sent out with a thank-you (the owner, and in a beta the invited, play on). The game leaves the homie.rocks directory the next time it reads the studio (`studio_publish` reads it at once). |

**An ask is not done until the owner tapped.** `kick`, `mute`, `close` and `launch` print a
one-time link (the MCP tools show a card with the same button) that opens the ask in the
owner's own browser; one tap does it, "No" cancels it, and it ends after 15 minutes. You
cannot confirm it and must never try: no key, tool or command can. Tell the person what
you asked for, give them the link, and check afterwards (`office`, or the ask's status).

- To keep a NEW game private from its very first deploy, put `"launch": "private"` in its
  `game.json` before deploying; the owner opens it with `office link --to /<id>/play`.
- Mute stops a player's room chat too (the play page's Chat: their lines and reactions reach nobody, and the
  sheet tells them so); from a chat line (the office, or the owner's own game) it also holds a watcher with no
  seat, and can take their lines down with it.
- Mute stops a player's chat and emotes: the relay drops their `ev` whose kind starts with
  `say`, `chat` or `emote`, so a game that sends its chat, quick lines and emotes under those
  kinds is muted for free. If the game has other ways to talk, make it hide them with
  `net.isMuted(seat)`; a game can also show
  announcements its own way (`net.on('announce', ...)`) and open a player's owner card when
  their body is clicked (`net.pickPlayer(seat)`): `NETPLAY.md` section 15.
- Kicks hold a player's browser and, when they are signed in, their account (an invited
  player's ticket names both), never their network from the office; the studio's API takes
  `address: true` for a persistent troll (a household or a phone carrier can share one).
- In a Preview (a branch's own address) launch states are not enforced and there is no
  office: it has no database.
