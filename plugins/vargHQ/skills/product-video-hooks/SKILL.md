---
name: product-video-hooks
description: >-
  Turn a product into scroll-stopping video hooks. Writes the first 3 seconds of TikTok, Reels and
  Meta product videos as three agreeing layers (what is on screen, the spoken line, the text
  overlay), from the buyer's own words, across 20+ hook types taken from Meta's Hooks Menu,
  Motion's 2026 hook data, Hormozi's callouts and the TikTok openers that spread in 2026 (late
  discovery, compliment then reveal, problem and fix in one clip, reply to a comment). It matches
  each hook to the buyer's awareness, checks it against platform claim rules, and, when footage
  exists, makes one MP4 per hook for testing. Use when someone asks for hooks, openers, the first 3
  seconds, a better intro, or new hook variants for a product video or ad. NOT for whole ad plans
  (use ecommerce-video-ads), generating a viral-style product-in-use hook clip from photos (use
  varg-product-hook), app or SaaS hooks, or YouTube titles and thumbnails.
license: MIT
metadata:
  author: vargHQ
  version: "1.0.0"
  varg.cost.typical: "free for written hooks; ~20–120 credits per generated 3 s hook clip (estimate)"
  varg.cost.estimate_tool: "varg:estimate_cost"
  varg.runtime.typical: "5–20 min"
  varg.models: "nano_banana_2_1, kling_v4_flash, kling_v4, seedance_2_5, eleven_v4, ffmpeg"
  varg.outputs: "hook list (markdown), mp4 9:16 hook clips"
  openclaw:
    requires:
      anyBins:
        - curl
    homepage: https://varg.ai
compatibility: >-
  Writing hooks needs nothing. Generated hook clips need the varg MCP (https://mcp.varg.ai/mcp) or
  VARG_API_KEY; joining hooks to an ad uses ffmpeg (see ecommerce-video-edit).
allowed-tools: Bash(curl:*) Bash(ffmpeg:*) Read Write Edit
---

# Turn a product into scroll-stopping video hooks

A hook is the first 2–3 seconds, and it decides whether anyone sees the rest. TikTok: say the value in 3 s, finish the hook by 6 s (90% of ad recall happens in the first 6 s). Meta: a hook delivered through both picture and sound gives 1.5× the purchase intent. Billo's H1 2026 average Meta hook rate (3 s views ÷ impressions) was 25.44%: Health & Beauty 28.1%, Apparel 22.9%, Pets 21.3%.

But a hook only has to stop the right people. Barry Hott scaled ads with hook rates under 15%, and an ad with a 39.5% hook rate but 14.3% hold still burned money. **Relevant beats loud. The hook must lead into the product.**

## 1. Inputs (ask once)

- The product and the **one thing it visibly does**
- The buyer and their exact words about the problem (reviews, comments, Reddit). Copy phrases word for word.
- Where it runs (TikTok Shop, TikTok ad, Meta ad, organic) and what is provable

## 2. Write each hook as three layers

| Layer | What | Example (knee sleeve) |
|---|---|---|
| Visual (0:00) | What is in frame on the first frame | A woman, 55, stops halfway up the stairs, hand on her knee |
| Spoken | One line, under 12 words | "If your knees crack on the stairs, watch this." |
| Text overlay | The same promise in ≤8 words, inside the safe zone | "Knees crack on stairs? 👇" |

The three must agree. "Odd visual + caption + voiceover all saying the same thing" is how operators report 50%+ hook rates.

## 3. Pick hook types (vary the type, not the words)

Use at least 4 different types per batch. The full bank with 60+ lines is in [references/hook-bank.md](references/hook-bank.md).

| Type | Template | Best stage |
|---|---|---|
| Callout / yes-question | "If you're over 50 and your knees crack…" / "Does your foundation slide off by 2 pm?" | Problem-aware |
| Payoff first | Open on the result (clean oven, clear skin, organised drawer) | Any |
| Problem and fix in one shot | The phone case shatters… then the same case saves the phone | Any (top TikTok Shop) |
| Late discovery | "Been shopping here for 7 years and I'm JUST finding this???" | Unaware |
| Compliment → reveal | "You look happier." / "Thanks, I found…" | Unaware |
| Gratitude | "I'll never forget the girl who told me the secret to…" | Unaware |
| Confession | "I was a hater of this. I was wrong." | Product-aware |
| Negative / warning | "Stop buying cheap phone cases until you see this." | Solution-aware |
| Exposing / testing | "Seeing if this $19 pan is actually worth it" | Solution-aware |
| Hidden culprit | "This is the real reason your skin sags after 50" | Unaware |
| Price anchor | "The big brand is $599. This is $49." (substantiate) | Solution-aware |
| Newness / restock | "It's finally back." | Most-aware (top Motion hit rate) |
| Reply to a comment | Video reply to "does it actually work on thick hair?" | Product-aware |
| Satisfying intro | Lid snap, foil peel, pour — sound on | Any |
| Destroy / stress test | Drop it, burn it, freeze it in ice and smash it | Any |
| Absurd alternative | The product used for something absurd | Unaware |
| Skeptical voice | "There's no way this works." | Product-aware |
| Street question | "What are you getting her for Christmas?" | Gifting season |

Motion's 2026 hit-rate order on Meta (578,750 creatives; includes Black Friday, so promo hooks are inflated): newness, sale announcement, price anchor, urgency, announcement, offer only, FOMO, new product, confession, exclusivity, curiosity.

## 4. Check every hook

- [ ] The product or the result is visible by second 2
- [ ] It leads into the product; no unrelated stunt
- [ ] Visual, spoken and text layers agree; text ≤8 words, inside the safe zone (out of the top 14%, bottom 35%, sides 6%)
- [ ] No claim you can't prove; no price unless it matches the live product page (TikTok Shop violations); no before/after that overstates results; no "Do you have [condition]?" on Meta (personal-attribute rule)
- [ ] Not a first-person result line for an AI person
- [ ] Different first frames across the batch (Meta groups ads with the same opening)

## 5. Make the hook clips (optional, costs credits)

For a hook that remakes an idea already viral for this kind of product (backyard-camera fail, torture test, gift reaction) as realistic phone footage, use `varg-product-hook`. Otherwise:


1. Quote first with `estimate_cost` and wait for a yes.
2. First frame: a still from the real product photo (`nano_banana_2_1`) or a frame of real footage.
3. Animate 3 s: `kling_v4_flash` for drafts, `kling_v4` or `seedance_2_5` for finals, the product photo as a reference on every clip. Keep the same character reference and scene baseline as the body, or the seam shows.
4. Voice the line (`eleven_v4`) or record it. Not for TikTok Shop presenters (AI voices banned there).
5. Join each hook to the body: `ecommerce-video-edit` §6 (`scripts/hook-variants.sh`), one MP4 per hook, named `<product>_<angle>_h<NN>-<type>_v1.mp4`.

## 6. When to make new hooks

- New hooks go on a **winning** body. A new concept comes first, hook swaps second: ten hook swaps of one video read as one ad to Meta.
- One winning body + 5 new openers: "one of those five will almost always outspend the others 30 to 1" (operator report).
- Cut the hook out of any reel that clears a 50% hook rate and keep it in a hook bank with its numbers.

## Related

`ecommerce-video-ads` (the whole plan) · `varg-product-hook` (viral-style hook clip from product photos) · `ad-creative-testing` (how many, when to kill) · `ecommerce-video-edit` (join hooks to a body) · `tiktok-shop-video`
