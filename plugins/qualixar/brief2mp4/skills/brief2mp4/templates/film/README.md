# Archive desk (film mode template)

The documentary look used by `scripts/film.py`. `scripts/film_build.py` fills `index.html` with one `<section class="beat">` per beat and inlines `film.js`; `film.css` is copied next to it. Nothing here needs the network: GSAP and the two fonts (Playfair Display and IBM Plex Mono, both SIL OFL) are vendored into the project by `scripts/vendor_libs.sh`.

## Layout (1920x1080, 5% safe margins)

| Part | Where | Notes |
|---|---|---|
| Plate | 96,54 and 1296x740 | A still or a map. Slow push-in at one speed in every beat; text never sits on it except map labels (drawn in the SVG) and burned captions |
| Caption | 96,830 and 1296 wide | Serif, 58 px, at most two lines; the words fade in one by one while the block slides up 18 px |
| Stamp | 1440,54 | `No. 03 / 07` and an optional date, typed in character by character |
| Ledger | 1440,330 | A counter in tabular mono numerals: counts up and lands on the exact number as it is spoken |
| Credit | 1440,880 | Author, licence, source of a picture that needs one |

At most four text blocks are on screen at once (stamp, caption, ledger, credit), none closer than 24 px, none past the frame edge. A beat with no picture shows its words large inside the plate instead (a title beat).

## Beat markup

```html
<section class="beat" id="B03" data-t0="8.4667" data-t1="14.2" data-kind="archive" data-fx="0.5" data-fy="0.42"
         data-s0="1.08" data-rate="0.014" data-vx="-10" data-vy="-4" data-count-from="0" data-count-to="1400000"
         data-count-at="0.6" data-count-end="3.1" data-dip-in="0.4">
  <figure class="plate"><img class="shot" src="assets/archive/ship.jpg" alt="..." /></figure>
  <p class="stamp">No. 03 / 07<br />MARCH 1931</p>
  <h2 class="caption">On the seabed</h2>
  <div class="ledger"><span class="n">0</span><span class="l">km of cable</span></div>
  <p class="credit">Author / CC BY 4.0 / Wikimedia Commons</p>
</section>
```

`data-t0` and `data-t1` are seconds (not HyperFrames' own `data-start`, which would let its runtime hide the beat). The camera is `s0 + rate * t` scale with a drift of `vx, vy` pixels a second around the focus `fx, fy`. A beat with `data-dip-in` or `data-dip-out` fades from or to the dark ground; the first beat of an act that dips in does not carry the `first` class.

## Rules the page keeps

The picture is a function of the timeline only: no clock, no random, no network. Starting states are in CSS. A beat's exit starts after its entrances end. SVG routes are drawn with pixel lengths (`getTotalLength`). `film.js` registers one paused timeline as `window.__timelines["main"]`. Check a new beat type with `npx hyperframes snapshot`, `scripts/check_clutter.py --dom` and the render traps in `references/render-traps.md`.
