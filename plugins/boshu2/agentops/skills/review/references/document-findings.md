# Document findings

Use this page when the subject is a plan, design, ADR, specification or skill
text rather than code. It narrows which document concerns count as findings;
every rule in [Review](../SKILL.md) still applies.

## Missing detail

An omission is a finding only when a competent implementer or validator could
not work it out from the subject, its references and the repository's
conventions. Judge it against what the subject's stage owes: an intent or
requirements draft is not missing the mechanics a later plan decides, and a
plan is complete once its implementer can act and its validator can judge
([Plan](../../plan/SKILL.md)). Show the problem before
proposing the fix; an attractive addition does not prove anything is missing.

## Where careful readers would diverge

Look for places where two careful implementers would act differently:

- two passages that cannot both hold when no source settles which governs;
- one term used for two things, or two terms for one;
- a reference to something never defined or since removed;
- a quantifier with no bound, such as "all callers" or "any failure";
- a list that could be examples or the complete set;
- a sentence that hides who acts;
- "after X" without saying whether X started, finished or was verified.

Vagueness that every implementer would resolve the same way is not a finding.

## Defects a source settles

When the text or a cited source fixes the answer, such as a wrong count, a
stale reference or a passage that conflicts with its declared owner or a
higher-precedence source, report the defect and its correction. Do not invent
an unlikely reading that turns it into an open question. Leave a choice open
only when no source decides it, and still give your recommendation.
