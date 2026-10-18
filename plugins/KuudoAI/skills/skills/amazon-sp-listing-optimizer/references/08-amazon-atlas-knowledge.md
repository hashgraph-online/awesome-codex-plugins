# amazon_atlas — Amazon knowledge base (Chroma)

`amazon_atlas` is a **Chroma vector database** (ChromaDB MCP server) of prebuilt,
indexed Amazon knowledge packages. The skill consults it to **ground and refine**
listing decisions in authoritative Amazon documentation — Seller Central
guidelines, per-category style guides, business rules, and A+ Content guidance —
instead of relying only on this skill's own reference files.

It is a **refinement layer, not a hard dependency.** When it's unavailable, the
skill falls back to `01-policy-rules.md` and the other bundled references. The skill
**reads** from amazon_atlas; the packages are built and maintained externally, so
don't write to them from listing work.

Load this doc when you need the collection map, the metadata schema for `where`
filters, or query patterns. Use the knowledge server and tool schemas exposed
by the client for the active deployment.

## Connecting and discovering

`amazon_atlas` uses a **meta-tool surface** like a code-mode SP-API server:

- `amazon_atlas:search` — find concrete tools by query.
- `amazon_atlas:get_schema` — get exact parameters before calling.
- `amazon_atlas:tags` — browse tool groups.
- `amazon_atlas:execute` — run a small Python block chaining `call_tool(name, args)` calls (handy to query several collections and trim results in one round trip).

The concrete document tools you'll use most:

- `chroma_list_collections` — list collection names (always confirm the live set; deployments vary).
- `chroma_get_collection_info` — name, document count, package metadata.
- `chroma_query_documents` — semantic search (the primary access pattern).
- `chroma_get_documents` — fetch by id or metadata filter. Note: an *unfiltered* get returns an arbitrary first-N (content-hash ordered), not a representative sample — use a query for exploration.

Never guess tool or argument names — confirm with `get_schema`.

## Collections

Validated on the reference instance (counts will drift):

| Collection | Count | Contents | Use for |
|---|---|---|---|
| `amazon_sellers` | ~4,750 | Seller Central docs + per-category style guides | Authoritative listing requirements (`doc_type: reference`, e.g. "Product Bullet Points Requirements") and category title/bullet/image conventions (`doc_type: style_guide`, `dataset: listing_categories_style_guide`). **Primary source.** |
| `amazon_rules` | ~140 | Amazon business rules & decision frameworks (also carries category style guides) | Grounding an ambiguous decision in an authoritative rule. |
| `amazon_vendors` | ~670 | Vendor Central + A+ Content management | A+ Content and Brand-side guidance — consult before A+ work. |
| `amazon_ads` | — | Advertising | Not relevant to listing optimization. |

## Metadata schema (for `where` filters)

Chroma `where` matches metadata **exactly**. Observed fields on documents:

| Field | Example values | Notes |
|---|---|---|
| `doc_type` | `style_guide`, `reference`, `guide`, `how_to` | Most useful filter. |
| `topic` | `listing`, `home_kitchen`, `fashion`, `baby_products`, `office_products`, `sports_outdoors`, `a_plus_content`, `brand` | Category / subject. |
| `dataset` | `listing_categories_style_guide`, `""` | Set on the category style guides. |
| `tags` | `"amazon, listing-optimization, style-guide, baby, safety"` | Comma-joined **string**, not an array — no array-contains; rely on `query_texts` for tag-like matching. |
| `title` | `"Product Bullet Points Requirements"` | Human title. |
| `section_path` | `"Baby Products Category Style Guide > Title formulas"` | Breadcrumb within the source. |
| `status` | `current` | Filter to current if you want only live guidance. |
| `domain` | `amazon` | — |

Chunks also carry plumbing fields (`chunk_index`, `next_chunk_id`, `content_hash`,
`source_ref`, `token_estimate`, …) — ignore them for retrieval. Because `id_scheme`
is content-based, identical content in two collections shares an id.

## Query patterns

### Category style for drafting/auditing copy

```python
chroma_query_documents(
    collection_name="amazon_sellers",
    query_texts=["title formula and bullet pattern for aprons"],
    where={"$and": [{"doc_type": "style_guide"}, {"topic": "home_kitchen"}]},
    n_results=3,
)
```

### Authoritative requirement (let semantics surface the `reference` doc)

```python
chroma_query_documents(
    collection_name="amazon_sellers",
    query_texts=["bullet point character limits and prohibited content"],
    n_results=3,
)
```

### A+ Content guidance

```python
chroma_query_documents(
    collection_name="amazon_vendors",
    query_texts=["A+ content module guidelines and rejection reasons"],
    where={"topic": "a_plus_content"},
    n_results=3,
)
```

### Several collections in one round trip

Use `amazon_atlas:execute` with a Python block that calls `chroma_query_documents`
for each collection and returns trimmed rows (title + short preview), to avoid
pulling large payloads into context.

## When to query

- Drafting or rewriting a title, bullet, or description for a specific
  product.
- Auditing image or copy compliance for a category-specific listing.
- Grounding an ambiguous decision in an authoritative rule (`amazon_rules`).
- Before A+ work, for current A+ guidance (`amazon_vendors`).
- The product is in a category not covered earlier in the conversation.

**Don't query** for universal length limits, prohibited content,
suppression triggers, or brand-name policy (`01-policy-rules.md` has them),
or for patch mechanics (`06-patch-construction.md`).

## When it's unavailable or returns nothing useful

1. Apply the general rules in `01-policy-rules.md`.
2. Say so plainly: "I don't have category-specific guidance for X; want me
   to draft from general principles, or do you have a reference to share?"
3. **Don't fabricate category rules.** A hallucinated category rule does
   more damage than none.

## Cross-category products

Some products straddle two categories: aprons (Home & Kitchen, worn like
apparel), branded kitchen towels, branded reusable bags, pet apparel.

- The catalog `classifications` path is where Amazon shelves the product.
  Start there.
- Run **two queries**, one per plausible `topic`, and apply the stricter
  rules from both.
- If the product is worn, apparel-style rules (department, model versus
  flat-lay imagery, size runs) generally apply whatever the shelf category.

## How this maps to the skill's own references

amazon_atlas **complements**, doesn't replace, the bundled references:

- `01-policy-rules.md` — universal hard rules. Use directly; no lookup needed. amazon_atlas's `reference` docs are where to confirm or expand a specific rule when a decision is contested.
- `04-bullet-intent-scoring.md` — universal optimization rubric. Pull category `bullet_pattern` style from amazon_atlas, then apply the rubric on top.
- `06-patch-construction.md` / `05-aplus-content.md` — mechanics. `amazon_vendors` adds current Amazon A+ guidance for the copy itself.

## Note on prior design

Earlier versions of this skill referenced a single `amazon_listing_style` Chroma
collection with a `category` / `sub_category` / `field` metadata schema. That
layout has been **superseded** by the `amazon_atlas` multi-collection knowledge
base documented here (validated against a live instance). If you encounter a
deployment that still exposes `amazon_listing_style`, treat it as legacy and
prefer the `amazon_atlas` collections when both are present.
