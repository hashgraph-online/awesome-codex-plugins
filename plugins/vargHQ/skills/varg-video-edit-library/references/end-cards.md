# End cards & CTAs

How a video ends: the call to action, URL and QR code, subscribe prompt, logo outro and the last line. 9 takes. Browse them with previews at https://skills.varg.ai/browse/skills/end-cards/.

The ending does one job: tell the viewer the single next step. A good end card reveals 2–3 items in order (logo, line, CTA or URL), holds at least 2–3 s, and matches the CTA wording on the landing page; on YouTube, leave a calm 5–20 s window with space for up to four end screen elements.

## Logo Lockup Outro

<a id="logo-lockup-outro"></a>The mark assembles, the wordmark settles beside it, then tagline and URL fade in under it.

Built on [Logo Outro](https://github.com/heygen-com/hyperframes/tree/main/registry/blocks/logo-outro) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Centered lockup on the film's backdrop; one soft glow bloom, tagline one size down, URL smallest and last.

- **When:** The last 3–5 s of any launch or product film.
- **Watch out:** Do not stack logo, tagline, URL, socials and a QR at once; reveal 2–3 items in order.
- **Timing:** Mark 0.6–0.8 s, wordmark 0.4 s, tagline +0.3 s, URL +0.3 s; hold ≥ 2 s before the cut.
- **Also called:** brand close, logo resolve, outro logo
- **Card:** https://skills.varg.ai/skills/logo-lockup-outro/

### FFmpeg

```bash
ffmpeg -i film.mp4 -loop 1 -i logo.png -filter_complex "[1]format=rgba,fade=in:st=41:d=0.6:alpha=1[l];[0][l]overlay=(W-w)/2:(H-h)/2-60:enable='gte(t,41)'" out.mp4
```

### HyperFrames

```bash
npx hyperframes add logo-outro
```
```html
<div data-composition-id="logo-outro" data-composition-src="compositions/logo-outro.html"
  data-variable-values='{"tagline":"Video by code","url":"varg.ai"}' data-start="41" data-duration="5" data-track-index="1"></div>
```

### Remotion

```tsx
const logo = spring({frame, fps, config:{damping:12}});
const tag = interpolate(frame,[24,36],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
const url = interpolate(frame,[33,45],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
```

### CapCut

Overlay the logo PNG, Animation In "Zoom in" 0.6 s; Text for tagline and URL with "Fade in" 0.3 s each, staggered.

### Components

- Logo Outro (hyperframes): `npx hyperframes add logo-outro` · https://skills.varg.ai/component/hf.logo-outro/
- Logo Brand Close (hyperframes): `npx hyperframes add logo-brand-close` · https://skills.varg.ai/component/hf.logo-brand-close/
- Logo Sting (hyperframes): `npx hyperframes add logo-sting` · https://skills.varg.ai/component/hf.logo-sting/

Sources: [Bohdan Motion: breakdown of the Grok Build Mode launch video](https://x.com/bohdanmotion/status/2082193183111614671) · [Bohdan Motion: Apple Mac Studio launch film, 10-step playbook](https://x.com/bohdanmotion/status/2093347071440851104)

## Action Line + CTA Button

<a id="action-line-cta-button"></a>One short action line lands, then a real-looking button pops in under it with a soft glow.

Built on [CTA Lockup](https://github.com/heygen-com/hyperframes/tree/main/registry/components/cta-lockup) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

"Start building today" in display type; a pill button with the exact CTA ("Try free") pops with a glow and an optional cursor click.

- **When:** Any film whose goal is a sign-up, demo booking or download.
- **Watch out:** Do not write two CTAs; one verb, one button, matching the landing page's button text.
- **Timing:** Line 0.5 s per-word, button pop 0.3 s back.out(1.6), click at +0.6 s, hold 2–3 s.
- **Also called:** CTA close, call to action, button end card
- **Card:** https://skills.varg.ai/skills/action-line-cta-button/

### HyperFrames

```bash
npx hyperframes add cta-lockup
```
Set the line and button text in `data-variable-values`; optional `press-ripple` for a click on the button.

### Remotion

```tsx
// npx shadcn@latest add @remocn/button  (state = f(frame): idle → hover → press)
const pop = spring({frame: frame-20, fps, config:{damping:10, stiffness:180}});
```

### CapCut

Text for the line; Stickers → search "button" or make a rounded shape + text; Animation In "Pop up"; add a click SFX.

### Components

- CTA Lockup (hyperframes): `npx hyperframes add cta-lockup` · https://skills.varg.ai/component/hf.cta-lockup/
- CTA Close (hyperframes): `npx hyperframes add cta-close` · https://skills.varg.ai/component/hf.cta-close/
- Glow Effect (motion-primitives): `npx motion-primitives@latest add glow-effect` · https://skills.varg.ai/component/motionprimitives.glow-effect/
- UI Button (remocn): `npx shadcn@latest add @remocn/button` · https://skills.varg.ai/component/remocn.button/

Sources: [Bohdan Motion: Secureframe launch video, one pain per scene](https://x.com/bohdanmotion/status/2069369111231049803) · [Bohdan Motion: breakdown of the ElevenLabs Flows launch video](https://x.com/bohdanmotion/status/2079974237893456071)

## URL Typed Into the Address Bar

<a id="url-typed-in-bar"></a>A browser bar appears and the product URL types itself in, then the page loads into the hero.

Built on [Safari](https://github.com/magicuidesign/magicui/blob/main/apps/www/registry/magicui/safari.tsx) by magic-ui, MIT. The write-up and recipes are varg's.

A clean Safari/Chrome bar centered on the backdrop; characters type with a caret; Enter press; the landing page fills the window.

- **When:** Web products where the URL is the CTA; also a smooth bridge back into the product for a final shot.
- **Watch out:** Do not type long paths or UTM strings; just the domain (varg.ai/video at most).
- **Timing:** Typing 50–80 ms/char, Enter + 0.2 s, page load 0.4 s, hold 2 s.
- **Also called:** type the URL, address bar CTA, domain reveal
- **Card:** https://skills.varg.ai/skills/url-typed-in-bar/

### HyperFrames

```bash
npx hyperframes add typewriter
npx hyperframes add browser-device-stage
```
Type inside the stage's address field; cut the page screenshot in with a 0.4 s fade at Enter.

### Remotion

```tsx
// npx shadcn@latest add @magicui/safari
const n = Math.floor(interpolate(frame,[0,url.length*2],[0,url.length],{extrapolateRight:'clamp'}));
<Safari url={url.slice(0,n)} imageSrc={frame>enterAt? hero : undefined}/>
```

### CapCut

Screenshot a browser bar as an Overlay; add Text with Animation In "Typewriter" 1 s over the field; cut to the site screenshot.

### Components

- Safari (magic-ui): `npx shadcn@latest add @magicui/safari` · https://skills.varg.ai/component/magicui.safari/
- Typewriter (hyperframes): `npx hyperframes add typewriter` · https://skills.varg.ai/component/hf.typewriter/
- Browser Device Stage (hyperframes): `npx hyperframes add browser-device-stage` · https://skills.varg.ai/component/hf.browser-device-stage/
- Typewriter (remocn): `npx shadcn@latest add @remocn/typewriter` · https://skills.varg.ai/component/remocn.typewriter/

Sources: [Bohdan Motion: breakdown of the Replit Design launch video](https://x.com/bohdanmotion/status/2083248851750728188) · [Magic UI: Safari](https://magicui.design/docs/components/safari)

## YouTube End Screen Layout

<a id="youtube-end-screen"></a>A 5–20 s outro with clean empty slots for YouTube's clickable video and subscribe elements.

Built on [Rounded Media Grid](https://github.com/heygen-com/hyperframes/tree/main/registry/blocks/mk-placeholder-grid) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Simple, calm backdrop; two 16:9 boxes and one circle reserved where YouTube places elements; a short spoken or written ask.

- **When:** Long-form YouTube tutorials, demos and launch explainers (videos ≥ 25 s).
- **Watch out:** Do not put busy motion or text where the elements will sit; up to four elements, and say out loud what to click.
- **Timing:** End screen window 5–20 s (YouTube limit); 8–12 s works for most; stagger element appearance.
- **Also called:** end screen, subscribe outro, next video card
- **Card:** https://skills.varg.ai/skills/youtube-end-screen/

### FFmpeg

```bash
# append a 12 s branded tail (same size/fps/codec)
printf "file main.mp4\nfile endscreen.mp4\n" > list.txt
ffmpeg -f concat -safe 0 -i list.txt -c copy out.mp4
```

### HyperFrames

```bash
npx hyperframes add mk-placeholder-grid
npx hyperframes add yt-lower-third
```
Layout 1920×1080: two video slots ≈ 615×345 and a 294 px circle; keep the last 20 s of the edit calm.

### Remotion

```tsx
<Sequence from={durationInFrames - 15*fps}>
  <EndScreenBackdrop/>  {/* leave rects empty for YouTube elements */}
</Sequence>
```

### CapCut

Add the end-screen background for the last 10–15 s, Text for "Watch next", leave the slots empty; add elements later in YouTube Studio → Editor → End screen.

### Components

- Rounded Media Grid (hyperframes): `npx hyperframes add mk-placeholder-grid` · https://skills.varg.ai/component/hf.mk-placeholder-grid/
- YouTube Lower Third (hyperframes): `npx hyperframes add yt-lower-third` · https://skills.varg.ai/component/hf.yt-lower-third/
- X Follow Card (hyperframes): `npx hyperframes add x-follow-card` · https://skills.varg.ai/component/hf.x-follow-card/

Sources: [YouTube Help: Add end screens to videos](https://support.google.com/youtube/answer/6388789) · [vidIQ: YouTube end screens](https://vidiq.com/blog/post/youtube-end-screens/)

## Scan-to-Try QR Card

<a id="scan-to-try-qr"></a>A high-contrast QR code with a one-line reason to scan, held long enough to grab a phone.

Built on [Camera Scan Gate](https://github.com/heygen-com/hyperframes/tree/main/registry/components/camera-scan-gate) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Black-on-white QR (≥300 px on 1080p) on a card with a light border beam; "Scan to try free" beside it; logo small above.

- **When:** Event screens, keynotes, TV/CTV spots and any video shown on a big screen.
- **Watch out:** Do not flash it for 2 seconds; hold it at least 7–10 s and never animate the code itself.
- **Timing:** Card in 0.4 s, code static, hold 7–10 s; border beam loop 3–5 s.
- **Also called:** QR end card, scan CTA, QR code outro
- **Card:** https://skills.varg.ai/skills/scan-to-try-qr/

### FFmpeg

```bash
ffmpeg -i film.mp4 -i qr.png -filter_complex "[1]scale=320:-1[q];[0][q]overlay=W-w-120:H-h-120:enable='gte(t,38)'" out.mp4
```

### HyperFrames

```bash
npx hyperframes add camera-scan-gate
```
Render the QR as a static `<img>` inside a white card; only the frame/beam animates.

### Remotion

```tsx
// npx shadcn@latest add @magicui/border-beam
<div style={{background:'#fff', padding:24, borderRadius:24}}><Img src={qr} style={{width:320}}/></div>
```

### CapCut

Overlay the QR PNG at the lower right inside the guides, no animation on the code; add a Text line "Scan to try" with Fade in.

### Components

- Camera Scan Gate (hyperframes): `npx hyperframes add camera-scan-gate` · https://skills.varg.ai/component/hf.camera-scan-gate/
- Border Beam (magic-ui): `npx shadcn@latest add @magicui/border-beam` · https://skills.varg.ai/component/magicui.border-beam/

Sources: [QRStuff: best practices for QR codes on TV commercials](https://www.qrstuff.com/feeds/blog/qr-codes-tv-commercials) · [MediaVillage: common QR code mistakes in TV ads](https://www.mediavillage.com/article/common-mistakes-tv-advertisers-make-when-implementing-qr-codes-for-television/amp/)

## Store Badges Close

<a id="store-badges-close"></a>A short headline settles above equal-size App Store and Google Play badges, often beside a phone.

Built on [Store Badge Lockup](https://github.com/heygen-com/hyperframes/tree/main/registry/components/store-badge-lockup) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Two official badges at identical height, centered under the line; a phone with the app's home screen to one side.

- **When:** Mobile app launches and app ads.
- **Watch out:** Do not stretch or recolor the official badges, and keep both at the same height.
- **Timing:** Headline 0.5 s, badges pop 0.3 s with 0.1 s stagger, hold 2–3 s.
- **Also called:** app store badges, download CTA, mobile app outro
- **Card:** https://skills.varg.ai/skills/store-badges-close/

### HyperFrames

```bash
npx hyperframes add store-badge-lockup
```
Pair with `vfx-iphone-device` or `device-frame-stage` for the phone on the side.

### Remotion

```tsx
{[appStore, playStore].map((src,i)=>{const s=spring({frame:frame-15-i*3,fps,config:{damping:12}}); return <Img src={src} style={{height:72, transform:`scale(${s})`}}/>})}
```

### CapCut

Overlay both badge PNGs at the same height; Animation In "Pop up" 0.3 s, second one 3 frames later.

### Components

- Store Badge Lockup (hyperframes): `npx hyperframes add store-badge-lockup` · https://skills.varg.ai/component/hf.store-badge-lockup/
- Social Proof Card (hyperframes): `npx hyperframes add social-proof-card` · https://skills.varg.ai/component/hf.social-proof-card/
- VPN YouTube Spot (hyperframes): `npx hyperframes add vpn-youtube-spot` · https://skills.varg.ai/component/hf.vpn-youtube-spot/

Sources: [Bohdan Motion: breakdown of the Grok Build Mode launch video](https://x.com/bohdanmotion/status/2082193183111614671)

## Pull Back to the Whole Canvas

<a id="pull-back-to-canvas"></a>The camera pulls out from the last detail to the whole product workspace, then lands on the logo.

Built on [Parallax Unzoom](https://github.com/heygen-com/hyperframes/tree/main/registry/components/parallax-unzoom) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

One long decelerating zoom-out: the last screen shrinks into a grid of everything shown, then the grid dims behind the logo.

- **When:** Close a demo that showed many features; it recaps without a montage.
- **Watch out:** Do not cut to a black card after the pull-back; let the workspace stay faintly behind the logo.
- **Timing:** Pull-back 1.2–2 s, expo.inOut; logo in during the last 0.5 s of the move.
- **Also called:** zoom out ending, unzoom reveal, workspace pull-back
- **Card:** https://skills.varg.ai/skills/pull-back-to-canvas/

### FFmpeg

```bash
-vf "zoompan=z='max(1,3.2-on*0.045)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1920x1080:fps=30"
```

### HyperFrames

```bash
npx hyperframes add parallax-unzoom
```
Or `pull-back-reveal` for a single stat → hero pull-back; set `data-start` so the move ends on the music resolve.

### Remotion

```tsx
// npx shadcn@latest add @remocn/infinite-bento-pan
const z = interpolate(frame,[0,48],[3.2,1],{extrapolateRight:'clamp',easing:Easing.inOut(Easing.exp)});
<AbsoluteFill style={{transform:`scale(${z})`, transformOrigin:'62% 40%'}}><Workspace/></AbsoluteFill>
```

### CapCut

On the final workspace clip, keyframe Scale 320% → 100% over 1.5 s with Graphs → "Ease in-out"; add the logo overlay at the end.

### Components

- Parallax Unzoom (hyperframes): `npx hyperframes add parallax-unzoom` · https://skills.varg.ai/component/hf.parallax-unzoom/
- Pull Back Reveal (hyperframes): `npx hyperframes add pull-back-reveal` · https://skills.varg.ai/component/hf.pull-back-reveal/
- Infinite Bento Pan (remocn): `npx shadcn@latest add @remocn/infinite-bento-pan` · https://skills.varg.ai/component/remocn.infinite-bento-pan/

Sources: [Bohdan Motion: breakdown of the Claude Design launch video](https://x.com/bohdanmotion/status/2080610655237751033) · [Lago: we killed our motion design job (Linear-style films, Remotion)](https://getlago.com/blog/we-killed-our-motion-design-job)

## Follow Card Sign-Off

<a id="follow-card-sign-off"></a>A profile card with avatar, handle and a Follow button that a cursor or tap presses.

Built on [Instagram Follow](https://github.com/heygen-com/hyperframes/tree/main/registry/blocks/instagram-follow) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Platform-faithful card (X, TikTok, Instagram) springs in; the Follow button flips to Following with a tick.

- **When:** Founder-led launches and build-in-public clips where the account is the CTA.
- **Watch out:** Do not use a card for a platform you are not posting on; match the card to where the video runs.
- **Timing:** Card 0.4 s spring, press at +0.8 s (0.1 s down / 0.2 s up), state flip 0.25 s, hold 1.5 s.
- **Also called:** follow CTA, social follow card, profile card outro
- **Card:** https://skills.varg.ai/skills/follow-card-sign-off/

### HyperFrames

```bash
npx hyperframes add instagram-follow   # or x-follow-card / tiktok-follow
```
Set name, handle and avatar through `data-variable-values`.

### Remotion

```tsx
// npx shadcn@latest add @remocn/x-follow-card
const followed = frame > pressAt;
```

### CapCut

Stickers → search "follow"/"subscribe" button stickers; or Text templates → "follow"; add a tap SFX.

### Components

- Instagram Follow (hyperframes): `npx hyperframes add instagram-follow` · https://skills.varg.ai/component/hf.instagram-follow/
- X Follow Card (hyperframes): `npx hyperframes add x-follow-card` · https://skills.varg.ai/component/hf.x-follow-card/
- TikTok Follow (hyperframes): `npx hyperframes add tiktok-follow` · https://skills.varg.ai/component/hf.tiktok-follow/
- X Follow Card (remocn): `npx shadcn@latest add @remocn/x-follow-card` · https://skills.varg.ai/component/remocn.x-follow-card/

Sources: [Y Combinator: Farza's launch video playbook (first 10 seconds, hooks)](https://x.com/ycombinator/status/2113654566776709147)

## Last Frame Equals First Frame

<a id="loop-to-first-frame"></a>The ending morphs back into the opening frame so autoplaying feeds loop without a visible seam.

Built on [Logo Sting](https://github.com/heygen-com/hyperframes/tree/main/registry/components/logo-sting) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

The final logo or shape contracts into exactly the pose the film opened on; one flash or chrome glint hides the joint.

- **When:** Short social cuts (6–20 s) that autoplay on loop in feeds.
- **Watch out:** Do not end on a hard black frame; the loop then reads as a restart, not a continuation.
- **Timing:** Match the first and last 3–5 frames exactly; place the joint on a downbeat.
- **Also called:** seamless loop ending, loop outro, boomerang logo
- **Card:** https://skills.varg.ai/skills/loop-to-first-frame/

### FFmpeg

```bash
# compare first and last frame
ffmpeg -i out.mp4 -vf "select=eq(n\,0)" -frames:v 1 first.png
ffmpeg -sseof -0.04 -i out.mp4 -frames:v 1 last.png
```

### HyperFrames

```bash
npx hyperframes add logo-sting
```
Author the open and close from the same keyframe values; check with `npx hyperframes snapshot` at t=0 and t=end.

### Remotion

```tsx
const t = frame / durationInFrames; // 0→1
const pose = interpolate(t,[0,0.1,0.9,1],[A,B,B,A]);
```

### CapCut

Duplicate the opening 0.5 s, place it at the end, and cross-fade 3–4 frames into it.

### Components

- Logo Sting (hyperframes): `npx hyperframes add logo-sting` · https://skills.varg.ai/component/hf.logo-sting/
- Metallic Paint (react-bits): `npx shadcn@latest add @react-bits/MetallicPaint-JS-CSS` · https://skills.varg.ai/component/reactbits.metallic-paint/
- Anamorphic Flare (remocn): `npx shadcn@latest add @remocn/anamorphic-flare` · https://skills.varg.ai/component/remocn.anamorphic-flare/

Sources: [zero on X: Apple-keynote launch film prompt (Screen Studio zoom, no crossfades)](https://x.com/twoclipping/status/2103835273813496100)
