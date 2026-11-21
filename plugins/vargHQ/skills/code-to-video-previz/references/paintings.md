# Case B: stage a shot from a painting or a still

A painting is a solved composition: where the eye goes, where the light falls, what stays dark. Cinematographers read
paintings; they rarely copy them. "you can study where the light sources are" (Sam Mendes). John Alcott found the Dutch masters
"a bit flat" on *Barry Lyndon* and "decided to light more from the side". Vittorio Storaro talked his director out of lighting
every scene like Caravaggio, on a film about Caravaggio. Exact staging is possible and costly: Gustav Deutsch's *Shirley*
matched Hopper's pictures for "at least one frame", which took tilted furniture and a camera that couldn't move three centimetres,
because in Hopper's paintings "there are no right angles, or else two to three suns" (translated). So stage the shot, then let go of the painting.

You can still put it in a 3D scene and move a camera through it. The method below was tested on Caravaggio's *The Calling of Saint
Matthew* (`example/calling/`) and by a fresh agent on Vermeer's *The Music Lesson*. Guessing a camera and positions put key points 9
to 22% of the frame off. Placing them from the picture puts them where the picture has them, in Three.js and Blender alike.

## The method: read the picture, don't guess it

**1. Put a grid on it.** `python3 scripts/grid.py painting.jpg --out grid.png`. Read everything as (u, v), fractions of
the frame, top-left origin.

**2. Find the vanishing point first, if the picture has straight lines.** Extend floor tiles, ceiling beams or table edges that
run straight into the picture and see where they meet. Paintings rarely centre it: *The Music Lesson* has it near (.58, .45). Use
`Frame(..., vp=(.58, .45))` and put `"vp": [.58, .45]` on the shot. Skip this and sizes change across the frame: a fresh agent that
followed the method without it got the same floor tile at 0.31 and 0.33 m. A grid of known squares also gives you the lens,
instead of leaving it a choice.

**3. List what matters, in this order:** figures (head, feet, hands), big masses, the horizon or eye level, the light's
direction and its shadow edge. Note what's dark, not only what's bright. Darkness is composition.

**4. Get depth and eye height from something of known size.** A standing adult is about 1.75 m:

```python
from place import Frame
F = Frame(1000, 1028, lens=35)     # lens is a choice: start at 35 mm, go wider if the perspective is steep
d = F.depth_of(.38, .93, 1.75)     # top of head at v=.38, soles at v=.93: he stands 3.1 m away
F.eye = F.eye_from(.93, d)         # his feet tell you the camera height: 1.37 m
```

Paintings cheat on perspective, so a single solution won't fit everything. Get the main figures right and let the rest go.
It's "easy to get strapped into following it 1:1", as one painter warns.

**5. Check it against a size you didn't ask for.** This is what tells you the numbers are sane. In our test the table top,
read from the picture at v = .67 and 3.5 m deep, came out at 0.76 m: a real table.

**6. Place everything by picture coordinates.** `F.world(u, v, depth)` returns the world point that lands exactly at that spot.
Give each figure a depth from where its feet meet the floor (`F.floor_depth(v)`) or from its height.

**7. Stage poses as joints if the gesture is the point.** A pointing hand is the picture in this painting, so the
example uses `style: "joints"`. Read head, neck, hip, shoulders, elbows, hands, knees and feet off the grid.

**8. Light it with one source and cut it with flags.** The diagonal shadow across the wall makes that painting. Put a hard
spot outside the frame, then use a `flag` (a plane that casts shadow and the camera can't see) to place the edge
exactly: take two points on the wall along the edge, and put the flag's edge on the lines from the light to those points.

**9. Pin it, render it, overlay it.** A pin placed from its own reading can only confirm the maths. Keep a few points back: read
them, don't place from them, and check them. Those are your evidence.

```bash
python3 scripts/check_staging.py staging.json          # pins: where it lands vs where the picture has it
bun scripts/stage_three.ts staging.json still s01:0 still.png
python3 scripts/compare.py painting.jpg still.png --out cmp
```

Look at `cmp_overlay.jpg` first. Lined-up shapes mean the camera and staging match. Pin numbers catch position errors, and
only your eyes catch "too bright" or "wrong mood". In our test the first render had the composition but the wall too
bright: light level is a judgement call.

**10. Now move the camera.** The painting gave you a world, and a slow push-in or a drift through it is a real shot.
Keep moves small: the further you travel, the more the cheated perspective shows.

## What to take from a painting

| read this | stage it as |
|---|---|
| where the light comes from, how high, how hard | key `pos`, `soft` (Blender only: three.js shadows stay hard), colour. Rembrandt: high 45°, one side. Caravaggio: hard, high, side-on, deep black fill. Vermeer: soft window side-light, which needs Blender, or accept a hard patch. A window seen from inside: a box with `unlit: true` |
| the shadow edges | flags |
| what's dark | fill near 0, dark greys on the figures' clothes, no hemisphere light |
| the palette | sampled colours (and `"tone": "none"`, because AgX desaturates), and a look line in the prompt rather than an adjective. Reproductions vary: Deutsch found they "deviate far too much" and matched from originals |
| the eye line | which way each head and hand points. Check it in the overlay |
| depth layers | foreground, middle, back. Keep them at real, different depths so a camera move produces parallax |
| the empty space | keep it empty. The urge to fill it is what makes a blockout look generic |

## Getting from the staging to a finished look

The grey render approves composition and light. For the look:

1. **Image-edit the render into a plate:** send the still as the first file with the painting as a reference ("keep the
   camera, geometry and light direction exactly; repaint with the materials, costume and palette of the second image").
   The approved result is your master plate and start frame.
2. **Animate from that plate,** with the grey clip as `@video1` for the camera (`references/handoff.md`).
3. **Keep light out of the guide clip:** `--flat`. The light reaches the model through the plate and the prompt.

A painting straight into a video model is a gamble: as a first frame, *The Last Supper* drifted toward photoreal while
*Starry Night* held its style, in promoted showcases. Naming a look is unreliable too. In the one test found, backlight, silhouette and rim
read; Rembrandt, chiaroscuro and bottom light did not. Describe the light as direction, softness and ratio. Rough
beats finished here as well: "Do not feed in a finished, beautiful storyboard" (Ryuki Yano, translated), because the model makes a "moving storyboard" of it.

The staging method above is tested. The plate and animation steps follow the standard still-to-video route, untested on paintings by us.

## Matching a real photograph

For architecture or a real location use **fSpy** (free, reads vanishing points off a photo and exports a camera to
Blender) in place of steps 3 and 4 when the picture has straight lines. Then model the room in Blender around that camera. It also
works on art and sketches, with hand fixes. The importer has conflicting reports on Blender 5; lzandman's fork is the lead we found, untested.
