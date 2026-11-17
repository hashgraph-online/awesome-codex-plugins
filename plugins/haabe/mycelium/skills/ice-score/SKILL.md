---
name: ice-score
description: "Use to prioritize solutions or opportunities using ICE scoring with evidence-backed confidence."
metadata:
  instruction_budget: "35"
  framework_dependency: "mycelium"
  framework_dependency_note: "This skill is designed to run within the Mycelium framework (https://github.com/haabe/mycelium). Standalone use will skip the canvas state, theory gates, and harness behavior the skill assumes. Install: /plugin install mycelium@haabe-mycelium."
---

# ICE Score Skill

ICE scoring as Itamar Gilad defines it: Impact x Confidence x Ease, each 0-10, with Confidence taken from his Confidence Meter.

## Preflight: Read target canvas file(s) before any Write/Edit

**Hard rule.** Before issuing `Write` or `Edit` against any `.claude/canvas/*.yml`, use the **Read tool** on that file in this session. Claude Code's Read-before-Write check requires the `Read` tool specifically — `cat`/`head`/`grep` via Bash do NOT satisfy it.

**Edit vs Write — different cost profiles** (verified 2026-05-14):
- **`Edit`** (exact-string replacement): `Read` with `limit: 1` satisfies the check at ~50 tokens. State-tracking is per-file, not per-byte — subsequent `Edit` calls work anywhere in the file. Use this for partial updates against large canvas files (e.g., `purpose.yml` at 800+ lines).
- **`Write`** (full replacement): do a **full Read** first. Write obliterates the file; you should see what you're about to replace. The `limit:1` shortcut is *not* appropriate here.

**ID-bearing entries — scan the ID space before assigning** (added 2026-05-15, v0.23.19): When adding a new component, opportunity, solution, or any other ID-bearing entry to a canvas file, run a Bash grep first to confirm the next ID in your prefix sequence is actually free:

```
grep -o "<prefix>-[0-9][0-9]*" .claude/canvas/<file>.yml | sort -u -t- -k2 -n | tail -3
```

Replace `<prefix>` with the canvas's ID prefix (`comp` for landscape, `opp` for opportunities, `sol` for solutions, `ht` for human-tasks, etc.). Then pick the next free integer, **matching the zero-padding already used in that file**. The sort is NUMERIC (`-t- -k2 -n`) rather than lexical, and that is not pedantry: a plain `sort -u` orders `ht-1` after `ht-080`, so on a canvas with inconsistent padding it reports the wrong maximum and the next ID collides. Verified on the dogfood repo 2026-08-13, where lexical sort returned `ht-1` as the highest human-task ID against an actual `ht-080`. `grep -o` is also deliberate: it matches IDs wherever they appear, including cross-references and prose, so an ID that was promised somewhere but not yet defined is not handed out twice. `validate_canvas.py` has a per-file duplicate-ID check (it reports `duplicate id '<id>'`) that catches the failure on CI, but a duplicate can persist in the working tree for days if CI isn't run between edit and discovery; that happened on 2026-05-15, when a duplicate ID was created in `landscape.yml`.

Original failure mode: anti-pattern #7 instance #5, 2026-05-09 — agent conflated Bash `head` with the Read tool, lost ~14k tokens to a Write-fail → remedial-full-Read → re-Write loop. The `limit:1` discipline (graduated 2026-05-14, v0.23.18) prevents the second-order cost where the agent *correctly* follows the rule but full-Reads every time. The ID-scan discipline (graduated 2026-05-15, v0.23.19) prevents the related class where the agent reads enough of the file to satisfy the Edit check but not enough to see existing ID assignments — kin to anti-pattern #8 (Stale State Read).

If this skill writes to multiple canvas files, register each one first (limit:1 for Edit-only paths; full Read for Write paths) AND ID-scan any prefix you intend to assign.

See `${CLAUDE_PLUGIN_ROOT}/engine/agent-operating-contract.md` *Canvas writes — Read before Write* for the canonical rule.

## Which ICE this is

> **Why this note exists.** ICE has two versions in the literature, and until 0.319.0 this skill
> matched neither. It averaged the three numbers, which is Ellis's arithmetic, while describing
> Gilad's Confidence Meter with values and bands that are in no version of his meter. The
> maintainer chose Gilad's version on 2026-10-11, after a read of both authors' own texts. If you
> scored with this skill before 0.319.0, read the last paragraph of this section.

**Ellis's ICE** ranks a growth team's backlog of experiments. Sean Ellis invented it: *"At
GrowthHackers, Sean developed the ICE score system"* (Ellis & Brown, *Hacking Growth*, ch. 4). The
person who submits an idea rates it *"on a ten-point scale, across each of the following three
criteria"*, and *"Then those ratings are averaged to provide an aggregate score for each idea"*
(same chapter). His Ease is the cost of the test, not of the finished thing: *"Ease is the measure
of the time and resources needed to run the experiment."*

**Gilad's ICE** scores product ideas in an idea bank. He credits Ellis as the inventor. His version
differs from Ellis's in four ways: the scale starts at 0, Ease is the effort to build the idea in
full, Confidence is worked out from evidence with his Confidence Meter, and the three are
multiplied. The score is the product: *"With ICE, each idea is assigned three numeric attributes:
Impact, Confidence, and Ease, each in the range 0–10. A fourth value holds the ICE score, which is
simply the three values multiplied together"* (Gilad, *Evidence-Guided*, ch. 3). His ebook also
allows the average: *"We multiply (or average) Impact, Confidence and Ease to get the ICE score."*
(*ICE Done Right*, p. 4). Every worked example of his that was read multiplies, and in the texts
read he does not argue for one operation over the other.

**Mycelium uses Gilad's, multiplied.** What is scored here is a product idea (an OST solution leaf,
a GIST idea), and the Confidence comes from his meter. The reasoning for the product is Mycelium's
own and is not a statement of his: the meter's values are small and far apart (0.01 for a
conviction, 3.0 for a test result), so under an average a Confidence of 0.16 and a Confidence of 10
differ by about 3.3 points out of 10, while under the product they differ by a factor of about
sixty. With the average, the evidence behind an idea would hardly move its rank.

**What changed, and when.** Until 0.229.0 this skill multiplied three 1-10 ratings and cited the
arithmetic to Ellis, who averages. From 0.229.0 to 0.318.x it averaged (`docs/errata.md` A1). Since
0.319.0 it multiplies, with the meter (`docs/errata.md` A7). **A score written before 0.319.0 was
computed differently and cannot be ranked against a score from this skill**: it is an average (or,
before 0.229.0, a product) of three 1-10 ratings, with a Confidence that did not come from the
meter. Two cases:

- **The leaf's decision is closed** (shipped, discarded, archived): leave the stored score exactly
  as it is. It is the record of how that call was made. Nothing rewrites it, and
  `scripts/check_ice_aggregate.py` keeps it in a baseline so it is never reported as an error.
- **The leaf is still a live candidate in a comparison you are making now**: rescore it now from
  its evidence, all three factors, before you rank. That is ordinary rescoring (Step 6), not a
  conversion: do not turn an old average into a product by arithmetic.

## Workflow

ICE scoring is applied to **OST solution leaves** (and to the GIST ideas that come from them).

### Step 1: Read the Four Risks assessment (Mycelium's addition)

For each solution leaf in `.claude/canvas/opportunities.yml`, check that `four_risks` has been assessed:
- **Value** (product lens): Do users want/need this?
- **Usability** (design lens): Can users figure it out?
- **Feasibility** (engineering lens): Can we build it within constraints?
- **Viability** (cross-cutting): Does it align with business/legal/ethical constraints? Inside it, ask the ethics question by name: **"Should we build it?"** Assuming it works exactly as designed, could it harm the people who use it or the people it reaches? Answer it with `/mycelium:harms-check`; if the solution has no user-facing flow and reaches no vulnerable people, say so in one line. Still four risks: this is a question inside Viability, not a fifth risk (`${CLAUDE_PLUGIN_ROOT}/engine/theory-gates.md`, Four Risks gate, for the Cagan source).

If any risk dimension is missing, assess it first. Each dimension must have its own evidence — a single combined statement fails (Torres Product Trio rule).

> **This step is Mycelium's own, and neither author's.** The leaf lifecycle
> (`engine/leaf-lifecycle.md`, Phase 2 before Phase 3) puts the risk assessment before the score, so
> the scorer has four separately evidenced readings to hand. Neither Ellis nor Gilad computes ICE
> from a risk assessment. Until 0.319.0 this skill said *"the risks are the inputs, ICE is the
> output"* and derived Impact from the value, usability and viability risks and Ease from the
> feasibility risk; that derivation is in neither author's text and is withdrawn. The assessment is
> now something you read while scoring (Step 2 says where), and the three factors are defined as
> Gilad defines them. Gilad does use Cagan's four risks, for a different job: they are what an
> idea's validation steps test (*Evidence-Guided*, ch. 4: *"Marty Cagan lists four areas of
> assumptions/risks"*).

### Step 2: Score the three factors, each 0-10

#### First, name the metric Impact is measured against

*"Impact is an estimate of how much the idea will improve the target metric."* (Gilad,
*Evidence-Guided*, ch. 3). So before any number is written, name the metric. He offers the
company's North Star Metric, a team's local North Star Metric, or a key result, and asks that an
idea bank be *"ranked against a consistent, long-standing metric"* (*ICE Done Right*, p. 9).

In a Mycelium project that metric is the desired outcome the leaf's opportunity sits under
(`opportunities.yml`, the outcome's `metric`, which names the North Star input it serves). For a
GIST idea it is the goal the idea is filed under in `gist.yml`. **Every idea in one ranking is
scored against the same metric.** Two scores against different metrics cannot be compared, and if
the leaves you were asked to rank sit under different outcomes, say so and rank each group on its
own.

#### Then score Impact, Ease and Confidence

Score **Impact** and **Ease** first, then **Confidence**: Confidence is about the other two.

**Impact (0-10): how much the idea will improve the metric you just named.**

- *"When you create your own impact table imagine 10 out of 10 as the maximum impact possible for
  a single idea, and organize the other levels accordingly."* (*Evidence-Guided*, ch. 3). The scale
  is the project's own; keep it the same for every idea in the ranking.
- **0 is a legal Impact.** His range starts at 0, and he reminds the reader: *"don’t forget None
  for Impact, as we saw that’s the case with most ideas"* (same chapter). An idea that will not
  move the metric scores 0 and totals 0.
- An idea that prevents a drop in the metric is scored the same way, on the size of the drop it
  prevents (same chapter).
- It is an estimate: *"It’s impossible to predict impact accurately, the number is always a guess
  or a projection, so don’t strive for perfection."* (same chapter). His ways to improve it, from
  least to most accurate: a guesstimate, past ideas of the same kind, assessment and fact-finding,
  a back-of-the-envelope calculation, a simulation, a test.
- *Mycelium's addition:* read the value, usability and viability assessments from Step 1 while you
  estimate. They say whether people want this, can use it, and whether the business can carry it,
  which bears on whether the metric moves at all. They inform the estimate; they are not a formula
  for it.

**Ease (0-10): the effort to build the idea in full.**

- *"Ease is an estimation of how hard or easy it is going to be to implement this idea in full.
  Ease is typically the inverse of effort (person-week) — low ease means high effort and vice
  versa."* (*Evidence-Guided*, ch. 3).
- Estimate the whole thing, not the next experiment: *"consider how long it will take to build the
  whole idea in full (production-ready) without stopping to test it."* (same chapter). This is
  where Gilad's Ease differs from Ellis's, which is the cost of running the test.
- The scale is the project's own: *"each team should build its own scale based on its own
  velocity."* (same chapter). Keep it the same for every idea in the ranking.
- *Mycelium's addition:* read the feasibility assessment from Step 1 while you estimate (the
  complexity, the dependencies, the unknowns, any spike that was run). It informs the effort
  estimate; it is not a formula for it.

**Confidence (0-10): how strong the evidence is that the Impact and the Ease are right.**

*"Confidence asks the question, “How sure are we that the idea will have the expected Impact and
the projected Ease?” Lower confidence scores indicate lower certainty. A score of 10 indicates
absolute conviction."* (*Evidence-Guided*, ch. 3). It is not a rating you choose. It is worked out
from the evidence you hold, with the Confidence Meter, and a strong feeling earns almost nothing:
*"Feeling strongly that your idea is good should give you little or no confidence no matter how
smart you are, what track record you have, and what position you hold in the company."* (same
chapter).

#### The Confidence Meter

The Confidence Meter is Itamar Gilad's (published by him under CC BY-SA 4.0). The weights, the caps
and the examples in brackets below are those of his spreadsheet version; the sentence about launch
data is from *Evidence-Guided*, ch. 3.

> **Licence of this table.** It is adapted from "Confidence Meter" by Itamar Gilad, which he
> licenses under Creative Commons Attribution-ShareAlike 4.0 International
> (http://creativecommons.org/licenses/by-sa/4.0/; the statement is in his spreadsheet). Changes
> made here: his rows are laid out as one table with the group caps beside them, and a launch-data
> row is added from the dial in *Evidence-Guided*. The table and the "How to work it out" paragraph
> under it are offered under the same CC BY-SA 4.0 licence, not under this repository's MIT
> licence. The rest of this file is the repository's own.

| Group | Evidence you hold for this idea's estimate | Each piece adds | The group adds at most |
|---|---|---|---|
| 1 | Self conviction | 0.01 | 0.1 for the three together |
| 1 | Pitch deck | 0.02 | |
| 1 | Thematic support (aligns with: vision/strategy, current trends/buzzword, outside research, macro trends, product methodology) | 0.05 | |
| 2 | Other's opinion (the team / management / external expert / investor / press think it's a good idea) | 0.1 | 0.5 for the two together |
| 2 | Estimates and plans (back of the envelope calculations, Eng / UX feasibility evaluation, project timeline, business model canvas) | 0.3 | |
| 3 | Anecdotal evidence (support by a few product data points, sales request, 1-3 interested customers, one competitor has it) | 0.5 | 1.0 |
| 4 | Market data (supported by surveys, smoke tests, all competitors have it) | 1.0 | 3.0 for the two together |
| 4 | User/customer evidence (supported by: lots of product data, top user request, interviews with 20+ users, usability study, MVP) | 2.0 | |
| 5 | Test results (supported by longitudinal user studies, large-scale MVP, alpha/beta, A/B experiments) | 3.0 | 5.0 |
| | Launch data (the idea is launched, with *"consistent usage, positive customer feedback, and the target metric that we aimed for should indeed improve"*) | Confidence is 10 | |

**How to work it out.** For each row, count the pieces of evidence of that kind you hold and
multiply by the row's weight. Add the rows of a group and cap the sum at the group's maximum.
**Confidence is the sum of the five capped groups.** Without launch data it cannot exceed 9.6
(0.1 + 0.5 + 1.0 + 3.0 + 5.0), and without test results it cannot exceed 4.6. The idea is at 10
only when it has launched and the launch data bears the estimate out.

Three rules of his for counting, all from *Evidence-Guided*, ch. 3:

- **The evidence must support this idea's estimate, not the topic.** When it bears on the problem
  but not clearly on this solution, take part of the weight: *"we can use a factor, say 0.5, to
  show that evidence is not conclusive"*.
- **Evidence against your estimate counts only if you change the estimate.** *"We could have
  chosen to reject the evidence and stick with our original estimate, in which case we’d get no
  confidence boost. But we chose to update the impact estimate based on the model, and thus got a
  confidence boost of 0.3."*
- **You do not need every kind of evidence for every idea.** How far to go depends on the size and
  risk of the idea (see Step 3, the cutoff on Confidence).

**His worked example** (same chapter): self conviction 0.01, thematic support 0.05, others'
opinion 0.1, estimates and plans 0.3, anecdotal evidence 0.5, and user/customer evidence at half
weight, 0.5 x 2.0 = 1.0. *"Our total confidence score is: 0.01 + 0.05 + 0.1 + 0.3 + 0.5 + 1.0 =
1.96 out of 10. This number is obviously not exact, but it places this idea in the area of
medium-low confidence."*

**The words he puts on the numbers.** In his text 0.16 is *"near-zero confidence"* and 1.96 is
*"medium-low confidence"*, and *"medium-high confidence levels"* are *"3.0+ on the confidence
scale"* (*Evidence-Guided*, ch. 3 and ch. 4). His dial has six bands, Near-Zero, Very Low, Low,
Med-Low, Medium and High, and does not print one number per kind of evidence. Use his words where
his text gives them, and otherwise report the number.

> **His published versions of the meter differ from each other, and this is the spreadsheet one.**
> The spreadsheet (the copy read is undated) carries the weights and caps in the table. The text of
> *Evidence-Guided* gives the same weight for each kind of evidence it puts a number on (0.01, 0.05,
> 0.1, 0.3, 0.5, 1.0, 2.0, 3.0; the pitch deck gets no number there, only *"near-zero
> confidence"*). The dial in the book (Figure 3.5) prints the ring marks 0.01, 0.03, 0.1, 0.2, 0.5,
> 1, 3, 5, 10; the same dial in *ICE Done Right* (p. 6) prints 7 where the book prints 5. His 2018
> article (*"Product Discovery With ICE and The Confidence Meter"*) works an example with an earlier
> calibration that reaches 6.5 after an MVP. The spreadsheet has no row for launch data; the 10 is
> the dial's mark at Launch data. Until 0.319.0 this skill described the meter as *"0.01=opinion,
> 1=anecdotal, 5=market data, 8=A/B test, 10=launch data"* and scored Confidence in bands of 1-3,
> 4-6 and 7-10. Those values are in none of his versions (market data is 1.0, not 5; no version has
> an 8), the bands were Mycelium's, and both are withdrawn.

### Step 3: Calculate, rank, and read the result for what it is

**ICE = Impact x Confidence x Ease.** Write the total with at most two decimals: *"the decimal
point doesn’t really matter; these are not exact numbers"* (*Evidence-Guided*, ch. 4). With the
meter most totals are small: his own examples run 9 x 0.6 x 5 = 27, 5 x 3.5 x 5 = 87.5 and
9 x 2.0 x 5 = 90 (*ICE Done Right*, pp. 5 and 7). Rank the leaves that share a metric by total.

**What the total is: a hint for comparing these ideas, today.**

- *"The scores themselves are meaningless — they’re just a way to compare ideas, but sorting ideas
  by ICE scores gives us an order of priority."* and *"ICE scores give us a hint— knowing what we
  know now, these are the ideas that look most promising. ICE does not guarantee that these are the
  best ideas, or that they will even work."* (*ICE Done Right*, p. 4).
- **Never report a total without its three factors.** Of his own five-step example he writes:
  *"Note that the three components of ICE—Impact, Confidence, and Ease—were far more helpful than
  the total ICE score, which created a number of false signals until Step 4."* (*Evidence-Guided*,
  ch. 4). And: *"The one number you should be most suspicious of is the ICE score."* (ch. 3).
- **A total resting on low Confidence is the least reliable.** *"the ICE scores are quite
  unreliable as long as confidence levels are low; they can fluctuate and change strongly given new
  information"* (ch. 3). When two leaves are close, say which one is untested.
- **The order is a recommendation.** *"The ICE priority order is just a recommendation. You should
  apply judgement. It’s okay to occasionally boost a low/medium-ranking idea."* (*ICE Done Right*,
  p. 7). His alternative to one sorted list is to pick inside confidence groups: *"So you can split
  your list of candidate ideas into these three groups by level of confidence, and pick ideas in
  each."* (*Evidence-Guided*, ch. 3): some low-confidence ideas for early validation, some
  medium-confidence ideas for early testing, a few high-confidence ideas for advanced testing and
  delivery.
- **Being picked is not a commitment to build.** *"picking an idea does not mean committing to
  building and launching it, but rather putting it into validation and acting on the evidence. No
  idea should be exempt from this rule."* (ch. 3).

**There is no threshold on the total.** No source gives an ICE total a pass mark, and Mycelium has
none. (Until 0.319.0 `engine/adaptive-thresholds.md` carried one, `ice_advance`, default 100;
retired.) **The one cutoff in the literature is on Confidence, before delivery:** *"As a general
rule you should only launch ideas that have reached at least medium Confidence."* (*ICE Done
Right*, p. 14) and *"With most ideas you want to reach at least medium-high confidence levels (3.0+
on the confidence scale) before you switch into delivery mode, and with bigger or riskier ideas you
should go further."* (*Evidence-Guided*, ch. 4). Mycelium already holds that cutoff, as the L4
entry lock: `scripts/scale_locks.py`, described in `engine/diamond-rules.md` (the entry locks). The
lock reads the KIND of evidence recorded behind the solution, not the Confidence number written
here, so a number you write in this skill opens nothing.

**A leaf that ranks low is parked, not killed.** Gilad keeps such ideas: *"Parked – ideas that we
feel don’t make the cut. This idea bank can be as long as needed and hold ideas indefinitely. It’s
good to keep even what seem like bad ideas, in case they remerge."* (*ICE Done Right*, p. 9). In
Mycelium a low-ranked leaf stays on the tree with its score and is sequenced later. A leaf is
archived only when its riskiest assumption is invalidated by a test (`engine/leaf-lifecycle.md`,
Phases 4 and 5), never on its score.

### Step 4: Identify riskiest assumptions

For the top-ranked solutions, extract the **highest-risk assumptions** from the Four Risks assessment — these are what `/mycelium:assumption-test` should target first. Prioritize assumptions where importance is high but evidence is low.

### Step 5: Bias check

Are high-scoring items benefiting from availability bias, IKEA effect, anchoring, or **hyperbolic discounting** (overweighting near-term Impact at the expense of longer-horizon outcomes)? Review for bias after scoring, before acting. *Source for hyperbolic discounting: Laibson, "Golden Eggs and Hyperbolic Discounting" (1997) — when the Impact dimension is rewarded for "what we can ship this sprint," delayed-payoff opportunities get systematically under-scored.*

### Step 6: Rescore whenever something is learned

A score is a running record, not a verdict given once. Gilad: *"I suggest that every time you learn
something new that changes your perspective on an idea, whether through reviews, data analysis,
research or experiments, you should rescore it."* (*ICE Done Right*, p. 15). His four occasions
(p. 8): *"When we’re looking at a new idea (triage)"*, *"When we’re choosing ideas to work on
(filtering)"*, *"When we find new data/evidence pertaining to an idea (learning)"*, and
*"Periodically, when we’re reviewing our idea banks against the goals (maintenance/hygiene)"*.

- All three factors move, in both directions. A test can raise Confidence while it cuts Impact:
  *"At the end of each successful step we can re-estimate the Impact and Ease of the idea with
  higher Confidence and adjust our investment in it accordingly."* (*Evidence-Guided*, ch. 4).
- Replace the three factors and the total on the leaf together, so the stored total is always the
  product of the stored factors. `scripts/check_ice_aggregate.py` checks exactly that.
- Scoring once and building in that order is the misuse he names: *"With this naive version, people
  use ICE to rank their ideas once and then go ahead and develop according to the order of
  priority."* (*ICE Done Right*, p. 16).
- At triage keep it short: *"Try not to spend more than a few minutes on each idea."* (*ICE Done
  Right*, p. 12).

### Output

**Lead with the recommendation** (Hick's Law, per `harness/design-principles.md` — a flat N-row ranking manufactures decision-tax; graduated from two consecutive `/framework-health` 4e flags, 2026-06-05 + 2026-06-12):

```
**Recommended: [top solution] (ICE [total] = Impact [I] x Confidence [C] x Ease [E])** — [one line: why it leads + the single riskiest assumption to test first]

Impact is measured against: [the metric named in Step 2]

| Solution | Value | Usability | Feasibility | Viability | I | C | E | ICE | Riskiest Assumption |
|----------|-------|-----------|-------------|-----------|---|---|---|-----|---------------------|
| ...      | risk  | risk      | risk        | risk      | X | X.XX | X | I x C x E | [what to test] |

Confidence, per solution: [solution]: [each kind of evidence counted and what it added] = [C]
```

The total is never shown without the three factors beside it, and each Confidence is shown with the evidence it was summed from, so a reader can check it against the meter. The four risk columns are Mycelium's addition (Step 1).

If the top two scores are within noise of each other (see Noise Check below), say so instead of manufacturing a false leader — "too close to call on current evidence; [X] would separate them" is a legitimate recommendation. There is no number for "within noise": it is a judgement you state with its reason (Noise Check below).

## Rules
- Every ICE score must trace back to a Four Risks assessment — no scoring without risk evaluation first. (This is Mycelium's lifecycle rule, `engine/leaf-lifecycle.md` Phase 2 before Phase 3. It is not Ellis's or Gilad's.)
- Each risk dimension must have separate evidence (Product Trio rule).
- **ICE is Impact x Confidence x Ease, each 0-10** (Gilad, *Evidence-Guided*, ch. 3). Not the average. Until 0.319.0 this skill averaged.
- **Confidence comes from the Confidence Meter and from nothing else.** A Confidence above 4.6 needs test results and a Confidence of 10 needs launch data (arithmetic on the meter's caps, Step 2). Until 0.319.0 this rule read "Confidence of 7+ requires test-validated evidence", on a 1-10 rating that was not the meter.
- **Never report a total without its Impact, Confidence and Ease.**
- **No threshold on the total.** The only cutoff is on Confidence before delivery, and the L4 entry lock holds it (`scripts/scale_locks.py`, `engine/diamond-rules.md`).
- **A low rank parks a leaf; it never kills one.** Archiving is for an invalidated riskiest assumption (`engine/leaf-lifecycle.md`).
- **Rescore whenever something is learned** (Step 6), and replace the factors and the total together.
- If all items score similarly, the risk assessments need more depth.
- Review for bias after scoring, before acting.
- **No OST leaf advances to selected without an ICE score.** A solution leaf may be sketched without ICE while still a candidate. The moment it is picked up for delivery (cycle opens, the diamond records `commit_to_build` with this leaf as its front runner), `ice_score` on the solution entry in `opportunities.yml` must be recorded: the three factors and their product as `total`. This is what makes the calibration dimension measurable later — a cycle that ships without a prior ICE prediction is a permanent dark cell in `cycle-history.yml`. See `engine/cycle-learning.md#cycle-class` for how this propagates into `cycle-history.yml.predicted.ice_score`.
  **A total of 0 is a recorded score when its factors are there** (changed 0.319.0). Until 0.318.x this rule said the `ice_score` "must be non-zero", and the checks behind it read a total of 0, or any total under 1, as no score at all. With Gilad's ICE an Impact of 0 is legal and totals 0, and meter values make totals under 1 ordinary. `scripts/check_leaf_lifecycle.py`, validator Check 38 and the cycle-history schema now accept a zero total whose three factors are recorded with at least one of them above zero; `{i: 0, c: 0, e: 0, total: 0}` still means nothing was scored.

- **Inside an L3, scores are hints for comparing its ideas, never a door (v0.301.0, DL-1367).** An L3 opens on its L2's target (/mycelium:ost-builder offers it), and the ideas under that target are its set. ICE helps compare them, as hints (Gilad, *ICE Done Right* p4: the scores are "just a way to compare ideas"); the L3 names its `front_runner` when it commits to build, and that choice is the human's, not the top score's. **ICE ranks the leaves; it never unlocks one.**
  **The history, kept because it was learned twice.** Until v0.242.4 the L3 door here read *"When a leaf is `selected`"* (a state with no writer; no schema declared it), so it never opened; v0.242.4 changed it to the highest-ranked leaf; v0.301.0 moved the door to the L2's target (ruling C: one L3 per target, its ideas compared inside it).

## Canvas Output
Update `.claude/canvas/opportunities.yml` — write `four_risks` and `ice_score` per solution leaf. Write the `ice_score` block with its three factors and their product together (`impact`, `confidence`, `ease`, `total`); a total stored without its factors cannot be checked or read.
When a scored leaf ships, write `shipped_at: YYYY-MM-DD` on the leaf (declared field, v0.203.0); the outcome-check lag and cycle-history read the field, and a ship date that lives only in a `shipped_note` is invisible to both.
Update `.claude/canvas/gist.yml` with idea ICE scores and confidence levels.
**Do not rewrite a score whose decision is closed.** `scripts/check_ice_aggregate.py` (run by `/mycelium:canvas-health`) checks that a new or changed total is the product of its factors, and holds the totals written under the earlier rules in a baseline as history.

## Theory Citations
- Gilad: *Evidence-Guided* (2023), ch. 3 "Ideas" and ch. 4 "Steps" — ICE as Impact x Confidence x Ease, each 0-10; the definitions of the three factors; the Confidence Meter; the Confidence cutoff before delivery. This is the version of ICE the skill uses (since 0.319.0).
- Gilad: *ICE Done Right* (ebook) — what the score is for (p. 4), parked ideas (p. 9), when to rescore (pp. 8, 15), the launch cutoff on Confidence (pp. 5, 14). It also allows averaging (p. 4).
- Gilad: The Confidence Meter, spreadsheet version (CC BY-SA 4.0) — the weights and caps in Step 2.
- Ellis & Brown: *Hacking Growth* (2017), ch. 4 — Sean Ellis invented ICE, for a growth team's experiment backlog, and **averages** the three ratings. Mycelium used his arithmetic from 0.229.0 to 0.318.x; see `docs/errata.md` A1 and A7.
- Torres: Continuous Discovery Habits (OST leaves as unit of evaluation)
- Torres: Product Trio (three perspectives feeding risk assessment)
- Cagan: Inspired (Four Risks as structured evaluation). Reading them before scoring is Mycelium's addition, not part of either author's ICE (Step 1).
- Kahneman: Thinking, Fast and Slow (bias in estimation)
- Kahneman, Sibony & Sunstein: Noise (2021) — unwanted variability in judgment (see Noise Check below)

### Noise Check (Kahneman, Sibony & Sunstein, 2021)

ICE scores are susceptible to **noise** — unwanted variability where different sessions or assessors produce different scores for the same evidence. Unlike bias (systematic skew in one direction), noise is random scatter.

**Detection**: Re-score the same evidence independently (different session or assessor) and compare the three factors, then the total. Each factor is 0-10 and the total is their product, so a difference in one factor is multiplied by the other two. **No number says how far apart two scorings must be before the gap matters. Whether it matters is a judgement you state with its reason.** Read each factor for what it is:

- **Confidence** is summed from the Confidence Meter (Step 2), so two scorings of the same evidence should give the same number. When they differ, compare the two lists of evidence counted, row by row. The difference is a piece counted under a different kind, a piece one scorer missed, or a part-weight one scorer applied and the other did not. Find it and correct the count before proceeding.
- **Impact** and **Ease** are estimates on the project's own scales (Step 2). When they differ, say whether the difference changes what you are about to decide (the order of the leaves, or which assumption is tested first). If it does, ask what each estimate rests on before proceeding.

**"Too close to call" is a judgement, stated with its reason.** Mycelium has no sourced number that separates a real lead from noise, so it does not give one. When you say two leaves are too close to call, say what makes the order unreliable (for example: the two scorings put the leaves in a different order, or the lead rests on a Confidence with no test behind it, and *"the ICE scores are quite unreliable as long as confidence levels are low"*, *Evidence-Guided*, ch. 3) and say what evidence would separate them.

*(Changed 0.320.0. Until then the Detection paragraph above and the audit procedure below read "If scores diverge by >1 point on any dimension". The number was Mycelium's own and carried no citation; the book is cited here for what noise is and for auditing it by scoring the same case independently, not for a number. It was written when each dimension was a 1-10 rating. On the meter most Confidence values are under 1, so two scorings of 0.16 and 0.96 are less than "1 point" apart while, with the same Impact and Ease, one total is six times the other. No sourced number replaces it.)*

**Mitigation**: Use structured assessment criteria (the Four Risks inputs above), apply scores independently before discussion, and anchor to evidence types rather than gut feel.

**Noise audit procedure**: Score the same evidence independently twice (different session or different assessor). Compare the two scorings factor by factor as under Detection. A difference between two scorings of the same evidence is noise: where it matters (Detection), investigate the scoring criteria and the evidence counted before proceeding. For solo developers: re-score after a 24h break to detect temporal noise.
