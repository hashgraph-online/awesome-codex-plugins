# Honesty rules

## Gameplay is captured, never made

- Anything presented as the game is recorded from the game running (`capture`), in a live room,
  with nothing pressed for the camera and nothing drawn over the play.
- Generated footage (a model's clip) is never cut into a trailer as if it were gameplay. A
  trailer may open on a generated or drawn title sequence; the moment gameplay starts, it is the
  game.
- No speed-ups, no reversed footage, no frame interpolation passed off as the game's frame rate.
  Held frames are counted in `capture.json`; if the game ran slowly, say so or capture again.
- Bots are bots. The game's own bots fill empty seats; never caption or voice them as people,
  and never claim player counts the room did not have.
- A page recording (`record`) is pressed by a script, in real time: it says so, and the cursor and
  press rings it draws are the recorder's, not the page's. Its frames are the page's own, held when the
  page did not repaint, never interpolated; on a software renderer or under 20 fps it is a recording
  of a slow computer, and is not shown as the game's speed.
- A studio's score or player numbers shown on screen are what the game drew during the capture.

## No real people, no real brands

- No likeness, voice or name of a real person (celebrities, public figures, private people) in a
  prompt, a reference image, a voice or the type. Invent the cast.
- No real logos, products, brands or copyrighted characters; no screenshots of other people's
  posts, videos or games; no "in the style of" a living artist.
- References a person supplies (a photo, a sketch) are theirs to give: ask when unsure.

## Money

- A budget before the first paid call; every call priced from the provider's own pricing and
  refused past the cap; a receipt written the moment the provider accepts the job; a resumed
  job never paid for twice. Report spend against the cap.

## Rights of what is made

- Music: the plan at render time decides (the `music` skill's `references/RIGHTS.md`).
- fal: outputs belong to the person under fal's terms, but each model has its own licence and
  content policy. Read the model page's licence line before commercial use and put the models in
  the video's credits (`add` does).
