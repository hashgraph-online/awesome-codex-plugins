# Academic slop pattern catalog

Each pattern lists why it hurts academic prose and a rewrite strategy. The categories
match the linter output (`scripts/slop_check.py`).

## chat-residue (always delete)

Assistant phrasing left in the text: "Certainly!", "I hope this helps", "Here is a revised version",
"As an AI language model", knowledge-cutoff disclaimers. These are evidence of unreviewed
AI output and can trigger misconduct concerns. Delete them and re-read the surrounding paragraph.

## stock-vocabulary

Words that LLMs overuse relative to human academic writing and that rarely add meaning:

| Pattern | Problem | Rewrite toward |
|---|---|---|
| delve into, explore the intricacies | Announces effort, not content | the analysis itself: "we measured", "we compared" |
| tapestry, landscape, realm, ecosystem (figurative) | Metaphor instead of a named system | the actual field, dataset or process |
| plays a pivotal/crucial/key role | Vague causal claim | the mechanism or magnitude |
| underscores the importance of | Asserted importance | the consequence ("without X, Y fails in 30% of cases") |
| sheds light on, paves the way for | Vague contribution | what was learned or what becomes possible |
| leverage, harness, unlock, empower | Business register | use, apply, enable, allow |
| showcase, boast, garner | Promotional register | show, have, receive |
| myriad, plethora, a wide range of | Unquantified quantity | the number, or "many" |
| multifaceted, holistic, seamless, meticulous | Evaluative filler | a precise property, or delete |

The words are not banned. "Landscape" is fine in ecology, and "leverage" is fine in finance. Flag them
when they are decorative.

## promotional and empty-emphasis

"groundbreaking", "revolutionary", "unprecedented", "paradigm shift", "cutting-edge", "remarkably",
"incredibly", "truly". Reviewers discount self-praise and often penalize it. Remove the adjective
and let the result (with its number) carry the weight. Use "novel" at most once, and only
where novelty is the claim.

## unsupported-significance

In empirical research "significant" means a statistical test was passed. Use it only with the test
and statistic nearby ("significantly lower (Mann-Whitney U, p = 0.003)"). Otherwise use "substantially",
"markedly" or, better, the magnitude itself.

## filler and signposting

- "It is important/worth noting that ...", "It should be noted that ...": delete the frame.
- "In order to" → "to". "Due to the fact that" → "because".
- "In conclusion," / "Overall," / "In summary," at paragraph starts: the section heading already does this.
- Sentence-initial "Moreover/Furthermore/Additionally" in more than about 1 sentence in 5: the text is
  listing, not arguing. Reorder so each sentence follows from the previous one.

## construction

- **"Not only X, but also Y"** and **"It's not just X, it's Y"**: rhetorical reveal structures. State X and Y plainly.
- **Rule of three**: reflexive triplets ("robust, scalable, and efficient") where only one property was
  tested. Keep what the evidence supports.
- **Colon teasers** in body text ("The result: a 20% gain."): fine once, grating when repeated.

## hedge-stack

"may potentially", "could possibly suggest", "might perhaps indicate". One hedge communicates uncertainty.
Two signal evasion. Choose the hedge by evidence strength:

| Evidence | Wording |
|---|---|
| Strong, replicated, causal design | "X causes Y", "X increases Y by ..." |
| Good but single study / observational | "X was associated with Y", "suggests" |
| Weak, indirect, exploratory | "is consistent with", "may", "we speculate" |

## rhythm (whole-text findings)

- **monotone-rhythm**: sentence lengths nearly uniform (coefficient of variation < 0.30). Human expert
  prose alternates short claims with long explanations.
- **uniform-paragraphs**: paragraphs of near-identical length suggest template filling.
- **repeated-opener**: many sentences begin the same way ("This study", "The results").
- **em-dash-pileup**: more than about 6 em dashes per 1,000 words. Use commas, colons, parentheses and full stops.
- **transition-overuse**: more than 20% of sentences open with a transition adverb.

## Beyond the linter: content-level slop

These are worse than any word choice and need judgment:
- **Restating the field** for a paragraph before the gap appears.
- **Symmetric praise-then-limitation** discussion paragraphs that say nothing specific.
- **Generic future work** ("future studies should explore larger datasets").
- **Claims that outrun the evidence**, such as "demonstrates" for a correlation or "universal" for three datasets.
- **Citations as decoration**: a reference that does not support the exact claim (see `citation-verification`).
