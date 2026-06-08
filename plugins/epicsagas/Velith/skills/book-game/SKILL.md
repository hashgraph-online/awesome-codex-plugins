---
name: book-game
description: "Game scenario patterns — quest/event trees, branching dialogue, world-building, character arcs across routes, lore bibles."
---

# Game Scenario Patterns

**Story architecture**: Main scenario (critical path, 60%) + Side scenarios (optional, 30%) + Hidden scenarios (easter eggs, 10%). Critical path must work standalone; side scenarios enrich but never gate main progression.

**Branching structure**: Binary choice (A/B), multi-way (3+ options), conditional (requires item/flag), timed (deadline-based). Branch depth: ≤4 levels before convergence. Convergence types: full (all paths merge), partial (some carry forward), butterfly (small choice → big consequence later).

**Quest design**: Objective (clear goal) → Prerequisites (what player needs) → Steps (3-7 per quest, each with verification) → Branch points (player agency) → Resolution + Reward. Quest chains: linear (A→B→C), hub (return to base between quests), parallel (simultaneous tracks).

**Dialogue system**: Dialogue nodes with speaker, line, emotion tag, and next-node links. Player responses: investigate (info), persuade (relationship), action (consequence). Branch dialogue: ≤3 choices per node. Emotional tone tracking per NPC (friendly/neutral/hostile affects available options).

**World-building layers**: Geography (maps, regions, travel routes) → History (timeline, key events, ruins) → Culture (factions, beliefs, customs, taboos) → Economy (resources, trade, scarcity) → Ecology (creatures, environments, hazards). Each layer must be consistent and interconnected.

**Character arc across routes**: Core identity (consistent across all routes) + Route-specific development. NPC relationship system: trust level (0-100) with threshold gates. Companion characters: personal quest triggered by trust threshold.

**Lore bible**: Entry per: location, character, faction, item, event, concept. Fields: name, description, connections (linked entries), game-mechanic relevance, narrative role. Consistency check: cross-reference all entries before finalizing.

**Scenario document structure**: Overview (concept, tone, themes) → World bible → Character bible → Main quest line → Side quests → Dialogue trees → Cutscene scripts → Branching map (visual flowchart). Each quest has: ID, title, summary, prerequisites, steps, branches, rewards, flags set.

**Format**: Markdown with YAML frontmatter per quest/node. Branching maps as Mermaid flowcharts. Dialogue as structured blocks with speaker/emotion/response fields.
