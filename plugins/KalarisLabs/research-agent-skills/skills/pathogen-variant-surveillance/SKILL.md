---
name: pathogen-variant-surveillance
description: Query live pathogen genomic surveillance data through the GenSpectrum LAPIS API to find which viral lineages are circulating now, how fast they are growing, and what mutations they carry. Use whenever a question depends on the current state of a pathogen population rather than on remembered facts - which SARS-CoV-2 variant is dominant, whether a Pango lineage is still designated or has been withdrawn, what clade or genotype of H5N1 is in a host or region, whether a PCR primer or assay target still matches circulating sequence, or how a lineage's prevalence has moved week to week. Triggers include "variant surveillance", "genomic surveillance", "what variant is circulating", "dominant variant", "Pango lineage", "lineage prevalence", "growth advantage", "SARS-CoV-2 variant", "XFG", "clade 2.3.4.4b", "H5N1 genotype", "influenza clade", "RSV/mpox/measles/dengue lineage", "CoV-Spectrum", "LAPIS", "Nextclade", "pango-designation", and any request to report what a pathogen population looks like today.
license: MIT
compatibility: Requires Python 3.11+. Scripts use only the standard library - no third-party packages. Needs network access to the public GenSpectrum LAPIS instances (lapis.cov-spectrum.org, lapis.genspectrum.org, lapis.pathoplexus.org) and to raw.githubusercontent.com for pango-designation. No API key.
allowed-tools: Read Write Edit Bash
metadata:
  version: '1.1'
  category: life-sciences
  maintainer: Kalaris Labs
  last-reviewed: '2026-07-27'
  tags: pathogen genomics, genomic surveillance, viral lineages, epidemiology
---

# Pathogen Variant Surveillance

## When to use

Any time an answer depends on what a pathogen population looks like **now**: which lineages are
circulating, whether one is growing, what a lineage name currently means, or whether an assay
target still matches.

## The rule

**Never state what is circulating, and never write a lineage name, from memory.**

Three things go wrong at once, and only the first is an ordinary knowledge-cutoff problem:

1. **Names post-date training.** The Pango designation list carries over 6,200 names and grows
   continuously.
2. **The nomenclature is a live data structure, not a convention.** `XFG` is a recombinant that
   only resolves through `alias_key.json`; `PQ.17` unaliases to `XDV.1.5.1.1.8.1.17`. Neither
   expansion is derivable by reasoning — the mapping is a file that changes.
3. **Prior knowledge gets retracted, not just outdated.** 294 names in the current
   `lineage_notes.txt` are withdrawn or redesignated. `PC.2` is now `LF.7.9`; `XFG.20` was
   withdrawn outright. A remembered lineage fact is not merely stale, it can be actively wrong.

Every number this skill reports is a count returned by a live instance, stamped with the data
version it came from.

## Scope

Surveillance data analysis for research. This skill describes sequences that were collected and
submitted; it does not produce clinical interpretations, outbreak-response recommendations, or
public-health guidance, and sequence counts are not case counts.

## Instances

One API shape covers every pathogen. `--instance` names a verified deployment; `--base-url`
reaches any other LAPIS instance.

| Instance | Host | Lineage column | Indexed |
| --- | --- | --- | --- |
| `sars-cov-2` | lapis.cov-spectrum.org (open GenBank data) | `pangoLineage` | yes |
| `h5n1`, `h3n2`, `h1n1pdm`, `influenza-a` | lapis.genspectrum.org | `clade` | no |
| `rsv-a`, `rsv-b`, `mpox`, `measles`, `dengue`, `west-nile`, `hmpv`, `ebola-zaire`, `ebola-sudan`, `cchf` | lapis.pathoplexus.org | varies | varies |

**Field names differ per instance and are never assumed.** Every script reads
`/sample/databaseConfig` at run time and picks the collection-date, submission-date and lineage
columns from what the instance actually declares. `dateFrom=` is correct on SARS-CoV-2 and a hard
400 on H5N1, whose collection date is `sampleCollectionDateRangeLower`.

## Scripts

```bash
cd skills/pathogen-variant-surveillance/scripts
```

| Script | Question answered |
| --- | --- |
| `resolve_lineage.py` | Does this name still exist, what does it expand to, what is it descended from? |
| `lineage_prevalence.py` | What share of sequences is this lineage, week by week, and is it growing? |
| `mutation_profile.py` | What mutations does it carry, and how does it differ from another lineage? |
| `reporting_lag.py` | How far back does the data have to go before it can be trusted? |

All four take `--format table|tsv|json` and print provenance (instance, data version, resolved
field names, filters) to stderr, so `> out.tsv` keeps the data clean and the provenance visible.

### Start from the data, not from a remembered list

```bash
# no names: discover what is actually circulating in the window
python3 lineage_prevalence.py --top 5 --where country=USA --weeks 12
```

> note: discovered the 5 most common pangoLineage values in the window:
> XFG.1.1, XFG.23.1.3, PY.1.1.1, XFJ.3.1.2, PQ.17

This is the right first command for "what is circulating". Naming lineages up front presumes you
already know which ones matter, which is the assumption this skill exists to remove.

### Check a name before using it

```bash
python3 resolve_lineage.py XFG.23.1.3 PQ.17 PC.2 NOTALINEAGE
```

```
query        status     unaliased                        parent    recombinant_of  descendants  sequences  detail
XFG.23.1.3   current    XFG.23.1.3                       XFG.23.1  LF.7+LP.8.1.2   6            317        S:A1174V, on C29137T branch
PQ.17        current    XDV.1.5.1.1.8.1.17               NB.1.8.1                  23           931        Alias of XDV.1.5.1.1.8.1.17
PC.2         withdrawn  B.1.1.529.2.86.1.1.16.1.7.2.1.2  LF.7.2.1                  4            25         now LF.7.9; Redesignated as LF.7.9
NOTALINEAGE  unknown    NOTALINEAGE                                                0            n/a        no such name in the live nomenclature
```

(`detail` abridged; each real row also cites the lineage proposal it came from.)

Exit code is 1 if any name is withdrawn or unknown, so it gates a manuscript's lineage list.
Note `PC.2`: withdrawn upstream, yet 25 sequences still carry the label because the instance's
assignments lag designation. Both facts are true and both matter.

### Prevalence and growth

```bash
python3 lineage_prevalence.py "XFG.1.1*" "XFJ*" --where country=USA --weeks 16 --growth
```

```
lineage   week        n   total  proportion  ci_low  ci_high  coverage
XFG.1.1*  2026-05-04  42  80     0.5250      0.4170  0.6308   ok
XFG.1.1*  2026-06-15  3   49     0.0612      0.0210  0.1652   ok
XFG.1.1*  2026-06-29  1   30     0.0333      0.0059  0.1667   low
XFG.1.1*  2026-07-13  0   0                                   low
```

Proportions carry Wilson intervals because surveillance weeks are small. Weeks whose denominator
has not filled in yet are flagged `low` and excluded from the growth fit unless
`--include-incomplete`.

The window is widened to whole ISO weeks, and says so when it does. A window starting mid-week
would give a first row covering three days and a last row covering four, neither comparable to the
full weeks between them.

`--growth` reports a weighted least-squares slope of log-odds against time. It is **descriptive**:
it absorbs every change in who is sequencing, where, and how fast they report. It is not a fitness
or transmissibility estimate. No slope is printed for a lineage with too few observations — see the
trap table for why that guard exists.

### Mutations, and whether an assay still matches

```bash
python3 mutation_profile.py "XFJ*" --versus "XFG*" --gene S --since 2026-01-01
```

```
mutation  gene  position  verdict  prop_a  prop_b  n_a  n_b
S:L441R   S     441       gained   1.000   0.000   66   0
S:A475V   S     475       gained   1.000   0.000   68   0
S:K444R   S     444       lost     0.000   0.996   0    5031
S:Q493E   S     493       lost     0.000   0.998   0    5359
```

Works the same on a segmented genome — `--instance h5n1 --gene HA` or `--gene seg4`. Use
`--nucleotide` for primer and probe questions, where the codon is not the unit that matters.

### Decide how far back to trust

```bash
python3 reporting_lag.py --where country=USA
```

```
lag_days  mean_complete  min_complete  max_complete  cohorts
14        0.456          0.332         0.557         6
30        0.677          0.580         0.822         6
60        0.868          0.802         0.949         6
90        0.939          0.916         1.000         6
```

> 90% of a cohort has arrived by 90 days. Trust collection dates up to 2026-04-28; treat anything
> later as provisional.

Run this **before** quoting any recent prevalence. The curve differs sharply by pathogen and
country: on H5N1 the same measurement returns 0% complete at 14 days and 15% at 30 days, so a
"current" H5N1 picture is effectively blind for two months.

## Traps that produce silently wrong answers

All verified against the live API on 2026-07-27. These are why this skill ships scripts rather
than a recipe; full detail in `references/lapis-api.md`.

| Trap | Consequence |
| --- | --- |
| A bare lineage name excludes its descendants | `pangoLineage=XFG` returns 4 sequences; `XFG*` returns 640 |
| A trailing `*` needs a lineage index | On H5N1 `clade=2.3.4.4b` returns 62,413 and `clade=2.3.4.4b*` returns **0** — the same syntax, the opposite meaning |
| Field names are per-instance | `dateFrom` is a 400 on H5N1; the collection date is `sampleCollectionDateRangeLower` |
| Only `date`-typed fields take ranges | H5N1 types `sampleCollectionDate` as a string, so it has no `From`/`To` keys at all |
| Recent weeks are not a sample of what circulated | They are a sample of whoever reports fastest; only 29% of a US cohort arrives within 7 days |
| LAPIS roots recombinants | Asking it for `XFG`'s parents returns nothing; only `alias_key.json` records `XFG = LF.7 + LP.8.1.2` |
| Withdrawn names persist in the data | `PC.2` was redesignated `LF.7.9` upstream while sequences still carry `PC.2` |
| An unknown name fails loudly only when indexed | Indexed columns reject a typo with a 400; unindexed columns answer `0` |
| Mutation `proportion` is over `coverage` | Not over all matching sequences — a poorly covered site can show 1.000 on very few reads |
| `/sample/aggregated` rejects `limit`/`orderBy` | The result has no inherent ordering; sort client-side |

## Reporting results

State the instance, the data version, the filters, and the window — a prevalence figure without
them cannot be reproduced, because the underlying database changes daily. Give counts alongside
proportions, quote the interval, and say explicitly when a window is too recent to support an
estimate. "No reliable estimate for the last six weeks" is a legitimate and often correct answer.

## References

- `references/lapis-api.md` — endpoints, filter grammar, per-instance schema differences, the
  instance registry, and every verified trap in full.
- `references/lineage-nomenclature.md` — Pango aliases and recombinants, designation churn,
  Nextstrain clades, WHO labels, influenza clades, H5N1 clades and genotypes, and how the naming
  systems map onto each other.
- `references/surveillance-caveats.md` — reporting lag, sampling and ascertainment bias, choosing
  a denominator, interval and growth interpretation, and the conclusions this data cannot support.

## Agent operating procedure

1. **Check the environment.** Confirm tool versions, the reference genome/annotation build and the input formats (FASTQ, BAM, VCF, h5ad).
2. **Pin down the inputs.** Confirm formats, identifiers and parameters from the data or the user. Ask rather than guess any value that changes the result.
3. **Run a small version first.** Run the pipeline on a small subset (one sample, one chromosome, a few thousand cells) first.
4. **Execute the full task** using the instructions and references above.
5. **Validate the result.** Check QC metrics, sample identities, genome build consistency and batch effects before interpreting results.
6. **Report.** State what was run (versions, commands, parameters), what was checked, and what is still uncertain.

| If this happens | Do this |
|---|---|
| Genome builds or identifiers do not match between inputs | Stop and harmonize (liftover, ID mapping) before continuing. |
| A function, flag or endpoint in these instructions is missing in the installed version | Check the installed version's own documentation (`help()`, `--help`, official docs), adapt, and tell the user. Never invent an API. |
| A required input, identifier or parameter is ambiguous | Ask the user, or state the assumption explicitly before running. |

**Integrity rules**

- Never fabricate results, parameters, identifiers, citations or statistics. If something cannot be run or verified, say so plainly.
- Do not interpret biological significance beyond what the statistics support; report multiple-testing correction.
- Treat version-specific details here as possibly outdated: confirm them against the official documentation for the installed version.
- Ask before actions that cost money, consume shared GPUs or cloud quota, touch personal or patient data, or cannot be undone.
