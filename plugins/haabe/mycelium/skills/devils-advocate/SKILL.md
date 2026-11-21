---
name: devils-advocate
description: "Systematically challenge current assumptions before major decisions. Counters confirmation bias, groupthink, and overconfidence."
metadata:
  instruction_budget: "26"
  framework_dependency: "mycelium"
  framework_dependency_note: "This skill is designed to run within the Mycelium framework (https://github.com/haabe/mycelium). Standalone use will skip the canvas state, theory gates, and harness behavior the skill assumes. Install: /plugin install mycelium@haabe-mycelium."
---

# Devil's Advocate

Run before every major diamond transition and architecture decision. Source: Kahneman, Shotton.

## Technique 1: Pre-Mortem
Imagine it's 6 months from now and this decision FAILED spectacularly.
1. What went wrong?
2. What assumption was the weakest link?
3. What signal did we ignore?
4. Who was affected and how?

## Technique 2: Assumption Reversal
For each key assumption:
- State the assumption explicitly
- Ask: "What if the OPPOSITE is true?"
- What evidence would support the opposite?
- Is there any evidence we've dismissed? Include language read by its words: a quote that never used our term may still describe the thing, and one that used it may not (`${CLAUDE_PLUGIN_ROOT}/engine/reading-for-meaning.md`).

## Technique 3: Red Team
Attack your own position:
- What would a competitor say about this approach?
- What would a skeptical user say?
- What would a security auditor find?
- What would an accessibility advocate flag?

## 10 Challenge Questions
1. What are we most confident about? (That's where overconfidence hides)
2. What evidence have we dismissed or downweighted?
3. Are we anchored on our first idea? (Shotton - anchoring bias)
4. Have we tested with users who DON'T match our ideal profile?
5. What would make us abandon this direction entirely?
6. Are we building for ourselves or for actual users?
7. What's the simplest version that could validate/invalidate this?
8. What have we NOT measured that we should?
9. If we had to start over, would we make the same choice?
10. Who disagrees with us and what's their strongest argument?

## Technique 4: Attribution-vs-Consistency Check
Per anti-pattern *Consistency-as-Evidence* (#7) — graduated 2026-05-09 from a recurring failure where causal chains were built from observational consistency rather than verified attribution.

For each piece of evidence supporting the current claim, label it:
- **Cleanly-attributed**: the cause was demonstrably driving the effect (the action was Mycelium-specific, the variable was isolated, the alternative explanations were ruled out).
- **Consistency-only**: the data is *compatible with* the hypothesis but doesn't *isolate* the cause (the user reported X in a context where Y was also true; the trend matches the prediction but matches three other predictions equally well).
- **Unrelated**: the evidence is a different question entirely; don't include it in the chain.

If ≥1 link in a chain is consistency-only, mark the chain provisional and explicitly identify the missing attribution evidence. If N=1, do not publish a structural conclusion (e.g., "this generalizes to all users") until N≥2 with attribution. Apply this check to your own analysis pre-publish, not after the user catches it.

## Technique 5: Ambient triggering on assertion-shaped patterns
Per the bias cluster (corrections.md TL;DR — L5 sycophancy, eval overfitting, sharper-framing anchoring; common root: "agent prefers what feels right over what evidence supports"):

Beyond formal diamond-transition use, run a fast self-check whenever you write text containing structural-claim shapes:
- "X causes Y"
- "this means Z"
- "the framework needs..." / "the user needs..."
- "the right answer is..."
- "this generalizes to..." / "this applies broadly..."

For each, ask: *what specific evidence supports this claim, and does any of it merely support it by consistency rather than attribution?* (Technique 4). If you can't name cleanly-attributed evidence for the claim, downgrade it: from assertion to hypothesis, from "X causes Y" to "X is consistent with Y; attribution evidence pending."

This converts the framework's own anti-bias discipline into a per-publish self-check, not just a per-decision ceremony. Graduated 2026-05-09 from corrections.md TL;DR open candidate.

**MEASURED FIRE RATE, 2026-08-16: ZERO — and this note stays until that changes.** In a dogfood session where twelve agent claims were withdrawn or corrected, this trigger fired on none of them. The operator caught six, explicit invocation of this skill caught two, late self-review caught three, one was caught proactively. **A detector keyed on the five shapes above then scored 0 of 5 recall against the claims actually withdrawn**, because those were universals and counts — "nobody left", "every instance", "eight statements" — not causal assertions. **The five shapes named above are the wrong list for the failure population this technique exists to catch.** Keep running it; do not treat it as coverage. Technique 7 is what measured well WHEN RUN — and as of 2026-09-22 it has its own measured problem about whether it runs at all. See its section.

## Technique 7: Blind adversarial pass — measured well when run, and rarely run

**USE THIS BEFORE A CLAIM LANDS ON A DURABLE SURFACE.** Techniques 3 and 5 ask you to attack your own position. Measured against real withdrawn claims, self-attack found little and the ambient trigger found nothing. This found defects that had already survived self-review, four local gates and CI.

**PREREQUISITE, AND CHECK IT BEFORE YOU START.** This technique REQUIRES the ability to spawn a subagent. If subagent spawning is unavailable — the host forbids it, the user has asked that agents not be spawned unprompted, or the runtime has no such tool — **then the technique with the best measured result is not available to you, and the fallback is self-attack, which this skill's own measurements describe as weaker.** In that case you MUST (a) say so in the output, naming this technique as unavailable rather than silently substituting Technique 3 or 5, and (b) offer to run it if the user is willing to permit one subagent. Reported by a plugin consumer 2026-08-31, where a session-level no-subagent instruction silently downgraded the pass and nothing in the skill said that had happened.

**THE MECHANISM.** Hand a claim — plus one line describing the procedure that produced it, and **nothing else** — to an agent with **no repository access and a hard no-tool instruction**. Ask for the single most likely way it is wrong. **Explicitly permit "NO OBJECTION"**, and say that declining is valued; without that the run cannot distinguish a real finding from a slot being filled. Then **verify each candidate defect against the artifact yourself** — that step is where the value is realised.

**Why it beats a detector**: a detector must recognise an error's shape, and real error shapes are diverse and lexically slippery. A blind reader recognises nothing. It simply was not present when the claim was made, so it does not inherit the reasoning that produced the error.

### Run it like this

- **Sample mechanically** (every Nth claim), never by picking the ones you suspect.
- **Two readers, not one** — but see the limit below on what agreement does and does not mean.
- **Pre-commit what each claim already concedes, BEFORE reading any objection.** Deciding afterwards whether the artifact "already said that" is unfalsifiable; almost any objection can be matched to a nearby hedge in hindsight.
- **Count distinct findings, not objections.** Two readers hitting one claim is one finding counted twice — right for measuring agreement, wrong for counting yield.

### What it cannot do — measured, not guessed

- **AGREEMENT BETWEEN READERS IS NOT INDEPENDENT CONFIRMATION.** Two readers given the same excerpt share the same blind spot. In one run both drew the same false conclusion because the mechanical sample omitted the sentence that disambiguated two different tests. **Their converging is evidence about the excerpt.**
- **A THIRD OF THE OUTPUT MAY BE UNRULABLE.** An independent scorer marked 40% of a subsample UNSURE — "too little context", "I don't remember". **The excerpt-sized format that makes this cheap is what makes much of its output uncheckable.** Price that in.
- **"DID IT CHANGE SOMETHING" MEASURES CONVICTION, NOT CORRECTNESS.** Acting on a false objection scores identically to acting on a true one. In one run an objection was acted upon, counted as a hit, and later ruled wrong.
- **CONVERSATIONAL PROVENANCE IS INVISIBLE TO IT, AND TO GIT.** The objection above was false because the design it attacked came out of a discussion, not from the data — a fact in no file. **A human who was there outranks both the blind reader and the commit log.** This is a ceiling, not a gap to close.
- **POSITIONING IS INVISIBLE TO IT.** A phrase can be well-sourced and vivid and still be unusable because of what it argues for. Both readers attacked one candidate on provenance; the disqualifying problem was that it took the wrong side.
- **HEDGING DOES NOT PROTECT A CLAIM — IT GIVES THE READER A TARGET.** Across two runs, two pre-committed inventories predicted heavily-hedged passages would absorb objections. They absorbed one of 45. The sharpest objection of either run landed on the most self-critical passage in the corpus.

**WHAT IS NOT CLAIMED**: that this generalises. The record is one author and one project, and the person scoring the objections wanted the method to work. The first two runs: the one independent scorer agreed on eight of the nine items he could rule.

**A THIRD RECORD, 2026-09-20: ABOUT TEN BLIND-READER RUNS IN ONE DAY, EACH OBJECTION CHECKED AGAINST THE CODE OR DATA AFTERWARDS** by the session that ran them (not by an independent scorer). Six confirmed catches, every one on work that had already passed the author's own review and the local gates, so self-review caught none of the six. One refuted objection, and its reader had said in advance what the objection would reduce to if wrong. Three errors no reader could see, all caught by the founder: each needed knowledge that is in no excerpt (who owns the repository, what the repository is for, what the world outside it looks like). That is the provenance ceiling above, with three fresh instances. **On that record the blind reader catches errors in the reasoning and the human catches errors in the frame, and on that day neither caught the other's.** The comparison it was measured against is self-review, not a colleague: for a solo builder the alternative to the blind reader is the author reviewing their own work.

**MEASURED FIRE RATE, 2026-09-22: IT FIRES ON 14 DAYS OUT OF 32, AND THIS NOTE STAYS UNTIL THAT CHANGES.** A prediction frozen on the day this technique shipped asked whether a technique with a demonstrated result gets invoked when nobody asks — i.e. whether evidence in a skill file changes behaviour. It was scored against its own frozen rule and **FAILED**. Over 32 days: 47 recorded blind runs against 985 commits touching a durable surface, a rate in low single digits against a 30% bar. **Eighteen of the 47 — 38% — landed on two days.** More than half the window has none.

**THAT BIMODAL SHAPE IS THE POINT, AND IT IS THE SAME SHAPE TECHNIQUE 5 SHOWS.** T5 measured zero because nothing triggers it. T7 measures well when run and still clusters onto the days its own machinery is the topic. **The pre-registered conclusion, fixed before the data, was NOT "write it more persuasively":** a technique needs a TRIGGER, and where none can exist the skill must say so rather than let a reader assume ambient coverage. This paragraph is that saying-so.

**SO DO NOT TREAT THIS SECTION AS COVERAGE EITHER.** Two places run Technique 7 by default (2026-11-12): `/mycelium:wardley-map` step 8b, once a map is drafted, and `/mycelium:diamond-progress` step 2b-2, before the Four Risks gate is recorded as passed. In both it can only raise concerns. Everywhere else nothing invokes Technique 7. It fires when an agent reads this file and chooses to, and the operating contract is read at session start while claims land hundreds of turns later. If a durable claim matters, invoke it explicitly — by name, at the moment of the claim — rather than trusting that having read this will be enough. The one thing the measurement cannot see is the occasions nobody noticed, so **the true rate is at or below the one reported here.**

### What it stands in for: judgement, never stake

Several of the theories this framework uses end at a remedy that needs a second person. A blind pass can stand in for that person when what is missing is their **judgement**: a review, a challenge, noticing what the author cannot see, from someone who was not there when the reasoning was formed. It never stands in for their **stake**: being one of the users or the people affected, giving the project independent contact with the world outside the excerpt (sensing), or adopting the thing. A blind reader holds no stake and sees only what it is handed, so a second reader of the same excerpt is not a second contact with the world, and a subagent that says it "would use" or "would adopt" the product is not a user or an adopter. Use a blind pass to raise a concern, never to clear one, and never count its output as evidence of users, of the world outside the excerpt, or of adoption. Where the missing input is stake, say that it is a limit of working alone and get it from real people.

## Technique 6: Cunningham's Law check (publish-rough-then-iterate)

"The best way to get the right answer on the internet is not to ask a question; it's to post the wrong answer." — Ward Cunningham (community attribution).

When deciding whether to publish a draft (a memo, a finding, a position), the bias is to wait for certainty. Cunningham's Law inverts this: a *specific wrong* answer attracts correction faster than a *vague right* one. Concretely:

- A vague position ("we should think about X") gets nodded at and forgotten.
- A specific position ("X is Y because Z") gets contradicted, sharpened, or confirmed — all of which produce information the vague position can't.

Apply this when the alternative to publishing is "wait until I'm sure." If the cost of being wrong publicly is bounded (corrections.md exists, version-discipline catches drift, retrospectives review), the publish-rough-then-iterate path produces faster learning than the wait-for-certainty path. The dogfood-first discipline + receipts case structure are Mycelium's institutionalized form of this. Don't apply where the cost of being wrong is unbounded (security claims, legal positions, irreversible commitments).

## When to Use
- Before every diamond scale transition (L2->L3, L3->L4)
- Before architecture decisions
- Before committing to a specific solution
- When the team feels "certain" (certainty is a bias signal)
- **Ambient (per Technique 5)**: any time the agent writes text with assertion-shaped structural claims. This is a quick self-check, not the full ceremony. **Its measured fire rate is zero — see the note there. Do not count it as coverage.**
- **After a Wardley map is drafted, and before a Four Risks gate is recorded as passed (per Technique 7, by default)**: `/mycelium:wardley-map` step 8b and `/mycelium:diamond-progress` step 2b-2 run it; it raises concerns and never passes anything.
- **Before a claim lands on a durable surface with an evidence grade (per Technique 7)**: canvas, decision log, a results file, anything a later reader will cite. **This is the technique with a measured positive result WHEN INVOKED**, and it is the one to reach for when the alternative is attacking your own position. **It also has a measured negative result about being invoked at all** (2026-09-22, below): do not read "best technique" as "technique that happens".

## Output
Log the challenge results in .claude/harness/decision-log.md alongside the decision.

When presenting challenges to the user, apply the interface-load/problem-load discipline in `${CLAUDE_PLUGIN_ROOT}/engine/status-translations.md`: lead with the substantive challenge and what it puts at risk; cut framework-facing narration (technique numbers, ceremony names).
