# review-fidelity.md — REVIEW(A): session→document fidelity

Run **immediately after SPEC, before PLAN, inline.** It checks exactly one thing: *did what was
decided in the session land in the document without evaporation or distortion?* (fidelity). First
cycle: the written Foundation is checked too. **Completeness is deliberately not checked here** — the
rationale is below; it is not an arbitrary narrowing.

Outside ELICIT's dialogue and the intent-completeness user-loopback, this is the only mid-run user
question besides the final gate, and only on the one branch that needs
it (a user-only intent-gap). Everything else REVIEW(A) finds, it fixes itself.

## Check fidelity only — a narrow diff, not a full re-audit

Compare the written `spec.md` (+ first cycle: the written Foundation in `handoff.md`) against what
the session actually settled. This is a **narrow diff**, not a whole-spec re-audit: if ELICIT's
real-time verification kept the session clean, this pass is light. You are looking for things that
were decided in dialogue but came through the writing **dropped, weakened, or twisted** — a settled
edge rule that didn't make it into the behavior section, an invariant softened into a "should," a
confirmed technical decision missing from the Foundation.

## Why fidelity only — the A=A / authorship argument (not an arbitrary cut)

A spec has two kinds of defect, and **who authored the intent** (the A=A line) decides who can catch which:

| | authored the intent? | strong at | weak at |
|---|---|---|---|
| REVIEW(A) | yes — and holds the session | **fidelity** (does the doc match the session?) | completeness (what the session *missed* — the author can't see his own omission = A=A) |
| intent-completeness / 3-doc-gate | no — independent | **completeness** (independent of the author = no A=A) | fidelity — not their job (intent-completeness runs *before* `spec.md` exists; the 3-doc-gate never saw the session) |

If REVIEW(A) tried to judge completeness, A=A means it cannot catch it anyway — the author cannot
enumerate his own unknown unknowns. So completeness is owned *elsewhere*: ELICIT **generates** it in
dialogue (`elicitation.md`, the "unsaid" engines), and **independent** checking is done by two
fresh-eyes passes — `intent-completeness.md` (before SPEC, hunts the agent's un-grounded guesses and
loops them to the *user*) and the `3-doc-gate` (final backstop on the artifact). REVIEW(A) does
**neither** completeness half — it checks fidelity only. (Both completeness files stay live and own
their half: `intent-review.md` is the risk-proportional **lenses ELICIT presses** during dialogue —
generation — and `first-cycle-review.md` is the **foundation-sufficiency rubric** that both ELICIT and
the 3-doc-gate press against — independent audit. Neither is REVIEW(A)'s fidelity job.)

*The shape of the gap REVIEW(A) cannot catch:* a **completeness gap is something the dialogue never
named at all** — not a decision dropped or softened in transcription (REVIEW(A) catches that), but an
entity, rule, or interaction *nobody ever raised*. Holding only the session, REVIEW(A) has nothing to
compare it against — **you cannot diff against what was never said** — so it is structurally blind to
this class, not merely careless. That is why the class is owned elsewhere: ELICIT's generative engines
(`elicitation.md`) are built to surface the unsaid *during* dialogue, and the independent 3-doc-gate is
the after-the-fact backstop on the finished artifact. REVIEW(A) is simply the wrong instrument for a
gap that is invisible from inside the session.

## Split the findings (two branches)

- **Internally resolvable** (something dropped in transcription, a gap the session already settled
  that you can fill from the record) → **fix the spec** yourself.
- **A user-only intent-gap** (something even the session never settled — only the user can fill it) →
  **do not auto-fill it.** Reopen ELICIT and ask. **The reopen is narrow — aimed at that specific
  gap only**, not a fresh run of the whole ELICIT loop (do not spin ELICIT→SPEC→REVIEW endlessly).
  If a gap survives even after the reopen and rewrite (rare), do not loop further — **escalate to the
  user explicitly.**

## Gate (proceed to PLAN when)

- `spec.md` is written (+ first cycle: the Foundation is written), and the fidelity check passes
  (zero blocking fidelity gaps).
- No user-only intent-gap remains (any was resolved by a narrow ELICIT reopen).

## Universality guard

Stack-agnostic. Fidelity is "session vs. document," independent of stack; what was decided is whatever
this project's dialogue produced, judged at runtime.
