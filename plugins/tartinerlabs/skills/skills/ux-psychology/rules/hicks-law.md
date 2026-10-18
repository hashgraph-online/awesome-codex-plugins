---
title: Hick's Law
impact: MEDIUM
tags: choices, decisions, menus, plans, options
---

**Rule**: Decision time grows with the number of equally likely choices. Where people must choose, cut, group, or recommend — but don't hide options people already know they want.

**Evidence**: Hick 1952 (*Quarterly Journal of Experimental Psychology*) and Hyman 1953 (*Journal of Experimental Psychology*) — reaction time rises with the logarithm of the number of alternatives. Choice overload is weaker than popularly believed: Iyengar & Lepper's 2000 jam study (*JPSP*) is famous, but Scheibehenne, Greifeneder & Todd's 2010 meta-analysis (*Journal of Consumer Research*) found a mean effect near zero with high variance — overload shows up in some studies, but no reliable conditions for it were identified.

### When Building

- **At decision points** (plan pickers, onboarding choices, primary actions on a screen) keep the options few and comparable, and mark a recommended one
- **Group** long option lists into labelled categories so users choose a group, then an item (`rules/gestalt-grouping.md`)
- **Defaults** remove a decision entirely when one option suits most people (`rules/defaults.md`)
- **Progressive disclosure** moves rare options out of the first decision (`rules/progressive-disclosure.md`)
- **Search and sort** for long lists where users know what they are looking for — a country list needs search, not fewer countries

### When Auditing

- Screens with several equal-weight primary actions
- Plan or option pickers with more than four or five options and no recommendation
- Settings or menus presenting every option flat and ungrouped
- Onboarding questions that force choices users cannot yet judge

### Incorrect

```tsx
// Six plans, no recommendation, eleven differing features
<PlanGrid plans={allPlans} />
```

### Correct

```tsx
<PlanGrid plans={[starter, team, business]} recommended="team" />
<Link href="/pricing/compare">Compare all plans</Link>
```

### Why This Matters

Every extra option at a decision point slows the decision and raises the chance of no decision at all. The cost is highest where people are least sure — exactly the onboarding and pricing moments that matter most.

### Alternatives

Hick's law does not apply when users already know their target — scanning a familiar, well-ordered list (countries, contacts, files) is a search, not a decision. Expert tools serve users who want every option visible. Cutting options people need to make a screen "simpler" just moves the cost elsewhere.
