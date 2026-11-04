# Lane 5: Schema Markup: Checklist and Templates

Detailed checklist, retrievability lens, and JSON-LD templates for
suede-seo-audit Lane 5. Grade-drop rules and scoring live in SKILL.md.

## Contents

- [Checklist](#checklist): validity, eligibility, and truthfulness
- [Retrievability lens](#retrievability-lens): which fields a model can quote,
  and whether the prose carries the structure the schema declares
- [Minimum templates](#minimum-templates): Organization, SoftwareApplication,
  BreadcrumbList, FAQPage, Article

## Checklist

- [ ] Decide whether a Google-supported structured-data feature fits the page.
      `No supported feature identified` is a valid result; schema is not
      mandatory for every page.
- [ ] Existing schema vocabulary and shape validate at schema.org/validator
- [ ] Markup intended for a Google feature passes the Rich Results Test and
      meets that feature's current required properties
- [ ] Schema type matches the page purpose:
  - Visible site-authored FAQ → `FAQPage` is valid schema.org vocabulary, but
    Google ended FAQ rich results for all sites on May 7, 2026. Use it only to
    mirror visible Q&A; never promise a search appearance.
  - Step-by-step instructions → `HowTo` is valid vocabulary with no Google
    rich result since 2023. Optional, never a fix for a ranking problem.
  - One user-submitted question with user-submitted answers → `QAPage`
  - Blog post or article → `Article` or `BlogPosting`
  - Product or app page → `SoftwareApplication` or `Product`
  - Docs or reference page → `TechArticle` or `WebPage`
  - Organization root page → `Organization`
  - Breadcrumb present for deep pages → `BreadcrumbList`
- [ ] FAQ schema represents the complete visible question/answer content (no
      hidden or hallucinated Q&A)
- [ ] `Organization` properties contain only verified facts. Add `logo` or
      `sameAs` only when the URLs are real, public, and identify the same entity.
- [ ] `SoftwareApplication` schema includes: `name`, `applicationCategory`,
      `operatingSystem`; include `offers` only when visible price/currency facts
      are verified and the targeted Google feature calls for them
- [ ] `Article` schema includes: `headline`, `author`, `datePublished`,
      `dateModified`

When warranted schema is missing or existing markup is broken, provide the
exact corrected JSON-LD block inline in the findings. Do not describe it only
in prose. Populate every field from visible page content or verified facts.
Never invent values, and never say valid markup guarantees a rich result.

For Google eligibility and policy, use:

- https://developers.google.com/search/docs/appearance/structured-data/search-gallery
- https://developers.google.com/search/docs/appearance/structured-data/sd-policies
- https://developers.google.com/search/test/rich-results

## Retrievability lens

Run this after the checklist above, over the JSON-LD you already parsed. It is a
second reading of evidence the lane already gathered, not a second fetch.

The checklist above answers *is this markup correct and honest*. It cannot
answer *which of these fields can a model actually quote*, and a page can pass
every validity check while failing that second question.

Google Cloud's Discovery Engine (Vertex AI Search) is Google's own retrieval
product, so its configuration surface is the clearest public statement of how
Google separates the effects a field can have. Read it as that and no more: it
documents a product you can configure, not the behaviour of Google Search. It
exposes three per-field settings, and their independence is documented rather
than inferred:

| Setting | Documented effect | Audit meaning |
|---|---|---|
| `searchable` | "whether this field can be reverse indexed to match unstructured text queries" | recall: can the document be found at all |
| `indexable` | "whether this field can be filtered, faceted, boosted, or sorted" | filtering and ordering |
| `retrievable` | "whether this field can be returned in a search response" | what can reach the model's answer |

> "A field can be searchable without being indexable or retrievable."

So a field can move ranking while never appearing in an answer, or appear in an
answer while moving no ranking. Each setting caps at 50 fields, which makes
retrievability a budget an operator spends, not a property markup carries on
its own.

Sources:

- https://cloud.google.com/generative-ai-app-builder/docs/provide-schema
- https://cloud.google.com/generative-ai-app-builder/docs/configure-field-settings
- https://cloud.google.com/generative-ai-app-builder/docs/add-website-metadata

**Stay inside what is documented.** For a data store you configure, page
schema.org annotations reach these settings only when an operator declares each
path explicitly (`siteSearchSchemaOrgPaths`, for example
`_root.aggregateRating.ratingValue`) and sets the flags on that path. Nothing
is retrievable by default. No Google documentation maps any schema.org property
to any flag inside Google Search, AI Overviews, or AI Mode.

Write findings inside that boundary:

- Supported: "no documentation says this property reaches an answer; the visible
  prose is the part of this claim the audit can verify."
- Supported: "`Article.dateModified` is a required property for the Article
  feature": cite the search-gallery page that says so.
- Unsupported, and never write it: "Google marks `acceptedAnswer` retrievable",
  or any sentence that names a flag as observed Google Search behavior.

The classifications below are claims about the page in front of you, decided by
evidence you can quote. They are not claims about Google's pipeline.

**Classify every property in every JSON-LD block:**

- [ ] `prose-backed`: the property's value states a claim that also appears in
      visible page text. Evidence: the property value and the quoted prose.
- [ ] `indexable-only`: the value is a filter, sort, or eligibility value (a
      date, rating, price, category, or `@type`) rather than a sentence a reader
      would quote, and a named Google feature lists it as required or
      recommended. Evidence: the search-gallery page for that feature.
- [ ] `decorative`: the property validates, has no prose counterpart, and no
      named Google feature requires it.
- [ ] `unclassified`: evidence supports none of the three. Record
      `unclassified`. Do not round to the nearest label; an unclassified
      property is an honest audit result and a guessed one is an invented claim.

**Flag schema-only claims.** When a property is the page's only
machine-readable statement of a material claim: a price, a date, a credential,
an availability, an answer: record it as a finding. The prose is the surface
both the reader and the audit can verify, so the fix is a prose counterpart,
not more markup. A property classified `indexable-only` or `decorative` is not
a schema-only claim; it carries no reader-facing claim to lose.

**Confirm the prose carries the structure the schema declares.** Some types
assert that the page has a shape. Count the entries in the JSON-LD, count the
matching visible elements, and record both numbers:

| `@type` | Structure declared | Visible prose must carry |
|---|---|---|
| `FAQPage` | N question/answer pairs | N headings, one per question |
| `HowTo` | ordered steps | one heading or list item per step, in document order |
| `ItemList` | N enumerated items | N items a reader can see and count |
| `BreadcrumbList` | a position hierarchy | a visible breadcrumb trail |

`<summary>`, `<button>`, `<dt>`, and styled `<div>` are not headings. Equal
counts pass; a prose count lower than the schema count is the finding, and it
stands even when the markup is valid and its text matches the visible text
character for character. This is the defect a validity-only reading cannot see:
the schema is correct about content the page has and wrong about structure the
page lacks.

Lane 4's **Retrieval chunking** block owns the measurement: the ~375-word
block size and which markup collapses into one block. Lane 5 owns the opposite
direction: the schema declared a structure, so verify the prose has it. Record
the count mismatch here and cite the Lane 4 block for the block size rather
than re-measuring it.

Retrievability check output format:
```
Property: [path], [prose-backed | indexable-only | decorative | unclassified], evidence: [quoted prose | feature doc URL | none]
Schema-only claims: [property = value, no prose counterpart] | none
Structure claim: [@type] declares [N] [questions/steps/items] | visible headings: [N] | [match/mismatch]
```

## Minimum templates

### Organization

```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "@id": "[Canonical organization URL]#organization",
  "name": "[Verified organization name]",
  "url": "[Canonical organization URL]"
}
```

Add `logo` and `sameAs` only when each URL is verified, public, and identifies
the same organization. They are not filler fields. Reuse the same `@id` on
every page (as `publisher`, `worksFor`, `brand`) instead of redeclaring the
organization with different values. Full Organization and Person templates and
the off-site consistency sweep live in `suede-ai-seo`'s entity-graph
reference.

### BreadcrumbList

Only when a visible breadcrumb trail exists on the page.

```json
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    { "@type": "ListItem", "position": 1, "name": "[Visible label]", "item": "[URL]" },
    { "@type": "ListItem", "position": 2, "name": "[Visible label]", "item": "[URL]" }
  ]
}
```

### SoftwareApplication

```json
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "[Product name]",
  "applicationCategory": "[e.g. DeveloperApplication]",
  "operatingSystem": "[e.g. macOS, Web]"
}
```

Add an `offers` object only when the offer is visible and verified. Never infer
that an app is free because no public price was found.

### FAQPage

Every `name` and `text` value must match the visible FAQ. This template
expresses schema.org vocabulary only; Google no longer shows FAQ rich results
for any site.

```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "[Visible question text]",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "[Visible answer text]"
      }
    }
  ]
}
```

### Article

```json
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "[Visible headline]",
  "author": { "@type": "Person", "@id": "[Author page URL]#person", "name": "[Author name]", "url": "[Author page URL]" },
  "datePublished": "[YYYY-MM-DD]",
  "dateModified": "[YYYY-MM-DD]"
}
```
