# The method behind the rows

How a game gets judged honestly, and the ways a test lies. Everything here was measured on games that
passed their tests and still failed people.

## Play it like a person

Hold a direction for most of a second, not one frame. Press the thing whose label sounds fun. Try the
control you would try first if nobody had told you anything. A script that presses every button in
order is a conformance test, and conformance is not what is wrong with a boring game.

## The five numbers a round owes you

| | say | why |
| --- | --- | --- |
| how long | seconds from start to finish, against the clock the game set | a 150-second round that ends at 40 means nobody has seen most of the game |
| how it ended | who won and by how much | if you cannot tell, a stranger cannot either |
| the tense moment | one sentence about the best five seconds, or "there wasn't one" | the answer that unsticks a stalled game |
| what did nothing | any control that produced no visible change | a dead control is the first thing people notice |
| what you wanted | the one thing you reached for and could not do | the next change |

Add **lead changes** (the number that separates a race from a procession) and **whether doing nothing
scores as well as playing** (the `play` row measures both humans).

## Different strategies in different seats

Seats that all play the same way can only prove the game runs. Give simulated seats different
standing strategies, one per side of the decision the game claims to be about: the greedy one that
takes the risk the design says should pay, the safe one, the one that goes near other players on
purpose, the middle. Then read which one scored zero. On one game whose whole idea was "carrying more
makes you a target", the greedy runner finished on 0, 0 and 0 in three rounds because at a full carry
it was slower than the hunter and could never escape: the exciting strategy was arithmetic, and the
game everyone described was never actually played. No screenshot and no reading of the code found it;
three rounds with four strategies did, in two minutes.

## The do-nothing test

Write it first: a player who stops touching anything, at every place a player plausibly stops, for
longer than anyone's patience. The game must come to get them (a nudge, a timer, the round moving on),
never freeze, never go black, never soft-lock the room. Continuous worlds must also be tuned in real
seconds: a decay tuned on a fast test clock empties a real room in a minute. Simulate a long idle
stretch and read the state before and after.

## Every scenario before "finished"

1. One person alone, with bots, on a computer.
2. One person on a phone, portrait and landscape (a game that needs landscape says so and survives the
   turn).
3. Two strangers who pressed Play at different times, including one who arrives mid-round and takes a
   bot's place (and its score: a joiner inherits the body, so only a round that starts after both are in
   says how they played).
4. The host leaving mid-round: someone else continues the same round, clock where it was.
5. The big screen (`/<id>/tv`): a spectator with no body, a join QR, the game moving.
6. Nobody touching anything.

Say which you tried. "We could not test it" and "we tested it and it was fine" must never sound alike.

## The ten-second test

Ten seconds of silent video, no context, on a phone someone is scrolling past: do they stop? Every
change should leave one moment worth clipping (a knockout that reads from across a room, a comeback you
can see coming, something that happens once a round and is unmistakable). A change that produced
nothing you would cut fifteen seconds around produced polish; polish compounds slowly and nobody shares
it. Take a swing (a hazard, a rule that changes the last ten seconds) rather than tuning a number.
Readable at a distance: whose is that, what just happened, who is winning. Punctuate: silence, then a
hit. A thing that happens constantly is wallpaper; once a round it is an event.

## Judging, not building

- **The builder never grades its own work.** A reviewer gets the goal, the bar and the running game,
  never the builder's reasons.
- **Measure, don't assert.** "I differenced the two frames: nothing moved more than 8 of 255" ends an
  argument that prose cannot.
- **Two instruments on the same build.** A reviewer given only pictures grades the picture: one scored
  a game 34/100 for a hunted player drawn at 1.14:1 contrast against the searchlight meant to mark
  him, while a play measurement of the same build found the round always ended at 40 s of 150 and the
  risky strategy scored zero. Neither could see what the other saw. When they disagree, the fight
  outranks the frame.
- **The whole frame and a real round, regularly.** A reviewer shown a crop can only ask about the crop:
  thirty-five changes in a row once went into one decorative prop, each winning its own comparison,
  while the game as a whole did not improve.
- **Judge the set.** Twenty screens that each passed review were one layout repeated fourteen times.
  Put the whole set in front of one reviewer: squint, how many distinct shapes are there?
- **A reference is a bar, not a template.** Ask "is it as good as that", never "is it shaped like that".
- **Group findings by cause** before assigning work; five findings, one cause, one fix in the shared layer.
- **A finding that names a relation has two sides**: "the brightest thing is not a player" can be fixed
  by darkening the floor or brightening the player; move one side on purpose and check the other.
- **Stop on a regression.** A change that is not clearly better than the one before is worse. Scores
  like 48, 54, 58, 50, 42 mean the peak was 58: go back to it.

## Measured bars

| what | bar |
| --- | --- |
| seated and moving | under 10 s from pressing Play, first press moves you within about a second |
| hold a direction 5 s | one straight line the pressed way on screen, camera yaw change under 10° |
| alternate directions 10 s | every press goes the pressed way within 600 ms |
| UI during play | at most about 12% of the screen, nothing opaque in the middle third |
| look | no black or one-colour frame; detail at several scales (edge share of a finished-looking frame is several times a placeholder's) |
| sound | starts on the first touch; every action answers; -16 to -12 LUFS while played; nothing clips; little lost on a phone |
| rounds | two strangers meet in one room and both see a round finish; a killed host hands over in 5 s; a late joiner takes a bot's place |

## How instruments lie

- **A software renderer fakes a stuck game.** Headless Chrome without the GPU draws a WebGL game at 1-2
  fps; count animation frames first and say BLOCKED under ~20 fps. With the GPU flags a headless shot
  matches the real screen within a fraction of a luma point.
- **Reading a WebGL canvas from a script returns black** unless it is read inside a late animation frame;
  use a screenshot of the page (the compositor's picture) instead.
- **A full-page screenshot stretches the viewport**, so phone-landscape media queries stop matching; take
  the viewport only.
- **Emulated phones pass while real phones fail.** Real touch on iPhone Safari differs (coalesced
  moves, passive listeners, pointer ids, 120 Hz); the iOS Simulator is the closest thing to an iPhone
  on a Mac (`xcrun simctl openurl booted <url>`, mouse drags become real touches). Say when a result
  is emulation only.
- **A delivered press is not a correct press.** Only the body's movement on screen proves direction.
- **Gate on the thing itself.** "A sound file plays" and "a texture is bound", not a number a hiss and a
  flat cube would pass. Ask what the cheapest thing that passes the check would be.
- **A still is not the game.** A title card or the moment before a round starts is a picture of
  nothing happening; shoot while it is being played.
- **Another run can replace what you are judging.** Note the build you judged (a digest, a commit) before
  and after.
- A reviewer that shares your working folder can "tidy" your half-written file: commit before you hand
  work to one.
