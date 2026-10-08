# Output self-check

A short, fixed checklist every skill applies to an artifact **before presenting it at a
checkpoint**. It makes the suite's standing claim — "every artifact obeys the suite's own
rules" — an actual pass the model runs, not a hope. It is the artifact-level complement to
the Quality Gate (which audits the course) and to `ts/scripts/check_content_markers.py` (which
scans finished files). Keep it terse; failing any line means fix-before-present, not ship.

Run silently; surface only the lines that fail, in the checkpoint's **Flags** block.

## The check (every produced artifact)

1. **Grounding** — every factual/evaluative claim traces to material the professor
   provided or to a cited source. Nothing invented to sound complete. Gaps are
   `[NEEDS PROFESSOR INPUT: …]`; uncertain domain claims are `[VERIFY: …]`.
2. **No silent defaults** — every consequential choice made for the professor is named in
   the checkpoint's "Key decisions", not buried in the artifact.
3. **Markers honest** — `[NEEDS PROFESSOR INPUT]` / `[VERIFY]` used for exactly what they
   mean; none left in a *finalized* student-facing artifact (drafts may carry them).
4. **Person-affecting guardrails** (feedback, letters, interventions, integrity cases):
   the artifact is built from a template that carries the claim-trace structure and the
   non-removable verify-before-send block; no student PII is written to the passport.
5. **Voice & altitude** — reads in the professor's plain voice, not AI-boilerplate
   ("delve", "exciting journey", "in today's fast-paced world"); pedagogy citations are in
   the *rationale*, never in the artifact itself.
6. **Accessibility floor** — student-facing artifacts use real headings/lists, alt-text
   notes for figures, and readable structure (Quality Gate U-checks).
7. **Passport discipline** — any passport write is append-not-overwrite, to this stage's
   own fields, and `confirmed_by_professor` is set only at a real confirmation.

## Why this is here, not just enforced by gates

The gates fire at stage boundaries (1.5, 3.5); many artifacts (a single lesson, one
feedback batch, an email) ship between gates. This check travels with *every* artifact so
the honesty rules don't depend on a gate being nearby. The deterministic scripts cover
what a machine can see (markers, passport structure, PII patterns); this list covers the
judgment a machine can't — and naming it makes it auditable rather than implicit.
