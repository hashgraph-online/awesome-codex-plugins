# Customer logos

Trusted-by marquees, logo grids, partner lockups and integration orbits. 7 takes. Browse them with previews at https://skills.varg.ai/browse/skills/logo-walls/.

Logos signal trust only when they look like one calm group: monochrome, equal optical height, even spacing, and recognizable names. Use marquees for breadth and static grids for recognition, keep motion slow, and only show logos you have permission to use.

## Trusted-By Logo Marquee

<a id="trusted-by-marquee"></a>A row of monochrome customer logos glides sideways in a seamless loop under a short line.

Built on [Infinite Slider](https://github.com/ibelick/motion-primitives/blob/main/components/core/infinite-slider.tsx) by motion-primitives, MIT. The write-up and recipes are varg's.

Logos in one color (white on dark, grey on light) at equal optical height, even gaps, faded edges, slow constant speed.

- **When:** After the hook or before the CTA, as quiet credibility.
- **Watch out:** Do not mix full-color logos at different sizes; grayscale at a uniform height reads as one trustworthy group.
- **Timing:** Loop 20–40 s for a full row; in a 3–5 s shot it should move ~10–20% of its width.
- **Also called:** logo slider, logo strip, customer marquee
- **Card:** https://skills.varg.ai/skills/trusted-by-marquee/

### FFmpeg

```bash
# scroll a wide logo strip (strip.png is 2× frame width, logos duplicated)
ffmpeg -i bg.mp4 -loop 1 -i strip.png -filter_complex "[0][1]overlay=x='-mod(t*120\,1920)':y=820:shortest=1" out.mp4
```

### HyperFrames

```bash
npx hyperframes add trust-strip
```
For motion: duplicate the row and tween `xPercent:-50` with `ease:"none"` over the clip.

### Remotion

```tsx
// npx shadcn@latest add @remocn/infinite-marquee
const x = -((frame * 2) % rowWidth);
<div style={{transform:`translateX(${x}px)`, filter:'grayscale(1) brightness(1.8)'}}>{logos}{logos}</div>
```

### CapCut

Overlay a long strip PNG of logos; keyframe Position X right → left across the clip; set Opacity 70%.

### Components

- Infinite Slider (motion-primitives): `npx motion-primitives@latest add infinite-slider` · https://skills.varg.ai/component/motionprimitives.infinite-slider/
- Infinite Marquee (remocn): `npx shadcn@latest add @remocn/infinite-marquee` · https://skills.varg.ai/component/remocn.infinite-marquee/
- Trust Strip (hyperframes): `npx hyperframes add trust-strip` · https://skills.varg.ai/component/hf.trust-strip/

Sources: [Genesys Growth: designing customer logo walls](https://genesysgrowth.com/blog/designing-customer-logo-walls) · [Huemor: logo bar](https://huemor.rocks/glossary/logo-bar/) · [Magic UI: Marquee](https://magicui.design/docs/components/marquee)

## Logo Grid Settles In

<a id="logo-grid-settles"></a>Logos fade and scale into a tidy grid with a soft stagger, then hold for a beat.

Built on [Logo Wall](https://github.com/heygen-com/hyperframes/tree/main/registry/components/logo-wall) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

3×3 or 4×2 grid, equal cell sizes, monochrome marks, thin dividers or none; one row at a time.

- **When:** A static "used by" moment where you want logos recognized, not just sensed.
- **Watch out:** Do not show more than ~12 logos; recognition drops when they shrink below ~6% of frame width.
- **Timing:** Each logo 0.3–0.4 s (scale 0.9→1, opacity), 40–60 ms stagger; hold ≥ 1.5 s.
- **Also called:** logo wall, logo cloud, customer grid
- **Card:** https://skills.varg.ai/skills/logo-grid-settles/

### HyperFrames

```bash
npx hyperframes add logo-wall
```
Swap the placeholder lettermarks for real SVGs; keep `filter: grayscale(1)`.

### Remotion

```tsx
logos.map((l,i)=>{const s=spring({frame:frame-i*2,fps,config:{damping:200}}); return <Img src={l} style={{opacity:s, transform:`scale(${0.9+0.1*s})`, filter:'grayscale(1)'}}/>})
```

### CapCut

Place logo PNGs in a grid on one frame; Animation In "Fade in" with 2-frame offsets per logo.

### Components

- Logo Wall (hyperframes): `npx hyperframes add logo-wall` · https://skills.varg.ai/component/hf.logo-wall/
- Animated Group (motion-primitives): `npx motion-primitives@latest add animated-group` · https://skills.varg.ai/component/motionprimitives.animated-group/
- Stagger Lattice (hyperframes): `npx hyperframes add stagger-lattice` · https://skills.varg.ai/component/hf.stagger-lattice/

Sources: [Genesys Growth: designing customer logo walls](https://genesysgrowth.com/blog/designing-customer-logo-walls) · [Huemor: logo bar](https://huemor.rocks/glossary/logo-bar/)

## Integrations Orbit the Logo

<a id="integrations-orbit"></a>App icons circle your logo on one or two thin rings turning in opposite directions.

Built on [Orbiting Circles](https://github.com/magicuidesign/magicui/blob/main/apps/www/registry/magicui/orbiting-circles.tsx) by magic-ui, MIT. The write-up and recipes are varg's.

Your mark centered; partner icons in small round chips on faint rings; inner ring clockwise, outer counter-clockwise, slow.

- **When:** "Works with the tools you use" beats; integrations and MCP connectors.
- **Watch out:** Do not spin fast; at more than one turn per ~20 s icons blur and look cheap.
- **Timing:** Ring period 20–40 s; icons fade in with 50 ms stagger; hold 2–3 s.
- **Also called:** integration orbit, orbiting icons, ecosystem
- **Card:** https://skills.varg.ai/skills/integrations-orbit/

### HyperFrames

```bash
npx hyperframes add locked-nucleus-orbit
```
Or drive `rotation` on two ring wrappers from the timeline (`ease:"none"`), counter-rotating each icon to stay upright.

### Remotion

```tsx
const a = (frame / (fps*30)) * Math.PI*2;
icons.map((ic,i)=>{const t=a+i*(2*Math.PI/icons.length); return <Img src={ic} style={{transform:`translate(${Math.cos(t)*R}px,${Math.sin(t)*R}px)`}}/>})
```

### CapCut

Place icons around a ring image, group them, and keyframe Rotation 0 → 45° across the clip; counter-rotate isn't needed for round chips.

### Components

- Orbiting Circles (magic-ui): `npx shadcn@latest add @magicui/orbiting-circles` · https://skills.varg.ai/component/magicui.orbiting-circles/
- Orbiting Items 3D (animata): `npx shadcn@latest add https://animata.design/r/list/orbiting-items-3-d.json` · https://skills.varg.ai/component/animata.orbiting-items-3-d/
- Ecosystem Constellation (remocn): `npx shadcn@latest add @remocn/ecosystem-constellation` · https://skills.varg.ai/component/remocn.ecosystem-constellation/

Sources: [Bohdan Motion: breakdown of the Replit Design launch video](https://x.com/bohdanmotion/status/2083248851750728188) · [Magic UI: Animated Beam](https://v3.magicui.design/docs/components/animated-beam)

## Partner × Partner Lockup

<a id="partner-lockup"></a>Two logos slide together from opposite sides and lock around a thin × or + mark.

Built on [Logo Brand Close](https://github.com/heygen-com/hyperframes/tree/main/registry/components/logo-brand-close) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Equal optical size, a hairline separator or ×; both marks resolve from blur to sharp at the same moment.

- **When:** Partnership announcements, integrations launches, co-marketing films.
- **Watch out:** Do not let one logo dominate unless the partnership is unequal on purpose.
- **Timing:** Slide 0.6–0.8 s expo.out, × fades in 0.2 s after, hold 2 s.
- **Also called:** co-brand lockup, partnership reveal, logo x logo
- **Card:** https://skills.varg.ai/skills/partner-lockup/

### HyperFrames

```bash
npx hyperframes add focus-blur-resolve
```
```js
tl.from("#a",{x:-160,filter:"blur(10px)",opacity:0,duration:0.7,ease:"expo.out"},0)
  .from("#b",{x:160,filter:"blur(10px)",opacity:0,duration:0.7,ease:"expo.out"},0)
  .from("#x",{scale:0.6,opacity:0,duration:0.2},0.5);
```

### Remotion

```tsx
const p = spring({frame, fps, config:{damping:200}});
<Img src={a} style={{transform:`translateX(${interpolate(p,[0,1],[-160,0])}px)`, filter:`blur(${(1-p)*10}px)`}}/>
```

### CapCut

Two logo overlays: Animation In "Slide right" / "Slide left" 0.6 s; a Text "×" with Fade in.

### Components

- Logo Brand Close (hyperframes): `npx hyperframes add logo-brand-close` · https://skills.varg.ai/component/hf.logo-brand-close/
- Focus Blur Resolve (hyperframes): `npx hyperframes add focus-blur-resolve` · https://skills.varg.ai/component/hf.focus-blur-resolve/
- Logo Enter (remocn): `npx shadcn@latest add @remocn/logo-enter` · https://skills.varg.ai/component/remocn.logo-enter/

Sources: [Huemor: logo bar](https://huemor.rocks/glossary/logo-bar/)

## Brand Chips Spring In

<a id="brand-chips-spring-in"></a>Round brand chips pop in one by one with a spring and overlap into a tidy stack.

Built on [Logo Enter](https://remocn.dev/r/logo-enter.json) by Kapish Dima (remocn), MIT. The write-up and recipes are varg's.

Circular chips with white borders, each overlapping the last by ~25%, springing from 0 to 1 scale.

- **When:** "Supports GPT, Claude, Gemini…" or "Used at" beats when space is tight (lower third, corner).
- **Watch out:** Do not show more than 6–7 chips; add a "+40" chip instead.
- **Timing:** Each chip 0.3 s spring (damping ~12), 60–80 ms stagger.
- **Also called:** logo chips, avatar stack logos, model logos
- **Card:** https://skills.varg.ai/skills/brand-chips-spring-in/

### HyperFrames

```bash
npx hyperframes add badge-pop
```
`tl.from(".chip",{scale:0,duration:0.3,ease:"back.out(1.8)",stagger:0.07})`

### Remotion

```tsx
// npx shadcn@latest add @remocn/logo-enter
<LogoEnter logos={[gpt, claude, gemini, krea]} />
```

### CapCut

Logo PNGs in circular Masks, overlapping; Animation In "Pop up" with 2-frame offsets.

### Components

- Logo Enter (remocn): `npx shadcn@latest add @remocn/logo-enter` · https://skills.varg.ai/component/remocn.logo-enter/
- Badge Pop (hyperframes): `npx hyperframes add badge-pop` · https://skills.varg.ai/component/hf.badge-pop/
- Avatar Group Hover (hyperframes): `npx hyperframes add avatar-group-hover` · https://skills.varg.ai/component/hf.avatar-group-hover/

Sources: [Bohdan Motion: breakdown of the Replit Design launch video](https://x.com/bohdanmotion/status/2083248851750728188)

## Logos Float Past in Depth

<a id="model-logos-float-past"></a>Partner or model logos drift past on a tilted plane, sharp near the camera and blurred toward the horizon.

Built on [Perspective Marquee](https://github.com/heygen-com/hyperframes/tree/main/registry/components/perspective-marquee) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

A 3D-tilted marquee of logos receding into depth with depth-of-field blur; slow, cinematic.

- **When:** Outros that say "not locked into one vendor" or show a broad ecosystem.
- **Watch out:** Do not mix this with a flat marquee in the same film; pick one logo language.
- **Timing:** Constant drift 2–4 s per logo crossing; tilt 20–35°.
- **Also called:** perspective marquee, 3D logo stream, floating logos
- **Card:** https://skills.varg.ai/skills/model-logos-float-past/

### HyperFrames

```bash
npx hyperframes add perspective-marquee
```

### Remotion

```tsx
// npx shadcn@latest add @remocn/perspective-marquee
<PerspectiveMarquee items={logos} tilt={28} />
```

### CapCut

Make a flat logo marquee clip first, then apply Effects → "3D" or Basic → rotate in 3D and a Blur gradient mask at the far end.

### Components

- Perspective Marquee (hyperframes): `npx hyperframes add perspective-marquee` · https://skills.varg.ai/component/hf.perspective-marquee/
- Perspective Marquee (remocn): `npx shadcn@latest add @remocn/perspective-marquee` · https://skills.varg.ai/component/remocn.perspective-marquee/

Sources: [Bohdan Motion: breakdown of the Replit Design launch video](https://x.com/bohdanmotion/status/2083248851750728188)

## Integration Logos Light Up

<a id="integration-logos-light-up"></a>A grid of integration tiles sits dim; each lights with a traveling border glow as the narration names it.

Built on [Constellation Hub](https://github.com/heygen-com/hyperframes/tree/main/registry/components/constellation-hub) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Muted tiles with a thin bright segment racing around the active tile's border; the logo brightens to full color.

- **When:** Name three or four key integrations out of many while keeping the others visible.
- **Watch out:** Do not light all tiles; the dim ones give scale, the lit ones give focus.
- **Timing:** Light each 0.3 s on its spoken word; border segment loop 1.5–2.5 s.
- **Also called:** logo grid highlight, connected tools, border light
- **Card:** https://skills.varg.ai/skills/integration-logos-light-up/

### HyperFrames

```bash
npx hyperframes add constellation-hub
```
Cue each tile's `brightness`/`grayscale` tween to its transcript word time.

### Remotion

```tsx
// npx shadcn@latest add @magicui/border-beam
const lit = cues.some(c => frame >= c.f && frame < c.f + 60 && c.i === i);
<Tile style={{filter: lit? 'none':'grayscale(1) brightness(0.6)'}}>{lit && <BorderBeam/>}</Tile>
```

### CapCut

Grid of logos at 50% opacity; duplicate the active logo on top at 100% with a glow sticker, timed to the voiceover.

### Components

- Constellation Hub (hyperframes): `npx hyperframes add constellation-hub` · https://skills.varg.ai/component/hf.constellation-hub/
- Border Trail (motion-primitives): `npx motion-primitives@latest add border-trail` · https://skills.varg.ai/component/motionprimitives.border-trail/
- Border Beam (magic-ui): `npx shadcn@latest add @magicui/border-beam` · https://skills.varg.ai/component/magicui.border-beam/

Sources: [Genesys Growth: designing customer logo walls](https://genesysgrowth.com/blog/designing-customer-logo-walls)
