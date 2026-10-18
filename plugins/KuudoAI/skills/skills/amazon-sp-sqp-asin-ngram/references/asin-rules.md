# ASIN-level IF → THEN rules (SQP / organic)

Apply after minimum thresholds (e.g. `total_impressions ≥ 200`, `asin_clicks ≥ 20`) or shrinkage for strong claims. Include attribution scope in badges. Cooldown 7–14 days per `{search_query, asin}` unless metrics move opposite intent.

Every THEN is a recommendation record, not a change this skill makes. The skill that owns the action previews it and waits for the user's yes (see SKILL.md, Guardrails).

| Observation (IF) | Action (THEN) | Goal |
|---|---|---|
| High query volume but `asin_impression_share < peer_p25` | `seo_update` + `pdp_update` toward dominant n-gram intent; re-check in 7d | Lift visibility |
| `asin_click_share > asin_impression_share` **AND** `asin_purchase_share ≤ asin_impression_share` | `pdp_update` (price vs median, ratings, delivery speed) | Reduce conversion friction |
| `CTR` below query benchmark while `asin_impression_share ≥ peer_p50` | `pdp_update` + hero imagery/title alignment | Raise CTR |
| `asin_purchase_share` trails `asin_click_share` by >30% and slow shipping share high | `shipping_speed_fix` + surface delivery promise; consider coupon/deal badge | Remove delivery friction |
| Price above market median and purchase share < peer_p25 | `price_test` (bounded, 7d) and re-evaluate share deltas | Win purchases efficiently |
| Underperforms vs brand peers on same query | `variant_mapping_fix` or re-balance on-page emphasis | Reduce cannibalization |

Cross-reference **conversion index** and **share funnel gaps** from `ngram-keyword-framework` / `references/rulebook-organic-sqp.md` when summarizing “why” for a row.
