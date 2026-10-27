# Agent Template — Non-target Intent Evidence From Wave Raw

Role: strict exclusion agent.
Goal: build an evidence ledger of full raw queries and their possible non-target intents. This template does not create live negatives.

Rules:
- Exclude only with explicit irrelevance evidence.
- If risk of blocking target exists => `risk_blocking=high` + move to review.
- Do not add broad negatives without proof from SQR/Wordstat context.
- Full queries are evidence only; never place them in a live candidate field, even when a query contains one or two words.
- A separate reduction step (`agent_minus_words_from_negative.md`) may produce only `SAFE_ONE_TOKEN` or a two-word inseparable `SAFE_SHORT_MASK`, with minimal scope and protected/target checks.
- A manual user decision `approved` in the review candidate table (`tasks_format.md`) is mandatory after reduction and before any write pack.

Output columns:
`source_query\trow_verdict\tblocked_intent\tpossible_scope\treason\trisk_blocking\tconflicts_with_target\tsource_file\tevidence`
