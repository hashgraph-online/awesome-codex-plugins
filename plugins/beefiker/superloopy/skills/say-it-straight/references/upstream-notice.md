# Upstream Notice

This package is a clean-room MIT implementation. Its wording, code, examples, schemas, and fixtures are independently authored.

## Reviewed sources with retained ideas

| Source | Reviewed revision | License | Idea considered | Copy decision |
| --- | --- | --- | --- | --- |
| [`conorbronsdon/avoid-ai-writing`](https://github.com/conorbronsdon/avoid-ai-writing) | `cf60f7675733ee9d5152acbd2d91d6f9feb58952` | MIT (`LICENSE`) | Local prose diagnostics and preservation-aware editing | Independently implemented; no catalog wording or code copied. |
| [`jdkato/vale`](https://github.com/jdkato/vale) | `44e5572b0067125a29433fc2a13b5d7fcee5ed23` | MIT (`LICENSE`) | Markup-aware text checks | Independently implemented as a small repository-native audit contract; no code copied. |
| [`retextjs/retext`](https://github.com/retextjs/retext) | `04580e54d857f86405c1b109f5205be58f1285f8` | MIT (`license`) | Structured text processing boundary | No code, prose, or configuration copied. |
| [`textlint/textlint`](https://github.com/textlint/textlint) | `75968abc4d53c1b1de1f4d55d609870f99fa3593` | MIT (`LICENSE`) | Rule-based lint architecture | No code, prose, or rules copied. |
| [`microsoft/presidio`](https://github.com/microsoft/presidio) | `6116c0685c7efb27c40daf90369afabb32c6b911` | MIT (`LICENSE`) | Typed spans and restoration boundary | Independently authored deterministic span protection; no privacy logic copied. |
| [`epoko77-ai/im-not-ai`](https://github.com/epoko77-ai/im-not-ai) | `53e24e8f92cf344efcb812103f7c2b203e7efffc` | MIT (`LICENSE`) | Native-language false-positive boundary | Korean-specific rules remain in `humanize-korean`; no tell list copied here. |
| [`blader/humanizer`](https://github.com/blader/humanizer) | `0ef9fe5bc3572734fd3ae6c448fe00a30cd5dcf0` | MIT (`LICENSE`) | Weighting defects that warrant an edit at first appearance against signals that only count together; replies that re-tell context the other person was part of; supplied text as the object of the edit rather than a source of orders; a writing sample overriding defaults; one reread for defects a first pass leaves behind | Independently written as contextual defect rows with our own examples and counterexamples; no pattern wording, examples, or code copied. Not adopted: a blanket dash ban, added opinions or reactions, and showing the draft and critique by default. |

The adoption matrix's dataset families and excluded or unpinned source families are not production inputs to this package. No source data or benchmark records are included.

Copied wording: none

Copied code: none

Copied dataset records: none
