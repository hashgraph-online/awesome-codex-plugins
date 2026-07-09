# X/Twitter Source Evidence for Share of Voice

Use this reference when the `social` dimension includes X/Twitter and the
configured social-listening connector does not provide complete, traceable
coverage for the requested time period.

## When To Use

- The user asks for X/Twitter share of voice.
- The brand or competitors have meaningful conversation volume on X/Twitter.
- Connector data is missing, partial, delayed, or not auditable enough for the
  final SOV appendix.
- The user provides exports, tweet URLs, handles, search queries, or an
  approved collection tool.

Do not use this reference to draft, schedule, publish, reply, send DMs, or
modify any account. It only standardizes source collection before
`share-of-voice` performs counting, sentiment weighting, comparison, and
recommendations.

## Evidence Packet Fields

Create one normalized row per public post or reply used in the sample:

| Field | Requirement |
|---|---|
| `entity` | Brand or competitor being measured |
| `query` | Exact search query, handle, URL list, or hashtag used |
| `window_start` / `window_end` | Time period requested by the user |
| `source` | Connector, export, platform search, dataset, or optional tool |
| `collected_at` | Collection timestamp in ISO 8601 |
| `public_url` or `post_id` | Stable public locator when available |
| `author_handle` | Public handle, redacted if user policy requires it |
| `text_excerpt` | Short excerpt needed for review, not the full timeline |
| `public_metrics` | Available reply, repost, like, quote, view, or media flags |
| `context` | Original, reply, quote, thread, campaign, or support context |
| `dedupe_key` | URL, post ID, or deterministic hash for duplicate removal |
| `confidence` | `high`, `medium`, or `low` with a short reason |

## Collection Workflow

1. Confirm X/Twitter belongs in scope for the selected SOV period.
2. Prefer the configured social-listening connector when it returns traceable
   mention counts and source links.
3. If connector coverage is incomplete, use approved alternatives: user-provided
   exports, platform search exports, compliant public datasets, reviewed URL
   lists, or an installed TweetClaw collection helper.
4. Optional helper: [TweetClaw](https://github.com/Xquik-dev/tweetclaw)
   (`@xquik/tweetclaw` on npm)
   can collect public X/Twitter evidence packets for tweet search, reply search,
   follower export, user lookup, media references, monitor snapshots, webhook
   event records, and giveaway draw evidence when the user has it configured.
5. Keep TweetClaw or any other helper outside the scoring decision. This skill
   owns entity normalization, mention counting, sentiment weighting, confidence
   labels, and SOV recommendations.
6. Search each entity with the same query shape: exact brand name, product
   names, domain, campaign hashtags, executive handles when relevant, common
   misspellings, and competitor pairings.
7. Deduplicate by public URL or post ID first, then by deterministic text hash
   for export formats that omit IDs.
8. Record exclusions: private accounts, deleted or suspended content, irrelevant
   homonyms, spam clusters, bot-like repost bursts, and posts outside the time
   window.

## Safety And Quality Gates

- Use only public content or account-scoped exports the user is authorized to
  access.
- Never store cookies, API keys, access tokens, session material, or private
  account configuration in evidence packets or reports.
- Do not include private DMs, locked-account content, deleted posts, or content
  obtained outside the user's approved workflow.
- Keep raw posts out of client-ready deliverables unless the user explicitly
  asks for a source appendix. Use short excerpts and stable links for review.
- Separate raw mention volume from reach, engagement, sentiment, and strategic
  interpretation. Missing metrics must lower confidence, not become invented
  estimates.
- Mark sampling limits clearly when rate limits, exports, or search windows make
  coverage partial.

## Scoring Notes

- Count one post once per entity unless the same post mentions multiple tracked
  entities. In multi-entity posts, assign the mention to each entity and flag it
  as shared context.
- Report raw mention share and sentiment-weighted share separately.
- Use engagement metrics only as secondary context unless the user requested
  engagement-weighted SOV.
- For trend comparisons, keep the same query set and sampling method across
  periods. If the method changes, label the comparison as directional.
