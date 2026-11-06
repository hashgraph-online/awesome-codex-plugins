# Look blockout (optional): reference pictures on the grey set

The animatic is a grey-box on purpose: it approves camera and blocking, and its greyscale export is the `@video1`
reference for Seedance. A look blockout is a separate, optional pass on top of the same set: reference pictures
and generated matte paintings go onto the grey geometry as textures, one still per shot is rendered and compared
side by side with its reference, and the person approves the look as stills, for free, before anything is
animated or paid for. Geometry, cameras and blocking stay code; only materials change.

The strongest code-built videos we studied worked this way: the reference picture set the look, the geometry was
three.js code, and one still was compared with the picture and fixed for 3 rounds before the film was touched
([x.com/0x_fokki](https://x.com/0x_fokki/status/2116289885870981296),
[x.com/elvar_official](https://x.com/elvar_official/status/2116192984299344372)). "Give it a video reference and
it can build the experience directly in three.js or Blender. Then keep improving the details, textures, and
lighting" ([x.com/MengTo](https://x.com/MengTo/status/2092275643623109037)).

## When to use it, and when not

| situation | look blockout? |
|---|---|
| the animatic itself is the film (3D product shot, explainer, render path B) | **yes**: this is how it stops looking like a toy |
| the look is still open and generation will cost real money | **yes**: approve the look as stills first, then spend |
| a Seedance video-to-video run | **no** for `@video1`: send the plain grey export (`--grey`). The look goes in as image references and the `Look:` line of the prompt |
| camera and blocking are not approved yet | not yet: fix the grey-box first, a texture hides framing problems |

**Never send a textured render as the greyscale `@video1` unless that is deliberate.** A colour previz once came
back from Seedance unchanged, as the output (see `seedance-v2v-pack.md`); a textured one invites the same. The
look render and the v2v reference are two different files: `renders/look/…` and `renders/look_*.mp4` versus
`renders/run_*.mp4 --grey`.

A look still is a good input for an image edit, though: render it, then edit it with `gpt_image_2_5` or
`nano_banana_2_1` on varg with the render as the first file ("keep the camera and the geometry exactly"), as in
`sets-and-blocking.md`. The approved edit becomes the master plate and an image reference for the run.

## What to texture

Few surfaces, the ones that carry the look:

- **Backgrounds**: a matte painting or a generated backdrop behind a window, a sky, a far street, a horizon. This
  is the biggest win per minute: the background fills most of a wide frame.
- **Ground**: the floor, a road, grass, tiled at a real-world scale so the size of the place reads.
- **A few hero surfaces**: the wall the dialogue plays against, the counter, the product's own surface.

Leave the mannequins grey (identity comes from character sheets, never from the previz) and keep labels off.
Sources: the moodboard and reference frames for the project, crops of approved stills, or a backdrop generated
for the purpose (a wide plate with no hero action, the same light direction as the set's key light).

## The starter's hook: `js/look.js`

Off by default. The review UI and `?export=1` render the grey film exactly as before (the stills and the
greyscale run clip stay byte-identical). Turn it on with `?look=1`, or `bun tools/capture.ts --look`.

```js
// js/look.js — one entry per image; images in assets/look/, loaded before the first frame
export const LOOK = [
  // matte painting behind the window; the grey 'street' blocks it replaces are hidden in look mode only
  { backdrop: 'skyline', url: 'assets/look/street_matte.jpg', size: [24, 10], pos: [0, 3, -12], hide: ['street'] },
  // the floor, tiled 4 × 4 across its 8 m
  { surface: 'floor', url: 'assets/look/floor_planks.jpg', repeat: [4, 4] },
  // a hero surface that shows the picture's own colours, unaffected by the set lights
  { surface: 'counter', url: 'assets/look/counter.jpg', lit: false },
];
```

- `backdrop`: a new unlit plane (`MeshBasicMaterial`, no fog), `size` in metres, `pos`, optional `rot` (radians).
  It faces +Z, toward cameras that look down −Z; rotate it for other walls. Put it far enough behind the opening
  that a small camera move gives parallax, and big enough to cover every frustum that sees it (check the map).
- `surface`: any set element by `S.o` key or object `.name` (the demo names `floor`, `wallL`, `wallR`, `pillar`,
  `counter`, `street`, `room`). Every mesh under it gets a cloned material with the image as its map, so shared
  materials (all walls use one) change only where you asked. `repeat: [u, v]` tiles it.
- `hide`: names of grey stand-ins the picture replaces. Hidden only in look mode.
- A missing file or an unknown name stops the page with `look: cannot load …` / `look: no set element named …`
  instead of rendering a silent grey frame.

Images load once, before `__ready`, so the seek-safe contract holds (`bun tools/check.ts` still proves it).
Commands:

```bash
bun tools/capture.ts --look --stills                 # renders/look/<shot>_{a,m,b}.png
bun tools/capture.ts --look --shots s01               # renders/look_run_s01.mp4, a code-rendered look clip
# http://localhost:8777/?look=1                      the review UI with the look on
```

`--look --grey` prints a warning: it is a textured render, not the grey-box reference. The HyperFrames builder
(`tools/make_hf.ts`) still renders the grey film; to render the look there, copy `assets/look/` into `hf/`,
create the film with `createFilm(edits, { look: true })` and hold the first render on `film.ready` (register it
on `window.__hf.buildReady`, see `seek-safe-rendering.md`).

Keep large images out of git, as for any media; the starter's `.gitignore` does not cover `assets/look/`.

## The loop: still vs reference, up to 3 rounds

1. Render one still per shot with the look on (`--look --stills`; the middle frame `_m` is usually the one).
2. Put each still next to its reference at the same height:
   ```bash
   ffmpeg -i renders/look/s01_m.png -i refs/s01_ref.jpg \
     -filter_complex "[0]scale=-2:720[a];[1]scale=-2:720[b];[a][b]hstack" renders/look/s01_vs_ref.png
   ```
3. LOOK at the pair and write the gaps as a list, in concrete terms: palette and value range, light direction and
   softness, how much of the frame is background, texture scale, what is missing. Do not grade the still as a
   whole ("looks good"); name what differs.
4. Fix the gaps, **one area at a time** (the background, then the ground, then one hero surface), re-render,
   compare again ([x.com/zavrenn](https://x.com/zavrenn/status/2116564845860360225)). Changing everything at once
   makes it impossible to tell which change helped.
5. Stop after 3 rounds per shot, or earlier when the pair matches. Then show the pairs to the person on a still
   board and get approval per shot. A note here costs a re-render; the same note after generation costs a run.

**Detail pass.** If the first version "looks like a toy" (flat colours, empty walls, every surface the same
roughness), do a detail pass before the next comparison: textures on the big surfaces, a light that matches the
reference's direction and softness, a few small props that give scale (a plant, a lamp, a sign without text).
Still one area per round. For a v2v run keep these details out of the grey-box: say them in the prompt instead
(the grey-box rules in `SKILL.md` stand).

**Motion, for a code-rendered final.** When the look render is the film, check that something changes every
2–3 seconds (a note from the same code-built films): a cut, the shot's one camera move, or a blocking beat. This is the existing grammar (cuts on bar
lines, one move per shot, one clear action per shot) read as a pacing check: at 120 BPM a bar is 2 s, so cutting
or landing an action on every bar already does it. A long stretch where nothing changes reads as a frozen frame.

## Related

- `sets-and-blocking.md`: the master set and the plate made from the blockout render.
- `seedance-v2v-pack.md`: why `@video1` is greyscale and how the look reaches Seedance instead (image references,
  the `Look:` line).
- `seek-safe-rendering.md`: the determinism contract the look pass keeps (load before the first frame).
- The `varg-mockups` skill: still boards for approval before animation.
