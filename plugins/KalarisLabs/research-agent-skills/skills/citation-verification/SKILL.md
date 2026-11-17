---
name: citation-verification
description: Verify that every reference in a manuscript really exists and matches its metadata, catching hallucinated, corrupted, mismatched or retracted citations before submission. Use when checking a .bib file or reference list, after an AI assistant drafted citations, when a DOI may point to the wrong paper, when a paper may have been retracted, when a dataset or software DOI (Zenodo, DataCite) will not resolve, when adding missing DOIs, marking unverifiable references, checking whether one DOI is real, or before camera-ready. Queries Crossref, DataCite, OpenAlex and arXiv and flags Retraction Watch notices; zero dependencies.
license: MIT
compatibility: Python 3.9+ standard library; needs network access to api.crossref.org, api.datacite.org, api.openalex.org and export.arxiv.org.
metadata:
  version: "1.0"
  category: literature-review
  maintainer: Kalaris Labs
  author: Kalaris Labs (Sayan Chowdhury)
  tags: citations, hallucination, DOI, Crossref, DataCite, OpenAlex, arXiv, retraction, references, research integrity
---

# Citation Verification

Language models (and tired humans) produce references that look right but are
not: plausible titles that were never published, real DOIs attached to the wrong
paper, wrong years, invented co-authors. Citing a paper that does not exist can
lead to desk rejection, a correction, or a misconduct inquiry. This skill makes
verification systematic.

## Non-negotiable rules

1. **Never write a reference from memory.** Every entry must come from a
   retrievable record (Crossref, OpenAlex, arXiv, PubMed, publisher page).
2. **A reference is verified only when its identifier resolves to a record whose
   title, first author and year all match.** A resolving DOI alone proves nothing.
3. **If you cannot verify a reference, say so.** Mark it `% UNVERIFIED` in the
   `.bib`, tell the user, and never quietly keep it.
4. Verify the claim too: open the abstract or the cited section and confirm the
   paper actually supports the sentence citing it.

## Workflow

```bash
export CROSSREF_MAILTO=you@university.edu   # polite pool: faster, fewer rate limits
python scripts/verify_citations.py references.bib --json citation-report.json
python scripts/verify_citations.py --doi 10.1038/nature14539 10.1126/science.aaa8415
python scripts/verify_citations.py references.bib --keys smith2020,li2023   # re-check a subset
python scripts/verify_citations.py references.bib --annotate                # add `% UNVERIFIED` comments in place
```

DOIs are resolved in Crossref, then DataCite (datasets, software, Zenodo, figshare), then OpenAlex.
A retraction is read from Crossref `updated-by` notices (Retraction Watch data) and cross-checked
against OpenAlex `is_retracted`. `--annotate` is opt-in because it rewrites the `.bib`: it inserts a
`% UNVERIFIED (<status>): <reason>` comment above each entry that needs attention, never edits an
entry body, and is idempotent (re-running replaces or removes stale markers).

Each entry gets a status:

| Status | Meaning | Action |
|---|---|---|
| `verified` | Identifier resolves; title/author/year agree | None |
| `found-add-doi` | No DOI in the entry, but an unambiguous match exists | Add the suggested `doi` field |
| `mismatch` | DOI resolves to a *different* work, or year/author disagree | Fix from the record, or find the intended paper |
| `doi-not-found` | DOI does not resolve anywhere | Typo or fabricated: search by title |
| `uncertain` | Title matches but year/author disagree, only a weak title match, an expression of concern, or no match while a source was rate-limited or down | Check manually (reprints, errata, homonymous papers), or re-run if the message names an unavailable source |
| `not-found` | No plausible match in Crossref, OpenAlex or arXiv | Treat as fabricated until proven otherwise (grey literature, theses and reports may legitimately be absent) |
| `retracted` | The record carries a retraction, withdrawal or removal notice | Do not cite as support. Replace it, or cite it explicitly as a retracted work |
| `unverifiable` | The entry has neither a DOI nor a title | Complete the entry, then re-run |
| `error` | The lookup failed (network, rate limit) | Re-run later; this is never evidence of a bad reference |

Exit code `0` means everything is verified or only missing DOIs; `1` means something needs a human; `2` is bad input.

## Handling the hard cases

- **Conference papers without DOIs** (NeurIPS, ICML, ICLR, many CS venues): the script
  falls back to arXiv. Cite the proceedings version with a `url` to the official
  proceedings page, and optionally keep `eprint` for the arXiv ID.
- **Preprint vs published**: if both exist, cite the peer-reviewed version unless
  the venue asks otherwise. OpenAlex links versions of the same work.
- **Books and chapters**: check ISBN via the publisher or Open Library. Crossref covers many but not all.
- **Datasets and software**: DataCite DOIs (Zenodo, figshare, many repositories) are resolved
  automatically. Software Heritage identifiers (`swh:1:...`) are not covered; check them at the archive.
- **Retractions**: the script reports them as `retracted` (Crossref `updated-by` notices from
  Retraction Watch plus OpenAlex `is_retracted`). Never cite a retracted paper as support. An
  `expression_of_concern` notice yields `uncertain` with the notice DOI. A DOI-less entry that
  matches by title gets the same check on the DOI the script suggests.
- **Non-English or old literature**: absence from these indexes is common. Confirm via
  library catalogs and document the source.

## Reporting to the user

Summarize as a table: key, status, problem, and the fix you applied or propose.
Apply only mechanical fixes automatically (adding a DOI for a `found-add-doi`
match). Anything `mismatch`, `uncertain` or `not-found` requires the user's
confirmation because only they know which paper they meant to cite.

## Related skills

- `bibtex-hygiene`: duplicates, missing fields, capitalization and formatting in the `.bib` file.
- `citation-management`: finding and exporting references from literature databases.
- `literature-review`: systematic searching and screening.
