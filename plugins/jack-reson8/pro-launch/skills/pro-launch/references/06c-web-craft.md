# Web craft: a website is a film that waits for a finger

Master copy. `pro-launch/references/06c-web-craft.md` is a synced copy of this file; edit here, then run the sync line at the bottom.

Read this whenever the deliverable is a web page: official site, landing page, hero, campaign microsite, "先出几个预览". It turns the film method of this skill (real frames → technique sheet → style frame → build → verify) into the order a web page must follow. `scripts/web_gate.py` checks the order with files and git; nothing in this file is optional advice.

**Why it exists (2026-10-24, tutti.pics).** Round 1: three heroes were coded from memory (paper ground, small photo, headline, two buttons, code-drawn icons), and references were found *afterwards* only to grade them. Jack: "差距也太大了吧，完全不是一个事情……web 感太重，React Bits、Rive、p5.js、代码绘制元素、插画、UI/UX 交互全忘了". Round 2 followed the steps below in this order and was accepted the same night: "非常好了，非常完美了……这回真的很好". The only difference was the order of work.

## W0 · The order (each step ends in a file; the next step reads it)

| # | Step | Artifact (default dir `docs/site/`) | Gate |
|---|---|---|---|
| 1 | Look up the global style library first (`python3 ~/.claude/style-library/lookup.py T` and keywords for the product; if the library is absent, say so and continue). Then ask which reference the user likes; if none, collect 8–14 stylized sites (a Sonnet subagent, brief in W1) and let the user point at one | `refs-web-<date>.md` with a line "用了库条目：…" | — |
| 2 | Decode the liked reference as **layers**, at phone and desktop size | `refs/<name>.json` + `-m.png` `-d.png` from `scripts/web_layers.js` | `web_gate.py` needs ≥1 dump |
| 3 | Technique sheet: ≥3 entries (liked ref, one mechanism ref, one product-native source) | `technique-sheets.md`, **committed before any site code** | `web_gate.py` checks fields + git order |
| 4 | Register + fusion rule + 2–3 style frames rendered in a scratch copy (`cp -R <this skill>/assets/web-hero <scratchpad>/frames`; setup.sh does not copy it; never inside `site/`), each beside the liked ref with ≥3 element-level "where it falls short" lines and a `Core gap:` line; show the user, then write `Picked:` **with the user's own words** | `style-frames.md` (`Register:`, frames, then `Picked:`), `style-frames/*-vs-ref.jpg` | core-gap gate (W4); no `Picked:` before the user answers |
| 5 | Only now copy `assets/web-hero/` into `site/` and build with the recipe (W3); verify like a phone (W5) | site code, `*.mp4`, screenshot sheet | `web_gate.py` before the first site commit, `--ship` before showing |

Run `python3 <this skill>/scripts/web_gate.py <project>` before the first site commit, and `--ship` before sending the user anything. If the user rejects a round, set `--restart <rev>` (the rejected commit) and go back to step 1 or 2, not to the code.

## W1 · Collect references (subagent brief, keep it this shape)
"Find 10–14 sites in the vein of <liked ref>; ≥4 not app sites (festival, fashion campaign, agency, athlete). For each: URL, what owns the first screen and its share, how type is treated, palette, motion/tech seen in source, signature move, what to borrow, and an evidence tag 【实看页面】/【部分实看】/【仅文本】. Drop sites that don't load. ≤15 min, single waits ≤60 s." The 2026-10-24 run (`Tutti/docs/site/refs-web-2026-10-24.md`) found that almost no app site is stylized except Lapse; the useful ones were a festival (Kelvin), a campaign (Later "Made You Look") and an agency (blue2purple). Those are now in the style library, family T.

## W1a · Read widely, not one reference (2026-10-25)
Matching one site makes a page that is "还不错但偏传统". Before style frames, survey **≥20 award-level sites across ≥4 sources** (Awwwards SOTY/SOTM/Developer award, FWA, CSS Design Awards, Webby, Cannes Lions Digital Craft, plus interactive art/game pieces), recorded as a **mechanism table**: what the visitor *does* → what happens → why it is surprising yet easy → which product verb it could carry. The liked reference sets the look; the survey supplies mechanisms. Each style frame must cite ≥2 mechanisms from different sources, and at least one frame must be built on a mechanism no app site uses. Two parallel Sonnet subagents (web awards / campaigns + interactive art) with evidence tags 【实看】/【文本】.

## W1b · Scroll stories
A first-screen dump can't show what happens below. `node <this skill>/scripts/web_scroll.js <url> <name> docs/site/refs --steps 13 [--video]` gives a 14-cell scroll contact sheet (and a smooth scroll video); a Haiku reader turns the sheets into technique lines. Use the same script on your own prototypes for the style frames (it is how the v3 A/B/C frames were recorded). Found 2026-10-25: Apple's and Shopify's pages turn into templates below the fold; Kelvin stays stylized because each section is one slab of colour whose subject is one treatment of the same photo.
Pitfalls: a full-screen fixed hero needs `html, body { height:auto; overflow-x: clip }` once a story follows (`overflow-x: hidden` silently breaks `position: sticky`); language auto-redirect sends the headless browser to `/en/`, so inject prototypes into every language page.

## W2 · Decode as layers, not as a look
`node <this skill>/scripts/web_layers.js <url> <name> docs/site/refs` dumps every first-screen background image, canvas, video, font, script and library. Lapse turned out to be **stacked PNGs on Webflow**: saturated ground · hand-lettered warped slogan as one image · real cutout hand + phone with charms · a flash PNG · hard-light grain (grained.js). No WebGL. Its beauty is art direction; code only moves grain. So: copy the **layer sandwich**, then beat the reference with what it doesn't have (a live layer the finger can move, the product's own action as the transition, the visitor's own photo).

Technique-sheet entry (06b fields plus two web fields; `web_gate.py` looks for these words):
```
### <id> · <work> (<owner, year>) · dump: refs/<name>.json
- hero: what owns the screen and its share
- type scale / whitespace / palette rule / depth & material / motion
- layer sandwich: ground → type → subject → light → texture, and what each is made of
- what code adds: which layer moves, and what it reacts to (finger, tilt, scroll, time, the visitor's photo)
- signature move:
- borrow: … · refuse: …
```

## W3 · Recipe that was accepted: "type wall + real subject + flash" (code: `assets/web-hero/`)
Use as a starting point, not a template to paste: swap the subjects, the looks table and the words for the new product.
- **Layers**: full-bleed flat ground (per state) → WebGL type wall → DOM cutout subject (`<img>` WebP with alpha, bottom-anchored, ≤72svh so the wall stays the hero) → flash overlay → grain in the shader. No paper margins, cards, sections or captions in the first screen.
- **Type wall**: 2D canvas draws rows of the slogan words (size = measured fit `min(TW·.98/width100·100, TW/2.15, TH/3.4)`, row gap 1.02, letterSpacing 1.2% of width), glow pass twice (`shadowBlur` .45 and .18 of size, light glow colour), ink pass with same-colour stroke .035 of size → uploaded as texture; screen uses the inner 86% so warps never show edges.
- **Shader**: fisheye `p *= 1 − .34·warp·|p|²`; two-octave value-noise flow (freq 1.7, amp .2·warp) + sine waves; pointer lens `p = m + d·(1 − .55·f)` and swirl `1.4·f` with `f = exp(−9|d|²)·strength`; tap "kick" multiplies warp ×(1+2.2·kick), decays ×.93/frame; grain = per-frame hash noise ±.16 weighted to mid-tones. warp per state .55–1.25.
- **States = the product's real outputs**: each flash swaps ground/ink/glow/words/subject treatment; every state maps to a real template id and carries a real share code. Subjects rotate (full body, half body, two friends).
- **Transition = the product's own action** (camera flash): radial white flash 550 ms, subject pops 1.035, wall kicks. Auto-advance every ~3.4 s until the first touch.
- **Try it with your own photo**: MediaPipe Selfie Segmenter (244 KB model self-hosted, Apache-2.0; ~9.6 MB wasm from a pinned CDN, preload on button press), smoothstep the confidence mask, everything local, honest failure text. Never RMBG-1.4/2.0 (non-commercial).
- **Save = share card**: composite canvas (wall + subject + outline + code label + domain) → Web Share with files, download fallback.
- **Marketing pages from the same engine** (one HTML, path decides): code page `/c/XXXXXX` (one wrong character → suggestions, never 404), code-only poster `/p/XXXXXX` (the wall *is* the code, no brand name: media hijack), fake-broken 404 (grey wall, grey subject, tap to "fix" = flash), daily opening look, waitlist sheet with referral rank (Pages Functions + D1, +5 places per invite).
- **i18n**: one template + `strings.json` → per-language pages with hreflang; per-language display font subset to woff2 (zh 1.38 MB → 21 KB); OG images per language and per template made by screenshotting `?og=N` at 1200×630.
- **Engineering**: DPR ≤1.5 for the shader; stop rAF on `visibilitychange`; `webglcontextlost` → reload; `prefers-reduced-motion` → static frame, no auto-advance; WebGL missing → `<h1>` fallback; first-screen JS ≈ 10 KB, zero dependencies.

## W4 · Core-gap gate (before showing anything)
Every `-vs-ref` entry gets a `Core gap:` line. If any "where it falls short" line is about **structure or stylization register** ("ref is a full-bleed key visual, ours is a page layout"; "ref's type is image material, ours is captions"), the frame is not shown; go back to W2. Element-level gaps (letterform craft, props on the subject, glow blending) may be shown, with the lines burned into the image.

## W5 · Verify like a phone (headless Chrome, `page.mouse` drives pointer events)
- Screenshot every state on a timer at 390×844 @2x; one small contact sheet is the only image the main session reads.
- Record a 10–15 s clip: drag a loop on the wall, three taps, one auto-advance; a second clip for the try-it flow (preload the runtime first so the clip shows the result, not the download).
- Tour sheet of every page type (home in two languages, code page with a typo, poster, rank, 404, template page) before telling the user it is done.
- Frame timing via rAF deltas; note machine load (`uptime`) next to the number and say it is not a phone measurement.

## W6 · Pitfalls already paid for
- Square CJK strokes (出片) merge into a lattice when rows touch: light halo + row gap ≥1.0 + letter spacing.
- A subject taller than ~72% of the screen hides the wall; the wall is the hero.
- Cutouts that touch the photo edge show straight cut lines on wide screens: side mask-gradient 5%.
- Latin words are narrower than CJK: fit rows by `measureText`, not character count; cap by height in landscape.
- Cloudflare Pages: once `404.html` exists, a `_redirects` rewrite to `/index.html` stops working; rewrite to `/` (or `/ja/`).
- Cleaning code with a regex deleted live data (poster words). Re-run the tour sheet after any mechanical edit.
- Mapping a look to a product template: read the product source for the real id (white outline was `doodle-white`, not `outline-single`).
- AI-generated "realistic" people were called 太垃圾; the product's own demo photos (marked for replacement) were accepted.
- `wrangler` OAuth tokens expire: `whoami` can still print the account while API calls fail with code 10000; run `wrangler login` and let the user click Allow.

Sync to pro-launch after editing: `cp ~/.claude/skills/pro-motion/references/web-craft.md ~/.claude/skills/pro-launch/references/06c-web-craft.md`

## W7 · Pre-launch pages are growth machines (2026-10-25)
Before choosing the below-the-fold structure, map it to AARRR and pick the one where each interaction *produces* the next growth step (Tutti v3 X: tap/hold/swipe = activation, each yields a poster with a code = share asset, the last gesture "give it to a friend" = referral into the waitlist). Mechanisms with evidence (research: Tutti `docs/site/refs-prelaunch-growth-2026-10-25.md`): referral counts only after the invitee completes the core action (anti-fraud; Robinhood/Superhuman pattern), visible live position + tiered rewards (3/10 invites), spoiler-free result grid next to the share code (Wordle), daily "today's look" for return visits, App Store pre-order + LINE official-account reservation per market, staged code release with old waitlist first. Every interaction needs a tap fallback (drag failed in testing; "tap the friend card" also works).
