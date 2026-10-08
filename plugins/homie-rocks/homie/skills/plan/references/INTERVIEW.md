# Plan interview: questions with options

Ask two or three at a time, each with options and your pick. Adapt the options to what the person has
said; these are starting points, not a script.

## 1. Game type and genre

- "What kind of game? A brawl in an arena, a race, a co-op survival, a puzzle versus, a party game of
  quick rounds, an adventure with a world to explore? From what you changed, I'd guess a brawl."
- "What does a player do in the first ten seconds?" (move and grab, aim and shoot, draw, guess, build)
- "How does a round end? First to a score, last one standing, the most points when the clock runs out?"
- Multiplayer shape: "Everyone against everyone, two teams, or all together against the game?"

## 2. Style and art direction

- "Pixel art, painterly, low-poly 3D, clean vector shapes, neon on black, hand-drawn? For phones at a
  glance I'd pick pixel or vector: they read small."
- "Name a game, film or picture it should feel like." (Two or three references are plenty.)
- "Day or night, cosy or tense, bright or moody?" Then propose a palette of four or five colours.
- Fonts: suggest one display font that fits (pixel: "Press Start 2P", "Silkscreen"; storybook: "Fraunces";
  sci-fi: "Orbitron", "Exo 2"; clean: "Inter").
- Ask once: "Do you want to steer the look closely (I'll show you three directions, drawn by the game itself,
  and you lock what you like), or should I pick and show you?" Hands-on: the `style` skill's board. Pick for me:
  `style init` with their words, then one line about the look.
- And once: "Art budget: free only (the starter library and the engine), a small budget on your own fal account
  (I'd suggest US$5 for a handful of generated props), or your own number?" Free only means no generated assets
  at all; the number is a hard cap (the `models` skill's `budget`).

## 3. Devices

- "People will play on phones and computers. Should it also work on a TV with phones as controllers, so
  friends on one couch play together?" (Say what that adds: the big screen view and each phone a pad.)
- Per device: "On a phone you steer from the lower left and press on the right; on a computer, keys.
  Anything that needs more than that?"

## 4. Players and rooms

- "How many in a room: 2 to 4 for a duel feel, 6 to 8 for a party, up to 32 for chaos?"
- "Rounds of 60 seconds, 90, or longer?" (Short rounds keep strangers.)
- "Bots fill empty seats. Should they be easy, or play to win?"
- "Someone who joins mid-round takes a bot's place. Do they keep the bot's score or start at zero?"

## 5. Progress and saves

Always ask: **"Does progress need to persist across sessions or devices?"** Then, if it does:

- "What does a player keep between visits: a character and its level, an inventory, unlocks, a collection,
  their settings? I'd keep the hero in one save, so it always saves whole."
- "Should it follow them to their phone and their laptop? Then they make an account with a passkey (Face ID or
  a fingerprint, no password); until they do, they play as a guest and keep it on that device."
- "Lifetime numbers that never reset: kills, gold earned, time played, best level?"
- "Can a death be forever? A hardcore mode wipes the character and writes its name in a hall of the fallen."
- No persistence (a match is all there is): say so in one line and move on; nothing to wire.

## 6. Art and film

- "Who are the characters, creatures or pieces? Name them and I'll give each a card."
- "Places: one arena, or several levels or zones?"
- "A cover and a trailer come from the game itself, free. Painted art or generated video is on your own
  fal account with a budget you set: want any of it, and how much at most?"
- For a 3D game: "Models come free from the engine and Homie's CC0 starter library first; a few signature props
  can be generated in your locked style for about US$0.54 each. Any you already own to bring in?"

## 7. Music and sound

- "A theme that loops while you play: fast and driving, calm, spooky, heroic? About what tempo?"
- "Which moments need a sound you'd recognise with your eyes closed?" (pick-up, hit, win, countdown)
- "Synthesized here for free, or a song from ElevenLabs on your own plan (quoted first)?"

## 8. Scope

- "For the first playable version: the core loop, one place, two or three characters, bots. Then art,
  sound and the landing page. Then more places or modes. Sound right?"
- "Anything that must be in the very first version?"
- "Anything you don't want at all?"

## Genre starters

| Genre | Ask about | A good default |
| --- | --- | --- |
| Arena brawl | knock-back, power-ups, the arena's hazards | 6–8 players, 60 s rounds, most knock-outs wins |
| Race | track shape, boosts, catch-up | 4–8 players, three laps or 90 s, first across wins |
| Co-op survival | waves, the enemies, reviving | 2–6 players, waves of 30 s, survive as many as you can |
| Party / quick rounds | the minigames, scoring across rounds | 4–8 players, 30 s rounds, five rounds a match |
| Puzzle versus | the board, sending trouble to others | 2–4 players, until one board fills |
| Adventure / RPG | classes, monsters, loot, zones, death, what persists | 2–8 players in a shared world, rounds as days or quests; the hero in cloud saves (start from the `ember-vale` starter) |
