# Data-Driven Game Content Patterns

Use this file when moving entities, items, loot, or balance data into files.

## When To Move To Data

Move content into data when:

- Spawn functions mostly differ by name, glyph, stats, effects, or level.
- Designers or agents need to add content without recompiling.
- Balance changes are frequent.
- Spawn tables need weights or level gates.
- Items and enemies share common components.

Keep content in Rust when:

- The behavior is still experimental and changes every edit.
- A field has no runtime system that can use it.
- The project has only one or two entities and no duplication yet.

## Schema Shape

```rust
use serde::Deserialize;
use std::collections::HashSet;

#[derive(Debug, Clone, Deserialize)]
struct ContentFile {
    entities: Vec<EntityTemplate>,
}

#[derive(Debug, Clone, Deserialize)]
struct EntityTemplate {
    kind: EntityKind,
    name: String,
    glyph: char,
    levels: HashSet<usize>,
    frequency: u32,
    hp: Option<i32>,
    effects: Option<Vec<EffectTemplate>>,
}

#[derive(Debug, Clone, Deserialize)]
enum EntityKind {
    Enemy,
    Item,
}

#[derive(Debug, Clone, Deserialize)]
struct EffectTemplate {
    effect: String,
    amount: i32,
}
```

## Example RON

```ron
ContentFile(
    entities: [
        EntityTemplate(
            kind: Item,
            name: "Spark Tonic",
            glyph: '!',
            levels: [0, 1],
            frequency: 2,
            effects: Some([EffectTemplate(effect: "Heal", amount: 4)]),
        ),
        EntityTemplate(
            kind: Enemy,
            name: "Ash Imp",
            glyph: 'i',
            levels: [1, 2],
            frequency: 3,
            hp: Some(3),
        ),
    ],
)
```

Adapt field names and format to the target project.

## Loading Rules

- Load data through one function with a clear path.
- Return `Result` from library code; use `expect` only when a missing data file
  is intentionally fatal for a binary.
- Validate immediately after deserialization.
- Include file path and entity name in error messages.
- Do not silently ignore unknown effects unless the design explicitly supports
  modding with warnings.

## Spawn Table Weighting

Simple weighted table:

1. Filter templates whose `levels` include the current level.
2. Add each template to an available list `frequency` times, or use a weighted
   random helper.
3. Pick from available templates for each spawn point.
4. Convert the chosen template into components.

Rules:

- Empty available table is an error or an intentional "spawn nothing" result.
- Frequencies should be positive.
- Level gates should be validated against expected game depth.
- Keep unique entities, player entities, and victory conditions out of generic
  random spawn tables unless the design requires them.

## Template To Components Boundary

Use one conversion path:

```rust
fn spawn_from_template(world: &mut World, point: Point, template: &EntityTemplate) {
    match template.kind {
        EntityKind::Enemy => {
            // Add enemy marker, position, render, health, AI, name.
        }
        EntityKind::Item => {
            // Add item marker, position, render, effects, name.
        }
    }
}
```

Do not let combat, rendering, and inventory systems each parse template data.

## Validation Checklist

- [ ] Every entity has a non-empty name.
- [ ] Every glyph is renderable by the chosen font/asset pipeline.
- [ ] Every level gate is within supported game depth.
- [ ] Frequency is non-zero for random-spawn content.
- [ ] Every effect string maps to a known effect implementation.
- [ ] Enemies have required combat stats.
- [ ] Items have at least one usable effect or pickup purpose.
- [ ] Generic spawn tables exclude player and one-off win conditions.

## Common Smells

| Smell | Fix |
|---|---|
| Data file contains fields no system reads | Remove field or implement system |
| Many custom spawn functions differ only by stats | Introduce templates |
| Runtime panic says only "failed to load" | Include path and entity context |
| Balance edits require recompilation | Move numbers to data |
| Data drives behavior names but behavior is missing | Validate effect registry |
