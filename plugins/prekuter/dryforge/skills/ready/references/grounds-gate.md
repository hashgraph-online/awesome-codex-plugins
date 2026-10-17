# grounds-gate.md — the question filter (shared by DECOMPOSE and ELICIT)

A candidate — a conflict flag from DECOMPOSE, or a probe-generated "unsaid" candidate from ELICIT's
re-measurement — becomes a **confident question** only if it clears this gate. The detectors
deliberately raise more than survives (they are liberal on purpose); this gate is what keeps the
dialogue from degrading into generic "have you thought about concurrency?" spray that fatigues the
user. Shared by both stages so the standard for "worth asking" is one rule, not two.

## The three grounds (state all three, per site)

A candidate is a confident question only if you can state **all three**:

1. **The specific site** — the exact requirement / code path / endpoint / entity it lands on (not
   "X in general").
2. **Why it is not already covered** — a *positive* argument that the spec, the plan, the code, the
   harness, or a framework/convention default does not already handle it. "Might be missing" /
   "unclear" is **not enough**: actively rule out that it is already covered.
3. **The concrete consequence** if it is left unaddressed.

If you cannot ground all three, do **not** raise it as a confident question.

## Asymmetric default

**Insufficient grounds → not a confident question.** This is the inverse of a keep-by-default pass:
escalate only what you can ground. The "why not covered" test (ground 2) is where most candidates
die — it removes the bulk of probe false positives (cross-stack testing showed roughly half of what
the detectors raise are false positives) while keeping the grounded structural/contract gaps.

## A load-bearing-dimension candidate may NOT be *silently* dropped (anti-evasion)

The drop default exists to suppress **noise** — not to let the agent route a load-bearing question it
doesn't want to ask around ELICIT's exit bar (`elicitation.md` — "no guess survives"). That exit only governs
candidates that *became questions*; a candidate killed here never reaches it. So a lazy agent could
under-argue ground 2 ("a framework default probably covers this") to drop a load-bearing dimension
before the bar ever sees it. **Close that route:** when the dropped candidate is on a **load-bearing
dimension the decision-surface accounting raised** (`elicitation.md`), the drop is **not silent** — it must be **recorded in the
spec as that dimension's `N/A — covered by [the ground-2 argument]`** (e.g. "Concurrency: N/A — the
framework's transaction default serializes these writes"). This converts a silent suppression into an
**auditable, falsifiable claim** the independent 3-doc-gate can check against the code. Dropping noise
stays silent; dropping a load-bearing dimension leaves evidence.

## Two tiers (so the gate never silently buries a real gap)

- **Confident questions** — grounded on all three. These are the questions you actually ask (ordered
  by leverage, each carrying a recommended default — see `elicitation.md` for the recommend-first
  rule).
- **Low-confidence candidates** — failed the "why not covered" test (typically a pre-existing trait,
  a framework default, or something derivable from a pattern) but might still matter. Hold them
  briefly for a quick scan; do not press them as blocking.

The low-confidence tier recovers the rare real-but-hard-to-ground item the gate would otherwise drop,
so the asymmetric default never *silently* buries a real gap.

## Universality guard

Stack-agnostic. The three grounds and the two tiers apply to any candidate in any stack; what counts
as a "framework default" or a "convention" that already covers a site is discovered from the project
at runtime, never assumed here.
