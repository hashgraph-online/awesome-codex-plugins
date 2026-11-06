---
name: suede-ops-architecture
description: "Suede AI Operations Architecture Skills: simplify workflows, choose bounded automation, define ownership, rollout, and verification. Use when asked \"turn this ops assessment into a plan\" or to design a practical operating system. NOT FOR: discovering and quantifying current operations (suede-ops-assessment), code implementation, or production changes without authority."
metadata:
  display-name: "Suede AI Operations Architecture Skills"
  version: 1.0.0
---

# Suede AI Operations Architecture Skills

## Compatibility

Requires an operations assessment or equivalent process/volume/owner evidence. Produces architecture and handoffs from supplied records; implementation and connected-system writes need their own tools and authority.

For a concrete input, expected output, recovery path, and validation check, read
[the worked contract](references/worked-contract.md). Use it to check the handoff
before treating the task as complete.

```text
Ordering law: data, then workflows, then intelligence.
```

An agent reading fragmented data does not report that it holds a third of the
picture. It returns a fluent, confident answer built on a third of the picture.
Fragmented input produces polished mistakes at scale, and polished mistakes
survive review that visible chaos would not. Architecture is what stops the
model from being asked a question its inputs cannot answer.

This skill ends with a written architecture, not a build. Every step below
produces a line in the Output Contract, and every gate names what an agent does
when it fails.

## Before Starting

Collect these. Work with what exists and name what is missing in the Output
Contract rather than blocking on it.

1. **Entities**: the nouns the operation runs on (client, project, order, job,
   track, release, patient).
2. **Work units**: the recurring things people do, one line each, in the words
   the person doing them uses.
3. **Tool list**: every system holding operational data, including
   spreadsheets, shared drives, and any inbox used as a database.
4. **Cycle length**: median days for one unit of work to go from open to done.
5. **Blast radius per work unit**: what a wrong output costs, and whether it
   can be undone.

Read `references/triage-examples.md` for worked classifications before running
Step 3 on unfamiliar work.

## Step 1: Schema before surfaces

Name the entities, their fields, and their relationships before designing a
screen, an automation, or an agent.

For each entity record: the fields it carries, the entity it belongs to, and the
lifecycle states it moves through.

**Gate.** Every work unit from Before Starting reads or writes at least one named
entity. A work unit touching no entity means the schema is incomplete.

**Halt format.** Stop. Name the unmapped work unit in one line. Offer: add the
missing entity, fold the work unit into an existing entity, or mark it
out of scope in writing. Wait for the choice.

## Step 2: One write path per entity

Each entity gets exactly one place a record is created and one path it is
updated. Everything else reads.

For each entity, list every write **path**: each tool, script, form, and
integration that can create or update it. People entering data through one
application share that application's path and do not count separately; two
applications writing the same record are two paths.

**Gate.** Write-path count per entity resolves to one. Two paths into the same
record rebuilds the silo the system is being built to remove, on newer software.

**Halt format.** Stop. Name the entity and each competing path in one line
apiece. Offer: designate one canonical writer and make the others read, put every
writer behind one service that owns the write, or split into two entities with
separate lifecycles. Wait for the choice.

## Step 3: Triage every work unit

Route each work unit to an automation, an agent, or a human. Apply the Written
Rule Test in order and stop at the first match.

| Test | Verdict | Build as |
|---|---|---|
| The complete rule can be written down, every branch included, with no "it depends", "usually", or "as appropriate", and inputs already arrive structured | **Automation** | Deterministic code. No model. |
| The rule can be written down, but inputs arrive as prose, audio, or images | **Automation with one extraction step** | Model parses input into the schema; the written rule decides. |
| The rule cannot be fully written, and two competent people given the same context would agree on the answer | **Agent** | Model interprets, drafts, or answers, against the schema from Step 1. |
| The rule cannot be fully written, and two competent people would disagree | **Human decides** | System assembles the full context and presents it; the person chooses. |

Adding a model to deterministic work buys nondeterminism and per-call cost in
exchange for nothing. Work that passes the first test stays code.

Settle the agreement question rather than estimating it: give the same three real
past cases to two people who do the work. Matching answers put the work unit with
the agents; diverging answers put it with the humans.

**Blast-radius override.** Apply after the table, and it wins. Any work unit
whose wrong output moves money, reaches someone outside the team, changes
access, or deletes data becomes **agent proposes, human approves** regardless of
the verdict above. Reversibility is the test, not difficulty.

Notifications into a channel the team already owns do not reach outside it and
keep their table verdict: a routing automation that posts to an internal channel
stays a plain automation.

**Halt format.** When a work unit cannot be classified (its rule was never
written down, or the two people needed to settle the agreement question are not
available), stop. Name the work unit in one line. Offer: write the rule now and
reclassify, run the three-case comparison with whoever does the work, ship it as
human-decides until either lands, or mark it out of scope. Wait for the choice.

## Step 4: Absorb, keep, or kill every tool

Each tool from the list gets one verdict and one proof path. Presence in a config
is not evidence that a tool is live: cite a last-write timestamp, a seat count,
an invoice line, or a recent export.

| Verdict | Criteria | Result |
|---|---|---|
| **Absorb** | The tool performs a function the new system's schema already owns, and it is system of record for nothing regulated or financial | Rebuild the function, cancel the tool |
| **Keep** | System of record for regulated, financial, or legally retained data, or it holds an integration surface that would cost more to rebuild than the build budget allows | Integrate and read from it |
| **Kill** | No writes across a full usage cycle (ninety days for a continuously used tool, a full year for anything on an annual or seasonal cycle such as tax, audit, insurance, or renewal software) or its function is already fully covered by a kept or absorbed tool | Cancel, rebuild nothing |

A tool with no proof path is unclassified, not killed. Report it as unknown and
name what evidence would settle it.

## Step 5: Choose the migration path in writing

Decided here, during architecture, and never improvised mid-build. Apply in
order and stop at the first match.

| Condition | Path |
|---|---|
| History is read daily in the ordinary course of work | **Full migration**: clean, map, backfill, run parallel for one cycle, dated cutover, read-only window, retire |
| Reference records outlive the work; closed transactions are rarely reopened | **Hybrid**: migrate clients, contacts, vendors, catalogs; leave transactional history read-only in place |
| Cycle length is short and closed records are rarely reopened | **Cutover date**: no backfill; new work opens in the new system, in-flight work finishes in the old one, which empties itself in one cycle |

A retention requirement on its own does not force a full migration. Read the
requirement's wording: most are satisfied by a read-only archive held for the
stated period, which the hybrid and cutover paths both preserve. Migrate for
daily use, archive for retention.

Cutover date is the cheapest path and the least chosen. When cycle length is
short, a full migration pays to move records that will close before the backfill
finishes.

Two rules hold on every path. The switch date reaches the whole team at least two
weeks ahead with training delivered before it arrives. The old tools are
cancelled on a dated line in the plan, because a backup kept alive becomes a
competing system inside a month.

## Step 6: Sequence into commanded phases

Order the build so nothing lands on a moving foundation: schema, then workflows,
then agents.

Each phase carries a completion standard that a command proves. A phase whose
standard reads as a judgment ("the schema looks stable") has no gate: replace it
with a command, a readback, or a file check whose output decides.

| Phase | Completion proved by |
|---|---|
| Schema | Migration applies clean on an empty database and every Step 1 entity round-trips |
| Workflows | Every deterministic work unit from Step 3 runs on real test data, including the failure branch |
| Agents | Every agent work unit scores against a fixed eval set, at a passing threshold written down before the set is run, and does so before real work depends on it |
| Migration | The chosen path's cutover date is dated, staffed, and communicated |

The next phase opens when the current phase's command passes. Report the command
and its output, not a claim that the phase is done.

**Halt format.** When a phase's command fails or has not been run, stop. Name the
phase and the failing command in one line. Offer: fix the phase and rerun the
command, narrow the phase so the command can pass on a smaller scope, or record
an explicit written exception naming who accepted the risk. Wait for the choice.

## Output Contract

```text
ENTITIES
- entity / fields / relationships / lifecycle states

WRITE PATHS
- entity / canonical writer / readers / collisions resolved

WORK TRIAGE
- work unit / verdict (automation | extraction | agent | human) / blast-radius override applied

TOOL VERDICTS
- tool / absorb | keep | kill | unknown / proof path

MIGRATION
- path chosen / cycle length / lookup frequency / cutover date / tools cancelled on

PHASE PLAN
- phase / completion command / gate status

OPEN
- unresolved halts, missing inputs, and unclassified tools
```

## Boundaries

- Produce the architecture; do not build it, migrate data, or cancel a live
  subscription.
- Do not mark a phase complete without pasting the command output that proves it.
- Do not classify a tool from a config entry, a memory, or an older audit. Cite a
  current proof path or report it unknown.
- Do not assign an agent to work whose wrong output is irreversible; that work is
  agent-proposes and human-approves.
- Do not invent cycle length, lookup frequency, or cost figures. Ask for the
  number, or record it as missing in the Output Contract.
- Do not treat a prior handoff, blueprint, or inventory as current truth when the
  live system can be read.

## Routing

- Need the current operation mapped and its friction costed before architecture
  -> gather the Before Starting inputs directly. `suede-customer-research` carries
  the interview and synthesis method, but its subject is an external customer
  segment, so borrow the technique and not its personas or jobs framing.
- Need to build the change across many files under one evidence-gated plan -> use
  `suede-graph-flo-xr`.
- Need parallel builders with explicit file ownership and rollback -> use
  `suede-agent-teams`.
- Need lead lifecycle, scoring, stage, and CRM routing rules -> use
  `suede-revops`.
- Need an eval set proving the agent tier of Step 6 -> use `suede-ai-eval`.
- Need the measurement layer for the shipped system -> use `suede-analytics`.
- Need findings-only review of the built diff -> use `suede-code --findings-only`.
- Need CI, required checks, or merge gates around the build -> use
  `suede-ci-gate`.
- From `suede-agent-teams`: route schema, write-path, and work-triage decisions
  back here before lanes open.
