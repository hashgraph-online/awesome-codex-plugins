# Deterministic Noise Patterns

Regex patterns for mechanical noise removal. Run BEFORE the LLM distill step. These substitutions are context-free and safe to apply automatically.

## Verbose Constructions (always replace)

Run these substitutions on the text. Each is a direct replacement with zero semantic risk.

```python
VERBOSE_SUBS = [
    (r'\bin order to\b', 'to'),
    (r'\bdue to the fact that\b', 'because'),
    (r'\bat this point in time\b', 'now'),
    (r'\bin the event that\b', 'if'),
    (r'\bfor the purpose of\b', 'for'),
    (r'\bon a daily basis\b', 'daily'),
    (r'\ba large number of\b', 'many'),
    (r'\bthe vast majority of\b', 'most'),
    (r'\bin spite of the fact that\b', 'although'),
    (r'\bis able to\b', 'can'),
    (r'\bhas the ability to\b', 'can'),
    (r'\bmake use of\b', 'use'),
    (r'\btake into consideration\b', 'consider'),
    (r'\bprior to\b', 'before'),
    (r'\bsubsequent to\b', 'after'),
    (r'\bin close proximity to\b', 'near'),
    (r'\bon the basis of\b', 'based on'),
]
```

## Hedging Phrases (delete — English)

Remove these phrases entirely (with any trailing whitespace). They add zero information.

```python
HEDGE_EN = [
    r"It'?s (important|worth) (to note|mentioning|noting) that\s*",
    r"It should be noted that\s*",
    r"It bears mentioning( that)?\s*",
    r"Needless to say,?\s*",
    r"It goes without saying( that)?\s*",
    r"As you may know,?\s*",
    r"As mentioned (above|earlier|previously),?\s*",
    r"Keep in mind that\s*",
]
```

## Hedging Phrases (delete — Italian)

```python
HEDGE_IT = [
    r"[ÈE]' importante notare che\s*",
    r"[Vv]ale la pena (menzionare|ricordare|notare)( che)?\s*",
    r"[Vv]a sottolineato che\s*",
    r"[Cc]ome (accennato|menzionato) (sopra|in precedenza|prima),?\s*",
    r"[Tt]enere presente che\s*",
    r"[Aa] questo punto nel tempo,?\s*",
    r"[Pp]er quanto riguarda\s+",
    r"[Ii]n sostanza,?\s*",
]
```

## Empty Conclusions (delete paragraph — multilingual)

If the LAST section/paragraph starts with any of these, and restates content from earlier sections, delete the entire section.

```python
CONCLUSION_STARTS = [
    # English
    r"In (summary|conclusion|essence)",
    r"To (summarize|sum up|recap)",
    r"(Overall|All in all),",
    r"At the end of the day,",
    r"The bottom line is",
    # Italian
    r"In conclusione,?",
    r"Per riassumere,?",
    r"Nel complesso,?",
    r"In sintesi,?",
    # French
    r"En (résumé|conclusion),?",
    r"Pour résumer,?",
    # Spanish
    r"En (resumen|conclusión),?",
    r"Para resumir,?",
    # German
    r"Zusammenfassend,?",
    r"Abschließend,?",
]
```

## Filler Openers (delete line — English)

If a line or paragraph STARTS with one of these, delete the opener (keep the rest of the sentence if it has content).

```python
FILLER_OPENERS = [
    r"^(Certainly|Absolutely|Of course)!?\s*",
    r"^Great question!?\s*",
    r"^That'?s a (really )?(good|great|excellent) (point|question)!?\s*",
    r"^Sure,?\s*(I'?d be happy to|let me)\s*",
    r"^Let me (explain|break this down)\.?\s*",
    r"^Here'?s the thing[.:]\s*",
    r"^I hope this helps!?\s*",
    r"^Let me know if you have any( other)? questions!?\s*",
]
```

## Empty Transitions (delete word — multilingual)

Remove standalone transition words at the start of sentences.

```python
TRANSITIONS = [
    # English
    r"^(Moreover|Furthermore|Additionally|In addition),?\s*",
    r"^(That being said|With that in mind|Having said that),?\s*",
    # Italian
    r"^(Inoltre|Peraltro|In aggiunta),?\s*",
]
```

## Slop Score (quick count)

Count occurrences of these buzzwords. Score = 100 - (2 * count). Below 70 = needs distilling.

```python
BUZZWORDS = [
    'delve', 'tapestry', 'landscape', 'paradigm', 'leverage', 'utilize',
    'facilitate', 'comprehensive', 'holistic', 'robust', 'cutting-edge',
    'state-of-the-art', 'revolutionary', 'innovative', 'novel', 'synergy',
    'empower', 'seamlessly', 'effortlessly', 'transformative',
]
```
