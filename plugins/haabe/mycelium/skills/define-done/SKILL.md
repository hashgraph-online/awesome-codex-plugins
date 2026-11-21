---
name: define-done
description: "Pin a measurable, outcome-based Definition of Done for a diamond — a behaviour-change that creates value, not a build-list. Problem-first Socratic sequence; writes definition_of_done to the diamond at birth or retrofits it when missing."
metadata:
  instruction_budget: "48"
  framework_dependency: "mycelium"
  framework_dependency_note: "This skill is designed to run within the Mycelium framework (https://github.com/haabe/mycelium). Standalone use will skip the canvas state, theory gates, and harness behavior the skill assumes. Install: /plugin install mycelium@haabe-mycelium."
---

# Define Done

Pin an explicit, outcome-based **Definition of Done** for a diamond. "Done" is *a change in human behaviour that creates value* (Seiden), not "the feature shipped" — you're done when it ships **and** has the intended impact (Amplitude). The diamond's implicit done defaults to the harshest, least-controllable bar ("a user shipped a product"), which is both wrong for validating *purpose* and a demotivation engine. This skill makes the bar explicit, measurable, and pre-committed.

This is distinct from `/mycelium:definition-of-done` (the per-feature agile *quality checklist* run at `close`). This skill sets the **outcome bar a whole diamond is judged against**; that one verifies a feature meets quality criteria. Both can apply.

## When to use

- **At diamond birth** — `/mycelium:interview` (L0) and child-diamond spawn (`/mycelium:diamond-progress`) call this before a diamond is "live."
- **Retrofit** — when `/mycelium:canvas-health`, `/mycelium:diamond-assess`, or the SessionStart nudge flags a diamond with no `definition_of_done`.
- Never silent-fill. The *question* is what produces a real bar ("fits, not ships"); a back-filled field is theatre.

## Preflight: Read target file before any Write/Edit

**Hard rule.** The `definition_of_done` field lives on the diamond in `.claude/diamonds/active.yml`. Before `Write`/`Edit` on it, use the **Read tool** on that file this session (`cat`/`head`/`grep` via Bash do NOT satisfy Claude Code's check). `Edit` with `limit:1` suffices for a partial update; full Read before a `Write`. See `${CLAUDE_PLUGIN_ROOT}/engine/agent-operating-contract.md` *Canvas writes — Read before Write*.

## The sequence (Socratic, problem-first)

Ask these in order. The teaching is in the **sequencing** (problem → signal → maybe-number → kill) and the good/bad contrast — not a help doc. Reject build-lists at step 1; that is the whole point.

**1. "When this is done, what's different — and for WHOM?"** → `outcome` + whose behaviour.
   Lead with the problem and the person, never the deliverable (Cagan: "most measurement problems are clarity problems").
   - ✗ *"the onboarding flow ships."* (a build-list — reject it)
   - ✓ *"non-fluent users get through the brief without hitting the vocabulary wall."*

   **At the learning scales (L0 to L3) what changes is a decision, not yet a behaviour (v0.317.2).** Those diamonds exist to find something out (see the build-mode gate below), so what is different when one is done is what its owner can now decide: what gets built, resumed, rewritten or dropped. Write the outcome as what they will know plus the decision the answer unlocks, and make the "for whom" whoever takes that decision. A behaviour change in the users comes later, from what gets built once the answer is in.
   - ✗ *"builders who shipped and heard nothing are shown to be stuck the way opp-080 says."* (a description of the need: nothing in it changes, and the problem appears only as an id)
   - ✓ *"you know, from builders' own stories, whether 'shipped something, nobody came, and cannot tell whether people passed or never arrived' is real and repeated. That decides what gets built next: the parked ideas resume against it, or the problem is rewritten or dropped before anything is built for it."*

   **Name the problem in words, never by an id alone.** The owner reads the bar weeks later without the canvas open, and an id carries nothing they can check against. Dogfood 2026-10-08: the owner could not interpret an L2 outcome that cited only its opportunity's id ("I cannot interpret the 'what changes', because I don't know what opp-080 says"), and once it was rewritten in words: "this kind of clarity must be a given in the way that these definitions are developed."

   **Then ask: "Write the opposite of this outcome. Would anyone choose it?"** An outcome whose opposite is absurd on its face makes no choice: "home cooks get better meals with less effort" has the opposite "worse meals with more effort", which nobody would pick, so the bar rules out no work and every later diamond can be argued to serve it. If the opposite is absurd, narrow one part at a time (who, what changes, how) until the opposite is something a reasonable builder might pick: "home cooks who cook most days and run out of ideas" has real alternatives (people who never cook, confident cooks). Keep both wordings, the first and the narrowed one, as an entry in the bar's `log[]`. This is advisory, never a block: the person judges whether the opposite is absurd, and a directional outcome that already rules something out passes as written. *Source: Roger Martin's test for a real choice ("is the opposite stupid on its face?"), as presented on the Product Growth podcast (2026-10-14). Devils-advocate's "What if the OPPOSITE is true?" asks whether an assumption is false, which is a different question.*

**2. "What's the ONE thing you'd SEE them DO that proves it?"** → `signal` (One Metric That Matters — one, not many).
   - ✗ *"it feels better."*
   - ✓ *"they came back for a second session."*

**3. *(optional)* "Is there a point where it's ENOUGH?"** → `threshold`, only if one genuinely fits.
   A number is **optional, not mandatory** — directional outcomes are legitimate. When you do set one, pair it with a qualitative guard ("3 warm bodies who bounce ≠ done") so it can't be gamed (Goodhart).

**4. Pre-mortem for the invalidation criterion** (schema key `kill_criterion`; the name is the worst reading of what it is — a pre-committed state and date at which the goal is shown WRONG, which is a completion path, not a termination; see `diamond-rules.md` on `close`). Ask in the past tense: *"It's [review date]. This diamond failed. What happened?"* (premortem finds ~30% more real failure reasons than "might it fail?" — Klein). From the answer derive a concrete **state + date** that means *kill, not finish*:
   - `state` — an objective benchmark that means this goal is **wrong**.
   - `date` — the review date by which the state must hold. Pre-commit BOTH, before the data (anti-HARKing).
   Invalidation-with-evidence at that date is a legitimate "done" — routed through `/mycelium:diamond-progress kill` + `dogfood-mode`, not silently declared.
   - `on_expiry` — **what happens when the date passes and NEITHER the outcome nor the kill has fired (v0.227.0).** Most results land between the lines, and a bar that is silent there stays open for good. The default is **stop**, or re-pitch as a NEW bar with a new written date. "Otherwise the bet continues" is not an answer: it is how a bar stays in limbo with every field filled. A bar written as an ordered `branches` list may say this in a last line whose `when` is "anything else".

**5. Hand the bar to someone who did not write it, before you accept it (v0.227.0).** Invent a handful of result sets, including awkward ones between the lines, and ask a reader who has NOT seen the conversation to say what the bar tells you to do in each. For a solo builder the reader is a blind subagent given only the bar's text. If they have to ask what a word means, or two cases resolve to nothing, the bar is not done: fix the wording and ask a FRESH reader. Record the result on the bar as `reader_test: {date, reader, cases, resolved, note}`. This step is not optional polish. Dogfood 2026-09-17: the author ran every mechanical check on four successive drafts of one bar and all four passed; a blind reader found a real defect in each (an extension rule that read two ways, a kill tied to an exact count that one extra offer missed, "the last taker" with nobody to refer to). The author checks the bar he meant; the reader checks the bar he wrote. And because a self-written stop rule is the weakest kind there is (Boulding et al. 1997: pre-committing to a rule you wrote yourself barely reduces escalation; a rule someone else applies does), the same reader, or another, applies the bar again AT its date. `check_dod_shape.py` reports a bar with no `on_expiry` and no `reader_test`, as advisories.

## Per-scale "done" + lead/lag defaults

Default `kind` by altitude: lower/activity scales take **leading** measures (predictive, team-influenceable); higher value-validation scales take **lagging** (already realized). Direct most attention to lead measures (4DX).

| Scale | "Done" means | `kind` default |
|---|---|---|
| L0 Purpose | people **keep choosing it** ("fits, not ships") | lagging |
| L1 Strategy | a where-to-play **bet validated** | lagging |
| L2 Opportunity | a real user need **confirmed worth solving** | mixed |
| L3 Solution | the solution **actually solves it** for users (not just built) | leading |
| L4 Delivery | shipped **AND** has the intended impact | leading |
| L5 Market | **adoption / business outcome** at scale | lagging |

## Build-mode gate — refuse build-to-earn during build-to-learn

The per-scale table isn't only a `kind` default — it encodes the **build mode** (Patton/Cagan). This skill enforces it at diamond birth (agent-adjudicated), with a `/canvas-health` lint backstop that fires unconditionally (step 8c there). This is the mechanism behind philosophy.md's *"the framework refuses to let the agent build-to-earn during a build-to-learn phase — that refusal is the gate."*

- **Build-to-LEARN** (a diamond whose terminal purpose is to *learn* — scales L0 Purpose → L3 Solution): its DoD `outcome` must be a **learning / validation** result ("the bet is validated", "the need is confirmed worth solving", "the solution actually solves it for users").
- **Build-to-EARN** (terminal purpose is to *ship value* — L4 Delivery, L5 Market): its DoD `outcome` is a **shipped-value / adoption** result ("shipped **AND** the intended impact landed").

**The discriminator is NOT the word "ship" — it is what the done-bar IS.** Discovery legitimately *ships to learn*: a fake-door test, wizard-of-oz, a disposable prototype shipped to a few opted-in users. Those are build-to-LEARN — the ship is the *method*, the *learning it yields* is the done-bar ("40% of the 5 opted-in users returned = demand validated"). Do NOT reject those.

**The gate — reject a build-to-LEARN diamond's DoD only when it is genuinely earn-shaped**, i.e. either:
- the **ship itself is the done-bar** (no learning behind it — "the flow is deployed" as the terminal criterion), OR
- **scope is all-users / permanent / production-hardened** rather than select opt-in (reuse G-M2's opted-in-vs-all-users line).

Then say: *"That's build-to-earn on a build-to-learn diamond — you haven't earned delivery yet (Patton/Cagan). What will this ship let you LEARN? Make the learning the done-bar, keep the ship disposable / opt-in. Production rollout is the L4 outcome, earned after discovery validates."* This is **distinct from the step-1 build-list rejection**: step 1 catches *"the flow ships"* as a non-outcome; this catches a well-formed but **premature earn-bar**. Conversely, a build-to-EARN (L4) diamond whose `outcome` is pure learning with **no value/impact** → prompt to reframe to earn ("shipped **AND** moved [signal]").

**Boundary note (mode shifts within a diamond; the DoD bar is per-diamond).** The DoD keys to the diamond's *terminal purpose* (its scale), but the mode shifts *within a diamond's loop* (discovery until `commit_to_build`, delivery after): even an L4 Delivery diamond has early experiments (a spike, "how should we build this?") that are build-to-learn — don't force its early spike into an earn-bar. And a build-to-EARN L4 child under a build-to-LEARN parent ships (earn) yet rolls up to the parent's *learning* (`rolls_up_to`). philosophy.md frames the line by the old **phases** (Discover/Develop divergent = learn; Define/Deliver convergent = earn; that narrative is rewritten in stage 6); this skill keys the *DoD outcome* to the diamond's terminal **altitude** — the same distinction, applied to the artifact each governs.

**Scenarios** — *happy:* L4 "shipped X and retention rose" ✓; L1 "the where-to-play bet is validated" ✓; L2 "fake-door: 40% of opted-in users clicked through = demand validated" ✓ (ships, but to learn). *sad (redirect):* L2 "ship the onboarding flow" (ship = the bar, no learning) → reframe to the need it must confirm first. *bad (blocked):* L0/L1 "deploy production auth to all users" → earn-during-learn, the "earn the right to start" gate firing.

**Ladder rule (contribution-not-summation):** a child diamond is done only when its outcome **rolls up** to move the parent outcome / validate the parent assumption — not just because the child shipped. A child that doesn't roll up is discarded, not summed. Set `rolls_up_to` on every child.

## Write the field

Write `definition_of_done` onto the target diamond in `.claude/diamonds/active.yml`:

```yaml
definition_of_done:
  outcome:   "<what changes, for WHOM — a behaviour, not a feature>"   # required; problem-first
  signal:    "<the ONE observable thing you'd see them DO>"            # required; OMTM
  kind:      leading | lagging                                        # defaulted by scale above
  threshold: "<a target IF one genuinely fits>"                       # OPTIONAL (numbers not mandatory)
  measure:                                                            # OPTIONAL — makes `signal` checkable post-ship; closes the outcome→discovery loop (/metrics-pull reads this)
    source:      "<metric adapter key (github, plausible, …) OR 'manual' for interview/observation outcomes>"
    field:       "<snapshot field path for automated sources; omit for source: manual>"
    target:      "<value or direction that means the outcome landed — reuse `threshold` if already set>"
    check_after: "<lag before checking, as Nd or Nw after ship (e.g. 14d, 8w) — matched to `kind`. Per-DoD; consumed by /metrics-pull's lag gate + the overdue nudge. Default 14d if unset>"
    guardrail:   "<counter-metric that must NOT worsen while `signal` improves — Goodhart guard (advisory: downgrades a 'met' to 'met-with-regression')>"
    last_checked: null                                                # stamped by /metrics-pull when the outcome-check runs
  rolls_up_to: "<parent diamond id + which parent outcome this serves>"  # child diamonds only
  kill_criterion:                                                       # the invalidation criterion; schema key kept for compatibility
    state: "<concrete benchmark that means this goal is WRONG>"
    date:  "<YYYY-MM-DD review date by which state must hold>"
    premortem: "<the failure it was generated from>"
    on_expiry: "<what happens when the date passes and neither outcome nor kill fired — default STOP, or re-pitch as a new bar with a new date; never 'continues'>"
  reader_test: { date: "<YYYY-MM-DD>", reader: "<blind subagent | a named person>", cases: 0, resolved: 0, note: "<what they had to ask about>" }   # step 5; re-run at the bar's date
  provenance: { source_class: internal_stakeholder, validated: false, captured_at: "<YYYY-MM-DD>" }
  log: []                                                               # dated updates go here: [{date: "<YYYY-MM-DD>", text: "<what was scored, re-specified or ruled>"}]
```

**The bar and its log are two things (v0.225.0).** `outcome`, `signal`, `threshold` and `kill_criterion` are the BAR: what the owner steers by, short enough to state from memory. Everything that happens to the bar afterwards (a sweep scored against the kill criterion, a re-specification, a ruling, a tally) is an entry appended to `log[]` as `{date, text}`. **Never add a dated key (`state_2026_09_01:`, `sweep_3_result:`) beside or inside the bar, and never grow `kill_criterion.state` into a history of itself.** When the bar itself changes, rewrite the bar field and put the OLD wording and the reason in a log entry. Dogfood 2026-09-16: a Definition of Done reached 76,904 characters, 59,229 of them dated notes under `kill_criterion`, and its owner could not state it; after the notes moved to `log[]` the bar was still 21,559 characters, so moving the log out is necessary and does not by itself make the bar short. When re-running this skill on an existing diamond, run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_dod_shape.py" --diamond-id <id>` first and show the owner the bar size before asking whether the bar still says what they mean.

`outcome` and `signal` are required; everything else is optional or scale-defaulted. At L0/L1 birth from the brief, a one-line `outcome` + `signal` stub is enough — depth comes from re-running this skill.

### `measure` — closing the outcome→discovery loop (optional)

Setting a DoD target and never checking whether it landed leaves the back half of the loop open (Kim's Second Way: outcomes must flow back). The optional `measure` block makes `signal` checkable after ship, so `/metrics-pull` can compare target-vs-actual and route the result back to discovery (met → confidence up / scale; missed → reopen the opportunity). Design notes, all evidence-grounded:

- **`source: manual` is first-class, not a fallback.** Many real outcomes — especially early, and any that depend on real users experiencing the thing — are interview/observation-based, not dashboard numbers. `measure` must NOT push you to pick the number you can automate over the outcome you care about (the metric-availability trap). Manual outcomes get *prompted*, not faked.
- **`check_after` is per-DoD, never a global window.** Outcome lag varies by what you measure (engagement lands in days; retention in weeks or months). Match it to `kind` — leading measures check sooner, lagging later — long enough to capture real signal, short enough to still act on it. Written as `Nd`/`Nw`; `/metrics-pull` skips the check (no false "missed") and the nudge stays quiet until it elapses.
- **`guardrail` is the Goodhart guard (advisory, with teeth).** When `signal` becomes a target it degrades; pair it with a counter-metric that must not worsen. It doesn't block, but `/metrics-pull` downgrades a "met" to "met-with-regression" when the guardrail worsened as the signal improved. Five metrics are harder to game than one.
- Omit `measure` entirely for a directional outcome with no meaningful check — that stays valid.

## Purpose-stance check on the bar you just wrote (WARN — never blocks)

**Run it after writing the field:**

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_purpose_stance.py"
```

**What it is for, and it is not the solution check wearing a different hat.** A definition of done is
the one artifact that says what this diamond is FOR. If it drifts from the product's own why/how/what,
every downstream gate can pass while the diamond delivers something the product no longer claims to be.
That drift is invisible by construction: nothing else in the framework reads a `definition_of_done`
against the purpose.

**The failure this closes, measured on the dogfood project 2026-08-23.** An L1 outcome was re-specified
on 2026-08-15; the `why` and `what` were rewritten on 2026-08-23 and the binding properties derived from
them the same day. **The bar was therefore written eight days before the definition it had to satisfy
existed, and nothing re-read it.** The founder found it by asking out loud whether it still fit — not
from any check. Worse, the script that would have answered him did not open `active.yml` at all until
plugin 0.123.0.

**If the diamond has no `purpose_stance`, ask for one now, while the bar is fresh.** This is the cheapest
moment: the builder has just articulated what done means, so the question "does this contradict what you
said the product is?" is a continuation of the conversation, not an audit weeks later.

**NEVER auto-fill it.** An agent-written `preserves` with no human read is the filler trap with extra
steps, and a `contradicts` verdict may only be overridden by a human. If the builder does not want to
answer now, leave the field absent — the WARN is the true state and it will keep reporting. **Absent is
honest; invented is not.**

**Exit is always 0 here.** This is firing point 7 in the wiring spec — WARN, never fail. A definition of
done must never be blocked by a stance check, or the skill that exists to make "done" concrete becomes
one more thing to satisfy first.

## Failure-mode guards (baked in)

- **No checklist theatre** — step 1 rejects "what you built"; the field is an outcome.
- **No Goodhart** — number optional; when set, pair with a qualitative guard.
- **Invalidation-path honesty** — done-by-invalidation requires the pre-committed state+date to have actually **fired with evidence** at the scheduled gate, logged via `dogfood-mode` + decision-log. It is not a way to declare failed work done.
- **Problem-first sequencing** prevents the metric-availability trap (picking the number you can measure over the outcome you care about).

## Provisional wording

The exact prompt phrasing above is **provisional** — only the why → who → how-should-behaviour-change → what scaffold (Impact Mapping) survived research verification; the specific wording did not. Validate it with `/mycelium:prompt-optimizer` A/B rather than treating the phrasing as settled. Design + evidence grades: `docs/definition-of-done.md`.

## Theory Citations
- Seiden (*Outcomes over Output*): done = a behaviour-change that creates value, not a feature shipped.
- Cagan (*Inspired*): problem-and-whom first; measurement problems are clarity problems.
- Roger Martin, as presented on the Product Growth podcast (2026-10-14): a choice whose opposite is stupid on its face is no choice; step 1's opposite question.
- Amplitude (*North Star Playbook*): shipped AND has impact.
- Adzic (*Impact Mapping*) / Microsoft Research: contribution-not-summation laddering; why→who→how→what.
- 4DX (McChesney) / Lean Analytics (Croll & Yoskovitz): lead-low / lag-high; One Metric That Matters.
- Duke (*Thinking in Bets*) / Klein (premortem) / pre-registration: state+date kill-criteria, pre-committed, generated by pre-mortem.
- SAFe (Epic Hypothesis Statement): done = hypothesis confirmed OR invalidated-and-cancelled.
