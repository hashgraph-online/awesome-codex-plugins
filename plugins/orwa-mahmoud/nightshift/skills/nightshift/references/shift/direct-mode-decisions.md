# Direct-mode decisions

Run directly means make progress, not avoid judgment:

- choose the strongest production-quality default;
- make reasonable, reversible decisions on the isolated branch or inside the artifact work target;
- preserve compatibility or include migration and rollback where a breaking change is justified;
- implement and verify the decision;
- record every significant choice, evidence, alternatives, shipped result, and rollback in
  `parking-lot.md`; then continue.

Stop for the owner only when the action is outside the granted coding-work boundary: publishing,
merging, deploying, deleting production data, exposing secrets, spending money, or changing legal or licensing policy.
A difficult or potentially breaking code change is not automatically outside the
boundary when it is isolated, tested, reviewable, and reversible.
