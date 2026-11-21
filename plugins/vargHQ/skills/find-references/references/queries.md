# From a request to references

Write the brief, then search. The end product of this step is a written description of light and staging, plus a job
card per kept candidate. A pile of images is an intermediate. The method as a whole is `our proposal`: no published
end-to-end test of a brief-to-reference method exists, and ours has had two cold runs (`evidence.md`). Scoring lives in
`judge.md`, access in `sources.md`. In tables, `tested` means tested 2026-11-03.

## 1. Extract the brief

Fill the fields in `SKILL.md` step 0. Then list 8 to 12 things that belong only to this subject: place, materials, numbers,
rituals, printed things. "This list is also your picture search: each place, material and printed thing on it is a query"
([taste-skill](https://github.com/Leonxlnx/taste-skill/blob/main/skills/taste-skill/SKILL.md)).

**Ask at most two questions.** Make it a rule: models "often identify ambiguity when explicitly asked to judge it, yet
in the QA setting they overwhelmingly default to direct answers" ([Su & Cardie 2026](https://arxiv.org/abs/2605.25284)).

- Ask for hates: cheap to answer, and they seed `never.md`. Ask for the method only if you cannot infer it: it changes
  every pack.
- Also ask for real assets to be attached (brand, UI, founder, product). It does not count as a question, and copying real
  material beats any reference.
- Assume the rest and say so: 9:16 and 15 s for ads, 16:9 and 45 s for launch films, nothing licensed.
- A talking head is the one exception, since the person is the whole film: "What did you do before this? What do you
  refuse to do? What do people get wrong about you?"

## 2. Vague request: show three territories

For "make something cool for my coffee brand", do not ask what cool means. Show pictures.

1. Write three territories that differ on light and world: *Before the shop opens* (dark, one lamp), *Neighbourhood
   counter* (1970s, daylight, talk), *Cold precision* (glass, white, lab).
2. Run one cheap query per territory. Open results. Pick three images for each.
3. Show the 3 × 3 sheet with one question: "Which row is nearest, and which is worst?"
4. Nearest gives feeling, world and light. Worst seeds `never.md`. If nobody replies, continue with the most distinctive
   territory and say so.

`reported`: images in clarifying questions gave improvements "of up to 90% in retrieval performance" in general search
([Melon, Yuan et al. 2024](https://arxiv.org/abs/2402.07742)). Nobody has tested contact sheets for creative direction.

## 3. Run the obvious query first, then step sideways

The safe middle is countable. `tested`: Refs `{"query":"dark UI","category":"launch"}` returned 2,277 films (word matching,
so an upper bound), and `{"query":"coffee","ai_made":false}` returned 70, with top-card summaries including "brew macro" and
"surreal color-coded worlds". Name what repeats, write it as tests in `never.md`, and give those titles no credit.

The obvious search may not show the obvious thing (`SKILL.md` step 1): in the ad cold run `coffee` also matched a publisher
named Coffee Stain, and none of 15 thumbnails opened showed a pour.

Then go one or two steps only. Evidence on distance conflicts, with moderate distance best in [one
study](https://www.lrdc.pitt.edu/Schunn/papers/fuchanetal-near-far-2013.pdf), and none tests film. Results must still
read as the same job.

| Move | Example |
|---|---|
| Same job, adjacent field | Candlelight in paintings. Cover art for palette. Pre-war portraits for character |
| Native format | `tested` Met `q=hanging scroll&medium=Paintings&geoLocation=China&hasImages=true` 906 for 9:16. False friend: `q=pillar print&hasImages=true` 1,139 includes cotton textiles, so filter by medium |
| Walk back the chain | What the makers looked at: Nosferatu leads to "German Romantic painters, like Caspar David Friedrich" ([ASC](https://theasc.com/article/nosferatu-exhumes-a-vampire-classic/)). Cite it only once opened |
| Local words | "Search in the place's own words (azulejo, not 'blue tile'...)" ([imagery.md](https://github.com/Leonxlnx/taste-skill/blob/main/skills/taste-skill/references/imagery.md)). `tested` Rijksmuseum `kaarslicht` 10 against `candlelight` 3. Dutch worked for candlelight only: in the cold run `dageraad`, `ochtend` and `venster` gave 19 opened records with no window-lit room |
| Local archive | Read the author field of good Commons hits: institutions upload whole collections, then ask for them by name. Cold run: `"Biblioteca de Arte" azulejos` returned 10, from the Gulbenkian Art Library, found only by reading an author field |
| Date limit | Before November 2022 to avoid slop. Before 2000 to escape the current look |
| Ban your first three names | List the first three famous names you think of, delete them, then search |

When references conflict, "choose one dominant direction and preserve its sharp traits" instead of averaging
([Refero](https://github.com/referodesign/refero_skill/blob/main/skills/refero-design/SKILL.md)).

## 4. Build one pack per job, from five slots

| Slot | What it is | Use on |
|---|---|---|
| L, literal | The source's own facets and words | Every source |
| C, caption | One sentence describing the imagined frame in catalogue language | Semantic engines only (FrameThrower, a token source). **Skip it if you have no semantic engine** |
| N, named | A maker or work you then open and verify | Keyword engines, archives |
| A, adjacent | The same job from painting, architecture, print, photo books, local words | Met, Commons, Discogs, Are.na |
| X, excluded | What must not appear. Keyword minus-terms only, otherwise a post-filter | Google, YouTube API, Commons |

**The queries per job are a starting floor, not a limit. Stop a job when two queries in a row add nothing new.** The floors
are `our proposal`. In the cold run Light took 26 queries against a floor of 6, Location 24 plus 7 walks against 3, and one
word pair (`interior tile` in HABS) changed the result. Add one whole-brief control query.

**Priority depends on the method. Change the order and say so in your `queries.md`.** Generated: light first. In our
48-still test (3 scenes × 2 models, two LLM judges, small) removing the light line lost the most film-likeness, +0.50 (p =
0.04), while a written palette line lowered it, −0.67 (p = 0.03). Coded: type, motion and palette first, and light only
where a shot has it (a 3D scene, a single still, an HDRI). Cut a floor the piece does not earn: 19 light queries for one
still in a 45 s film were too many (cold run on a coded film).

| | Never | Light | Framing | People | Location | Texture | Palette | Type | Motion | Music |
|---|---|---|---|---|---|---|---|---|---|---|
| Queries | 2 | 6 | 4 | 4 | 3 | 2 to 3 | 2 | 2 to 3 | 3 | 3 |
| Sources | 2 | 3 | 2 to 3 | 2 to 3 | 2 | 2 | 2 | 2 | 2 | 2 |
| Evaluate, generated | 1st | 2nd | 3rd | 4th | 5th | 6th | 7th, from three named frames of candidates; re-extract after the pick | 8th | 9th | 10th |
| Evaluate, coded | 1st | if a shot has it | 5th | if a person appears | if needed | 6th | 4th, the same way | 2nd | 3rd | if needed |

No study here tests creative reference search, so treat each row as a direction:

| Rule | Why, `reported` |
|---|---|
| Keep the whole query, use parts to check candidates | Decomposition "during initial retrieval frequently harms retrieval performance due to semantic dilution, yet substantially improves reranking" ([Yin et al. 2026](https://arxiv.org/abs/2606.08577), text) |
| Never write negatives into a semantic query. Filter afterwards | Models "struggle significantly with negation, often performing at chance level" ([NegBench](https://arxiv.org/abs/2501.09425)). `tested` On Refs a long sentence containing "no people" returned 181: those words are just keywords |
| Keep only real hits from an imagined caption | It beat a baseline ([Gao et al. 2022](https://arxiv.org/abs/2212.10496)), but gains appeared where the text already held the answer ([Yoon et al. 2025](https://arxiv.org/abs/2504.14175)) |
| Use facets or image-to-image for framing | Text embeddings "behave as bags of concepts", weak on pose and viewpoint ([VisRet 2025](https://arxiv.org/abs/2505.20291)). A generated proxy image may serve only as a throwaway query and must never reach the board |

## 5. Shape each query for its engine

Each source has its own language. Open one known good result, read its tags or styles, and reuse those exact strings. A
silent zero usually means wrong vocabulary, so log it and show the person. Any catalogue facet beats describing it in a
sentence.

- Keyword indexes (Commons, Met, AIC, Openverse, Are.na) want one or two words.
- Semantic indexes want a plain phrase: "Search matches meaning, not keywords"
  ([mobbin](https://github.com/mobbin/skills/blob/main/skills/search/SKILL.md)).
- X needs one term or phrase per query and client-side re-filtering. Rules in `experts.md`.

| Job | Safe middle | One step further | `tested`: what came back |
|---|---|---|---|
| Light | `cinematic lighting` | Met `q=candlelight&medium=Paintings&hasImages=true` | 6 objects. Of two opened, [Holy Family with Saint Anne](https://www.metmuseum.org/art/collection/search/436344) was exactly right and [Saint Catherine](https://www.metmuseum.org/art/collection/search/436908) had no candle |
| Light | `description=candlelight` | Rijksmuseum `description=kaarslicht&type=painting` | 3 against 10 ([Rijksmuseum](https://data.rijksmuseum.nl/search/collection?description=kaarslicht&type=painting)) |
| Framing | `vertical video composition` | Met hanging scrolls, above | 906 |
| People | `old fisherman face weathered` | LoC FSA `fisherman`; Openverse `fisherman portrait` | Openverse 0 against 87; [LoC 243](https://www.loc.gov/collections/fsa-owi-black-and-white-negatives/?q=fisherman&fo=json&c=8) |
| Location | `moody liminal diner night cinematic` | Commons `Category:Diners in the United States` | Category found |
| Texture | `vintage film look` | Flickr feed tag `superia400` | 20 ([docs](https://www.flickr.com/services/feeds/docs/photos_public/)) |
| Type | `sci-fi title` | Fonts In Use `/tags/242/science-fiction`, a Typeset In The Future film | Found |
| Motion | `cool animation` | Refs `{"query":"kinetic type","category":"motion","ai_made":false}` | 1,827 of CPU coolers and cars against 64 on target |
| Music | `chill background music` | Discogs `style=Dub Techno&type=master&year=1996` | 47, including Pelon "No Stunts" |

Traps, `tested`: Openverse `wet street night neon reflection` returned 0, so use two words. Discogs `style=Library Music`
returned 0, so read the real style name off a known record. Met `q=Candles&tags=true&hasImages=true` returned 40 including a
button, so tags find subjects, not light.

## 6. Fuse, then open, then cut

Fusion merges duplicates and rank across queries: reciprocal rank fusion "requires no tuning" and defaults to 60
([Elastic](https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion)),
`score(d) = sum over queries of 1 / (60 + rank(d, q))`. Save each search's JSON, then:

```bash
python3 -I "$S/search.py" fuse a.json b.json --limit 20    # --per-maker N is optional; off by default
```

Fusion does not cut by maker: in the ad cold run a per-maker cut would have dropped The Visit, the top light candidate.
Read the top of each query too (`SKILL.md` step 4). Items with no maker never merge: Rijksmuseum's untitled IDs took 3 of
20 slots in Light.

Then, `our proposal`:

1. **Open every candidate you keep.** Keyword hits lie, as the Met row shows. Do not trust your own light label
   (`light.md`).
2. Merge what fusion missed: by canonical URL, then maker and title, then image hash.
3. Cut to a shortlist: one pick per maker in this job, and at most the second across the board. With embeddings, use MMR at
   λ = 0.7, our starting value and not a published one.
4. Give the person 3 candidates per job, shuffled, no scores, grouped by job. Never one ranked list: 182 participants
   showed more fixation from examples in a list than in context ([Chan et al. 2024](https://arxiv.org/abs/2401.11022)).
5. Close the loop once or twice (`SKILL.md` step 6).

## 7. Translate feeling into hypotheses

No validated dictionary exists, and no published mapping covers lens, framing, grade and tempo together on real footage.
Treat this as a starting guess that a chosen frame overrides. **M** means a measured effect exists, **C** means craft,
**H** means an untested hypothesis.

| Feeling | Light | Colour | Framing | Tempo and music |
|---|---|---|---|---|
| Tense | Low-key (M), one hard source (C) | Cool, hard contrast (C) | Low angle (C, M mixed), centred (C) | Minor, low register, loud (M, scary) |
| Mysterious | Low-key (M), hidden face lowers pleasantness (M, n = 9) | Dark, low saturation (H) | Foreground layers, doorways (C) | Slow, low dynamics (H) |
| Lonely, pressured | One source, large dark area (H) | Low saturation (H) | Centred, negative space (C) | Slow, minor, soft (M, sad) |
| Sad | Dim, soft (H) | Darker, lower saturation (M) | Close-up on a sad face (M, one study) | Minor, slow, low, dark timbre (M) |
| Warm, cosy | Warm colour temperature, lower intensity (M, rooms) | Warm, medium saturation (H) | Medium, close, eye level (H) | Slow, soft, major (H) |
| Joyful, energetic | Bright (M, appeal rises) | Bright and saturated (M) | Moving camera, wide (H) | Major, fast, high, staccato (M) |
| Powerful | Dark ground (M), high contrast (H) | Saturated, dark (M) | Low angle (M mixed) | Low register, loud (H) |
| Calm, peaceful | Soft, even, daylight (H) | Bright, low saturation (M) | Wide, static (H) | Slow, soft, high register (M) |
| Clean, exact, premium | Soft top light, shadow control (H) | Few hues, measured contrast (H) | Geometry, generous margin (H) | Moderate, steady, little reverb (H) |

Give two opposite adjectives different jobs. For "sad but hopeful", keep the light sad and let music or the last shot
carry hope: a craft guess. Effects are mostly small. Music has the strongest evidence, with cue models explaining 77 to
89% of rating variance ([Eerola et al.
2013](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2013.00487/full)).

## 8. Coded versus generated

The same film gives two searches. If generated: a desk lit by one lamp, and type kept out of the model. If coded: this,
`tested 2026-11-03`, cold run on a coded film. An invoicing app for freelance translators, 16:9, 45 s, in HyperFrames.
Loves Swiss railway posters and Dieter Rams. Hates dark-mode gradients and everything fading in. One generated still of a
translator.

| Job, in the order run | Queries | Came back |
|---|---|---|
| Never | Refs `{"query":"launch film","category":"launch","max_seconds":60,"ai_made":true}`, offsets 0 to 40; Impeccable | 41 cards, and their summaries gave the repeats; named patterns |
| Type | `commons-cat "Category:SBB Historic - Plakate"`; Poster House `keyword=12702&country=12842`; Fonts In Use `/uses/6396/der-film-exhibition-poster-and-catalog` | 48 sheets, the find of the run; 1; Akzidenz-Grotesk named. No record names a railway poster's typeface |
| Motion | Refs `{"query":"launch","made_with":"hyperframes"}`; `commons "filetype:video kinetic typography"`, `"filetype:video Bahnhofsuhr"` | 3, for a person to watch; 2 and 1, clips to measure |
| Palette | LAB command on named sheets | Six hex with shares on a flat sheet. Poor on a pictorial one |
| One still: light, people | LoC FSA `desk lamp`, Commons `Harriet Backer lamplight`; LoC FSA `translator`, Commons `traductrice bureau` | 1, 1, 3, 1, on target. Poly Haven was no use: no 3D, no sun |

No judge was needed: 24 reads on the still cut nobody. Output: `DESIGN.md` and `timing.md`. Beats assumed. The table per job
is in `SKILL.md`.

## 9. Feed far fewer references than a model accepts

Vendor limits are ceilings, `reported`:

| Model | Limit |
|---|---|
| [Kling 4.0](https://kling.ai/quickstart/kling-4-model-user-guide) | ≤15 assets. Without stated roles "the model will infer their intended use, making the results less predictable" |
| [Seedance 2.5](https://docs.byteplus.com/en/docs/ModelArk/seedance-2-5-prompt-guide) | ≤50, second-hand: the page body did not render for us |
| [Veo 3.1](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/video/use-reference-images-to-guide-video-generation) | "up to three images of a single person, character, or product". No documented style type, so a light reference becomes words |
| [Nano Banana 2.1](https://aistudio.google.com/docs/image-generation) | 14 total, ≤10 objects and ≤4 characters |

Scores fall with count. MultiBanana scored Nano Banana 7.817 with one reference, 4.891 with two, and 4.453 averaged over
3 to 8 objects ([paper](https://arxiv.org/html/2511.22989)). Adherence falls when references "carry a salient state of
the controlled attribute", most for light ([VIF-Bench 2026](https://arxiv.org/html/2609.37709)). Those are older or
adjacent models: nobody has benchmarked Kling 4, Seedance 2.5 or Nano Banana 2.1 by count. The working rule,
`our proposal`:

- Feed 1 to 5. Each gets one role and stated exclusions: `@ImageN defines X only. Do not copy Y, Z from @ImageN.`
  ([post](https://x.com/AiwithBloodline/status/2115841225106604469))
- Light identity references flat, so the light reference can work
  ([post](https://x.com/sirlifehacker/status/2115227821912281228) uses 18% grey).
- Pass only what the shot needs.

## 10. One brief end to end

Raw request: "make something cool for my coffee brand". Assumed brief: someone cares about this before you are awake;
quiet, earned, not cosy; a small roastery now; generated plates, coded end card; 9:16, 15 s. Row one of the sheet
assumed chosen. FrameThrower lines were not run.

| Job | Queries |
|---|---|
| Never | `tested` Refs `{"query":"coffee","ai_made":false}` 70. Seen: brew macro, capsule choice, surreal product worlds. Expected and unconfirmed by any agent source: slow-motion pour, latte art, falling beans, steam on black. Person: Meta Ad Library, TikTok Creative Center |
| Light | `tested` Met `q=candlelight&medium=Paintings&hasImages=true` 6. `tested` Are.na `practical light` 22 pages. Not run: FrameThrower caption `one bare work lamp over a steel table before dawn, hands half lit, room falling to black`. Person: Google `"practical light" film still before:2022-11-30` |
| Framing | `tested` Met `q=still life&medium=Paintings&hasImages=true&dateBegin=1600&dateEnd=1800` 87. Not run: FrameThrower `closeup` and `high_angle` filters (the `extreme-close-up` value on its developers page is not in the OpenAPI enum) |
| People | Who: a third-generation roaster who tastes before sunrise and distrusts marketing. `tested` Met `q=Lewis Hine&artistOrCulture=true&hasImages=true` 61; Commons `"August Sander"` 75, many about the archive |
| Location | `tested` Commons `"coffee roaster" interior -Starbucks` 70, surfacing a small German roastery |
| Texture | `tested` Poly Haven `t=textures&c=fabric` 43. Openverse `burlap` returned HTTP 500 at test, retry once |
| Palette | First board: three named frames of candidates. After the pick, re-extract from the picked frame. Keep it loose |
| Type | Person: Fonts In Use `search?terms=coffee` for the competitive set, then `terms=hardware`. Set in code |
| Motion | `tested` The coffee results as anti-reference. Not run: Refs `{"query":"macro","category":"films","max_seconds":30,"ai_made":false}` |
| Music | Slow, soft, low dynamics (M, peaceful). `tested` Discogs `style=Dub Techno&type=master&year=1996` 47; Openverse audio `dub techno` 240, for licensed temp only |

Feed: 2 images, a neutral roaster sheet and a neutral packaging sheet. Light goes in words, read from the opened
painting.
