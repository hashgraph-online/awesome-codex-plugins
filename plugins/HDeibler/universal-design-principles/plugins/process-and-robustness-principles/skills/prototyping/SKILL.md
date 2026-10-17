---
name: prototyping
description: 'Use this skill whenever the design has unknowns that need testing — when a sketch could resolve a debate, when assumptions about user behavior could be checked cheaply, when a high-fidelity build would benefit from a low-fidelity draft first. Trigger when planning research, when scoping a new feature, when stakeholders want to see something concrete, or when the team is stuck arguing about an approach. Prototyping is one of the foundational principles in ''Universal Principles of Design'' (Lidwell, Holden, Butler 2003) and one of the highest-leverage process principles — the cheapest prototype that resolves the question is almost always cheaper than the consequences of skipping it.'
---

# Prototyping

Prototypes are simplified and incomplete models of a design used to explore ideas, validate assumptions, refine specifications, and test functionality before committing to full implementation. The discipline is matching prototype fidelity to the question being asked — paper sketches answer structural questions cheaply; coded prototypes answer performance questions but cost more. Picking the right fidelity for each question lets teams iterate fast where it matters most.

## Definition (in our own words)

A prototype is a deliberately incomplete version of a design built to answer a specific question that wasn't answerable from specifications alone. Prototypes range from paper sketches (minutes to make, structural questions only) to working code (days or weeks, real-world behavior questions). They are throwaway by intent — the team learns what they need to learn and moves on. The book identifies three kinds — *concept*, *throwaway*, and *evolutionary* — each suited to different questions.

## Origins and research lineage

- **Engineering practice** — prototypes have been used since the industrial revolution. Wright brothers built and tested over 200 wing prototypes before the Flyer.
- **Software engineering** — Frederick Brooks' *The Mythical Man-Month* (1975, 1995) and Barry Boehm's spiral model (1986) both emphasized prototyping as risk reduction.
- **Lidwell, Holden & Butler** (2003) compactly distinguish three prototype kinds: concept (exploratory), throwaway (specific question), evolutionary (incremental refinement toward the final).
- **Tom Kelley & David Kelley** at IDEO, *The Art of Innovation* (2001) and *Creative Confidence* (2013). Codified prototyping as core to design thinking; "fail fast" via cheap prototypes.
- **Michael Schrage**, *Serious Play: How the World's Best Companies Simulate to Innovate* (Harvard Business School Press, 1999). Argued that prototyping cultures outperform specification cultures.
- **Modern continuous-delivery practice** — every staging deployment is, in a sense, a prototype of production behavior; canary releases prototype at increasing scale.

## Why prototyping matters

Specifications and discussions can hide assumptions that only become visible when something concrete exists. A team can argue for weeks about whether a flow makes sense; ten minutes with a paper prototype usually resolves it. Engineering can spend weeks building something that turns out to be wrong; a clickable Figma in advance would have caught the issue.

The economics: prototyping costs scale roughly logarithmically with fidelity (sketch ~ 1x cost, wireframe ~ 5x, mockup ~ 20x, code ~ 100x), but error-discovery cost scales roughly logarithmically with the phase the error is found in (requirements ~ 1x, design ~ 5x, code ~ 50x, production ~ 500x+). Catching errors at the prototype phase is dramatically cheaper than catching them in production.

## The three kinds (from the book)

### Concept prototyping

For exploring preliminary ideas. Quick, cheap, often disposable.

Examples:
- Concept sketches.
- Storyboards.
- Mood boards.
- Wireframes.
- Cardboard mockups for industrial design.
- Foam props.

The book's caution — the **artificial reality problem**: a skilled artist or modeler can make any design look like it will work in a concept prototype. Don't conflate "looks plausible" with "will work in production."

When to use: very early, when the question is "is this concept worth exploring further?" or "do stakeholders agree on direction?".

### Throwaway prototyping

For testing specific aspects of a design. Built to answer a question, then discarded.

Examples:
- Wind-tunnel models of automobile aerodynamics.
- Performance benchmarks of a specific algorithm.
- A/B test variants.
- Standalone interactive demos.

The book's caution — the **scaling-and-integration problem**: a feature that works in a throwaway prototype may not scale or integrate properly when built into the production system.

When to use: when one specific aspect needs verification (performance, usability of one flow, market reaction).

### Evolutionary prototyping

For incrementally building toward the final design. The prototype itself evolves into (or becomes) the production system.

Examples:
- Software MVPs that grow into the product.
- Architectural mockups that inform the final building.
- Iterative product development with continuous user feedback.

The book's caution — the **tunnel vision problem**: evolutionary prototypers often get fixated on tuning existing specifications rather than exploring alternatives. Each iteration improves the current direction but may miss a better direction entirely.

When to use: when design specifications are uncertain or changing, and the team can sustainably iterate.

## When to apply

- **Whenever there's significant uncertainty** about a design choice.
- **Before major implementation investments** — a few hours of prototyping can save weeks of building the wrong thing.
- **When stakeholders disagree** — concrete prototypes resolve disputes that abstract discussions can't.
- **For user testing** — most useful research uses prototypes as the subject.
- **For technical risk reduction** — performance, integration, and scale risks become visible in prototypes earlier than in production.

## When NOT to over-apply

- **For trivial, well-understood decisions.** Prototyping the placement of a Save button on a CRUD form wastes effort.
- **In safety-critical final stages.** Prototypes are by definition incomplete; once a design is destined for safety-critical deployment, formal verification beats further prototyping.
- **As a substitute for shipping.** Endless prototyping without commitment is procrastination disguised as research.

## The fidelity ladder

Different fidelities answer different questions; pick the cheapest fidelity that answers your question.

| Fidelity | Cost | Answers |
|---|---|---|
| Paper sketch | Minutes | Structure, IA, "does this make sense?" |
| Wireframe | Hours | Layout, component placement, navigation |
| Mockup (static, high-fidelity) | Hours-days | Visual style, brand fit, "looks like" |
| Clickable prototype (Figma, Framer) | Days | Interaction flow, "feels like" |
| Coded prototype | Weeks | Performance, edge cases, real data |
| Production beta | Months | Actual user behavior at scale |

(See `iteration-prototype-fidelity` in this plugin for deeper detail on fidelity choices.)

## Worked examples

### Example 1: paper prototype to resolve a debate

Designers and engineers disagree on a flow. Engineering says it's complicated; design says users will figure it out.

A 30-minute paper prototype: sketch the flow on index cards, walk a colleague through it.

Outcome: in 30 minutes, both sides see what works and what doesn't. The debate resolves with concrete evidence rather than opinion.

### Example 2: clickable prototype for user research

A new feature. Before building, the team makes a clickable Figma prototype. They test with 5 users.

Outcome: 3 of 5 users misunderstand the same step. The team revises the flow before any code is written. The build, when it happens, reflects the revisions.

If the team had skipped the prototype, the misunderstanding would have surfaced after weeks of engineering work.

### Example 3: technical spike (throwaway prototype)

A team wants to add real-time collaboration. They suspect their current architecture might not handle the latency. They spend a week building a throwaway prototype with WebSockets, just to measure latency under load.

Outcome: latency is acceptable; the throwaway prototype is discarded; the team proceeds to design the production version informed by what they learned.

If they had skipped the prototype and built the production version directly, they'd have been months in before discovering the latency problem.

### Example 4: evolutionary prototype as MVP

A startup builds an MVP — minimal feature set, minimal polish — and ships it to early customers. Each iteration adds features and polish based on what customers actually use.

Outcome: after a year, the MVP has evolved into the production product. Many features the team initially planned were dropped because customers didn't want them; new features were added based on patterns observed in usage.

The risk: the team may have stuck too closely to the initial concept, missing pivot opportunities. The book's tunnel-vision warning applies.

## The three failure modes (from the book)

Each prototype kind has a characteristic failure:

### Concept: the artificial reality problem

Skilled designers and modelers can make any design *look* like it works. Beautiful storyboards and high-fidelity Figma mockups can suggest a product that, when built, doesn't actually function. Stakeholders see polished prototypes and assume they're closer to ready than they are.

Mitigation: be explicit about what the prototype proves and doesn't prove. A pretty Figma proves "the structure makes sense"; it doesn't prove "this will work."

### Throwaway: the scaling/integration problem

A prototype that works in isolation may not work when integrated. A performance benchmark that assumes idealized conditions may fail under real production load. A user-tested flow that worked with a small group may fail at scale.

Mitigation: identify the assumptions the throwaway makes; verify those before trusting the result. "This worked in our prototype with 100 records" doesn't mean "this will work with 100 million."

### Evolutionary: the tunnel vision problem

Each iteration improves the current direction. Over time, the team gets fixated on tuning existing specifications rather than questioning whether a different direction would be better.

Mitigation: periodically take a step back. Are we iterating on the right thing? Is there a fundamentally different approach we should explore? The "kill your darlings" discipline.

## Cross-domain examples

### Industrial design

The book uses the OXO Good Grips peeler as an example of prototyping in industrial design. The Ojex juicer (also pictured in the book) went through many prototypes — 2D sketches for mechanical motion, 3D foam for form, functional models for usability — each at the right fidelity to answer the question of that stage.

### Aviation

Wright brothers built and tested over 200 wing prototypes before the Flyer. Modern aircraft go through years of prototyping before production — wind-tunnel models, partial assemblies, full mockups, flight prototypes.

### Architecture

Frank Lloyd Wright produced extensive sketches for each project. Mies van der Rohe built physical scale models. Modern architects use BIM software to prototype digitally before construction.

### Software MVPs

The Lean Startup approach (Eric Ries) treats early product versions as evolutionary prototypes. Build the smallest thing that lets you learn from real customers; iterate based on what you learn.

## Anti-patterns

- **Production-quality prototypes.** Building prototypes to production code quality defeats the cost advantage of prototyping.
- **Treating prototypes as products.** Shipping a prototype as if it were finished. Usually missing edge cases, accessibility, performance.
- **Prototypes that don't answer a question.** Building a prototype because "we should make a prototype" rather than because there's a specific question to answer.
- **Skipping prototyping entirely.** "We'll just build it" — produces development-iteration churn that's far more expensive.
- **Polishing too early.** Spending hours on visual design before structure is settled; the polish has to be redone.
- **Stakeholder confusion.** Stakeholders see a prototype and think it's the product. Communicate fidelity explicitly.

## Heuristics

1. **The "what question is this answering?" check.** Before building any prototype, name the question. If you can't, you're not ready to prototype.
2. **The cheapest-fidelity rule.** Pick the cheapest fidelity that answers the question. Going higher than needed is waste.
3. **The "what does this prove?" framing.** State explicitly what the prototype proves and doesn't prove. Communicate this with stakeholders.
4. **The disposability check.** If you'd be sad to throw the prototype away, you over-invested. Prototypes are means; the learning is the end.

## Related principles

- **`iteration`** — prototypes are the vehicles of iteration.
- **`feedback-loop`** — prototypes generate feedback that shapes design.
- **`satisficing`** — prototypes test whether designs satisfice for users; full optimization isn't needed.
- **`scaling-fallacy`** — prototypes that work small may fail large; the throwaway-prototype caution.
- **`uncertainty-principle`** — prototyping with measurement may itself affect what's being measured.
- **`weakest-link`** — prototypes find weak links cheaply.

## Sub-aspect skills

- **`prototyping-concept-throwaway-evolutionary`** — distinguishing the three prototype kinds and when each applies.
- **`prototyping-when-and-what`** — picking what to prototype, what fidelity to use, and when to stop prototyping and ship.

## Closing

Prototyping is the cheapest source of design certainty available. The teams that build the right prototypes — at the right fidelity, asking the right questions — consistently outperform teams that try to specify their way to certainty. The discipline is asking what the prototype is for, picking the cheapest fidelity that answers, and being willing to throw the prototype away once the answer arrives.
