# Project Map Candidate Ranking

Use this reference when several entries could match a query.

## Ranking Signals

Prefer candidates with:

1. Direct glossary or title match to the user's words.
2. Matching tags for domain, capability, data shape, workflow, or risk.
3. `Preferred` or `Stable` status.
4. Recent `Last Verified` and `Source-Verified` evidence.
5. Matching entry points, routes, APIs, or source paths.
6. Strong `Use When` fit and no `Do Not Use When` conflict.
7. Related entries that connect feature, flow, surface, implementation, and contract.

Deprioritize candidates with:

- `Deprecated`, `Legacy`, `Unknown`, `Inferred`, or `Stale` evidence unless the user asks about history.
- Broad names but weak tags.
- Similar UI but different business meaning.
- Matching source path but mismatched semantic responsibility.
- Missing `Use When` or `Do Not Use When`.

## Query Expansion

Expand from:

- Chinese and English business terms.
- User phrases from glossary entries.
- Code names, API names, route names, menu labels, and file names.
- Tags such as `batch-import`, `excel`, `approval`, `permission`, `async-job`, `polling`.

## Source Verification Threshold

Verify source before making these claims:

- "This route/file is the current entry point."
- "This implementation can be reused."
- "This contract has these fields."
- "This is preferred/deprecated."
- "This behavior definitely happens."

You can skip source verification only when answering a rough map and clearly labeling the result as map-derived.
