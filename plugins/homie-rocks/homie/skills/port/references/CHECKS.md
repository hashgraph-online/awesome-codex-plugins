# The checks, row by row

`npx --no-install homie-studio port check <id> --url <site>` opens real browsers
(Chrome on the GPU, and WebKit when installed), never more than two at once, on the
real play page. Every row, what it measures, and what a failure usually means.
The receipt (`receipt.json`) and screenshots are in `games/<id>/.port/check-<stamp>/`;
a failed hold carries its `path` on screen (x right, y down, in bodies).

Run single rows with `--only owner-desk,owner-phone,owner-iphone,round,life,tv`
(`life` = host-kill + late-join).

Rules games build and pass strict types and generated play before these browser checks.
Both players are replicas of the server. Directional controls are N/A for declared
stationary anchors; prove the real commands, turn changes and immediate local feedback
instead. An intentional freeze is a blocked sample: repeat during active play without
removing the mechanic. Native DOM buttons must receive actual touch taps, not only clicks.

## owner-desk · owner-phone · owner-iphone

A private room (`?room=chk-…`), the player alone with bots.

- **hold**: one direction held 5 s (keys: `down` then `left`; a side view: `right`
  then `left`). Passes when the free run (until something blocks it) is one straight
  line the pressed way on SCREEN axes (direction within 15°, under 10% of moving
  frames off by more than 25°), it travelled more than two bodies, and the camera's
  yaw changed by less than 10°.
- **alternate**: 10 s of presses (420 ms each, 170 ms apart; down/up/left/right, or
  left/right in a side view). Each press must start moving the pressed way within
  600 ms and keep going that way; presses that move nothing (a wall) are "blocked"
  and do not count, but at least 70% must move and 90% of those must be right.
- **board** games: ten key presses (desk) or swipes (phones); each must change
  `moves` and report `lastMove` = the pressed direction within 1.2 s.
- **maze** games (`view: 'maze'`): a turn pressed into a wall may wait for the next
  opening (the body keeps going meanwhile); it fails only if the body then moves
  against the pressed way. Reversals must still answer within 600 ms.
- phone = Android Chrome (Pixel 7, DPR 2.625) and iPhone 15 WebKit, with real touch
  events: a thumb lands at 24%/74% of the screen (change with `thumb` in the probe),
  slides 70 px the pressed way and holds with a small wobble.

Failures and their usual cause:

| Says | Usually |
| --- | --- |
| too few samples / no body on the probe | probe missing, or the player has not arrived; rules views use `room.me` and the starter probe |
| barely moved | input never reached the body: keys go to the game's canvas/document? on phones, touch not wired (use the touch kit), or the stick's keys don't match the game's keys |
| went the wrong way | input read in the character's facing, a mirrored axis, or a y-up/y-down mix-up in `self`/`basis` |
| not a straight line | acceleration/inertia or steering that curves (tank controls), a camera-relative mapping to a moving camera |
| the camera turned by itself | the camera follows the heading; give it a yaw only the player turns |
| alternate: wrong way | input latency (movement missing from shared `defineMove`?), or momentum that keeps the old direction for > 600 ms |
| iPhone only fails | a pointer id sentinel (`-1`), passive listeners, a page gesture, an overlay taking touches — use the touch kit |
| a press or a hold is thrown off now and then | something hit the player (a bot's shot, a knockback): report `busy` in the probe while the body is not the player's to steer, and keep bots off newcomers for their first seconds |

## ui-cover

On the Android phone during play: the share of the screen the game's DOM UI covers
(8 px grid; full-screen canvases are the world, not UI) must be ≤ 12%, and nothing
opaque may sit in the middle third. Fix: chips, not panels; `pointer-events: none`
and translucent backgrounds; hide menus during play. A game whose world IS HTML (a
board of tiles, a card table) names it with `exposePort({ world: '.board' })` so the
board counts as the world; stationary DOM controls may make this row N/A. Never rewrite a game's renderer just to pass this row; inspect its actual board on phone sizes.

## round

Two fresh browsers (a computer and a phone) press Play (the real lobby, like two
strangers), must land in the same room, and must both see a round finish that lists
both of them in its results. It plays for them (keys, drags) the whole time. Fails:
different rooms (the page ignored the shell's room), no results (rules need automatic
rounds or a room handler calling `world.round.end()`), or only one person listed
(a person's declared player entity is missing from the results). A turn game needs
its actual moves played; random directions alone cannot prove a match.

## host-kill · late-join (the `life` row)

A computer opens a private room and a phone joins. After 3 s the first browser
closes. In a server rules game the phone remains a replica and the SAME round
continues: there is no election. A new computer then joins the same round, receives
state, takes the appropriate bot slot and can use the actual controls. Keep
`on.arrive` initialization separate from `onRoom.roundStart`; a join must not reset
the whole room. Read `room.round` for the authoritative clock.

For an unchanged older browser-hosted game only, `host-kill` instead checks that
the phone becomes host within 5 s and restores the same round from its checkpoint.
Its maintenance contract remains in NETPLAY.md sections 1–28.

Also try these manually in two browsers:

- Everyone leaves, then someone enters before the 60 s forget interval. The server
  resumes its saved room; the new arrival gets the intended body and initialization.
- Reload the same person's tab: their body and score return without resetting others.
- Disconnect one person's network while another joins: after reconnect, each person
  has one body and the intended score. Do not add browser-host handoff code.

## tv

`/<id>/tv` on a 1280×720 screen: a spectator with no seat and no body, the join QR,
a game picture that is not black, frames advancing. The join QR is required on an
address another phone can reach; on a loopback preview (127.0.0.1, localhost) the page
leaves the join card out on purpose, so the row says `qr: not applicable` and does not
fail on it. A local pass therefore says nothing about the live QR: run this row against
the deployed address before release. Fails: the game gives a spectator
a body (rules views have `room.seat === null`), or renders nothing without a player.
A spectator does not keep an empty server room ticking: keep a real player connected
when testing live action. A LAN address can prove the local QR without deploying.

## audio · sandbox · errors

- **audio**: every AudioContext is running after the first keys (skipped when the
  game has no Web Audio). Fails: the context was made before the toolkit loaded
  (load `homie-port.js` first / import `port/early` first) or a title gate.
- **sandbox**: which stand-ins the toolkit installed (storage, cookies, gamepads).
- **errors**: no uncaught error in any browser (console errors and HTTP 4xx are
  listed for you to read; a 404 is usually an absolute path).
