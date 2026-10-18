# Character Template

Use this template when creating a new character file at `characters/{character-name-kebab}.md`.

```yaml
---
name: "{Full Name}"
role: {protagonist|antagonist|supporting|minor|narrator|deuteragonist}
status: {alive|deceased|unknown|missing|cut}
# died-in: {chapter-NN}  (deceased characters only)
aliases:
  - "{Alias 1}"
pronunciation: "{optional, e.g. SEER-sha}"
voice-words:
  - "{word or phrase they reach for}"
voice-avoid:
  - "{word they would never say}"
relationships:
  - character: {other-character-kebab}
    type: {relationship-type}
locations:
  - {location-kebab}
tags:
  - {tag-1}
  - {tag-2}
arc: {character-arc-theme}
arc-type: {change-positive|change-negative|flat}
lie: "{The false belief the character clings to}"
truth: "{The belief that would set them free}"
ghost-wound: "{The past wound that made the lie feel true}"
---
```

`pronunciation`, `voice-words`, and `voice-avoid` are optional. `pronunciation` feeds the narrator's guide in `story build --format narration`; the voice lists are checked by `story voices`. `died-in` is optional and applies only to the deceased: the template comments it out, so uncomment it and set a chapter id for a death, and leave it out for a living character. The `lie`, `truth`, `ghost-wound`, and `arc-type` fields belong to the `theme-craft` skill, which sets them. Set `died-in` (with `status: deceased`) when a character dies on the page so `story continuity` can flag appearances in later chapters; leave it out for characters who died before the story begins, and keep them in `mentions` only, since `story continuity` warns when one is listed in a chapter or scene cast. Posthumous appearances in flashbacks, memories, or recordings belong in chapter/scene `mentions`, not `characters`. `status: cut` keeps a removed character's file. `story reindex` still lists that file.

## Appearance

Physical description: build, height, distinguishing features, typical clothing, how they carry themselves.

## Personality & Traits

Core personality traits, temperament, habits, quirks. What makes them memorable in a scene.

## Backstory

Key events that shaped who they are. Only include what's relevant to the story.

## Motivations & Goals

What drives them. What they want (external goal) and what they need (internal goal). How these conflict.

## Location References

Important places tied to this character. Keep this list in sync with `notable-characters` in location files.

## Voice & Speech Patterns

How they talk: vocabulary level, sentence length, verbal tics, dialect, tone. Include 2-3 example lines of dialogue that capture their voice.

Example:
> "I didn't come here to make friends. I came here because someone has to clean up this mess."

## Character Arc

- **Starting state:** Where they begin emotionally/psychologically
- **Key turning points:** What changes them
- **Ending state:** Where they end up (or projected end)

Arc-type guidance (set `arc-type` in frontmatter; the lie/truth framing follows the widely taught Weiland school of character arcs):

- **Change-positive:** The classic arc. The character moves from lie to truth — each turning point cracks the lie a little more until the climax forces the choice between the old belief and the new one. The `ghost-wound` is the past event that made the lie feel true; reference it whenever the lie resurfaces.
- **Change-negative:** The tragic arc. The character clings to the lie and doubles down at each turning point. Track the spiral: each refusal of the truth costs more than the last, until the lie wins and the ending is worse than the beginning.
- **Flat (steadfast):** The character already holds the truth and does not need to change. Do not give them growth beats — write tests-of-steadfastness instead: moments where holding the truth costs them something, and they hold it anyway. Their arc is measured by how they change the world around them, not by how they change.

## Antagonist Design

An antagonist file uses this same template — set `role: antagonist` and give them the same depth as the protagonist. A worthy opponent:

- **Believes they are right.** The antagonist acts from their own logic, values, and wound — not from a desire to be evil. If you cannot write their case for them, they are a cardboard villain.
- **Is stronger in some dimension.** Resources, skill, knowledge, position, conviction — the protagonist must grow or outthink them to win. An opponent weaker than the hero generates no tension.
- **Argues the counter-premise.** The antagonist embodies the story's opposing value (see the `premise:` / `counter-premise:` fields in `story.md`). Their arc is the dark mirror of the protagonist's.
- **Could carry the story.** Draft their plan as if they were the protagonist of their own plot: goal, plan, escalations, what the protagonist's interference costs them. If their opposition collapses without the hero's involvement, it is passive — rewrite it.

When the true antagonist is a system, culture, or institution, personify it: give the force a face — a specific person who embodies and enforces it. The reader argues with a person, not an abstraction.

## Timeline

Key life events in chronological order:

| When | Event | Relevance |
|------|-------|-----------|
| | | |
