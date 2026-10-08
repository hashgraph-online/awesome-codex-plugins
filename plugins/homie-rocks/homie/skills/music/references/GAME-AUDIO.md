# Music in a game

## Loops

`music.mjs loop <slug> --bars <n> --from-bar <k>` cuts `n` bars starting at bar `k` of the
mastered song, on the song's measured bar lines, and makes the wrap seamless: the music that
would follow the loop's last sample is crossfaded (30 ms, equal power) into its first. It writes a
16-bit WAV (exact length everywhere) and an Ogg (Vorbis, or Opus where ffmpeg has no Vorbis
encoder; smaller). Both decode to exactly `bars × beats × 60 / bpm` seconds.

Play it in WebAudio, never with an `<audio loop>` element (it gaps on the wrap):

```js
const ctx = new AudioContext();
const buf = await ctx.decodeAudioData(await (await fetch('/music/theme/theme-loop-8bars.wav')).arrayBuffer());
const src = ctx.createBufferSource();
src.buffer = buf;
src.loop = true;           // loopStart 0 and loopEnd 0 mean the whole buffer
const gain = ctx.createGain();
gain.gain.value = 0.6;     // under the game's own sound effects
src.connect(gain).connect(ctx.destination);
src.start();               // after the player's first tap or key: browsers need a gesture
```

- **Never an mp3 for a loop.** mp3 encoders add silence at both ends; the wrap clicks or gaps.
- Test the Ogg on an iPhone before relying on it; the WAV plays everywhere.
- To change intensity with the game (calm, chase, final seconds), make the song in sections of
  the same tempo and key, loop each, and crossfade between loops on a bar line: the next bar
  starts at `start + ceil((ctx.currentTime - start) / bar) * bar`.

## Levels

- A menu or title theme: master to -14 LUFS.
- A bed under gameplay sound effects: -18 to -20 LUFS (`master --lufs -18 --tp -1.5`), so hits
  and pickups stay on top without the game turning its own sounds up.
- Stingers (a win, a round starting): a separate short instrumental render (3 to 5 s) at the
  same tempo and key as the bed.

## Stems

`music.mjs stems <slug> --yes` asks ElevenLabs to split the master into stems (vocals, drums,
bass, other). It is paid and its price is measured off the account, so it needs the person's
go-ahead and fits inside the song's budget. Stems let a game drop the vocals under dialogue or
bring the drums in when the action starts.

## The page

A song entry with `--for-game <id>` is a score: its page links the game, and its loops and stems
are listed for download so another studio's game can use them (under the song's licence: say
what it is in `credits`).
