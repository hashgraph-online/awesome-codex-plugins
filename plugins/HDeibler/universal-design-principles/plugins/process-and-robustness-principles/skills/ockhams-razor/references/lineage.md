# Ockham's Razor — origins and research lineage

## Medieval philosophy

The principle is named for William of Ockham (c. 1287–1347), an English Franciscan friar and philosopher. Ockham articulated several versions of the principle that "entities should not be multiplied beyond necessity" (Latin: *Entia non sunt multiplicanda praeter necessitatem*). The principle was a methodological tool in medieval philosophical and theological argument: when explaining a phenomenon, the simplest explanation that fits the evidence is preferred.

Ockham didn't invent the idea — earlier philosophers (Aristotle, Aquinas, Duns Scotus) had articulated similar principles — but his name is attached to it through historical tradition.

The original use was epistemological: when constructing explanations of natural or theological phenomena, don't posit unnecessary entities. If two theories explain the same phenomenon equally well, the one with fewer assumed entities is preferred.

## In modern science

The razor became a methodological touchstone in modern science. Newton's third "rule of reasoning" in *Principia Mathematica* (1687): "We are to admit no more causes of natural things than such as are both true and sufficient to explain their appearances." Einstein's variant: "Everything should be made as simple as possible, but no simpler."

In scientific practice, the razor functions as a tiebreaker. Among theories that fit the data equally well, the simpler one is preferred. This isn't because nature is "simple" but because simpler theories are easier to test, falsify, and build upon.

The razor doesn't claim that simpler theories are *true* — it claims they're a better starting point. Complex theories may turn out to be correct (general relativity is more complex than Newtonian mechanics), but they need to earn their place by explaining things the simpler theory can't.

## In engineering and design

Engineering has independently arrived at similar principles through painful experience with complexity:

- **KISS (Keep It Simple, Stupid).** Lockheed engineer Kelly Johnson's principle for designing aircraft.
- **YAGNI (You Aren't Gonna Need It).** Extreme Programming principle: don't build features until they're actually needed.
- **DRY (Don't Repeat Yourself).** A different kind of simplicity — eliminating redundancy.
- **Worse is better.** Richard Gabriel's controversial 1989 essay arguing that simpler systems often beat more elaborate ones in real-world adoption.

These all express variations of the razor adapted to engineering contexts: complexity is expensive; eliminate what you can.

## In product design

In product design, the razor cuts in a few specific contexts:

**Feature decisions.** Should we add this feature? The razor asks: does it earn its place? Could users accomplish the goal without it?

**Architectural decisions.** Should we use this technology / framework / dependency? The razor asks: is the simpler alternative sufficient?

**Visual decisions.** Should the design include this element? The razor asks: does it serve the user, or is it decoration?

**Interaction decisions.** Should this be a setting, a default, or something the system decides? The razor asks: is the user's choice valuable, or is it just complexity?

The discipline is to be willing to say no to additions, even attractive ones, when they don't earn their place.

## The razor and its critics

The razor is widely cited but also widely contested. Critics make several points:

**Complexity is sometimes essential.** Some problems are genuinely complex; oversimplifying solutions to them produces failures.

**"Simpler" is in the eye of the beholder.** What counts as simpler often depends on assumptions and context. A design that's simpler in code may be more complex to use, or vice versa.

**Premature simplification is its own failure.** Stripping things before understanding their purpose can be worse than including them.

**The razor is a heuristic, not a law.** It works as a tiebreaker, not a rule that overrides other considerations.

These critiques don't undermine the razor — they refine its application. The razor is most useful as a discipline against unnecessary complexity, not a mandate for minimum complexity.

## Empirical patterns worth remembering

The literature on complexity in design and engineering converges on:

- **Complexity has compounding costs.** Each addition is small; the accumulated cost is substantial.
- **Removal is harder than addition.** Once a feature exists, removing it generates user resistance even if usage is low.
- **The right time to simplify is at the moment of decision.** Adding restraint at decision time prevents accumulation.
- **Simple systems evolve more easily than complex ones.** A simple system can become complex; a complex system rarely becomes simple without major rework.
- **Documentation length is a proxy for complexity.** When the user manual gets longer, the design has gotten more complex.

## Modern relevance: AI and complexity

The current generation of AI tools introduces a new variant of the razor question. AI capabilities tempt designers to add intelligence everywhere — every input gets autocomplete, every action gets a recommendation, every workflow gets an AI assistant.

The razor question: does each AI capability earn its place? Or is it adding complexity that the user has to evaluate and trust without proportional benefit?

Some AI features genuinely earn their place (search relevance, spam detection, transcription). Others are complexity in disguise (an AI suggestion that's wrong as often as right; a chat interface for tasks that have a clearer non-chat solution).

The razor still cuts: even powerful capabilities should be added only when they're better than the simpler alternative.

## Sources informing this principle

- William of Ockham (14th century). Various philosophical writings.
- Newton, I. (1687). *Principia Mathematica*. (Rules of reasoning.)
- Einstein, A. (Various).
- Gabriel, R. (1989). "The Rise of Worse is Better." (On the trade-offs in software engineering.)
- Lockheed engineering tradition (KISS principle).
- Beck, K., et al. (2000s). Extreme Programming literature (YAGNI principle).
- Lidwell, W., Holden, K., & Butler, J. (2003). *Universal Principles of Design*.
- Various essays on minimalist design (Dieter Rams, John Maeda's *The Laws of Simplicity*).
