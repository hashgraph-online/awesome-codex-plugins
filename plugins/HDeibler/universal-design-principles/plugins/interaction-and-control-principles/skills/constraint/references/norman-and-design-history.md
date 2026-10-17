# Constraint: design-history reference

A reference complementing the `constraint` SKILL.md with deeper context on the principle's history and Norman's broader framework.

## Norman's four-part taxonomy

In *The Design of Everyday Things* (1988, 2013), Donald Norman distinguished four kinds of constraint:

- **Physical**: structural prevention (a slot only accepts the right shape).
- **Semantic**: relies on the meaning of the situation (a steering-wheel column only goes one direction because of what driving means).
- **Cultural**: relies on convention (red means stop because of cultural agreement).
- **Logical**: relies on reasoning ("the third button must be the one I haven't tried").

Lidwell, Holden, and Butler (2003) compressed these into two: physical and psychological (where psychological subsumes Norman's semantic, cultural, and logical). The simplification is workable for design purposes; the four-part version is more precise for analysis.

## Cross-domain examples of constraint design

### USB-C and the elimination of orientation error

USB-A required users to insert the connector "right-side up" — and most people got it wrong on the first try, often the second too. USB-C's rotational symmetry eliminated the problem at the design layer. Generations of frustration eliminated by a single design move.

### Child-safety pill caps

Push-and-twist simultaneously is a constraint calibrated to adult vs. child motor skill. Trade-off: arthritic adults sometimes struggle. The design acknowledges the trade-off and accepts it because childhood poisoning prevention is the higher priority.

### Lockout-tagout in industrial settings

Workers physically lock and tag energy sources before maintenance. The lock requires deliberate removal before re-energizing. Slips that would otherwise injure workers are blocked at the design layer.

### Software type systems

Strongly-typed languages constrain the values a variable can hold. A function declared to take a `User` won't accept a `String`. Many runtime errors are prevented at compile time because the constraint catches them.

### Web browsers' cross-origin restrictions

A web page can't read content from another origin. The constraint prevents an entire class of security vulnerabilities. Trade-off: legitimate cross-origin use cases need explicit opt-in (CORS).

## Constraint vs. confirmation vs. recovery

Three layers of error response:

- **Constraint**: prevent the wrong action.
- **Confirmation**: ask the user to verify before committing.
- **Recovery**: let the user undo after the fact.

The right design uses all three at different levels of stakes:

- Routine reversible actions: recovery only (undo).
- Higher-stakes reversible: confirmation + recovery.
- Irreversible: constraint + confirmation, with structural prevention preferred.

## When constraint isn't enough

Some real-world systems can't constrain certain actions:

- A user with admin access can delete production data. The constraint can't be "they can't delete it"; it must be "they must really mean to."
- A pilot can override the auto-pilot's stall protection. Sometimes pilots need to do that; the constraint is balanced against authority.

In these cases, layered defenses (constraint + confirmation + recovery + audit log) replace pure prevention.

## Resources

- **Norman, D.** *The Design of Everyday Things* (1988, 2013).
- **Reason, J.** *Human Error* (1990).
- **Petroski, H.** *To Engineer Is Human* (1985) — engineering-side perspective on prevention vs. response.
