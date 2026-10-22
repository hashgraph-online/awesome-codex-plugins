# What broke, and the rule it left

Every line here is something real players, real phones or an independent tester
found in multiplayer web games built on this contract. Numbers are what was
measured. Read it before porting; come back when a check fails.

These observations include older browser-hosted ports. New ports use server rules
and shared `defineMove`; the historical `bound`, `take`/`give`, `adopt`, checkpoint
and host-election remedies below apply only to maintaining those older games.
For a rules rewrite, encode knocks/freezes in motion, use map sweeps and predicted
poses, initialize `on.arrive`, and let the runtime save and resume the server room.
Do not copy an old browser-host architecture. The reported timings are observations,
not a performance or feel guarantee.

## Movement

- **Your own body should answer locally.** Historical owner movement answered a key in
  8–17 ms in these trials; waiting for the host took 100–200 ms. Rules games use
  shared `defineMove` for immediate prediction. A turn game gives local press/selection
  feedback while its authoritative turn and score wait for the server.
- **Bound claims by time, not per frame.** A per-frame speed bound at 60 fps let a
  cheat run at ~6× speed; a bound of 0.4 s of "bank" reset an honest phone that had
  stalled for a second. Bound a claim by `maxSpeed × 1.3 × dt` plus a little slack,
  and reset only a claim more than half a second of running away (`room.bound` does).
- **After the host hands a body back** (the end of a knockback, a respawn), bound the
  first claim from the host's spot by the time since the hand-back, not by one frame,
  or a loaded host resets honest owners by metres.
- **Never let the host move a body its owner draws** (a ledge snap, a latch, a slide
  the host alone applied): the owner snaps back 1–3 m. If the rules must move a
  person, `take` the body, do it on the host, `give` it back.
- **A replay of every unacknowledged input counts the walk twice** after a stall
  (3–5 m back, then 8–10 m forward). Cap prediction replay at the snapshot's age plus
  the round trip.
- **Snapshot precision matters for feet.** 1 cm positions put a replica inside a
  kerb and made 1–2 m zig-zags; settle the owner's body on the ground again after
  adopting a position.

## Controls and camera (the owner's own hands)

- **"Pressing back keeps changing your direction."** The stick was read in the
  character's facing and the chase camera followed that facing: back turned the
  character toward the lens, the camera swung behind it, and back now meant a new
  direction — 10–13 of 13–16 taps went the wrong way, a 5 s back hold turned the
  camera 180°. The fix: read input on the camera's screen axes; the camera's yaw
  changes only for a look input. A "stable chase" that re-aligned after 0.9 s of rest
  still turned the view 80–90° on its own and broke the next presses, so a fixed
  orientation (north up) is the safe default for top-down and three-quarter views.
- **"You are so high above now."** A 15 m boom at 55° made the character 6% of a
  phone's height. The better default: character ~14% of a phone's height (~20% on a
  desktop), pitch 34–37°, the street ahead visible.
- **Obstacles fade; the camera never jumps in front of them.**
- **A camera's ground reference must be smooth.** A pad's bounding box treated as
  its floor lifted the camera 18 m and floated name tags 200–300 px off their owners.
  Rate-limit the camera's ground height (~6 m/s) and anchor tags to the body.

## Phones and touch

- **iOS Safari's touch ids are random 32-bit numbers, negative half the time.** A
  stick that used `-1` as "no finger" and `id >= 0` as "a finger" drew its knob
  perfectly and never moved the player, while the buttons worked. Emulators number
  fingers 0, 1, 2 and passed for hours. Use `null` for "no finger" (the touch kit does).
- Native DOM buttons belong outside `guardGestures`' touch selector unless they
  handle touch pointers explicitly; suppressing native clicks can make an `onclick`
  button inert on phones. Verify with a real touch tap.
- **A pinch between two thumbs is a page gesture**: the browser cancels both touches.
  Listen on the window, capture phase, non-passive; `preventDefault` every game
  touch; cancel Safari's `gesture*` events; a phone-safe viewport (no zoom).
- **`pointercancel` is not a lifted finger**, and a window blur is not either (the
  play page focuses the frame, which blurs it).
- **The stick belongs to the finger that started in its zone** — a resting palm must
  not steal it (a tester's grip broke 16% of presses).
- **Invisible overlays eat touches.** A hidden dock's 319×219 box took 21–28% of
  touches; a fading boot card ate the first thumb for 0.6–0.8 s. Every non-control
  element over the game gets `pointer-events: none`.
- **Small pushes must move you**: a thumb past the dead zone starts at ~35–60%.
- **A landscape arena on an upright phone** shrinks into a strip with two thirds of
  the screen empty; people read it as broken. Follow the player (a camera centred
  on your body) or lay the world out for portrait. Ember Vale's starter did it until
  0.18.1 (its 1600x1000 vale was 390x244 on a 390x844 phone, bodies 11 px across).
- **Arrivals spawned inside each other**: until 0.18.2 `createRoom` gave every body
  that arrived mid-round (a joiner with no bot to take over) spawn index 0, so three
  heroes stood in one spot in Ember Vale. Now a mid-round arrival gets the lowest
  index no body holds; spread `spawn(slot, i)` round the map with it, the first few
  far apart (Ember Vale: 0°, 180°, 90°, 270°…).
- **Names pile up where bodies crowd** (a party round its guides, a spawn point):
  four labels drawn at their bodies became one unreadable smear. Place them on the
  screen, yours first, the rest moved a row or faded (`createLabels`).
- **The UI owns at most ~12% of a phone's screen** and nothing opaque sits in the
  middle third during play; panels are small chips that open on demand. "The
  controls took over the screen" was an owner's verdict on a game with great visuals.
- **WebKit throws on `navigator.getGamepads()`** in the sandboxed frame on every
  poll (the toolkit guards it). **MSAA** (`antialias: true`) with post-processing drew
  a black world on iPhone and on a Pixel; turn it off on phones.
- **A slow phone must not be the host for long**: a phone host below ~20–30 fps
  slowed the whole room; hand the room to a seated computer (`net.handOff()`), never
  in a host's first 30 s, at most once a minute.

- Every stick reports up as y = -1 (screen axes). In a 3D world, map it to the ground by which side of
  the body the camera sits on, never by the body's facing, or up means a different way every turn.
- A stick sample of exactly zero is "no news", not "stop": coast to a stop over about 400 ms, or a
  dropped touch packet stutters the body.

## Joining, leaving, hosting

- **The first visitor plays at once with bots.** A lone stranger waiting for a
  second player waits forever.
- **A late joiner takes a bot's place**, not a new body: pick a bot that is doing
  well but not winning (the one nearest the pack), give a short shield, and never
  hand over a bot that is dead, carrying the win, or a lap down.
  Express admission in declared rules and preserve the existing player body on
  reconnect, so a reload is not a way back into an elimination round.
- **A room can outlive everyone in it.** The relay keeps an empty room's round for
  60 s; the next visitor hosts that same round. Its body is a takeover like any
  other (`onTakeover`, then `adopt`): do the newcomer's reset there, not only in a
  `join` handler.
- **A joiner's clock is right from its first frame**: a stale "1:30" showed for a
  second in production; take the clock from the room's round, not a local default.
- **A person's first 15–20 s show one objective**; bots do not hunt a newcomer;
  bonus offers and secondary prompts wait.
- **Host migration continues the same round.** A promoted host during the results
  once started round n+1 instead of the round the room had announced; adopt the
  room's round and its end time. Survivors must not snap: the new host keeps each
  person's body where their own browser has it.
- **A host that stalls (a shader compile, a texture rebuild) for 1.5 s is replaced.**
  Keep snapshots going around long work (send one before and after), and precompile
  shaders behind the first frame.
- **A burst is a stall's echo.** A loaded phone flushed a second of snapshots at once
  and the relay called the host stalled; drop a snapshot when the socket already has
  ~3 KB queued (the helper does). Inputs are paced under the relay's cap (the helper does).

## Bots

- Bots that stood still 40% of the time made the room feel dead: commit to a target
  for seconds, detect "stuck" by position (not reported speed), pick the most open
  direction to get out.
- Bots that won every round made people leave; a rubber band measured against the
  leading PERSON (not the host's own body) keeps rounds close.
- Bots made 17 of 19 kills in a co-op shooter and people felt like passengers: send
  the action toward people, and let people deal more damage in their first minute.

## The big screen

- It is a spectator: a big screen showed a bot's personal prompts ("TAKE THE WIRE?",
  "JUMP TO RECOVER") to the whole room. Report, never prompt.
- It follows people: a director camera that sat on a bot 44 of 55 samples was fixed
  to follow a moving person first, hold ~5 s, and cut cleanly.
- 16 px text at 1080p is too small across a room.

## Sound

- No "tap for sound" screen: resume the audio context on the first touch, key or
  click (capture phase), play a silent sample inside that gesture on iOS, and set the
  audio session to `playback` so the silent switch does not mute it (the toolkit does).
- A held stick unlocks sound only when the finger lifts (browsers grant activation on
  touchend); the first tap does it.
- Phone speakers lose everything under ~300 Hz; a low-pass sweep at 720 Hz vanished
  on a phone.
- A port that came with no sound, or whose sound was cut, is not finished: the `sound` skill
  synthesizes effects and a theme for free and wires them in; the `playtest` skill's sound row
  captures what the game really plays.

## Harness traps (when a check looks wrong)

- Software rendering (SwiftShader) runs at ~1.3 fps and fakes a stuck game; the check
  launches Chrome on the GPU.
- A background tab throttles its frames; the check keeps each page in front.
- Timings taken on a loaded machine lie; rerun a slow row when the machine is quiet.
- A harness that steered the wrong way once threw out a whole run: when a row says
  "went the wrong way", confirm with your own eyes on the screenshots before
  rewriting the controls.
