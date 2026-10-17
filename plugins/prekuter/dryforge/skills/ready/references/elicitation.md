# elicitation.md — ELICIT (realize the user's intent)

The heart of the front door: a real conversation whose **one job is to realize the user's intent** —
to understand the user deeply enough that the spec written from it is *their* design, not a stranger's.
It replaces a human design partner, so it *actively asks*, but never asks just anything.

## The one rule (everything below serves this)

> **Realize the user's intent. Ask well. Never pass over the unknown.**

The discipline underneath every decision is **understand vs. guess.** For each load-bearing decision
you face, exactly one of two things is true:
- **You understand the user's intent on it** — they said it, or it follows from what they said + the
  domain/code + their established goal/values. Then *realize it* — that is their intent, even though
  your hand wrote it.
- **You do not** — you'd be a stranger picking a "reasonable default." That is a **guess**, and a
  guess on a load-bearing decision is **forbidden**. Close the gap by the right method (below): the
  decision is not yours to default.

There is **no third option** ("pick a sensible default and move on"). "Move on from a load-bearing
unknown" is the failure that detonates later — the agent decides what the user would have decided
differently, and it surfaces as rework, a wrong-direction build, or a thin result. *A reasonable
default by someone who hasn't understood this user is still a guess.*

**Floor, not ceiling.** This is guidance, not a script — never hardcode question lists or stack
choices; specifics are discovered at runtime. Floor-not-ceiling lifts the *ceiling* on how well you
elicit; it never lowers the *floor* of "no guess survives on a load-bearing decision."

## The two methods — by where the knowledge sits (both serve the one goal)

You reach understanding by one of two methods, chosen per decision by **who holds the knowledge.**
Both converge on the same thing — the user's intent.

| The decision is... | knowledge sits with | method | how |
|---|---|---|---|
| **domain / behavior** | the **user** | **EXTRACT** | draw it out ("when X, what should happen?"). The user knows; you must not invent. Mine to the end. |
| **technical** | the **agent** | **PRESENT** | translate the user's generality, *grounded in the domain you've extracted*, into concrete options + trade-offs, recommendation first; the user chooses. |

These are not two phases that take turns — they are two *ways to not-guess*, interleaved as the
dialogue needs. Crucially, **PRESENT depends on EXTRACT**: you cannot present the right technical
options until you understand the domain they must serve. So domain understanding leads, and technical
decisions are presented *against* it.

**Spend questions asymmetrically — but the asymmetry is about *method*, not *permission to skip*.**
Functional/domain intent: extract deeply (only the user holds it). Load-bearing technical: present
(default + trade-off, the user decides in one beat — *never* silently defaulted; a silent technical
default traps the user who didn't know to object). Genuinely trivial (changing it costs the user
nothing and has no downstream weight): decide it — *that is not a guess*, it's understood-as-not-caring.
What is "load-bearing" is a runtime judgment (would changing it force rewriting downstream, or would
the user plausibly have a preference?), never a fixed list.

## Build a model of the user (this is how you *understand* rather than guess)

Understanding is not a feeling — it is a **model of the user you build and maintain as you talk**:
- their **goal** (what they are really trying to achieve — often not the literal feature list),
- their **values / priorities** (what they keep returning to — e.g. a word repeated three times is a
  core value, not filler),
- their **constraints** (scale, "just a personal project," a deadline, a platform),
- the **domain facts** they've given.

Every load-bearing decision is tested against this model: **does the model *ground* this decision?**
- Grounded → realize it (understood — derived from the user, even if they didn't say it literally).
  *This is how you avoid asking the derivable (don't re-ask what the model already settles).*
- Model is **silent** here → this is exactly the gap. You don't get to fill a model-silence with a
  default — you close it (extract or present). Model-silence on a load-bearing point **is** the guess.

This makes "understand vs. guess" *operational and checkable*: a decision you can trace to the model
is the user's; a decision the model can't ground is a stranger's. The richer your model, the more you
can realize without asking — and the fewer guesses hide as "reasonable defaults."

## Scope by cycle — first establishes the foundation, delta works within it; **both equally rigorous**

The cycle changes *what you must understand*, never *how rigorously you avoid guessing.* Delta is
**not** "lighter" — the intent for this task must be just as fully realized as in a first cycle.

- **First cycle (no harness): a forced foundation design.** You must establish the project's
  foundation — its domain model and its technical decisions — from scratch, because nothing holds it
  yet. Force-load `project-scoping.md` (CALIBRATE: character → depth), then run the **domain extraction**
  (`project-design-domain.md`) and the **technical presentation** (`project-design-technical.md`).
  **Their floors are non-negotiable, not loop-optional:** the domain **breadth guard** (you may not
  close without asking "are there other major entities/features/rules?"), the domain **depth floor**
  (every concept has its four facts; every rule is testable), and the technical **no-silent-decision**
  rule (every load-bearing technical decision settled by the user, presented as options). These are
  the structures that *force* understanding over guessing while the foundation is being laid — do not
  dilute them into a light pass. Scope = project foundation + this task.
- **Delta (harness exists): task intent within the foundation — with the same rigor.** Do **not**
  re-run foundation design (the harness holds the domain model, conventions, stack — read the floor
  from it, don't re-ask what it answers). But the task's load-bearing intent must be realized with the
  **full** "no guess survives" discipline: extract the task's domain intent, present its technical
  decisions, run the same generation and the same exit check. Scope = this task only; rigor = full.

## Account the decision surface — enumerate the obligations, don't wait to be told

The user names a fraction of what's load-bearing; you must surface the rest (the decisive difference
from tools that only tidy what was said). But **naming is where this fails silently** — you don't
sweep what you never named (a real failure: an agent settled "one booking = one service" without ever
surfacing booking *cardinality* as a decision). An implicit "did I cover enough?" feeling is the
weakest move (self-judgment). So **make the surface explicit: enumerate the
load-bearing decisions this design is *obligated to answer*, then account for each.**

**1. Name the entities first (a manifest).** List every entity, actor, state-holder, and external
system the goal touches — you cannot enumerate a decision for an entity you never named, so this
bounds the surface. (The breadth guard, materialized: before closing, also ask "is there one we
haven't named?")

**2. Walk four lenses over each entity and each colliding pair to surface obligation-slots** — a slot
is *a question the design must answer or it isn't a design*:
- **STRUCTURAL** — cardinality, composition, identity, relationships (*one X = one or many Y?*). The
  lens whose absence let the cardinality guess through; never skip it.
- **BEHAVIORAL** — lifecycle (created→changes→ends), concurrency (actors racing on shared state →
  atomicity / tie-break / ordering), policy, edge dispositions. **Name the kind first** — the kind you
  don't name is the sweep you don't run. The *combination* of two concepts also creates unsaid edges
  ("can be cancelled" + "carries a payment" → "when cancelled, what happens to the payment?"): walk
  the colliding pairs.
- **TECHNICAL** — persistence, interface/delivery form, consistency model.
- **CONTRACT** — status/enum value *sets*, uniqueness/identity rules, output keys, two-conceptually-
  distinct-fields-collapsed-into-one.

These lenses are **accelerators for spotting, not an exhaustive catalog**: if a load-bearing slot fits
none, your lenses are incomplete for *this* domain — name the new one, don't force-fit. (The floor is
"no slot left a silent guess," which is lens-independent; the lenses only lift the ceiling.)

**3. Enumerate ≠ ask — the over-asking firewall.** Enumerating is cheap, internal, and exhaustive;
*asking* is expensive, user-facing, and minimal. Resolve each slot in this **fixed order** before it
may become a question:
1. **The user-model grounds it** (said / derived from the model / a chosen option)? → realize it,
   **don't ask** (the derivable — see "Build a model of the user").
2. **A tuning value inside an already-settled mechanism** (conventional default / tuned-later, no user
   preference)? → record a sensible default **marked tunable**, **don't ask**.
3. **Survives both = `assumed`** (load-bearing, model-silent — you'd pick it as a stranger). This is
   the guess. → **ask** it (domain = extract, technical = present).

So the surface is enumerated *exhaustively* (completeness) while questions stay *minimal*:
only `assumed` slots become questions. **An `assumed` slot may not survive into the spec** — that is
the exit bar, now *observable* (below) rather than a feeling.

The three probes in `gap-analysis.md` (domain-silence, completeness-sweep, cardinality-coupling) are
concrete slot-finders that populate the lenses; the risk-proportional lenses in `intent-review.md`
press the high-stakes slots harder. The accounting is **ephemeral working memory** — it drives the
exit scan and feeds the independent backstop, then evaporates; it is **never** written into the spec
as provenance tags (`output-format.md`).

## Ask well — so the user can actually answer

A generated candidate is not yet a question. Throw only what survives:

1. **grounds-gate** (`grounds-gate.md`) — a confident question can state its site, why it isn't already
   covered, and the consequence. This filters noise so the dialogue isn't "have you considered
   concurrency?" spray. (It does **not** let you drop a *load-bearing* candidate by under-arguing —
   `grounds-gate.md`.)
2. **Lead with a recommendation / default.** Never throw a question empty-handed. For domain, lead with
   a concrete conception the user adjusts; for technical, lead with the recommended option + trade-off.
   A concrete proposal is faster to answer than a blank slate. (This is *how you present*, not a
   license to default — the user still decides.)
3. **Right-sized rhythm.** Highest-leverage first; batch a few related questions when it serves the
   user (platform limit: at most 4 questions / 4 options per structured prompt). Don't pad with
   low-value questions to look thorough — but "don't pad" bans *trivia*, it **never** excuses skipping a
   load-bearing one. When unsure if something is load-bearing, surface it: one question costs a beat; an
   un-surfaced load-bearing decision costs a wrong-direction build.

**Delivery.** When options are enumerable, prefer the platform's structured-input tool (2–4 options,
recommended first labeled `(Recommended)`, "Other" allowed); pure open questions stay plain text.
Give each structured question a **very short header/label (a word or two)** and keep option labels
short — an over-long header/label, or more options than the cap allows, makes the structured tool
**reject the call**. If the structured-input tool ever rejects or fails, **immediately re-ask the same
question as plain text** — never stall or dead-end on a tool error.

**For a DOMAIN (extract) question delivered as choices, an explicit open option is MANDATORY** — a
"none of these — here's mine" / "I have a different idea" choice *visible among the options*, not just
the platform's generic "Other". **The open option counts toward the 4-option cap** — so a domain choice
question carries **at most 3 substantive options + the open one** (4 total); if more substantive options
than that are in play, drop to **plain text** rather than overflow the cap (overflowing rejects the
call). Domain knowledge is the **user's**; your options are a *scaffold / recommendation*, never the
boundary of what they may answer — boxing a domain question into your 3 options is the opposite of
extracting (you'd cap the user's own model with yours). A genuinely open domain question (where you
can't even enumerate sensible options) is better asked as **plain text**. (Technical *present*
questions, where the option space is legitimately yours, don't need the mandatory open option — there
the recommendation is the point.)

## Mandatory: the load-bearing technical shape is surfaced (first cycle / unfixed stack)

A spec needs a target technical shape, and greenfield has no code to derive it from. So before leaving
you MUST have **presented** the load-bearing technical shape — persistence, interface/delivery form,
and (when the domain has shared state) **the concurrency/consistency model**. **The stack choice alone
does not satisfy this** — picking a stack does not settle "how do simultaneous actions resolve?".
Present = options + trade-offs + a beat to decide; never silent. If the code already fixed the shape,
**confirm** rather than re-ask.

## Exit — you may write the spec only when no guess survives on a load-bearing decision

Stop and proceed to SPEC **only when all hold** (not merely when the user says "that's enough"):

1. **The decision surface is accounted** — entities named (manifest), the four lenses walked over each
   entity and each colliding pair, and **every load-bearing slot is `grounded`, `deferred-tunable`, or
   was asked-and-answered. No slot is left `assumed` (a silent guess).** This is observable — a scan
   over the enumerated surface — not a feeling.
2. **Every load-bearing decision is grounded in the user** — traceable to what they said, to the model
   you built (derived + the user wouldn't object), or to a presented option they chose. **No
   load-bearing decision is a default you couldn't ground.** The load-bearing unit is the
   **decision / mechanism / policy the user has intent on**, *plus* any **value the user would
   genuinely have a preference on** (which side wins a contested case; how strict or lenient a policy
   is; a direction). Surfacing a yes/no for a mechanism does not settle these preference-values — they
   are grounded too.
   - It does **NOT** include **tuning values** — a configurable number *within an already-settled
     mechanism* that is a *conventional default* or is *tuned later by feel*, on which the user has no
     preference. That is the **executor's inference** (derivability — the produce/execute boundary):
     record a sensible default *marked tunable* and move on. **Do not force-surface tuning values, and
     do not treat a defaulted one as an un-grounded guess** — forcing each into the dialogue is
     over-asking and breeds false "ungrounded" findings.
   - **The test per value:** *does the user genuinely have a preference on it, or is it a conventional
     default / something they'd tune later?* Preference → ground; default/tunable → the executor infers.
     (What is a "mechanism" vs a "tuning value" is judged per project at runtime — never a fixed list.)
3. **Load-bearing technical shape presented** (first cycle / unfixed stack), and the first-cycle
   foundation floors met (breadth guard, depth floor, no open technical decision).
4. **No material gap remains** — only trivia the user need not decide.

A clean record of this is simply the spec itself: every load-bearing decision appears as a settled
rule, and the **non-derivable ones carry their reason in the thinking-base** (`output-format.md`) — in
the user's own terms, as prose, *not* machine tags. If a decision is load-bearing and you cannot write
its rule from understanding (only from a guess), the exit bar is **not** met — close it.

**A thin input raises the bar — it does not lower it.** Few signals, big gaps → ask *more*, mine
*harder*. Producing a thin result from a thin input is the exact failure this front door exists to
prevent. A self-assessed "low-blast" call scopes *dialogue length*, never the generation's coverage —
every entity the goal touches is named and swept regardless.

## The gate is insurance, not your safety net

There is a downstream independent check, but **elicit as if it does not exist.** A load-bearing guess
that reaches it is an **ELICIT failure** — you closed while a decision was still a stranger's. Told a
check exists, an LLM drifts to "do the minimum it'll pass" — that is **reward-hacking**, laziness in
the costume of "the backstop will handle it." Your objective is *this dialogue realizing the user's
intent*, never "a doc that passes." Independent checking exists because you (A=A) cannot fully see your
own guesses — so one **independent** check audits your decision surface before the spec freezes
(confirming each `grounded`/`deferred` disposition is real, and hunting any obligation-slot you never
enumerated) and routes its findings back to the user (`intent-completeness.md`). It is a backstop on a
*small* residual, never a substitute for the work.

**Don't churn clean input.** A part already well-grounded has nothing to convert — there the value is
*verify + promote* (confirm an assumption against the code, promote it to a fact, escalate on
conflict). Don't hand a resolvable uncertainty downstream as a hedge.

## Terminology

- **spec = the contract** (binding WHAT; ground truth; authority). **plan = a provisional blueprint**
  realizing it. A task's content is a **behavioral contract** (goal/invariant/what-to-verify), not
  premature code; don't call the plan "the contract."

## Universality guard

No concrete stack, framework, library, or tool name appears in this file or the skill. All guidance is
stack-agnostic and language-agnostic; the actual stack and the user's language are discovered at
runtime from the material and the code — never assumed.
