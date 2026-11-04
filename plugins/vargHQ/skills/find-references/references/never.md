# Never references

A never board lists what must not appear in the references or the final video, as tests a stranger can check. It proves
nothing about quality. Two tests run separately: slop (the default look) and AI (who made it). A human-made reference
can be slop, and an AI frame can pass as human. Run provenance on references and the never board on everything.

Tests come from two places: the search you ran, and the person's stated hates.

## Build the board from the default

1. Run the obvious search, then the laziest version of the brief, and ban what comes out. Finding references makes nothing,
   so a throwaway code render, or one or two cheap images, happens only if the person agreed. Otherwise read a gallery or
   Impeccable. Say what the search actually returned, and
   mark anything expected but unconfirmed: in the ad cold run Refs `coffee` reached 17 coffee cards of 48, 9 of them
   Nespresso, so the board described Nespresso and not small roasteries. For ads, the real picture of a category is in Meta
   Ad Library and TikTok Creative Center, which are person-only: write those links.
2. Write each entry as "reject if" something a stranger can check, on a frame, a clip or a text as fits, and say which. A
   slow-motion pour, the one hate in that cold run, cannot be seen on a frame at all. Add a positive translation for the
   prompt, where you saw it (URL and date) and a review date. Add an exception line where real work can trip it.
3. Sort into tiers. **Category:** what the search showed competitors doing. **Project:** the person's stated hates, what was
   rejected last time. Universal checks (provenance, a surviving physics or functional check, burned-in default text and
   music) run on everything anyway, so list one only when you saw it in the search or the person hates it.
4. Keep about 7 to 12 entries and 3 to 6 negative images, `our proposal`: no study covers list length.
5. Apply it at four gates. **Intake:** drop a reference only if what matches a test is what it lends. De Hooch's The Visit
   shows people drinking, yet it lends only light, so it stays. **Prompt:** positive translation. **Frame QA:** check at
   100% crop. **Cut QA:** sweep against the previous project for repeated openings and entrances.
6. Review at the start of each project, because tells expire: purple gradients gave way to cream within about a year in
   a single source.

| Bad | Why | Good entry |
|---|---|---|
| "no AI look" | Not observable | **Reject if** at 100% crop the skin shows one even sheen and no pores. **Prompt as:** "visible pores, uneven tone, matte T-zone, fine flyaway hairs". Skip when the brief is beauty |
| "no bad text" | Unverifiable | **Reject if** OCR of any frame differs from the script by one character |
| "not cinematic" | Real photos look cinematic too | **Reject if** the backlit haze and rim light have no source in frame. **Prompt as:** "single tungsten lamp frame left, daylight from the window, shadows fall right" |
| "no floaty camera" | No shared meaning | **Reject if** camera speed stays constant from first frame to last with no start, stop or reason. **Prompt as:** "handheld, stops when she stops, small correction at the end". A taste rule |
| "no slop music" | Not a test | **Reject if** the lyric is syllables with no meaning, or the piano part needs more than 10 notes at once |
| "don't look like template" | Vague | **Reject if** the same entrance animation plays on more than one section, or a mono eyebrow label sits above every heading |

Starter ideas for what to look for, kept only if you see them: an object in frame would not work. A shadow, reflection or
contact does not match its source. More than one section uses the same entrance. A model-added subtitle or music track. The
softest shot in an edit stands out next to its neighbours. Narration is warm and even with no change in pace.

**Name this one: a character sheet cloned from a found photo.** "create a character sheet from a pinterest pic...
Strictly keep 100% of face, hair, body, clothing and all details"
([post](https://x.com/simonecanciello/status/2116268465463976312), 2,318 likes, 4,033 bookmarks, 340,703 views,
2026-10-30). The recipe copies a stranger's likeness. **Reject if** an identity reference starts from a photo of a
person you cannot name and hold a release for. **Instead:** write who the person is (`people.md`), then use your own
face, a consenting person with a signed release naming AI use, or a generated fictional person with no resemblance to
anyone.

**Removal alone is not enough.** "the 'avoidance aesthetic': anyone could guess it from the category plus the list of
things to avoid" ([tells.md](https://github.com/Leonxlnx/taste-skill/blob/main/skills/taste-skill/references/tells.md)).
So run subject inventory, references, a lock, then the never check. Name no replacement fonts or colours: "every
published 'use this instead' list has become the next wave of tells within months" (tells.md). `DESIGN.md` names the one
font you picked, which is a different list (`type-graphics.md`). Separate defaults from
bans: "the brief's own words can earn any of them"
([impeccable](https://github.com/pbakaus/impeccable/blob/main/skill/reference/craft-floor.md)). A hit is "a reason to
look closer, not a verdict" ([Impeccable](https://impeccable.style/slop)).

**A token that looks like a tell is earned when it names its source frame.** A 1957 Müller-Brockmann
[poster](https://commons.wikimedia.org/wiki/File:Josef_M%C3%BCller-Brockmann_1957.jpg) truly measures `#F4F1EA` at 36.4%,
crop 96% (`tested 2026-11-03`, cold run on a coded film). **Reject if** the token sits near a tell and names no source
frame.

## Dated tells, late 2026

Most evidence uses 2024-era models. No equivalent study has run on Nano Banana 2.1, GPT Image 2.5 or Seedance 2.5. Date
every tell. Tells catch defaults. They never prove a frame is human.

| Medium | Still useful | Stale or weak |
|---|---|---|
| Image | Functional and physics errors, the hardest category at 64.1% with an 18-point gain from unlimited viewing ([Kamali et al.](https://arxiv.org/html/2502.11989)). Plastic skin (professional beauty looks the same). Attractor subjects: 700 runs converged, with 12 dominant motifs of "visual elevator music" ([Hintze et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC12827715/)) | Hands and garbled text on leading models. Farid: "it's not six fingers or garbled text" ([Berkeley](https://www.ischool.berkeley.edu/news/2025/bbc-interviews-hany-farid-clues-give-away-ai-generated-footage)). "Cinematization" is a taste problem, since it is "very common for authentic photographs" ([guide](https://arxiv.org/abs/2406.08651)) |
| Video | Broken physics: 25 of 40 participants used this "logic" strategy ([arXiv 2602.03374](https://arxiv.org/html/2602.03374)). Impossible logistics. One soft shot in a sharp edit ([post](https://x.com/tetsuoai/status/2115277212824019367)). Model-added subtitles and music, per [Kling's guide](https://kling.ai/quickstart/kling-4-model-user-guide) | Low resolution helps only on scraped references. Clip length is fading. Floaty camera has no peer-reviewed source |
| Code motion and type | "fade-and-slide-up entrances on each section" and the five current clusters, including warm cream near #F4F1EA with a terracotta accent near #D97757 and #0B0B0B standing in for black ([Anthropic](https://raw.githubusercontent.com/anthropics/skills/main/skills/frontend-design/SKILL.md)). "centered text, gradient background" ([post](https://x.com/rexan_wong/status/2103707054108299437)). Graphics pinned to the screen and not the scene, dark gradients that band on upload, counters that jiggle ([post](https://x.com/tetsuoai/status/2115277212824019367), 436 bookmarks). 68 catalog entries, 62 detector rules ([Impeccable](https://impeccable.style/slop)) | Inter and purple gradients are the older tell. The current official file no longer names them. All "are legitimate for some briefs" |
| Launch films | "Fast cuts, black and white, historical film, rocket ships... Every YC company has the same video" ([post](https://x.com/ndrewpignanelli/status/2115465586822316257), 184 bookmarks) | Opinion |
| Voice | Cloned voices are heard as more authoritative and warm, with reduced variance in accent and speaking rate ([Zhou et al. 2026](https://arxiv.org/abs/2605.16578)). Ban the same warm agent | Vocabulary tells expire by model era ([WP:Signs](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)) |
| Music | Impossible performance: piano over 10 simultaneous notes, guitar beyond the fretboard, pseudo-lyrics ([MUSEBENCH](https://arxiv.org/html/2610.20310)). "Everything sounds too glossy" ([Start-Track](https://start-track.com/start-tracks-guide-on-how-to-spot-ai-music/), one writer's advice) | Popularity does not filter: up to 85% of 2025 streams on AI tracks were fraudulent ([Deezer](https://newsroom-deezer.com/2026/07/ai-music-exceeds-50-percent-daily-uploads-deezer/), sells detection) |

## Negatives backfire in prompts

Across 11 text-to-image models, 9 scored lower on a negated statement, and 41.5% of failed statements rendered exactly
what the prompt forbade ([NegT2IBench](https://arxiv.org/abs/2610.03084)). So translate the board into positive
description. Use a negative line only where the vendor documents it. "Convert style words into camera/light/material
behaviors (not filters)" ([post](https://x.com/IamEmily2050/status/2018697592800981099), 2,676 bookmarks). No published
comparison of the two phrasings exists for Seedance 2.5, Kling 4 or Veo 3.1. `reported`:

| Generator | Vendor says | Do |
|---|---|---|
| Veo | "no" and "don't" are "Not recommended" ([guide](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/video/video-gen-prompt-guide)) | Describe what you don't want in plain nouns, such as "wall, frame" |
| Runway Gen-4 Image | A negative prompt "may result in the opposite happening" ([guide](https://help.runwayml.com/hc/en-us/articles/35694045317139-Gen-4-Image-Prompting-Guide)) | Positive only |
| Kling 4.0 | "Only two types of negative instructions are truly necessary: no subtitles and no background music" ([guide](https://kling.ai/quickstart/kling-4-model-user-guide)) | Those two, nothing else |
| Seedance 2.5 | Audio negatives such as "No BGM; generate only environmental sounds and action sounds." ([BytePlus](https://docs.byteplus.com/en/docs/ModelArk/seedance-2-5-prompt-guide)) | Audio constraint at both the beginning and the end |

## Keep slop out of a search

Eyes and detectors both fail, so prove provenance first. `reported`: people score 76% on AI images from 2024 models, 72%
at a one-second glance and 82% at 20 s ([Kamali et al.](https://arxiv.org/html/2502.11989)). On 5-second talking clips
from 2026 models they score 52.6% on fakes, and the best detector's AUROC is 69.7
([DF26](https://arxiv.org/abs/2609.07369)). Curated images were detected less than the mean regeneration in 35 of 39
cases, so viral AI images are the worst case for a search. Text-image models ranked AI images above real ones ([Xu et
al.](https://arxiv.org/html/2311.14084)), so never let CLIP-style rank decide what reaches a person.

**Sort sources by when the collection closed.** `tested 2026-11-03`:

| Source | Call | Returned |
|---|---|---|
| Commons search | `"low key" portrait filetype:bitmap -deepcat:"AI-generated images"` | 83 |
| Commons record | `action=query&titles=File:<name>&prop=imageinfo&iiprop=timestamp\|user\|extmetadata\|commonmetadata` | Upload date, author and camera in one call. The best provenance check found |
| Internet Archive | `title:(lighting) AND mediatype:image AND addeddate:[* TO 2022-11-30]` | 90, with noise such as "Tree Lighting" |
| [LoC](https://www.loc.gov/photos/?q=window+light+portrait&fo=json&c=5&dates=1900/1970) | `q=window+light+portrait&fo=json&dates=1900/1970` | 48 |
| Wayback | `web.archive.org/cdx/search/cdx?url=<page>&matchType=exact&limit=1&output=json&fl=timestamp,original` | First capture of a page. An empty result does not mean new |

Date cuts, `our proposal`: 2022-01-01 when you need strict human work, 2022-11-30 as the looser default. A date limit is
a heuristic and discards good recent human work. `tested 2026-11-03`: an agent's search tool ignored Google's `before:` and
returned a page dated 2022-12-16 and a guide dated 2025. Verify each date.

**Filters reduce AI. None excludes it.**

| Filter | How it works | Maker's own limit | Access |
|---|---|---|---|
| [DuckDuckGo](https://duckduckgo.com/duckduckgo-help-pages/results/how-to-filter-out-ai-images-in-duckduckgo-search-results), `noai.duckduckgo.com` | Blocklist. [List](https://github.com/laylavish/uBlockOrigin-HUGE-AI-Blocklist) last pushed 2025-10-02 | "These lists are not exhaustive" | `person`. `tested 2026-11-03`: non-JS fetch returned no results |
| [Kagi](https://help.kagi.com/kagi/features/exclude-ai-images.html) `ai:none`, `ai:only` | Website reputation | "no reliable way to automatically identify AI-generated images" | Paid, `person` |
| [Slop Evader](https://github.com/tegacodes/slop-evader) | Limits search to before Nov 30, 2022 | "just a convenience" | `person` |
| [Cosmos](https://help.cosmos.so/en/articles/11717948-content-filtering) | "Show", "Blur", "Hide" setting | Founder on banning AI: "That's not a line that I want to draw." ([Fast Company SA](https://fastcompany.co.za/co-design/2026-01-21-have-you-heard-of-cosmos-an-alternative-to-pinterest-and-instagram/)) | `person` |
| [Pinterest](https://help.pinterest.com/en/article/gen-ai-labels) | "AI modified" label from metadata and classifiers | Admits it may miss. Follow each pin to its origin | `person` |
| [Refs](https://refs.video/mcp) `ai_made:false` | Its own schema: true = "made with AI/code (Claude, Remotion, three.js)", false = human-made | So `false` also removes code-made films, and `true` mixes them with generated. For a coded piece use `made_with` | `agent`, `tested 2026-11-03` |
| [Pexels](https://www.pexels.com/acceptable-use-policy/), [Unsplash+](https://help.unsplash.com/en/articles/6604629-what-types-of-content-do-you-accept), [Dribbble](https://dribbble.com/guidelines) | Rules against generated uploads | Users report AI anyway. Unsplash's covers Unsplash+ only | Rule, not proof |

**The byte scan is one-way.** A hit rejects. A miss proves nothing.

```
python3 -I "$S/ai_marker.py" <file-or-folder> [more ...]
```

It looks for `trainedAlgorithmicMedia`, `compositeWithTrainedAlgorithmicMedia`, `SynthID`, `OpenAI` and `Made with
Google AI`, and reports `c2pa`. It is a string check, not signature validation. `tested 2026-11-03`: 15 of 15 generated
stills carried a marker and 0 of 40 non-AI files did, and five re-encode methods (ImageMagick resize and `-strip`,
`sips`, ffmpeg to JPEG and to PNG) all read `miss` afterwards. So any re-encoded web copy reads clean.

`c2pa` alone prints `READ`, not `REJECT`: Content Credentials are a general format, not an AI label (`our proposal`), so
a person opens the manifest at [verify.contentauthenticity.org](https://verify.contentauthenticity.org/).

Detectors misfire both ways, so never pass a reference on one ([NewsGuard](https://www.newsguardtech.com/?p=33448)). Do
not ask a vision model "is this AI?": multimodal LLMs "struggle with hallucination" on it ([arXiv
2506.07045](https://arxiv.org/abs/2506.07045)).

**Finish every reference with one label**, checking in order of cost: film title or holding archive, named author, body
of work, date, credits, byte scan, EXIF, oldest copy (person-run), the look at 100% crop. `our proposal`: no study
validates this sequence.

| Label | Means | Use |
|---|---|---|
| **HUMAN-PROVEN** | A verified film title or named archive or museum as holder, or a named author plus a date before 2022 plus a body of work or credits | Any job |
| **LIKELY HUMAN** | A named author or a date, with nothing against | Measure light and framing, note the risk |
| **UNKNOWN** | Nothing proven | Mood only. No measurements, no feeding |
| **AI** | A marker, or the maker says so | Never board only |

"No AI marker" and "detector says human" are never a pass. Real productions get called AI as well
([post](https://x.com/DCdaily/status/2027399224887804298)), and human-labelled sources can be contaminated, as one
illustrator alleges of artists tracing AI images ([post](https://x.com/nekomichiii/status/2117448342544568459), no
evidence shown).

## Where to find real negatives

Record the date on every negative, and re-check any older than 12 months. Pull from the niche too: the dangerous
negative is the tasteful default, and "farmer girl" bait will never tempt a client.

| Source | Route | Access | Verdict |
|---|---|---|---|
| Commons AI category | `portrait deepcat:"AI-generated images"`, `tested 2026-11-03` 103. Use `deepcat:`, since files sit in subcategories | `agent` | Best free labelled set |
| [Impeccable](https://impeccable.style/slop) | Read the catalog of 68 entries | `agent` | Best for code video |
| [Civitai](https://developer.civitai.com/site/reference/images.md) | Site API: generated images with prompts. Not re-tested | `agent` | A model's defaults |
| [@FacebookAIslop](https://x.com/FacebookAIslop/status/1868764698331824242) | `from:FacebookAIslop`, curated since 2024, 11,653 bookmarks on the top post | `token` | The bait end only |
| Kagi `ai:only`, r/aislop | Links only. Reddit returned 403 | `person` | Fast slop board |

## Human references still produce slop

A reference produces slop when everyone uses it, when only its surface is copied, or when the model's defaults pull it
back. The Wes Anderson AI trailer copied "bold pastel coloring" and "has approximately zero soul"
([SlashFilm](https://www.slashfilm.com/1274079/a-i-generrated-wes-anderson-star-wars)).

Five tests, all reasoning and untested, `our proposal`:

1. **Prompt pack.** If a name has its own prompt pack or "X style" preset, go to what its makers looked at or to one
   specific scene.
2. **Surface.** If you can only list pastel, symmetry and stares, you have a costume. Say why the look exists.
3. **Swap.** Change the brief and see if the board stays the same. If it does, the board is a default.
4. **Spread.** Take references from different media and eras.
5. **One axis.** Borrow one thing per reference.

Do not pass a director or artist name to a generator. Pass measurements. This also avoids the "style of" call with a
living artist.

## Judge it

Criteria N1 to N5 in `judge.md`.
