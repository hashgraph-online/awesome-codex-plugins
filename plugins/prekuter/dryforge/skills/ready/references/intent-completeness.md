# intent-completeness.md — the independent guess-hunt (before SPEC, loops to the user)

ELICIT's job is to realize the user's intent with **no stranger-guess surviving on a load-bearing
decision** (`elicitation.md`). But the author cannot fully police that himself: an agent's own guesses
look to him like *reasonable understanding* ("of course I'd default it this way") — that is the A=A
trap. So before the spec freezes, an **independent perspective** hunts the one
thing the author can't see: **load-bearing decisions that are the agent's guess, not the user's
intent** — and each is **looped back to the user** to decide, *while the user is still here*.

This runs at **ELICIT's exit, before SPEC.** It is the producer's own independent check — distinct
from, and earlier than, the 3-doc-gate: it catches guesses *in the intent* and routes them to the
**user** (extract/present), so they are *decided*, not patched into an artifact after the fact. With
it doing the completeness work, the late 3-doc-gate finds little.

## Why independent, why now

- **Independent (A=A).** The hunter must **not** have authored the dialogue — its value is that it
  isn't invested in the author's defaults. It is dispatched as a fresh subagent and **defaults to
  skeptical**: a load-bearing decision is a *guess* unless the intent shows it grounded in the user.
- **Now (before SPEC), not at the gate.** A guess caught here is **closed by the user** (the dialogue
  is still open). A guess caught at the 3-doc-gate is caught *after* the whole 3-doc is built, when the
  cheap move is to patch the document — which bakes the agent's guess in instead of getting the user's
  intent. Hunt early; route to the person.

## Dispatch

Dispatch a fresh subagent that did **not author** the intent. Give it:
- **The chat session + ELICIT's decision surface** — it **reads the dialogue** (that is how it judges
  whether a slot's disposition is grounded in what the user actually said) plus the enumerated,
  dispositioned surface (each slot `grounded` / `deferred-tunable` / asked-and-answered), the domain
  model, and the user-model. It is independent because it **didn't make the decisions**, *not* because
  it's blind — reading the work is what an independent reviewer does; it is the *authoring*, not the
  *seeing*, that A=A distrusts. A fresh subagent cannot see this session — **serialize the relevant
  dialogue verbatim into the dispatch prompt** (or point it at a recorded transcript); never a
  paraphrase/summary, which silently breaks the evidence base the disposition audit judges against.
  It may also read the **domain/code** (grounds reality).
- **Read-only**, returning a **structured list** (no raw dump).
- **The mandate — audit the decision surface** (`elicitation.md`). Two audits:
  1. **Disposition audit** — for each slot marked `grounded` or `deferred-tunable`, is that defensible
     from the dialogue, or did the agent **rubber-stamp a guess as "grounded"**? Flag any disposition
     you cannot trace to what the user said, their stated goal/values, or an option they chose.
  2. **Residual-enumeration audit** — independently walk the lenses (structural / behavioral /
     technical / contract) over the named entities and colliding pairs and find any **obligation-slot
     the producer never enumerated** (the dangerous A=A miss — e.g. an entity's *cardinality* settled
     without ever being surfaced as a decision).
  Aim especially at: technical decisions presented as settled (was the user given the choice?); a
  mechanism settled with a **preference-value** silently filled (which side wins a contested case, how
  strict a policy is); edge/interaction dispositions no one chose; **structural** decisions
  (cardinality/composition/identity) resolved silently.
- **Do NOT flag *tuning values*.** A configurable number within an already-settled mechanism that is a
  conventional default or is tuned later by feel — one the user has no preference on — is the
  **executor's inference (derivability), not a stranger-guess.** Flagging tuning values is a false
  positive and the source of needless findings (`elicitation.md`, "exit bar item 2"). The hunt is for
  *decisions/preferences the user should own*, not for values the implementer reasonably defaults.
- It does **not** invent the missing intent — it **names the un-grounded decision** as a question for
  the user.

## Process the results — loop to the user, do not patch

- **Empty → proceed to SPEC.** Every load-bearing decision is the user's. Good.
- **Findings → the orchestrator relays each to the user** (in the user's language, no internal tokens)
  and **closes it by the right method** (`elicitation.md`): a domain decision → **extract** (ask what
  they want); a technical decision → **present** (options + recommendation, the user chooses). The
  agent does **not** resolve the finding by writing a better default into a doc — that is the guess the
  hunt exists to stop.
- **Bounded local re-walk after closing — not an open-ended loop.** Closing a finding can open new
  edges, but only in its *neighborhood*: re-walk **only the slots the answer touches** (e.g. "a booking
  holds many services" re-opens that relation's edges/contract), then re-check that delta **once**. If
  the same neighborhood is still non-empty on the second pass, **stop and escalate to the user** — do
  not keep looping. A finding that can't be closed even after asking (the user defers) is recorded
  explicitly and escalated; never silently defaulted.

## Boundary with the 3-doc-gate

| | intent-completeness (here) | 3-doc-gate |
|---|---|---|
| when | ELICIT exit, **before** SPEC | **after** the full 3-doc |
| input | chat session + the **decision surface** (+ code) | the **3-doc** (+ code) |
| hunts | un-defensible dispositions + **un-enumerated** slots | executability + contract fidelity |
| resolves by | **looping to the user** (extract/present) | relaying blockers, fixing the doc |

Completeness of *intent* is won here, with the user. The 3-doc-gate is the final backstop on the
*artifact* — it should find little, because the guesses were already routed to the person who owns the
intent.

## Universality guard

Stack-agnostic and language-agnostic. "Grounded in the user" is judged against whatever this user
actually said and values, in their own terms, discovered at runtime — never a fixed list of decisions
to check.
