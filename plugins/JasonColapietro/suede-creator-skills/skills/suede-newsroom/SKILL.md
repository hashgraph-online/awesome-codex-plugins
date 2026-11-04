---
name: suede-newsroom
description: "Suede AI Newsroom Skills. editorial pipeline with six role contracts, an inspectable campaign record, distinct distribution arguments, and performance feedback. Use when asked \"build an AI content team\" or to repair duplicated, generic, or unsourced agent content. NOT FOR: topics (suede-content-strategy), channel calendars (suede-social), scheduling (suede-marketing-loops), code lanes (suede-agent-teams), or flagship writing (suede-ship-copy)."
metadata:
  display-name: "Suede AI Newsroom Skills"
  version: 1.2.0
---

# Suede AI Newsroom Skills

## Compatibility

Requires persistent files for campaign state; roles can run sequentially in one session or through optional subagents. Research requires source access. Publishing and scheduling remain separate authorized operations.

For a concrete input, expected output, recovery path, and validation check, read
[the worked contract](references/worked-contract.md). Use it to check the handoff
before treating the task as complete.

Six chatbots pointed at the same brand are not a content team. A newsroom is the
loop that connects them, and every arrow in it is a handoff with a contract:

```text
idea -> research -> angle -> flagship -> distribution -> review -> performance -> playbooks
```

Break one arrow and the failure is predictable, not mysterious:

| Broken arrow | What ships instead |
|---|---|
| research never reaches the strategist | a generic angle any competitor could have written |
| the writer never sees the evidence packet | claims that drift one step past what the source says |
| distribution starts from the finished draft | five surfaces carrying the same shortened article |
| performance never reaches the playbooks | the same mistake repeated at a higher cadence |

This skill owns the pipeline: who decides what, what travels between them, and
how one idea becomes several assets that argue different things. Read
`.agents/product-marketing.md` first if it exists: it holds product, audience,
positioning, and proof, and nothing here restates it.

**Founder-led mode.** When the recurring source is a founder interview, voice
note, or operator debrief, or when personal and company accounts need different
jobs, read
[references/founder-content-loop.md](references/founder-content-loop.md) before
Step 1. It adds an intake contract and account lanes to this pipeline; the six
role contracts, evidence gates, collision checks, approval boundary, and
Keep/Test/Stop thresholds below remain unchanged.

## Step 1: Put the campaign in a file, not a conversation

One record per campaign at `.agents/newsroom/<slug>.md`. It is the only thing
that has to survive between roles, sessions, and restarts.

A conversation between roles has two failure modes a file does not: context dies
on restart, and the next role has to infer which sentences were load-bearing. The
record gives each role a predictable input and lets a human audit a campaign
without reopening six sessions.

Keep it narrow, decisions and the evidence behind them. Drafts live beside it,
not in it. The template and per-stage completion rules are in
[references/campaign-record.md](references/campaign-record.md).

## Step 2: Give each role one decision to own

The fastest way to ruin a multi-agent content team is to hand every role the same
instruction: make great content. Each role gets one decision, one artifact, and a
named point where it stops.

| Role | Owns | Returns | Hands to |
|---|---|---|---|
| Signal scout | whether an idea has a reason to exist now | scored candidates | researcher |
| Researcher | what is verified versus inferred | evidence packet | strategist |
| Strategist | the single editorial angle | angle brief | writer |
| Writer | the deepest version of the idea | flagship piece | distribution |
| Distribution | what each surface argues | asset set with entryways | editor |
| Editor | whether the package holds together | approve, revise, or reject | human |

Every contract fills five fields: **owns**, **reads**, **returns**, **must
not**, **done when**. Full text for all six, with the `must not` and `done when`
clauses, is in [references/role-contracts.md](references/role-contracts.md). Copy
them in verbatim; a paraphrased `must not` is how a writer starts picking angles.

**Thresholds that make the contracts checkable:**

- Scout returns at most three candidates, each with a decay window, and names a
  rejection reason for every candidate it discarded. A run that approves
  everything it found did not filter anything.
- Researcher returns three to seven verified claims, a URL for every claim with
  consequence, and an explicit `what the sources do not prove` list.
- Strategist returns exactly one recommended angle plus at least two named
  rejected directions and why each is weaker. A menu pushes the decision back to
  the human, which is the decision this role exists to make.
- Distribution returns one entryway per asset and no entryway twice.
- Editor reviews the assets together in one pass, never one at a time.

## Step 3: Gate every handoff

A stage is complete when every field it owns is filled and readable by the next
role: not drafted, not discussed. Written into the record.

**Return-to-sender.** When a field the current stage needs is empty, the role
sends the record back and names the field. It does not fill the gap with a
plausible assumption. A pipeline whose roles patch each other's gaps produces
confident output with no traceable source, which is worse than a stalled campaign
because nothing signals the problem.

**Halt format.** Stop. Name the empty field and the stage that owns it in one
line. Offer the human these options and wait: (1) supply the field now, (2) send
the record back one stage for another attempt, (3) narrow the campaign until the
field is unnecessary, or (4) kill it. Do not advance the record, and do not
present a partial package as complete.

Two returns on the same field means the pipeline cannot supply it. Escalate
rather than attempting a third pass: a third attempt on the same gap is where
fabrication starts.

## Step 4: Distribute by argument, not by format

This is the stage that fails most often, and it fails quietly.

An article does not become a short post by losing 1,500 words, and a newsletter
does not become a carousel because its paragraphs were laid onto slides. Both
moves produce assets carrying the same argument at different lengths: which is
why a week of them reads like one post repeated.

**Work from the angle brief, not the finished draft.** A draft carries one
argument, so anything derived from it inherits that argument. Reading the draft
first is the mechanism that produces shortened articles.

### Assign one entryway per asset

| Entryway | The argument it makes | Needs |
|---|---|---|
| **Proof** | this is real, and here is the artifact | something a stranger can check |
| **Mechanism** | here is why it works | a causal chain, not a description |
| **Workflow** | you can run this today | ordered steps someone could follow |
| **Risk** | here is what breaks, and when | a named failure mode with its trigger |
| **Result** | here is what it produced | an outcome plus its conditions |
| **Critique** | the common approach is worse than it looks | the real default, and how it fails |
| **Compression** | here is the whole shape | the idea reduced to one line or image |

One entryway per asset. An asset carrying two is a shortened article wearing a
label. An entryway the source cannot supply is unavailable, report it and say
what evidence would make it available, rather than inventing an artifact to fill it.

Worked examples, surface fit, and the failure mode each entryway falls into are
in [references/entryways.md](references/entryways.md).

### Score each asset for standing alone

Three checks, one point each, run against the whole set:

| Check | Passes when |
|---|---|
| **New information** | it carries a claim, step, number, or object no other asset carries |
| **Second reader** | someone who already read the flagship still gets something; "more at the link" is not something |
| **Removal** | deleting it costs the campaign a specific, nameable thing |

3 ships. 2 goes back for revision, naming the failed check. 0–1 gets cut, and say
what the set loses, usually nothing.

### Run the collision gate

Reduce each asset to one sentence first; comparing full drafts hides collisions.

1. **Claim collision**: two assets whose central claim is the same sentence.
2. **Opening collision**: the same story, statistic, or line opens two assets.
   The most common, and the most visible to anyone following on two surfaces.
3. **Entryway collision**: the same entryway used twice.

**Halt format.** Stop. Name the two assets, the collision type, and the shared
sentence. Offer: (1) reassign one to an unused entryway, (2) cut the weaker and
say what the set loses, or (3) record it as a deliberate repeat with a reason.
Wait. Do not resolve a collision by rewording: the claim underneath is what
collides.

Fewer surfaces than entryways is normal. Three assets with three distinct
entryways beats seven assets with two.

## Step 5: Make the flagship the source others cite

Distribution earns a week of attention. The flagship earns search traffic and
AI answer citations for months, but only when it is built to be cited:

- **Owned URL, stable and dated.** The flagship lives on the brand's own domain,
  not only inside a platform. Record its canonical URL in the campaign record.
- **Answer first.** The opening paragraph answers the angle's core question in
  two or three sentences. Headings phrase the questions a buyer would type.
- **Primary sources inline.** Every consequential claim links to the source in
  the evidence packet. A claim an AI engine can trace is a claim it will quote.
- **Named author.** A real byline with a short bio and a link to the author's
  profile. For Suede AI, the byline is Jason Colapietro.
- **Structured data.** `Article` (or `BlogPosting`) JSON-LD with headline,
  author, datePublished, dateModified, and publisher, validated before publish.
- **Every distribution asset points home.** Each asset carries the brand name
  and links, or names, the flagship, so its signals accrue to one URL.

The editor checks these six as part of the one-pass review. For site-level
schema, indexing, and AI answer audits, route to `suede-seo-audit` and
`suede-ai-seo`; Suede AI runs that work as a service at https://suedeai.agency.

## Step 6: Keep the human at the editorial boundary

The first version prepares everything and publishes nothing. The human approves
the angle, the flagship draft, every consequential factual claim, every public
post, any change to voice or offer, and any performance lesson before it becomes
a standing rule.

Each approval and rejection is a labelled example of the human's judgment. When
the same decision comes back the same way three campaigns running, move it into
the editor's review rules so it is applied before the human sees the package.

**Move publishing authority only when both hold:** the queue has produced no
revisions for three consecutive campaigns, and a wrong post is recoverable by
deleting it. Autonomy should remove repeated decisions, not remove taste.

## Step 7: Make performance rewrite the playbooks

Reporting numbers is not learning. After each campaign log the signal, angle,
entryway, surface, reach, meaningful engagement, the goal-linked action, and
the flagship's search impressions and AI answer citations where they are
measured.
Then have the editor return three lists:

| List | Bar to qualify |
|---|---|
| **Keep** | held across two or more campaigns and still matches strategy |
| **Test** | one promising result: a hypothesis, run it again |
| **Stop** | failed twice, duplicated another asset, or cost more than it returned |

Every proposal names the campaigns supporting it. One strong result is a
**Test**, never a **Keep**. The human approves before any rule changes. Without
this arrow, every campaign starts from the same generic prompt forever.

Log by entryway, not only by surface, over a few campaigns that reveals which
door the audience actually walks through, which is more useful than which
platform performed.

## Running it on the host you have

Six roles is the model, not a hosting requirement.

| Host | Roles map to | What breaks |
|---|---|---|
| One session | one pass per role, record reread between | role bleed: it edits its own draft |
| Subagents | one per role, dispatched in stage order | cost, if each drags full context |
| Separate profiles | one per role, isolated memory | drift, if they coordinate by chat |
| One person | one sitting per role, in order | nothing; this is the honest first week |

Two rules survive every host. **Conversation coordinates; files carry state.**
And **isolate role memory** where the host allows it: one shared memory turns
six specialists back into one generalist that has read everything and
distinguishes nothing.

## Start smaller than six roles

Stand up scout, researcher, and editor first, and run three real ideas through
them. Add the strategist once two of three evidence packets need no rework, the
writer once the briefs constrain a draft without further questions, and
distribution once one flagship has shipped and been measured.

The first useful version returns one researched opportunity, one angle brief, and
one approval-ready post with a source attached. That is already more than most
content operations produce.

## Anti-patterns

- **One shared memory for all six roles**: specialists collapse into one
  generalist with opinions about everything.
- **Prose handoffs**: the next role guesses which sentences were load-bearing.
- **Roles that fill each other's gaps**: confident output, no traceable source.
- **Splitting the draft instead of the argument**: produces length variants.
- **One hook rewritten seven ways**: the claim underneath is identical, so the
  reader sees the repeat even when the wording differs.
- **Adding the writer first**: the most visible role, and the one that produces
  least value without an evidence packet in front of it.
- **A performance log nobody converts to rules**: analytics theatre.

## Banned vocabulary

Avoid "fully autonomous media company", "content on autopilot", "replaces a
marketing team", "repurpose", "atomize", and "one piece into fifty posts". The
first three hide the approval steps; the last three describe reformatting, and
naming the work that way produces the work. Say which argument each asset makes.

## Boundaries

- Do not publish, schedule, or send anything. The pipeline prepares packages; the
  human releases them.
- Do not record a claim without the source that supports it, and do not upgrade an
  inference to a verified claim at any stage.
- Do not introduce a claim, number, or quote during distribution that the evidence
  packet does not carry.
- Do not invent a proof object, result, or failure mode to fill an entryway the
  source does not support. Report the entryway as unavailable.
- Do not present an unscored asset set as ready, and do not resolve a collision by
  rewording rather than reassigning.
- Do not report a stage complete without the record fields that stage owns being
  filled, and do not fabricate reach or engagement. An unmeasured campaign is
  logged as unmeasured.

## Routing

- Which topics, pillars, or clusters the pipeline should work on -> use
  `suede-content-strategy`. That skill decides what it operates on; this one
  decides how it moves.
- Platform mix, cadence, calendars, listening, account audits, and Instagram
  programs -> use `suede-social`.
- Cadence, state, idempotency, and stop conditions for a scheduled stage -> use
  `suede-marketing-loops`.
- Writing the flagship for a high-stakes public surface -> use `suede-ship-copy`.
  A single shorter surface -> use `suede-copy`.
- A video moment bridged to one long-form guide -> use `suede-clip-to-guide`.
- Stripping AI writing patterns from the drafted assets -> use `suede-deslop`.
- Measurement plumbing behind the performance log -> use `suede-analytics`.
- Paid variants of these angles -> use `suede-ad-creative`.
- Agents editing code in parallel with file ownership and rollback -> use
  `suede-agent-teams`. This skill covers editorial lanes, not repository lanes.
- From `suede-content-strategy` and `suede-social`: route role contracts, the
  handoff record, and entryway assignment back here.
