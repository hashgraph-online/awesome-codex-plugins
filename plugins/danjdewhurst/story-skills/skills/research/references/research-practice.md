# Research Practice

## What needs checking

Check anything a reader with first-hand knowledge could catch:

- Dates, sequences, and durations of real events
- How a job, weapon, vehicle, tool, or procedure actually works
- Medicine: injuries, recovery times, drugs, and what a body can survive
- Law and police procedure for the setting's country and era
- Geography, travel times, weather, tides, daylight hours for the date
- Period detail: money, clothing, food, speech, technology available
- Language and names for the culture, region, and era

Invented worlds still borrow physics, biology, and human behaviour; check
those when the plot turns on them.

## Forming questions

Turn a topic into questions the prose actually answers. "Victorian
medicine" cannot be verified; "Would a London surgeon in 1872 have used
carbolic spray?" can. One note may hold several related questions; list
each under `## Question` so findings can answer them one by one.

## Search plan

Write the plan into the note before searching so the work can be resumed
or handed to the user. The examples in this file are illustrative: the
sources, figures, and URLs show the format and are not verified facts.

```markdown
## Search Plan

- Primary: Environment Agency tide tables for 2024; Severn Bore
  Trust timetable (official data)
- Secondary: Smith, *The Severn Estuary* (2020), ch. 4
- People: a local surfer or river warden (interview)
- Place: Minsterworth bank at a spring tide (site visit)
```

Search the primary sources first, then use secondary sources to interpret
them. Record dead ends too ("no 1950s timetable online; archive request
needed") so they are not repeated.

## Judging sources

Prefer, in order: primary sources (records, first-hand accounts, official
data), expert secondary sources (academic work, professional references),
then general references. Note the date of each source; practice changes.
When two sources disagree, record both and mark the note `disputed` until
the user decides which the story follows.

A primary source is evidence from the time or the thing itself: a record,
a diary, a photograph, a statute, a manual, the place, a person who was
there. A secondary source interprets primary ones. Treat encyclopaedias,
forums, and AI summaries as leads to a real source, never as the source.

## Recording findings

Write findings as short factual statements, each with its citation: author
or institution, title, date, and page, section, or URL.

The figures below are illustrative placeholders; verify real values
against the sources before using them.

```markdown
## Findings

- The Severn bore is largest near the spring equinox, two to three days
  after a new or full moon. (Smith, *The Severn Estuary*, 2020, p. 112)
- It travels upstream at about 16 km/h. (Environment Agency tide notes,
  https://example.gov.uk/severn-bore, accessed 2026-03-02)
- > "The bore is at its best when the tide exceeds 9.5 metres at
  > Sharpness." (Severn Bore Trust timetable 2024, p. 2)
```

Quote exact wording when the prose depends on it: a term of art, a
regulation, a period phrase. Keep quotes short and always give the page or
URL. Add each source to the `sources` frontmatter list as well.

## Confidence

Set `confidence` from the evidence, and revise it as findings change:

| Confidence | Evidence |
|------------|----------|
| `high` | A primary source, or two independent sources that agree |
| `medium` | One reputable secondary source, not yet cross-checked |
| `low` | Recalled, inferred, or from a single weak or undated source |

Confidence is separate from `status`. A note can be `verified` at `medium`
confidence when its one good source is enough for how the prose uses it.

## Accuracy levels

| `accuracy` | Meaning | Sources needed |
|------------|---------|----------------|
| `must-be-accurate` | A real fact a reader could check | Yes; verify before final |
| `blended` | Real facts mixed with deliberate invention | Yes for the real part; record the invention under `## Story Use` |
| `invented` | A made-up fact kept for consistency | No; never triggers the open-research warning |

## Risk and reviewers

Set `risk` whenever a mistake could cause real harm or liability:

- `legal` - law, courts, contracts, police powers presented as how things work
- `medical` - symptoms, dosages, treatment, survivability
- `weapons` - how weapons function or are made
- `safety` - anything a reader might copy (climbing, diving, chemistry, fire)
- `cultural` - portraying a culture, faith, community, or identity
- `defamation` - real, identifiable people or organisations
- `technical` - engineering, security, aviation, or other specialist systems

A risky note needs a qualified human reviewer before the chapters using it
are final. Record them in `reviewed-by`, a list of names or roles that
`story add research` has no flag for, so edit the frontmatter by hand:

```yaml
reviewed-by:
  - "Dr A. Patel, A&E consultant"
```

After you edit the frontmatter, run `story reindex .`, `story wordcount . --write`, and `story check .`.

Research gathers facts and flags concerns; it never
substitutes for professional advice, and the agent never gives legal,
medical, weapons, or safety advice. Omit operational detail that would let
a reader cause harm; the scene rarely needs it. Route defamation and
sensitivity questions to the `editorial-review` skill.

## Deliberate departures

Fiction may bend facts. Record every intentional change under
`## Story Use` with the reason ("moved the bore a week earlier so it lands
on the festival"). This stops a later fact-check from "fixing" a choice.
