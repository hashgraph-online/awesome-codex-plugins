# Search, retrieval, and query craft

How to find the right documents, and how to avoid the three ways Paperclip queries commonly go wrong:
searching the wrong source, writing a keyword-shaped query for an embedding model, and using SQL as
if it were full-text search.

Examples omit the auth prefix. Every real invocation needs it, because shell state does not survive
between tool calls: `[ -f .env ] && { set -a; . ./.env; set +a; }; paperclip <command>`. All search
and lookup flags documented here were executed against 0.7.15.

## Sources

`-s` is mandatory on every search. Omitting it prints this list and exits non-zero.

| Flag | Contents |
|---|---|
| `-s pmc` | PubMed Central full text (~7.7M documents) |
| `-s arxiv` | arXiv preprints (~3.0M) |
| `-s biorxiv` | bioRxiv preprints (~400K) |
| `-s medrxiv` | medRxiv preprints (~86K) |
| `-s papers` | All four paper corpora at once |
| `-s abstracts` | Abstract-only corpus — much broader, no full text |
| `-s fda` | US FDA regulatory documents |
| `-s fda/jp` | Japan PMDA |
| `-s fda/eu` | EU EMA / EPAR |
| `-s trials` | All trial registries |
| `-s trials/us` | ClinicalTrials.gov |
| `-s trials/eu` | EudraCT, CTIS, ISRCTN |
| `-s trials/jp` | UMIN, jRCT |
| `-s trials/cn` | ChiCTR |
| `-s proteins` (alias `-s uniprot`) | UniProt + PDB + ChEMBL |
| `-s clipboard` | Your own uploaded documents |

Combine with commas — `-s pmc,biorxiv,medrxiv` — or use a virtual directory instead of the flag:

```bash
paperclip search "pembrolizumab" /fda/us
paperclip search "breast cancer" /trials/us
```

Counts above come from `paperclip sql "SELECT source, COUNT(*) FROM documents GROUP BY source"` on
2026-07-27; they grow monthly.

### Choosing

- General biomedical literature → `-s pmc`.
- User said "trials", "regulatory", "FDA", "label" → the matching flag or directory.
- Recent, not-yet-peer-reviewed work → `-s biorxiv` or `-s medrxiv`.
- ML/methods work → `-s arxiv`.
- Need breadth over depth, willing to lose full text → `-s abstracts`.
- Proteins, drugs, compounds, structures → **ask first** whether the user wants structured records
  (`-s proteins`) or papers about the topic (`-s pmc`). They are different answers.

When several sources are genuinely needed, run separate targeted searches rather than one broad one —
the ranking is per-source and the results are easier to reason about.

## Search options

| Option | Notes |
|---|---|
| `-n, --limit N` | Default is small. Use `-n 5`/`-n 10` before `map`, higher before `filter` |
| `-e, --exact` | Exact phrase |
| `--since DATE` | Documents after a date |
| `--sort relevance\|date` | `date` for "what's new", `relevance` otherwise |
| `--author`, `--journal`, `--year` | Metadata narrowing |
| `--ranking hybrid\|bm25\|vector\|analogical` | See below |
| `--corpus` | Ignore an active repo's scope during discovery |

### Ranking modes

- `hybrid` (default) — semantic plus keyword. Correct for almost everything.
- `bm25` — pure lexical. Use for exact terminology, gene symbols, catalog numbers.
- `vector` — pure semantic. Use when vocabulary varies but the topic is fixed.
- `analogical` — matches papers sharing a *structural method* across unrelated fields. Requires a
  descriptive query; a keyword string produces nothing useful.

## Writing the query

The query is embedded with a model fine-tuned on paper abstracts. Give it abstract-shaped text.

1. **Best — a full abstract.** If the user has a reference paper, read it and paste the whole
   abstract as the query. This is exactly what the model was trained on.
2. **Good — one or two sentences describing the method or problem.** Say what the work *does*, not
   what it is *about*: "correcting for systematic under-reporting in training data where the
   missingness mechanism is unknown".
3. **Good — the problem in plain language.** "My training labels are unreliable because some
   positives are systematically recorded as negatives" surfaces positive-unlabeled learning work
   across NLP, biology, and cosmology.
4. **Weak — bare keywords.** "CRISPR delivery nanoparticle" returns topically adjacent papers. Fine
   for `hybrid`, useless for `analogical`.

### Analogical search worked example

```bash
# From a known paper: read it, then use its abstract as the query
paperclip cat /papers/PMC1234567/meta.json
paperclip search -s arxiv   --ranking analogical "<full abstract>" -n 10
paperclip search -s biorxiv --ranking analogical "<full abstract>" -n 10

# From a described problem
paperclip search -s arxiv --ranking analogical \
  "I need to approximate an expensive leave-one-out computation cheaply by exploiting low-rank structure in my parameter space" -n 10
```

Run it against each source separately. The useful analogue is usually in the field you would not have
thought to check.

## Reading the results

```text
Found 3 papers  [s_5bcc8044]

  1. Targeted nonviral delivery of genome editors in vivo
     Connor A. Tsuchida, Kevin M. Wasko, Jennifer R. Hamilton, Jennifer A. Doudna
     PMC10945750 · PMC · 2024-03-04
     https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10945750/
     "This paper reviews targeted nonviral delivery methods for CRISPR-Cas genome editors in vivo..."

[304ms, saved to s_5bcc8044]
```

The quoted line is a **generated summary, not an extract**. It is a triage signal only — open the
document and read the lines before you cite anything.

`s_5bcc8044` is the result id. Feed it to `filter`, `map`, or `results`. Recover ids later with
`paperclip results --list`, which shows each id alongside the command that produced it.

### Output shape is nondeterministic

The block above is only one of the two shapes `search` returns. The *same* command, same query, same
redirection target, also returns raw JSON:

```json
{"results_id": "s_e18e2e62", "count": 1, "papers": [{"document_id": "PMC12131857", "source": "pmc",
 "score": 51.81, "backend": "opensearch", "pub_year": 2025, "title": "...", "journal_title": "...",
 "authors": "...", "doi": "...", "tldr": "...", "abstract_snippet": "..."}]}
```

Eight identical runs of `paperclip search -s pmc "CRISPR" -n 1` produced a mix of both. It does not
correlate with piping, redirection, or `--json`: forcing `--json` produced JSON 0/8 times, and
`lookup --json` returns rendered text too.

So **do not write a parser against `search` output.** What is reliable:

| Need | Reliable route |
|---|---|
| The result id | `grep -oE 's_[a-f0-9]{8}' \| head -1` — matches both shapes |
| Per-paper structured rows | `paperclip results <id> --save out.csv` → stable header `title,authors,id,source,date,url,abstract` |
| One document's metadata | `paperclip cat /papers/<id>/meta.json` — a file read, always JSON |

Rendered output additionally carries ANSI colour codes; strip with `sed $'s/\033\\[[0-9;]*m//g'`.

## `filter` — trim before you spend LLM calls

```bash
paperclip search -s fda "semaglutide" -n 50
paperclip filter --from s_abc123 "semaglutide cardiovascular outcomes"
paperclip map --from s_abc123 "What were the primary endpoints and results?"
```

`filter` **overwrites the result set in place** — the id stays the same and the discarded results are
gone. If `--require N` cannot be satisfied, widen the original search for a fresh id; filtering an
already-filtered set will not bring anything back.

## `lookup` — exact metadata match

No ranking, no semantics. Use when the user already identified the document.

```bash
paperclip lookup doi 10.1101/2024.01.15.575613
paperclip lookup pmc PMC7194329
paperclip lookup pmid 32943797
paperclip lookup arxiv 2403.03507
paperclip lookup author "James Zou" -n 10
paperclip lookup journal "Nature Medicine"
paperclip lookup title "CRISPR base editing" --json
```

`--json` is accepted but was observed returning rendered text rather than JSON. Do not depend on it —
see *Output shape is nondeterministic* below.

Fields: `doi`, `author`, `title`, `abstract`, `source`, `date`, `pmc`, `pmid`, `arxiv`, `journal`,
`publisher`, `type`, `keywords`, `category`, `license`, `year`, `volume`, `issue`, `issn`.

## `grep` — the real full-text search

This is the tool for "which papers mention X". It scans document bodies, so it finds mentions in
Methods, Results, Data Availability, and reference lists that abstract-level search never sees.

```bash
paperclip grep -l "SLC30A8" /papers/                 # corpus-wide, filenames only
paperclip grep -n "lipid nanoparticle" /papers/PMC10945750/content.lines
paperclip grep -c "CRISPR" /papers/PMC12345/content.lines
paperclip grep -A 3 -B 1 "IC50" /papers/PMC12345/content.lines
paperclip grep -i -e "off-target" -e "offtarget" /papers/PMC12345/content.lines
paperclip grep "TP53" /proteins/
```

Corpus-wide output groups matched paragraphs by document and returns a result id:

```text
Matched 80 paragraphs across 80 papers [results_id: s_a5590fe3]

  arx_1312.6639/ (1 matches)
    …rs13266634SLC30A8C/CC/C  rs1153188DCDT/TT/A…
```

Two behaviors worth knowing:

- The corpus scan is **time-bounded**. A no-match result prints
  `bounded scan — re-run with --exhaustive for a full-timeout scan`. For a rare term, do that before
  concluding it is absent.
- Line numbers in the output come from the `L<n>` prefixes stored in the file, so `-n` output can be
  cited directly.

## `scan` — several patterns, one pass

```bash
paperclip scan /papers/PMC12345/content.lines "CRISPR" "off-target" "efficiency"
paperclip scan -i -C 3 /papers/PMC12345/content.lines "IC50" "EC50" "dose"
```

Results are grouped by pattern with context. Prefer this to three sequential greps.

## SQL

**SQL is for counting and grouping, never for finding papers by content.** It sees titles and
abstracts only, and `ILIKE '%term%'` is an unindexed scan. A paper whose Methods mention your term
will not appear.

```bash
paperclip sql "SELECT source, COUNT(*) AS n FROM documents GROUP BY source"
paperclip sql "SELECT pub_year, COUNT(*) AS n FROM documents
               WHERE title ILIKE '%CRISPR%' GROUP BY pub_year ORDER BY pub_year DESC LIMIT 10"
```

Constraints: `SELECT` only, 15 s timeout, 200-row cap.

### `documents` columns

`id`, `title`, `doi`, `authors`, `source`, `abstract_text`, `pub_date`, `pub_year`, `journal_title`,
`article_type`, `pmid`, `keywords`, `categories`.

`paperclip sql --help` describes a lower-level view of the same store with `document_id`, `month_year`,
`created_at`, plus `content_blocks` (`document_id`, `line_number`, `content`, `section`, `block_type`,
`citation_info`) and `figures` (`document_id`, `graphic`, `source_path`). Both column vocabularies are
accepted; the server normalizes them, and a `pub_year` projection may come back labelled `pub_date`.
Do not depend on the header string — alias explicitly:

```bash
paperclip sql "SELECT pub_year AS year, COUNT(*) AS n FROM documents GROUP BY pub_year ORDER BY year DESC LIMIT 5"
```

### Protein SQL

```bash
paperclip sql -s proteins "SELECT COUNT(*) FROM uniprot_v.proteins"
paperclip sql -s proteins "SELECT * FROM pdb_v.structures_by_accession WHERE accession='P00533' LIMIT 10"
paperclip cat /proteins/P04637/meta.json
```

Key views: `uniprot_v.proteins`, `uniprot_v.features`, `pdb_v.structures_by_accession`,
`chembl_v.bioactivities_by_accession`, `chembl_v.drugs_by_accession`. The join key throughout is the
UniProt accession.

**Run `paperclip skills show proteins` before writing any protein query.** Column names, enum values,
and join semantics are not guessable, and a guessed query returns plausible wrong answers rather than
an error. There are further protein workflows in `paperclip skills`: `domain_map`, `ptm`,
`catalytic_residues`, `sequence_analysis`, `experimental_methods`.

## Decision table

| Question | Tool |
|---|---|
| "Papers about X?" | `search -s pmc "X"` |
| "Which papers mention X?" | `grep "X" /papers/` |
| "This DOI/PMID/arXiv id" | `lookup` |
| "How many papers per year on X?" | `sql` |
| "Papers like this one, other fields" | `search --ranking analogical "<abstract>"` |
| "Exact phrase / gene symbol" | `search -e` or `--ranking bm25`, or `grep -F` |
| "Everything in this one paper about X" | `scan` or `grep` on its `content.lines` |
