---
title: Decoration
impact: LOW
tags: doodles, annotations, emoji, stickers, flourishes
---

**Rule**: Treat flourishes (doodles, handwritten notes, emoji, stickers, sparkles) as a budget. Spend it on low-stakes screens, in one hand-drawn style, and keep it off payment, errors, and dense data.

**Evidence**: Emotional design research (Norman, *Emotional Design*, 2004) finds that visceral delight helps first impressions and moments of success. The same cues read as unserious where users feel exposed: paying, losing data, or reading figures they must trust.

### When Building

- **Where decoration helps**: onboarding, welcome, success, empty states, and store screenshots.
- **Where it does not**: payment and checkout, error and destructive confirmations, financial or medical figures, and dense data tables.
- **One style**: one hand-drawn stroke, one annotation font, one sticker style. Doodles from different sources look pasted on.
- **Annotations explain something.** An arrow pointing at the feature, a circled number, or a handwritten "this one" earns its place. Random sparkles do not.
- **Emoji in headlines**, at most one, and only in Product showcase or Character-led directions.
- **Decoration is never the only signal.** Anything that carries meaning (a circled item, a highlighted value) also has a text or accessibility equivalent.

### When Auditing

- Sparkles, confetti, or doodles near prices, payment buttons, or errors
- Several decorative styles on one screen
- Decoration on every screen, including daily screens
- Meaning carried only by a doodle or emoji

### Incorrect

```tsx
<PriceTag value={price} />
<Sparkles />
<Text>Best deal ever!!! 🎉🔥</Text>
```

### Correct

```tsx
<PriceTag value={price} />
<Text style={type.caption}>Billed yearly. Cancel anytime in Settings.</Text>
```

### Why This Matters

A little decoration makes a product feel made by people. Too much, or in the wrong place, makes it feel unserious exactly when the user needs to trust it.

### Alternatives

Products for children, games, and products whose brand is playfulness can decorate more widely, and still keep payment and errors clear.
