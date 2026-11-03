# Camera language for a three.js animatic

How to turn "MCU, slightly low, slow push in on 50 mm" into START/END keys, and back into words for the camera
plan and the video prompt. The starter's `js/camera.js` implements every formula here.

## The camera key

`{ p: [x, y, z], t: [x, y, z], fov: vertical degrees, roll: degrees }`, in metres, +Y up.

- **Put the target `t` on the subject** (the eyes of a person, the middle of a product). Shot size is measured at
  the target distance, orbit and dolly pivot on it, and the frustum on the map then points at something real.
- Eye height of a standing adult ≈ 1.65 m, seated ≈ 1.2 m. "Eye level" means the camera is at the subject's eye
  height, not at 1.6 m by default.
- A shot has two keys, START (a) and END (b), an ease and a path. One move per shot. Two moves in a row are two
  shots, or one shot with a cheat (see sets-and-blocking.md).

## Shot size

Size = frame height at the subject = `2 · |t − p| · tan(fov / 2)`. Thresholds for a person (the starter's
`sizeOf`):

| size | frame height at the subject | shows |
|---|---|---|
| ECU, extreme close-up | < 0.2 m | eyes, a hand, a detail |
| CU, close-up | < 0.4 m | the face |
| MCU, medium close-up | < 0.7 m | head and chest |
| MS, medium shot | < 1.1 m | from the waist up |
| MLS, medium long shot | < 1.5 m | from the knees up |
| FS, full shot | < 2.4 m | the whole body with a little room |
| WS, wide shot | < 8 m | the person in the place |
| EWS, extreme wide | ≥ 8 m | the place, the person is small |

For an object, divide by its height ratio: a 0.3 m bottle has `refScale = 0.3 / 1.8 ≈ 0.17`, so "CU bottle"
means the bottle fills the frame. A vehicle or creature uses its own height the same way; otherwise a close shot
of a 9 m ship is labelled "extreme wide" because it is measured against a person.

**Frame tighter than you want.** Seedance video-to-video came back looser than the previz (a CU became a medium
shot). If the size matters, go one size tighter in the previz.

## Angle

From the pitch of the view direction: below −60° top shot (bird's eye), −60° to −15° high angle, −15° to +15° eye
level, +15° to +60° low angle, above +60° worm's eye. A roll over 5° is a dutch angle. Low angles make a subject
bigger and threatening, high angles smaller; keep eye level as the default and spend angles on story beats.

## Lens ↔ FOV

Full-frame equivalent with 36 mm on the LONG side of the frame (landscape and portrait alike). three.js wants the
vertical FOV:

| lens | 16:9 vertical FOV | 16:9 horizontal | 9:16 vertical | 9:16 horizontal |
|---|---|---|---|---|
| 14 mm | 71.7° | 104.3° | 104.3° | 71.7° |
| 18 mm | 58.7° | 90.0° | 90.0° | 58.7° |
| 24 mm | 45.7° | 73.7° | 73.7° | 45.7° |
| 28 mm | 39.8° | 65.5° | 65.5° | 39.8° |
| 35 mm | 32.3° | 54.4° | 54.4° | 32.3° |
| 50 mm | 22.9° | 39.6° | 39.6° | 22.9° |
| 65 mm | 17.7° | 31.0° | 31.0° | 17.7° |
| 85 mm | 13.6° | 23.9° | 23.9° | 13.6° |
| 100 mm | 11.6° | 20.4° | 20.4° | 11.6° |
| 135 mm | 8.6° | 15.2° | 15.2° | 8.6° |

`fovFromMM(mm, aspect)` and `lensMM(fov, aspect)` in `camera.js` do the conversion. What lenses mean on screen:
18–24 mm wide, close and dynamic, distorts faces near the edge; 35 mm the natural "film" lens for wides and
mediums; 50 mm neutral; 65–85 mm portraits and over-the-shoulder singles, flattens the background; 100 mm+ long
lens, compressed, voyeuristic. Choose the size by moving the camera and the look by the lens: a CU on 24 mm and a
CU on 85 mm are the same size with a different face and background.

## The narrow frame (check it, do not guess)

Horizontal half-FOV = `atan(tan(vFOV / 2) · W / H)`. In 9:16 at vFOV 55° the horizontal half-FOV is only 16°: a
subject 17° off the camera axis is out of the frame. In a real 36-shot vertical previz, a seated character's head sat 33°
below the camera axis with a vertical half-FOV of 30° and disappeared; a wide lost both subjects; an
over-the-shoulder camera stood behind a headrest; another stood inside a bulkhead and showed only the wall. The starter's `checkShot` warns for subjects out of frame, on the
edge, blocked by geometry, and for a camera inside geometry. Look at the set map for every shot anyway.

## Moves and how to key them

| move | START → END | ease, path |
|---|---|---|
| static / locked off | same keys (or `ease: 'hold'`) | — |
| push in / pull out (dolly) | `p` moves along the view direction, same `t`, same lens | inOut, line |
| zoom in / out | same `p` and `t`, `fov` changes | inOut |
| dolly zoom (vertigo) | push in while the FOV widens so the subject keeps its size | linear |
| truck (side) | `p` and `t` move sideways together | inOut, line |
| crane / pedestal up, down | `p.y` (and usually `t.y`) changes | inOut |
| pan / tilt | same `p`, `t` swings left/right or up/down | inOut |
| orbit / arc | `p` moves around a fixed `t` | **path `arc`** (a straight line cuts the corner toward the subject) |
| follow / track | `t` follows the subject's path; key START and END where the subject is | linear |
| whip pan | big `t` change in a short shot | whip |
| handheld / impact | add `shake: [localSeconds]` (deterministic sines, decays in 0.4 s) | — |

Eases: `inOut` for most moves, `out` for a move that settles on the subject, `in` for one that leaves, `linear`
for tracking and constant drift, `hold` to stay on START. A crane up with a tilt down (like the starter's s03)
keeps a landing object centred while the camera rises.

## Coverage and cutting

- **The 180° line.** Draw the line through the two people talking (on the map). Keep every camera of the scene on
  one side, or A and B swap screen sides between cuts and the audience loses who looks at whom. The map shows it
  at a glance: all frustums of the scene start on the same side of the line.
- **Eyelines.** In shot/reverse shot, A looks screen right and B looks screen left. A head turn toward something
  off screen (the window) must match where that thing is in the wide.
- **30° rule.** Two consecutive shots of the same subject should differ by at least 30° of angle or one shot size,
  or the cut looks like a jump.
- **Cut on action or on the beat.** Put cuts on bar lines of the music, and let an action that starts in one shot
  finish in the next (block it once in world time and both shots show the same moment).
- **Vary the coverage.** If the existing stills are all frontal medium shots, the previz is where you decide the
  over-the-shoulders, profiles, inserts and low angles. Review notes on one music video were exactly that: every
  shot in the main location looked the same.
- **One clear action per shot.** Notes from real reviews: "make it clearer that the music is the weapon", "the
  pause between these scenes is too long", "the antagonist must be visible at 20 s or the story drops". Each one is
  cheap to fix in the animatic and expensive after generation.

## Writing the camera in prompts

Per shot, in absolute seconds from the clip start: `1. 0.0–4.0 s. Wide, eye level, slow push in: <action>.`
Size + angle + move, then one action. The camera plan's `size`, `angle`, `lens` and `move` columns are written for
this. State scale in words when a model might get it wrong ("the drone is about half a metre across, much smaller
than a person").
