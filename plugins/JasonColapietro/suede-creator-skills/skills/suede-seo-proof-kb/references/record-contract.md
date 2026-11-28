# Proof record and audience contract

Use these fields in the existing evidence tool. An approved private Markdown table or a local JSON file is enough; the design does not require a new database.

| Field | Example shape | Review question |
| --- | --- | --- |
| Claim ID and revision | `proof-csv-export-duration`, revision 2 | Is this a single independently changeable fact? |
| Public wording | A complete sentence including population and period | Can a reader distinguish this outcome from a universal guarantee? |
| Evidence locator and owner | Owner-approved reference plus named maintainer | Can an authorized reviewer retrieve the source without exposing it to readers? |
| Observed date and period | ISO date plus data start and end | Is it recent and relevant enough for the intended page? |
| Method and baseline | Version, inputs, unit, cohort, sample, exclusions, comparison | Would a different setup make the same sentence misleading? |
| Verification | observed, unverified, stale, disputed | What was checked, by whom, and against which revision? |
| Permission | public, attributed public, anonymized, internal only, permission withheld, revoked | Is the exact excerpt cleared for this audience and channel? |
| Scope | relevant product variant, region and claim restrictions | Who can rely on this claim? |
| Change tracking | review date, expiry rule, superseded/replacement ID | What event should trigger a recheck? |
| Known uses | URL, anchor, locale, visible text or metadata, last checked | Can the team find everywhere this sentence or value appears? |

Keep source facts and publication decisions separate. If disclosure is restricted, export only the cleared wording and its approved public citation. A customer that permits anonymized reporting on the website may not have approved named quotes or ad use. New brand statements, measurements and public citations are not substitutes for customer consent.

For changing prices, retain plan and currency, whether tax or shipping is included, and the effective date. For time-based performance claims, keep comparable windows and state whether the data describes a sample, the median, an upper bound, or another distribution statistic. Re-evaluate whether independent measurements or comparisons are needed when the audience or methodology changes.

## Prompt-gap evidence row

Record the question, expected answer category, exact market/model and measurement date, whether the prompt completed, any cited page that was inspected, the site's best existing answer, and the eligible proof IDs. A completed response without a citation and a request that never completed are different results. If a credible answer already exists on site, note whether the missing item is a new source, page section, link or measurement before proposing a new URL.
