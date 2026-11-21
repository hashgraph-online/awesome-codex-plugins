---
name: purpose-properties
description: "Derive the binding properties your why/how/what impose on everything below them, so no solution can silently contradict your own product definition. Retrofit entry point for projects that started before v0.120.0; also the re-derive path when why/how/what change and every stance below them goes stale."
metadata:
  instruction_budget: "21"
  framework_dependency: "mycelium"
  framework_dependency_note: "This skill is designed to run within the Mycelium framework (https://github.com/haabe/mycelium). Standalone use will skip the canvas state, theory gates, and harness behavior the skill assumes. Install: /plugin install mycelium@haabe-mycelium."
---

# Purpose Properties Skill

Retrofit and re-derive entry point for `purpose.yml#purpose_properties`. **For new projects this runs
inside `/mycelium:start` Step 3b.** Use this skill when:

- The project existed before **v0.120.0** and has no `purpose_properties` (the retrofit case — every
  project created before that release, since `/mycelium:start` Step 4 exits for already-initialized
  projects and never reaches the extraction).
- `why`, `how` or `what` changed, so `derived_from_hash` no longer matches and **every stance below
  it is superseded** (the drift case — this is the one that matters most and the easiest to skip).
- A property list exists but the user wants to revisit which properties are `binding`.

Full contract: https://github.com/haabe/mycelium/blob/main/docs/purpose-stance.md (it lives in the repository, not in the installed plugin).

## Step 1: Read the current state and say which case this is

Read `purpose.yml`. Then say plainly which of these you are in, because the three have different
consequences and the user should not have to infer it:

- **No `purpose_properties`** → retrofit. Nothing below has ever been checked against the purpose.
- **Hash mismatch** → drift. Report it as *"your purpose changed after these were derived, so every
  `purpose_stance` below them was reasoned under a definition you have since changed."* This is the
  state that quietly invalidates work; name it in those terms.
- **Hash matches** → nothing to do. Report the property count and stop. Do not re-derive for tidiness.

## Step 2: Attempt extraction, and classify what fails

For every element of `why`, `how` and `what`, ask: **can I name a specific solution that would
CONTRADICT this?**

- **Yes** → candidate property. Record `property`, `verbatim` (their words, not yours), `source`, and
  the contradicting solution in `contradicted_by`.
- **No** → **do not force one.** Quality adjectives — *secure, accessible, fast, simple, delightful,
  robust* — yield nothing checkable, because every candidate solution claims to satisfy them.

**Measured 2026-08-23, blind:** *"accessible and secure"* produced **no** checkable property, while
five abstract framework principles produced clean ones. **The axis is not abstract vs concrete — it
is quality adjective vs structural claim.** Do not treat concrete-sounding words as safe.

## Step 2a: Screen for quality adjectives BEFORE trusting your own refusal

**DO NOT RELY ON NOTICING.** Step 2 says a quality adjective yields nothing checkable and asks you to
decline. The evidence that an extractor actually declines is **one blind run, one model family** — the
2026-08-23 test, where the extractor returned NONE for *"accessible and secure"* unprompted. That
result is real and it is thin, and this skill runs under model families that test never touched, in
runtimes where no hook fires to catch the difference. **A model that does not refuse produces a
confident property, marks it binding, and creates a stance field that every solution answers
`preserves` forever — populated, green, and meaningless.** The mechanism's own failure mode, at its
entry point.

So the screen is a rule, not a judgement:

**TRIGGER LIST — if an element contains any of these words, it routes to Step 3 REGARDLESS of whether
you extracted something from it:**

> secure · safe · private · accessible · usable · intuitive · simple · easy · fast · performant ·
> scalable · reliable · robust · flexible · modern · seamless · delightful · high-quality ·
> best-in-class · efficient · powerful · lightweight

**Extracting a property from one of these words is not evidence the word was checkable.** It is the
predicted failure. Route it, let the builder supply the standard, and record what they say.

**AND THE GENERAL TEST, for words the list does not carry** (it cannot be complete, and treating it
as complete is the next version of this bug):

> **Would every plausible competing solution ALSO claim to satisfy this?**
> If yes, it is a quality adjective, whatever it sounds like. Route it.

*"Secure"* fails that test — nobody proposes an insecure login. *"Anonymous"* passes it — a solution
requiring an account plainly does not claim anonymity. **Note that the concrete-sounding word is the
one that fails.** The axis is never how technical the word looks.

**WHAT IS STILL UNTESTED, stated so nobody reads the list as coverage:** whether a builder actually
answers the Step 3 prompt. The 2026-08-23 run exercised extraction only — no builder was asked
anything — so the recovery path has evidence for its necessity and none for its effectiveness.

## Step 2b: Check the ALTITUDE of every candidate before you record it

**A property must sit at the altitude where violation is meaningful.** Ask, of each candidate:

> **What would have to be true for this to be violated — a single move, or a design choice?**

- **A design choice** → it is a property of the product. Record it.
- **A single move** → **you have extracted a rule about BEHAVIOUR, not a property of the product.
  Do not record it.** A property that can be violated by one sentence turns the stance field into a
  footnote requirement, and a check people must satisfy per action is one they mute.

**WORKED EXAMPLE, and it is why this step exists.** From *"Theory-guided decisions: every significant
decision is grounded in established frameworks"*, two independent blind extractions BOTH produced
*"a significant decision must name the framework it rests on"* — per decision. The words invite it.
But the founder's reading is the right one: **not everything needs to be grounded for the overall to
be grounded.** The principle is about how the SYSTEM is built — its gates, skills and structure derive
from theory — not about an audit trail on each move. Pitched per-decision it is micromanagement; the
same project's `(per: <source>)` convention, injected into every session, sits at **4 citations
across 197 decision-log entries**.

**AND CHECK WHETHER IT IS ALREADY MECHANISED BEFORE MINTING A PROPERTY.** That same principle is
already enforced at the right altitude by `check_theory_fidelity.py` on every push. **Point at the
existing check; do not mint a property that duplicates it** — two mechanisms for one claim means one
of them drifts unnoticed.

**`binding` and altitude guard different failures.** `binding: true` limits HOW MANY properties are
checked. Altitude limits how GRANULAR each one is. **Both end the same way if you get them wrong — a
check nobody reads — and only one of them is visible in the field.**

## Step 3: Interview the builder on what failed — with candidates, not an open question

> You said **"secure"**. Which of these would you call a violation?
> (a) passwords stored in plaintext (b) no transport encryption (c) sessions that never expire (d) something else

**Recognition is cheap; generation is not.** Offer three plausible violations drawn from the domain,
and expect (d) to be where the real answer lives.

- **They answer** → you have a property; record the violation in `contradicted_by`.
- **They cannot, or decline** → record `binding: false` and `aspiration_reason` (the schema requires
  `binding` on every property; an aspiration without it fails validation, found by the first E2E
  happy-path run, v0.248.1), and say the consequence out loud:
  *"'secure' stays undefined, so no solution will ever be checked against it."* **A skip is a
  recorded choice, never a blank.**

**This is NOT `/mycelium:user-interview`.** That skill asks about specific past behaviour, which is
right for discovering user needs and wrong here — this elicits a definition from the builder about
their own intent, where the question is hypothetical by design.

## Step 4: The user marks `binding`, and only they can

Present the candidates and ask which ones, if violated, would **break the product** rather than merely
disappoint. Only those get `binding: true`, and only those are ever checked.

**Do not set these yourself.** A why/how/what yields many adjectives; an agent marking them all
binding turns the check into noise, and noise gets muted. Set `confirmed_by: human` only after they
have actually answered.

**IF THEY REJECT THE BOOLEAN, THEY ARE PARTLY RIGHT — DO NOT TALK THEM OUT OF IT.** A builder on
2026-08-31 answered: *"I have problem seeing them as booleans. They have a value (say 1-10), and then
can be weighed against each other."* The resolution is better than either frame, and the day produced
all three categories:

- **Constraints** — violate it and the thing is out, no compensation. `binding: true`.
- **Weighted criteria** — most properties. Set `weight` 1-10 and leave `binding: false`. **No checker
  reads `weight`**; it is for the human's own trade-offs, and saying so plainly is what keeps the field
  honest.
- **Constraints with a named unlock** — the most useful category, and the one nobody asks for
  unprompted. Not eternal, not tradeable, changeable through one specified event.

**Why not simply switch to weights.** A pure weighted score permits compensatory trade-offs, so a high
total can outvote a violated must — that is exactly how someone accepts a role that pays well and
requires the relocation they called non-negotiable. `binding` is guarding something real. Keep it as
the compensation gate and let `weight` carry everything else.

**Asking for the unlock.** For each `binding: true` property, ask: *"is there anything that would
legitimately change this, and what exactly would have to happen?"* Record it as `unlock.state`.

> **THE UNLOCK MUST BE AN EVENT, NOT A MOOD.** Worked example: a "Steinkjer base" constraint unlocks on
> *a family conversation held and logged* — explicitly NOT on income pressure. **An unlock that fires
> "when things get bad enough" is indistinguishable from erosion, and it fires exactly when judgement is
> worst.** If they cannot name an observable event, the property has no unlock. Leave it off rather than
> writing a soft one; a soft unlock is worse than none because it launders a broken constraint as a
> planned one.

Only `binding: true` properties are checked, exactly as before. Weights and unlocks change what the
canvas can RECORD, not what the gate enforces.

## Step 5: Write, then say what changed downstream

Write `purpose_properties` to `purpose.yml` (Read before Write, per the canonical rule). Set
`derived_from_hash` by running:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_purpose_stance.py" --canvas-dir .claude/canvas
```

**On a re-derive, tell them what it invalidated**: every existing `purpose_stance` was reasoned under
the old definition and now needs re-reading. Do not silently leave stale stances looking current.

## What this skill does NOT do

- **It does not judge whether a solution serves the purpose.** Nothing in Mycelium does; that
  judgement is unreliable and a checker that unreliable is a second opinion wearing a gate's clothes.
- **It does not write a stance on any solution.** That belongs to `/mycelium:ost-builder`.
- **It does not clear a `contradicts`.** Only a human can, and the check enforces it.

## Step 6: Offer the BEARING, and take "no" for an answer (v0.230.0)

L0 holds **three** references, and only two of them existed before this release: `why` is the
**ORIGIN** (backward, fixed, singular) and the North Star metric reads **POSITION**. The third is a
**BEARING** — forward, and deliberately not arrivable. Without it, drift has nothing to be drift
*from*: an origin and a position give you a line, not a direction.

After Step 5, read `purpose.yml#just_cause`. If it is absent, say so once and offer to write it:

```yaml
just_cause:
  statement: <what you are heading toward, which you do not expect to arrive at>
  contradicting_decision: <a concrete decision this project could take that would contradict it>
  reviewed: <YYYY-MM-DD>
```

**`contradicting_decision` is the whole check, and the field is worthless without it.** If the user
cannot name a decision that would contradict the bearing, **the bearing is not a bearing** — it is a
pleasantry that every future decision will satisfy. Say that plainly and write nothing rather than
record an unfalsifiable one. This is the same shape as Sinek's test for a why, recorded verbatim from
his 2026-09-08 *A Bit of Optimism* appearance: *"is it a statement of belief, could you argue against
it, is it self-explanatory, is it one point"*.

**An absent bearing is a legitimate state.** The field is optional, a project may run without one,
and offering it every run would make it nag-shaped. Offer on the retrofit and drift cases, not on
every invocation. **Do not compute anything from these three references** — they are not coordinates.
Drift here is *checkable*, by naming a decision, and not computable.

**Then read the statement against Sinek's five criteria for a Just Cause** (*The Infinite Game*,
2019, read at the source). A Just Cause is:

1. **For something**: affirmative and optimistic.
2. **Inclusive**: open to all those who would like to contribute.
3. **Service oriented**: for the primary benefit of others.
4. **Resilient**: able to endure political, technological and cultural change.
5. **Idealistic**: big, bold and ultimately unachievable.

Name to the user any criterion the statement does not meet, and let them revise it or keep it.
`contradicting_decision` above stays the check that decides whether anything is written at all. The
fifth criterion is the one this field already rests on: a statement that could be achieved is not a
Just Cause, by Sinek's own test, so a bearing written as a milestone fails it.

**A Just Cause is not a why, and Sinek says so.** *"A Just Cause is not the same as our WHY. A WHY
comes from the past. It is an origin story... A Just Cause is about the future. It defines where we
are going."* He also allows more than one: *"Unlike a WHY, of which there can be only one, we can
work to advance more than one Just Cause."* The `just_cause` field holds one object. Whether it
should hold several is not settled, and this skill does not settle it; if the user names more than
one, say that the field holds one.

## Theory grounding

Sinek (*Start With Why*) — the why/how/what ordering, and the reason the innermost ring governs the
others. **Used as an ordering, never for the book's neuroscience claims, which do not survive
checking.** The mechanism itself is this project's own: a declaration that can be checked, rather
than an alignment that cannot.
