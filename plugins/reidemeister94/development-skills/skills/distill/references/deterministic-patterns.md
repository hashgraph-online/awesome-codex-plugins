# Deterministic Noise Patterns

The canonical kill-lists. The pre-pass runs the script below; it edits the file in place and prints the slop score. Context-free and safe to apply automatically before the LLM step.

```python
import re, sys
text = open(sys.argv[1]).read()

VERBOSE_SUBS = [
    ('in order to','to'),('due to the fact that','because'),('at this point in time','now'),
    ('in the event that','if'),('for the purpose of','for'),('on a daily basis','daily'),
    ('a large number of','many'),('the vast majority of','most'),('in spite of the fact that','although'),
    ('is able to','can'),('has the ability to','can'),('make use of','use'),
    ('take into consideration','consider'),('prior to','before'),('subsequent to','after'),
    ('in close proximity to','near'),('on the basis of','based on'),
]
for old, new in VERBOSE_SUBS:
    text = re.sub(r'\b'+re.escape(old)+r'\b', new, text, flags=re.IGNORECASE)

# Hedges deleted entirely (any trailing whitespace)
HEDGE = [
    r"It'?s (important|worth) (to note|mentioning|noting) that\s*", r"It should be noted that\s*",
    r"It bears mentioning( that)?\s*", r"Needless to say,?\s*", r"It goes without saying( that)?\s*",
    r"As you may know,?\s*", r"As mentioned (above|earlier|previously),?\s*", r"Keep in mind that\s*",
    r"[ÈE]' importante notare che\s*", r"[Vv]ale la pena (menzionare|ricordare|notare)( che)?\s*",
    r"[Vv]a sottolineato che\s*", r"[Cc]ome (accennato|menzionato) (sopra|in precedenza|prima),?\s*",
    r"[Tt]enere presente che\s*", r"[Aa] questo punto nel tempo,?\s*", r"[Ii]n sostanza,?\s*",
    r"[Pp]er quanto riguarda\s+",
]
for p in HEDGE:
    text = re.sub(p, '', text, flags=re.IGNORECASE)

# Filler openers + transitions deleted at line start (keep rest of sentence)
LINE_START = [
    r"^(Certainly|Absolutely|Of course)!?\s*", r"^Great question!?\s*",
    r"^That'?s a (really )?(good|great|excellent) (point|question)!?\s*",
    r"^Sure,?\s*(I'?d be happy to|let me)\s*", r"^Let me (explain|break this down)\.?\s*",
    r"^Here'?s the thing[.:]\s*", r"^I hope this helps!?\s*",
    r"^Let me know if you have any( other)? questions!?\s*",
    r"^(Moreover|Furthermore|Additionally|In addition),?\s*",
    r"^(That being said|With that in mind|Having said that),?\s*",
    r"^(Inoltre|Peraltro|In aggiunta),?\s*",
]
for p in LINE_START:
    text = re.sub(p, '', text, flags=re.MULTILINE|re.IGNORECASE)

# Slop score
BUZZWORDS = ['delve','tapestry','landscape','paradigm','leverage','utilize','facilitate',
    'comprehensive','holistic','robust','cutting-edge','state-of-the-art','revolutionary',
    'innovative','novel','synergy','empower','seamlessly','effortlessly','transformative']
count = sum(len(re.findall(r'\b'+re.escape(w)+r'\b', text, re.IGNORECASE)) for w in BUZZWORDS)
score = max(0, 100 - 2*count)
open(sys.argv[1], 'w').write(text)
print(f'PRE-CLEAN: slop_score={score}/100 | buzzwords={count}')
```

Empty conclusions are LLM-judgment (delete a final paragraph only if it restates earlier content), so they stay in the Step 2 distill, not here. Multilingual conclusion starters to watch: `In summary/conclusion/essence`, `To summarize/sum up/recap`, `Overall`, `The bottom line is`; IT `In conclusione/sintesi`, `Per riassumere`; FR `En résumé/conclusion`; ES `En resumen/conclusión`; DE `Zusammenfassend`, `Abschließend`.
