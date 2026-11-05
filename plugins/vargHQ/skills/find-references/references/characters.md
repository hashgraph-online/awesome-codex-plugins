# Character references

For non-human characters and mascots. Model sheets prove how a character is drawn, and motion clips prove how it moves.
They do not give you the design, and all of it is studio art: every reference here is `words`. Never feed it, and never
name a living artist or studio style in a prompt. Real people go through `people.md`.

## Read it

Fill the same identity card with different fields. `our proposal`, not validated.

| Field | What goes in |
|---|---|
| Silhouette | Reads as a black shape at thumbnail size |
| Shape language | Round, square or spiky. Name one. What each tends to say: `craft-evidence.md` in `character-passport` |
| Material and wear | What it is made of and how that wears |
| Body logic | What its joints can do |
| Scale | Next to a human |
| Signature movement | One movement, named with a Sakugabooru tag: `walk_cycle`, `fabric`, `creatures` |
| Want | What it wants |
| Never | What it never does |
| Mascots only | Works in one colour and at favicon size |

Collect 2 to 3 model sheets for layout, 3 unrelated designs for shape language and 1 motion clip. Mix sources. The
three-person rule becomes a three-design rule: a trait copied from one design is a copy, not a language.

## Search it

| Source | Exact route | What came back | Access | Verdict |
|---|---|---|---|---|
| [Character Design References](https://characterdesignreferences.com/) | Static pages, no site search tested | Model sheets and "art of" books. Its robots names ClaudeBot and GPTBot | `agent`, one-off lookups | Best for how studios lay out a sheet |
| [Sakugabooru](https://www.sakugabooru.com/tag.json?name=character_acting&limit=5) | `/tag.json?name=<tag>`, `/post.json?tags=<tags>&limit=N`. Metadata only, no clip downloads | `tested 2026-11-03`: `character_acting` 89,172, `creatures` 38,716, `fabric` 22,840, `walk_cycle` 6,124. `character_acting+animal` returned tagged clips | `agent`, targeted reads | Best for movement. Robots signal `use=reference`, `ai-train=no` and name ClaudeBot, so keep to targeted reads. A person watches the clips |
| [Are.na](https://api.are.na/v2/search/channels?q=mascot+character+design&per=100) | `mascot character design`, then the walk in `style-boards.md` | `tested 2026-11-03`: 5 channels, led by "☻ Design Characters" 182 blocks, 63 followers. `mascots` alone returned 504 | `agent`, unstable | Good for shape language |
| [ArtStation](https://www.artstation.com/) | A person browses | 403 with a plain User-Agent. Do not spoof it | `person` | Link only |
| "Art of" books | The Art of Pixar, The Art of Kung Fu Panda, The Art of The Lion King ([list](https://creativebloq.com/buying-guides/best-character-design-books)) | No open search API found | `person` | Look at them, then write words |
| [Pictoplasma](https://pictoplasma.com/), [Animation Resources](https://www.animationresources.org/) | Not tested | Home pages answer, search not tried | `person` | Try only if the rest run dry |
| Living Lines Library | Did not resolve | | `dead` | Skip |

Search Sakugabooru by the tag, not by what you want to feel. Tag names are exact: `tags=smear` returned 0 while `smears`
returned 62,126 (`tested 2026-11-03`). Read movement with `motion.md`.

## Sheets for generators

Recurring characters need locks, and those come after this step. `reported` from posts, not reproduced:

- Henry Daubrez: "Before generating a single frame, I locked character bibles, turnarounds, wardrobe details, prop
  references... Without them, identity drifts" ([post](https://x.com/henrydaubrez/status/2062212204406173744)).
- Monique Pryce: "my set always has front, quarter, profile, and full body"
  ([post](https://x.com/second_bassoon/status/2117703324321694077)).

These describe `feed` sheets of fictional or consenting subjects, which you make yourself. A studio model sheet teaches
you the layout and never goes in. Build the sheet with the `character-passport` skill. Mascot recipes:
`varg-character-design`.

## Code vs generated

- **Generated.** The reference must prove the card. The output is the card, then your own sheet as the `feed` reference.
- **Code-made.** The reference must prove the silhouette and the movement. The output is the card plus a movement read
  from `motion.md`. You draw the character, so never trace a sheet.

## Worked example

"A spark-plug mascot" for a tool-brand ad, `tested 2026-11-03`. Are.na `mascot character design` → "☻ Design Characters"
(182, 63). Sakugabooru `character_acting+animal` for personality in movement, tag `creatures` 38,716. Character Design
References for sheet layout. Output: the card, all `words`.

## Reject if

- The black-shape silhouette does not read at thumbnail size.
- A mascot fails in one colour or at favicon size.
- All your designs share one artist or studio. Your card would be a style copy.
- The prompt names a living artist or a studio style.
- The motion clip shows no single movement you can name.

Universal rejects: `never.md`.

## Judge it

Motion M1 to M6 in `judge.md` for movement (a draft, off by default), Never N1 to N5 for rejects. A person owns the
final call on character taste.
