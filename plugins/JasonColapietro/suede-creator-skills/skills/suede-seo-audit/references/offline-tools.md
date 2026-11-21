# Offline SEO tools

Requires Node.js 22 or newer. No npm dependencies, Python runtime, account,
credentials, network fetching, or Search Console access. Run the commands in
SKILL.md from the installed skill folder. MCP tools remain read-only discovery
and skill-text tools; they do not execute this CLI. Copy or install the full
skill folder to run it. npm and Python distributions bundle the same supporting
files; Python users still need Node to execute the SEO CLI.

## Supplied HTML inventory

`audit --input pages.json --out reports/NEW_NAME [--merchant]` takes JSON:

```json
{
  "origin": "https://example.test",
  "pages": [
    {"url": "https://example.test/en", "html": "<title>Example</title><h1>Example</h1>"}
  ]
}
```

Provide an absolute normalized HTTP(S) page URL from that origin, no credentials
or fragments, and literal HTML for each page. No files, URLs, redirects, headers,
images, linked documents or schema IDs are fetched. URL spelling, slash and
query are identity. The non-rendering tokenizer skips comments, inert templates
and raw-text decoys; it is not a full HTML conformance validator or rendered DOM.
Limits: 25 MB input file, 1–1,000 pages, 2 MB HTML per page. Duplicate or foreign
page URLs fail. An empty inventory fails to prevent accidental empty baselines.

Outputs: `seo-audit.json`, escaped `seo-audit.md`, `metadata-snapshot.json`.
Merchant output exists only with `--merchant`; choose it for actual purchasable
products, not editorial reviews. Check visible content, active purchase state
and current Google documentation separately before claiming eligibility.

## Immutable snapshots and drift

`drift --before BASELINE --after CURRENT --out reports/NEW_NAME` validates both
snapshot schemas, matching origin, URL uniqueness and timestamp order. Captures
never overwrite an existing output directory. Save baselines deliberately and
capture a new run for every comparison. "Immutable" means the CLI refuses reuse;
it does not make files tamper-proof or read-only at filesystem level.

Supplied inventories always set `coverage.complete=false`, `sourceKind=supplied`.
Missing URLs mean `not-observed`, not removed, broken or noindexed. Module users
may explicitly attest complete selected local builds; only two such inventories
produce `absent-from-build`, still not proof of a live deletion. Arrays of
annotations and JSON object keys are normalized to avoid ordering noise; heading
order remains significant. Markdown truncates field values to 2,000 characters;
JSON retains them. HTTP headers, response status, rankings and performance are
unmeasured. Reports may contain your supplied evidence: review before sharing.

## Supplied SERP exports

`serp-clusters --input serp.json --context "engine/locale/device/period" --out
reports/NEW_NAME [--depth 10] [--threshold 0.3]` takes an array:

```json
[
  {"keyword":"example topic", "collectionContext":"Synthetic fixture only",
   "organic":[{"rank":1,"url":"https://example.test/guide"}]}
]
```

Every keyword needs a distinct rank for each organic position 1–K and K distinct
document URLs. Short, gapped and duplicate-URL samples are explicitly excluded;
malformed ranks/URLs and mixed supplied collection contexts fail. Context is a
required user label, not verified provenance. Group only comparable engine,
locale, device and collection periods. Inputs with no explicit per-row context
use your run label, so confirm provenance yourself.

At most 500 keywords, 500 characters per keyword, K 1–100, threshold (0,1].
Same-depth overlap = shared document URLs / K. URL fragments are removed, while
host, protocol, path, trailing slash and query remain distinct. Keywords use
NFKC, lowercase and collapsed whitespace. Sorted greedy complete-link grouping
requires every pair within a group to meet the threshold, preventing transitive
chains. It is deterministic, not a globally optimal partition or semantic
intent classification. Output includes pair evidence and exclusions. Budgets:
5 MB sample evidence and 2 MB qualifying pair evidence. Exceeding a budget fails
without writing a report or silently sampling. No ranking, demand, traffic,
conversion or future outcome is inferred, and no calendar or target is changed.

## Safe output and tests

All commands require a new output directory outside the working directory or
inside its `reports/` subtree. Existing directories and protected source paths
(including symlink ancestors) are refused. Plain filenames only; Markdown escapes
HTML, link syntax and table delimiters. JSON is data, not embeddable HTML.

Run `node --test scripts/tests/*.test.mjs` from the skill folder. Fixtures use
reserved `.test` domains and synthetic content. They require no external service.
