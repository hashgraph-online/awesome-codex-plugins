# Quotes & reviews

Testimonials, review cards, star ratings, posts and replies as proof inside a video. 9 takes. Browse them with previews at https://skills.varg.ai/browse/skills/quotes/.

Proof works when it is real and short: one strong sentence, a name and role or handle, and a face or avatar. Reveal quotes at reading pace (3–4 words per second), keep cards platform-faithful only for real posts used with permission, and prefer honest ratings like 4.7 over a perfect 5.0, which buyers distrust.

## Tweet as Proof Card

<a id="tweet-proof-card"></a>A real post from a user animates in as a card: avatar, name, text, then counts tick up.

Built on [X Post Card](https://github.com/heygen-com/hyperframes/tree/main/registry/blocks/x-post) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

A clean X-style card floats over a blurred UI or gradient; text reveals at reading pace, likes and reposts count up last.

- **When:** Right after a feature demo, as proof that real people already use it.
- **Watch out:** Do not invent posts or edit the wording; use real posts with permission and keep the handle visible.
- **Timing:** Card in 0.4 s (back.out 1.2), text at ~3 words/s, counts 0.8 s ease-out, hold 1.5 s after.
- **Also called:** post card, X post overlay, social proof tweet
- **Card:** https://skills.varg.ai/skills/tweet-proof-card/

### HyperFrames

```bash
npx hyperframes add x-post
```
```html
<div data-composition-id="x-post" data-composition-src="compositions/x-post.html"
  data-variable-values='{"name":"Ada","handle":"@ada","text":"This saved my week","likes":1240}'
  data-start="12" data-duration="5" data-track-index="2"></div>
```

### Remotion

```tsx
// fetch once with react-tweet's getTweet(id), render the card yourself, animate:
const s = spring({frame, fps, config:{damping:14}});
<div style={{transform:`scale(${interpolate(s,[0,1],[0.9,1])})`, opacity:s}}><EmbeddedTweet tweet={data}/></div>
```

### CapCut

Screenshot the post, add as Overlay, Mask → Rectangle with round corners, Animation In "Zoom in" 0.4 s; add a soft shadow in Video → Basic.

### Components

- X Post Card (hyperframes): `npx hyperframes add x-post` · https://skills.varg.ai/component/hf.x-post/
- X Follow Card (hyperframes): `npx hyperframes add x-follow-card` · https://skills.varg.ai/component/hf.x-follow-card/
- X Follow Card (remocn): `npx shadcn@latest add @remocn/x-follow-card` · https://skills.varg.ai/component/remocn.x-follow-card/

Sources: [Vercel: introducing react-tweet](https://vercel.com/blog/introducing-react-tweet) · [Senja: what is a Wall of Love](https://support.senja.io/what-is-wall-of-love-3whg8) · [CapCut: turn testimonials into quote graphics for short-form](https://www.capcut.com/create/testimonial-quote-graphics-short-form-content)

## Quote at Reading Pace

<a id="quote-at-reading-pace"></a>One strong customer sentence reveals word by word, then the name, role and avatar settle under it.

Built on [Testimonial Card](https://github.com/heygen-com/hyperframes/tree/main/registry/components/testimonial-card) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Large serif or grotesque quote on a quiet card; quote marks in the accent color; author line smaller and lighter.

- **When:** Between demo beats, to let a customer say the claim instead of the brand.
- **Watch out:** Do not use a whole paragraph; pick the single strongest 1–2 sentence pull quote.
- **Timing:** Words at 3–4 words/s, author in 0.3 s after, hold = word count ÷ 3 + 1 s.
- **Also called:** testimonial card, customer quote, pull quote card
- **Card:** https://skills.varg.ai/skills/quote-at-reading-pace/

### HyperFrames

```bash
npx hyperframes add testimonial-card
```
Pass the quote, author and handle through `data-variable-values`; size `data-duration` from the word count (words/3 + 2 s).

### Remotion

```tsx
const words = quote.split(' ');
words.map((w,i)=>{const o=interpolate(frame,[i*8,i*8+8],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'}); return <span style={{opacity:o, filter:`blur(${(1-o)*6}px)`}}>{w} </span>})
```

### CapCut

Text → Text templates → "quote"; Animation In: "Typewriter" or "Fade in by word"; author line as a second text layer 0.3 s later.

### Components

- Testimonial Card (hyperframes): `npx hyperframes add testimonial-card` · https://skills.varg.ai/component/hf.testimonial-card/
- Testimonial Proof Card (hyperframes): `npx hyperframes add testimonial-proof-card` · https://skills.varg.ai/component/hf.testimonial-proof-card/
- Text Generate Effect (aceternity): `npx shadcn@latest add @aceternity/text-generate-effect` · https://skills.varg.ai/component/aceternity.text-generate-effect/

Sources: [Morphic: how to make a customer testimonial video](https://morphic.com/resources/how-to/make-a-customer-testimonial-video) · [CapCut: turn testimonials into quote graphics for short-form](https://www.capcut.com/create/testimonial-quote-graphics-short-form-content) · [Text animation for readability: kinetic type without overcomplication](https://cursa.app/en/page/text-animation-for-readability-kinetic-type-without-overcomplication)

## Star Rating Sweep

<a id="star-rating-sweep"></a>Five stars fill left to right to the real score while the number counts up beside them.

Built on [Star Rating Fill](https://github.com/heygen-com/hyperframes/tree/main/registry/components/star-rating-fill) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

A row of outline stars; the fill layer sweeps to 4.8 and keeps the partial last star; "4.8 · 2,300 reviews" beside it.

- **When:** App and marketplace products; end of a testimonial run; pricing scenes.
- **Watch out:** Do not round up to a perfect 5.0; buyers distrust it and purchase likelihood peaks around 4.2–4.5.
- **Timing:** Sweep 0.8–1.0 s, power2.out; number counts in the same window; hold 1.5 s.
- **Also called:** rating stars, review score, app store rating
- **Card:** https://skills.varg.ai/skills/star-rating-sweep/

### HyperFrames

```bash
npx hyperframes add star-rating-fill
```
Set `data-variable-values='{"rating":4.8,"count":"2,300 reviews"}'`; the fractional star is preserved.

### Remotion

```tsx
const r = interpolate(frame,[0,24],[0,4.8],{extrapolateRight:'clamp',easing:Easing.out(Easing.cubic)});
<div style={{width:`${r/5*100}%`, overflow:'hidden'}}>★★★★★</div>
```

### CapCut

Stickers → search "5 stars"; reveal with Mask → Linear keyframed left to right; add a Text counter manually per frame or use a counter text template.

### Components

- Star Rating Fill (hyperframes): `npx hyperframes add star-rating-fill` · https://skills.varg.ai/component/hf.star-rating-fill/
- Social Proof Card (hyperframes): `npx hyperframes add social-proof-card` · https://skills.varg.ai/component/hf.social-proof-card/
- Counter (animata): `npx shadcn@latest add https://animata.design/r/text/counter.json` · https://skills.varg.ai/component/animata.counter/

Sources: [PowerReviews / Spiegel Research Center: from reviews to revenue](https://www.powerreviews.com/from-reviews-to-revenue/) · [Retail TouchPoints: purchase likelihood peaks at 4.2–4.5 stars](https://www.retailtouchpoints.com/topics/customer-experience/purchase-likelihood-highest-for-products-rated-between-4-2-and-4-5-out-of-5-stars)

## Wall of Love Marquee

<a id="wall-of-love-marquee"></a>Two or three rows of review cards drift in opposite directions, fading at the edges.

Built on [Marquee](https://github.com/magicuidesign/magicui/blob/main/apps/www/registry/magicui/marquee.tsx) by magic-ui, MIT. The write-up and recipes are varg's.

Small cards with avatar, name and one line each, in rows moving at slightly different speeds under a short headline.

- **When:** Show breadth of love fast: many voices, none read in full. Good behind a stat like "10,000 teams".
- **Watch out:** Do not expect anyone to read the cards; put the one quote you need read in its own scene.
- **Timing:** Each row loops in 20–40 s; rows at 1×, 0.8×, 1.2× speed. Edge fade 10–15% of width.
- **Also called:** testimonial marquee, review wall, love wall
- **Card:** https://skills.varg.ai/skills/wall-of-love-marquee/

### HyperFrames

```bash
npx hyperframes add perspective-marquee
```
Drive x from the timeline (`tl.to(row,{xPercent:-50,duration:30,ease:"none"},0)`) so it stays seek-safe; duplicate the row content for a seamless loop.

### Remotion

```tsx
// npx shadcn@latest add @magicui/marquee  (replace CSS animation with frame-driven x)
const x = -((frame * speed) % rowWidth);
<div style={{transform:`translateX(${x}px)`, maskImage:'linear-gradient(90deg,transparent,#000 12%,#000 88%,transparent)'}}>
```

### CapCut

Export a long strip image of cards, add as Overlay, keyframe Position X from right to left over the clip; duplicate and reverse for the second row.

### Components

- Marquee (magic-ui): `npx shadcn@latest add @magicui/marquee` · https://skills.varg.ai/component/magicui.marquee/
- Perspective Marquee (hyperframes): `npx hyperframes add perspective-marquee` · https://skills.varg.ai/component/hf.perspective-marquee/
- Perspective Marquee (remocn): `npx shadcn@latest add @remocn/perspective-marquee` · https://skills.varg.ai/component/remocn.perspective-marquee/

Sources: [Magic UI: Marquee](https://magicui.design/docs/components/marquee) · [Senja: what is a Wall of Love](https://support.senja.io/what-is-wall-of-love-3whg8)

## Community Post as Proof

<a id="community-post-proof"></a>A real community post or comment card pops over the footage with its upvotes counting up.

Built on [Reddit Post Card](https://github.com/heygen-com/hyperframes/tree/main/registry/blocks/reddit-post) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Reddit-style or YouTube-comment-style card, platform-faithful; the text types on, then the vote count rises.

- **When:** Developer and consumer products where community chatter is more believable than a logo.
- **Watch out:** Do not fake platform UI for posts that never existed; quote real ones and blur usernames if needed.
- **Timing:** Card pop 0.3 s, typing 30–40 ms/char, count-up 0.8 s.
- **Also called:** reddit post, forum thread proof, comment card
- **Card:** https://skills.varg.ai/skills/community-post-proof/

### HyperFrames

```bash
npx hyperframes add reddit-post
```
Or `npx hyperframes add yt-comment-card` for comment-style proof over footage.

### Remotion

```tsx
const chars = Math.floor(interpolate(frame,[6,6+text.length*1.1],[0,text.length],{extrapolateLeft:'clamp',extrapolateRight:'clamp'}));
<p>{text.slice(0,chars)}</p>
```

### CapCut

Add the screenshot as Overlay, Animation In "Pop up"; place it in the upper third so captions stay clear.

### Components

- Reddit Post Card (hyperframes): `npx hyperframes add reddit-post` · https://skills.varg.ai/component/hf.reddit-post/
- Comment Cards (hyperframes): `npx hyperframes add yt-comment-card` · https://skills.varg.ai/component/hf.yt-comment-card/

Sources: [CapCut: turn testimonials into quote graphics for short-form](https://www.capcut.com/create/testimonial-quote-graphics-short-form-content) · [Morphic: how to make a customer testimonial video](https://morphic.com/resources/how-to/make-a-customer-testimonial-video)

## Reviews Arrive as Notifications

<a id="reviews-as-notifications"></a>Short reviews land as system notifications that stack and push each other down.

Built on [Animated List](https://github.com/magicuidesign/magicui/blob/main/apps/www/registry/magicui/animated-list.tsx) by magic-ui, MIT. The write-up and recipes are varg's.

iOS/macOS-style banners with app icon, name and one line each; new ones spring in at the top, older ones slide down and dim.

- **When:** Show momentum: sign-ups, five-star reviews, payments or "new message" pings piling up.
- **Watch out:** Do not let the stack grow past 4–5 cards; older ones should leave the frame.
- **Timing:** One every 0.4–0.8 s, accelerating slightly; each card spring (damping ~14).
- **Also called:** notification stack, toast proof, incoming reviews
- **Card:** https://skills.varg.ai/skills/reviews-as-notifications/

### HyperFrames

```bash
npx hyperframes add notification-cascade
```
Or `notification-stack` for 1–5 token-driven cards on cue times.

### Remotion

```tsx
// npx shadcn@latest add @magicui/animated-list (frame-driven)
const visible = items.filter((_,i)=> frame > i*15).slice(-4);
```

### CapCut

Text → Text templates → search "notification"; stagger 3–4 copies 0.5 s apart with Animation In "Slide down".

### Components

- Animated List (magic-ui): `npx shadcn@latest add @magicui/animated-list` · https://skills.varg.ai/component/magicui.animated-list/
- Notification Cascade (hyperframes): `npx hyperframes add notification-cascade` · https://skills.varg.ai/component/hf.notification-cascade/
- Notification Stack (hyperframes): `npx hyperframes add notification-stack` · https://skills.varg.ai/component/hf.notification-stack/

Sources: [Bohdan Motion: X launch video, 40% of runtime on real UI](https://x.com/bohdanmotion/status/2079611760894431568) · [CapCut: turn testimonials into quote graphics for short-form](https://www.capcut.com/create/testimonial-quote-graphics-short-form-content)

## Pull Quote Beside the Speaker

<a id="pull-quote-beside-speaker"></a>While a customer talks on camera, their key sentence appears as large type in the empty side of the frame.

Built on [Lower Third — Dark Card](https://github.com/heygen-com/hyperframes/tree/main/registry/blocks/lt-dark-card) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Speaker framed left or right third; the strongest line fades up per word on the open side, high contrast, no card needed.

- **When:** Video testimonials and interviews, so the claim survives sound-off viewing.
- **Watch out:** Do not cover the speaker's face or hands, and do not repeat every word they say — only the pull quote.
- **Timing:** Start with the spoken words; per-word fade 0.2–0.3 s; hold to the end of the sentence + 0.5 s.
- **Also called:** testimonial overlay, quote over interview, speaker quote
- **Card:** https://skills.varg.ai/skills/pull-quote-beside-speaker/

### FFmpeg

```bash
-vf "drawtext=text='Cut our onboarding in half':x=w*0.55:y=h*0.4:fontsize=72:fontcolor=white:alpha='min(1,max(0,(t-8.2)/0.3))':enable='between(t,8.2,12)'"
```

### HyperFrames

```bash
npx hyperframes add soft-blur-in
```
Time each word's `tl.from` to its transcript timestamp; keep the text inside the open half of the frame.

### Remotion

```tsx
// npx shadcn@latest add @remocn/per-word-crossfade
const o = interpolate(frame,[w.start*fps, w.start*fps+6],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
```

### CapCut

Captions → Auto captions, delete all but the pull-quote line, restyle it large on the open side; Animation In "Fade in by word".

### Components

- Lower Third — Dark Card (hyperframes): `npx hyperframes add lt-dark-card` · https://skills.varg.ai/component/hf.lt-dark-card/
- Per-Word Crossfade (remocn): `npx shadcn@latest add @remocn/per-word-crossfade` · https://skills.varg.ai/component/remocn.per-word-crossfade/
- Soft Blur In (animata): `npx shadcn@latest add https://animata.design/r/text/soft-blur-in.json` · https://skills.varg.ai/component/animata.soft-blur-in/

Sources: [Morphic: how to make a customer testimonial video](https://morphic.com/resources/how-to/make-a-customer-testimonial-video) · [CapCut: turn testimonials into quote graphics for short-form](https://www.capcut.com/create/testimonial-quote-graphics-short-form-content)

## Split-Flap Headline Quote

<a id="split-flap-quote"></a>A short quote or result spells itself out on a split-flap board, tiles flipping until they land.

Built on [Text Flipping Board](https://ui.aceternity.com/components/text-flipping-board) by aceternity, Aceternity License (free components). The write-up and recipes are varg's.

Dark tiles with a center seam, each walking through letters and settling left to right with mechanical clicks.

- **When:** A memorable short line: a result ("SHIPPED IN 2 DAYS") or a three-word review.
- **Watch out:** Do not use more than ~20 characters; long boards flip forever and nobody reads them.
- **Timing:** 1.2–2 s total, tiles settle 40–60 ms apart; add a soft click SFX per settle.
- **Also called:** departure board, solari board, flip board quote
- **Card:** https://skills.varg.ai/skills/split-flap-quote/

### HyperFrames

```bash
npx hyperframes add split-flap-board
```
Each cell's drum position is derived from time, so seeking any frame shows the right letter.

### Remotion

```tsx
const settleAt = i*2 + 20; // frames
const ch = frame>=settleAt ? target[i] : ABC[(frame + i*3) % ABC.length];
```

### CapCut

Text → Text templates → search "flip"/"board"; or use Animation In "Flip" per letter layer.

### Components

- Text Flipping Board (aceternity): `npx shadcn@latest add @aceternity/text-flipping-board` · https://skills.varg.ai/component/aceternity.text-flipping-board/
- Split-Flap Board (hyperframes): `npx hyperframes add split-flap-board` · https://skills.varg.ai/component/hf.split-flap-board/

Sources: [Jamie on X: SFX breakdown of a launch video](https://x.com/jamiesmotion/status/2110099791958982703) · [SVGator: kinetic typography, a guide to text in motion](https://www.svgator.com/blog/kinetic-typography-a-guide-to-text-in-motion/)

## GitHub Stars as Proof

<a id="star-count-proof"></a>Stargazer avatars fly past while a star counter odometers up to the repo's real total.

Built on [GitHub Stars](https://remocn.dev/r/github-stars.json) by Kapish Dima (remocn), MIT. The write-up and recipes are varg's.

A ★ icon with a rolling count; avatars blur-stagger in a cloud behind it, then the count locks with a small pop.

- **When:** Open-source and developer tools; the moment you say "loved by developers".
- **Watch out:** Do not show a stale number; read it from the API on render day and round honestly (12.4k, not 12k+).
- **Timing:** Count 1.2–1.8 s, ease-out; avatars stagger 20–40 ms; lock pop 0.2 s.
- **Also called:** stargazers, star count, open source proof
- **Card:** https://skills.varg.ai/skills/star-count-proof/

### HyperFrames

```bash
npx hyperframes add count-up
npx hyperframes add avatar-cloud
```
Set the target via `data-variable-values='{"to":12400}'`; fire the avatar cloud 0.2 s before the count.

### Remotion

```tsx
// npx shadcn@latest add @remocn/github-stars
const n = Math.round(interpolate(frame,[0,45],[0,stars],{extrapolateRight:'clamp',easing:Easing.out(Easing.quad)}));
```

### CapCut

Add a ★ sticker and a Text layer; keyframe the number with a counter text template (Text → templates → "number").

### Components

- GitHub Stars (remocn): `npx shadcn@latest add @remocn/github-stars` · https://skills.varg.ai/component/remocn.github-stars/
- Avatar Cloud (hyperframes): `npx hyperframes add avatar-cloud` · https://skills.varg.ai/component/hf.avatar-cloud/
- Count Up (react-bits): `npx shadcn@latest add @react-bits/CountUp-JS-CSS` · https://skills.varg.ai/component/reactbits.count-up/

Sources: [Animation principles for data visualization](https://skills.cat/skills/dylantarre/animation-principles/data-visualization)
