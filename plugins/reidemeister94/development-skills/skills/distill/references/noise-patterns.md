# Noise Patterns Reference

Taxonomy of noise in LLM-generated text, from academic research (Verbosity != Veracity, ACL 2025) and empirical analysis.

## 1. Hedging Language

**Kill list:**
- "It's important to note that..."
- "It's worth mentioning that..."
- "It should be noted that..."
- "It bears mentioning..."
- "One could argue that..."
- "It goes without saying..."
- "Needless to say..."
- "As you may know..."
- "As mentioned above/earlier..."
- "Keep in mind that..."

**Italian equivalents:**
- "È importante notare che..."
- "Vale la pena menzionare che..."
- "Va sottolineato che..."
- "Come accennato sopra/in precedenza..."
- "Tenere presente che..."

**Rule:** If removing the hedge doesn't change meaning, remove it. Apply in ALL languages — the patterns are structural, not language-specific.

## 2. Empty Transitions

**Kill list:**
- "Moreover" / "Furthermore" / "Additionally" / "In addition"
- "That being said" / "With that in mind" / "Having said that"
- "On the other hand" (when not contrasting)
- "In terms of..." / "When it comes to..." / "With respect to..." / "In the context of..."

**Rule:** Logical connection should be evident from content.

## 3. Empty Conclusions

**Kill list:**
- "In summary" / "In conclusion" / "In essence"
- "To summarize" / "To sum up" / "To recap"
- "Overall" / "All in all" / "At the end of the day"
- "The bottom line is..."
- Any final paragraph that restates previous content

**Italian equivalents:**
- "In conclusione" / "In sintesi"
- "Per riassumere" / "Per concludere"
- "Nel complesso" / "In definitiva"

**Rule:** A conclusion should synthesize or add insight, not repeat. Apply in ALL languages.

## 4. Filler Openers

**Kill list:**
- "Certainly!" / "Absolutely!" / "Of course!"
- "Great question!" / "That's a really good point!"
- "Sure, I'd be happy to help with that!"
- "Let me explain..." / "Let me break this down..."
- "Here's the thing..."

**Rule:** Delete entirely. Start with actual content.

## 5. Buzzword Inflation

**Replace or remove:**
- "delve" → "examine" or state the finding
- "leverage" / "utilize" → "use"
- "facilitate" → "help" or "enable"
- "tapestry" / "landscape" / "realm" / "paradigm" → be specific
- "cutting-edge" / "state-of-the-art" / "revolutionary" → state the specific advance
- "holistic" / "comprehensive" / "robust" → what does it cover?
- "synergy" / "alignment" / "empower" → what happens?
- "seamlessly" / "effortlessly" → remove (if true, the reader sees it)
- "innovative" / "novel" → state what's new

**Rule:** Replace with specifics. If removable without loss, remove.

## 6. Verbose Constructions

**Replace:**
- "in order to" → "to"
- "due to the fact that" → "because"
- "at this point in time" → "now"
- "in the event that" → "if"
- "for the purpose of" → "to" / "for"
- "on a daily basis" → "daily"
- "a large number of" → "many"
- "the vast majority of" → "most"
- "in spite of the fact that" → "although"
- "is able to" / "has the ability to" → "can"
- "make use of" → "use"
- "take into consideration" → "consider"
- "prior to" → "before"
- "subsequent to" → "after"
- "in close proximity to" → "near"
- "on the basis of" → "based on" / "from"

## 7. Structural Padding

**Patterns:**
- Unnecessary introductory paragraphs without information
- Rigid 5-paragraph essay structure forced on content that doesn't need it
- Headers for single-paragraph sections (header repeats the paragraph)
- Bullet points where a single sentence suffices
- Tables with only 2-3 rows (clearer as prose)
- Decorative formatting (excessive bold, rules, emoji bullets)

**Rule:** Structure serves navigation. Short documents need minimal structure.

## 8. Non-Committal Language

**Patterns:**
- "X can be Y" when you mean "X is Y"
- "X may help with Y" when evidence shows it does
- "It depends on various factors" without stating which
- Presenting all sides as equally valid when evidence favors one
- Excessive "might", "could", "possibly", "potentially"

**Rule:** Make the strongest claim the evidence supports. Qualify only when the qualification carries information.

## 9. Repetition and Redundancy

**Patterns:**
- Same idea in different words within a section
- "X, which means Y" where Y is obvious from X
- Echo sentences: "This is important. The importance cannot be overstated."
- Overlapping list items
- Re-explaining a concept already covered

**Rule:** State each fact once, where most relevant.

## 10. Verbosity Compensation (academic)

When uncertain, LLMs produce:
- **Ambiguity**: vague answers instead of specific
- **Question repetition**: restating the question
- **Enumeration**: listing all possibilities instead of selecting
- **Verbose details**: excessive context around simple facts
- **Verbose format**: unnecessary formatting, emphasis on non-key terms
