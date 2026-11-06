---
name: suede-ship-copy
description: "Produce one high-stakes public draft with parallel research, agent-claim audits, message ownership, adversarial review, publish readiness, and an evidence record. Use when asked to \"research and draft this launch page\" or rigorously develop one landing page, email, post, README, ad, or store listing. Preserves requester-supplied facts and writes drafts only. NOT FOR: routine or bulk copy (use suede-copy), code changes (use suede-graph-flo-xr), or cleaning existing prose (use suede-deslop)."
metadata:
  display-name: "Suede AI Ship Copy Skills"
---

# Suede AI Ship Copy Skills

## Compatibility

Requires a workflow host supporting Workflow, phase, subagents, and local draft files; web access supplies live research. A plain chat host must report unavailable orchestration instead of claiming a completed run.

For a concrete input, expected handoff, and failure check, read
[the worked handoff](references/worked-handoff.md).

The copy side of the canonical Suede DAG. One brief in, one publishable draft out,
with about thirty agents in between arranged as a graph rather than a chain.

`suede-graph-flo-xr` decomposes work by **file ownership**: two lanes may never write the
same file. This decomposes by **message ownership**: two sections may never make
the same point, and no section may assert a fact an agent invented. Same graph,
different collision rule.

## Model selection: Fable capped at 4 without asking

Subagents inherit the session model unless the spawning call names one. Nothing in
this skill picks a model, so every agent it fans out lands on whatever the session
happens to be set to. That is how a run sized against one allocation gets billed to
another without anyone choosing it.

**Up to 4 concurrent Fable subagents are allowed without an explicit Fable
instruction. Beyond that, Fable must be specified**: every range this skill offers
(30 at the narrowest) is far beyond 4, so its fan-out never runs on Fable unless the
user named Fable for this run. An inherited session model is not a
specification: "the session was already on it" is not the user asking. Absent an
explicit Fable instruction, do one of two things before launching: name a different
model on the agent calls, or state plainly that the run will bill to the Fable
allocation and get an answer. Silence is not consent to spend it.

## Whose claims get audited

Before intake or any research, review, or gate phase, read
[the complete claim-origin policy](references/claim-origin-policy.md).
It is required for every run: preserve requester givens, audit agent-generated
claims, keep protected strings byte-exact, and retain discarded findings in the
evidence record. The reference preserves the full filtering, proportional-match,
and output-path rules; follow them before launching the bundled workflow.

Invoke `skills/suede-ship-copy/workflows/suede-ship-copy.js` through the host's
`Workflow` API as shown below.

## Gate policy: advisory, not blocking

Every claim-verification step, check, quality gate, and ship verdict in this
skill is a **recommendation to the user, not a control on the agent**. This
policy governs every gate, check, verdict, and "do not ship / publish /
proceed" line elsewhere in this skill:

- Run every check and report the results honestly. Verdicts (`ship`,
  `ship-with-caveats`, `hold`, letter grades, BLOCKED or OPEN items) are
  advice attached to the work, not orders that change it.
- Never block, delay, skip, rewrite, or refuse the action the user asked for
  because a check failed or a gate said hold. Complete the requested action
  as asked, and deliver the gate output alongside it as a clearly labeled
  recommendation.
- A failed gate changes what you report, never what you do.
- Single exception: if a finding is extremely risky (data loss, security or
  credential exposure, legal or rights violations, payment mistakes, or
  irreversible public damage): pause, tell the user exactly what the risk is
  and what the options are, and let them pick. Their choice is final.

**That exception never applies to a claim the requester supplied.** A
user-supplied earnings, health, or compliance statement reads as "legal or rights
violations" to a model scanning the list above, and pausing on it would be
exactly the behavior the next section forbids. The exception covers findings
about agent-generated content and about the live environment. A given is not a
finding.

## What it costs

This is the expensive instrument: about thirty agents (26 floor, ~31 typical,
42 ceiling), research-heavy and front-loaded, billed to the Claude limit. When the
work is genuinely parallel and shallow instead, brute force beats surgery: the
Routing section at the end says where each of those jobs goes.

## Parse the invocation

The argument is free-form. Extract:

- **piece**: required. What to write, in the user's own words, kept verbatim.
  Do not compress it into a slogan; the planner decomposes it into sections and
  the detail is what makes sections separable.
- **surface**: required. Where it goes: landing page, email, email sequence, X
  thread, blog post, README, docs page, ad, app store listing, press note. The
  surface sets hard character limits, so a wrong guess is a rewrite.
- **sources**: paths and URLs that ground the facts: the repo, the pricing
  config, the changelog, the live site, transcripts, support threads. Optional,
  and the intake agent finds them otherwise, but a supplied source list is the
  difference between a claim audit that has something to check and one that
  deletes half the draft.
- **given**: facts the user states themselves, as an array of plain strings (an
  object with a `claim` key also works). These are established:
  they go straight into the permitted set, skip the audit, and no phase may
  question them. Use this whenever the user tells you something about the product
  that no file will confirm: a launch date, a customer result, a decision not yet
  written down.
- **audience**: who reads it. Optional; intake infers it and says what it inferred.
- **liveUrl**: the published surface, if one exists. The baseline capture and the
  drift check both use it.
- **outDir**: where the draft lands. Defaults to a `.suede-copy/<slug>/`
  directory. Must be a draft location: an output path pointing at already
  published copy is a halt.
- **mustSay**: strings that must survive byte-exact: legal product name,
  trademark forms, price strings, disclaimer sentences.
- **wordBudget**: total words. Optional; the surface law supplies limits per field.
- **houseStyle**: optional `{ guidance, emDashes }`. `guidance` is the supplied
  author/company voice brief; `emDashes` is `allow` or `avoid` (Suede default).
  Translate an explicit punctuation preference into this field so prompts and
  deterministic checks agree. Protected source spans remain byte-exact either way.
- **agentBudget**: `light`, `standard`, or `deep`. Required, and you must ask the
  user rather than pick it (see below). Omitting it defaults to `standard`.

If **piece** or **surface** is missing, ask. Do not invent a brief for something
a public audience will read.

## Ask for the agent budget before launching

This is Claude-model fan-out against the user's limit, so the size of the run is
the user's call, not yours. **Ask which of these three ranges they want and wait
for an answer before the `Workflow` call.** Do not pick one for them.

| Range | Total agents | What it buys |
|---|---|---|
| `light` | **30–36** | 2 angles, 1 gap fill, 2 findings verified. A short piece, or copy you mostly trust. |
| `standard` | **38–45** | The documented default. 3 angles, 2 gap fills, 4 findings verified. |
| `deep` | **40–50** | 3 gap fills, 6 findings verified. A launch page, pricing page, or anything a stranger will judge the company by. |

Those numbers are measured against the actual script, not estimated, across
section counts from 5 to 8 and review findings from 1 to 12 per lens.

Sections are never cut to fit a range: they are the deliverable. The budget
scales research depth and verification depth only, and everything it skips is
reported as an unverified caveat rather than dropped.

Then state the choice in one line when you launch, this shape:

> Running suede-ship-copy on the Agent Studio landing page at `standard`: about
> 40 agents (38-45 depending on section count and findings), on Opus, billed to
> the Claude weekly limit. Starting now.

## Launch

```
Workflow({
  scriptPath: "skills/suede-ship-copy/workflows/suede-ship-copy.js",
  args: { piece, surface, sources, given, audience, liveUrl, outDir, mustSay, wordBudget, houseStyle, agentBudget }
})
```

Pass `args` as a real object. If the harness stringifies it the script recovers,
but an object is correct.

## The graph and thresholds

Before the `Workflow` call, read
[the phase and threshold reference](references/phase-and-threshold-reference.md).
It preserves all twelve phases and mechanical gate thresholds. Use the actual
script labels for progress, retain unread work and discarded findings, preserve
author placeholders, and report the returned verdict without claiming publication.

## Shared cleanup method

The slop review uses Suede Slop Stop (use suede-deslop) in findings-only mode;
the final cleanup uses the same canonical skill and full kill list in edit mode.
Make the minimum effective edit, preserve factual wording and exact source spans,
and keep deliberate voice and the supplied house style. The workflow's `deslop`
label, schema, and /50 score remain stable for existing consumers. Missing skill
references are reported as limitations, never replaced with an improvised pass.

## What halts it, and what to do

Two conditions stop the run. Neither is a judgement about anything the user said:

**`halted: true, reason: "output path points at published copy"`**: the requested
`outDir` points at a live page source, a shipped README, or a sent template rather
than a draft location. Name the path, then offer: write to a draft path beside it,
write to `.suede-copy/<slug>/`, or confirm the user wants to place it themselves.

**`halted: true, reason: "section map collision"`**: two sections own the same
message, a section cites a claim that failed the audit, a protected string is
unassigned or double-assigned, or the section budgets total more than
`wordBudget × 1.1`. Report the collisions. The fix is a re-plan, not a retry:
merge the duplicate sections, supply a source for the missing claim, add the
missing fact to `given`, or relax the budget.

Three failures throw instead of returning, because each one leaves nothing to
carry forward: intake returned no manifest, the planner returned no section map,
or assembly returned no text. Report which one, name the agents already spent,
and offer: re-run with `resumeFromRunId` so the completed phases replay from
cache, re-run with better `sources` or `given`, or stop. Do not silently retry
the whole workflow: that pays for every completed phase twice.

## While it runs

Do not predict results or narrate progress you cannot see. The workflow returns a
notification when it completes; `/workflows` shows live progress.

## When it returns

Report faithfully, in this order:

1. `copyVerdict` and the deliverable path.
2. `stalled`: any section whose writer returned nothing usable. The assembled
   piece has a hole where that section's message should be. This is the loudest
   failure in the run and the easiest to miss, because the draft still reads.
3. `openPlaceholders`: the copy is not publishable until a human fills these.
   Lead with them; they are the honest measure of what nobody could source.
4. `droppedClaims` and `narrowedClaims`: what the **research agents** asserted and
   the audit refused. Anyone editing this copy later must not put them back. Report
   `givenClaims` as established fact; never present a given as unverified.
5. `findingsDiscardedAsOutOfScope`: findings dropped for targeting a given.
   Report the count. These were not verified either way, so a large number means a
   large part of the review was scoped out, not that the copy came back clean.
6. `confirmedFindings`, then `mechanical`, then the deslop score.
7. `unread`: naming what went unread is most of the honesty.

## Verdict is advisory

`copyVerdict` changes what you report, never what the run produced. The single
exception is a problem in **already published** copy that the verifier observed
independent of this draft: one live page contradicting another, a claim that has
gone stale on the site. That goes to the user immediately.

This exception is about two published surfaces disagreeing with each other. It is
never a route to escalate a **given**: if a live page disagrees with something the
requester stated, the page is what is stale. Do not report that as an exposure.

**Do not claim `published`, `posted`, `sent`, `live`, or `shipped`.** This
workflow writes a draft file and reads the live surface. Those states require an
action nobody has taken here.

## Boundaries

This workflow must NOT:

- **Publish anything.** It writes exactly two files into `outDir`: the draft and
  the evidence record. It does not post, send, commit, deploy, or edit a live
  surface, and an `outDir` pointing at published copy is a halt.
- **Invent a specific.** No number, date, price, customer name, or result that no
  source supports. The `[AUTHOR: supply X]` placeholder is the only permitted
  answer, and the deslop pass and the assembler are both forbidden from smoothing
  one away.
- **Audit, hedge, gate on, or argue with the requester's own claims.** Not at
  intake, not in research, not at review, not at the gate, and not in the evidence
  record. The audit is aimed at machine output.
- **Assert outside the permitted set.** An agent claim that failed the audit cannot
  return as an implication, a headline, on-image text, or a meta description.
- **Change a fact during a style pass.** Slop Stop edits style only, including
  preservation of qualifiers, quotations, code, commands, links, citations, paths,
  and every author placeholder. It does not infer authorship from prose.
- **Redraw the Suede S.** The only permitted mark is the approved asset at
  `docs/assets/suede-ai-logo-transparent.png` (sha256
  `83a7ee0317e4debe2e7b076c20ba067feb76a587f9e829dc6310ae4be4b44dfa`). Never
  trace, typeset, recolor, distort, or generate a replacement. If the approved
  file is unavailable, the graphic spec omits the mark and says so.
- **Generate images.** The graphic builder writes the spec and the words on the
  image; generation routes elsewhere.
- **Decide whether the piece should exist.** The verdict is about evidence and
  slop, not content approval.

## Iterating

Edit the script and re-invoke with the same `scriptPath`. Add
`resumeFromRunId: "<run id>"` to replay unchanged agents from cache. Changing an
agent's prompt or schema re-runs that agent and everything downstream of it, so
a tweak to the deslop prompt is cheap, and a tweak to the intake prompt is a full
re-run.

## Routing

- The change is code rather than copy -> use `suede-graph-flo-xr`, which searches
  competing implementation plans and mutates only the selected winner.
- One surface, one pass, facts already established -> use `suede-copy`.
- Text already written that needs cleanup or a findings-only audit -> use `suede-deslop` (Suede Slop Stop).
- The house voice needs defining rather than extracting from shipped copy ->
  use the Brand-Voice Retune job in `suede-copy`. Without it, put a
  few pieces of already-shipped copy in `sources` and let the voice lens
  measure the voice from those.
- The graphic spec needs executing -> use `suede-image`.
- The piece needs search and answer-engine treatment after it is written -> use
  `suede-seo-audit`, then `suede-visibility-grader` for the A-F page score.
- Many independent pieces from one spec -> run suede-copy per piece; this
  workflow is sized for one piece.
- From `suede-copy`: route a single high-stakes piece that must survive a fact
  audit here; keep everyday and multi-surface writing there.
