---
title: Social Proof
impact: MEDIUM
tags: testimonials, reviews, trust, norms, landing, pricing
---

**Rule**: When unsure, people follow what others like them do. Show real, specific evidence of other people's use and satisfaction where the user is deciding.

**Evidence**: Cialdini, *Influence* (1984) — social proof as a principle of compliance. Goldstein, Cialdini & Griskevicius 2008 (*Journal of Consumer Research*) — hotel guests reused towels more when told most guests did, and most of all when told most guests *in the same room* did: the closer the reference group, the stronger the effect.

### When Building

- **At the decision point** — testimonials and reviews near the sign-up button or plan choice, not on a separate page
- **Specific and attributable** — a real name, role, company, or photo; a concrete outcome ("cut our invoicing time in half") beats generic praise
- **Similar people** — show customers like the visitor (same industry, team size, use case) where segmentation allows
- **Real numbers** from real data — active users, ratings with review counts, "most popular" plan based on actual uptake
- **Show the distribution** — a rating with its review count; a few critical reviews increase credibility

### When Auditing

- Testimonials or counters that are hard-coded with no data source
- Generic, unattributed quotes
- "Most popular" labels not backed by data
- Social proof placed far from the decision it supports

### Incorrect

```tsx
<Badge>🔥 2,341 people signed up today</Badge> {/* hard-coded */}
```

### Correct

```tsx
<Rating value={stats.rating} count={stats.reviewCount} />
<Testimonial quote={t.quote} name={t.name} role={t.role} company={t.company} />
```

### Why This Matters

At uncertain moments — first visit, plan choice, sign-up — people look for evidence that others like them made the same choice and were glad. Real evidence reduces that uncertainty; fake evidence destroys trust once spotted.

### Alternatives

Negative social proof backfires: "most people don't finish their profile" normalises not finishing — frame the desired behaviour instead. Invented reviews, counters, or "popular" labels are deceptive patterns and, for reviews, illegal in many markets (`rules/deceptive-patterns.md`). New products without users should show other evidence (a clear demo, a guarantee) rather than fake numbers.
