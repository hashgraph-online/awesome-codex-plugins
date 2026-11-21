# Citations and number lineage

The report's authority rests on two things: the reader can check anything you assert, and no number is invented.

## 1. Inline markers

Put `[S1]`, `[S2]` … immediately after the claim they support, inside the sentence, before the closing punctuation.

> Plan A costs 1.2bn KRW, 33% more than plan B [S2].

Rules:

- One marker may support one sentence, not a paragraph. A paragraph of unsourced sentences is a paragraph of unsourced claims.
- A general statement that is common knowledge needs no marker; a specific number, date, name, quote, or comparison always does.
- The marker sits after the claim, not before it, and not in a footnote at the end of the page.
- The number is a function of the source list order, so inserting a source in the middle renumbers every marker after it. Fill sources first, markers last, or accept the renumber.

## 2. Number lineage

Every number carries one of three labels, and the label is visible at authoring time even if it is not printed:

| Label | Meaning | How to write it |
|---|---|---|
| measured | Computed here from data this run touched | Show the calculation and its input, in the source or a companion file |
| sourced | Taken from a named source | Marker to the source list |
| estimated | A judgement with a stated basis | Say what it is based on, in the sentence |

A derived number shows its formula and its inputs. "$4.1M annualised" with no formula is a claim, not a number.

When two sources disagree, keep both and say so. A reconciled number that hides the disagreement is worse than two numbers the reader can weigh.

## 3. The source list

The source list is the last section of the report, and it is a table.

| Marker | Source | Retrieved |
|---|---|---|
| S1 | Title of the document, publisher, URL | 2026-11-13 |
| S2 | Internal: Q3 finance export, file name, sheet | — |

Rules:

- Every marker in the body appears here, and every row here is cited at least once. An uncited row is a source you read but did not need; delete it or cite it.
- A retrieved source carries the date it was actually opened. A date you did not verify is worse than no date.
- An internal file names the file and, when it is a workbook or a database, the sheet or table.
- A person's statement names the role and the date, not just the name. `Head of Ops, interview 2026-11-04` beats `김민수`.
- No source you did not open. A search snippet, a summary, or a model's recollection is a lead, not a source.

## 4. Quotes

A quote is verbatim or it is a paraphrase, never in between.

- Verbatim quotes keep their original language and their original punctuation. Rendering the quote translation beside it is allowed; silently translating it is not.
- A paraphrase uses no quotation marks and no words from the source that would imply a quote.
- A quote longer than three lines is cut down or moved to an appendix. A report is not a clipping service.

## 5. What fails the check

Blocking:

- A marker with no matching row.
- A row with no matching marker.
- A specific number with no marker, no measurement, and no estimate label.
- A quote attributed to a source that does not contain it.

Advisory:

- A source without a retrieval date, when the source is an internal file.
- A source whose retrieval date is older than a year, when the claim is about a current state.
- Two markers for the same claim when one would do.

## Sources

> Checked 2026-11-13.

| Claim | Source |
|---|---|
| Source grades, the reviewed-versus-cited split, and the requirement that a snippet is a lead rather than a source | `instructions/sourcing/reliable-search.md` |
| Number lineage labels and the derived-number formula requirement | `instructions/sourcing/reliable-search.md` and the citation contract in `instructions/validation/index.md` |
| Verbatim quotation preserving the source language | This package's contract, consistent with the report language rule in `SKILL.md` |