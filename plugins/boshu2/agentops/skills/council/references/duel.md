# Duel: members score each other's ideas

Loaded by [Council](../SKILL.md) when the caller selects a scored duel.
[Idea Genie](../../idea-genie/SKILL.md) challenges one consequential choice for
Plan; this is the scored tournament.

Before launch the caller fixes the question, the rubric (for example
usefulness, feasibility, cost or complexity, risk), its scale, and the
per-member idea cap.

1. **Generate.** Each member returns its own ranked ideas with evidence, sealed.
2. **Score.** In fresh contexts, each member scores every other member's ideas
   on each rubric line with a reason. Scores stay sealed from other scorers,
   and no member sees any score of its own ideas.
3. **Reveal.** Each member sees how peers scored its ideas and concedes or
   defends with evidence: one bounded round, fresh contexts, peer-informed
   (see [debate](debate.md)).
4. **Synthesize.** Rank by cross-member agreement. Flag a large score gap
   between members as information worth investigating; do not average it away.
   Keep concessions and dissent. A score is a judgment, never proof.

Record each context's ideas, scores, concessions and defenses, with its round,
in `judges[].judgment`; no new schema.

It's working if no member sees scores of its own ideas before the reveal.
