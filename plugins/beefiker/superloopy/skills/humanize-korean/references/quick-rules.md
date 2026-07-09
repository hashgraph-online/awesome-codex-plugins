# Humanize Korean Quick Rules

This compact rule set adapts Korean AI-tell categories from `epoko77-ai/im-not-ai` for Superloopy packaging. Use it as a checklist, not as permission to change facts.

## Superloopy Additions

- Protected spans outrank every rewrite rule.
- Register preservation outranks naturalness.
- A sentence may remain slightly formal if loosening it would change genre or authority.
- Do not remove all structure from operational, legal, release-note, or support-copy text.
- Treat repeated English terms differently from standard technical acronyms: `API`, `LLM`, `GPU`, `MCP`, `URL`, and version tags stay unchanged.
- Prefer Korean-native verbs over noun-heavy rewrites, but do not invent a subject to make a sentence active.

## Protected Spans

Keep these byte-for-byte unless the user explicitly asks otherwise:

- Proper nouns, product names, model names, organization names, acronyms, and code identifiers.
- Numbers, dates, versions, units, prices, URLs, email addresses, code spans, quoted spans, legal references, formulas, and statistical notation.

## S1: High-Signal AI Tells

| ID | Pattern | Repair |
| --- | --- | --- |
| A-2 | Repeated `~를 통해`, `~을 통해`, `통하여` | Prefer `~로`, `~해서`, or a direct verb when meaning stays intact. |
| A-3 | Empty `~에 있어(서)` framing | Use `~에서`, `~을 볼 때`, or delete the frame. |
| A-7 | Literal have/take/make phrasing such as `가지고 있다` | Restore a Korean verb or adjective. |
| A-8 | Double passive such as `되어진다`, `되어졌다` | Use active voice or a single passive. |
| C-5 | Emoji in reports, official copy, or columns | Remove unless the genre clearly needs them. |
| C-10 | Repeated colon-style headings | Shorten the heading or turn it into a sentence. |
| C-11 | Comma after Korean connective endings | Remove the comma unless punctuation is structurally needed. |
| D-1 | Formulaic pivots such as `결론적으로`, `따라서`, `요약하면`, `정리하면` | Keep at most one or replace with a concrete transition. |
| D-2 | Vague significance claims such as `시사하는 바가 크다`, `주목할 만하다` | Delete or state the actual consequence. |
| D-3 | Empty emphasis such as `본질적으로`, `핵심적으로` | Delete unless it carries a specific distinction. |
| D-4 | Hype words repeated without evidence | Replace with concrete facts already in the source. |
| D-5 | Personified abstract subjects | Prefer the real actor when the source gives one. |
| D-6 | Formulaic endings such as `~할 때다`, `~해야 한다` | Close with a plain claim when register allows. |
| H-1 | Sentence-initial connectors repeated across a text | Cut most of them; let sentence order do the work. |
| I-1 | `~인 것이다`, `~한 것이다` endings | Use direct declarative endings. |
| J-2 | Quotation marks used only for emphasis | Keep only true quotes or a few essential terms. |

## S2: Repeated Or Genre-Dependent Tells

| ID | Pattern | Repair |
| --- | --- | --- |
| A-1 | `~에 대해(서)` where a direct object works | Use `~를`, `~을`, or a natural postposition. |
| A-4 | Repeated `~라는 점에서` | Use `~라서`, `~라는 이유로`, or merge into the sentence. |
| A-5 | `~와 관련하여`, `관련된` padding | Use `~에`, `~의`, or a concrete relation. |
| A-6 | `~에 기반하여`, `~을 바탕으로` padding | Use `~로`, `~을 보고`, or a direct predicate. |
| A-9 | Passive `~에 의해` | Make the actor the subject when known. |
| A-10 | Repeated `~할 수 있다` | Use a direct claim when the source supports it. |
| A-11 | Repeated purpose clauses with `~을 위해` | Use `~려고` or a shorter modifier. |
| B-1 | Repeated Korean plus parenthesized English | Pair once, then use the Korean term or the established acronym. |
| C-7 | Mechanical three-part transitions | Fold transitions into the surrounding prose. |
| C-9 | `(1)`, `(2)`, `(3)` indexing in prose genres | Convert to paragraphs unless list structure is useful. |
| E-1 | Uniform sentence lengths | Mix one short sentence and one longer sentence per paragraph when natural. |
| E-2 | Four or more identical endings in a row | Vary endings without changing register. |
| F-4 | Heavy nominalization chains | Restore verbs or adjectives. |
| F-5 | Abstract `~적` noun chains | Shorten or rewrite into concrete nouns. |
| G-1 | Repeated `~것이다`, `~할 것이다` | Use present or confirmed forms where warranted. |
| G-2 | Repeated `~로 보인다`, `~인 듯하다` | State directly when the source is certain. |
| H-3 | Meta frames such as `이는`, `이 점에서` | Fold into the claim or delete. |
| I-2 | `X은 ~라는 점에 있다` | Use `X는 ~다`. |
| I-3 | `~다는 뜻이다`, `~다는 의미다` | Integrate the meaning into the sentence. |
| J-1 | Decorative Markdown emphasis in serious prose | Remove most decoration. |
| J-3 | Bullets in column/report prose | Keep bullets only when they improve scanning or are part of the source genre. |

## Rewrite Order

1. Freeze protected spans.
2. Remove S1 signature phrases.
3. Reduce translationese and passive constructions.
4. Adjust hedging only where certainty already exists.
5. Smooth repeated structure and sentence endings.
6. Remove visual decoration that makes the text feel generated.
