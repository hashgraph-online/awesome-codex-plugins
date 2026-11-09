# Query Evidence

Use this rule before writing the report and before choosing a terminal. It owns the report shape, the answer-only discipline, the verification the answer needs, and the four terminals in `Result:` line format.

## 1. Answer Only

- Answer the question that was asked. One metric, one grain, one population, one set of filters, one time window.
- No bonus charts, no extra breakdowns, and no extra exploration passes beyond what the question needed. A second grouping, a trend, or a chart appears only when the question names it.
- A question that the data cannot answer is reported as such. Never substitute a related number for the one asked, and never let a convenient column redefine the metric silently. When the metric's definition is ambiguous and changes the answer, stop and ask once instead of picking quietly.
- A cause the data cannot show ("why did sales drop") gets the computed change first and the possible causes as explicitly unverified hypotheses after it.

## 2. Report Shape

Save `.hyper/data/<slug>/report.md`. The answer is first, the evidence after it, and the terminal last:

````markdown
# <Question title>

## Answer

<the number or table that answers the question, in the first lines>

## Question

<one measurable quantity: metric, grain, population, filters, time window>

## Engine and placement

<probe output summary: interpreter, engine and its version, placement decision from `rules/placement.md`>

## Query

```sql
<the exact query text that ran>
```

<row counts: the input rows read, the rows the result holds>

## Handling

<null and duplicate handling for every column the answer depends on>

## Timing and digest

Input: `<file>` (<bytes> bytes, <rows> rows)
Digest: `<sha256>`
Wall-clock: <milliseconds> ms on <machine>

## Cross-check

<headline figure by a second route, agreement or the quantified difference>

Result: answered
````

- The question line names the grain in words: per day, per region, per customer, per order. A total without its grain is not comparable to anything.
- The query is the exact text that ran, copied out of the run, not reconstructed from memory. A row count and a timing that were not measured are marked as not measured.
- The input digest is the SHA-256 of the input file as read. When the input is a table in a database, the digest is the query text plus the number of rows returned; say which one is reported.

## 3. Verification

- Every heavy query reports its row counts and its timing. "It completed" is not evidence; the count and the milliseconds are.
- Cross-check one headline figure by a second route: another table, a raw count, a second engine, or a re-expression of the same query. Name the second source beside the figure and state whether it agrees; quantify any difference.
- When a second source is unavailable, disclose that and leave the cross-check unverified. Never invent agreement.
- A query that errors or produces an unreadable value gets at most two rewrites inside the same question. A third failure ends the run as `blocked` with the failing query and the error.

## 4. Terminals

The report ends with exactly one `Result:` line naming exactly one terminal:

| Terminal | When |
|---|---|
| `answered` | The answer was computed, with row counts, timing, and the input digest in the report |
| `prerequisite_missing` | No usable engine. The missing engine and the install command are reported; nothing is installed |
| `awaiting_input` | One question remains whose answer changes the number: a metric definition, a time zone for a day boundary, or which of two conflicting files is authoritative |
| `blocked` | The data is unreadable, larger than any safe placement, or access is denied |

- `prerequisite_missing` names the missing engine and the install command, but never runs it. A missing engine is a prerequisite, not a failure of the question.
- `awaiting_input` asks one question at a time and names the choice each answer would change. It is used only when a missing definition changes the number and the data cannot settle it.
- `blocked` names the exact blocker: the unreadable file, the size that defeats every placement, or the denied access. A blocker that a different placement could avoid is not `blocked`.
- This skill never commits or pushes. The report is the end of the run.

## Sources

> Checked 2026-11-09.

| Claim | Source |
|---|---|
| Answering only the question asked, with row counts and timing kept beside the result | `dbc-hbin/omp-ulw@74df40f mechanisms/data-analyst/SKILL.md` (mechanism reference, re-authored) |
| Retaining the query, file and input digest, grain, filters, null and duplicate handling, row counts, and timing with the output | `dbc-hbin/omp-ulw@74df40f mechanisms/data-analyst/references/execution-surfaces.md` (mechanism reference, re-authored) |
| Cross-checking one headline figure and disclosing it as unverified when no second source exists | `dbc-hbin/omp-ulw@74df40f mechanisms/data-analyst/references/visualization.md` (mechanism reference, re-authored) |
| The four terminals and the `Result:` line | user instruction, 2026-11-09 (integrator contract) |

### Evidence grade

`LOCAL` - the report shape, the answer-only discipline, and the four terminals are this package's chosen design. The mechanism rows are re-authored from a public repository at a pinned commit that carries no license; no text or code was copied.
