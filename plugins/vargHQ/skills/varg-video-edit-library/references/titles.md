# Headlines & callouts

Words over footage: headlines, key phrases, lower thirds, highlights and callouts that point at the thing that matters. 14 takes. Browse them with previews at https://skills.varg.ai/browse/skills/titles/.

On-screen words carry the story when sound is off, so every title must be readable in the time it is on: about 2–3 words per second plus a second to settle, kept inside the outer 10% of the frame. Good titles enter fast (0.3–0.6 s, ease-out), hold still while being read, and use one motion idea per line; emphasis goes to a single phrase, not the whole sentence.

## Kicker Over Rising Headline

<a id="kicker-headline-rise"></a>A small mono kicker fades in, then the headline rises word by word from a soft blur.

Built on [Titlecard Calm](https://github.com/heygen-com/hyperframes/tree/main/registry/components/titlecard-calm) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

A tiny uppercase label ("NEW · AGENTS") sits above a large grotesque headline. Words lift 20–40 px and clear from blur in a short stagger.

- **When:** Open a chapter or name a feature before its demo. It works over a plain backdrop or over darkened footage.
- **Watch out:** Do not animate the kicker and the headline at the same moment; the eye needs the small label first.
- **Timing:** Kicker 0.3 s, then words 0.5 s each with an 80–120 ms stagger, power3.out. Hold ≥ 1 s plus ~0.4 s per word.
- **Also called:** eyebrow title, section title card, chapter card
- **Card:** https://skills.varg.ai/skills/kicker-headline-rise/

### FFmpeg

```bash
-vf "drawtext=text='NEW · AGENTS':x=(w-tw)/2:y=h*0.38:fontsize=28:fontcolor=white:alpha='min(1,max(0,(t-0.2)/0.3))',\
drawtext=text='Ship in one prompt':x=(w-tw)/2:y=h*0.45:fontsize=96:fontcolor=white:alpha='min(1,max(0,(t-0.5)/0.5))'"
```

### HyperFrames

```bash
npx hyperframes add soft-blur-in
```
```js
tl.from(".kicker",{opacity:0,y:8,duration:0.3},0.2)
  .from(".hl .word",{opacity:0,y:30,filter:"blur(8px)",stagger:0.1,duration:0.5,ease:"power3.out"},0.45);
```

### Remotion

```tsx
// npx shadcn@latest add @remocn/staggered-fade-up
const s = spring({frame: frame - i*3, fps, config:{damping:200}});
style={{opacity:s, transform:`translateY(${interpolate(s,[0,1],[30,0])}px)`}}
```

### CapCut

Text → Add text twice (kicker small, headline large). Animation → In: "Fade in" 0.3 s on the kicker, "Rise"/"Blur in" 0.5 s on the headline, start the headline clip 0.25 s later.

### Components

- Titlecard Calm (hyperframes): `npx hyperframes add titlecard-calm` · https://skills.varg.ai/component/hf.titlecard-calm/
- Soft Blur In (hyperframes): `npx hyperframes add soft-blur-in` · https://skills.varg.ai/component/hf.soft-blur-in/
- Staggered Fade Up (remocn): `npx shadcn@latest add @remocn/staggered-fade-up` · https://skills.varg.ai/component/remocn.staggered-fade-up/
- Soft Blur In (remocn): `npx shadcn@latest add @remocn/soft-blur-in` · https://skills.varg.ai/component/remocn.soft-blur-in/

Sources: [Text animation for readability: kinetic type without overcomplication](https://cursa.app/en/page/text-animation-for-readability-kinetic-type-without-overcomplication) · [GSAP docs: SplitText](https://gsap.com/docs/v3/Plugins/SplitText) · [Kinetic typography without After Effects (plan ~2 words per second)](https://oakgen.ai/blog/kinetic-typography-without-after-effects)

## Rotating Benefit Word

<a id="rotating-benefit-word"></a>A fixed phrase holds while one word in it cycles through benefits, uses or audiences.

Built on [Flip Words](https://ui.aceternity.com/components/flip-words) by aceternity, Aceternity License (free components). The write-up and recipes are varg's.

"Built for [designers]" with the bracketed word flipping to developers, marketers, founders. The slot resizes so the line stays centered.

- **When:** Show that one product serves many people or jobs without cutting to new title cards.
- **Watch out:** Do not cycle more than 3–4 words or faster than one per ~1.2 s; the viewer must read each one.
- **Timing:** Swap every 1.2–2 s; each swap 0.35–0.5 s with the old word exiting up and the new word rising in.
- **Also called:** word rotate, flip words, swapping word headline
- **Card:** https://skills.varg.ai/skills/rotating-benefit-word/

### HyperFrames

```bash
npx hyperframes add morph-text
```
Put the fixed prefix in its own span; in the timeline swap the slot: `tl.to(slot,{yPercent:-100,opacity:0,duration:0.35},t).set(slot,{textContent:next}).fromTo(slot,{yPercent:100},{yPercent:0,opacity:1,duration:0.4},">")`.

### Remotion

```tsx
// npx shadcn@latest add @remocn/inline-word-roll
const idx = Math.floor(frame / (fps*1.5)) % words.length;
const p = spring({frame: frame % (fps*1.5), fps, config:{damping:200}});
```

### CapCut

Make one text layer per word on top of the fixed phrase, butt them end to end (1.5 s each), and give each Animation → In: "Slide up" and Out: "Slide up" 0.35 s.

### Components

- Flip Words (aceternity): `npx shadcn@latest add @aceternity/flip-words` · https://skills.varg.ai/component/aceternity.flip-words/
- Word Rotate (magic-ui): `npx shadcn@latest add @magicui/word-rotate` · https://skills.varg.ai/component/magicui.word-rotate/
- Inline Word Roll (remocn): `npx shadcn@latest add @remocn/inline-word-roll` · https://skills.varg.ai/component/remocn.inline-word-roll/
- Container Text Flip (aceternity): `npx shadcn@latest add @aceternity/container-text-flip` · https://skills.varg.ai/component/aceternity.container-text-flip/

Sources: [Kinetic typography without After Effects (plan ~2 words per second)](https://oakgen.ai/blog/kinetic-typography-without-after-effects) · [Text animation for readability: kinetic type without overcomplication](https://cursa.app/en/page/text-animation-for-readability-kinetic-type-without-overcomplication)

## Masked Line Reveal

<a id="masked-line-reveal"></a>Each line slides up out of an invisible slot, so the type looks cut from the frame.

Built on [Vertical Cut Reveal](https://github.com/danielpetho/fancy/blob/main/src/fancy/components/text/vertical-cut-reveal.tsx) by fancy, MIT. The write-up and recipes are varg's.

Lines rise from behind a hard mask edge with no blur or fade, one after another, then exit upward the same way.

- **When:** Editorial statements, manifesto lines, or the one-sentence promise near the open.
- **Watch out:** Do not let the mask clip descenders; give the mask box ~0.15 em padding below the baseline.
- **Timing:** Per line 0.5–0.7 s, expo.out or power4.out, 0.08–0.12 s between lines.
- **Also called:** slot reveal, cut-out text, line mask up
- **Card:** https://skills.varg.ai/skills/masked-line-reveal/

### HyperFrames

```bash
npx hyperframes add line-by-line-slide
```
```js
// SplitText with masks: lines wrap in overflow:hidden
tl.from(split.lines,{yPercent:110,duration:0.6,stagger:0.1,ease:"power4.out"},0.3);
```

### Remotion

```tsx
// npx shadcn@latest add @remocn/mask-reveal-up
<div style={{overflow:'hidden'}}><div style={{transform:`translateY(${interpolate(spring({frame:frame-i*4,fps,config:{damping:200}}),[0,1],[110,0])}%)`}}>{line}</div></div>
```

### CapCut

Text → Text templates: search "slide up" or use Animation → In: "Wipe up" per line; stack one text layer per line, offset 3–4 frames.

### Components

- Vertical Cut Reveal (fancy): `npx shadcn add @fancy/vertical-cut-reveal` · https://skills.varg.ai/component/fancy.vertical-cut-reveal/
- Line-by-Line Slide (hyperframes): `npx hyperframes add line-by-line-slide` · https://skills.varg.ai/component/hf.line-by-line-slide/
- Mask Reveal Up (remocn): `npx shadcn@latest add @remocn/mask-reveal-up` · https://skills.varg.ai/component/remocn.mask-reveal-up/

Sources: [GSAP docs: SplitText](https://gsap.com/docs/v3/Plugins/SplitText) · [Codrops: 7 must-know GSAP animation tips](https://tympanus.net/codrops/2025/09/03/7-must-know-gsap-animation-tips-for-creative-developers/) · [Text animation for readability: kinetic type without overcomplication](https://cursa.app/en/page/text-animation-for-readability-kinetic-type-without-overcomplication)

## Marker on the Key Phrase

<a id="marker-highlight-phrase"></a>A marker band draws behind the one phrase that matters while the rest of the line stays calm.

Built on [Inline Highlight](https://github.com/heygen-com/hyperframes/tree/main/registry/components/inline-highlight) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

A sentence holds still; a flat or hand-drawn colored band sweeps left to right behind two or three words, and their color shifts to match.

- **When:** Point at the claim the voiceover stresses ("in 30 seconds", "without code").
- **Watch out:** Do not highlight more than one phrase per line; two bands cancel each other out.
- **Timing:** Line settles first; band sweeps 0.4–0.6 s, power2.inOut, starting on the spoken word.
- **Also called:** highlight sweep, highlighter, emphasis marker
- **Card:** https://skills.varg.ai/skills/marker-highlight-phrase/

### HyperFrames

```bash
npx hyperframes add inline-highlight
```
```js
tl.fromTo(".mark",{"--hl":0},{"--hl":1,duration:0.5,ease:"power2.inOut"},wordTime);
```

### Remotion

```tsx
// npx shadcn@latest add @remocn/marker-highlight
const w = interpolate(frame,[at,at+15],[0,100],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
<span style={{background:`linear-gradient(#FDE047,#FDE047) 0 85%/${w}% 40% no-repeat`}}>{phrase}</span>
```

### CapCut

Add a solid shape sticker behind the words (Stickers → Shapes), set its anchor left, keyframe Scale X from 0 to 100% over 0.5 s.

### Components

- Inline Highlight (hyperframes): `npx hyperframes add inline-highlight` · https://skills.varg.ai/component/hf.inline-highlight/
- Text Highlighter (fancy): `npx shadcn add @fancy/text-highlighter` · https://skills.varg.ai/component/fancy.text-highlighter/
- Marker Highlight (hyperframes): `npx hyperframes add marker-highlight` · https://skills.varg.ai/component/hf.marker-highlight/
- Marker Highlight (remocn): `npx shadcn@latest add @remocn/marker-highlight` · https://skills.varg.ai/component/remocn.marker-highlight/

Sources: [Text animation for readability: kinetic type without overcomplication](https://cursa.app/en/page/text-animation-for-readability-kinetic-type-without-overcomplication) · [Bohdan Motion: Secureframe launch video, one pain per scene](https://x.com/bohdanmotion/status/2069369111231049803)

## Strike Old, Write New

<a id="strike-and-replace"></a>A line strikes through the old way, then the new word takes its place.

Built on [Strikethrough Replace](https://github.com/heygen-com/hyperframes/tree/main/registry/components/strikethrough-replace) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

"12 months" gets a red line drawn across it and drops away; "2 weeks" lifts into the same spot in the accent color.

- **When:** Frame the before/after promise: old cost vs new cost, old workflow vs new.
- **Watch out:** Do not swap before the strike line finishes; the cross-out is the joke and needs ~0.3 s to land.
- **Timing:** Strike 0.3–0.4 s, hold 0.2 s, old word out 0.25 s, new word in 0.4 s with slight overshoot (back.out(1.4)).
- **Also called:** strikethrough replace, before/after words, correction
- **Card:** https://skills.varg.ai/skills/strike-and-replace/

### HyperFrames

```bash
npx hyperframes add strikethrough-replace
```
Set the old/new strings in the block's variables: `data-variable-values='{"from":"12 months","to":"2 weeks"}'`.

### Remotion

```tsx
// npx shadcn@latest add @remocn/strikethrough-replace
const strike = interpolate(frame,[0,10],[0,100],{extrapolateRight:'clamp'});
```

### CapCut

Text 1 (old) + a thin red line sticker keyframed Scale X 0→100% over 0.3 s; cut to Text 2 (new) with Animation → In: "Pop up".

### Components

- Strikethrough Replace (hyperframes): `npx hyperframes add strikethrough-replace` · https://skills.varg.ai/component/hf.strikethrough-replace/
- Strikethrough Replace (remocn): `npx shadcn@latest add @remocn/strikethrough-replace` · https://skills.varg.ai/component/remocn.strikethrough-replace/
- Value Swap (remocn): `npx shadcn@latest add @remocn/value-swap` · https://skills.varg.ai/component/remocn.value-swap/

Sources: [Bohdan Motion: Secureframe launch video, one pain per scene](https://x.com/bohdanmotion/status/2069369111231049803) · [Text animation for readability: kinetic type without overcomplication](https://cursa.app/en/page/text-animation-for-readability-kinetic-type-without-overcomplication)

## Clean Lower Third

<a id="clean-lower-third"></a>Name and role slide in at the lower left on a quiet bar, hold 3–5 s, then wipe out.

Built on [Lower Third — Clean Bar](https://github.com/heygen-com/hyperframes/tree/main/registry/blocks/lt-clean-bar) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

A white or charcoal card with an accent tab; name in bold, role in a lighter weight at 60–80% size. Enters with a clip wipe, not a bounce.

- **When:** Introduce the founder, a customer or an engineer the first time they speak.
- **Watch out:** Do not place it inside the outer 10% of the frame or over the speaker's chin and hands.
- **Timing:** In 0.4–0.5 s, hold 3–5 s (about 4 s for a short name), out 0.3 s.
- **Also called:** name tag, speaker title, chyron
- **Card:** https://skills.varg.ai/skills/clean-lower-third/

### FFmpeg

```bash
-vf "drawbox=x=192:y=850:w=560:h=110:color=black@0.7:t=fill:enable='between(t,3,7.5)',\
drawtext=text='Ada Park':x=220:y=868:fontsize=44:fontcolor=white:enable='between(t,3,7.5)'"
```

### HyperFrames

```bash
npx hyperframes add lt-clean-bar
```
```html
<div data-composition-id="lt-clean-bar" data-composition-src="compositions/lt-clean-bar.html"
  data-variable-values='{"name":"Ada Park","role":"CTO, Acme"}'
  data-start="3" data-duration="4.5" data-track-index="3"></div>
```

### Remotion

```tsx
const inP = spring({frame, fps, config:{damping:200}});
const clip = interpolate(inP,[0,1],[100,0]);
<div style={{clipPath:`inset(0 ${clip}% 0 0)`, position:'absolute', left:'10%', bottom:'12%'}}>…</div>
```

### CapCut

Text → Text templates → search "lower third" or "name"; set it at the lower left inside the guides, duration 4 s, Animation In "Wipe right".

### Components

- Lower Third — Clean Bar (hyperframes): `npx hyperframes add lt-clean-bar` · https://skills.varg.ai/component/hf.lt-clean-bar/
- Lower Third — Accent Underline (hyperframes): `npx hyperframes add lt-accent-underline` · https://skills.varg.ai/component/hf.lt-accent-underline/
- Lower Third — Side Rule (hyperframes): `npx hyperframes add lt-side-rule` · https://skills.varg.ai/component/hf.lt-side-rule/
- YouTube Lower Third (hyperframes): `npx hyperframes add yt-lower-third` · https://skills.varg.ai/component/hf.yt-lower-third/

Sources: [TechSmith: the complete guide to lower thirds](https://www.techsmith.com/blog/edit-videos-lower-thirds/) · [Fiveable: lower thirds and titles (3–5 s on screen)](https://fiveable.me/tv-studio-production/unit-7/thirds-titles/study-guide/kQd4R1XeWNW530P9) · [Frame.io: how to make lower third titles that don't suck](https://blog.frame.io/2017/12/04/create-lower-thirds-titles-that-dont-suck/)

## Hand-Drawn Callout Arrow

<a id="hand-drawn-callout-arrow"></a>A wobbly arrow draws itself from a short label to the exact button or number on screen.

Built on [Hand-Drawn Arrow](https://github.com/heygen-com/hyperframes/tree/main/registry/components/hw-arrow) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

A marker-style stroke with a slight boil travels from a two-word note in the margin to the UI target; the head lands last.

- **When:** Point at a small detail in a UI shot that the viewer would otherwise miss.
- **Watch out:** Do not let the arrow cross the product UI it points at; route it around and land on the edge of the target.
- **Timing:** Label 0.3 s, stroke draw 0.5–0.7 s power2.out, hold ≥ 1.5 s.
- **Also called:** annotation arrow, doodle callout, ink arrow
- **Card:** https://skills.varg.ai/skills/hand-drawn-callout-arrow/

### HyperFrames

```bash
npx hyperframes add hw-arrow
```
```js
tl.fromTo("#arrow path",{strokeDashoffset:len},{strokeDashoffset:0,duration:0.6,ease:"power2.out"},2.1);
```

### Remotion

```tsx
// npx shadcn@latest add @remocn/ink-arrow
const draw = interpolate(frame,[0,18],[len,0],{extrapolateRight:'clamp'});
<path strokeDasharray={len} strokeDashoffset={draw}/>
```

### CapCut

Stickers → search "arrow" (hand-drawn), place it, Animation In "Wipe" or keyframe Scale from the tail corner; add a Text label beside it.

### Components

- Hand-Drawn Arrow (hyperframes): `npx hyperframes add hw-arrow` · https://skills.varg.ai/component/hf.hw-arrow/
- Scribble Callout Circle (hyperframes): `npx hyperframes add hw-callout-circle` · https://skills.varg.ai/component/hf.hw-callout-circle/
- Ink Arrow (remocn): `npx shadcn@latest add @remocn/ink-arrow` · https://skills.varg.ai/component/remocn.ink-arrow/
- Arc Motion Path (hyperframes): `npx hyperframes add arc-motion-path` · https://skills.varg.ai/component/hf.arc-motion-path/

Sources: [Text animation for readability: kinetic type without overcomplication](https://cursa.app/en/page/text-animation-for-readability-kinetic-type-without-overcomplication) · [Bohdan Motion: breakdown of the Claude Design launch video](https://x.com/bohdanmotion/status/2080610655237751033)

## Dim Everything But the Target

<a id="dim-around-spotlight"></a>The frame darkens except a soft ellipse around the element being talked about.

Built on [Feathered Spotlight](https://github.com/heygen-com/hyperframes/tree/main/registry/components/yt-feather-highlight) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

A feathered hole in a 50–70% black layer opens over one card, field or chart bar; optional thin ring and label beside it.

- **When:** Dense dashboards or settings screens where a zoom would lose context.
- **Watch out:** Do not leave the dim on for more than a beat or two; return to the full frame before the next point.
- **Timing:** Dim in 0.3 s, hold 1.5–3 s, release 0.3 s. Move the hole with power2.inOut.
- **Also called:** feathered spotlight, focus highlight, vignette callout
- **Card:** https://skills.varg.ai/skills/dim-around-spotlight/

### FFmpeg

```bash
-vf "vignette=angle=PI/4:x0=1190:y0=430:enable='between(t,4,7)'"
```

### HyperFrames

```bash
npx hyperframes add yt-feather-highlight
```
Animate the hole's CSS variables on the timeline: `tl.to(el,{"--x":"62%","--y":"40%","--r":"180px",duration:0.5,ease:"power2.inOut"},t)`.

### Remotion

```tsx
const o = interpolate(frame,[0,9],[0,0.65],{extrapolateRight:'clamp'});
<AbsoluteFill style={{background:`radial-gradient(circle 180px at 62% 40%, transparent 70%, rgba(0,0,0,${o}))`}}/>
```

### CapCut

Duplicate the clip on an overlay track, apply Mask → Circle (feather ~30) on the top copy, lower the bottom copy's brightness (Adjust → Brightness −40).

### Components

- Feathered Spotlight (hyperframes): `npx hyperframes add yt-feather-highlight` · https://skills.varg.ai/component/hf.yt-feather-highlight/
- True Focus (react-bits): `npx shadcn@latest add @react-bits/TrueFocus-JS-CSS` · https://skills.varg.ai/component/reactbits.true-focus/
- Pointer Circle + Countdown (hyperframes): `npx hyperframes add yt-circle-pointer` · https://skills.varg.ai/component/hf.yt-circle-pointer/

Sources: [Trainn: how to add zoom effects to product demo videos](https://trainn.co/answers/how-to-add-zoom-effects-to-product-demo-videos/) · [Consensus: 5 tips to record the best product video](https://goconsensus.com/blog/5-crucial-tips-to-recording-the-best-product-video)

## Impact Headline Slam

<a id="impact-headline-slam"></a>A heavy headline scales down hard into frame and lands with a 2–3 frame shake.

Built on [Headline Slam](https://github.com/heygen-com/hyperframes/tree/main/registry/components/headline-slam) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Condensed black type arrives from 140% scale with motion blur, stops dead, the frame jolts once, then everything is still.

- **When:** The single loudest claim in a hype cut, or the product name on the music drop.
- **Watch out:** Do not slam more than once or twice per film; repeated impacts read as noise.
- **Timing:** Scale-in 0.18–0.25 s (power4.in), shake 3 frames, then a 1–1.5 s hold. Put it on the beat.
- **Also called:** title slam, punch title, shutter slam
- **Card:** https://skills.varg.ai/skills/impact-headline-slam/

### HyperFrames

```bash
npx hyperframes add headline-slam
```
Place the block so its land frame sits on the downbeat (`data-start` = beatTime − 0.2).

### Remotion

```tsx
// npx shadcn@latest add @remocn/impact-shake
const s = interpolate(frame,[0,6],[1.4,1],{extrapolateRight:'clamp',easing:Easing.in(Easing.exp)});
const shake = frame>=6&&frame<9 ? (frame%2?6:-6) : 0;
```

### CapCut

Text → Animation In: "Zoom in"/"Slam" 0.2 s; add Effects → "Shake" for 3 frames on the land; add a whoosh/impact from Audio → Sound effects.

### Components

- Headline Slam (hyperframes): `npx hyperframes add headline-slam` · https://skills.varg.ai/component/hf.headline-slam/
- Shutter Slam (hyperframes): `npx hyperframes add shutter-slam` · https://skills.varg.ai/component/hf.shutter-slam/
- Impact Shake (remocn): `npx shadcn@latest add @remocn/impact-shake` · https://skills.varg.ai/component/remocn.impact-shake/

Sources: [Jamie on X: SFX breakdown of a launch video](https://x.com/jamiesmotion/status/2110099791958982703) · [NewscastStudio: Apple brings its aesthetic to a sports graphics package](https://www.newscaststudio.com/2022/04/11/apple-tv-friday-night-baseball/)

## Phrase Builds From the Center

<a id="center-build-phrase"></a>Words arrive one at a time and push the growing phrase so it always sits centered.

Built on [Kinetic Center Build](https://github.com/heygen-com/hyperframes/tree/main/registry/components/kinetic-center-build) by Remocn (hyperframes), Apache-2.0. The write-up and recipes are varg's.

First word lands center; each next word drives in from the right and shoves the line left until the full phrase locks center.

- **When:** Say the tagline in sync with the voiceover, word for word.
- **Watch out:** Do not time words to a fixed interval; cue each one from the word timestamps of the voiceover.
- **Timing:** Each word 0.25–0.35 s, expo.out; final hold ≥ 1 s.
- **Also called:** kinetic center build, word push, voiceover words
- **Card:** https://skills.varg.ai/skills/center-build-phrase/

### HyperFrames

```bash
npx hyperframes add kinetic-center-build
```
Feed word start times from the transcript JSON into the block variables so each push lands on its spoken word.

### Remotion

```tsx
// npx shadcn@latest add @remocn/kinetic-center-build
const shown = words.filter(w => frame >= w.startMs/1000*fps);
```

### CapCut

Captions → Auto captions (word-level), then style each caption chunk as a single word in the center; Animation In "Slide left" 0.25 s.

### Components

- Kinetic Center Build (hyperframes): `npx hyperframes add kinetic-center-build` · https://skills.varg.ai/component/hf.kinetic-center-build/
- Kinetic Center Build (animata): `npx shadcn@latest add https://animata.design/r/text/kinetic-center-build.json` · https://skills.varg.ai/component/animata.kinetic-center-build/
- Word Push (remocn): `npx shadcn@latest add @remocn/word-push` · https://skills.varg.ai/component/remocn.word-push/

Sources: [Kinetic typography without After Effects (plan ~2 words per second)](https://oakgen.ai/blog/kinetic-typography-without-after-effects) · [SVGator: kinetic typography, a guide to text in motion](https://www.svgator.com/blog/kinetic-typography-a-guide-to-text-in-motion/)

## Specular Sweep Title

<a id="specular-sweep-title"></a>A static title receives one clean light sweep through its glyphs, then rests.

Built on [Text Shimmer](https://github.com/heygen-com/hyperframes/tree/main/registry/components/text-shimmer) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

A narrow white gradient band passes diagonally through the letters once, like light catching a metal logo.

- **When:** Mark a premium moment: price reveal, plan name, the product name in the end card.
- **Watch out:** Do not loop the sweep; one pass is polish, a loop is a loading state.
- **Timing:** One pass 0.8–1.2 s, power2.inOut, starting ~0.3 s after the title settles.
- **Also called:** shimmer title, shine sweep, metal glint
- **Card:** https://skills.varg.ai/skills/specular-sweep-title/

### HyperFrames

```bash
npx hyperframes add shimmer-sweep
```
```js
tl.fromTo(".title",{"--sweep":"-30%"},{"--sweep":"130%",duration:1,ease:"power2.inOut"},1.2);
```

### Remotion

```tsx
// npx shadcn@latest add @remocn/shimmer-sweep
const x = interpolate(frame,[30,60],[-30,130],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
backgroundImage:`linear-gradient(110deg,#999 ${x-10}%,#fff ${x}%,#999 ${x+10}%)`, WebkitBackgroundClip:'text'
```

### CapCut

Effects → search "shine"/"light sweep" and apply only to the text layer for 1 s.

### Components

- Text Shimmer (hyperframes): `npx hyperframes add text-shimmer` · https://skills.varg.ai/component/hf.text-shimmer/
- Shimmer Sweep (hyperframes): `npx hyperframes add shimmer-sweep` · https://skills.varg.ai/component/hf.shimmer-sweep/
- Shimmering Text (animate-ui): `npm install @animate-ui/react motion` · https://skills.varg.ai/component/animateui.shimmering-text/
- Shimmer Sweep (remocn): `npx shadcn@latest add @remocn/shimmer-sweep` · https://skills.varg.ai/component/remocn.shimmer-sweep/

Sources: [NewscastStudio: Apple brings its aesthetic to a sports graphics package](https://www.newscaststudio.com/2022/04/11/apple-tv-friday-night-baseball/) · [Codrops: 7 must-know GSAP animation tips](https://tympanus.net/codrops/2025/09/03/7-must-know-gsap-animation-tips-for-creative-developers/)

## Decode-In Tech Title

<a id="decode-in-tech-title"></a>Random glyphs churn and lock into the real word from left to right.

Built on [Matrix Decode](https://github.com/heygen-com/hyperframes/tree/main/registry/components/matrix-decode) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Monospace characters flicker through symbols and settle one by one into the product or feature name.

- **When:** Developer tools, security, AI or infra products; feature names that are code-like.
- **Watch out:** Do not scramble long sentences; keep it to 1–3 words or it becomes unreadable noise.
- **Timing:** 0.6–1.0 s total, each glyph locks 30–50 ms after the previous one. Use a fixed seed so renders match.
- **Also called:** scramble text, matrix decode, hacker reveal
- **Card:** https://skills.varg.ai/skills/decode-in-tech-title/

### HyperFrames

```bash
npx hyperframes add matrix-decode
```
The block is seek-safe: the glyph at any frame is derived from time + seed, so preview and render match.

### Remotion

```tsx
const locked = Math.floor(interpolate(frame,[0,24],[0,text.length],{extrapolateRight:'clamp'}));
const out = text.split('').map((c,i)=> i<locked? c : GLYPHS[(i*7+frame*13)%GLYPHS.length]).join('');
```

### CapCut

Text → Animation In: "Typewriter" or "Glitch" 0.6 s on a monospace font.

### Components

- Matrix Decode (hyperframes): `npx hyperframes add matrix-decode` · https://skills.varg.ai/component/hf.matrix-decode/
- Hyper Text (magic-ui): `npx shadcn@latest add @magicui/hyper-text` · https://skills.varg.ai/component/magicui.hyper-text/
- Scramble Reveal (hyperframes): `npx hyperframes add scramble-reveal` · https://skills.varg.ai/component/hf.scramble-reveal/
- Text Scramble (motion-primitives): `npx motion-primitives@latest add text-scramble` · https://skills.varg.ai/component/motionprimitives.text-scramble/

Sources: [SVGator: kinetic typography, a guide to text in motion](https://www.svgator.com/blog/kinetic-typography-a-guide-to-text-in-motion/)

## Footage Inside the Letters

<a id="footage-inside-letters"></a>Huge block letters act as windows onto playing product footage or a demo clip.

Built on [Video Text](https://github.com/magicuidesign/magicui/blob/main/apps/www/registry/magicui/video-text.tsx) by magic-ui, MIT. The write-up and recipes are varg's.

Full-bleed heavy type on black or white; the product video plays only through the letterforms.

- **When:** Open a launch film with the product name, or bridge into a demo by expanding the letters.
- **Watch out:** Do not use thin fonts; strokes under ~12% of the cap height show too little footage.
- **Timing:** Hold 1.5–2.5 s; optionally scale the type up 4–8× over 0.6 s to fall into the footage.
- **Also called:** video text, knockout type, text mask video
- **Card:** https://skills.varg.ai/skills/footage-inside-letters/

### HyperFrames

```bash
npx hyperframes add texture-mask-text
```
Place the `<video class="clip">` inside the masked wrapper; animate the wrapper scale, not the video.

### Remotion

```tsx
// npx shadcn@latest add @magicui/video-text
<div style={{WebkitMaskImage:'url(#word)', maskImage:'url(#word)'}}><OffthreadVideo src={demo}/></div>
```

### CapCut

Put white text on black as the lower layer and the footage above it, then set the footage Blend → "Multiply" so it only shows through the letters.

### Components

- Video Text (magic-ui): `npx shadcn@latest add @magicui/video-text` · https://skills.varg.ai/component/magicui.video-text/
- Texture Mask Text (hyperframes): `npx hyperframes add texture-mask-text` · https://skills.varg.ai/component/hf.texture-mask-text/

Sources: [Lago: we killed our motion design job (Linear-style films, Remotion)](https://getlago.com/blog/we-killed-our-motion-design-job) · [Bohdan Motion: breakdown of the Replit Design launch video](https://x.com/bohdanmotion/status/2083248851750728188)

## Tracking-In Feature Label

<a id="tracking-in-label"></a>Wide-spaced letters draw together into a tight, crisp label as the blur clears.

Built on [Tracking In](https://github.com/heygen-com/hyperframes/tree/main/registry/components/tracking-in) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

A short label starts with very wide tracking and soft blur, then closes to normal spacing with a tiny spring.

- **When:** Feature names, plan names and section labels over UI — quiet and premium.
- **Watch out:** Do not use it on paragraphs or long names; tracking changes reflow the whole line.
- **Timing:** 0.6–0.9 s, expo.out; letter-spacing from ~0.5 em to 0.
- **Also called:** letter-spacing reveal, tracking in, premium label
- **Card:** https://skills.varg.ai/skills/tracking-in-label/

### HyperFrames

```bash
npx hyperframes add tracking-in
```
```js
tl.from(".label",{letterSpacing:"0.5em",filter:"blur(6px)",opacity:0,duration:0.8,ease:"expo.out"},0.4);
```

### Remotion

```tsx
// npx shadcn@latest add @remocn/tracking-in
const p = spring({frame,fps,config:{damping:18,stiffness:120}});
letterSpacing:`${interpolate(p,[0,1],[0.5,0])}em`
```

### CapCut

Text → Animation In: "Spread in"/"Letter spacing" 0.6–0.8 s.

### Components

- Tracking In (hyperframes): `npx hyperframes add tracking-in` · https://skills.varg.ai/component/hf.tracking-in/
- Tracking In (remocn): `npx shadcn@latest add @remocn/tracking-in` · https://skills.varg.ai/component/remocn.tracking-in/
- Micro Scale Fade (remocn): `npx shadcn@latest add @remocn/micro-scale-fade` · https://skills.varg.ai/component/remocn.micro-scale-fade/

Sources: [Text animation for readability: kinetic type without overcomplication](https://cursa.app/en/page/text-animation-for-readability-kinetic-type-without-overcomplication) · [Material Design: motion duration and easing](https://m1.material.io/motion/duration-easing.html)
