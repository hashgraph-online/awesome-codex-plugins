# Suede AI Ship Copy Skills: Claim Origin Policy

## Complete claim-origin policy

**The audit exists to catch agents inventing things. It never runs on the
requester.**

A research lens that reports "cold start drops to 40ms" is a machine asserting a
number, and it gets opened against its source. The requester saying the same
thing in the brief is the person who owns the product telling you a fact about
it. Those are not the same input and this workflow never treats them as the same
input.

Anything the requester supplies (the brief, the `given` list, `mustSay` strings)
enters the permitted claim set marked `origin: "user"` and is **exempt at every
stage**:

- Intake transcribes it. It does not verify, source, soften, or flag it.
- The audit never sees it. A research fact that merely restates a given is
  removed before the audit rather than checked: the given itself already carries
  that content into the permitted set, so nothing is lost. The run log and the
  evidence record both say "removed", not "passed through".
- **Protected strings are not claims.** A `mustSay` product name or legal line is
  a string to preserve byte-exact, not an assertion to exempt from review. Letting
  a product name count as a given would exempt half the draft from review, so the
  exemption corpus excludes them.
- Research lenses are told it is established and are forbidden from returning a
  constraint that contradicts it.
- Writers assert it plainly. No "reportedly", no "according to", no hedge.
- A review finding aimed at one is **discarded by a pure function** before a
  verifier is spent on it, so a persuasive lens cannot argue its way back in.
  It runs a second time after refutation, so a verifier that sustained one anyway
  still cannot hand it to the reviser.
- The match is **proportional**, not a character floor: the shorter of the given
  and the quoted text must be contained in the longer *and* be at least 60% of it,
  with a 6-character minimum. A lens quoting most of a given is out of scope; a
  lens quoting two words that happen to appear inside one is not. That matters in
  both directions: a flat floor would let a compound sentence (something you said
  **and** something an agent invented) launder the invented half behind the true
  half.
- The refute prompt says out-of-scope **at every severity**, not only for blockers.
- The publish-readiness gate skips it: no spot-check, no drift verdict, no risk
  entry, and no escalation when a live page disagrees. A stale page losing to the
  requester is the correct outcome, not a finding.
- The evidence record lists it as given, with no "unverified" label.

The exemption errs toward dropping. A legitimate finding lost because it brushed
a given is a cost worth paying; a given rewritten by the reviser because a filter
was too clever is the thing this workflow promises cannot happen.

The only hazard that can stop this run is an output path pointing at published
copy, which is a fact about a file path rather than a judgement about anything
the requester said. If an intake agent tries to mark anything else blocking, the
script downgrades it to advisory and logs the overreach.

Invoke the workflow bundled at `skills/suede-ship-copy/workflows/suede-ship-copy.js`.
If you keep a personal copy, `~/.claude/workflows/suede-ship-copy.js` works the same way.
