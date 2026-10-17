# Translation

Use this reference when the user asks to translate writing into another language
and quality depends on meaning, source-language writing style, tone, voice,
terminology, formatting, or cultural fit.

## Goal

Translate the artifact while preserving intended meaning and carrying the source
language's writing style into the target language. Preserve voice, rhythm,
sentence texture, imagery, register, pacing, and emotional effect where the
target language allows. Do not flatten the source style into generic polished
prose.

## Flow

1. Frame source language, target language, locale, audience, purpose, and format.
2. Ask blocking questions only if language, locale, fidelity level, or glossary is missing.
3. Identify source-style targets: voice, rhythm, imagery, register, sentence texture, pacing, and emotional effect.
4. Identify fixed terms, names, commands, file paths, code, citations, and formatting.
5. Build a small glossary for repeated or high-risk terms.
6. Translate in the requested mode.
7. Review for meaning fidelity.
8. Review for source-style preservation and target-language naturalness.
9. Propose targeted changes when quality matters.
10. Revise only accepted or adjusted changes.

## Translation Modes

Use one mode explicitly:

```text
literal: preserve source structure closely, even when target-language flow is less natural
natural: prioritize fluent target-language reading while preserving source voice and effect
localized: adapt idioms, examples, and cultural framing without erasing source style
parallel: show source and translation side by side
review-only: critique an existing translation without rewriting
```

Default to `natural` unless the user asks for literal translation or legal,
technical, academic, or citation-sensitive fidelity.

## Question Gate

Ask only questions that change the translation:

```text
Target language and locale?
Literal, natural, localized, or parallel mode?
Should names, titles, terms, commands, or formatting stay unchanged?
Should sentence rhythm, imagery, register, or voice stay close to the source?
Is there a glossary or style reference?
Who is the target reader?
```

If the user already provided enough context, state assumptions and translate.

## Output Shape

Use this shape even for short translations:

```text
Frame
- Source language:
- Target language and locale:
- Mode:
- Style targets:

Translation
[translated artifact, preserving source markdown formatting here]

Review
- Fidelity:
- Source style:
- Fixed tokens / terminology:

Revision Path
- Proposed changes: [targeted options or "none until user review"]
- Decision needed: apply | reject | adjust

Learning Status
No reusable preference learned; no reviewed decisions were collected.
```

Preserve the source artifact's markdown inside `Translation`. Do not drop
`Frame` or `Review` merely because the source was plain text.

## Preserve Source Writing Style

Before translating, identify the source's style targets:

```text
voice
tone
sentence rhythm
sentence length and texture
imagery and metaphor density
register and diction
narrative distance or point of view
pacing
emotional temperature
silence, ambiguity, or directness
```

Preserve these as target-language effects, not as mechanical word order. If a
literal structure would sound broken in the target language, preserve the effect
with a natural target-language structure and note the choice when it matters.

## Preserve Exactly Unless Told Otherwise

Preserve these by default:

```text
code blocks
inline code
file paths
CLI commands
URLs
IDs
API names
proper nouns
citations
tables and headings
markdown structure
```

For fiction, preserve character names unless the user asks for localization.
For technical writing, preserve product names and protocol terms unless a
standard translated term exists.

## Glossary Format

```text
Glossary
- Source term:
  Translation:
  Rule:
  Confidence:
```

Use glossary entries for repeated terms, ambiguous terms, domain terms, and
names with intentional translation choices.

## Translation Output Shape

For short tasks:

```text
Translation
[translated text]

Notes
- [only important choices or ambiguities]
```

For substantial tasks:

```text
Frame
- Source language:
- Target language:
- Mode:
- Audience:
- Constraints:

Source Style Targets
- [voice, rhythm, imagery, register, pacing, emotional effect]

Glossary
- [term choices]

Translation
[translated text]

Review
- Fidelity:
- Source style:
- Target-language naturalness:
- Terminology:
- Formatting:

Proposed Changes
- [targeted changes if revision is needed]
```

## Untranslatable Concepts

Some source elements have no direct equivalent in the target language. When you
encounter one, do not silently flatten it. Choose one strategy and note it:

```text
Strategy options:
- Borrow: keep the source word, italicised, with a brief gloss on first use
- Approximate: find the closest target-language expression and note the loss
- Expand: add a short phrase that carries the cultural weight
- Flag: mark as [untranslatable — awaiting user decision]
```

Common categories:
- Cultural time markers (e.g. a Chinese watch-name for a time of night)
- Untranslatable emotional states (e.g. Portuguese *saudade*, Japanese *mono no aware*)
- Idioms that are opaque in the target language (e.g. "beat a dead horse")
- Concepts of face, honour, or social hierarchy that carry different weight across cultures
- Genre-specific registers that have no equivalent (e.g. classical literary Chinese in modern English)

For idioms: translate the meaning, not the image, unless the user asks to keep
the source idiom for a specific effect. Note the choice.

## Style Preservation Example

Source (Chinese, literary): short sentences, restrained emotion, image-first, no stated feeling.

Flattened target (avoid): "The rain stopped before dawn. She felt relieved."
— states the feeling directly, loses the source restraint.

Preserved target: "The rain stopped before dawn. She did not move."
— preserves the restraint by showing action, not naming emotion.

When choosing between fluency and source style, prefer source style and note
the tension. The user can always choose to smooth it.

## Review Rubric

Check:

```text
meaning fidelity
source style preservation
tone preservation
voice preservation
rhythm and pacing
imagery preservation
register preservation
terminology consistency
idiom handling
reader naturalness
format preservation
omissions or additions
ambiguity handling
```

## Interaction With Style Distillation

If the user provides style references or asks to preserve a known voice, read
`references/style-distillation.md` first, create or load a style pack, then use
that pack as a translation constraint.

If the user asks to translate and improve, translate first, then use the main
critique and revision loop.

## Common Mistakes

- Translating code, commands, file paths, or IDs.
- Losing the source writing style by making everything generic and polished.
- Preserving literal word order while losing the original voice, rhythm, or emotional effect.
- Over-localizing when the user asked for faithful translation.
- Keeping source-language idioms that sound unnatural in the target language.
- Failing to flag ambiguous terms.
- Treating one translation choice as a permanent preference without user review.
