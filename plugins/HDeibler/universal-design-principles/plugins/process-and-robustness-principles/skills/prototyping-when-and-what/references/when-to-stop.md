# When to stop prototyping: reference

A reference complementing `prototyping-when-and-what` with patterns for the prototype-to-ship transition.

## Stopping criteria

Define before starting:

- **The question is answered.** The prototype's purpose was to resolve X; X is resolved.
- **Diminishing returns.** Each iteration produces less new learning.
- **Build-vs-prototype crossover.** The next iteration would essentially be the production build; just build.
- **External pressure.** Time, budget, or competitive pressure forces commitment.

Without explicit stopping criteria, prototyping can continue indefinitely (perfectionism) or stop too early (premature commitment).

## The "good enough to ship" framing

Lean Startup popularized "MVP" — minimum viable product. The threshold for "viable" is the stopping criterion: enough to learn from real users, not necessarily enough to be loved.

For internal tools: viable might mean "team can use it without major friction."
For consumer products: viable might mean "early adopters tolerate it; we learn from their use."
For enterprise products: viable might mean "lighthouse customer signs."

Each context has different viability thresholds.

## Prototype-to-product transition

The transition is risky:

- **Code prototypes** often have technical debt that makes production-quality refactoring expensive.
- **Visual prototypes** lack edge-case handling.
- **Flow prototypes** miss accessibility considerations.

Plan the transition explicitly. Some teams treat the production build as a separate project informed by the prototype; others continue evolving the prototype with progressively higher quality bars.

## Risk of indefinite prototyping

Symptoms:

- Multiple "we just need one more iteration" cycles.
- Stakeholders treating prototypes as products.
- The prototype's polish exceeding the original brief.
- Team forgetting why they started prototyping.

When these appear, force the question: are we building this or not? If yes, ship the next iteration as v0.1 production; learn from real use.

## Resources

- Ries, E. *The Lean Startup* (2011) — MVP framing.
- Brooks, F. *The Mythical Man-Month* (1995) — "plan to throw one away."
- Knapp, J. *Sprint* (2016) — five-day design sprint with explicit stopping.
