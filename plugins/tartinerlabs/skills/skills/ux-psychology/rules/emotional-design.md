---
title: Emotional Design
impact: MEDIUM
tags: emotion, anxiety, reassurance, tone, delight, trust, identity
---

**Rule**: Emotion runs highest at predictable moments: the first impression, risk (money, data, anything irreversible), waiting, failure, success, and leaving. Find those moments in the flow and design for the feeling there. Reassure when there is risk, stay calm when something fails, and be warm when things succeed. Feeling follows function, so these moments only help once the flow works.

**Evidence**: Norman, *Emotional Design: Why We Love (or Hate) Everyday Things* (2004) — people respond at three levels: visceral (first impression), behavioral (the experience of use), and reflective (what the product means to them afterwards). Norman argues that anxiety narrows attention and makes people worse at problem-solving, while positive affect broadens it. Isen, Daubman & Nowicki 1987 (*Journal of Personality and Social Psychology*) — people put in a positive mood solved a creative problem (Duncker's candle task) more often. Hassenzahl & Tractinsky 2006, "User experience — a research agenda" (*Behaviour & Information Technology*) — experience combines the product with the user's mood, expectations, and goals over time. Walter, *Designing for Emotion* (2011) — pleasure sits on top of functional, reliable, and usable, never in place of them. Norton, Mochon & Ariely 2012, "The IKEA effect: When labor leads to love" (*Journal of Consumer Psychology*) — people value what they helped make more highly.

### When Building

- **Map the emotional moments** — before writing copy, mark the screens where the user is exposed (payment, permissions, deleting, sending, publishing), waiting, failing, succeeding, or leaving. Routine screens stay neutral; these get deliberate design
- **Reassure at the point of risk** — state the consequence and the safety net next to the action: "You won't be charged until 2 Nov", "You can undo this for 30 days", "Nothing is posted without your OK"
- **Calm at failure** — keep the user's work, take the blame off them, and give a way forward (`rules/error-prevention.md`, `rules/microcopy.md`)
- **Tone follows the user's state** — plain and steady when they are anxious or frustrated, warmer when things go well. Personality and humour only in low-stakes moments
- **Reflect the user back** (reflective level) — show what they made and achieved in their own terms ("You've sent 120 invoices this year"), and let them shape their space (names, layouts, themes). People value what they built
- **Delight last, and sparingly** — a completion moment or a personal touch on a milestone, once the basics work (`rules/peak-end.md`)

### When Auditing

- High-stakes actions (payment, deletion, sending, permission asks) with no word on consequence or reversibility
- The same upbeat tone in errors as in success; jokes in failures, payments, or destructive actions
- Celebrations on routine actions, or delight added while the flow underneath is broken
- Emotional pressure — guilt, fear of missing out, loss-framed nags, streaks that punish a missed day. Report these as CRITICAL under `rules/deceptive-patterns.md`
- A product that never shows users their own work or progress back to them

### Incorrect

```tsx
<CardForm />
<Button onPress={subscribe}>Subscribe</Button>
```

### Correct

```tsx
<CardForm />
<Button onPress={startTrial}>Start 14-day free trial</Button>
<Text>You won't be charged until 2 Nov. We'll email you 3 days before. Cancel anytime in Settings.</Text>
```

### Why This Matters

Emotion changes how people think, not just how they feel about it afterwards. An anxious user reads less, misses things, and abandons; a confident one explores and recovers from mistakes. The moments with the strongest feeling are also the ones people remember (`rules/peak-end.md`) and decide whether to come back on.

### Alternatives

Expert and internal tools get most of their emotional value from reliability and calm — skip the personality and the celebrations. The visceral level's visual craft (colour, type, motion) belongs to visual-design and animation skills; this rule decides *where* feeling matters, not how it looks. Emotion used against the user's interest — to retain, upsell, or shame — is a deceptive pattern, not emotional design (`rules/deceptive-patterns.md`).
