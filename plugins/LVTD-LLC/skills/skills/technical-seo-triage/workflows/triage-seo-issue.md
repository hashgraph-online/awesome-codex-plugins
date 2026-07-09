# Triage SEO Issue Workflow

Use this workflow to diagnose traffic drops, indexing issues, technical SEO errors, and migration risk.

## When to Use

- Organic impressions, clicks, or conversions changed unexpectedly.
- Important URLs are not indexed or canonicalized as expected.
- Google Search Console reports errors.
- A migration, redesign, URL change, or platform change is planned.
- A technical SEO audit needs prioritization.

## Prerequisites

- URL(s), date range, and symptom.
- GSC access or exported data.
- Analytics, logs, crawl data, or CMS change history if available.
- Knowledge of recent releases, migrations, content changes, or template changes.

**Reference**: `references/core/knowledge.md`, `references/core/rules.md`

## Workflow Steps

### Step 1: Define The Symptom

**Goal**: Make the problem specific.

- [ ] Record what changed: impressions, clicks, CTR, average position, index status, conversions, or revenue.
- [ ] Record when it changed.
- [ ] Identify affected URL patterns, page types, countries, devices, and query groups.
- [ ] Separate brand and non-brand traffic.

### Step 2: Locate The Search Stage

**Goal**: Classify where the failure happens.

- [ ] Discovery: Is the URL linked, in sitemap, and known to Google?
- [ ] Crawling: Is Google fetching the URL?
- [ ] Indexing: Is it indexed, excluded, duplicate, or canonicalized elsewhere?
- [ ] Ranking/clicking: Is it indexed but losing impressions or clicks?
- [ ] Conversion: Is traffic present but business value missing?

### Step 3: Inspect Evidence

**Goal**: Use primary data before proposing fixes.

- [ ] Use GSC URL inspection and performance comparison.
- [ ] Check canonical selected by Google versus declared canonical.
- [ ] Check robots, noindex, redirects, status codes, schema, and load errors.
- [ ] Crawl affected URL sets.
- [ ] Review release history and content/template changes.

### Step 4: Prioritize Fixes

**Goal**: Order work by risk and impact.

- [ ] Fix blockers first: robots, noindex, broken redirects, status errors, broken canonicals.
- [ ] Fix architecture issues: orphan pages, weak internal links, low-value URL traps.
- [ ] Fix content/UX issues only after technical blockers are understood.
- [ ] For migrations, prefer staged changes when risk is high.

### Step 5: Validate Recovery

**Goal**: Confirm the fix worked.

- [ ] Re-crawl affected URLs.
- [ ] Request reinspection or resubmission where appropriate.
- [ ] Monitor impressions first, then clicks, then conversions.
- [ ] Compare against unaffected controls when possible.
- [ ] Document the root cause and prevention step.

## Quick Checklist

```text
[ ] Symptom narrowed
[ ] Search stage identified
[ ] GSC inspected
[ ] Canonicals/robots/status/redirects checked
[ ] Internal links/crawl paths reviewed
[ ] Fixes prioritized
[ ] Validation plan defined
```

## Exit Criteria

Task is complete when the issue has a classified search stage, evidence-backed root cause hypothesis, prioritized fixes, and a measurable validation plan.
