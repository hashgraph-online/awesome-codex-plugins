# Opportunity score and report QA

## Stop-word and token hygiene

Maintain a configurable stop list; demote low-signal tokens that can still matter inside multi-grams.

```yaml
ngram_hygiene:
  stopwords: [for, with, of, the, a, an, holder, set]
  demote_if_in_multigram: true
  min_token_entropy: 1.2
  normalize: {lower: true, strip_punct: true, collapse_ws: true}
```

## Lift-aware opportunity score (RankScore)

Replace pure volume ranking with a composite reflecting upside.

**Inputs per `{query, asin}`**

- `V` = normalized query volume (0..1)
- `IS_gap` = max(0, peer_median_impression_share - asin_impression_share)
- `CS_gap` = max(0, peer_median_click_share - asin_click_share)
- `PS_gap` = max(0, peer_median_purchase_share - asin_purchase_share)
- `Price_gap` = (asin_median_price - market_median_price) / market_median_price
- `Ship_friction` = weighted share of two_day (and slower) vs same/one_day

**Compute**

```
Conversion_gap = max(0, click_share - purchase_share)
RankScore = wV*V + wIS*IS_gap + wCS*CS_gap + wPS*PS_gap + wConv*Conversion_gap
            + wShip*Ship_friction + wPrice*max(0, Price_gap)
```

**Default weights**

`wV=0.15, wIS=0.15, wCS=0.15, wPS=0.25, wConv=0.15, wShip=0.10, wPrice=0.05`

## Guardrail badges (per finding)

```json
{
  "badges": {
    "data_sufficient": true,
    "peer_benchmarks": ["P25", "P50"],
    "attribution_scope": "SQP search-page (short window)",
    "cooldown_ok": true,
    "thin_data_reason": null
  }
}
```

## Action scope tags

- `[ORGANIC]` — PDP, images, title, bullets, variant
- `[OPS]` — shipping speed, fulfillment/badges, inventory
- `[ADS]` — sponsored tactics, budget/bids/placement
