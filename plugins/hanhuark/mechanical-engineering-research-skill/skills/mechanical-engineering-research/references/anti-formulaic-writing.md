# Anti-Formulaic Technical Writing

Use this reference while drafting or revising an abstract, manuscript section, proposal narrative, review, or response to reviewers. These are editorial-quality safeguards, not a way to infer whether a human or AI wrote a document.

## Abstracts

Write the abstract as the paper's high-level story:

1. the important problem or application;
2. the knowledge or capability gap;
3. the approach and the main qualitative finding; and
4. the scientific or engineering implication.

Use quantitative results selectively. Include one or two anchor values when they establish the scale, comparison, or significance of the main finding. Do not turn the abstract into a compressed results table by listing operating conditions, multiple metrics, and several percentage changes. Put secondary numerical detail in the results section.

## Formulaic Language Pass

Read the draft for constructions that make adjacent sentences sound templated or overproduced.

- Use **conversely** only for a real logical opposition to the immediately preceding claim. Ordinary sequencing, a different condition, or a second observation usually needs no transition or a simpler one such as `by contrast`, `in contrast`, or `under these conditions`.
- Use **establish**, **establishes**, and **established** only when the evidence genuinely demonstrates a defined result. Replace vague phrases such as `establishes a relationship` with the actual supported finding, for example `shows that increasing cavity density delayed bubble coalescence in the tested range`.
- Prefer specific physical verbs such as `measured`, `observed`, `showed`, `indicated`, `quantified`, `predicted`, `reduced`, or `increased` when they more accurately state the evidence.
- Vary sentence openings and transitions. Do not make every paragraph follow claim, contrast word, and conclusion as a fixed pattern.

## Term Legitimacy

Do not introduce a phrase into technical prose merely because it is grammatically convenient. Before retaining an unfamiliar label, compound, or modifier, ask whether an informed reader in the target field would recognize it, whether it is needed for the argument, and whether it has been defined or supported by a source when appropriate.

- Flag unexplained labels assembled from generic words, especially dense compound modifiers and convenient constructions such as `-aware`, `-driven`, `-enabled`, `-centric`, or `-oriented`. They are not automatically wrong; they need a clear, field-appropriate meaning.
- Prefer the ordinary technical noun and a direct verb. Replace an opaque label with the physical quantity, method, mechanism, or decision it denotes.
- Do not flag established field terminology, standard instrument/model names, accepted mathematical language, or a necessary newly defined construct simply because it is unfamiliar to the auditor.
- When a new term is genuinely useful, define it once, use it consistently, and confirm that it clarifies rather than disguises the physical or methodological meaning.

## Vague And Repeated Terms

Audit repeated general-purpose terms such as forms of **enable**, forms of **establish**, **unusually**, and **together**. These words are not banned. Review them when they recur or when they carry the main technical claim without naming the mechanism, comparison, or result.

- Replace `enables improved cooling` with the actual capability or causal path, for example `increases the wetted area available for evaporation` when that is what the evidence supports.
- Replace `establishes the effect` with the measured, derived, or compared finding.
- Give `unusually` a comparator, regime, or quantitative basis; otherwise remove it.
- Replace vague uses of `together` with the relationship between the named observations, methods, or mechanisms. `The optical and acoustic signals jointly identified the onset of dryout` is clearer than `Together, the results showed ...`.

Repeated use is a prompt for editorial review, not a zero-tolerance rule. A precise term may remain when it is the most accurate wording.

## Reader Focus And Modifier Load

Technical writing should help an informed reader identify the subject, action, and point of a sentence on the first reading. Formal completeness is not a substitute for comprehension. A sentence or title can be grammatically correct while burying its central idea under a catalog of attributes, adjacent labels, and qualifications.

- State the main technical object and claim first. Retain a modifier only when it distinguishes the system, regime, evidence, or mechanism in a way the argument needs.
- Do not make a title a catalog of related activities or tools. Select the unifying research object and the main contribution; place secondary scope in the abstract, keywords, or opening paragraph.
- Split a modifier-heavy sentence when its qualifications answer different questions. Give the reader the main finding first, then state the operating regime, diagnostic basis, limitation, or exception in a following clause or sentence.
- Give the main clause most of the sentence's value. A long list of attributes, inputs, or caveats must materially change the reader's interpretation; do not retain it merely because it makes the sentence sound more complete.
- Prefer ordinary field-recognized nouns to a string of adjectives. For example, replace a label such as `physics-grounded, evidence-bounded, stage-resolved interpretation` with the specific measurement, model, or conclusion it denotes when that is clearer.
- Do not remove qualifiers that materially change scientific meaning. Conditions, uncertainty, validity limits, and evidence boundaries remain necessary; the goal is to attach them where the reader can see what they qualify.

During revision, ask: can a domain colleague state the subject and practical or scientific point after one reading? If not, revise the structure before adding more precision.

## Hyphens And Dashes

Use hyphen-minus (`-`) for standard compound modifiers only where grammar requires them, especially before a noun: `high-speed imaging`, `two-phase flow`, and `current-density dependence`. Avoid inventing or stacking compounds that obscure the underlying nouns.

- Write ordinary noun phrases as `flow boiling`, `vapor film`, `heat transfer`, and `phase change` unless a target journal's style guide specifies otherwise.
- Recast densely hyphenated modifiers into a short clause when that is clearer. For example, replace `current-density-regulated morphology` with `morphology regulated by current density` when the mechanism needs emphasis.
- Avoid unspaced em dashes in technical prose. Use a period, comma, colon, parentheses, or a subordinate clause according to the logical relationship. If a parenthetical dash is retained and the target style permits it, put a space on both sides: `the dryout transition – not the absolute heat flux – governed the acoustic response`.
- Do not use a dash merely to append a second thought. A period or comma usually makes the hierarchy between the main point and the added detail easier to read.
- Treat parenthetical dashes separately from numeric ranges and mathematical notation. Follow the target journal's style for a range such as `10-20 kPa` or `10–20 kPa`; do not add parenthetical spaces inside a range. Preserve a required minus sign or mathematical symbol.

## Final Editorial Check

Before delivery, perform a targeted search for `conversely`, forms of `enable` and `establish`, `unusually`, `together`, dash characters, repeated hyphenated compounds, catalog-like headings, and modifier-heavy sentences. Review each occurrence in context. The objective is not a zero count; it is precise, varied, readable writing whose claims match the evidence.

For UTF-8 plain-text, Markdown, or LaTeX drafts, the coordinator can produce an inventory with:

```text
python skills/mechanical-engineering-research/scripts/audit_technical_writing.py draft.md
```

The report cannot determine whether a phrase is field-standard or whether prose is AI-generated. Use it to focus the human editorial review.
