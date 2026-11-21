---
name: proxmox-writing-style
description: >-
  Unofficial skill for the Proxmox Technical Writing Style Guide. Use it to
  write, edit, or review Proxmox documentation: Proxmox VE, Proxmox Backup
  Server, and Proxmox Mail Gateway admin guides, wiki pages, how-to guides,
  procedures, release notes, and UI text. Also use it when the user asks for
  the Proxmox style, the Proxmox wiki style, or a style review of Proxmox
  text. It covers voice, mood, sentence length, procedures, headings,
  punctuation, product names, terms, abbreviations, and examples.
license: MIT
metadata:
  source_url: https://pve.proxmox.com/wiki/Technical_Writing_Style_Guide
  source_revision: "12596"
  source_last_edited: "2026-05-27 09:17"
  verified_on: "2026-08-27"
---

# Proxmox Writing Style

Use this skill for Proxmox technical documentation, how-to guides, release notes, procedures, and user-facing technical text.

For before and after rewrites of each rule, read [references/examples.md](references/examples.md).

When you review text, report each problem with the rule, the problem text, and a correct rewrite.

## Workflow

1. Identify whether the text describes a system or gives instructions.
2. Put the important information near the start of each sentence.
3. Use US English spelling.
4. Write short, clear sentences.
5. Use active voice.
6. Use simple words for non-native English readers.
7. Keep one term for one concept.

## Voice and Mood

For descriptions, use third-person indicative mood.

For instructions, use second-person imperative mood.

Avoid first-person singular. Avoid first-person plural unless `we recommend` makes a sentence much clearer.

Do not use `should`, `could`, or `might` in instructions. Use an imperative verb, `must`, or `can`.

Do not use `one` as a pronoun.

## Sentences

Aim for an average of 15 to 20 words per sentence.

Vary sentence length and the word that starts each sentence.

Use a connective word, such as `for example`, `however`, `therefore`, or `furthermore`, to show the relationship between two ideas.

Turn three or more sequential items in running text into a list.

## Procedures

Give each procedure a descriptive heading.

Use a numbered list for ordered tasks.

Use a bullet list for one-step procedures or unordered options.

Make each step one clear action. Use parallel structure across the steps in one procedure.

Include `Enter` in the same step that needs it.

State the purpose before the action when that lets readers skip irrelevant steps.

Use lowercase letters for substeps. Use lowercase Roman numerals for sub-substeps.

## Headings

Use title-style capitalization for level 1 and level 2 headings.

Use sentence-style capitalization for lower heading levels.

In title-style headings, lowercase `a`, `an`, `the`, short prepositions, and short conjunctions unless they start or end the heading. Capitalize a proper noun regardless of its position.

## Punctuation and Lists

Use the Oxford comma in lists of three or more items.

Use a comma before a coordinating conjunction that joins two independent clauses.

Use a comma after sequence words, introductory phrases, and dependent clauses at sentence start.

Use a comma between two adjectives that each modify the noun on their own, such as `a slow, expensive process`.

Do not use a comma between the two verbs of a compound predicate, such as `Open the file and edit the setting`.

Do not use a comma in place of a semicolon between two independent clauses.

Use a slash only for a true combination, such as `TCP/IP`.

Use hyphens for compound modifiers before nouns, such as `command-line tool`.

Use an em dash without spaces around it.

Keep punctuation consistent within each list: use full sentences with end punctuation throughout, or phrases without end punctuation throughout, not a mix.

## Terms

Use the exact company, product, and technology names:

- `Proxmox VE`
- `Proxmox Virtual Environment`
- `Proxmox Mail Gateway`
- `Proxmox Backup Server`
- `OpenVZ`
- `CentOS`
- `VMware`
- `Ceph`
- `HTML`
- `the web`
- `web interface`
- `web UI`

Do not use `Proxmox` alone as a product name.

Do not abbreviate `Proxmox VE`, `Proxmox Mail Gateway`, or `Proxmox Backup Server` as `PVE`, `PMG`, or `PBS` in prose.

Use `USB flash drive`, not `USB stick` or `thumb drive`.

Use `motherboard`, not `mainboard`.

Use `container` instead of `CT`, unless the text names a UI item.

Use `VM` only when the text names a UI item or the term is already introduced.

Use `guest` or `virtual guest` for text that covers VMs and containers together.

Treat `data` as singular for consistency with existing Proxmox documentation.

## Abbreviations

Avoid lazy abbreviations.

Use `about` instead of `approx.`.

Use `for example` instead of `e.g.`.

Use `that is` instead of `i.e.`.

Avoid `etc.` when the previous words already imply examples.

Spell out an acronym at first use, followed by the acronym in parentheses.

Do not use an acronym if it appears only once.

Common acronyms can stay short: `USB`, `HTML`, `URL`, and `FAQ`.

## Style

Use contractions, such as `it's`, `you're`, and `don't`. Avoid a contraction that a reader could misread as a different word.

Replace jargon, slang, and idioms with plain, familiar words.

Use `they`, `them`, or `their` for a person of unspecified gender, or rewrite the sentence to avoid a pronoun.

Choose `a` or `an` by the sound that follows, not by the letter, such as `a university` and `an MGC`.

## Examples

Use only examples that are clear, correct, and tested.

Omit an example you cannot test.
