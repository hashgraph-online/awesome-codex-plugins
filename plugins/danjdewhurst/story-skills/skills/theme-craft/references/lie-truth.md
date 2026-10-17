# Lie, Truth, Ghost Wound, and Arc Types

The planning machinery behind character arcs: the false belief that drives
the character, the truth that resolves it, the wound that planted the lie,
and which of the three canonical arc types the character follows.

## The lie and the truth

- **The lie** is the character's false belief about themselves, other people,
  or the world — e.g. "Trusting people gets you killed," "I am only valuable
  when I win," "Love is control." The lie generates:
  - **Flaw:** the behavior the lie produces (withdrawal, cruelty, control).
  - **Fear:** what the lie says will happen if they act differently.
  - **Want:** the external goal the character pursues *because* of the lie
    (the wrong thing they think will fix their life).
- **The truth** is the belief that replaces the lie — e.g. "Trust is a risk
  worth taking." The truth produces the character's **need**: the internal
  change the story actually demands.
- **The ghost wound** is the backstory event that planted the lie — the
  formative betrayal, loss, or failure. One specific scene, not a vague
  childhood. Record it concretely: who, what happened, what the character
  concluded.

## Arc types

The character template's "starting state → turning points → ending state"
field assumes a positive change arc. Three canonical types exist; record
which one each significant character follows, because the arc type dictates
what the turning points must contain.

**`change-positive`** — the character starts believing the lie and ends
believing the truth. Turning points are the moments the lie costs them, the
crisis where the lie fails completely, and the climax where they act on the
truth. This is the default; if unsure, use this.

**`change-negative`** — the character clings to the lie and it destroys them
(or leaves them diminished). Turning points: opportunities to choose the
truth, each refused; the lie's victories getting darker; the climax where
they double down on the lie and pay the full price. The negative arc still
needs the truth clearly visible — the reader must see the door the character
refuses to walk through.

**`flat`** — the character already holds the truth; the *world* changes
around them. Turning points are **tests of steadfastness**, not growth beats:
pressure to abandon the truth, temptations to adopt the lie, costs paid for
holding firm. The climax proves the truth by the character's refusal to
break, and the world (or the supporting cast) changes in response. Flat arcs
without escalating tests read as static — each test must cost more than the
last.

## Frontmatter fields

The character template (`character-management/references/character-template.md`)
carries these fields — fill them in for significant characters:

`arc-type` is `change-positive`, `change-negative`, or `flat`. Keep the
choice as the value only. An inline `#` comment is stored as part of the
scalar.

```yaml
arc-type: change-positive
lie: "{The false belief}"
truth: "{The belief that resolves it}"
ghost-wound: "{The specific backstory event that planted the lie}"
```

The protagonist must have all four fields. Supporting characters get them
when their arc intersects the theme; minor characters don't need them.

## Guidance for turning points

When drafting or revising a character's turning points, check them against
the arc type:

- `change-positive`: does each turning point make the lie more expensive?
  Does the climax require acting on the truth at real cost?
- `change-negative`: is the truth visible and reachable at each turning
  point? Does the character *choose* the lie each time (not merely fail to
  see the truth)?
- `flat`: is each turning point a genuine test — could the character
  plausibly break? Do the tests escalate? Does someone or something else
  change *because* they held firm?
