# Entity and Knowledge-Graph Consistency

Answer engines attribute facts to entities: an organization, a person, a
product. When the name, founder, URL, or description differs from one source
to the next, engines hedge, merge you with someone else, or leave you out. This
reference is the Suede procedure for making one entity unambiguous everywhere.

## 1. Pick the canonical facts

Write them down once, then copy from this sheet everywhere.

| Field | Canonical value | Notes |
|---|---|---|
| Organization name | | Exactly as it should be cited |
| Alternate names | | Former names, abbreviations |
| Entity home URL | | Usually /about |
| Logo URL | | Stable, crawlable, square-safe |
| Founder / key people | | Names as they appear in bylines |
| One-sentence description | | What it is, for whom, doing what |
| Verified profiles | | Only profiles the entity controls |
| Contact / address | | Only if public |

## 2. Entity homes

- Organization: one About page that states the canonical description, people,
  founding date (if public), and links to every verified profile.
- Person: one author page per byline with role, credentials that can be
  checked, and links to their verified profiles.
- Product: one canonical product page per product.

Give each a stable `@id` (the page URL plus `#organization`, `#person`, or
`#product`) and reference that `@id` from every other page instead of
re-declaring the entity with different values.

## 3. JSON-LD templates

Populate only with facts visible on the page or verified. Omit any property
you cannot verify; never pad `sameAs`.

Organization (on the entity home, referenced site-wide):

```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "@id": "https://example.com/#organization",
  "name": "Example Co",
  "alternateName": ["Example"],
  "url": "https://example.com/",
  "logo": "https://example.com/logo.png",
  "description": "Example Co builds [what] for [whom].",
  "founder": { "@id": "https://example.com/about/jane-doe#person" },
  "sameAs": [
    "https://www.linkedin.com/company/example-co",
    "https://github.com/example-co",
    "https://www.wikidata.org/wiki/Q00000000"
  ]
}
```

Person (on the author page):

```json
{
  "@context": "https://schema.org",
  "@type": "Person",
  "@id": "https://example.com/about/jane-doe#person",
  "name": "Jane Doe",
  "jobTitle": "Founder and CEO",
  "worksFor": { "@id": "https://example.com/#organization" },
  "url": "https://example.com/about/jane-doe",
  "sameAs": [
    "https://www.linkedin.com/in/janedoe",
    "https://x.com/janedoe"
  ]
}
```

Article byline (on each post), linking instead of redeclaring:

```json
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "[Visible headline]",
  "author": { "@id": "https://example.com/about/jane-doe#person" },
  "publisher": { "@id": "https://example.com/#organization" },
  "datePublished": "2026-10-01",
  "dateModified": "2026-10-20"
}
```

Some consumers resolve `@id` references only within one page. When a page uses
an `@id` it does not define, also include a minimal node (`@id`, `@type`,
`name`) so the page stands alone.

Validate with the Schema.org Validator for shape and the Rich Results Test for
any Google feature you target. Google documents Organization markup for logo
and knowledge-panel details; schema is not required for AI features, and its
value here is consistency, not a ranking switch.

## 4. Consistency sweep

Check each source against the canonical sheet. Record found value, canonical
value, and fix owner.

- Own site: title tags, footer, About, author pages, JSON-LD, press page.
- Social bios: LinkedIn, X, YouTube, Instagram, TikTok, GitHub.
- Business listings: Google Business Profile, Bing Places, Apple Business
  Connect (when local or physical).
- Review and directory listings: G2, Capterra, Product Hunt, app stores,
  industry directories.
- Knowledge bases: Wikidata (edit only with sources and per its notability and
  conflict-of-interest rules), Wikipedia (do not edit your own article; request
  changes on the talk page), Crunchbase.
- Press bios and speaker pages.

Score: matching facts divided by facts checked. Report per source, fix
the highest-traffic mismatches first, and re-run monthly.

## 5. Common failures

- Old brand name lingering in a directory or app-store developer name.
- Founder title differing between LinkedIn and the site.
- `sameAs` pointing to a profile of a different company with the same name.
- Multiple Organization blocks across pages with different `name` or `logo`.
- Author pages with no link from the byline.
- A Person schema claiming credentials the visible page does not show.
