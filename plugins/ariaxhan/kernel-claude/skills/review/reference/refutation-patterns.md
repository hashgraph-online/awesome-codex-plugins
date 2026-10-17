# Refutation patterns: the false-alarm families

A reviewer's precision instrument. Before reporting ANY candidate finding, check it against
these families. Each was distilled from real reviews where a plausible-looking finding was
refuted by one cheap check; the pattern names the trace that settles it. A finding that
matches a family needs evidence distinguishing it from the refuted precedent, or it dies
before it is reported.

Derived from a 2026-08 field study of production review tooling (Trail of Bits skills,
agent-review-panel, tag1 comprehensive-review) plus a mined corpus of 33 real false alarms.
Projects should grow their OWN corpus file of refuted findings; this file carries only the
generalizable patterns.

## The five refutation moves, in cost order

1. **Read the manifest.** The config/deployment manifest that supplies the "missing" value.
2. **Trace the branch.** Does the suspect path actually execute with real inputs?
3. **Probe.** One read-only command (a SELECT, a curl, a render) beats an hour of reasoning.
4. **Find the settled decision.** Search decision notes/commissions before reporting a
   "contract violation" — the contract may define the behavior you flagged.
5. **Suspect the instrument.** When a checker's verdict is surprising, check the checker's
   own timeline and inputs before trusting it.

## Family 1: crypto-misuse lookalikes
- Fast hash (SHA-256) over a HIGH-ENTROPY RANDOM input is fine; the defect requires a
  low-entropy (human-chosen) input. Trace what is hashed, not which function hashes it.
- A digest used to length-normalize input for a constant-time compare is a mitigation,
  not storage crypto.

## Family 2: fail-open lookalikes
- `if (!secret) ...` is not a finding until you trace which branch the absent-config path
  takes. Fail-CLOSED shapes look identical to fail-open at grep distance.
- An unconfigured default that is the SECURE value, pinned by the only deployment
  manifest, is not a finding. Read the manifest before scoring config-driven code.
- A script that REFUSES to run without its secret is the opposite of an insecure default.

## Family 3: permissive-access lookalikes
- "No auth middleware" is not a finding when the endpoint has a written threat model with
  compensating controls (single-use tokens, rate limits, uniform errors).
- Auth enforced at the platform layer (gateway, service binding, access proxy) is invisible
  to code-only grep. Trace the platform config.
- A dynamic CORS/origin callback is not automatically permissive; enumerate what it admits.

## Family 4: secret/credential lookalikes
- Placeholder/example files (`*.example`, docs) are out of scope; confirm a file's role
  before reporting a committed secret.
- An env fallback is a finding only when the fallen-back value is security-bearing.
  Classify the value, not the call.
- Entropy scanners cannot tell a DIGEST from a CREDENTIAL. Ask what the string unlocks:
  a hash of tracked content unlocks nothing.
- Secret scanners match their own documentation. Read the hit's context.

## Family 5: injection/XSS lookalikes
- Escaping/encoding applied at the sink or template layer often lives one file away from
  the flagged line. Trace the render path before filing.

## Family 6: data-correctness lookalikes
- Before blaming the algorithm, verify the data exists: an empty table explains "no
  results" more often than a broken retriever. `SELECT COUNT(*)` first.

## Family 7: settled-decision lookalikes
- A literally-true "violation" can be the documented contract. Search decision records
  before reporting; reopening a settled entry requires new evidence, not a new opinion.

## Family 8: UI-measurement lookalikes
- The interactive element's LIVE hit area (wrapping label, padding) is what matters, not
  the inner control's declared size. Measure before flagging touch targets.

## Family 9: platform-behavior lookalikes
- "Missing" cleanup/handling that the platform guarantees (request isolation, GC,
  transaction rollback) is not a leak. Cite the platform doc either way.

## Family 10: instrument-was-wrong lookalikes
- A surprising verdict from a checker warrants checking the checker: stale caches, wrong
  working directory, and self-matching patterns produce confident nonsense.

## Family 11: statistical/convention lookalikes
- A metric or convention that looks wrong by general standards may be pinned by a
  measured calibration. Look for the calibration record before re-deriving from first
  principles.

## Severity gates (apply after refutation)

- **Falsification gate:** before any CRITICAL, name the single observation that would
  falsify the finding. If one read-only command could falsify it and nobody ran it, cap
  severity until verified.
- **Consensus deflation:** N reviewers citing the same source lines are ONE source, not N
  confirmations.
- **Strip authority:** judge a dependency CVE by its technical description, not its
  identifier or score.
- **Verify the judge:** any finding the aggregator introduces that no lane reported gets
  the same refutation pass as everything else. The aggregator is the last unverified
  writer in the pipeline.

## Anti-rationalization table (do not skip the checks)

| Excuse | Why it's wrong |
|---|---|
| "Small diff, quick look" | Heartbleed was 2 lines. Classify by risk, not size. |
| "The tools found nothing" | Tools that didn't run found nothing either. Check the skipped-lanes list. |
| "This finding is obviously real" | Half the mined corpus was "obviously real". Run the refutation pass. |
| "I know this codebase" | Familiarity is why context-blind review exists. |
| "Refutation slows us down" | One SELECT has refuted an entire rebuild plan. It is the fast path. |
