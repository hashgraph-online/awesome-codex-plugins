# Evidence behind the ranking

All collected on 2026-11-03. Full write-up with charts: https://varg.ai/how-to/make-a-moodboard-for-an-ai-video.
Raw data and scripts: https://github.com/vargHQ/aeo/tree/main/research/2026-11-03-moodboards (private).

## 1. The 48-still line test

Three scenes (night bus stop, perfume bottle, cyclist on a mountain pass), each as a six-line board (palette, light,
framing, texture, type, motion), with one line removed at a time, and with no board: 8 versions × 3 scenes ×
2 models (Nano Banana 2.1, Seedream 5 Pro) = 48 stills at $0.05 each. Two blind judges (Opus and Sonnet, r = 0.96
over 336 paired scores) scored each line 0–2 and film-likeness 1–10.

Share of the line's spec met in the image:

| Line | Left out | Written | Lift | Nano Banana 2.1 | Seedream 5 Pro |
|---|---|---|---|---|---|
| Type | 0% | 73% | +73 | 78% | 68% |
| Palette | 29% | 89% | +60 | 94% | 83% |
| Framing | 17% | 76% | +59 | 86% | 65% |
| Light | 35% | 88% | +53 | 90% | 86% |
| Motion | 8% | 57% | +49 | 51% | 62% |
| Texture | 50% | 81% | +31 | 78% | 83% |

Film-likeness, full board minus the board without that line (mean of 6 pairs, one-sample t-test):

| Line | Adds | p |
|---|---|---|
| Light | +0.50 | 0.04 |
| Texture | +0.33 | 0.39 |
| Framing | +0.25 | 0.08 |
| Type | +0.08 | 0.86 |
| Motion | −0.25 | 0.41 |
| Palette | −0.67 | 0.03 |
| Whole board vs no board | +1.00 | 0.01 |

Pixel check: removing the palette line moved pixels from mean ΔE 13.3 to 19.9 off the brief's hex set; removing any
other line changed it by less than 1.5. Colour histogram distance from the full board: no palette 0.451, no board
0.572, other lines 0.13–0.20.

Where it failed: Seedream met the top-down perfume framing 50% and the straight-down aerial 58%; wheel blur on the
cyclist 0–17%; one title misspelled ("ASCENST"). Every image a judge flagged as "wrong brief" was a no-board image.

Limits: one image per prompt; stills only show frozen motion; judges are models; references and subject lock were
not in the test.

## 2. X (Twitter)

160 queries over three windows (7 days, since July, all-time top) → 6,086 unique posts (2,634 from Oct 27–Nov 3,
5,001 about AI creation). Seven reader agents read the top 220 posts per dimension (1,540 posts); 218 quotes were
checked word for word by script.

Save multiplier for posts that mention a topic, against similar posts (OLS on log bookmarks with views, age, media and
length; n = 4,722 posts with ≥500 views; 95% CI):

| Topic | Saves | 95% CI | p |
|---|---|---|---|
| References | ×1.25 | 1.14–1.38 | <0.001 |
| Type | ×1.23 | 1.10–1.36 | <0.001 |
| Palette | ×1.20 | 1.08–1.33 | <0.001 |
| Sound | ×0.97 | 0.87–1.08 | 0.61 |
| Motion | ×0.94 | 0.85–1.04 | 0.24 |
| Texture | ×0.93 | 0.83–1.04 | 0.19 |
| Framing | ×0.86 | 0.77–0.97 | 0.01 |
| Light | ×0.79 | 0.70–0.89 | <0.001 |
| Subject | ×0.74 | 0.66–0.82 | <0.001 |

Specific vs vague wording (same model): hex codes ×1.58 (n = 79), named fonts or px sizes ×2.19 (n = 87), vague
words ("cinematic", "beautiful", "stunning", "8k", "hyperrealistic") ×0.69 (n = 2,144).

"This matters most" claims found by the readers: light 11, texture 9, motion 9, framing 8, palette 7, type 3; in the
overall packet references 3, subject 2, sound 2, light/texture 2. Light talk gets claims and likes, not saves; posts
that hand over a reusable asset (a reference, hex codes, a font) get saved.

## 3. Official guides (14 rows, 13 vendors)

Explicit advice per dimension: subject 14, style/references 14, light 13, framing 13, palette 12, type 12, motion 11
(every video guide), texture 10, audio 8.

What they put first:
- Subject first: Kling, Seedance 2.0, Luma Ray2, Wan, Nano Banana.
- Look first: Veo 3.1 ("[Cinematography] + [Subject] + …"), Sora 2 ("Establish this style early"), Pika H3 Flex,
  Higgsfield ("GLOBAL STYLE comes first"), GPT Image (scene first).
- Order does not matter: Runway ("The order in which elements are introduced in a prompt do not matter"); Midjourney
  sets none.
- Reference roles first: Kling 4.0, MiniMax H3, Seedance 2.5.
- Everyone: for image-to-video, prompt motion only. Seedance: "place important content at the front".

## 4. Benchmarks and perception research

- Camera motion followed: VBench mean 49.58% over 13 models (Sora 27.16%, Kling 1.6 61.73%, Veo 3 54.94%).
- Changing an attribute during a shot: "models fail in about 80% of the time" (VBench-2.0).
- Colour is the easiest attribute, then texture (T2V-CompBench; Kling-1.0 colour 0.7971, texture 0.6149).
- On-screen text: best 0.37 (T2VTextBench, Sora); exact text in layouts Sora-2 0.671, Veo 3.1 0.416, reference 0.940.
- What vision models read in film frames (ShotBench, mean of 24): framing 64.1%, lighting type 57.5%, shot size
  53.3%, camera angle 45.6%, composition 43.0%, lighting condition 41.6%, lens size 37.7%, camera movement 37.4%.
- Aesthetic scores (EVA): content 0.3423, composition and depth 0.2937, light and colour 0.2671, technical 0.1242.
- Colour and emotion: Pleasure = .69B + .22S, Arousal = −.31B + .60S (Valdez & Mehrabian 1994).
- Film editing outweighs colour for emotion (Cao et al. 2024: η²p 0.715 vs 0.001).
- Average Hollywood shot length fell from ~10 s (1930s–40s) to under 4 s after 2000 (Cutting 2011).
- "lighting" appears in ~14% of 2.2M DiffusionDB prompts; "cinematic" in ~13.6% of Midjourney prompts.

Every source URL: `links.md` §4 and §5.
