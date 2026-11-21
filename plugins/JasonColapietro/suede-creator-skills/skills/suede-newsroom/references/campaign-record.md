# The campaign record

One file per campaign at `.agents/newsroom/<slug>.md`. It carries decisions and
the evidence behind them, drafts live beside it, not in it.

## Contents

- [Template](#template)
- [Stage completion rules](#stage-completion-rules)
- [Returns](#returns)
- [Filled example](#filled-example)

---

## Template

```markdown
# Campaign: <slug>

status: signal | research | angle | flagship | distribution | review | approved | killed
owner-stage: <role currently holding the record>
opened: YYYY-MM-DD

## Founder intake
# Founder-led mode only. Omit this section for other campaigns.
mode-setup-path:     # .agents/newsroom/founder-loop.md
source-path:
captured-on:
speaker:
account-lanes:       # founder account | company account | both
firsthand-observations:
decisions-and-lessons:
voice-markers:
proof-leads:
claims-to-verify:
off-limits:

## Signal
event:
source-url:
decay-window:
reader-question:
proof-object:
rejected-candidates:

## Research
current-source:
verified-claims:      # 3-7, each with a URL
inference:            # separate from claims, never promoted silently
quotes:
numbers:
contradictions:
not-proven:
mechanisms:

## Angle
reader:
reader-outcome:
central-tension:
thesis:
flagship-format:
reusable-object:
proof-required:
sections:
entryway-candidates:
rejected-directions:  # >= 2, each with a reason

## Flagship
path:
claims-traced:        # each consequential claim -> packet line
approval-state:       # draft | human-approved | revision-requested

## Distribution
assets:               # surface | visible identity | account lane | entryway | central claim | standalone reason | score | claims used | approval state
collisions:           # empty, or the resolution recorded

## Review
checklist:            # the editor's seven rows, each with a verdict
decision:             # approve | revise | reject

## Performance
measured-on:          # a date, or "unmeasured"
reach:
meaningful-engagement:
goal-linked-action:
proposals:            # keep | test | stop, each naming its campaigns
approved-by-human:    # yes | no | pending

## Returns
# date | field | from-stage | to-stage
```

## Stage completion rules

A stage is complete when every field it owns is written into the record and
readable by the next role.

| Stage | Complete when |
|---|---|
| Founder intake | `mode-setup-path` resolves; every founder-led field is filled; proof leads and claims to verify remain separate |
| Signal | all signal fields filled; `rejected-candidates` non-empty |
| Research | 3–7 `verified-claims` each with a URL; `not-proven` non-empty; inference separated |
| Angle | exactly one thesis; every `proof-required` item exists in `verified-claims`; two or more `rejected-directions` |
| Flagship | every consequential claim appears in `claims-traced`; `path` resolves to a real file |
| Distribution | one entryway per asset, every asset scoring 3, `collisions` empty or resolved; founder-led rows also name visible identity, account lane, central claim, and approval state |
| Review | all seven checklist rows have a verdict; `decision` recorded |
| Performance | real figures with a `measured-on` date, or an explicit `unmeasured` |

## Returns

When a needed field is empty, set `owner-stage` back to the previous role, append
a line to `## Returns`, and halt with the format in `SKILL.md` Step 3. Two returns
on the same field means the pipeline cannot supply it, escalate to the human.

## Filled example

```markdown
# Campaign: agent-handoff-contracts

status: angle
owner-stage: strategist
opened: 2026-08-28

## Signal
event: Three teams described the same failure, multi-agent content setups
  producing near-identical posts across platforms.
source-url: support ticket cluster #4411, #4460, #4472
decay-window: weeks: a workflow complaint, not a news cycle
reader-question: "why does my AI content team keep writing the same post?"
proof-object: side-by-side of four platform posts from one ticket, hooks near-identical
rejected-candidates:
  - vendor pricing change: no reader outcome, decays in days
  - a model release: already covered by every newsletter this audience reads

## Research
current-source: the ticket cluster above, plus two public write-ups of the pattern
verified-claims:
  1. All four sampled setups fed the finished draft, not the brief, to the
     repurposing step. [ticket #4411 transcript]
  2. Three of four used one shared memory across roles. [ticket #4460]
  3. None recorded which claims the assets relied on. [audit notes]
inference: shared memory is *likely* the larger cause: not established here
contradictions: one public write-up blames prompt length, which this sample
  does not support
not-proven: that separating memory alone fixes duplication; no controlled comparison
mechanisms:
  - a finished draft carries one argument, so anything derived repeats it
  - shared memory removes the difference between specialists
```

The angle stage then picks one thesis from that, and names what it rejected.
