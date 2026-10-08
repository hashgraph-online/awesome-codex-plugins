# Naming Languages

Names carry a culture's sound. A few rules per culture make names feel
related, keep cultures distinct from each other, and prevent accidental
look-alikes that confuse readers.

## Phonology sketch

For each culture or language, write a short sketch in a system file
(`story add system 'Vellish tongue' --type social`) or the culture section
of a location or faction:

- **Sounds used:** consonants and vowels the language favours
  (`k, t, r, s, v, l; a, e, o`), and sounds it never uses (`no th, no w`)
- **Syllable shape:** `CV`, `CVC`, clusters allowed or not (`str-` yes,
  final `-ng` no)
- **Stress:** first syllable, penultimate, or last
- **Common endings:** `-ar`, `-ek`, `-issa` and what they mark (place,
  person, gender, rank)
- **Spelling conventions:** how sounds are written (`k` never `c`),
  apostrophes and accents (use sparingly; each one slows the reader)

Keep two cultures apart by changing at least two of: sound set, syllable
shape, and endings.

## Naming rules

Record how people and places are named in each culture:

- Order of given name, family name, patronymic, clan, or title
- Names that change at life events (adulthood, marriage, office)
- Place names built from features (`-ford`, `-holm`, `Kel-` for hill)
- Words that are taboo or reserved (the dead, gods, royalty)

Build a short list of roots (hill, river, iron, grey, old) and make place
names from them, so a reader who notices `Kelmar` and `Kelvoss` feels the
pattern.

## Pronunciation

Give invented names a `pronunciation` field on characters, locations,
systems, factions, artifacts, and glossary terms:

```yaml
pronunciation: "SEER-sha"
```

Use plain respelling with the stressed syllable in capitals, not IPA,
unless the user asks for IPA. `story build --format narration` collects
every `pronunciation` into a guide table for audiobook narrators (see the
`adaptation` skill).

## Collision check before naming

Before committing to a new name, check it against every existing name:

```shell
story names 'Mira' 'Kelvos' 'Oda'
```

`story names` compares candidates with character names and aliases,
locations, factions, artifacts, systems, and glossary terms and aliases. A
candidate's given name (the first word that is not a title or article
such as `The`, `Lord`, or `Captain`) is compared with each character's
given name; everything else is compared as a whole name. An exact match
with either is a clash: an error (exit 1). It warns about look-alikes
(the same first four letters, or the same initial within an edit distance
of 1, or 2 when both words have five letters or more) and about given
names sharing an initial with a major character. Multi-word names such as
`Ashen Citadel` are only checked for exact clashes, so pass a distinctive
word on its own (`story names 'Ashen Reach' Ashen`) to catch look-alikes. Readers skim names
by shape: `Mara` and `Mira`, or `Kelvar` and `Kelvoss`, blur together.
Change the initial or the length unless the resemblance is deliberate
(siblings, a namesake), and say so in the file.

`story prose .` also warns about similar character first names.

When renaming an existing entity, preview
`story rename <kind> <id> '<New Name>' --prose --dry-run`, show the user
the replacements, and run it without `--dry-run` only once they approve,
so the chapter text follows as well as the references. Then run
`story reindex .`, `story wordcount . --write`, and `story check .`.
