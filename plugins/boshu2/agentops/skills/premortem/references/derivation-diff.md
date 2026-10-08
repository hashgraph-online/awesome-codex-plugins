# Derivation-diff challenge

Loaded by [Premortem](../SKILL.md) for integration- or extension-class plans
when anchoring on the working plan is the consequential risk.

Select an independent derivation using
[Plan's shared challenge method](../../plan/references/challenge.md), then
compare. Give one fresh context only the intent source and the relevant ground
truth (the vendor docs and stock behavior for integration work, the
repository's patterns and behavior spec for extension work) and never the
author's design. Have it sketch its own design from that ground truth alone.
Compare that independent design with the working plan in the advisory findings;
each supported divergence is a question to resolve. Convergence is weak
evidence that the plan follows the ground truth; divergence names where it may
not.

The challenger answers two questions with an artifact, not an opinion:

- Cathedral: is this the smallest real thing, or does it rebuild what already
  exists? Artifact: the simplest version that satisfies acceptance, plus the
  named reason it is insufficient. No named reason means build the simple one.
- Grain: for integration work, does every component the plan writes have a
  native counterpart in the substrate? Artifact: the native-counterpart list,
  one row per component the plan authors, naming the substrate feature it
  duplicates or the reason none exists.

These are integration- and extension-class checks. The Grain list applies only
to integration-class work; do not impose it on routine feature work.
