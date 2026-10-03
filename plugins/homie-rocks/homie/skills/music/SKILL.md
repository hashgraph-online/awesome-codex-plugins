---
name: music
description: Make songs, themes and game scores for a Homie studio with ElevenLabs Music, through the creator's OWN ElevenLabs account — a composition plan for anything sung, a transcription check that every line is actually sung, mastering to a loudness target, seamless loops and stems for games — then a song page on the studio's site. It tells the person the plan, the rights and the credit cost before anything is rendered, and never spends past the budget they set. Use when someone in a studio asks for a song, a theme song, a jingle, background music, a game score, loops or stems.
compatibility: Node 22 and ffmpeg. ElevenLabs' own CLI (elevenlabs, signed in with elevenlabs auth login) or ELEVENLABS_API_KEY, on the creator's own ElevenLabs account.
metadata:
  providers: elevenlabs
---

# Music for a studio

A studio is the folder with `studio.json` (the `studio-setup` skill makes one). Songs live in
`music/<slug>/`, listed in `music/manifest.json`; a published entry is a page at
`/music/<slug>/` on the studio's own site. Everything below runs through one script in this
skill's folder: `scripts/music.mjs` (in Claude Code:
`node "${CLAUDE_PLUGIN_ROOT}/skills/music/scripts/music.mjs" <command>`; elsewhere, the path next
to this file). Run it from inside the studio. It needs Node 22 and ffmpeg. Every command takes
`--json`.

Finish in this turn: a render is one call that usually returns in a minute or two. Only stop early to
ask the person something (the go-ahead on the cost, a budget, an install).

## 1. The provider, only now

A studio that never makes music is never asked about ElevenLabs. **Free first:** sound effects, a
chiptune or synth theme, a game score from chords and patterns, loops and stems that cost nothing and
need no account are the `sound` skill (synthesized on this computer). Use this skill for sung songs and
produced music from a model, when the person wants that and has (or will make) an ElevenLabs account.
Check when this skill starts:

```sh
node <music.mjs> check
```

It reports the road (the `elevenlabs` CLI signed in, or `ELEVENLABS_API_KEY` in the
environment), the plan, the credits left and when they reset, whether the account can go over,
the rights that plan gives, ffmpeg, and whether the studio's site has song pages.

Not connected? Offer ElevenLabs' own tools, never a copy of anyone's key or code:

- **The official CLI** (what this skill uses for music): `brew install elevenlabs/tap/elevenlabs`
  (or `npm install -g @elevenlabs/cli`), then `elevenlabs auth login`. It opens ElevenLabs in the
  browser; the person signs in once and the sign-in stays in the OS keychain. Nobody pastes a key.
  The person approves the install. An older CLI works; `brew upgrade elevenlabs` keeps it current
  (1.4.0 on 2026-09-25).
- **Or their own API key** from https://elevenlabs.io/app/developers/api-keys, set as
  `ELEVENLABS_API_KEY` in the environment Claude or Codex runs in. Never ask them to paste it
  into the chat and never write it into the studio.
- **ElevenLabs' plugin** for Claude Code (`/plugin marketplace add elevenlabs/plugin`, then
  `/plugin install elevenlabs@elevenlabs`; in Codex `codex plugin marketplace add elevenlabs/plugin`)
  brings their own skills and their hosted MCP (`https://api.elevenlabs.io/v1/mcp`, signed in on
  ElevenLabs' page: speech, voices, transcription, agents). Their skills alone: `npx skills add
  elevenlabs/skills`. It is optional here, and their MCP has no music tools: songs, stems and the
  lyric check go through this skill's script, which keeps the budget, the receipts and the rights.
  Their speech and sound-effect tools spend the same credits: tell the person the cost first, and the
  Homie mod (Claude Code) and Homie's hooks (Codex) hold a generating tool (an `estimate_only` call is free).

Prefer the CLI to a raw API call or a pasted key; never call ElevenLabs' API with `curl` for a song
(the same request twice is twice the bill, and nothing records it).

No ffmpeg: offer `brew install ffmpeg` (macOS) or the system package; the person approves.

## 2. Say the plan and the rights, plainly, before anything is made

From `check`, tell the person in two or three lines: the plan (tier), the credits left, and what
the plan allows. ElevenLabs' terms: **the free plan has no commercial licence** (no ads, sales or
monetised channels, and published copies credit "Eleven Music"); **paid plans include a
commercial licence** (not for Beta features) under their Terms and Prohibited Use Policy. The plan
**at render time** is what counts, and every render records it. Details:
`references/RIGHTS.md`.

## 3. Write the song

Write `music/<slug>/spec.json` (shape and a full example: `references/COMPOSITION.md`): tempo,
key, global styles and what to avoid, and sections in whole bars, each either instrumental or
with its sung lines. Then:

```sh
node <music.mjs> plan <slug> --spec music/<slug>/spec.json
```

It builds the composition plan (every section a whole number of bars, so section starts are bar
lines that loops and video cuts can land on), checks ElevenLabs' limits (each section 3 s to
120 s, lines up to 200 characters) and quotes the cost.

- **Anything sung goes through the plan's sections.** A prompt with lyrics beside it has come
  back with nothing sung; `render --prompt` refuses words for that reason.
- A theme or a song: the hook inside the first 10 seconds, one or two sung lines per bar at
  most, simple words that sing clearly.
- A game score: instrumental, a steady tempo, sections of 4, 8 or 16 bars that can each loop.
- Describe sound, not artists: no "in the style of" a real singer or band, no real person's name
  or voice (ElevenLabs refuses them, and they are not ours to use).

## 4. Price it, get the go-ahead, render once

```sh
node <music.mjs> quote --seconds <s> [--vocals] [--budget <credits>]
```

About **27.5 credits per second** of `music_v2` (measured on a paid account; every render then
records what it really cost, read off the account before and after). Tell the person the cost and
ask for the go-ahead and a cap. Then:

```sh
node <music.mjs> budget <slug> --cap <credits they agreed to>
node <music.mjs> render <slug> --dry-run      # free: the CLI validates the request and sends nothing
node <music.mjs> render <slug> --yes          # the one paid render
```

- `render` refuses with no budget, refuses anything that would pass the cap, and asks again
  without `--yes`. If the ask costs more than the cap, say so and offer what fits: the longest
  length within it (`quote --budget` works it out), or a shorter section that loops honestly to
  length (a loop, called a loop). Never raise a cap yourself.
- ElevenLabs' balance can take a minute to show a render (measured: unchanged right after,
  +445 a minute later). `render` waits up to 40 s for it; if it has not moved, the quote is
  counted against the cap and the receipt is marked pending. `node <music.mjs> reconcile <slug>`
  a minute later writes the real number. Never report a pending cost as zero.
- Never re-send a failed render on your own: the same request twice is twice the bill. A render
  that was sent and never answered leaves `work/render-<n>.pending`; the script refuses to send
  again until the person has looked at their ElevenLabs history and agrees (`--again`).
- Never buy credits, never change the plan, never turn on usage-based billing.

## 5. Check that every line is sung

```sh
node <music.mjs> lyrics <slug>
```

ElevenLabs' own speech-to-text (Scribe) listens to the render, and every planned line is
matched against what it heard, in order. A line passes at 75 % of its words (sung contractions
drift: "I'll" comes back "I"). A **MISS** is a line the model did not sing, or sang as something
else. Tell the person; the fix is a simpler line (the key word on a strong beat, fewer syllables)
and another paid render, which needs their go-ahead. Update the lyrics shown on the page to what
is actually sung.

## 6. Master it

```sh
node <music.mjs> master <slug>                       # -14 LUFS integrated, -1 dBTP: the web and streaming
node <music.mjs> master <slug> --lufs -18 --tp -1.5   # a bed under game sound effects
node <music.mjs> analyze music/<slug>/<slug>.mp3      # duration, loudness, tempo, first beat
```

Two-pass loudness, then a limiter, measured after on both the WAV master (kept off the site) and
the mp3 the page plays. Listen-worthy numbers go in your report, not adjectives.

## 7. Loops and stems for games

```sh
node <music.mjs> loop <slug> --bars 8 --from-bar 4    # a seamless loop cut on bar lines, WAV + OGG
node <music.mjs> stems <slug> --yes                   # paid, priced by measurement; ask first
```

The loop is cut at the song's measured bar lines, the tail crossfaded into the head, and checked:
the jump at the wrap against the music's own sample steps, and the beat grid of the loop played
three times. Never ship a loop as mp3 (encoders pad the ends with silence). Using loops in a
game: `references/GAME-AUDIO.md`.

## 8. The page

```sh
node <music.mjs> add <slug> --title "<Title>" --blurb "<one line>" [--for-game <game id>] --publish
node <music.mjs> publish <slug>
```

`add` writes the manifest entry from what is in `music/<slug>/` (the mp3 the page plays, the
master kept off the site, loops and stems offered for download, the lyrics, the plan and rights
at render time, the credits line). `publish` rebuilds and redeploys the site and checks the
page answers 200 and the audio answers a byte range. Without storage the site serves the song
itself (a song is a few MB; the limit is 25 MiB a file). A studio that has storage (`storage add`)
keeps its big media in its own R2: the deploy uploads the song (over 1 MiB, or left out of git),
reads it back, checks it by SHA-256 and serves it from R2 at the same address. If the studio is
not online yet, use the `publish` skill first. If `check` says the studio's `@homie-rocks/studio`
predates song pages, say so and update it.

## 9. Tell the person

Four or five lines: the page link, the length, the credits it cost (measured) and what is left,
the plan and whether it may be used commercially, the lyric check result, the loudness. Commit
`music/` in the studio (the big audio files stay out of git by the studio's `.gitignore`; the
manifest, spec, plan and receipts go in).

## Never

- Never print, paste or store a key; never ask for one in chat.
- Never render without the person's go-ahead on the cost, and never past their cap.
- Never claim rights the plan did not give, and never drop the "Eleven Music" credit on a
  free-plan render.
- Never imitate a real artist, voice or person.
