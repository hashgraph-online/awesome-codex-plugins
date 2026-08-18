# Game Prototype Loop Guide

## Operating Model

Treat game creation as a sequence of answered questions, not a march through a feature backlog. A polished feature can still be wrong; a crude prototype that exposes the wrongness quickly is valuable.

Use this sequence:

1. Experience: what should the player feel, do, notice, or learn?
2. Problem: what design challenge must be solved to create that experience?
3. Assumptions: what could make the idea fail?
4. Prototype: what is the cheapest artifact that tests one assumption?
5. Evidence: what observation would change the plan?
6. Decision: what should the builder do next?

## Risk Categories

- Core fun risk: the central action may not be enjoyable.
- Comprehension risk: players may not understand goals, controls, feedback, or consequences.
- Novelty risk: the idea may feel too familiar or too strange.
- Scope risk: content, art, level design, AI, networking, or tuning may exceed the available budget.
- Technical risk: the engine, input model, physics, camera, tools, or performance target may be uncertain.
- Balance risk: choices, rewards, difficulty, or economies may collapse into obvious strategies.
- Production risk: the game may need too many assets, encounters, or bespoke moments.
- Audience risk: the target player may not want the promised experience.

## Prototype Types

- Paper prototype: tests rules, economy, turn structure, and information clarity.
- Spreadsheet prototype: tests math, progression, resource loops, and expected value.
- Greybox prototype: tests movement, camera, combat feel, timing, layout, and readability.
- Toy prototype: tests a repeated action without levels, story, or progression.
- Wizard-of-Oz prototype: simulates AI, multiplayer, generation, or backend behavior manually.
- Slice prototype: tests whether a representative minute of the game can carry the intended experience.

## Filters For Selecting Ideas

Score each concept against these filters:

- Designer conviction: the team has real curiosity and energy for it.
- Player promise: the experience is legible to a target player.
- Essential experience: the concept supports the intended emotion or activity.
- Novelty: it has a clear reason to exist.
- Feasibility: the implementation can be made with available time, tools, and skill.
- Growth path: the prototype can expand into a full game without changing identity.
- Evidence path: there is a realistic way to test whether it works.

## Source Notes

- Book source: Jesse Schell, *The Art of Game Design: A Book of Lenses, Third Edition*, chapters 7-8 (`https://www.routledge.com/The-Art-of-Game-Design-A-Book-of-Lenses-Third-Edition/Schell/p/book/9781138632059`).
- Related framework: Hunicke, LeBlanc, and Zubek, "MDA: A Formal Approach to Game Design and Game Research" (`https://www.cs.northwestern.edu/~hunicke/pubs/MDA.pdf`).
