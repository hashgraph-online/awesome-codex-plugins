---
name: video-packaging
description: "Generate or critique video packaging — title + thumbnail-text pairs where the title carries context and keywords, the thumbnail text carries the tension, and any word echoed between them is rejected as wasted real estate. Generate mode delivers 3 pairs tagged by discovery intent (search vs browse) with a recommendation and A/B note; critique mode returns a PASS/FIX/FAIL verdict with 3 fixed pairs. Triggers on \"/digital-marketing-pro:video-packaging\", \"title for this video\", \"thumbnail text ideas\", \"why is no one clicking this video\", \"critique this title\", \"package this video\". Pairs with /digital-marketing-pro:video-script, pulls real query phrasing from /digital-marketing-pro:keyword-research for search-intent titles, and gates title claims through /digital-marketing-pro:check before anything ships."
argument-hint: "[brand-name] [--topic <video topic>] [--critique \"<existing title> / <thumb text>\"]"
user-invocable: true
---

# /digital-marketing-pro:video-packaging

Packaging decides whether a video gets watched; the content only decides
whether it deserved to be. On every video surface the viewer sees two elements
at once — the title and the thumbnail text — and the craft is that **they must
do different jobs**:

- **The title carries context and keywords** — what the video is, phrased the
  way people search and the way the platform's systems read it.
- **The thumbnail text carries the tension** — the number, the contradiction,
  the "wait, what?" that a human reacts to in half a second.
- **Overlap is wasted real estate.** A thumb word that already appears in the
  title bought nothing with the scarcest pixels the brand owns.

## Discovery intent — tag every package

A video idea earns discovery one of two ways, and the packaging differs:

| Intent | How it is found | Packaging consequence |
|---|---|---|
| **Search** | Typed queries; ranks over months | Title leads with the query phrasing (front-load the keyword); thumb adds the differentiator vs the other results |
| **Browse** | Suggested/home feeds; spikes on click-through | Title can spend more of its length on intrigue; thumb carries the pattern-break |
| **Both** | Rare; usually a search topic with a browse-worthy angle | Package for search, let the thumb do the browse work |

**No search or browse logic → not a video idea yet.** Route it back through
topic development before spending packaging effort on it. For search-intent
videos, pull the real query phrasing from
/digital-marketing-pro:keyword-research rather than guessing it.

## Generate mode

Input: the topic or concept, the brand, target platform, intent if known.

```
# Video packaging — [topic]

**Discovery intent:** Search / Browse / Both — [the reasoning in one line]

## Pair 1 — [angle: curiosity / benefit / identity]
**Title:** [≤60 chars where possible — what survives truncation comes first]
**Thumb text:** [1-3 words]
**Why they pair:** [the different jobs, and how they combine into one click decision]

## Pair 2 — [different angle]
## Pair 3 — [different angle]

## Recommendation
[Which pair leads and why — grounded in the intent tag, not taste]

## A/B note
[Which single element to vary if testing — never both at once]
```

## Critique mode

Input: an existing title and/or thumbnail text (works from a screenshot
description too).

```
# Packaging critique — [the draft]

## Verdict: PASS / FIX / FAIL

## The pairing check
[Do title and thumb do different jobs? Quote any echoed words — each is the
finding, verbatim.]

## Working
[What earns its place]

## Not working
[Specific, quotable problems — vague titles, buried keywords, thumb text
restating the title, curiosity with no clarity]

## 3 fixed pairs
[Revised packages, same content, same claims — packaging never promises what
the video does not deliver]
```

## Critical rules

- **Reject any pair where a thumb word appears in the title.** This is the
  countable core rule — check it word by word, not by impression.
- **Titles ≤60 characters where possible**; when longer, everything that
  matters sits before the truncation point.
- **Thumb text: 1–3 words.** Four is a caption, not a thumbnail.
- **Clarity beats curiosity.** A pair that intrigues but does not say what the
  viewer gets fails — curiosity-gap packaging that the content cannot pay off
  is churn, and on regulated brands it is a compliance finding.
- **Packaging never outpromises the video.** The claims in a title pass the
  same brand guardrails as any other copy; run /digital-marketing-pro:check
  before anything ships.
- **Three pairs minimum in Generate; three fixes minimum in Critique.** One
  option is a decision already made; the client gets choices with reasoning.
- **Tag the intent every time.** An untagged package is a guess about how the
  video will be found — and search and browse reward different structures.

## Pairs with

- /digital-marketing-pro:video-script — the script this packaging fronts;
  its thumbnail-concept step follows the same pairing rule
- /digital-marketing-pro:keyword-research — real query phrasing for
  search-intent titles
- /digital-marketing-pro:check — claims and compliance gate before publishing
