# Channel Selection

Use this reference when choosing evidence channels and writing the query plan.

## Topic To Channel Map

| Topic shape | Start here | Add this if needed | Avoid |
|------|------|------|------|
| Internal project behavior or history | local repository search | git history or GitHub evidence if repo metadata matters | live web search first |
| Library or package usage | the official docs for the named version, through the available doc or fetch capability | GitHub issues, releases, or examples | generic blogs before docs |
| Product, repository, or release comparison | GitHub releases, issues, changelog, code search | live web coverage for independent commentary | relying only on marketing pages |
| Market, trend, or current-events research | live web search with date awareness | official reports or company filings | stale evergreen articles |
| Academic or concept research | primary papers or official references | secondary explainers for synthesis | opinion pieces as primary evidence |
| Multi-option technical comparison | official docs for each option, then independent benchmarks or case studies | GitHub evidence for implementation reality | conclusions without a criteria grid |

## Selection Notes

- Prefer the smallest channel set that can answer the question well.
- Use live search whenever the request is current, latest, or date-sensitive.
- For codebase-only questions, stay inside the repository unless outside evidence is explicitly needed.
- When a package version is specified, start with the official docs for that version.
- Raw files (PDF, JSON, feeds, sitemaps) are fetched directly; a rendered page or any other source that a plain fetch cannot read follows Blocked Sources below.

## Blocked Sources

A source the plan needs but a plain fetch cannot read - a 403 or 429, a bot challenge such as `Just a moment...`, an empty JavaScript shell, or a dead or removed page - is never dropped silently. Repository-only questions never take this path.

1. When the runtime exposes a blocked-page access capability (a skill or tool the caller named, or a browsing capability), use it for that one source after its `sources.md` row is open.
2. Record the route in that row: `Channel` holds the access route and its provenance label (`live`, `api`, `reader`, `snapshot`, `rendered`); `Version/freshness` holds the snapshot timestamp of a `snapshot`; `Caveat` names the report path the capability saved, when it saved one.
3. Cite a `snapshot` as a dated copy ("<archive> copy as of <timestamp>"), never as the current page, and never use it for a recency claim its date cannot support.
4. An HTTP 200 from a reader or an archive is not access. A body that still shows a challenge, an interstitial, or binary bytes is recorded as inaccessible.
5. A login wall, a paywall, or a legal block (451) stays inaccessible even when a copy exists: record it and look for another source.
6. The source counts once against the collection budget like any other; the capability's own attempts open no new budget.
7. With no such capability, record the source as inaccessible with its signal (status code or challenge title) and move to the next channel.

## Search Craft

- Search in English first: it is the largest corpus on most engines, code hosts, and documentation sites. Add a local-language sweep afterwards when the topic is local or the user names a source language.
- Vary the operator or angle on every query; the same query twice wastes a pass. Operator support differs by engine, so treat a missing operator as a cue to rephrase, not as a failure.

| Operator | Example | Use |
|---|---|---|
| `site:` | `site:github.com <topic>` | Restrict to a domain |
| `filetype:` | `filetype:pdf <topic> survey` | Papers and specifications |
| `intitle:` / `inurl:` | `intitle:benchmark <topic>` | Targeted pages |
| `"exact"` / `-term` | `"<exact phrase>" -tutorial` | Precision and exclusion |
| `OR` | `<a> OR <b> <topic>` | Coverage |
| `before:` / `after:` | `<topic> after:<YYYY-MM-DD>` | Recency control |

- High-yield angles: official docs (`site:<docs domain>`), implementations (`site:github.com`), changelogs (`changelog OR "release notes" <version>`), alternatives (`vs OR alternative OR comparison`), and counter-evidence (`<claim> problems OR criticism OR regression`), which also serves the claim gate's counter-search.
- Use a sitemap (`<base>/sitemap.xml`) to find the right official page instead of guessing URLs.

## Sources

> Checked 2026-11-03.

| Claim | Source |
|---|---|
| English-first search with a later local-language sweep, the operator table, the high-yield angles, and sitemap discovery, adapted from the `ulw-research` skill | <https://github.com/code-yeongyu/oh-my-openagent/tree/0d80470e4201925727e88afbafcdf24d7801a588> |
| Name tools by capability rather than one runtime's tool name | <https://github.com/alpoxdev/hypercore/blob/01be78de5973eb75a616e5156058621a6fabbc97/instructions/cli/capability-contract.md> |
| Blocked-source handling: one capability call per source, provenance labels, dated snapshot citation, and paywalls staying inaccessible | this package's chosen design, not a validated optimum |

### Evidence grade

`LOCAL` - the channel map is this package's own policy. Operator support is engine-specific, which is why the table is a guide rather than a guarantee.
