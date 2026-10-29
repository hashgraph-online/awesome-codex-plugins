---
name: ad-creative-testing
description: >-
  Turn one winning ad into a creative testing plan for TikTok and Meta. Decodes why an ad won
  (hook, argument, buyer, format), plans concepts that Meta's Andromeda and TikTok treat as
  genuinely different (buyer × angle × format × first frame, not caption swaps), sets how many
  creatives to launch, the budget per test and when to judge, writes file and ad names that make
  results readable, reads hook rate, hold rate, CTR and CPA to find which part failed, and says
  when to kill, iterate or scale. Use when someone asks how many ads to test, how to make ad
  variants, why their variants all perform the same, whether an ad is fatigued, when to kill an
  ad, or how to scale a winner. NOT for producing the videos (use ecommerce-video-ads,
  ecommerce-video-edit or product-video-hooks) or for media-buying account setup.
license: MIT
metadata:
  author: vargHQ
  version: "1.0.0"
  varg.cost.typical: "free (planning); production costs come from the skills it hands off to"
  varg.runtime.typical: "10–30 min"
  varg.outputs: "test plan (markdown table), naming sheet (csv)"
  openclaw:
    homepage: https://varg.ai
compatibility: >-
  Planning only; needs nothing. Reads exported ad metrics (CSV) when the person shares them.
allowed-tools: Read Write Edit
---

# Turn one winning ad into a creative testing plan

Winners are rare. In Motion's 2026 benchmark (578,750 Meta creatives, $1.29B spend), only 5–8% of ads became winners (spend ≥10× the account median and ≥$500). One agency's 1,780 AI creatives produced 8 that crossed $100K in spend (self-reported). The plan exists to find the rare winner cheaply, then milk it.

## 1. The rule that changed: similar ads count as one

Meta groups ads that look or feel alike as variations of one creative and says iteration "should not replace true creative diversification" ([Meta](https://www.facebook.com/business/news/demystifying-creative-diversification)). Agencies report that the same opening or the same look ranks as the same ad, and that 30 face and setting swaps of one winner made CPA triple. TikTok asks for 3–5 *very different* creatives per ad group and at least 12 new videos a month on Smart+ and GMV Max.

**So a variant is a new concept**: a different buyer, angle, format or first frame. A new caption, colour or voice on the same video is not a variant.

## 2. Decode before you multiply

For the current winner (or the competitor ad that has run 30+ days), write down:

| Part | Question | Example |
|---|---|---|
| Hook | Pain callout, result shown, or visual interrupt? | Result shown: a clean oven at 0:00 |
| Argument | Why buy: speed, price, proof, transformation, comparison? | Speed: "60 seconds" |
| Buyer | Who actually bought (not the targeting)? | Renters, 25–35 |
| Format | Unboxing, demo, yapper, us vs them…? | Hands-on demo |

## 3. The test map: change one thing, read one thing

| Test | Keep | Change | If it wins |
|---|---|---|---|
| New hook | Argument, format, body | First 3 s (new frame, line, text) | The opener was the weak spot: make 5 more |
| New format | Argument | Demo → before/after → founder → podcast | Push the message into every format |
| New face / setting | Script | Creator, room (AI swaps OK here) | You extended the winner's life |
| New argument | Product | "Recommended by…", "30 days later…" | Start a new decode |
| New buyer | Product, format | Persona, age, room, problem | New audience pocket |

## 4. How many, how much, how long

**No winner yet (explore):**
- 8–15 concepts per batch across 3+ angles, every awareness stage live (offer, objections/reviews, us vs them, problem → fix, big win). At least 2 statics (Notes app, review card, us vs them) per batch: the cheapest angle test.
- Draft cheap (stills + voice, a fast video model), produce fully only what passes review.
- TikTok: 3–5 creatives per ad group, new creatives into the *existing* ad group. Meta: one ad set with many ads is normal under Andromeda (Advantage+ Sales allows 50); Meta's Creative Testing tool takes 2–5 ads at ≤20% of budget for 7 days.
- Run an angle in at least 3 executions (demo, founder or talking head, raw UGC) before calling it dead.

**A winner exists (exploit):** all-in on that angle. 3–5 new openers on its body, then 10 new executions of the concept + angle + persona. Operators report one of five new openers "will almost always outspend the others 30 to 1".

**Cadence:** about 2 concepts a week with 2 spoken-hook and 2 visual-hook versions each for brands under $100K/month (Savannah Sanchez); 15–21 high-intent ads a week at large scale (operator reports).

**When to judge:** not in the first 48 hours. Give each creative about 1–3× target CPA in spend (or ~5–10 conversions) before deciding. TikTok GMV Max: keep each ROI setting at least 3 full days.

## 5. Read the funnel to find the broken part

| Symptom | Broken part | Fix |
|---|---|---|
| Low hook rate (3 s views ÷ impressions; Meta average 25.44% in H1 2026) | The first frame didn't earn the stop | New visual hook (`product-video-hooks`) |
| High hook rate, low hold (watched to 25%/50%) | Story tension lost after the hook | Tighter body, product earlier, cut dead air |
| High hold, low CTR | No commercial reason to click | Clearer offer, CTA said and shown |
| High CTR, low conversion | The landing page broke the promise | Fix the page, not the ad (one brand cut CAC from $140 to under $80 with the same ads by raising CVR 1% → 3%) |
| Views but no sales (organic) | Wrong audience or no buying intent | Judge by orders per 1,000 views; comments like "where do I buy?" are the signal |

Operator bands (not platform numbers): hook rate under 25% weak, 30–40% OK, 40%+ strong; hold under 15% weak, 35%+ strong; CTR under 1% weak, 3%+ strong. Always check CPA or ROAS before killing on hook rate alone.

## 6. Kill, keep, scale

- **Kill:** spent 1–3× target CPA with CPA well above target, and the funnel row above has no cheap fix.
- **Fatigue:** two signals at once — CPM up 20% week over week, CTR down 15–20%, frequency over ~3, CPA up with nothing else changed. Fix: new hook on the body first, then a new face, then a new angle. Keep ~10 approved backups to rotate.
- **Check the cause first:** a budget change or a new audience can look like fatigue. Last season's winners can work again (one Black Friday ad "printed again" a year later).
- **Leave the highest-volume ad on** even when its CPA looks high: it probably does more than the dashboard credits it with.

## 7. Names that make results readable

```
{date}_{product}_{persona}_{angle}_{format}_{hook-id}_{creator}_{len}s_{cta}_v{N}
2026-10-27_serum_busy-mom_problem-fix_ugc-car_H07-confession_ava_28s_shopnow_v1
```

Keep a **hook bank** (every tested hook with its hook rate) and a **concept log** (persona, angle, format, result). Tag every ad by angle (PAIN / PROOF / CONTRAST / AUTHORITY…) so spend can be read per angle.

## Output

Deliver a table: concept, buyer, angle, format, first frame, hook line, skill that makes it, draft cost (from `estimate_cost`), budget, judge-after (CPA × N), file name. Then hand each row to the production skill.

## Related

`ecommerce-video-ads` · `product-video-hooks` · `ecommerce-video-edit` (one MP4 per hook) · `make-video-ad-variants-for-testing` on varg how to

Sources: [Motion 2026 benchmarks](https://runneth.com/library/research/creative-benchmarks-2026/top-visual-formats), [TikTok creative best practices](https://ads.tiktok.com/help/article/creative-best-practices?lang=en), [TikTok GMV Max](https://ads.tiktok.com/help/article/best-practices-for-product-gmv-max?lang=en), [Jon Loomer on Creative Testing](https://www.jonloomer.com/meta-creative-testing/), [Savannah Sanchez](https://runneth.com/library/talk/15-proven-ugc-ad-hooks-that-are-working-right-now-savannah-sanchez/), [Billo hook rates](https://billo.app/creative-insider/data-insights/hook-rate-benchmarks-h1-2026/), operator posts on X (see `ecommerce-video-ads/references/sources.md`).
