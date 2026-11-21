# HyperFrames: HTML, CSS and GSAP to MP4

HyperFrames renders a web page frame by frame in headless Chrome and encodes the frames to video. You write HTML and CSS for the look and a paused GSAP timeline for the motion; the renderer seeks that timeline to every frame and takes a screenshot. Because it seeks rather than plays, anything that depends on real time (timers, `requestAnimationFrame` loops, the clock) will not show up the way you expect. Drive everything from the timeline.

Docs: https://hyperframes.heygen.com (machine-readable index at `/llms.txt`). Offline: `npx hyperframes docs <topic>` with topics `data-attributes`, `gsap`, `compositions`, `rendering`, `examples`, `troubleshooting`.

## Start a project

```bash
npx hyperframes init my-video --example blank --non-interactive --skip-skills
# or, inside a folder you already made for the video:
npx hyperframes init . --example blank --non-interactive --skip-skills
cd my-video
```

This writes `index.html` (the root composition), `hyperframes.json`, `meta.json` and `package.json`. Add `--resolution portrait` for 1080x1920. `--skip-skills` stops `init` from installing HyperFrames' own agent skills into the user's skill folders; leave it off only if the user wants them. `init` still writes its own `AGENTS.md` and `CLAUDE.md` into the project folder: they are HyperFrames' notes for agents, harmless, and you can delete them if the user does not want them.

## The composition contract

```html
<div id="root" data-composition-id="main" data-start="0" data-duration="12"
     data-width="1920" data-height="1080">
  <h1 id="line1" class="clip" data-start="0" data-duration="12">Ideas are cheap.</h1>
</div>
<script>
  const tl = gsap.timeline({ paused: true });
  tl.fromTo("#line1", { opacity: 0, y: 60 }, { opacity: 1, y: 0, duration: 0.6, ease: "power3.out" }, 0.2);
  window.__timelines = window.__timelines || {};
  window.__timelines["main"] = tl;
</script>
```

- The root element carries `data-composition-id`, `data-start`, `data-duration`, `data-width`, `data-height`.
- Every timed element has `data-start` and `data-duration` (seconds) and the class `clip`.
- Register exactly one **paused** root timeline per composition in `window.__timelines["<composition-id>"]`. Child timelines you nest into it must not be paused, or they will not move when the root is seeked.
- Timeline positions are seconds from the start of the composition. Keep a comment block at the top of the script that lists the beat sheet times; it makes fixes fast.
- **Vendor GSAP into the project; no CDN at render time.** Run `bash <skill>/scripts/vendor_libs.sh . [--three] [--fonts inter,space-grotesk]` in the project: it writes pinned copies to `vendor/` (GSAP 3.15.0, three 0.170.0, font files with their licences and a `fonts.css`). Load GSAP with `<script src="vendor/gsap.min.js">`. The `init` template points at a CDN; replace that line. A render that fetches from the network can differ between runs and fails offline.

## Sound

- Music or voiceover: an `<audio>` element with `data-start`, `data-duration` and a local file path, for example `<audio src="assets/bed.wav" data-start="0" data-duration="12"></audio>`.
- Video with its own sound: keep it on the `<video>` element with `data-has-audio="true"` and no `muted`. Silent footage: `muted`.
- Or render silent and add sound in the finish step: `scripts/finish.sh --audio bed.wav`. This is the simplest path and also sets loudness.

## Splitting a long piece

Put each scene in its own file under `compositions/` and pull it into the root with `data-composition-src="compositions/scene2.html"`. Each scene registers its own timeline under its own id. Long pieces stay editable and you can render one scene alone with `--composition`.

## Commands you will use

```bash
npx hyperframes lint .                          # structure errors, fast
npx hyperframes check .                         # lint + runtime + layout + contrast in one gate
npx hyperframes snapshot . --at 0.5,3,7.5       # PNG stills at exact seconds: look at them
                                                # they are written under .hyperframes/artifacts/snapshots/<id>/ (the command prints the path)
npx hyperframes render . -o draft.mp4 --quality draft --workers 4
npx hyperframes render . -o render.mp4 --quality delivery --fps 30
npx hyperframes render . -o fix.mp4 --start 4 --end 7   # re-render a span only
```

Quality presets: `draft` for iterating, `looks` (default) for review, `delivery` for the final. `--workers` sets parallel Chrome processes (about 256 MB each); 4-8 suits most laptops. Renders queue by default, so starting two does not make either faster.

## Patterns that work

- **Word-by-word or line-by-line type:** wrap each word in a `<span>` and stagger: `tl.from(".l1 span", { yPercent: 110, opacity: 0, duration: 0.5, stagger: 0.06, ease: "power3.out" }, 0.3)`. Put the words inside a wrapper with `overflow: hidden` for a clean mask reveal.
- **Count-ups:** tween a plain object and write the rounded value into the element in `onUpdate`. Format with `toLocaleString("en-US")` so the commas are right.
- **A shape that carries across scenes:** one element (a bar, a circle) that grows to fill the frame becomes the next background. It reads as one continuous film instead of a slide show.
- **Camera feel on 2D:** scale the whole stage from 1.0 to 1.04 over the shot. Tiny, but it keeps a held frame alive.
- **Fonts: vendor them too.** `vendor_libs.sh . --fonts inter,space-grotesk` (any [Fontsource](https://fontsource.org) id) writes the `.woff2` files and `vendor/fonts/fonts.css`; link that stylesheet and use the family name as written there. Check a snapshot to confirm the face actually loaded; a fallback font is the most common silent failure.

## Common failures and the fix

| You see | Cause | Fix |
|---|---|---|
| Nothing moves in the render | Timeline not registered, wrong id, or not paused | `window.__timelines["<id matching data-composition-id>"] = tl` with `paused: true` |
| An element never appears | Missing `data-start` / `data-duration`, or its time range does not cover the tween | Give it the full range it is on screen |
| Nested animation frozen | Child timeline created paused | Create children unpaused; only the root is paused |
| Different result every render | `Math.random()`, `Date.now()`, or a fetch | Seeded random, fixed values, local files |
| Text in the wrong font | Font not loaded before capture | Vendor the font files locally with `@font-face`; confirm in a snapshot |
| Render is the wrong length | Root `data-duration` differs from the brief | Set it to the exact seconds; `finish.sh --seconds` trims and pads too |

## Reading the output, and warnings to expect

- `render` prints a long trace. The line that matters says `rendered in`; search for it rather than reading the whole log.
- `hyperframes check` and `check_delivery.sh` warn about **holds**: a closing line held still, or a freeze over 1.5 s. When the brief asks for that hold, the warning is expected: say so in REPORT.md next to the brief line that asked for it. When it did not, it is dead air: fix it.
- `hyperframes check` may also suggest a longer closing hold than the brief allows. The brief wins; note the difference in REPORT.md.
- **Eases, by name.** GSAP's `power1` is quadratic, `power2` cubic, `power3` quartic and `power4` quintic; `.out` decelerates into place (arrivals), `.in` accelerates away (exits), `.inOut` does both. `none` is linear: use it only for constant spins and turntables. When a brief names a feel ("snappy", "soft"), write the ease you chose into SPEC.md.
- **Freeze warnings and small motion.** `check_delivery.sh` looks for whole-frame freezes. A small element that keeps moving (a counter, a dot) can still trip it, because the change is below its threshold. Pull two stills a second apart inside the flagged stretch and compare them before you call it dead air.
- **Starting states belong in CSS.** A `tl.set(el, {...}, 0)` at time 0 may not be applied when the renderer captures frame 0, so an element meant to start hidden flashes in the first frame. Put the starting state (`opacity: 0`, an offset transform) in CSS and animate from it; `hyperframes check` warns about this.
- **`first_frame_empty` from `hyperframes check`** can be a false alarm when elements are created by script: the static check does not run your script. Confirm with `npx hyperframes snapshot . --at 0` and look at the frame.
