# Chapter Template

Use this template when creating a new chapter file at `chapters/chapter-{NN}.md`.

```yaml
---
title: "{Chapter Title}"
number: {N}
pov: {character-kebab}
locations:
  - {location-kebab}
characters:
  - {character-kebab}
mentions:
  - {referenced-character-kebab}
arcs-advanced:
  - {arc-kebab}
status: {outline|draft|revised|final|complete}
date: {YYYY-MM-DD}
time: "{HH:MM}"
hook: {cliffhanger|question|revelation|reversal|decision|emotional|resolution}
word-count: {N}
---
```

`date` and `time` are the chapter's place on the story clock, in the same formats as scene records (see `scene-template.md`); set them when the chapter has no scene records, since `story timeline` and the clock checks in `story continuity` skip undated chapters and scenes.

`hook` is optional but expected once a chapter is drafted: it records how the chapter ends. `story pacing` warns about drafted chapters with no `hook` and about three or more consecutive chapters ending on `resolution`.

`characters` lists characters present in the chapter's scenes. `mentions` is optional and lists characters who are only referenced, remembered, recorded, or seen in flashback - including deceased characters, so `story continuity` does not flag them as posthumous appearances.

## Outline

*Beat-by-beat outline approved before writing:*

1. {Beat 1 - what happens, what it accomplishes}
2. {Beat 2}
3. {Beat 3}
...

**Arc beats advanced:** {Which plot points this chapter hits}
**Foreshadowing planted:** {Any setups placed}
**Foreshadowing paid off:** {Any earlier setups resolved}

---

## Chapter Text

{Full prose goes here}
