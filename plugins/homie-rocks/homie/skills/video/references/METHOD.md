# A music video (or a cutscene) from generated footage

The method: the generated clips are the motion; a hand-built JavaScript drawing is the picture;
the words are a main event, not subtitles; everything sits on the song's beat grid, and nothing
ships until a frame-by-frame check says the mouths, the words and the hits land.

## 0. The song and the grid

The song comes from the `music` skill (its render keeps every sung word's time). Then:

```sh
node <video.mjs> grid <slug> --song <music slug>
```

`videos/<slug>/grid.json`: the tempo, every beat, every bar line, the sections of the song's
plan with their start times, and every sung word (`w`, start `s`, end `e`, in seconds of the
song). The model's own word stamps ran 50 to 80 ms after what is heard on some words, so `grid`
moves each word to the vocal onset nearest its stamp (the original stays in `stamp`), and lyric
type then pops on the consonant. Plan everything in these numbers.

## 1. A style sheet

`videos/<slug>/STYLE.md`, one page, before any image is made:

- **The risk.** One real aesthetic decision the video is built around (a limited palette with a
  meaning, a print process, a camera rule). Not "cinematic", not generic AI gloss.
- **Palette** as hex values and what each colour stands for; **line** (weight, texture); **type**
  (two or three faces, each with a job: the big hits, the quiet lines, the machine voice).
- **What never appears**: real people, logos, brands, copyrighted characters, text in the
  generated images (models misspell it; type is drawn later).

## 2. Character and set sheets

One image call per sheet (the `gen` command with an image model; prices are per image or per
megapixel). A character sheet is one invented person or creature on a plain ground: front,
three-quarter and profile, their palette, one prop that tells who they are. A set sheet is a
place, empty, lit the way the style says. Look at each; redo the ones that break the style before
anything moves. Keep the prompts in `videos/<slug>/prompts/`.

## 3. The shot list on the grid

`videos/<slug>/SHOTS.md`: one row per shot with its bar range and times from `grid.json`, the
lyric it carries, what is seen, which sheets it uses, and whether it is a **performance** (a
character sings: needs the song as an audio reference) or a **picture** shot (motion only). Cuts
land on bar lines (or beats in a fast section). Characters on one side of the frame, words on the
other. Price the whole list before generating anything: shots x price, against the budget.

## 4. Bases

For each shot, a clip from a reference-to-video model (Seedance 2.5 on fal:
`bytedance/seedance-2.5/reference-to-video`; read its schema with the fal MCP
`get_model_schema`). A performance shot:

```json
{
  "prompt": "Flat cel-shaded animation in exactly the style of @Image1. The singer from @Image2 sings the vocal of @Audio1 with precise lip sync, mouth closed when @Audio1 is silent. Static camera. No text appears. One continuous shot.",
  "image_urls": ["@file:work/keyframes/s03.png", "@file:work/sheets/singer.png"],
  "audio_urls": ["@file:work/audio/s03.wav"],
  "resolution": "480p",
  "duration": "6",
  "aspect_ratio": "16:9",
  "generate_audio": true
}
```

- The audio reference is exactly the shot's slice of the song:
  `node <video.mjs> slice <slug> --from <shot start> --to <shot end> --out work/audio/<shot>.wav`.
- Always an explicit `duration` (a whole number of seconds that covers the shot): "auto" cannot
  be priced, so `gen` refuses it.
- 480p or 720p is enough under a draw-over; 1080p costs about twice 720p and is only worth it
  where the base itself is seen.
- Picture shots: image-to-video from a keyframe, `generate_audio: false`.
- A keyframe that comes back off-style (the wrong season, a photoreal face, the subject too small
  to read a mouth) is redone before its clip is made: an image is cents, a clip is dollars.

## 5. The sync check on every base

```sh
node <video.mjs> lag <slug> --base work/bases/s03.mp4 --ref work/audio/s03.wav
```

A reference-to-video model that sings the reference plays it back in its own soundtrack, and
draws the lips against that. Cross-correlating the clip's sound with the reference (GCC-PHAT)
gives the offset: about 0 ms with a sharp peak means the lips are timed to the song by
construction. No clear peak means the clip did not use the reference: regenerate it. A clear peak away from 0
is a shift, not a failure: one 480p clip dropped the quiet half second before the first sung word
of its reference, so its sound (and its lips) ran 475 ms ahead of the song; `lag` says so and
gives the `baseStart` that puts the lips back on the song. At 120 BPM a beat is 500 ms, so
check that the peak is far above the next one before trusting a shift near a beat's length. Then look:
`film frames` the clip and check mouths at a few sung words (open on vowels, closed on m/b/p and in
the gaps). A stylised mouth (a beak, a mask) at 480p opens with the phrases rather than each
syllable; a human-like mouth at 720p syncs closer. Choose the character with that in mind.

## 6. The draw-over and kinetic type

```sh
node <video.mjs> film init <slug>                          # film/index.html, film.js, look.js, shots.json
node <video.mjs> film frames <slug> --base work/bases/s03.mp4 --id s03
node <video.mjs> film render <slug> [--from 0 --to 12]     # work/film-h.mp4
node <video.mjs> film render <slug> --mode v                # work/film-v.mp4 (1080x1920)
```

- `film.js` renders any frame as a pure function of time (`renderAt(t)`): the shot at that time,
  the base frame under it, the look, the words. `film render` photographs every frame in order in
  a headless GPU Chrome and encodes them with the song, so a render is the same film every time.
- `look.js` is the look, and it is meant to be rewritten for each video: the starting point
  prints the base as two inks on paper (halftone dots, line work, a hand-made boil twelve times a
  second, paper tooth fixed to the card) and sets the sung words big for shots marked `big`,
  quiet for `quiet`. Push it where the style sheet says.
- `shots.json`: `at` and `dur` (on the grid), `base` (the frames folder), `baseStart` (where in
  the clip to start: remap a story beat onto the lyric that needs it), `focus` (where the
  subject is, 0..1, so a crop keeps them), `type` (`big`, `quiet`, `none`) and `side` (where the
  words go, opposite the subject). `songStart` is where the song starts in the film.
- Inserts with no character (a title, a graphic moment, an object) can be drawn entirely in
  `look.js` with no base at all: a shot with no `base` gets only the paper and the type.

## 7. The sync loop

```sh
node <video.mjs> words <slug> --in work/film-h.mp4            # every sung word's frame, labelled
node <video.mjs> sync <slug> --in work/film-h.mp4 --at 4.00,8.00,12.00
```

`words` makes a sheet with one frame at each sung word's onset: the mouth and the lyric type
must match the word under it. A word lost at a cut (its first syllable before the cut) is carried
by starting that line in the preceding shot. `sync` compares the sound's onset with the
picture's change at each hit or cut: within one frame passes. Fix, re-render the range, check
again, as many times as it takes.

## 8. Contact-sheet review

```sh
node <video.mjs> sheet <slug> --in work/film-h.mp4 --every 1
```

Look at every cell: type that runs off the frame, a face under a word, a shot that reads as a
different film, a frame gone black. Then a closer look at the hook and the chorus (every half
second). Nothing is finished until the whole video has been watched this way.

## 9. Deliver and publish

Copy the finished cuts to `videos/<slug>/<slug>.mp4` (16:9) and `<slug>-vertical.mp4` (9:16),
then `add … --kind music-video --for-song <music slug> --publish` and `publish`. Credits name the
song (and its provider) and the models the footage came from.

## A cutscene

The same steps with a script instead of a song: the audio reference is the scene's dialogue or
sound design (made with the `music` skill or recorded), the grid is the scene's own timing (a
`grid.json` you write: `beats` at the story's hits, `words` from the dialogue's timing), and it
is delivered at the game's own resolution for playback inside the game (`games/<id>/public/`).
