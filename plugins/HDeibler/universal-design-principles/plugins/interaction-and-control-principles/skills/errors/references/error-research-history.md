# Error research and design history

A reference complementing the `errors` SKILL.md with the academic and engineering history.

## Norman's "Categorization of Action Slips"

Donald Norman's 1981 paper in *Psychological Review* introduced the slip/mistake distinction to design vocabulary. Prior to Norman, "human error" was treated as a general category attributable to user failure. Norman's reframing — that errors are properties of design — opened the modern human-centered design tradition.

The paper categorized slips by mechanism: capture (a habitual sequence overrides the intended one), description (insufficient specification of intent), data-driven (an external stimulus triggers the wrong action), associative-activation (one thought activates a wrong related thought), and others. The classification was largely descriptive but useful for distinguishing fix strategies.

## Reason's *Human Error* (1990)

James Reason's book is the standard reference work in the human-error literature. Key contributions:

- **Skill-based, rule-based, knowledge-based** error taxonomy (slightly more granular than Norman's slips/mistakes).
- **Latent vs. active errors** — some errors lie dormant in system design until conditions trigger them.
- **The Swiss-cheese model** of cascading failures: complex accidents happen when multiple latent vulnerabilities align with active errors. No single point of failure causes the accident; the accident emerges from the system.

Reason's work originated in industrial-safety contexts (Chernobyl, Bhopal, Three Mile Island) and has been applied to medicine, aviation, software, and product design.

## Perrow's *Normal Accidents* (1984)

Charles Perrow argued that complex tightly-coupled systems produce catastrophic accidents as an emergent property — the system's complexity itself makes some accidents inevitable. Tight coupling means a small failure cascades; complexity means operators can't foresee all interaction effects.

Software engineering grapples with this constantly. Modern microservices architectures, with their complex inter-service dependencies, exhibit normal-accident dynamics — a single service's failure cascades unexpectedly because the coupling is tight and the system is complex.

The design response: reduce coupling, simplify when possible, build observability so failures are visible, and recognize that some accidents are emergent properties of complexity rather than failures of operators.

## Gawande's *The Checklist Manifesto* (2009)

Atul Gawande, surgeon and writer, documented how aviation-style checklists reduce error in surgery, construction, and software. Key findings:

- Checklists prevent slip-type errors by externalizing memory.
- Resistance to checklists comes from professional pride ("I don't need a checklist for this") — but data shows even experts benefit.
- Effective checklists are short, focused on critical steps, and used at "pause points" (preflight, time-out before incision).

The book popularized checklists in software and product engineering. Pre-deployment checklists, code-review checklists, and incident-response runbooks all descend from this thinking.

## Cross-domain examples

### Aviation: the rise of CRM

The 1977 Tenerife airport disaster — two 747s collided on a runway — was traced partly to crew dynamics: the captain's authority discouraged challenge. The aviation industry developed Crew Resource Management (CRM) training to encourage crews to challenge each other's decisions, reducing decision-mistakes. Decades of airline safety improvements descend from CRM.

### Medicine: Universal Protocol

The Universal Protocol (mark surgical site, time-out before incision) was developed to prevent wrong-site surgery — a high-stakes mistake that occurred more often than the public realized. Implementation reduced wrong-site surgeries dramatically.

### Industrial: lockout-tagout

LOTO procedures prevent slip-type errors by physically blocking accidental energizing of equipment. The locked-out lock requires deliberate removal before the equipment can be re-activated.

### Software: defensive programming

The slip/mistake distinction maps to software practice: type checking and assertions catch some slips at compile time; documentation, code review, and testing catch some mistakes pre-production. The practice of "defensive programming" treats user input as adversarial — not because users are adversaries but because errors are inevitable.

## Resources

- **Norman, D.** "Categorization of Action Slips" (*Psychological Review*, 1981).
- **Norman, D.** *The Design of Everyday Things* (1988, 2013).
- **Reason, J.** *Human Error* (1990).
- **Perrow, C.** *Normal Accidents* (1984).
- **Gawande, A.** *The Checklist Manifesto* (2009).
- **Casey, S.** *Set Phasers on Stun* (1998) — case studies of design-induced errors.
