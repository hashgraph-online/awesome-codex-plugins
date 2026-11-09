# Research Workflow

Use this rule file when a research task starts. It owns framing, the fidelity record, the journal, the first collection wave, saving, and the closing briefing. Expansion, verification, and gates live in their own rule files.

## 1. Confirm The Request

- If the user gave no topic, ask for it in one question and stop before any collection.
- Pick the depth from the user's words (`SKILL.md`, trigger conditions); with no depth word, use the default mode.
- Mark the request date-sensitive when it says `latest`, `current`, `today`, `recent`, `this year`, or similar relative-date wording.

## 2. Frame The Question

Start from "what must be true if the user's premise is true?", not from "what does the first search say?". Write this block before any search, into `brief.md` (default, deep, parallel) or the report's scope section (`--quick`):

```text
Core question: <the actual information need, one sentence>
Axes: <axis - what to search, where, why>   (quick 1-2, default 3-4, deep 4-6; orthogonal, no shared angle)
Expected truths: <E1 - a statement that must hold if the premise is right>  (one per axis at least)
Entity: <the canonical name and first-party URL of anything the topic names, or "to settle in wave 1">
Codebase relevant: yes/no | External: yes/no | Execution checks likely: yes/no
Precision demand: <what a wrong claim costs here: low | normal | high (legal, medical, financial, security, public-facing)>
```

Expected truths are what the run checks reality against. Each one ends the run as `true`, `violated`, or `unknown`, and the report says which.

## 3. Record The Fidelity Fields

Three fields say what the report must stay faithful to. Infer each one first; ask only when the answer changes the outcome and nothing in the request, destination, or sources decides it.

| Field | Values | Default | Ask when |
|---|---|---|---|
| `as of` | latest at run start, a version, release, tag, commit, date, or quarter | latest at run start, with the run date | the topic is version-bound or time-sensitive and nothing names an anchor |
| `source floor` | `standard`, `primary only`, `pointed only: <ids/URLs/paths>` | `standard` | a restricting phrase ("official docs only") sits beside a question whose answer lives outside that floor |
| `derived numbers` | `allowed`, `none` | `allowed` | the request both asks for comparisons or growth and says "only the sources' own numbers" |

Record each field with `answered_by: request | default | user`. Put at most one question per field in a single message, default option first, and start collection without waiting; a late answer is folded in before the report is written. Pointed-at sources with no restricting word are seeds, not a floor.

## 4. Open The Journal

For default, deep, and parallel runs, create `.hyper/research/[NN].slug/` beside the future report and keep the files described in `references/journal-format.md`. `--quick` keeps its ledger and query log inside the report.

- The leader writes every journal file; lanes never do.
- Each source, quote, number, and lead is written the moment it lands. The journal is the recovery point after context loss: after a compaction, re-read `brief.md` and the journal before doing anything else, then resume from the open wave.

## 5. Plan Channels And Queries

Read `references/channel-selection.md`. For each axis, write the distinct queries and the channel each targets into the query log before running them. Search in English first; add a local-language sweep when the topic is local or the user names a source language.

## 6. Run The First Wave

- Launch every axis in the first wave at once - as lanes when the parallel modifier applies (`rules/parallel-research.md`), otherwise as consecutive searches by the leader. Do not "start with one axis and see".
- The first wave settles the entity when one is unresolved: canonical name, first-party URL or account, whether it exists in the claimed category, and a confidence line. An unresolved entity never becomes a premise in a later query or lane prompt.
- Open every candidate before counting it. A result snippet is a lead; the opened artifact is the source.
- For each opened source, add a ledger row with publisher, dates, channel, grade, and role, then note the exact quote or line the claim rests on.
- When a channel is unavailable, say so in the query log and use the next-best channel rather than inventing a tool.

Then hand over to `rules/expansion-and-convergence.md`.

## 7. Save The Report

Save the report to `.hyper/research/[NN].slug.md`, where `NN` is the next zero-padded sequence number in `.hyper/research/` and `slug` is a short ASCII summary of the topic. The journal directory uses the same `[NN].slug` stem. Create the report file with its section headings as soon as the brief exists, so an interrupted run leaves a partial report on disk instead of nothing.

When the report file is created, its first five lines carry `STATUS: draft`. That line stays while any gate is open and is removed only after the last gate runs. A run that finds `STATUS: draft` on the existing report resumes from the journal instead of starting a new report file.

The journal brief records the deliverable promise next to the fidelity fields: the format (`md` by default), the path, and the `answered_by` value that chose the format (`user`, `default`, or `request`). The promised format and path are what the saved report is measured against in `rules/validation.md`.

## 8. Closing Briefing

The final chat message carries, in this order:

- the headline conclusion in one to three sentences
- the saved report path, and the journal path when one exists
- an effort line: sources reviewed and cited, distinct domains, waves, excursions, and execution checks, read off the journal rather than recalled
- after the gates run, `bash scripts/report-state.sh finish --state <journal>/report-state.json --report <report.md> --ledger <journal>/sources.md` writes `outcome.json` into the journal; `report-state.sh briefing --state <journal>/report-state.json` prints the sources, domains, repairs, gate results, and residual defects counted from that file. Use those printed numbers in the effort line, not recalled ones.
- the run state (`converged` or `exhausted`) and the main caveat or open gap when confidence is limited

## Sources

> Checked 2026-11-03.

| Claim | Source |
|---|---|
| Framing from expected truths, the analysis block, entity disambiguation in the first wave, the real-time journal, the early report skeleton, and the closing effort line, adapted from the `ulw-research` skill | <https://github.com/code-yeongyu/oh-my-openagent/tree/0d80470e4201925727e88afbafcdf24d7801a588> |
| The three fidelity fields, reduced from the upstream seven, with inferred defaults and `answered_by` | same source, reduced by this package |
| A snippet is a lead and never primary evidence; reviewed and cited are counted apart | `instructions/sourcing/references/source-ledger.md` |
| Keep the authoritative plan outside the context window and re-read it after compaction | `instructions/context-engineering/CONTEXT_ENGINEERING.md` |

### Evidence grade

`LOCAL` - this file states this package's own procedure, adapted from the upstream skill named above. The axis counts and the fidelity field set are this package's choices.
