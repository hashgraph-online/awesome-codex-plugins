# Engineering Standard — All Depths

Trace the actual flow and callers before choosing a change. Reuse existing
code, standard-library/native facilities, then installed dependencies. Prefer
meaningful names, direct control flow, and cohesive functions/modules; readability
beats code golf. Delete unused/duplicate code and unnecessary layers rather than
adding wrappers or speculative frameworks.

Address encountered bad code, mixed responsibilities, and oversized modules in
the task's execution path. Fix shared causes once. Plan substantive cleanup with
the feature; implement it without extra permission when already authorized. If
additional files are needed, update ownership/contracts and serialize overlapping
work before editing. Do not hide necessary repairs behind an obsolete file fence
or refactor unrelated systems. Planning-only requests still stop before coding.

Preserve observable behavior and safety invariants. When existing coverage is
weak, add characterization tests before refactoring. Run targeted regression
checks before/after meaningful changes and one full suite at final integration.
Tests should expose behavioral failures, not mirror lines, private structure,
or cosmetic choices. Record material deviations and measured verification.
