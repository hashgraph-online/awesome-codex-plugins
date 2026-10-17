# intent-review.md — the completeness lenses (ELICIT's risk-proportional press)

The lenses ELICIT applies while generating what to understand to press into **what the user didn't say**.
Off-the-shelf plan tools only tidy what the user *said*; the hard problems live in the unsaid. These
lenses are how ELICIT mines it — the **risk-proportional press on the high-stakes slots the
decision-surface accounting enumerates** (`elicitation.md`), not an optional flourish: every
load-bearing slot must pass under them before ELICIT may close. What scales with risk is the *depth/force* per item (a trivial goal gets
a light pass; a high-blast goal gets several diverse lenses pressed hard) — **not** whether the sweep
runs. This is the generative completeness work, done *during* dialogue where the user can still answer;
it is **not** a thing to defer to the gate (deferring it is the reward-hack named in `elicitation.md`).

(The **independent** completeness audits are `intent-completeness.md` — auditing the decision surface
before SPEC — and the `3-doc-gate` on the finished artifact; the session→document fidelity check is
REVIEW(A)'s. This file is the generative lenses ELICIT owns.)

**Floor, not ceiling.** The lenses below are a floor to provoke the press, not a fixed checklist; let
what is actually at risk in *this* intent decide where to push.

## Risk-proportional aim — do not blanket-audit

Pressing the whole intent inflates cost for little gain. Aim where the risk lives:

- **Press the assumptions and the non-derivable decisions** — the things the code/material did not
  settle. Code-derived, already-grounded content is low risk — skip it.
- **Confirm the load-bearing technical shape was surfaced.** For greenfield (or any intent the code
  did not pin), the persistence approach, interface/delivery form, and any plan-defining technical
  choice must actually have been surfaced and settled. An un-surfaced shape is a material gap (only the
  user can fill it). (Functional completeness is easy to over-focus on while the whole stack goes
  unstated; this is the guard against that.)
- **Probe the output / interface contract for completeness.** Where the intent defines an output, API,
  schema, or data model, the *shape downstream consumers (and the executor) depend on* is a recurring
  source of late-caught gaps: the entities/fields and their constraints, the exact response/output
  keys, the status/enum value sets (and whether two conceptually distinct fields were collapsed into
  one), uniqueness/identity rules. A half-pinned contract derails downstream work even when the
  behavior reads clear — so check the contract is fully specified, not just the behavior. Whether a
  given intent even *has* such a contract is judged at runtime (a pure-CLI tool's output format, a
  service's response schema, a library's return type — or nothing). Not a fixed field checklist.

## The three lenses (scale to stakes)

A small, low-blast goal gets one quick pass; a complex, high-blast goal gets these diverse lenses,
pressed harder:

- **Implementer lens** — *what can't I build from this?*
- **User-intent lens** — *what did they likely mean that's unstated?*
- **Edge lens** — *what breaks?*

No fixed number of passes — judgment, not a checklist. These lenses are the *qualitative* companion to
`gap-analysis.md`'s mechanical probes: the probes detect silences from the domain's type; these
lenses press the high-stakes assumptions from a skeptic's angle.

## What a lens raises is still a candidate

Anything a lens surfaces is a **candidate**, not yet a question — it passes through `grounds-gate.md`
(site / why-not-covered / consequence) and is asked with a recommended default attached, exactly like
any other ELICIT candidate. A lens that cannot ground its finding drops it.

## Universality guard

No concrete stack, framework, library, or tool name appears here. The lenses and criteria are
stack-agnostic; what is actually at risk is judged at runtime from the intent and the code.
