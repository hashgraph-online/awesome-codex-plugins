# Adoption and decision lineage

Read this for an adoption question or a "why is it like this" question.
Research's [evidence rules](../SKILL.md#evidence-rules) still apply.

## Adoption questions

For "should we adopt, replace or keep X" or "does advisory Y reach us", the
answer needs both sides. Ours: the current tool and a cited place it is used,
or a searched absence plus where X would plug in, and any earlier decision on
the same question. Theirs: a current primary source for each external fact the
answer rests on. A strong side never covers a missing one; then answer "not yet
answerable" and list what to inspect. Keeping the current tool or doing nothing
is a real option. A claim made in the conversation is a lead to check, not
evidence. For a choice that is costly to undo, each decisive claim needs two
independent sources; a vendor page speaks for its own product and is not
independent support. Rank candidates for "what should we use for X" only when
the short list comes from current sources and the criteria are stated or
recoverable; otherwise return what was found and name what is missing.

When the question compares another tool's features with ours, tag each of its
capabilities by source: `code` (their source shows it; cite the `file:line`
you opened and say what the code does, often less than the claim), `docs`
(a README, page or announcement says it; unverified) or `hosted` (a service
you cannot inspect). Only a `code` capability can be recommended for adoption;
a `docs` or `hosted` one stays a gap to verify. Our side of each row cites our
file, or the search command and scope that found nothing. Recommend taking the
pattern in our own terms, not their runtime or storage engine, and hand a
choice that is costly to undo (an architecture fork, a storage or data
migration) to [Plan](../../plan/SKILL.md).

## Decision lineage

For "why is it like this" or "how did this idea change", trace one decision or
idea through commits, ADRs, issues, reviews and prior reports into dated, cited
buckets: first appearance, clearest statement, current form, reversals,
contradictions (two claims that cannot both hold) and abandoned variants. An
empty bucket says what was searched; a supersession is not a contradiction; do
not smooth messy history into a tidy story. Before presenting a past reason as
binding, check that its cause still holds in the current tree or record; if
not, report that as evidence for reopening, leaving the call to its owner or
the caller.
