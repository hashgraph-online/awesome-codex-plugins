# Snowflake Method

Randy Ingermanson's widely taught top-down design method: start from one sentence and grow it in ten steps, alternating between plot and cast, until the outline is detailed enough to draft from. Each step expands the one before, so a problem found late sends you back to the smallest artifact that contains it. It is a design process, not a beat sheet: pair it with a structure from `references/structure-models.md` (three-act fits its three disasters) and use it when the user wants to plan the whole book before drafting. For stopping partway, see `references/outlining-ladder.md`; steps 1-2 cover its premise rung and steps 8-9 its step outline and full outline rungs.

## Step 1: One-Sentence Summary

The whole novel in one sentence of about fifteen words: who, what they want, what stands in the way. No character names needed; a role and a situation carry it.

**Where it lives:** the first sentence of `## Synopsis` in `story.md`. `story synopsis` prints that sentence as the logline. It is not the `premise:` field, which holds the controlling idea (value + cause). Use the logline recipe in `story-init`'s `references/title-logline.md`.

## Step 2: One-Paragraph Summary

Five sentences: the setup, the first disaster, the second disaster, the third disaster, and the ending. Each disaster closes a phase and forces the protagonist into a harder course; the ending resolves the third.

**Where it lives:** the rest of `## Synopsis` in `story.md`, after the logline. Three-act is the natural fit: set `structure: three-act` in `plot/_index.md` and map the disasters onto its beats: first disaster at the first plot point (~25%), second at the midpoint (~50%), third at the second plot point (~75%). Record the three disasters as the first rows of the main arc's Plot Points table (scaffold the arc with `story add arc '{Name}' --type main --character {id} --theme '{theme}'`) and in `plot/timeline.md`.

## Step 3: Character Summaries

One short sheet per major character: name, their storyline in one sentence, their abstract motivation (what they want from life), their concrete goal (what they want in this story), the conflict that blocks the goal, the epiphany (what they learn or refuse to learn), and a one-paragraph storyline.

**Where it lives:** `story add character '{Name}' --role {protagonist|antagonist|deuteragonist|supporting}` for each, then fill `## Motivations & Goals` (motivation is the need, goal is the want) and `## Character Arc` (the epiphany sets the ending state). Set `arc-type`, `lie`, and `truth` in frontmatter when the epiphany is a lie/truth shift (see `character-management`'s `references/character-template.md`). An antagonist's summary states the `counter-premise:` from their side. If a sheet contradicts the Step 2 paragraph, fix whichever is wrong before continuing.

## Step 4: One-Page Synopsis

Expand each sentence of the Step 2 paragraph into its own paragraph. The setup, disaster, and ending paragraphs become the main arc's body.

**Where it lives:** the main arc file's `## Setup`, `## Rising Action` (one numbered item per disaster and its fallout), `## Climax`, and `## Resolution`. Run `story synopsis . --pages 1` to read back what the arcs say; if it reads thin or wrong, the arc sections are thin or wrong.

## Step 5: Character Synopses

Tell the story again from each major character's side: about a page for the main cast, half a page for the rest. This is where subplots surface, because each character's version shows what they are doing while the protagonist is offstage.

**Where it lives:** a character's own storyline becomes an arc file: `story add arc '{Name}' --type character --character {id}` for an inner change, `--type subplot` for an outer thread. Put the synopsis in the arc's sections and a pointer to it in the character's `## Character Arc`. Keep offstage history in `## Backstory`.

## Step 6: Long Synopsis

Expand each paragraph of the Step 4 synopsis into roughly a page, weaving in the subplots from Step 5. Ingermanson's version is about four pages.

**Where it lives:** the arc files, with `## Rising Action` carrying the escalations in order and new plot points added to each arc's Plot Points table and to `plot/timeline.md`. Setups that need a later payoff go in `continuity/promises/` (`story add promise '{Setup}' --planted chapter-{NN}`) and open mysteries in `continuity/questions/` (`story add question '{Question}' --introduced chapter-{NN}`). `story synopsis . --pages 3` is the CLI's longest read-back; it has no four-page mode.

## Step 7: Character Charts

Fill out every major character in full: appearance, history, voice, relationships, what they want, and how they change. This is reference material for drafting, so write only what the page will use.

**Where it lives:** the remaining sections and frontmatter of each character file (`## Appearance`, `## Personality & Traits`, `## Voice & Speech Patterns`, `## Timeline`, `relationships`, `locations`, `voice-words`, `voice-avoid`, `ghost-wound`). Relationships are bidirectional: add the matching entry to the other character's file.

## Step 8: Scene List

Break the long synopsis into a list of scenes, one line each: POV character, what happens, and a rough length. Reorder and cut here, where it is cheap.

**Where it lives:** `story add chapter '{Title}' --number {N} --pov {id} --arc {arc-id}` for each chapter, then `story add scene '{Title}' --chapter chapter-{NN} --scene {M} --pov {id} --location {id} --arc {arc-id}` for each scene, with the one-line summary under the scene's `## Purpose`. Where the list already knows them, pass `--hook {hook}` to `story add chapter` for how the chapter ends and `--outcome {outcome}` to `story add scene` for whether the POV character gets what they want. Fill the `Chapter` column of each arc's Plot Points table and `plot/timeline.md` as scenes are placed. Run `story pacing .` to see the list's shape: runs of `yes` outcomes, missing sequels, length outliers.

## Step 9: Scene Descriptions

A few paragraphs per scene: what the POV character wants, what goes wrong, what changes, any dialogue beats already known. Treat this step as optional: skip it for writers who find that planning every scene in prose drains the draft.

**Where it lives:** a `## Scene Card` section in each scene file, using `scene-craft`'s `references/scene-cards.md` format, plus `characters`, `location`, `date`/`time`, and `state-changes` in the scene frontmatter.

## Step 10: First Draft

Write the book from the scene files. Hand off to the `chapter-writing` skill, one chapter at a time.

When drafting finds a better story than the design, change the design at the smallest step that holds the change (a scene, an arc section, the Step 2 paragraph) and let the larger artifacts follow, rather than drafting away from the plan.

## Maintenance

After every step from Step 2 on that creates or edits arcs, characters, chapters, scenes, promises, or questions, run `story reindex .`, `story wordcount . --write`, and `story check .`. In early steps `story check .` reports characters named in an arc before their file exists; they clear once Step 3 creates them.

## When to Ask the User

- Before Step 1, whether they want all ten steps or will stop partway (Step 4 and Step 8 are natural stopping points).
- When a character synopsis in Step 5 changes the main plot: show the change against the Step 2 paragraph and ask which version is the story.
- Before Step 9, whether they want scene descriptions at all.
