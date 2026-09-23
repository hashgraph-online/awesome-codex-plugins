---
name: book-screenplay
description: "Screenplay craft reference: format, three-act and sequence structure, scene construction, dialogue subtext, A/B/C story weaving, series bibles, and screenplay-specific AI tells. Read by all agents on film, TV, and web-series projects."
---

# Screenplay

A screenplay is a document for collaborators, read by people who read hundreds. It must be fast, visual, and impossible to put down on page 10. Novelistic interiority does not exist here; everything the audience learns, they see or hear.

## Structure

- **Three acts by page**: feature 90-120 pages; Act 1 to ~25, Act 2 to ~85, Act 3 to end. One page ≈ one minute.
- **Eight sequences** (two per act in 1 and 3, four in 2), each 12-15 pages with its own mini-arc: status quo → disruption → strategy → complication → crisis → decision → new status quo. Sequences prevent the second-act sag.
- **Beat placement**: inciting incident by page 10-12; first-act turn ~25; midpoint ~55 (a reversal, not an event); low point ~75; third-act turn ~85.
- **TV**: cold open, act breaks at commercial points (4-5 acts for network, 3 for streaming), A/B/C stories per episode, season arc bible with per-episode outlines. Pilot must establish the engine (what generates episodes forever).
- **Web series**: 8-15 pages per episode, hook in the first 30 seconds, cliffhanger every episode.
- **Short**: 5-30 pages, one turn, no subplot.

## Scene

- **Slug line**: `INT./EXT. LOCATION - DAY/NIGHT`. Location names consistent across the script (bible).
- **Every scene**: someone wants something, something is in the way, the scene ends with the situation changed. Outcome: yes-but, no-and, no-but.
- **Enter late, leave early.** Cut the arrival, the greeting, the goodbye.
- **Action lines**: present tense, only what can be seen or heard, 3-4 lines max per paragraph, white space is pacing. No "we see." No camera directions unless writer-director.
- **Character introduction**: NAME in caps at first appearance, age, one telling detail. Not a paragraph of backstory.

## Dialogue

- Subtext over statement. Characters talk around the thing.
- Distinct voice per character: rhythm, vocabulary, what they never say. Cover the names; the reader should still know who is speaking.
- Monologues ≤ 5 lines unless the script earns a set piece.
- Parentheticals rarely; the actor decides.
- V.O. and O.S. sparingly and consistently.
- Korean: 존댓말/반말 relationships fixed per pair in the bible; a shift is a story event. 지문 in 현재형.

## A/B/C stories

A-story (main plot, ~70%), B-story (relationship or theme, ~25%), C-story (runner, ~5%). B carries the theme; A carries the plot; they collide at the midpoint and the climax. Alternate A and B every 2-3 scenes; do not run five A scenes in a row.

## Format

Industry-standard layout (Courier 12, 1.5" left margin, dialogue block width). Drafts are markdown with a strict convention so `book-publish` can export to Fountain and PDF:

```
INT. KITCHEN - NIGHT

Action line.

CHARACTER
(parenthetical)
Dialogue.
```

Transitions only between sequences. No bold, no italics except in the title page.

## Screenplay-specific tells

- Action lines that describe emotion ("she feels devastated").
- Characters stating their motivation or the theme.
- Every scene starting with the character entering and ending with them leaving.
- Uniform scene length.
- Dialogue that answers the previous line directly.
- On-the-nose exposition disguised as argument ("As you know, we've been married ten years").
- Montages to skip the hard scene.
- The final scene that mirrors the first scene with one word changed.

## Bible

Per character: verbal signature, want/need, 존댓말 map. Per location: what it looks like once, then consistent. Props and costume that carry meaning are tracked. Time of day and day count across the script.

## Validation (architect scoring for screenplay)

Beat placement within tolerance; each sequence has a mini-arc; A/B collide at midpoint and climax; every scene has a change; page count in range for the format; no scene without a slug; character introductions correct; dialogue distinguishable by voice.

## Visuals

Scripts carry no interior images. Pitch and series-bible packages do: cover/key art, character reference sheets, location boards, a tone board of 6-9 images, and a season-arc diagram (figure-engineer). All through `/book-visuals`; the art bible for a pitch deck is the show's visual identity.
