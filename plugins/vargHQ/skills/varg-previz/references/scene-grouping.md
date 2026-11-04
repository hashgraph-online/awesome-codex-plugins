# Grouping shots into master scenes and runs

## Why

Every AI generation re-invents the world. If a location's wide and its close-ups come from different runs with
different refs, the layout, the face and the light drift. Group by location so each place is generated from one
master plate, ideally in one multi-shot run with hard cuts.

## How

1. Tag every storyboard shot with `scene` = location + lighting state, e.g. `A_cafe_day`, `A_cafe_night` (same set,
   different light), `B_street`, `C_studio`, `reuse_*` for existing clips. Tag `set` = which 3D set frames it.
2. Shots of one scene do NOT need to be adjacent on the timeline. Generate them together, then cut them back in
   (in the music video, the cockpit run h01 v03 v04 v05 v06 is interleaved with space shots in the edit).
3. Split each scene into **runs of 4–11 s** (Seedance accepts 4–30 s, but short runs keep motion obedient and retakes
   cheap). Keep shots in timeline order inside a run. If the sum is not a whole number of seconds, pad the LAST shot
   with a tail handle (the previz renders past the shot end; the tail never goes in the edit). Minimum 4 s.
   `scripts/new_previz.py` pre-groups runs this way into `previz/seedance/pack.json`; adjust by hand.
4. Merge runs when the director wants one continuous scene (two 5 s runs → one 10 s run): fewer seams, same price.
5. Mark reuse shots (`source: "reuse"` or pack `reuse`); they cost nothing and are in no run. Mark shots made
   entirely in code (`source: "code"`, e.g. a title card) the same way.
6. Name reference clips by run: `video_06__D__p15-c16-c17.mp4` (pack index, run key, shots). The index stays the same
   when you build only some runs.

## Scene table (keep it in scenes.md)

| scene | shots | cut time | gen | refs |
|---|---|---|---|---|
| A café | s01 s02 | 3.5 s | 4 s | woman sheet, café master |
| B street | s03 s04 | 4.5 s | 5 s | walker sheet, street master |
| C studio | s05 s06 | 4.0 s | 4 s | product sheet, presenter sheet |

The pack's `PROMPTS.md` also stores, per run, the placement table (shot → in-clip range → timeline time) so the
editor can drop clips onto the grid.

## Rewrites

When the director changes the story: update the storyboard entries (picture, action, camera, scene,
`needs_new_still`), the scene table and cost, the treatment, the previz shots and the pack runs, and log the verbatim
note, all in one pass.
