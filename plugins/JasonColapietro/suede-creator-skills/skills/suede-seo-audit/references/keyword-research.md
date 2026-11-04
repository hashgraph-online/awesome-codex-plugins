# Lane 0: Evidence-Based Keyword Research

Read this file only when keyword discovery is requested. Lane 0 produces a
brief, not a grade.

**Goal:** identify a defensible query theme and content gaps without inventing
search demand, ranking difficulty, or traffic potential.

## Evidence rules

- Record the source, market, device scope, and observation date for every
  numeric search-volume, traffic, CPC, or ranking claim.
- Prefer current first-party data: Search Console queries, site analytics,
  Google Ads Keyword Planner exports, or another user-supplied dated export.
- If no numeric source is available, write `volume: unknown`. Do not infer a
  monthly range from query length, topic breadth, or intuition.
- Distinguish an observed SERP from a ranking guarantee. Search results vary by
  time, location, device, and personalization.
- Do not manufacture difficulty scores. Describe the visible competition and
  evidence instead: result types, recognized domains, page intent, content
  depth, and the target site's existing authority or coverage.
- Use `related topics and entities`, not `LSI keywords`. Include terms only
  when they help a reader understand the subject.

## Protocol

1. **Primary query theme:** choose one phrase or tightly related query family
   that matches the page's purpose. Classify intent as informational,
   navigational, commercial, transactional, or mixed. Cite the evidence used.

2. **Supporting query themes:** list 3-5 related queries that serve the same
   reader without forcing unnatural repetition. Mark each as observed in a
   source, seen on the live SERP, or inferred from the subject.

3. **Related topics and entities:** list the people, products, standards,
   concepts, and subtopics a complete answer should cover. Group them by
   reader need. This is a coverage map, not a density quota.

4. **Competitor content gap:** when competitor URLs are supplied or a live
   search is authorized, inspect the current pages. For each competitor:

   a. Record the URL, access date, title, and relevant H2/H3 sections.
   b. Identify useful subjects the target page omits.
   c. Classify each gap as `critical`, `important`, or `optional` based on
      reader intent, not presumed ranking impact.

   Output:

   ```text
   Competitor: [URL] (checked [YYYY-MM-DD])
   Missing subject: [subject or heading]
   Evidence: [what the competitor covers and the target omits]
   Reader value: [why this helps answer the primary intent]
   Priority: [critical | important | optional]
   ```

   If live competitor pages were not checked, say so. Do not invent their
   headings, rankings, or traffic.

5. **Search-feature eligibility:** name only features supported by current
   Google Search documentation for the page type. Separate:

   - technically eligible;
   - validated in the Rich Results Test;
   - observed in a live result;
   - not verified.

   Structured data can make a page eligible for a supported feature; it does
   not guarantee display.

## Content brief

Generate this only when Lane 0 is active and a page is being built or
substantially revised.

| Field | Guidance |
|---|---|
| Reader and job | Name the reader, question, and useful outcome. |
| Primary query theme | Phrase or query family, intent, evidence source, market, and date. |
| Demand evidence | Numeric value with dated source, or `unknown`. |
| Competitive evidence | URLs and observations checked live, or `not checked`. |
| Required sections | Subjects needed to answer the reader completely; do not copy competitor headings mechanically. |
| Related topics/entities | Natural coverage map; no occurrence quota. |
| Schema eligibility | Supported Google feature and required properties, or `no supported rich-result type identified`. |
| Internal links | Verified anchor text and destinations that help the reader continue. |
| External sources | Current primary or authoritative sources for factual claims. |
| Length | Whatever is needed to answer the intent clearly. Do not assign a universal word-count target. |

## Output

```text
Primary query theme: [query family]
Intent: [informational | navigational | commercial | transactional | mixed]
Evidence source: [source, market, device scope, checked date]
Demand: [sourced value/range | unknown]
Visible competition: [observations with URLs | not checked]
Supporting query themes: [query, observed/inferred, evidence]
Related topics and entities: [grouped list]
Content gaps: [subject, evidence, reader value, priority]
Search-feature eligibility: [feature: eligible/validated/observed/not verified]
Content brief: [reader-first section and source plan]
```

Incorporate this brief into Lanes 2-7 where relevant. Never turn missing
numeric tooling into fabricated precision.
