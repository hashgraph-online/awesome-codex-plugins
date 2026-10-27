---
name: ontology-term-resolution
description: Resolve free-text scientific labels to ontology term IDs and validate existing CURIEs against the EBI Ontology Lookup Service (OLS4). Also look up prefixes in Bioregistry, resolve compact identifiers via Identifiers.org, map lab shorthand with ZOOMA, and build Ontobee term pages. Use whenever an ontology identifier must be produced or checked - annotating tissue, cell type, disease, phenotype, assay, chemical, organism, sex, or developmental stage fields; preparing metadata for GEO, ENA, BioSamples, CELLxGENE, HCA, or ISA-Tab submission; auditing a metadata table of term IDs; checking whether a term is obsolete and what replaced it; or deciding HPO vs HP. Triggers include "ontology term", "ontology ID", "CURIE", "controlled vocabulary", "UBERON", "CL:", "MONDO", "HPO", "EFO", "ChEBI", "NCBITaxon", "GO term", "PATO", "Zooma", "Bioregistry", "Identifiers.org", "Ontobee", "annotate this tissue/cell type/disease", and any request to emit or verify an identifier shaped like PREFIX:0001234.
license: MIT
compatibility: Requires Python 3.11+. Scripts use only the standard library - no third-party packages. Needs network access to https://www.ebi.ac.uk/ols4, https://bioregistry.io, https://resolver.api.identifiers.org, and https://www.ebi.ac.uk/spot/zooma (all public, no API key).
allowed-tools: Read Write Edit Bash
metadata:
  version: '1.2'
  category: scientific-databases
  maintainer: Kalaris Labs
  tags: ontologies, CURIEs, OLS, metadata annotation, FAIR data
---

# Ontology Term Resolution

## When to use

Any time an ontology identifier is about to be written down or trusted: annotating a metadata
column, filling a submission template, auditing a table someone else produced, or checking whether
an ID in an old file is still current.

## The rule

**Never write an ontology ID from memory, and never accept one without checking it.**

Ontology IDs are memorable in form and arbitrary in detail. A plausible-looking `UBERON:0002108`
is a real term (small intestine) that is not the liver, and nothing downstream will catch the
substitution — the ID is well-formed, the ontology is right, and the metadata is silently wrong.
Reviewers cannot spot it either, which is why these errors persist into published datasets.

Every ID this skill emits comes from a live OLS lookup. Every ID it is handed gets verified.
Bioregistry, Identifiers.org, ZOOMA, and Ontobee answer prefix, landing-page, and shorthand
questions — they do not replace that OLS check.

## Which service

| Question | Script | Authority |
| --- | --- | --- |
| What is the term for "left ventricle"? | `scripts/resolve_terms.py` | OLS |
| OLS missed lab shorthand (`PBMC`, `WT`) | `scripts/map_terms.py`, then `validate_terms.py` | ZOOMA proposes; OLS decides |
| Is `EFO:0001067` real, current, correctly labelled? | `scripts/validate_terms.py` | OLS |
| Is `HPO` a real prefix? Does `HP:notanid` match the pattern? | `scripts/lookup_prefix.py` | Bioregistry |
| Which landing page should this CURIE open? | `scripts/lookup_prefix.py` | Identifiers.org + Ontobee URLs |

All four scripts take single values or files, emit TSV or JSON, and need no packages beyond the
standard library. Full traps for the non-OLS services are in `references/companion-apis.md`.

## Resolve text to terms

```bash
cd skills/ontology-term-resolution/scripts

# one string, constrained to the ontology that should define it
python3 resolve_terms.py "liver" --ontology uberon
```

```
query   rank  curie           label  ontology  match_type   strategy  defining_ontology
liver   1     UBERON:0002107  liver  uberon    exact_label  exact     true
```

```bash
# a column of tissue names; anything not an exact hit is reported, not guessed
python3 resolve_terms.py --input tissues.txt --ontology uberon \
    --exact-only --format tsv -o resolved.tsv

# accept fuzzy fallbacks, then review the partial hits by hand
python3 resolve_terms.py "left ventrical of heart" --ontology uberon --top 3
```

The search escalates `exact` (label and synonym) → `token` → `fulltext` and stops at the first
strategy that returns anything, reporting which one fired. `--exact-only` disables the ladder.
`--branch UBERON:0000465` restricts candidates to descendants of a term.

**Read `match_type` before using a result.** `exact_label` and `exact_synonym` are safe;
`partial` means OLS returned its best guess for a string that does not exist as written, and
needs a human decision. `unresolved` is a legitimate output — see `references/curation-rules.md`
for the normalisations worth retrying first.

## Validate existing IDs

```bash
python3 validate_terms.py UBERON:0002107 EFO:0001067 UBERON:9999999
```

```
id              status     actual_label                  ontology  replacement     detail
UBERON:0002107  ok         liver                         uberon
EFO:0001067     obsolete   obsolete_parasitic infection  efo       MONDO:0005135   obsolete; replaced by MONDO:0005135
UBERON:9999999  not_found                                                          no such term in the ontology this prefix names
```

Exit code is 1 if anything failed, 0 otherwise, 2 on usage or network trouble — so it works as a
CI gate on a metadata file:

```bash
# id + label columns; catches IDs that exist but are labelled as something else
python3 validate_terms.py --input metadata.tsv --strict

# a tissue column must hold UBERON anatomical entities and nothing else
python3 validate_terms.py --input tissue_ids.tsv \
    --branch UBERON:0000465 --expect-ontology uberon
```

| Status | Meaning | Verdict |
| --- | --- | --- |
| `ok` | Exists, current, consistent with everything asserted | pass |
| `matched_synonym` | Claimed label is a synonym; primary label differs | warn |
| `imported_only` | Home ontology no longer asserts this ID | warn |
| `not_a_class` | Term is a property or individual | warn |
| `not_found` | No such term | fail |
| `obsolete` | Obsoleted; `replacement` gives the successor when one exists | fail |
| `label_mismatch` | ID and claimed label describe different things | fail |
| `wrong_ontology` | Right kind of ID, wrong ontology for this column | fail |
| `wrong_branch` | Not a descendant of the required root | fail |
| `malformed_curie` | Not of the form `PREFIX:local` | fail |

`--strict` promotes warnings to failures.

## Check a prefix or compact identifier

```bash
python3 lookup_prefix.py HP HPO HP:0001250 HPO:0001250
```

```
query        status          preferred_prefix  canonical_curie  pattern    detail
HP           ok              HP                                 ^\d{7}$
HPO          synonym_prefix  HP                                 ^\d{7}$    'HPO' is a synonym of preferred prefix HP
HP:0001250   ok              HP                HP:0001250       ^\d{7}$
HPO:0001250  synonym_prefix  HP                HP:0001250       ^\d{7}$    'HPO' is a synonym of preferred prefix HP
```

Bioregistry accepts synonym prefixes. Identifiers.org does not — `HPO:0001250` is HTTP 400.
Rewrite to the preferred prefix before handing a CURIE to OLS. Landing-page columns come from
Bioregistry mappings (`providers.miriam`, `mappings.ontobee`), not from templating that
preferred prefix: `ORPHA:558` is a 400, `orphanet:558` is a 200, and OBA has no Identifiers.org
namespace at all. Empty cells mean the service does not host the prefix. This script does
**not** say the term exists; that is still `validate_terms.py`.

## Map lab shorthand (ZOOMA)

```bash
# after resolve_terms.py returned unresolved / partial
python3 map_terms.py PBMC --ontology cl --exact-only
```

`--ontology` is required. Unfiltered ZOOMA annotate returns FOODON, XAO, and BTO alongside UBERON
for `liver`, all at HIGH confidence. HIGH/GOOD hits are candidates only — run `validate_terms.py`
on every CURIE before writing it down.

## API behaviour that will mislead you

These are verified against the live service and are the reason this skill ships scripts rather
than a recipe. Full detail in `references/ols4-api.md`.

| Trap | Consequence |
| --- | --- |
| `exact=true` is exact **token** matching | `liver` returns 161 hits in UBERON; adding `queryFields=label` returns 1 |
| `/search` never returns `is_obsolete` or `term_replaced_by` | Named in `fieldList` they are dropped silently; only term detail can answer "is this ID still current" |
| `ontology=efo` returns MONDO and CL hits | Ontologies import each other; filter on the CURIE prefix yourself |
| The same term appears once per importing ontology | Deduplicate on `obo_id`, keep `is_defining_ontology: true` |
| The `obo_id` index has holes | `MONDO:0000001` is live but unindexed by `obo_id`; an IRI fallback is required to avoid a false `not_found` |
| IRIs are not all OBO PURLs | EFO and Orphanet use their own namespaces — resolve IRIs, do not template them |
| OxO is retired | Returns HTML with HTTP 200; use term cross-references or SSSOM instead |
| A branch check does not exclude cell types from anatomy | CARO puts `cell` under `anatomical structure`; constrain the prefix too |
| ZOOMA without an ontology filter | `liver` returns 100+ HIGH hits across FOODON, XAO, BTO, UBERON |
| Identifiers.org synonym prefixes | `HPO:0001250` is HTTP 400; Bioregistry accepted the same CURIE |
| Identifiers.org encoded colon | `HP%3A0001250` is HTTP 400; the path must keep `:` |
| Bioregistry `preferred_prefix` is not the Identifiers.org namespace | `ORPHA:558` is 400; `orphanet:558` is 200. `hp:0001250` and `chebi:15377` are 400 because those namespaces embed the prefix in the LUI. Use `providers.miriam` from `/api/reference/{CURIE}`; omit the URL when that mapping is missing (OBA, XAO, ECTO) |
| Ontobee search | HTML page only — no JSON API; do not scrape it |

## Choosing the ontology

MONDO for disease, HP for phenotype, UBERON for tissue, CL for cell type, EFO for assay, ChEBI for
compounds, NCBITaxon for organism, PATO for sex and for `normal`. Prefix-to-OLS-id mappings (`HP`
is served as `hp`, `Orphanet` as `ordo`), branch roots for `--branch`, and the overlapping-ontology
judgement calls are in `references/ontology-registry.md`.

## Reporting results

Give the ID **and** the label, and say how each was matched. A table of bare IDs cannot be
reviewed. State unresolved terms explicitly rather than filling them with the nearest hit.

## References

- `references/ols4-api.md` — endpoints, parameters, response fields, and every verified OLS trap.
- `references/companion-apis.md` — Bioregistry, Identifiers.org, ZOOMA, and Ontobee: when to use
  each, and the traps that make an unfiltered or synonym-prefix call look successful.
- `references/ontology-registry.md` — prefix/ontology-id table, branch roots, which ontology owns
  which concept.
- `references/curation-rules.md` — candidate-selection procedure, normalisations to retry,
  auditing an existing table, obsolete terms, cross-ontology mapping.

## Agent operating procedure

1. **Check the environment.** Confirm network access, API keys (if required) and the database's current API documentation and rate limits.
2. **Pin down the inputs.** Confirm formats, identifiers and parameters from the data or the user. Ask rather than guess any value that changes the result.
3. **Run a small version first.** Fetch a single known record and check the response format before bulk queries.
4. **Execute the full task** using the instructions and references above.
5. **Validate the result.** Identifiers resolve, record counts are reported, and the database version or access date is recorded.
6. **Report.** State what was run (versions, commands, parameters), what was checked, and what is still uncertain.

| If this happens | Do this |
|---|---|
| HTTP 429 or 5xx errors | Respect rate limits with backoff, batch requests, and report partial results honestly. |
| A function, flag or endpoint in these instructions is missing in the installed version | Check the installed version's own documentation (`help()`, `--help`, official docs), adapt, and tell the user. Never invent an API. |
| A required input, identifier or parameter is ambiguous | Ask the user, or state the assumption explicitly before running. |

**Integrity rules**

- Never fabricate results, parameters, identifiers, citations or statistics. If something cannot be run or verified, say so plainly.
- Never invent accession numbers, IDs or records; report 'not found' instead.
- Treat version-specific details here as possibly outdated: confirm them against the official documentation for the installed version.
- Ask before actions that cost money, consume shared GPUs or cloud quota, touch personal or patient data, or cannot be undone.
