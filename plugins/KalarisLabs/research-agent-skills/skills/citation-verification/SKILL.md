---
name: citation-verification
description: Verify that every reference in a manuscript really exists and matches its metadata, catching hallucinated, corrupted or mismatched citations before submission. Use when checking a .bib file or reference list, after an AI assistant drafted citations, when a DOI may point to the wrong paper, when adding missing DOIs, or before camera-ready. Queries Crossref, OpenAlex and arXiv; zero dependencies.
license: MIT
compatibility: Python 3.9+ standard library; needs network access to api.crossref.org, api.openalex.org and export.arxiv.org.
metadata:
  version: "1.0"
  category: literature-review
  maintainer: Kalaris Labs
  author: Kalaris Labs (Sayan Chowdhury)
  tags: citations, hallucination, DOI, Crossref, OpenAlex, arXiv, references, research integrity
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
```

Each entry gets a status:

| Status | Meaning | Action |
|---|---|---|
| `verified` | Identifier resolves; title/author/year agree | None |
| `found-add-doi` | No DOI in the entry, but an unambiguous match exists | Add the suggested `doi` field |
| `mismatch` | DOI resolves to a *different* work, or year/author disagree | Fix from the record, or find the intended paper |
| `doi-not-found` | DOI does not resolve anywhere | Typo or fabricated: search by title |
| `uncertain` | Title matches but year/author disagree, or only a weak title match | Check manually (reprints, errata, homonymous papers) |
| `not-found` | No plausible match in Crossref, OpenAlex or arXiv | Treat as fabricated until proven otherwise (grey literature, theses and reports may legitimately be absent) |

Exit code `0` means everything is verified or only missing DOIs; `1` means something needs a human.

## Handling the hard cases

- **Conference papers without DOIs** (NeurIPS, ICML, ICLR, many CS venues): the script
  falls back to arXiv. Cite the proceedings version with a `url` to the official
  proceedings page, and optionally keep `eprint` for the arXiv ID.
- **Preprint vs published**: if both exist, cite the peer-reviewed version unless
  the venue asks otherwise. OpenAlex links versions of the same work.
- **Books and chapters**: check ISBN via the publisher or Open Library. Crossref covers many but not all.
- **Datasets and software**: verify DataCite DOIs (`https://api.datacite.org/dois/{doi}`) or
  Zenodo/Software Heritage identifiers.
- **Retractions**: check each DOI against Retraction Watch data (in Crossref as
  `update-to` / `relation` metadata) and never cite a retracted paper as support.
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
