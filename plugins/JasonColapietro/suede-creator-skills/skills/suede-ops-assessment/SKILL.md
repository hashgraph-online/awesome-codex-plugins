---
name: suede-ops-assessment
description: "Suede AI Operations Assessment Skills: map real work, silos, friction, ownership, costs, and adoption signals from operator evidence. Use when asked \"where is our team losing time\" or to rank operational opportunities before designing automation. NOT FOR: choosing and building the target architecture (suede-ops-architecture), auditing requester-supplied figures, or unapproved system access."
metadata:
  display-name: "Suede AI Operations Assessment Skills"
  version: 1.0.0
---

# Suede AI Operations Assessment Skills

## Compatibility

Works from operator interviews and authorized process records. No integration is required for an assessment; connected data access must be authorized. Agent estimates must be marked separately from requester-supplied figures.

For a concrete input, expected output, recovery path, and validation check, read
[the worked contract](references/worked-contract.md). Use it to check the handoff
before treating the task as complete.

```text
Iron law: map the floor, not the org chart.
```

Every operation has two maps. The leadership map describes how the business is
meant to run. The floor map describes how the work actually gets done, including
each workaround, each unofficial spreadsheet, and each extra step that exists
because something broke once. A system designed from the leadership map gets
routed around, because the people doing the work can feel the mismatch on day
one.

This skill produces the floor map and the numbers attached to it. It stops
before deciding what to build.

## The requester's numbers are given

Their hours, costs, volumes, error rates, and history are inputs, not claims to
audit. No step here verifies, scores, hedges, or gates on a figure the requester
supplied.

What does get audited is anything **this skill** produces: a benchmark it
reached for, an estimate it filled in, a process step it inferred rather than
heard. Mark every one of those inline as `[assumed]` and list them in the Output
Contract, so a reader can tell the operation's own numbers from this skill's.

Never substitute an industry average for a number the requester has. Ask for
theirs, or record the line as missing.

## Before Starting

1. **Scope**: which processes, departments, or surfaces are in the assessment.
2. **Access**: what the requester has authorized you to read. Work inside it.
3. **Who does the work**: names or roles per process, separated into people who
   perform it and people who manage it.
4. **Self-applied or on behalf**: a founder assessing their own operation reads
   Step 5 differently from an outside team assessing a client's.

Read `references/interview-guide.md` before the first interview.

## Step 1: Interview the floor

Interview at least one person **per process** who performs it, not only the
person who manages it. Where the two descriptions differ, record both and mark
the performer's version as the floor map.

Run it as a walkthrough rather than a survey: the question is what happens next,
repeated until the process ends. The guide carries the full question bank; these
four earn their place in every interview.

- Walk me through this from the beginning, including the steps too small to
  mention.
- What do you type or copy by hand more than once?
- Where does work sit and wait, and who is it waiting on?
- If volume doubled next quarter, what breaks first?

That last one returns more than the rest combined. People work next to the
weakest part of the operation every day and are rarely asked about it.

**Count the exceptions rather than describing them.** When someone says a path
runs "only sometimes", ask how many of the last twenty cases took it. An
exception that turns out to be a fifth of the volume is a main path nobody has
drawn yet.

**Follow up after two days.** People remember the forgotten step, the second
spreadsheet, and the quarterly exception once the interview has settled.

**Gate.** Every in-scope process has at least one performer interview. When the
requester performs the process themselves, their own walkthrough is the performer
interview: record it as such and move on rather than halting for a second
person who does not exist.

**Halt format.** Stop. Name each process covered only by management description.
Offer: schedule the performer interview, proceed and mark that process
`[leadership map only]` throughout the blueprint, or drop it from scope. Wait for
the choice.

## Step 2: Inventory every silo

A silo is any place operational information lives that other systems cannot see.
Catalog all of them: software, spreadsheets, shared drives, inboxes used as
databases, and the messaging channels where decisions actually get made.

Record per entry: what it holds, who writes to it, who reads from it, what it
overlaps with, and its monthly cost.

Cite a proof path for anything claimed to be live: a last-write timestamp, a
seat count, an invoice line, or a recent export. A tool nobody can produce
evidence for is recorded **unknown**, never assumed dead or alive.

**Steps with no system behind them are the finding, not a gap in the
inventory.** A process step that lives only in somebody's memory is
tribal knowledge: record it, name the person the operation stalls without, and
carry it into the ranking as key-person risk.

**Gate.** Every step from Step 1 resolves to one of three: an inventory entry, a
named tribal-knowledge holder, or manual work that depends on no system at all.
Physical and judgment work belongs in the third bucket; recording it as tribal
knowledge invents a risk that is not there.

## Step 3: Quantify the friction in their numbers

Attach a figure to each bottleneck, built from three components. Show the inputs
beside each result so a reader can check the arithmetic.

| Component | Formula |
|---|---|
| Labor | hours per week × loaded hourly cost × 52 |
| Error | cost per occurrence × occurrences per year |
| Throughput | work the team could not take on, priced the way the requester prices it |

Throughput is the softest of the three, because it prices work that did not
happen. Carry it as a separate line rather than folded into the total, and let
Step 4 mark its confidence honestly.

Where a figure is missing, write `missing: <what would settle it>` on that line
and carry it to the Output Contract. A bottleneck with no number is still a
finding; it ranks below the ones that carry figures.

**Quantify the process, never the person.** Write "intake re-entry costs
$40,000 a year", never "Dana wastes eight hours a week". The same arithmetic
becomes a performance review the moment a name is attached to it, which is not
what the requester asked for and not what the interviews were given under.

## Step 4: Rank the opportunities

Generating forty opportunities is easy. Knowing which six matter, which three
come first, and which ten sound impressive and return little is the deliverable.

Score each opportunity:

- **Value**: the annual figure from Step 3.
- **Complexity**: start at 1 for the build itself, then add one point each for:
  every system touched beyond the first, every write path that changes, every
  exception branch from Step 1, and every human approval gate that stays. The
  floor of 1 is what keeps the simplest opportunity from dividing by zero.
- **Rank**: value divided by complexity, sorted high to low.
- **Confidence**: `measured` when the requester supplied the figure from their
  own records, `stated` when they supplied it from memory, `missing` when Step 3
  could not fill it.

Report three groups explicitly: what to do first, what is real but later, and
what looks impressive and returns little. The third group is the one that earns
the assessment its fee, because it is the work nobody would otherwise decline.

## Step 5: Read the engagement signal

How an operation behaves during the assessment predicts whether it will use what
gets built. This is an observation reported to the requester, never a reason to
withhold or slow the work.

| Signal | Observable |
|---|---|
| Strong | Interviews happen as scheduled; follow-ups answered within one business day; people volunteer pain points unprompted |
| Weak | Interviews rescheduled more than once; single-sentence answers to walkthrough questions; a request to skip the map and see a demo |

Report what was observed and what it predicts. When the assessment is
self-applied, read the same signals against the requester's own participation
and say so plainly rather than scoring a team that was never involved.

## Step 6: Watch adoption for thirty days

Runs after a system built on this assessment goes live. One metric leads:
**Adoption Rate**, the share of the workflows **the system was built to carry**
that are actually running through it.

The denominator is the built scope, not every workflow Step 1 mapped. Measured
against the full map, a system that deliberately covers six of twenty workflows
reads as 30% adoption at perfect uptake, which reports a scoping decision as a
failure.

Compute it from system logs. Asking people whether they are using something
measures willingness to answer, not adoption.

**The shadow system is the signal to watch for.** Someone quietly keeping the old
tracker as insurance is diagnostic information, not disobedience: it means either
the training missed them or the system genuinely does not handle their case. Both
are cheap to fix in month one and expensive in month four, when the shadow
spreadsheet has become the real system again.

When Adoption Rate comes in low, check the assessment before blaming the build.
A system designed from a rushed or leadership-only map produces a mismatch the
team feels immediately, and Step 1's gate is where that gets prevented.

**Halt format.** When no logging exists to compute Adoption Rate, stop. Say so in
one line. Offer: instrument the workflows first, agree a manual sampling method
and its margin, or proceed without the metric and record that in the Output
Contract. Wait for the choice.

## Output Contract

```text
FLOOR MAP
- process / steps / performer interviewed / [leadership map only] where it applies

EXCEPTIONS
- process / exception path / share of last twenty cases

SILO INVENTORY
- system / holds / writers / readers / overlaps / monthly cost / proof path or unknown

TRIBAL KNOWLEDGE
- step / holder / what stalls without them

FRICTION
- bottleneck / labor / error / annual total / confidence / missing inputs
- throughput, carried separately: work not taken on, priced, confidence

RANKED OPPORTUNITIES
- first / real but later / impressive and low-return, each with value, complexity, rank

ENGAGEMENT SIGNAL
- observed behavior / what it predicts

ADOPTION (when Step 6 has run)
- Adoption Rate / built scope used as the denominator / source of the log
- shadow systems found / cause assigned to training gap or system gap

ASSUMED BY THIS SKILL
- every [assumed] line, so the requester can separate their numbers from ours

OPEN
- unresolved halts, missing figures, and unknown systems
```

## Boundaries

- Report the map and the numbers; do not cancel a tool, change a system, or
  decide the build. Step 4 ranks opportunities and stops there.
- Never verify, score, or hedge a figure the requester supplied. Audit only what
  this skill invents, and mark it `[assumed]`.
- Never substitute an industry benchmark for a number the requester has.
- Attach costs to processes, never to named individuals.
- Interview only with the requester's authorization, and record a session only
  with the participant's agreement in that session.
- Read only the systems access was granted for. An uninventoried system is
  recorded as unknown rather than reached for.
- Do not carry a prior blueprint, handoff, or inventory forward as current truth
  when the live system can be read.

## Routing

- Need the schema, write paths, automation-versus-agent calls, and build order
  once the map exists -> use `suede-ops-architecture`.
- Need what external customers say, need, and resist -> use
  `suede-customer-research`.
- Need lead lifecycle, scoring, stage, and CRM routing rules -> use
  `suede-revops`.
- Need the measurement layer and dashboards for a shipped product -> use
  `suede-analytics`.
- Need a new user reaching first value in a product -> use `suede-onboarding`.
- Need parallel lanes to run a large assessment across departments -> use
  `suede-agent-teams`, then return here for the method.
- From `suede-ops-architecture`: route a missing or leadership-only floor map
  back here before the schema is drawn.
