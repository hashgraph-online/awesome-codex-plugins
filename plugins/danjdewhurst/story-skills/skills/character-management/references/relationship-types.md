# Relationship Types Reference

Use these types in character frontmatter `relationships[].type` field.

## Family

| Type | Description |
|------|-------------|
| parent | Parent of the other character |
| child | Child of the other character |
| sibling | Brother or sister |
| spouse | Married partner |
| partner | Unmarried romantic partner |
| grandparent | Grandparent of the other character |
| grandchild | Grandchild of the other character |
| uncle | Uncle of the other character |
| aunt | Aunt of the other character |
| nephew | Nephew of the other character |
| niece | Niece of the other character |
| cousin | Cousin |
| in-law | Related by marriage (specify in notes) |

## Social

| Type | Description |
|------|-------------|
| friend | Close friend |
| ally | Allied but not necessarily close |
| rival | Competitive relationship |
| enemy | Hostile opposition |
| adversary | Named personal opposition with direct stakes |
| mentor | Teacher/guide figure |
| student | Learner/protege |
| employer | Boss or authority figure |
| former-supervisor | Former boss or authority figure |
| former-subordinate | Once worked under the other character |
| subordinate | Works under the other character |
| colleague | Works alongside |

## Story Role

| Type | Description |
|------|-------------|
| protagonist | Main character in opposition or partnership (any backlink type) |
| antagonist | Primary opposition to this character (any backlink type) |
| love-interest | Romantic interest |
| foil | Character who contrasts/highlights traits |
| confidant | Character they confide in |

## Usage

The type set is open and extensible: the CLI does not enum-check `relationships[].type`, so any kebab-case value passes `story validate`. Prefer a type from this reference when one fits; when none does, coin a descriptive kebab-case type and use it consistently. `story links` checks the backlink type only for the inverse pairs and symmetric types below; any other type accepts any backlink type.

Relationships are bidirectional. When adding a relationship to one character, add the inverse to the other:

- If A has `type: parent` to B, then B has `type: child` to A
- If A has `type: mentor` to B, then B has `type: student` to A
- If A has `type: rival` to B, then B has `type: rival` to A (symmetric)

Inverse pairs:
- parent <-> child
- grandparent <-> grandchild
- uncle or aunt <-> nephew or niece (either gendered inverse is valid, e.g. uncle <-> niece)
- mentor <-> student
- employer <-> subordinate
- former-supervisor <-> former-subordinate

Symmetric types (same both ways):
- sibling, spouse, partner, in-law, friend, ally, rival, enemy, adversary, cousin, colleague, foil, confidant, love-interest

## Upgrading from before 0.10.0

This reference used to allow `former-supervisor` on both sides of a pair and `antagonist` as the backlink for `adversary`. `story links` warns on those pairings rather than failing, naming the fix:

```text
warning: characters/ilya.md relationship adversary to mara has backlink antagonist, a pairing from before story-skills 0.10.0; change the backlink to adversary [legacy-backlink-type]
```

Change the backlink on the named character to the expected type (`former-subordinate` for a former supervisor, `adversary` for an adversary), then rerun `story links`.
