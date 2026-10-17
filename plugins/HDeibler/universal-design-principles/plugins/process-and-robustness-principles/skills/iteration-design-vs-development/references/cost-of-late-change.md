# The cost of late change: reference

A reference complementing `iteration-design-vs-development` with the empirical basis for "shift left" thinking.

## Boehm's cost-of-change curve

Barry Boehm's research (1981, refined since) showed that the cost to fix a defect rises by orders of magnitude across the project lifecycle:

| Phase | Relative cost |
|---|---|
| Requirements | 1x |
| Design | 5x |
| Coding | 10x |
| Testing | 50x |
| Production | 100–500x+ |

The numbers vary across studies but the shape is consistent: defects discovered early are dramatically cheaper to fix than defects discovered late.

The implication: invest in early activities (requirements, design, prototyping, review) to push defects "left" on the curve.

## Why early defects are cheaper

- **Less work depends on the defective decision.** A change in requirements affects no code; a change in design affects the spec but no code; a change in code affects only that module; a change after deployment affects users and dependent systems.
- **The team's mental model is fresh.** Refactoring code you wrote last week is easier than refactoring code you wrote two years ago.
- **Fewer external dependencies.** Once an API is exposed, partners depend on it; changes have ripple effects.
- **Lower stakes.** A prototype's "bug" is an exploratory finding; a production bug affects revenue and trust.

## Modern variations

The shift-left philosophy has produced specific practices:

- **Test-driven development** — write tests before code; defects in test design surface before defects in code.
- **Property-based testing** — generate random inputs to find edge cases at the test phase.
- **Static analysis / linting** — catch defects at edit time, before commit.
- **Code review** — catch defects before merge.
- **Pre-deployment canary releases** — catch defects in a small percentage of production before full rollout.

Each shifts defect discovery earlier on the curve.

## When development iteration is unavoidable

Some defects can only be found after real-world deployment:

- **Performance issues at scale.**
- **Cross-browser / cross-device rendering bugs.**
- **Race conditions and timing issues.**
- **User behaviors no one predicted.**

The goal isn't zero late-stage defects; it's *minimizing* them. A well-designed project has few surprises during build because design iteration was thorough.

## Resources

- **Boehm, B.** *Software Engineering Economics* (1981).
- **McConnell, S.** *Code Complete* (1993, 2nd ed. 2004).
- **Brooks, F. P.** *The Mythical Man-Month* (1975, 1995).
- **Atlassian / GitHub engineering blogs** — modern shift-left practices in CI/CD.
