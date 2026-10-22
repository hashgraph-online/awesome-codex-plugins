# Titles and Comparable Books

Title principles (comps, hook phrasing, title as promise) are in
`../../story-init/references/title-logline.md`. This file is the
brainstorming procedure and the premise-stage comp check.

## Brainstorm across families

Generate 3-4 candidates in each family, then cut. Mixing families stops
the list collapsing into twenty variants of one idea.

| Family | Pattern | Example shape |
|--------|---------|---------------|
| Image | A concrete object or place from the story | *The Drowned Bell* |
| Phrase from the world | A saying, rule, or term only this story has | *Keep the Light Lit* |
| Character | A name, role, or epithet | *The Last Keeper* |
| Contradiction | Two words that should not sit together | *A Quiet Wreck* |
| Question or promise | What the reader will want answered | *Who Rows Out* |
| Genre signal | The shelf's usual register for this genre | Match the comps' weight and length |

## Cut to a shortlist of five

For each candidate, check:

1. **Promise:** does it promise the tone and subject of the logline?
2. **Shelf:** does it sit beside the comps without sounding like one of
   them?
3. **Sayable:** can someone say it to a bookseller after hearing it once?
   Read it aloud.
4. **Searchable:** a search for it should not bury the book under a
   famous title, film, or product. If web search is available, check and
   report what you found; otherwise tell the user to check.
5. **Not a spoiler:** it does not give away the ending or the twist.

Present the five with one line each on what they promise. The user picks
or asks for another round.

## Check names against the project

Once the project exists, run candidate titles' key words, and every new
character, place, or term name, through the collision check:

```shell
story names 'Maren' 'Bellrock' --path .
```

Pass each word separately when a title or name has more than one
(`"Bell Tower" Bell Tower`): multi-word names are only checked for exact
clashes.

- **Exact clash** (error, exit 1): the name already belongs to a
  character, alias, location, faction, artifact, system, or glossary
  term, or its given name (the first word that is not a title or article
  such as `The`, `Lord`, or `Captain`) equals a character's given name,
  so *Lady Sera* clashes with *Sera Voss*. Pick another, or confirm the
  reuse is deliberate and rename the existing entity with
  `story rename <kind> <id> '<New Name>' --prose`, so its chapter text
  follows too: run it with `--dry-run` first, show the user the
  replacements, and run it for real only once they approve. After a rename, run `story reindex .`,
  `story wordcount . --write`, and `story check .`.
- **Look-alike warning:** the same first four letters (*Maren* /
  *Marenna*), or the same initial and one letter apart (two for words of
  five letters or more: *Maren* / *Marek*). Readers confuse these.
- **Shared initial with a major character:** fine in moderation; a cast
  where three leads start with M is hard to follow.

## Premise-stage comp check

Comparable books at this stage are a sanity check, not a pitch (the
submission comps list is built later in the `submission` skill).

Ask the user for two or three recent books the idea sits beside, or
suggest candidates only when web search can verify them. For each:

- **Same shelf?** Category (adult, YA, MG, children's), genre, and form.
  A comp on a different shelf means one of them is the wrong book to
  compare.
- **What is the same?** Name it concretely: setting, relationship, voice,
  structure.
- **What is different?** If nothing substantial, the premise needs a new
  angle; return to `what-if-generation.md` and apply "invert it" or "give
  it to the wrong person" to the part that overlaps.
- **Length?** The comps' length is a check on `form` and `target-words`.

Rules:

- Never invent a title, author, year, prize, or sales figure. Unverified
  comps are marked unverified in the notes.
- A premise that resembles an existing book is not a failure; most do.
  It needs one clear difference a reader would notice on the jacket.
