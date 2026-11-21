# Caption craft shared by every look

Read this before any single caption look. It holds the rules all 17 looks share: how many words to show, when, where, how big, how fast, and when a look is the wrong choice. Source numbers match `../sources.md`.

## 1. Pick the chunking mode first, then the look

| Mode | Words on screen | Use for | Avoid for |
|---|---|---|---|
| Phrase | 5-12 words, 1-2 lines (3 in 9:16) | podcasts, interviews, courses, docs, anything > 60 s, accessibility deliverables | nothing; it is the safe default [1][4][28] |
| Group | 2-5 words per page | short-form talking heads, clips, ads, explainers 15-90 s | dense numbers, legal text |
| Single word | 1 word | hooks (first 1-3 s), punchlines, beat-cut promos, clips <= 20 s | long talks, names, prices, steps, lists [14][30][43] |

- Build pages from word timestamps: combine tokens over ~1.2 s and break on silences of ~400 ms (Remotion `createTikTokStyleCaptions`) [16].
- Line breaks follow grammar even inside 3-word pages: never split article+noun, preposition+phrase, pronoun+verb, auxiliary+verb, first+last name [1][4][6].

## 2. Where one word at a time hurts

- In word-for-word display viewers spent ~90% of the time on the text and ~10% on the picture, and understood less [14].
- Caption-dependent viewers call single-word captions too fast and say highlights hijack their eyes [30][31][32][43].
- At 180 wpm a word lasts ~10 frames (0.33 s); faster speakers give 6-8 frames, under the time anyone can read and look at a face [4].
- Rule: single-word mode only for hooks, punchlines and <= 20 s beat-driven clips; switch to Group or Phrase after the hook. Merge words shorter than 8 frames into the next card. Never show numbers, names, prices or steps one word at a time.

## 3. Timing (30 fps)

- Caption block in-time: first audio frame or within 1-2 frames [3]. Out-time ~0.5 s after the audio when nothing follows; 2-frame minimum gap; close gaps under 0.5 s [3].
- Active word: switch 1-2 frames (33-67 ms) before the onset. Picture-early is not noticed up to ~125 ms; picture-late is noticed from ~45 ms [15]. Check every caption has voice under it within ~120 ms [41].
- Karaoke: the line leads (10-20 frames early, never more than 1.5 s [4]); the fill follows the voice (starts 1 frame early, sweeps over the word's duration, \kf) [20].
- Per-word animation budget: <= 6 frames. Entrances 4-8 frames, exits ~30% shorter. Material tokens: short4 200 ms, medium2 300 ms; emphasized cubic-bezier(0.2,0,0,1), emphasized-decelerate (0.05,0.7,0.1,1), emphasized-accelerate (0.3,0,0.8,0.15) [18]. GSAP back.out default overshoot 1.70158, elastic.out default (1, 0.3) [19]. Remotion spring defaults mass 1 / damping 10 / stiffness 100, bouncy; raise damping to calm [17].
- Reading speed: 160-180 wpm (0.33-0.375 s/word), adult ceiling 20 cps, children 17 cps; captions 0.83-7 s each [1][2][4].

## 4. Size and position

| | 16:9 (1920x1080) | 9:16 (1080x1920) |
|---|---|---|
| Accessible baseline | line height 7-8% H, font ~6.25% H (~67 px) [4] | line height 3.9-4.5% H, font ~3.5% H (~67 px) [4] |
| Short-form group looks | 56-72 px | 80-96 px (4.2-5% H) |
| Single-word looks | 96-120 px | 110-150 px (5.7-7.8% H) |
| Max line | 68% W, 42 chars [1][4] | 696 px centred (64% W), ~13-22 chars |
| Lines | 2 | 3 max [4] |
| Position | bottom centre inside central 90% x 75% [4] | block centre ~58-62% H, bottom edge <= 1248 px [10][11] |

- 9:16 safe box from the platforms' ad specs (worst case): top 288, bottom 672, left 120, right 192 px [10][11][13]; zones grow with ad caption length [12]. Organic posts: nothing important in the bottom 20% or right 15% [39]. Keep >= 60 px from edges and test on a phone at arm's length [44].
- Move captions off mouths, name supers and on-screen text; in 9:16 sit a little higher than in 16:9 because faces live in the top half [2][4][6].
- The short-form sizes above are house values derived from the BBC baseline (bigger because fewer words share the line); verify on a phone.

## 5. Colour and contrast

- >= 4.5:1 between text and what is directly behind it [8]. Pre-computed pairs: white/black 21:1; yellow #FFE600/black 16.6:1; cyan #00FFFF/black 16.8:1; light blue #4DA3FF/black 8.0:1; #2563EB/black only 4.1:1; white/#1F5BFF 5.25:1; white/#6D28D9 7.1:1; #0A0A0A/lime #C6FF3D 16.8:1; #141414/orange #FF7A1A 7.1:1 but white/orange 2.6:1 (fails).
- Translucent boxes over a worst-case white frame: black at 50% gives 4.0:1 (fails), 60% gives 5.7:1, 75% gives 10.4:1. Glass needs a 55-65% dark tint plus text shadow over bright shots [8][25].
- BBC caption palette: white, yellow, cyan, green on black [4]. One colour reads best for caption-dependent viewers [28].
- Flicker and shimmer: never more than 3 flashes per second [9].

## 6. Type

- Sans serif, medium to black weight, mixed case; caps only for single words or stress [4][6][36].
- Short-form favourites that are OFL: Montserrat (800-900), Inter, Poppins, Plus Jakarta Sans, Archivo Black, Anton, Bebas Neue; editorial: Instrument Serif, Playfair Display, Fraunces; legibility-first: Atkinson Hyperlegible [37][38][46]. OFL allows commercial video use without attribution [27].
- Outlines: `-webkit-text-stroke` with `paint-order: stroke fill`, ~0.1-0.14 em [24]. Animate scale with transforms, never font-size [20].

## 7. Look-to-audience map

| Look (slug) | Best for | Words |
|---|---|---|
| translucent-box-subtitles | long podcasts, interviews, docs, courses, accessible versions | phrase |
| line-hug-box-captions | UGC ads, talking heads, how-to | group/phrase |
| sliding-pill-captions | podcast clips, explainers | group |
| active-word-pop-captions | creator clips, hype ads | group |
| active-word-color-captions | podcast clips, interviews, comedy timing | group |
| gradient-word-captions | music promos, launches, creator brands | group |
| white-card-captions | SaaS, corporate, LinkedIn, education | phrase |
| serif-italic-captions | documentary, luxury, essays, narration | phrase |
| frosted-panel-captions | tech, product, lifestyle over rich footage | group |
| neon-tube-captions | nightlife, music, gaming, events | group |
| bounce-word-pill | hooks, ad openers <= 20 s | single |
| shadow-minimal-captions | cinematic vlogs, travel, calm brand films | phrase |
| karaoke-fill-captions | lyrics, sing-alongs, rhythmic VO | line |
| outline-spring-captions | gaming, reactions, commentary | group |
| word-tile-captions | listicles, tech/finance tips | group |
| tilted-card-word-pop | hooks, memes, beat promos | single |
| grow-highlight-captions | business podcasts, coaching ads | group |

Styled word-tracking captions are chosen for attention and rhythm; they amplify body language but cost some viewers the message [35]. Ship a plain phrase version (translucent-box-subtitles) as the accessible deliverable, and do not copy the trend look when the brand has its own type and colour [40].

_TikTok, YouTube, Instagram and Meta are named only to describe their published safe zones; their names, logos and interfaces are trademarks of their owners._
