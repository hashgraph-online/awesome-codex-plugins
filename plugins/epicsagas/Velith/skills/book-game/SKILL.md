---
name: book-game
description: "Game narrative craft reference: branching architecture, quest design, dialogue systems, lore bible, player agency, and game-writing AI tells. Read by all agents on game scenarios, visual novels, and interactive fiction."
---

# Game Narrative

The reader is a player. They act, and the story must answer. A game script that reads well but ignores the player's hands is a screenplay with buttons.

## Architecture

- **Critical path (60%)**: must work if the player does nothing optional. Every beat of the main story lands regardless of side content.
- **Side content (30%)**: enriches, never gates. Side quests reward with understanding of the world or characters, not only items.
- **Hidden (10%)**: for players who look. Rewards curiosity.
- **Branch depth** ≤ 4 before convergence. Convergence types: full (all paths merge), partial (state carries), butterfly (small early choice, large late consequence; use once or twice per game, telegraph nothing).
- **Choice types**: binary, multi-way, conditional (flag/item), timed. A choice with no consequence is a menu, not a choice. A choice where one option is obviously correct is not a choice.
- **Endings**: each ending is earned by a pattern of choices, not one final selection. The player should be able to explain why they got their ending.

## Quest design

Per quest: ID, title, hook (why the player cares), prerequisites (flags, items, relationships), steps (3-7, each verifiable by the game), branch points, resolution, rewards, flags set. Quest chains: linear, hub, parallel.

The hook is narrative, not "collect five." The reward includes a change in the world the player can see.

## Dialogue system

- Node: speaker, line, emotion tag, next-node links, conditions.
- Player responses ≤ 3 per node; each is a stance (investigate, push, withdraw), not a paraphrase of the same thing.
- NPC state (trust, fear, knowledge) affects available lines. Track in the bible.
- Barks and ambient lines carry world texture; write them with the same care as cutscene dialogue.
- Lines are short. Players skip. The most important line in a conversation is the one that changes state, and it should be unmissable.
- Localization: avoid idioms that do not travel; keep string lengths sane for UI.

## Lore bible

Entries per location, character, faction, item, event, concept, rule. Fields: name, description, connections, mechanical relevance, narrative role, first appearance, flags. Consistency check before finalizing: every named thing in a quest or line exists in the bible. World rules (magic, tech, politics) are stated once and never broken without a story reason.

## Character across routes

Core identity is constant; route-specific development varies. A companion who is warm on one route and cold on another needs a reason the player can find. Personal quests unlock on trust thresholds. Companions comment on the player's choices; silence is also a comment.

## Game-writing tells

- NPCs who explain the world to a player character who lives in it.
- Every choice offering good / neutral / evil.
- Quest text that restates the objective marker.
- Lore dumps in item descriptions that nobody reads.
- Villains monologuing at the boss door.
- Companions who approve of everything.
- Endings differentiated by one final dialogue choice.
- Uniform dialogue length across NPCs.

## Format

Markdown with YAML frontmatter per quest and per dialogue tree. Branching maps as Mermaid flowcharts. Dialogue as structured blocks:

```markdown
### NODE guard_gate_01
**Speaker:** GUARD · **Emotion:** wary · **Condition:** !has_pass
"State your business."
- [investigate] "What happened here?" → guard_gate_02
- [push] "Let me through." → guard_gate_03 (sets: guard_hostile)
- [withdraw] (leave) → END
```

Deliverables per outline: overview, world bible, character bible, main quest line, side quests, dialogue trees, cutscene scripts, branching map, flag table.

## Validation (architect scoring for game)

Critical path works standalone; branch depth within limit with defined convergence; every choice has consequence; endings earned by patterns; every named entity in the bible; flag table complete and no orphan flags; quest steps verifiable.

## Visuals

The scenario document needs: world map and region maps (figure-engineer base layers from the lore bible, stylized by the illustrator), branching maps (Mermaid flowcharts from the quest data, never drawn by hand), character sheets with mechanical annotations, location key art, item and UI mock references. Character and location sheets are locked before scene art. Consistency is not optional: the art bible's constants become the studio's reference. All through `/book-visuals`.
