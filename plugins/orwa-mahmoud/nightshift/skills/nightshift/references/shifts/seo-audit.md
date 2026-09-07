# SEO audit — finite — prioritized, cited findings from an explicit site or tree

Use when the owner names a site, a URL list, or a local documentation/marketing tree and wants a
reviewable audit rather than a guessed ranking. The list of sources is whatever they supplied;
the shift ends when every supplied source is recorded and the report is checked.

Supported on any persistent folder or repository that can hold the report. A local HTML/markdown
tree is enough. Live crawl, Search Console, analytics, backlink databases, and production SSH are
out of scope unless the owner provided that evidence in the source list.

Follow `$NIGHTSHIFT_PLUGIN_ROOT/skills/nightshift/references/cited-research.md` for the source
manifest, citations, observations versus inferences, executive summary, private-material rules,
and `check-report` verification. Typical hours: 2–4.

```text
- [ ] **SEO audit — produce a prioritized, cited audit of the named site or tree.**
  - Discovery: read only the owner-approved site, URL list, or local source tree recorded in the
    work order or punch-list scope. Write a dated source manifest (`ok` / `unavailable`) before
    drafting findings. Do not add URLs from memory or search.
  - For each `ok` source, evaluate the evidence that is actually present: metadata, canonicals,
    headings, indexability signals (robots, noindex, sitemap if in the tree), structured data,
    internal links, duplication, content quality, and discoverability. Use real performance
    numbers only when the owner provided them (a lab file, a HAR, a Lighthouse JSON). Missing
    measurements stay `unavailable`, never estimated.
  - Separate verified defects, opportunities, and unavailable data. Rank defects by user impact
    and fixability in the report; do not invent Search Console, analytics, backlink, ranking, or
    production-access claims that were not in the source list.
  - Review first writes the report (and manifest) only. Direct mode may edit authorized local
    source files after the report names the change; it never publishes, deploys, or submits to a
    search console.
  - Inherit cited-research.md: observations vs inferences, `[S1]` citations, no fabricated
    access. Keep private code, secrets, customer data, and unpublished material out of external
    fetches and out of the report.
  - Dedupe against snag-log.md (ALL seen — fixed and rejected).
  - Ends when every supplied source is `ok` or `unavailable` with a reason, the report passes
    check-report, and leftover local edits (direct mode only) are behind the item gate.
  - Verify: `"$NIGHTSHIFT_PLUGIN_ROOT/runtime/check-report.sh" --project "$NIGHTSHIFT_WORKSPACE"
    --report <audit.md> --manifest <sources.tsv> --output <audit.md>` (native Windows:
    `& "$NIGHTSHIFT_PLUGIN_ROOT\runtime\windows\check-report.ps1"`); the item gate is green at
    every commit or artifact receipt (artifact mode: `$NS/receipts/`).
```
