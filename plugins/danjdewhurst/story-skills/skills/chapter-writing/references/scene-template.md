# Scene Template

Use this template when creating a machine-readable scene file at `scenes/chapter-{NN}-scene-{NN}.md`.

```yaml
---
title: "{Scene Title}"
chapter: chapter-{NN}
scene: {N}
pov: {character-kebab}
location: {location-kebab}
characters:
  - {character-kebab}
mentions:
  - {referenced-character-kebab}
arcs-advanced:
  - {arc-kebab}
status: {outline|draft|revised|final|complete}
date: {YYYY-MM-DD}
time: "{HH:MM}"
travel-hours: {N}
outcome: {yes|no|yes-but|no-and}
sequel: {true|false}
dilemma: "{The choice the POV character must make in the sequel}"
state-changes:
  - character: {character-kebab}
    knowledge: "{What they learned in this scene}"
  - character: {character-kebab}
    physical: "{An injury or other bodily change that carries forward}"
  - target: {artifact-kebab}
    owner: {character-kebab}
    change: "{What happened to the object}"
---
```

`date` and `time` place the scene on the story clock. Set them as soon as the scene's moment is settled: `story timeline` lists undated scenes separately, and `story continuity` runs its clock and travel checks (scenes out of order, a character reaching a location faster than the location `routes` allow) only on dated scenes, so leaving them blank switches those checks off without a warning, except that an undated scene with `travel-hours` above 0 warns. `date` is `YYYY-MM-DD`; `time` is a quoted `"HH:MM"` or one of `dawn`, `morning`, `midday`, `afternoon`, `evening`, `night`. `travel-hours` is optional: a plain number (not quoted) of hours the POV character needed to travel since the previous scene. Leave it out when no journey happens; `story continuity` errors when the timestamps allow less. `mentions` lists characters who are only referenced or remembered in the scene.

`state-changes` lists what the scene changes that later scenes must keep, in two shapes. A change to a character names them with `character` and records `knowledge`, `physical`, or `emotional`, the same fields as `continuity/state.md`. Always record what a character learns as `character` + `knowledge`: `story continuity` checks those entries against `knowledge-state` in `continuity/state.md` (add the same `fact` id when that entry has one), and `story context` gives later scenes the POV character's changes. A change to an object names the artifact with `target`, may set its new `owner` or `location`, which the prop custody check compares with `object-state`, and describes it in `change`. Never put a character id under `target`. Keep only the entries the scene needs.

`outcome` is optional: whether the POV character gets what they want in the scene. `yes-but` and `no-and` are the complicating outcomes; `story pacing` warns after three or more consecutive `yes` outcomes. Leave it out for sequel scenes, which react rather than pursue a goal. `sequel` and `dilemma` are optional. Set `sequel: true` when the scene is the reaction half of the scene/sequel unit; leave them out for ordinary action scenes.

## Purpose

What this scene changes for plot, character, theme, or reader knowledge.

## Sequel

For `sequel: true` scenes — the reaction → dilemma → decision half that follows a scene ending in a setback:

- **Reaction:** How the POV character processes the setback emotionally
- **Dilemma:** The impossible choice they face between the options available
- **Decision:** What they decide to do next — the goal that launches the following scene

## Continuity Notes

Track character state, object state, knowledge, timing, and location facts that later chapters must preserve.
