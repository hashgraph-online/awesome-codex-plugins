# Numbers & charts

Counters, big stats, bar and line charts, race charts, progress rings and before/after metrics. 12 takes. Browse them with previews at https://skills.varg.ai/browse/skills/numbers/.

One number per beat, big, with a short label, counting in 0.8–1.5 s with an ease-out and holding long enough to remember. Label charts directly, cut axes and gridlines to the minimum, highlight the hero bar in the brand color, and show the before value before the improved one.

## Big Stat Count-Up

<a id="big-stat-count-up"></a>One huge number counts from zero to its value and lands, with a short label under it.

Built on [Count Up](https://github.com/heygen-com/hyperframes/tree/main/registry/components/count-up) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

The number fills ~40% of frame width in tabular figures; a label ("teams", "faster") in a smaller weight beneath.

- **When:** One proof stat per scene: users, speed, money saved.
- **Watch out:** Do not put three stats on one card; a stat you want remembered deserves its own beat.
- **Timing:** Count 0.8–1.5 s ease-out (expo.out), land with a 1.03 scale pop, hold ≥ 1.5 s.
- **Also called:** number ticker, count up, hero stat
- **Card:** https://skills.varg.ai/skills/big-stat-count-up/

### FFmpeg

```bash
# counter with drawtext expression (0→10000 over 1.2 s)
-vf "drawtext=text='%{eif\:min(10000\,10000*t/1.2)\:d}':x=(w-tw)/2:y=(h-th)/2:fontsize=220:fontcolor=white"
```

### HyperFrames

```bash
npx hyperframes add count-up
```
Set `data-variable-values='{"from":0,"to":10000,"suffix":"+"}'`; use `font-variant-numeric: tabular-nums` so the width does not jitter.

### Remotion

```tsx
const v = interpolate(frame,[0,36],[0,10000],{extrapolateRight:'clamp',easing:Easing.out(Easing.exp)});
<span style={{fontVariantNumeric:'tabular-nums'}}>{Math.round(v).toLocaleString()}+</span>
```

### CapCut

Text → Text templates → search "number"/"counter"; or Effects → "Number counter" where available; set end value.

### Components

- Count Up (hyperframes): `npx hyperframes add count-up` · https://skills.varg.ai/component/hf.count-up/
- Number Ticker (magic-ui): `npx shadcn@latest add @magicui/number-ticker` · https://skills.varg.ai/component/magicui.number-ticker/
- Count-Up Stat Card (hyperframes): `npx hyperframes add mk-progress-stat` · https://skills.varg.ai/component/hf.mk-progress-stat/

Sources: [Piktochart: Apple keynote tips, one stat per slide](https://piktochart.com/blog/tips-keynote-presentation.md) · [Animation principles for data visualization](https://skills.cat/skills/dylantarre/animation-principles/data-visualization) · [Bohdan Motion: Secureframe launch video, one pain per scene](https://x.com/bohdanmotion/status/2069369111231049803)

## Odometer Digit Roll

<a id="odometer-digit-roll"></a>Each digit rolls on its own wheel to the target, places settling right to left like an odometer.

Built on [Number Wheel](https://github.com/heygen-com/hyperframes/tree/main/registry/components/number-wheel) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Digits slide vertically in masked slots, with slight motion blur; new places rise into view as the number grows.

- **When:** Prices, live counters, plan comparisons — numbers that change rather than appear.
- **Watch out:** Do not roll digits at the same speed; lower places spin faster and settle last.
- **Timing:** 0.8–1.4 s; ones place settles last; ease out with a tiny overshoot.
- **Also called:** rolling number, number wheel, slot digits
- **Card:** https://skills.varg.ai/skills/odometer-digit-roll/

### HyperFrames

```bash
npx hyperframes add number-wheel
```

### Remotion

```tsx
// npx shadcn@latest add @remocn/rolling-number
<RollingNumber from={0} to={1299} />
```

### CapCut

Text → Text templates → "odometer"/"rolling number" if available; else stack digit columns and keyframe Position Y in masks.

### Components

- Number Wheel (hyperframes): `npx hyperframes add number-wheel` · https://skills.varg.ai/component/hf.number-wheel/
- Rolling Number (remocn): `npx shadcn@latest add @remocn/rolling-number` · https://skills.varg.ai/component/remocn.rolling-number/
- Sliding Number (animate-ui): `npm install @animate-ui/react motion` · https://skills.varg.ai/component/animateui.sliding-number/

Sources: [Animation principles for data visualization](https://skills.cat/skills/dylantarre/animation-principles/data-visualization)

## Bars Grow with Value Labels

<a id="bars-grow-with-labels"></a>Bars rise from the baseline in a staggered cascade with values riding their tops.

Built on [Animated Bar Chart](https://github.com/heygen-com/hyperframes/tree/main/registry/components/animated-bar-chart) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Few bars (3–6), thick, rounded tops; the hero bar in accent color, others muted; labels count up with the bars.

- **When:** Benchmarks, growth by quarter, us-vs-them comparisons.
- **Watch out:** Do not draw full axes and gridlines; label bars directly and drop the clutter.
- **Timing:** Each bar 0.6–0.9 s ease-out, 80–120 ms stagger; hero bar last; hold 2 s.
- **Also called:** bar chart, animated bars, column chart
- **Card:** https://skills.varg.ai/skills/bars-grow-with-labels/

### HyperFrames

```bash
npx hyperframes add animated-bar-chart
```
Or `chart-story` to land the exact supplied values in reading order.

### Remotion

```tsx
// npx shadcn@latest add @remocn/animated-bar-chart
const h = spring({frame: frame - i*3, fps, config:{damping:200}}) * value/max * 600;
```

### CapCut

Make rectangle shapes; keyframe Scale Y from 0 at the bottom anchor; add value Text layers above each.

### Components

- Animated Bar Chart (hyperframes): `npx hyperframes add animated-bar-chart` · https://skills.varg.ai/component/hf.animated-bar-chart/
- Animated Bar Chart (remocn): `npx shadcn@latest add @remocn/animated-bar-chart` · https://skills.varg.ai/component/remocn.animated-bar-chart/
- Chart Story (hyperframes): `npx hyperframes add chart-story` · https://skills.varg.ai/component/hf.chart-story/

Sources: [Animation principles for data visualization](https://skills.cat/skills/dylantarre/animation-principles/data-visualization) · [Piktochart: Apple keynote tips, one stat per slide](https://piktochart.com/blog/tips-keynote-presentation.md)

## Line Draws with Riding Label

<a id="line-draws-riding-label"></a>A line draws itself left to right while the current value rides the pen tip, ending on a dot and big label.

Built on [Minimal Line Graph](https://github.com/heygen-com/hyperframes/tree/main/registry/blocks/mk-line-graph) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

One or two series on a quiet grid; the draw front has a glowing dot; value labels pop at key points.

- **When:** Growth over time, usage curves, "hockey stick" moments.
- **Watch out:** Do not draw both series at once if one is the point; draw the comparison first, faded, then the hero line.
- **Timing:** Draw 1.2–2 s power1.inOut; end dot pop 0.2 s; hold 1.5 s.
- **Also called:** line chart, growth curve, trend line
- **Card:** https://skills.varg.ai/skills/line-draws-riding-label/

### HyperFrames

```bash
npx hyperframes add mk-line-graph
```
Or `data-chart` for bar + line with NYT-style labels.

### Remotion

```tsx
// npx shadcn@latest add @remocn/animated-line-chart
const p = interpolate(frame,[0,54],[0,1],{extrapolateRight:'clamp',easing:Easing.inOut(Easing.sin)});
<path strokeDasharray={len} strokeDashoffset={len*(1-p)}/>
```

### CapCut

Export the chart as a PNG; Mask → Linear keyframed left to right to reveal the line; add a dot sticker following the edge.

### Components

- Minimal Line Graph (hyperframes): `npx hyperframes add mk-line-graph` · https://skills.varg.ai/component/hf.mk-line-graph/
- Animated Line Chart (remocn): `npx shadcn@latest add @remocn/animated-line-chart` · https://skills.varg.ai/component/remocn.animated-line-chart/
- Data Chart (hyperframes): `npx hyperframes add data-chart` · https://skills.varg.ai/component/hf.data-chart/

Sources: [Animation principles for data visualization](https://skills.cat/skills/dylantarre/animation-principles/data-visualization)

## Ranked Bar Race

<a id="ranked-bar-race"></a>Ranked bars grow and overtake each other over time while the axis rescales and a year/date ticks.

Built on [Bar Chart Race](https://github.com/heygen-com/hyperframes/tree/main/registry/blocks/bar-chart-race) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Horizontal bars with logos at their ends, sorted live, a big date counter in the corner; your product climbs to #1.

- **When:** Market share, popularity over time, "fastest growing" stories.
- **Watch out:** Do not run the race too fast; viewers need ~0.5–1 s per period to follow overtakes.
- **Timing:** 0.5–1 s per period, smooth interpolation between periods, final hold 2 s.
- **Also called:** bar chart race, ranking animation, leaderboard
- **Card:** https://skills.varg.ai/skills/ranked-bar-race/

### HyperFrames

```bash
npx hyperframes add bar-chart-race
```
Feed the time series as variables; ranks and the axis are recomputed per frame from time.

### Remotion

```tsx
const t = frame / (fps*0.8); const i0 = Math.floor(t), k = t - i0;
const values = series.map(s => s[i0] + (s[i0+1]-s[i0])*k);
const ranked = [...values.keys()].sort((a,b)=>values[b]-values[a]);
```

### CapCut

Build in Flourish (Bar chart race template), screen-record the preview, import and trim.

### Components

- Bar Chart Race (hyperframes): `npx hyperframes add bar-chart-race` · https://skills.varg.ai/component/hf.bar-chart-race/
- Data Chart (hyperframes): `npx hyperframes add data-chart` · https://skills.varg.ai/component/hf.data-chart/

Sources: [Flourish: how to make bar chart race visualizations](https://flourish.studio/blog/bar-chart-race/)

## Progress Ring Fills

<a id="progress-ring-fills"></a>A thin ring draws on to a percentage while the number in its center counts up in sync.

Built on [Conic Progress Ring](https://github.com/heygen-com/hyperframes/tree/main/registry/components/conic-progress-ring) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Thin stroke on a faint track, rounded cap, the percent in the center; optional color shift as it passes thresholds.

- **When:** Accuracy, uptime, completion, savings as a percentage.
- **Watch out:** Do not use thick donut charts with many slices; one ring, one number.
- **Timing:** 1.0–1.6 s power2.out; center count shares the same easing.
- **Also called:** conic ring, gauge, percentage arc
- **Card:** https://skills.varg.ai/skills/progress-ring-fills/

### HyperFrames

```bash
npx hyperframes add conic-progress-ring
```
Or `mk-usage-arc` — one helper call drives both ring and number.

### Remotion

```tsx
const p = interpolate(frame,[0,40],[0,0.94],{extrapolateRight:'clamp',easing:Easing.out(Easing.quad)});
<circle r={90} strokeDasharray={565} strokeDashoffset={565*(1-p)} strokeLinecap="round"/>
<text>{Math.round(p*100)}%</text>
```

### CapCut

Use a ring sticker with Mask → Circle sweep, or Text templates → "progress".

### Components

- Conic Progress Ring (hyperframes): `npx hyperframes add conic-progress-ring` · https://skills.varg.ai/component/hf.conic-progress-ring/
- Hairline Arc Gauge (hyperframes): `npx hyperframes add mk-usage-arc` · https://skills.varg.ai/component/hf.mk-usage-arc/
- SVG Line Draw Loader (hyperframes): `npx hyperframes add svg-line-draw-loader` · https://skills.varg.ai/component/hf.svg-line-draw-loader/

Sources: [Animation principles for data visualization](https://skills.cat/skills/dylantarre/animation-principles/data-visualization)

## Before → After Metric

<a id="before-after-metric"></a>The old number shows, gets crossed or rolls, and the new better number takes its place.

Built on [Value Swap](https://remocn.dev/r/value-swap.json) by Kapish Dima (remocn), MIT. The write-up and recipes are varg's.

"12 months" in grey slides up and out; "2 weeks" rolls in bold accent; an arrow or delta chip ("−83%") pops beside it.

- **When:** Outcome claims: time saved, cost cut, conversion lifted.
- **Watch out:** Do not show the delta before the viewer has read the old value; give it ~1 s.
- **Timing:** Old hold 0.8–1.2 s, swap 0.4–0.6 s, delta chip pop 0.2 s, hold 1.5 s.
- **Also called:** value swap, metric change, from-to number
- **Card:** https://skills.varg.ai/skills/before-after-metric/

### HyperFrames

```bash
npx hyperframes add slot-machine-roll
```
Or `strikethrough-replace` when the old value should be crossed out.

### Remotion

```tsx
// npx shadcn@latest add @remocn/value-swap
<ValueSwap from="12 months" to="2 weeks" at={30}/>
```

### CapCut

Two Text layers; old one Animation Out "Slide up", new one In "Slide up" at the same frame; add a delta chip sticker.

### Components

- Value Swap (remocn): `npx shadcn@latest add @remocn/value-swap` · https://skills.varg.ai/component/remocn.value-swap/
- Slot Machine Roll (hyperframes): `npx hyperframes add slot-machine-roll` · https://skills.varg.ai/component/hf.slot-machine-roll/
- Strikethrough Replace (hyperframes): `npx hyperframes add strikethrough-replace` · https://skills.varg.ai/component/hf.strikethrough-replace/

Sources: [Bohdan Motion: Secureframe launch video, one pain per scene](https://x.com/bohdanmotion/status/2069369111231049803)

## Money Counter Payoff

<a id="money-counter-payoff"></a>A currency figure counts up fast, flashes green on landing, and a small burst celebrates it.

Built on [Apple Money Count](https://github.com/heygen-com/hyperframes/tree/main/registry/blocks/apple-money-count) by Stronkter (hyperframes), Apache-2.0. The write-up and recipes are varg's.

Big $ value in finance-style type; digits blur while climbing, settle, flash green; confetti or coins burst once.

- **When:** Payment, revenue, creator-earnings and savings products.
- **Watch out:** Do not celebrate made-up numbers; show real or clearly labeled example figures.
- **Timing:** Count 1–1.5 s expo.out, flash 0.2 s, burst 0.8–1.2 s.
- **Also called:** revenue counter, earnings count, money stat
- **Card:** https://skills.varg.ai/skills/money-counter-payoff/

### HyperFrames

```bash
npx hyperframes add apple-money-count
npx hyperframes add confetti
```
Confetti is seeded, so every render matches.

### Remotion

```tsx
const v = interpolate(frame,[0,40],[0,10000],{extrapolateRight:'clamp',easing:Easing.out(Easing.exp)});
const flash = interpolate(frame,[40,46],[1,0],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
<span style={{color: flash>0? '#22C55E' : '#fff'}}>${Math.round(v).toLocaleString()}</span>
```

### CapCut

Counter text template + Effects → "Confetti"/"Money rain" for 1 s at landing; add a cash-register SFX.

### Components

- Apple Money Count (hyperframes): `npx hyperframes add apple-money-count` · https://skills.varg.ai/component/hf.apple-money-count/
- Confetti (hyperframes): `npx hyperframes add confetti` · https://skills.varg.ai/component/hf.confetti/
- Confetti (tsparticles): `pnpm add @tsparticles/engine @tsparticles/slim @tsparticles/preset-<name>` · https://skills.varg.ai/component/tsparticles.confetti/

Sources: [Jamie on X: SFX breakdown of a launch video](https://x.com/jamiesmotion/status/2110099791958982703)

## Axis-Free Speed Comparison

<a id="axis-free-comparison"></a>Two or three bars with no axis numbers, just labels and a big multiplier like "2.4× faster".

Built on [Chart Story](https://github.com/heygen-com/hyperframes/tree/main/registry/components/chart-story) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Clean bars in the product gradient vs grey competitors, "Higher is better" note, the multiplier counts up as the hero bar grows.

- **When:** Performance claims in keynote style where the relative gap is the message.
- **Watch out:** Do not drop axes without stating the test conditions in a small footnote.
- **Timing:** Bars 0.8 s ease-out, hero bar last; multiplier count 0.8 s; hold 2 s.
- **Also called:** Apple-style chart, 2x faster, relative bars
- **Card:** https://skills.varg.ai/skills/axis-free-comparison/

### HyperFrames

```bash
npx hyperframes add chart-story
```
Hide the axis, set the hero bar fill to the brand gradient, and drive a `count-up` for the multiplier.

### Remotion

```tsx
// npx shadcn@latest add @remocn/animated-bar-chart
const m = interpolate(frame,[20,44],[1,2.4],{extrapolateLeft:'clamp',extrapolateRight:'clamp'}).toFixed(1);
<h1>{m}× faster</h1>
```

### CapCut

Two rectangle shapes keyframed on Scale X; Text "2.4× faster" with a counter template; small footnote text.

### Components

- Chart Story (hyperframes): `npx hyperframes add chart-story` · https://skills.varg.ai/component/hf.chart-story/
- Animated Bar Chart (remocn): `npx shadcn@latest add @remocn/animated-bar-chart` · https://skills.varg.ai/component/remocn.animated-bar-chart/
- Basic Number Ticker (fancy): `npx shadcn add @fancy/basic-number-ticker` · https://skills.varg.ai/component/fancy.basic-number-ticker/

Sources: [Piktochart: Apple keynote tips, one stat per slide](https://piktochart.com/blog/tips-keynote-presentation.md) · [Bohdan Motion: Apple Mac Studio launch film, 10-step playbook](https://x.com/bohdanmotion/status/2093347071440851104)

## Dense Specs Wall

<a id="dense-specs-wall"></a>A grid of short spec tiles fills the frame in a fast stagger — numbers and two-word labels.

Built on [Grid Card Assemble](https://github.com/heygen-com/hyperframes/tree/main/registry/components/grid-card-assemble) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Tight grid of tiles ("4K · 60fps", "20 GB", "9:16") assembling in a wave, then the camera holds for one beat.

- **When:** Near the end of a film, to signal depth after the story has been told.
- **Watch out:** Do not expect each tile to be read; this is a texture of capability, keep it under 2 s and don't narrate every tile.
- **Timing:** Whole wall 1–1.5 s, tile stagger 20–40 ms from center; hold 1–2 s.
- **Also called:** specs grid, feature wall, capability grid
- **Card:** https://skills.varg.ai/skills/dense-specs-wall/

### HyperFrames

```bash
npx hyperframes add grid-card-assemble
npx hyperframes add stagger-lattice
```
`stagger:{each:0.03,from:"center",grid:"auto"}`

### Remotion

```tsx
tiles.map((t,i)=>{const d=Math.hypot(t.col-cx,t.row-cy); const s=spring({frame:frame-d*2,fps,config:{damping:200}}); return <Tile style={{opacity:s, transform:`scale(${0.9+s*0.1})`}}/>})
```

### CapCut

Build the wall as one image; reveal with a Mask → Circle expanding from the center over 1 s.

### Components

- Grid Card Assemble (hyperframes): `npx hyperframes add grid-card-assemble` · https://skills.varg.ai/component/hf.grid-card-assemble/
- Specs Checklist (hyperframes): `npx hyperframes add mk-specs-list` · https://skills.varg.ai/component/hf.mk-specs-list/
- Stagger Lattice (hyperframes): `npx hyperframes add stagger-lattice` · https://skills.varg.ai/component/hf.stagger-lattice/

Sources: [Bohdan Motion: Apple Mac Studio launch film, 10-step playbook](https://x.com/bohdanmotion/status/2093347071440851104) · [SaaSFrame: understanding the bento layout trend](https://www.saasframe.io/blog/the-bento-layout-trend)

## Pain Metric Falls Away

<a id="pain-metric-falls"></a>A painful metric (hours, cost, errors) draws a falling line while the number counts down and the mood lifts.

Built on [Decline Chart](https://github.com/heygen-com/hyperframes/tree/main/registry/components/decline-chart) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Line drops steeply as the value counts down; the background goes from dark/red-tinted to clean once the product arrives.

- **When:** The problem → solution turn in the first third of a film.
- **Watch out:** Do not open on the solution's numbers before the pain has been shown.
- **Timing:** Count down 1–1.5 s, line draw in the same window, background shift 0.6 s after.
- **Also called:** decline chart, cost drops, problem stat
- **Card:** https://skills.varg.ai/skills/pain-metric-falls/

### HyperFrames

```bash
npx hyperframes add decline-chart
```

### Remotion

```tsx
const v = interpolate(frame,[0,40],[480,32],{extrapolateRight:'clamp',easing:Easing.inOut(Easing.cubic)});
<h1>{Math.round(v)} hrs/month</h1>
```

### CapCut

Counter text template counting down; keyframe the background Adjust → Saturation/Temperature after the drop.

### Components

- Decline Chart (hyperframes): `npx hyperframes add decline-chart` · https://skills.varg.ai/component/hf.decline-chart/
- Count Up (hyperframes): `npx hyperframes add count-up` · https://skills.varg.ai/component/hf.count-up/
- Animated Number (motion-primitives): `npx motion-primitives@latest add animated-number` · https://skills.varg.ai/component/motionprimitives.animated-number/

Sources: [Bohdan Motion: Secureframe launch video, one pain per scene](https://x.com/bohdanmotion/status/2069369111231049803)

## Ticking Time-Saved Clock

<a id="ticking-time-saved"></a>Clock-style digits slide as seconds tick, timing the task live on screen.

Built on [Sliding Number](https://github.com/ibelick/motion-primitives/blob/main/components/core/sliding-number.tsx) by motion-primitives, MIT. The write-up and recipes are varg's.

A small mono timer in a corner (00:00 → 00:38) with digits sliding vertically; it stops and pops when the task finishes.

- **When:** Prove speed claims in real time: "rendered in 38 seconds".
- **Watch out:** Do not speed up the footage while the timer claims real time; keep them honest or label "sped up 4×".
- **Timing:** Digit slide 0.2–0.3 s per tick; final pop 0.2 s.
- **Also called:** sliding clock digits, timer, live time counter
- **Card:** https://skills.varg.ai/skills/ticking-time-saved/

### FFmpeg

```bash
-vf "drawtext=text='%{pts\:gmtime\:0\:%M\\\:%S}':x=w-tw-60:y=60:fontsize=48:fontcolor=white:box=1:boxcolor=black@0.5:boxborderw=12"
```

### HyperFrames

```bash
npx hyperframes add number-pop-in
```
Derive the shown seconds from `tl.time()` so it matches the footage exactly.

### Remotion

```tsx
const s = Math.floor(frame / fps);
const mm = String(Math.floor(s/60)).padStart(2,'0'), ss = String(s%60).padStart(2,'0');
```

### CapCut

Text → Text templates → search "timer"/"stopwatch"; place top right and match its length to the clip.

### Components

- Sliding Number (motion-primitives): `npx motion-primitives@latest add sliding-number` · https://skills.varg.ai/component/motionprimitives.sliding-number/
- Number Pop In (hyperframes): `npx hyperframes add number-pop-in` · https://skills.varg.ai/component/hf.number-pop-in/
- Camcorder HUD (hyperframes): `npx hyperframes add camcorder-hud` · https://skills.varg.ai/component/hf.camcorder-hud/

Sources: [FFmpeg filters documentation (timeline enable, drawtext, zoompan, overlay)](https://ffmpeg.org/ffmpeg-filters.html)
