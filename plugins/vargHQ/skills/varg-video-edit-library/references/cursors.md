# Cursors & clicks

Smooth cursor paths, click ripples, keystroke overlays, agent cursors and the auto-zoom that follows the pointer. 9 takes. Browse them with previews at https://skills.varg.ai/browse/skills/cursors/.

The cursor is the viewer's guide, so it must be smooth, large enough to see on a phone, and predictable. Smooth the path, ease every move (0.4–0.9 s, ease-out), mark clicks with a quiet ring and a press, and zoom toward the click just before it happens; on phones use touch circles, not arrows.

## Auto Zoom on Every Click

<a id="auto-zoom-on-click"></a>The camera eases in toward each upcoming click, trails the cursor on a spring, and eases out after.

Built on [Zoom Follow Cursor](https://github.com/heygen-com/hyperframes/tree/main/registry/components/cursor-zoom-follow) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Zoom begins slightly before the click, the frame follows the cursor smoothly, each click gets a ring; between actions the camera returns to full view.

- **When:** Any cursor-driven screen recording; it is the default polish for SaaS demos.
- **Watch out:** Do not track every mouse jitter; smooth the path and only re-target when the cursor dwells.
- **Timing:** Lead the click by 0.3–0.5 s, zoom 1.5–2×, follow spring damping ~20, ease out 0.6 s.
- **Also called:** screen studio zoom, zoom to cursor, click zoom
- **Card:** https://skills.varg.ai/skills/auto-zoom-on-click/

### FFmpeg

```bash
# zoom around a known click (x=1380,y=420) from 4.0 s to 6.0 s
-vf "zoompan=z='if(between(it,3.6,6),min(zoom+0.04,1.8),max(zoom-0.04,1))':x='1380-iw/zoom/2':y='420-ih/zoom/2':d=1:s=1920x1080:fps=60"
```

### HyperFrames

```bash
npx hyperframes add cursor-zoom-follow
```
Set slots: `image`, `zoom` (1.8), `click1_x/y`, `click2_x/y`, `click3_x/y`, `accent`.

### Remotion

```tsx
// npx shadcn@latest add @remocn/cursor
const z = clicks.reduce((acc,c)=> acc + interpolate(frame,[c.f-15,c.f,c.f+40,c.f+58],[0,0.8,0.8,0],{extrapolateLeft:'clamp',extrapolateRight:'clamp'}),1);
const origin = `${smoothX}px ${smoothY}px`;
```

### CapCut

Desktop: select the recording → Video → Basic → keyframe Scale/Position around each click; use Graphs → "Ease in-out".

### Components

- Zoom Follow Cursor (hyperframes): `npx hyperframes add cursor-zoom-follow` · https://skills.varg.ai/component/hf.cursor-zoom-follow/
- UI Cursor (remocn): `npx shadcn@latest add @remocn/cursor` · https://skills.varg.ai/component/remocn.cursor/
- UI Focus Zoom (hyperframes): `npx hyperframes add ui-focus-zoom` · https://skills.varg.ai/component/hf.ui-focus-zoom/

Sources: [Screen Studio: auto zoom, cursor smoothing, click effects](https://screen.studio/) · [OpenScreen docs: creating demos (zoom regions from cursor dwell)](https://www.mintlify.com/siddharthvaddem/openscreen/guides/creating-demos) · [zero on X: Apple-keynote launch film prompt (Screen Studio zoom, no crossfades)](https://x.com/twoclipping/status/2103835273813496100)

## Oversized Look-Here Cursor

<a id="oversized-look-here-cursor"></a>A macOS arrow at ~3–4× normal size glides in and lands its tip on what matters.

Built on [Oversized Cursor](https://github.com/heygen-com/hyperframes/tree/main/registry/components/oversized-cursor) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

A crisp, oversized pointer with a soft shadow enters from off-frame in one arc, presses with a small squash, and leaves.

- **When:** Launch films where the cursor is a character guiding the eye, especially on mocked UI.
- **Watch out:** Do not use a tiny system cursor in a 1080p film; it disappears on phones.
- **Timing:** Entry 0.4–0.9 s power3.out; press scale 0.84 in 0.1 s, release 0.22 s; exit 0.5–0.7 s power2.in.
- **Also called:** big cursor, hero pointer, guide cursor
- **Card:** https://skills.varg.ai/skills/oversized-look-here-cursor/

### HyperFrames

```bash
npx hyperframes add oversized-cursor
```
```js
tl.fromTo("#cur",{top:"118%"},{top:"42%",left:"61%",duration:0.85,ease:"power3.out",immediateRender:false},0.25)
  .to("#cur",{scale:0.84,duration:0.1,ease:"power2.in",transformOrigin:"21% 14%"},1.2)
  .to("#cur",{scale:1,duration:0.22,ease:"power2.out"},1.3);
```

### Remotion

```tsx
// npx shadcn@latest add @remocn/simulated-cursor
<Img src={arrow} style={{width:'7cqw', transform:`translate(${x}px,${y}px) scale(${press})`}}/>
```

### CapCut

Stickers → search "cursor"/"mouse", scale it up ~3×, keyframe Position along the path with ease-out; add a click SFX.

### Components

- Oversized Cursor (hyperframes): `npx hyperframes add oversized-cursor` · https://skills.varg.ai/component/hf.oversized-cursor/
- Press Ripple (hyperframes): `npx hyperframes add press-ripple` · https://skills.varg.ai/component/hf.press-ripple/
- Spotlight Card (hyperframes): `npx hyperframes add spotlight-card` · https://skills.varg.ai/component/hf.spotlight-card/

Sources: [HyperFrames skill: oversized cursor motion conventions](https://tessl.io/registry/skills/github/heygen-com/hyperframes/oversized-cursor--oversized-cursor) · [zero on X: Apple-keynote launch film prompt (Screen Studio zoom, no crossfades)](https://x.com/twoclipping/status/2103835273813496100)

## Click Ripple and Button Press

<a id="click-ripple-press"></a>Every click shows a quiet expanding ring while the clicked button presses in and responds.

Built on [Press Ripple](https://github.com/heygen-com/hyperframes/tree/main/registry/components/press-ripple) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

A thin ring grows from the cursor tip and fades; the button dips to 0.94 scale in sync and returns, then shows its new state.

- **When:** Make clicks legible in recordings with no sound or when cursor moves are fast.
- **Watch out:** Do not use big colorful bursts on every click; save a celebratory burst for the final success.
- **Timing:** Ring 0.35–0.5 s ease-out to ~3× size; button press 0.1 s down, 0.2 s up.
- **Also called:** click effect, ripple, tap feedback
- **Card:** https://skills.varg.ai/skills/click-ripple-press/

### HyperFrames

```bash
npx hyperframes add press-ripple
```
Target the button with the same `t` as the cursor press so both react on one frame.

### Remotion

```tsx
const r = interpolate(frame,[clickAt,clickAt+12],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
<div style={{width:40,height:40,borderRadius:99,border:'2px solid #fff',transform:`scale(${1+r*2})`,opacity:1-r}}/>
```

### CapCut

Stickers → search "click"/"tap" ripple; place on each click frame; Screen Studio exports have this built in.

### Components

- Press Ripple (hyperframes): `npx hyperframes add press-ripple` · https://skills.varg.ai/component/hf.press-ripple/
- Simulated Cursor (remocn): `npx shadcn@latest add @remocn/simulated-cursor` · https://skills.varg.ai/component/remocn.simulated-cursor/
- Success Check (hyperframes): `npx hyperframes add success-check` · https://skills.varg.ai/component/hf.success-check/
- UI Button (remocn): `npx shadcn@latest add @remocn/button` · https://skills.varg.ai/component/remocn.button/

Sources: [Screen Studio: auto zoom, cursor smoothing, click effects](https://screen.studio/) · [HyperFrames skill: oversized cursor motion conventions](https://tessl.io/registry/skills/github/heygen-com/hyperframes/oversized-cursor--oversized-cursor)

## Shortcut Keycaps Overlay

<a id="shortcut-keycaps-overlay"></a>Physical-looking keycaps rise at the bottom of the frame and press in the real order when a shortcut is used.

Built on [Keystroke](https://remocn.dev/r/keystroke.json) by Kapish Dima (remocn), MIT. The write-up and recipes are varg's.

Rounded keycaps (⌘, ⇧, K) appear bottom-center, modifiers stay held while the letter taps, then the row fades.

- **When:** Keyboard-driven tools and tutorials where the shortcut is the lesson.
- **Watch out:** Do not show every keystroke while typing text; only shortcuts and modifier combos.
- **Timing:** Keys rise 0.2 s with 40 ms stagger, press 0.08 s, hold 0.8–1.2 s, fade 0.2 s.
- **Also called:** keystroke overlay, show shortcuts, keycaps
- **Card:** https://skills.varg.ai/skills/shortcut-keycaps-overlay/

### HyperFrames

```bash
npx hyperframes add badge-pop
```
Build keycaps as `<kbd>` elements; `tl.from(".kbd",{y:30,opacity:0,stagger:0.04,duration:0.2})` then press the letter with `scale:0.92`.

### Remotion

```tsx
// npx shadcn@latest add @remocn/keystroke
<Keystroke keys={['⌘','K']} />
```

### CapCut

Text → Text templates → search "keyboard"/"key"; or record with KeyCastr/Screen Studio "Show shortcuts" on.

### Components

- Keystroke (remocn): `npx shadcn@latest add @remocn/keystroke` · https://skills.varg.ai/component/remocn.keystroke/
- Badge Pop (hyperframes): `npx hyperframes add badge-pop` · https://skills.varg.ai/component/hf.badge-pop/

Sources: [KeyCastr: open-source keystroke visualizer](https://github.com/keycastr/keycastr) · [Screen Studio: auto zoom, cursor smoothing, click effects](https://screen.studio/)

## Named Agent Cursor

<a id="named-agent-cursor"></a>A cursor with an accent name tag ("Claude", "Agent") moves and clicks on its own, typing each step.

Built on [Agent Cursor](https://github.com/heygen-com/hyperframes/tree/main/registry/components/agent-cursor) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

A colored arrow with a pill label like a multiplayer cursor; the label shows the current step ("Opening settings…").

- **When:** AI agents that operate a UI: computer use, browser agents, design agents.
- **Watch out:** Do not let the agent cursor look like the user's; give it a distinct color and label.
- **Timing:** Moves 0.5–0.8 s power2.inOut, label text swaps 0.25 s, dwell 0.4 s before each click.
- **Also called:** AI cursor, agent pointer, labeled cursor
- **Card:** https://skills.varg.ai/skills/named-agent-cursor/

### HyperFrames

```bash
npx hyperframes add agent-cursor
```
Feed the step list as variables; the label types each step before the click.

### Remotion

```tsx
// npx shadcn@latest add @remocn/cursor
<div style={{transform:`translate(${x}px,${y}px)`}}><Arrow color="#7C3AED"/><span className="pill">{steps[i]}</span></div>
```

### CapCut

Cursor sticker + a Text pill grouped as a compound clip; keyframe Position; change the pill text per step.

### Components

- Agent Cursor (hyperframes): `npx hyperframes add agent-cursor` · https://skills.varg.ai/component/hf.agent-cursor/
- Multiplayer Cursors (hyperframes): `npx hyperframes add multiplayer-cursors` · https://skills.varg.ai/component/hf.multiplayer-cursors/
- Avatar Group Hover (hyperframes): `npx hyperframes add avatar-group-hover` · https://skills.varg.ai/component/hf.avatar-group-hover/

Sources: [Cursor 3 Design Mode and its launch video](https://pasqualepillitteri.it/en/news/3794/cursor-design-mode-what-it-is-how-it-works-cursor-3) · [Bohdan Motion: breakdown of the Claude Design launch video](https://x.com/bohdanmotion/status/2080610655237751033)

## Multiplayer Cursors Drift In

<a id="multiplayer-cursors-drift"></a>Several labeled cursors in different colors drift in from the edges and gather on the canvas.

Built on [Multiplayer Cursors](https://github.com/heygen-com/hyperframes/tree/main/registry/components/multiplayer-cursors) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Three to five colored cursors with name tags and soft glows arrive, idle-wobble, and one makes the edit.

- **When:** Collaboration features (Figma-style presence, shared docs) and "for teams" beats.
- **Watch out:** Do not move all cursors in sync; offset timing and paths or it looks robotic.
- **Timing:** Arrivals staggered 0.15–0.3 s, each 0.8–1.2 s power2.out; idle wobble ±6 px over 2 s.
- **Also called:** collaboration cursors, team cursors, live presence
- **Card:** https://skills.varg.ai/skills/multiplayer-cursors-drift/

### HyperFrames

```bash
npx hyperframes add multiplayer-cursors
```
Colors derive from tokens; set names via variables.

### Remotion

```tsx
const wob = Math.sin((frame + i*17)/18)*6;
<Cursor x={baseX+wob} y={baseY+Math.cos((frame+i*11)/22)*6} label={names[i]} color={colors[i]}/>
```

### CapCut

Duplicate a cursor sticker 3–4 times, recolor (Adjust → Hue), add name Text to each, keyframe different paths.

### Components

- Multiplayer Cursors (hyperframes): `npx hyperframes add multiplayer-cursors` · https://skills.varg.ai/component/hf.multiplayer-cursors/
- Avatar Cloud (hyperframes): `npx hyperframes add avatar-cloud` · https://skills.varg.ai/component/hf.avatar-cloud/
- Avatar Group Hover (hyperframes): `npx hyperframes add avatar-group-hover` · https://skills.varg.ai/component/hf.avatar-group-hover/

Sources: [UX Design Bootcamp: the rise of Linear style design](https://bootcamp.uxdesign.cc/the-rise-of-linear-style-design-origins-trends-and-techniques-4fd96aab7646)

## Drag a Card Across Columns

<a id="drag-card-across"></a>The cursor grabs a card, lifts and tilts it while carrying, and drops it into a new column with a settle.

Built on [Drag and Drop Cursor](https://github.com/heygen-com/hyperframes/tree/main/registry/components/cursor-drag-drop) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Card scales to 1.04, tilts ~3° in the direction of travel and gains shadow; on drop it straightens and neighbors shuffle.

- **When:** Task boards, file managers, builders — anything where drag is the core action.
- **Watch out:** Do not move the card at linear speed; drag should accelerate and decelerate like a hand.
- **Timing:** Lift 0.15 s, carry 0.6–0.9 s power2.inOut, drop settle 0.25 s back.out(1.4).
- **Also called:** drag and drop, kanban drag, move task
- **Card:** https://skills.varg.ai/skills/drag-card-across/

### HyperFrames

```bash
npx hyperframes add cursor-drag-drop
```

### Remotion

```tsx
// npx shadcn@latest add @remocn/cursor  (drag waypoint)
const p = interpolate(frame,[10,34],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp',easing:Easing.inOut(Easing.quad)});
const tilt = Math.sin(p*Math.PI)*3;
```

### CapCut

Overlay a card screenshot, keyframe Position and Rotation (0° → 3° → 0°) with a cursor sticker parented by matching keyframes.

### Components

- Drag and Drop Cursor (hyperframes): `npx hyperframes add cursor-drag-drop` · https://skills.varg.ai/component/hf.cursor-drag-drop/
- UI Cursor (remocn): `npx shadcn@latest add @remocn/cursor` · https://skills.varg.ai/component/remocn.cursor/
- Keyframe Scrub Stack (hyperframes): `npx hyperframes add keyframe-scrub-stack` · https://skills.varg.ai/component/hf.keyframe-scrub-stack/

Sources: [Consensus: 5 tips to record the best product video](https://goconsensus.com/blog/5-crucial-tips-to-recording-the-best-product-video) · [HyperFrames skill: oversized cursor motion conventions](https://tessl.io/registry/skills/github/heygen-com/hyperframes/oversized-cursor--oversized-cursor)

## Select Text, Then Act

<a id="select-text-then-act"></a>The arrow becomes an I-beam, drags a selection across a phrase, and a menu or AI action appears on it.

Built on [Text Select Cursor](https://github.com/heygen-com/hyperframes/tree/main/registry/components/cursor-text-select) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Selection grows character by character in the accent color; a small popover ("Rewrite", "Explain") blooms at the selection end.

- **When:** Writing tools, AI editors, docs and code review features.
- **Watch out:** Do not select a whole paragraph instantly; the drag is what makes it believable.
- **Timing:** Drag 0.5–0.8 s, popover 0.2 s scale from 0.9, choose + apply 0.6 s.
- **Also called:** text selection, highlight and rewrite, context menu
- **Card:** https://skills.varg.ai/skills/select-text-then-act/

### HyperFrames

```bash
npx hyperframes add cursor-text-select
npx hyperframes add cursor-context-menu
```

### Remotion

```tsx
const n = Math.floor(interpolate(frame,[0,18],[0,phrase.length],{extrapolateRight:'clamp'}));
<mark style={{background:'#93C5FD'}}>{phrase.slice(0,n)}</mark>{phrase.slice(n)}
```

### CapCut

Record it for real; zoom 160% on the selection; add a pop SFX when the menu appears.

### Components

- Text Select Cursor (hyperframes): `npx hyperframes add cursor-text-select` · https://skills.varg.ai/component/hf.cursor-text-select/
- Context Menu Cursor (hyperframes): `npx hyperframes add cursor-context-menu` · https://skills.varg.ai/component/hf.cursor-context-menu/
- Inline Highlight (hyperframes): `npx hyperframes add inline-highlight` · https://skills.varg.ai/component/hf.inline-highlight/

Sources: [Screen Studio: auto zoom, cursor smoothing, click effects](https://screen.studio/)

## Touch Taps on Phone UI

<a id="touch-taps-on-phone"></a>A translucent touch circle taps, swipes and pulls to refresh on a phone screen instead of an arrow.

Built on [Touch Indicator](https://github.com/heygen-com/hyperframes/tree/main/registry/components/touch-indicator) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

A soft grey dot (~44 pt) appears on touch, compresses on press, drags with momentum on swipes, and fades on release.

- **When:** Mobile app demos and phone mockups; anywhere an arrow cursor would look wrong.
- **Watch out:** Do not show an arrow cursor on a phone; use touch circles sized like a fingertip.
- **Timing:** Tap: appear 0.08 s, press 0.1 s, release 0.15 s. Swipe 0.3–0.5 s with momentum carry.
- **Also called:** tap indicator, touch circle, mobile gestures
- **Card:** https://skills.varg.ai/skills/touch-taps-on-phone/

### HyperFrames

```bash
npx hyperframes add touch-indicator
npx hyperframes add swipe-rail
```
Or `gesture-tap` for a single button tap and `pull-to-refresh` for list pulls.

### Remotion

```tsx
const press = interpolate(frame,[tapAt,tapAt+3,tapAt+8],[0,1,0],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
<div style={{width:88,height:88,borderRadius:99,background:'rgba(255,255,255,0.45)',transform:`scale(${1-press*0.15})`,opacity:press?1:0}}/>
```

### CapCut

Add a white circle shape at 45% opacity on each tap frame (0.2 s), with Animation In "Zoom out"; keyframe its Position for swipes.

### Components

- Touch Indicator (hyperframes): `npx hyperframes add touch-indicator` · https://skills.varg.ai/component/hf.touch-indicator/
- Gesture Tap (hyperframes): `npx hyperframes add gesture-tap` · https://skills.varg.ai/component/hf.gesture-tap/
- Swipe Rail (hyperframes): `npx hyperframes add swipe-rail` · https://skills.varg.ai/component/hf.swipe-rail/
- Share-Sheet Carousel (hyperframes): `npx hyperframes add share-sheet-carousel` · https://skills.varg.ai/component/hf.share-sheet-carousel/

Sources: [Rotato: how to make an animated mockup](https://rotato.app/blog/animated-mockup) · [Screen Studio: auto zoom, cursor smoothing, click effects](https://screen.studio/)
