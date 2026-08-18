# Game Mechanics Design Guide

## Mechanics Checklist

Use this checklist whenever a gameplay feature is underspecified.

### Space

- What is the play space: discrete grid, continuous arena, graph, track, map, menu, dialogue state, or abstract economy?
- What positions, distances, adjacency, zones, and boundaries matter?
- What spatial information is visible, hidden, or inferred?

### Time

- Is play turn-based, real-time, simultaneous, pausable, tick-based, or event-driven?
- What timing windows matter?
- What can happen before the player can respond?

### Objects And Attributes

- What entities exist?
- Which attributes change?
- Which attributes are visible to the player?
- Which values are authored, generated, or derived?

### State

- What state defines a valid game moment?
- What state transitions can occur?
- What state must persist across sessions, levels, or runs?

### Actions

- What can the player do?
- What can the system do?
- Which actions are strategic, dexterity-based, social, creative, or expressive?
- Which actions are forbidden even if the engine could support them?

### Rules And Goals

- What are the hard rules?
- What are soft incentives?
- What are immediate, short-term, and long-term goals?
- What prevents a player from ignoring the intended loop?

### Skill, Chance, And Information

- Which outcomes depend on player skill?
- Which outcomes depend on chance?
- What information is secret, revealed, noisy, delayed, or player-created?
- Does chance create suspense and variety, or does it erase agency?

## Emergence Scan

For every mechanic, ask:

- Can simple rules combine into surprising decisions?
- Can one strategy dominate all others?
- Can the player get trapped in a boring but optimal loop?
- Can feedback arrive too late to teach?
- Can the mechanic scale into new content without bespoke code every time?

## Implementation Bias

For AI-built games, prefer:

- Declarative rule data over hardcoded special cases.
- Small deterministic simulations with reproducible seeds.
- Tunable constants grouped in config.
- Debug overlays for hidden state, probabilities, cooldowns, and target selection.
- Unit tests for edge cases before visual polish.

## Source Notes

- Book source: Jesse Schell, *The Art of Game Design: A Book of Lenses, Third Edition*, chapters 12-14 (`https://www.routledge.com/The-Art-of-Game-Design-A-Book-of-Lenses-Third-Edition/Schell/p/book/9781138632059`).
- Related framework: Hunicke, LeBlanc, and Zubek, "MDA: A Formal Approach to Game Design and Game Research" (`https://www.cs.northwestern.edu/~hunicke/pubs/MDA.pdf`).
