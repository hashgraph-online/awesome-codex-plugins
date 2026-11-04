# Perspective photo wall

A masonry wall of photos and short captions, tilted back in perspective, sliding toward the camera in a seamless loop. Use it as a portfolio opener, a "made with" montage or a background under a title. 16:9, 9:16 and 1:1; 6-12 s, loops.

## How the pros do it
- Build depth with a CSS 3D scene, not fake scaling: a `perspective` on the parent, `transform-style: preserve-3d`, and the wall rotated on X. Smaller perspective = stronger distortion; anything nearer than the perspective distance is not drawn, so keep the wall's near edge behind it [35].
- Move content along the surface at constant speed (linear). Tunnel and wall demos translate a strip from one end to the other with a linear keyframe and loop it [1]; the registry tunnel runs at a fixed 3 segments/s by default [41].
- Make the loop seamless by moving exactly one repeat period (one row pitch or one full tile height) per loop, then wrapping with modulo [1][41].
- Keep type crisp while it travels toward camera: render captions as real text or SVG, not bitmaps, so they stay sharp as they scale [4].
- Fade the far end into the background (fog) so tiles appear rather than pop at the horizon [41].
- Captions on a wall are labels: caps grotesque, 14-20 px at 1080p, +0.08 to +0.12em tracking [22].
- Keep one consistent visual system for every tile (same corner radius, caption position, border) so the wall reads as one object [54].

## Presets
| Preset | Look | Key values |
|---|---|---|
| `perspective-photo-wall.gallery` | Light gallery wall leaning back, slow drift | perspective 1100 px, rotateX 58deg, 4 columns, speed 0.5 row/s, paper #F2EFE8, Inter 600 caps captions |
| `perspective-photo-wall.night` | Dark wall, photos glow slightly, faster | perspective 900 px, rotateX 62deg, 5 columns, speed 0.8 row/s, bg #0B0B0D, fog to bg over the last 35% of depth |
| `perspective-photo-wall.floor` | Wall becomes a floor seen from above, title sits on top | perspective 800 px, rotateX 72deg, rotateZ -12deg, 6 columns, speed 0.4 row/s |

## Timing and numbers
- Loop: 10 s = 300 f at 30 fps; travel exactly N row pitches (N = 3-5) so frame 300 equals frame 0.
- Speed: 0.4-0.8 row pitch per second. Faster than ~1 row/s and captions cannot be read (20 chars/s ceiling [37]).
- Tile sizes at 1920x1080 before tilt: column width 300-380 px, gutter 24 px, masonry heights from {0.75, 1, 1.33} x width (seeded).
- Camera: perspective-origin 50% 0% (vanishing point toward the top) for a wall leaning back; 50% 50% for a floor.
- Fog: opacity ramp from 1 at depth 0.65 to 0 at depth 1.0 of the visible run.
- 9:16: 3 columns, rotateX 55deg; 1:1: 4 columns.
- Title over the wall: centered lockup with a 40-60% black or paper scrim behind it.

## Build it
1. Start from the HyperFrames `gallery-tunnel` block (images slot list, fog, fixed speed) if a full tunnel is fine; for a single leaning wall, start from `perspective-marquee` [41].
2. Scene div: `perspective: 1100px; perspective-origin: 50% 0%`. Wall div: `transform-style: preserve-3d; transform: rotateX(58deg)`.
3. Lay out a seeded masonry (mulberry32 seed) twice its visible height; duplicate the first repeat period at the end.
4. On the timeline: `y = -(t * speed * pitch) % periodHeight` written in an `onUpdate` that reads `tl.time()` (no wall clock).
5. Fog: a gradient overlay in the wall's local space, or per-tile opacity from its computed depth.
6. Remotion: same structure; compute `y` from `useCurrentFrame()`.

## Mistakes that look amateur
- Tiles pop in at the horizon → extend the strip past the far edge and fade with fog.
- Visible jump at the loop point → travel an exact multiple of the repeat period; check frame 0 vs last frame.
- Perspective so strong the near tiles clip → raise `perspective` or lower rotateX; near edge must stay behind the viewer plane [35].
- Captions rasterized as images → they blur when they come close; use text/SVG [4].
- Eased (accelerating) travel on a loop → linear only.
- Random aspect ratios from source photos → crop to the 3 masonry ratios.

## Sources
[1] @jh3yy, CSS 3D tunnel — https://x.com/jh3yy/status/1732553845530566855 — rotated planes, linear travel, perspective on the scene
[4] @jh3yy, blow-out text — https://x.com/jh3yy/status/1702790661911494765 — SVG text stays crisp in z
[22] Butterick, Letterspacing — https://practicaltypography.com/letterspacing.html — caption tracking
[35] MDN, perspective — https://developer.mozilla.org/en-US/docs/Web/CSS/perspective — perspective distance rules
[37] Netflix Timed Text Style Guide — https://partnerhelp.netflixstudios.com/hc/en-us/articles/217350977-English-USA-Timed-Text-Style-Guide — reading speed
[41] HyperFrames registry, gallery-tunnel / perspective-marquee — https://github.com/heygen-com/hyperframes/tree/main/registry — fixed speed, fog
[54] Territory Studio interview — https://www.pushing-pixels.org/2014/08/07/the-craft-of-screen-graphics-and-movie-user-interfaces-interview-with-david-sheldon-hicks-of-territory-studio.html — one visual system
