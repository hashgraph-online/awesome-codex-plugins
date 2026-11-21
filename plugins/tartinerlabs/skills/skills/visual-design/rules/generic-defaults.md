---
title: Generic Defaults
impact: MEDIUM
tags: template-look, defaults, ai-slop, first-impression
---

**Rule**: Find and replace the defaults nobody chose. A UI looks generic when its look comes from the framework, the component library, or the first suggestion, not from the product.

**Evidence**: First impressions of visual appeal form within about 50 milliseconds and persist (Lindgaard et al. 2006). Users who see the same defaults across many products read them as "template", and transfer that judgement to the product's quality (aesthetic-usability effect, Kurosu and Kashimura 1995).

### When Building

Before calling a screen done, check for these defaults and replace each one with a choice:
- **Untinted greys** (`gray-100`, `#F5F5F5`, `#E5E5E5`) and pure white and black. Tint them (`rules/color.md`).
- **A purple-to-blue or rainbow gradient hero.** Replace it with the product's signature visual.
- **The same radius and shadow on every block.** Use a scale and cards by role (`rules/surfaces.md`).
- **Everything centred**: headings, paragraphs, and buttons stacked down the middle. Left-align the content.
- **The library's default primary colour** (Tailwind blue, Material purple, the system blue in a non-native-styled app).
- **Emoji or generic icons in place of the product's content.** Use real data or the signature visual.
- **Three equal feature cards with icons**, which is the default marketing layout. Show the product instead.
- **Default font at default weights only.** Even a heavier display weight is a choice.
- **Glass, glow, and gradient borders added for "modern".** Use them only when the direction calls for them.

### When Auditing

- Count how many of the defaults above appear on the first screen. Three or more reads as a template.
- Ask whether a screenshot could belong to any other app in the category. If yes, the product's own content is missing.
- Check that the component library's theme has been set, not left at its defaults.

### Incorrect

```tsx
<section className="text-center bg-gradient-to-r from-purple-500 to-blue-500 rounded-xl shadow-lg p-8">
  <h1 className="text-4xl font-bold">Supercharge your workflow</h1>
  <button className="bg-blue-500 rounded-lg">Get started</button>
</section>
```

### Correct

```tsx
<section className="bg-surface px-6 py-16">
  <h1 className="font-display text-5xl text-ink">A week of dinners,<br />planned in minutes.</h1>
  <ProductPreview className="mt-10 -rotate-2" />
  <button className="mt-8 rounded-full bg-ink text-surface">Plan this week</button>
</section>
```

### Why This Matters

Defaults are why products made with the same stack look alike. Replacing a handful of them with deliberate choices does more for how polished a product looks than any amount of extra decoration.

### Alternatives

Internal tools, admin panels, and prototypes can keep library defaults. Consistency matters more there than character. A product that deliberately follows the platform's native look (system colours, system font, standard components) has made a choice, not accepted a default.
