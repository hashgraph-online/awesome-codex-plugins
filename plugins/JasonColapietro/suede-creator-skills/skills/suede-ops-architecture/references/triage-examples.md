# Triage Examples

Worked classifications for the Written Rule Test in Step 3. Read the row whose
shape matches the work unit, not the row whose industry matches.

- [Automation](#automation): the rule is complete and inputs are structured
- [Automation with extraction](#automation-with-extraction): the rule is complete, inputs are prose
- [Agent](#agent): the rule resists writing, competent people agree
- [Human decides](#human-decides): competent people disagree
- [Blast-radius overrides](#blast-radius-overrides): verdicts the override changes
- [Misclassifications](#misclassifications): the four that recur

## Automation

The rule is writable end to end and the input already arrives as fields.

| Work unit | Why it stays code |
|---|---|
| Form submitted, create record, assign owner by territory, notify channel | Territory is a lookup table; every branch is enumerable |
| Invoice past due by a set number of days, escalate to the next dunning stage | The stage ladder is a fixed sequence with dated triggers |
| Deal reaches closed-won, provision the account and open the onboarding checklist | Provisioning steps are identical every time |
| Nightly reconcile of two systems, flag rows whose totals differ | Difference is arithmetic, not interpretation |
| File lands in a watched folder, validate against schema, route or reject | Validation is the schema itself |

A model added to any of these buys nondeterminism and per-call cost and returns
nothing the lookup table did not already have.

## Automation with extraction

The decision is a written rule. The model's only job is turning prose into
fields, and it never chooses the outcome.

| Work unit | Extracted | Decided by |
|---|---|---|
| Inbound email triaged to a queue | Requested action, account, urgency | Routing table on the extracted fields |
| Receipt or invoice image entered into accounting | Vendor, date, line items, total | Chart-of-accounts mapping |
| Voice note turned into a task record | Task, owner, due date | Assignment rules |
| Job application parsed to a candidate record | Role, years, location, work authorization | Screening thresholds |

The split matters under audit: when the outcome is challenged, the written rule
is the answer and the extraction is the evidence.

## Agent

The rule resists complete writing, and competent reviewers agree on the answer
given the same context.

| Work unit | Why judgment is required |
|---|---|
| Draft a reply to a support question from the knowledge base | Phrasing and relevance shift per question |
| Summarize a call into a structured record | Salience cannot be enumerated |
| Draft a scope of work from a discovery transcript | Assembly from context, reviewed before it leaves |
| Answer an internal question across documentation | Retrieval plus synthesis |
| Classify free-text feedback into themes that do not exist yet | The categories are the output |

Every one of these reads from the Step 1 schema. An agent pointed at scattered
sources returns a confident answer shaped by whichever source it happened to
reach.

## Human decides

Two competent people, same context, different answers. The system prepares; the
person chooses.

| Work unit | What the system assembles |
|---|---|
| Approve a discount past standard | Margin, history, cohort precedent, renewal exposure |
| Accept or decline a client | Fit signals, capacity, concentration risk |
| Price an exception | Comparable jobs, cost basis, relationship value |
| Set the release date | Open defects, staffing, external commitments |
| Terminate an account | Contract terms, revenue impact, notice obligations |

The value is compressing a long research task into a short review, not removing
the person.

## Blast-radius overrides

The table verdict is right and the override still applies, because the cost of a
wrong output is not the cost of a hard one.

| Work unit | Table verdict | Ships as |
|---|---|---|
| Send the drafted client email | Agent | Agent drafts, human sends |
| Issue the refund the policy allows | Automation | Automation prepares, human releases |
| Delete records past retention | Automation | Automation lists, human confirms |
| Change a user's permissions | Automation | Automation proposes, human applies |
| Post to the company account | Agent | Agent drafts, human publishes |

Reversibility decides, not difficulty. A trivially easy action that cannot be
undone still takes the override.

The override reads "outside the team" literally. Posting a new record into the
team's own Slack or email channel does not trigger it and stays a plain
automation; sending that same record to the client does.

## Misclassifications

Four that recur, and the tell for each.

**Deterministic work dressed as judgment.** "It depends" that resolves to a
lookup table nobody wrote down. Tell: the person doing it answers every example
you give them without hesitating. Write the table; ship it as an automation.

**Judgment work dressed as deterministic.** A rule with an "and use your
judgment for the rest" clause. Tell: the exception branch carries more volume
than the rule. Ship the rule as an automation and the exception to an agent or a
person, separately.

**One work unit that is three.** Intake, decision, and notification bundled into
a single line. Tell: the verdict changes depending on which half you look at.
Split, then classify each part.

**An agent standing in for missing schema.** The agent exists to reconcile
sources that disagree. Tell: its prompt names more than one system of record.
Fix Step 2 and the agent's job shrinks or disappears.
