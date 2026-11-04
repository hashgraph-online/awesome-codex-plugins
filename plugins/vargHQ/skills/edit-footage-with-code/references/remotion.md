# Editing footage in Remotion

Install the official skills in the video project: `npx skills add remotion-dev/skills`. They cover the API, and since Remotion Skills 2.0 they deliberately carry no design direction: "slides" are Claude's default, not Remotion's (@JNYBGR). So taste comes from your style file and references, not from the engine.

Remotion needs a paid company license above 3 employees. Check before committing a client project.

The split in public reports: many people cut in an editor or ffmpeg and use Remotion only for overlays (@JJEnglert, @SimonHoiberg, @okuyama_ai_, @darrrragh). Others edit whole talks in it (@TassyOmah_'s 3-camera podcast; @JNYBGR). Both work. Cutting first is the safer default. Remotion's timeline, launched 2026-11-03, lets a person trim by hand and writes the change back as React code.

## Put the cut in a project

`build_cut.py` writes `edit/Cut.tsx`. Copy the source take to `public/`, then:

```tsx
import {Composition} from 'remotion';
import {Cut, CUT_FRAMES} from './Cut';

export const RemotionRoot = () => (
  <Composition id="edit" component={Cut} durationInFrames={CUT_FRAMES} fps={30} width={1920} height={1080} />
);
```

Set `fps` and size from the probe. Current API, checked against the docs on 2026-11-03:

- Use `<Video>` from **`@remotion/media`**. Older posts say "use `<OffthreadVideo>`, never `<Video>`". They mean the old `<Video>` from `remotion`, and `<OffthreadVideo>` still works.
- `trimBefore` and `durationInFrames` are in **frames**. `trimAfter` and `startFrom` are deprecated.
- Conform phone footage first, or it judders: `ffmpeg -i in.mov -vf fps=30,format=yuv420p -fps_mode cfr out.mp4`. Never `-r 30` (@eliana_jordan).
- Prefer a single `acut.mp4` with one `<Video>` when the cut is locked. Keep many clips when a person will keep trimming in the timeline.

## The clock

Put one timing file in the project and derive everything from it (@trq212, @rameerez):

```ts
// src/timing.ts: a generated file, from the cut's own transcript
export const FPS = 30;
export const W = {price: 412, until: 88} as const;      // word indexes you cue from
export const at = (word: number) => Math.round(words[word].start * FPS);
```

Build a cue sheet of `{id, at, dur}`. No frame number appears as a literal in a component, or one early change breaks every later scene. Put a shot's video, captions and overlays under one `<Sequence>`, so moving it moves them together.

Captions: `@remotion/captions` and its `Caption` format, with `createTikTokStyleCaptions` for word-by-word. Convert from your transcript rather than transcribing twice: `{text, startMs, endMs, timestampMs: null, confidence: null}`.

## Taste you must supply

Remotion's defaults look like slides, and this is the top complaint across languages (@VincentWei93, @rrrusxx, @rameerez). What helps, in the order people report it:

1. A reference clip rather than a style name (@rexan_wong).
2. Each element enters on its own word. Nothing arrives as a full page (@bozhou_ai).
3. One still per scene, approved, before any animation.
4. No two consecutive scenes share an entrance, durations vary, and text enters by word (@shintaro032).
5. Every animation is driven by `useCurrentFrame()`. Web components with their own clock break on render.

## Overlays as separate files

For a person finishing in Resolve or Premiere, render graphics with true alpha:

```bash
npx remotion render edit out/overlay.mov --codec prores --prores-profile 4444 --pixel-format yuva444p10le --image-format png
```

All four flags matter (@eliana_jordan).

## Check it

```bash
npx remotion still edit --frame=240 out/f240.png      # one frame, before any video
npx remotion render edit out/draft.mp4 --scale=0.5    # a low-res draft for review
python3 <skill>/scripts/qa_cut.py out/draft.mp4 --heard heard.json --intended edit/intended.json
```

Judge the exported MP4, not the Studio preview (@eliana_jordan). One 4K render took over 10 minutes and revealed a blank middle section (@bozhou_ai), so sample frames before the final.

## Known limits

- Fine corrections on real footage are contested: @ma_shi_onoda (12 years on YouTube, self-stated) and @okuyama_ai_ keep an NLE for client work.
- Expect 20-30 messages for a simple video on a new setup (@SelmanKahyaX), and 2-3 days for a polished film (@rameerez). One-prompt claims have been corrected in public, including by Remotion's maker.
