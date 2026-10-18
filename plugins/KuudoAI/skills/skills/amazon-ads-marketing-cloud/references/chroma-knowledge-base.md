# Chroma `amazon_ads` Collection — Retrieval Guide

This reference describes the structure and contents of the `amazon_ads` Chroma collection that the `amc` skill consults via the `chroma_mcp` server. Use it to write higher-quality queries and to choose between semantic search and metadata-driven retrieval.

> **Connection details (URL/port/auth) live in the client's MCP configuration, not in this skill.** Use the knowledge tools and schemas the client exposes for the active deployment.

## Collection at a glance

| Field | Value |
|---|---|
| Collection name | `amazon_ads` |
| Approximate size | ~1,900 chunks across ~54 documents |
| Embedding model | `all-MiniLM-L6-v2` (cosine distance) |
| Distance metric | Cosine — **lower is better** |
| Domain | Amazon Marketing Cloud — playbooks, references, schemas, analyses |

Use `chroma_get_collection_info` if you need to confirm the count and embedding model in your environment, since the collection may be re-indexed.

## Two retrieval modes

The collection supports two complementary access patterns. Choose based on what you know.

### Mode A: Semantic search (`chroma_query_documents`)

Use when you don't know which document you want. The query is embedded and matched against chunk embeddings.

```
chroma_mcp:chroma_query_documents
  collection_name: "amazon_ads"
  query_texts: ["your natural-language query"]
  n_results: 5
```

**Response shape.** The server wraps results under `data` and metadata under `meta`:

```json
{
  "data": {
    "ids":       [["..."]],
    "documents": [["..."]],
    "metadatas": [[{...}]],
    "distances": [[0.5295, ...]],
    "included":  ["documents", "metadatas", "distances"]
  },
  "meta": {"collection": "amazon_ads", "query": ["..."], "n_results": 5}
}
```

Defensive unwrap (survives envelope changes):

```python
payload = res.get("data", res)
docs   = payload["documents"][0]     # outer list is per-query; index 0 for one query
metas  = payload["metadatas"][0]
dists  = payload["distances"][0]
```

Walking `res["documents"]` directly returns empty. **Always check `distances`** before trusting results — see "Distance interpretation" below.

### Mode B: Metadata-driven retrieval (`chroma_get_documents`)

Use when you know the document, doc type, or want to walk a playbook in order. Filters by metadata, no embeddings involved — exact and deterministic.

```
chroma_mcp:chroma_get_documents
  collection_name: "amazon_ads"
  where: {"semantic_id": "off-amazon-conversions"}
  limit: 200
```

Same `{"data": ..., "meta": ...}` response envelope as Mode A. Walk `res["data"]["documents"]` (one-level list — no per-query nesting since there's no query to nest by).

**Why this matters:** playbooks are split across many chunks (the largest doc has 220 chunks). Semantic search returns 5–10 chunks at a time and may miss the section you need. Metadata retrieval pulls the entire document deterministically.

**Useful filter keys** (all available on every chunk):

| Key | Example values | Use for |
|---|---|---|
| `semantic_id` | `off-amazon-conversions`, `custom-attribution-overview` | Pull a specific known doc |
| `source_ref` | (8-char hash) | Pull all chunks from one source file (alternative to `semantic_id`) |
| `doc_type` | `howto`, `analysis`, `reference`, `schema` | Filter to playbooks vs. table refs vs. analyses |
| `dataset` | `sponsored_ads_traffic`, `dsp_impressions`, `conversions_with_relevance` | Find docs about a specific table |
| `code_languages` | `sql` | Only chunks containing SQL |
| `chunk_index`, `chunk_total` | `0`, `32` | Walk a doc in order |
| `previous_chunk_id`, `next_chunk_id` | (chunk hash) | Follow chunk-to-chunk links |
| `version`, `status` | `2023-10-20`, `current` | Avoid stale content |

**Composite filters** (Chroma uses MongoDB-style operators):

```
where: {"$and": [
  {"doc_type": "howto"},
  {"dataset": "amazon_attributed_events_by_traffic_time"}
]}
```

### Recommended workflow: hybrid

1. **Discover** with semantic search at `n_results: 5`
2. **Inspect distances** — reject anything > 0.85 unless you're confident
3. **Identify** the `semantic_id` of the best hit
4. **Walk the doc** with `chroma_get_documents` filtered on that `semantic_id` (or `source_ref`) to get the full playbook in order

This is far more reliable than running 5–10 semantic queries hoping to assemble the same content.

## Distance interpretation

Empirical baselines measured against the actual collection with `all-MiniLM-L6-v2`:

| Distance | Quality | Action |
|---|---|---|
| **< 0.65** | Strong match | Use confidently |
| **0.65 – 0.80** | Decent match | Read the chunk before relying on it |
| **0.80 – 0.90** | Weak | Likely related but probably not the target doc — try a metadata filter or a rephrased query |
| **> 0.90** | Noise | Discard. Do not present to the user as evidence |

**Theory of mind:** Don't blindly use top-N results. A query with all five hits at distances 0.85+ means the collection probably doesn't have what you're looking for in that phrasing — change the query, switch to metadata mode, or fall back to `tool-gotchas.md` and the AMC SQL essentials in `SKILL.md`.

## Document catalog

The collection holds approximately 54 distinct documents. Below is the catalog discovered through systematic probing, sorted by chunk count (largest documents first). Use these `semantic_id` values directly with `chroma_get_documents` or as anchors for semantic queries.

### References (table schemas, data sources, SQL reference)

| `semantic_id` | Chunks | Title |
|---|---|---|
| `amazon-attributed-events` | 220 | Amazon Attributed Events Overview |
| `custom-attribution-overview` | 83 | Custom Attribution Overview |
| `introduction-to-amc-sql` | 62 | Introduction to AMC SQL |
| `amazon-sponsored-ads-traffic` | 40 | Amazon Sponsored Ads Traffic Overview |
| `audience-segment-insights` | 20 | Introduction to Audience Segment Insights |
| `amazon-dsp-clicks-table` | 17 | Amazon DSP Clicks Table |
| `amazon-dsp-impressions-table` | 13 | Amazon DSP Impressions Table |
| `introduction-to-events-manager` | 11 | Introduction to Events Manager |
| `paid-features-overview` | 9 | Overview of AMC Paid Features |
| `amazon-marketing-cloud-data-sources` | 8 | Amazon Marketing Cloud Data Sources |
| `amazon-ads-conversions-relevance` | 6 | Amazon Ads Conversions with Relevance |
| `data-aggregation-thresholds-amc` | 6 | Data Aggregation Thresholds in AMC |
| `amc-sql-reference` | 5 | AMC SQL Reference |
| `amazon-dsp-video-events` | 3 | Amazon DSP Video Events Table |
| `amazon-your-garage-tables` | 2 | Amazon Your Garage Tables |
| `amazon-dsp-impressions` | 1 | Amazon DSP by Matched and User Impressions Tables |

### Playbooks and how-tos

| `semantic_id` | Chunks | Title |
|---|---|---|
| `off-amazon-conversions` | 51 | Off-Amazon Conversions Playbook |
| `programmatic-audience-framework` | 39 | Programmatic Audience Framework Playbook |
| `customer-long-term-value-cltv` | 39 | Understanding Customer Long-Term Value (CLTV) |
| `amc-lookalike-audiences-promotional-events` | 37 | AMC Lookalike Audiences for Promotional Events |
| `keyword-clustering` | 37 | Keyword Clustering for Amazon Advertising Optimization |
| `filter-by-ad-product-type` | 34 | How to Filter by Ad Product Type |
| `enhanced-scoring-overlapping-amc-audiences` | 27 | Enhanced Scoring for Overlapping AMC Audiences |
| `optimal-frequency-deep-dive` | 22 | Optimal Frequency Deep Dive (On- and Off-Amazon Conversions) |
| `instructional-query-revision-custom-attribution-position-based` | 21 | Custom Attribution: Position Based Model |
| `query-digital-subscriptions` | 21 | Query Digital Subscriptions Purchases and Downloads |
| `optimize-amc-sql-queries` | 21 | How to Optimize AMC SQL Queries |
| `custom-attribution-last-touch` | 20 | Custom Attribution: Last Touch |
| `custom-attribution-linear` | 20 | Custom Attribution: Linear Model |
| `amazon-brand-store-insights-amc` | 20 | Amazon Brand Store Insights in AMC |
| `custom-attribution-first-touch` | 19 | Custom Attribution: First Touch |
| `introduction-to-amc-sandbox` | 18 | Introduction to AMC Sandbox |
| `automotive-insights-amazon-your-garage` | 16 | Automotive Insights with Amazon Your Garage |
| `introduction-to-digital-out-of-home-ads` | 13 | Introduction to Digital Out-of-Home Ads |
| `sponsored-products-dsp-display-overlap` | 11 | Sponsored Products and DSP Display Overlap Analysis |
| `reach-penetration-target-audience` | 10 | Reach Penetration Within Target Audience |
| `audience-ready-upgrade` | 10 | Audience Query for Identifying Upgrade Opportunities |
| `sponsored-brands-traffic-conversions` | 10 | How to Query Sponsored Brands Traffic and Conversions |
| `sponsored-tv-incremental-reach` | 9 | Sponsored TV Incremental Reach Sales and Conversion |
| `compare-first-party-unknown-customer-performance` | 9 | Comparing First-Party and Unknown Customer Performance |
| `sponsored-display-dsp-overlap` | 9 | Analyzing the Impact of Sponsored Display and DSP Advertising |
| `incremental-reach-timing-exposures` | 8 | Incremental Reach and Timing of Exposures |
| `introduction-to-amc-lookalike-audiences` | 7 | Introduction to AMC Lookalike Audiences |
| `new-to-brand-purchases` | 7 | New-to-Brand Purchases Analysis |
| `join-union-sponsored-ads-traffic-conversions` | 7 | Joining and Unioning Sponsored Ads Traffic with Conversions |
| `introduction-to-prime-video-ads` | 6 | Introduction to Prime Video Ads |
| `how-to-use-template-analytics` | 5 | How to Use Template Analytics |
| `filter-text-strings` | 3 | How to Filter Text Strings |

### Analyses

| `semantic_id` | Chunks | Title |
|---|---|---|
| `optimal-frequency-analysis` | 32 | Optimal Frequency Analysis in Amazon Marketing Cloud |
| `amazon-dsp-display-streaming-tv-sponsored-products-overlap` | 15 | DSP Display, Streaming TV, and Sponsored Products Overlap |
| `campaign-performance-user-funnel-stages` | 15 | Campaign Performance by User Funnel Stages |
| `overlap-by-campaign-groups` | 11 | Overlap by Campaign Groups |
| `audience-overlap-analysis` | 7 | Audience Overlap Analysis |
| `high-value-customer-segments` | 7 | Identifying High Value Customer Segments |
| `analyze-sponsored-products-brands-bid-boost-performance` | 6 | Analyze Sponsored Products and Sponsored Brands Bid Boost Performance |
| `creative-asin-impact-analysis` | 5 | Creative ASIN Impact Analysis |

> **Note:** Catalog reflects a snapshot taken via systematic probing. The collection may be re-indexed. Use `chroma_get_collection_info` for current totals and `chroma_get_documents` with metadata filters to enumerate live content.

## Validated query phrasings

The following queries were measured against the live collection. They are good *starting points* — adjust for the user's specific question.

| Goal | Query phrasing | Best distance |
|---|---|---|
| Filter by ad product type | `"ad types placements not supported AMC LIMIT"` | 0.535 |
| Events Manager / off-Amazon setup | `"amazon_attributed_events_by_traffic_time table schema"` | 0.507 |
| Enhanced scoring / persona overlap | `"enhanced scoring overlapping audiences persona"` | 0.569 |
| Conversions with relevance | `"conversions_with_relevance attribution data source"` | 0.621 |
| CLTV / rule-based audiences | `"rule-based audience for_audiences user_id"` | 0.608 |
| Sponsored TV incremental reach | `"Sponsored TV incremental reach sales"` | 0.664 |
| Automotive / Your Garage | `"automotive insights Amazon Your Garage"` | 0.651 |
| Keyword clustering | `"keyword clustering campaign optimization"` | 0.644 |
| AMC sandbox | `"sponsored_ads_traffic table columns"` (cross-matches sandbox + traffic ref) | 0.596 |
| Optimal frequency by ad format | `"optimal frequency analysis ad format"` | 0.703 |
| Template analytics (no-SQL) | `"template analytics no-SQL audiences"` | 0.684 |
| Audience Segment Insights | `"audience segment insights in-market lifestyle"` | 0.716 |
| Lookalike for promo events | `"lookalike audience seed promotional event"` | 0.748 |
| AMC SQL optimization | `"optimize AMC SQL queries execution order CTE"` | 0.742 |

**Queries that scored poorly** in testing — avoid or reach for metadata mode instead:

| Goal | Bad query | Distance | Better approach |
|---|---|---|---|
| Position-based attribution | `"position-based attribution model"` | 0.879 | Use `where: {"semantic_id": "instructional-query-revision-custom-attribution-position-based"}` |
| Programmatic audience framework | `"campaign performance reach unique users"` | 0.841 | Use `where: {"semantic_id": "programmatic-audience-framework"}` or query `"programmatic audience framework DSP"` |
| First-party vs unknown customers | `"first-party customer compare unknown performance"` | 0.929 (noise) | Use `where: {"semantic_id": "compare-first-party-unknown-customer-performance"}` |

## Doc type taxonomy

The four `doc_type` values map to clearly different content shapes:

- **`reference`** — Table schemas, column lists, data source overviews, the AMC SQL dialect doc. Use for "what columns does X have" / "what are the AMC functions" questions.
- **`howto`** — Step-by-step playbooks and instructional queries. Use for "how do I measure Y" / "walk me through Z" questions.
- **`analysis`** — Analytical templates with prescribed metrics and interpretation. Use for "what's the right way to look at A" questions.
- **`schema`** — Pure schema/DDL chunks (rare; only `amazon-your-garage-tables` at the time of this writing).

Filter on `doc_type` whenever you can to cut noise — e.g., for a table-schema question, `where: {"doc_type": "reference"}` will keep playbook chunks out of the results.
