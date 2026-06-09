# Research Strategy Reference

## Core Principle

**Every field has an authority hierarchy.** The quality of your answer depends on climbing as high as possible on that hierarchy. This document provides frameworks for doing that across any domain.

---

## 1. Universal Evidence Quality Framework

### The Evidence Pyramid (applies to all domains)

```
           ┌───────────────┐
           │  Systematic    │  ← Synthesizes ALL evidence on a question
           │  Reviews /     │     Strongest: Cochrane, meta-analyses
           │  Meta-analyses │
           ├───────────────┤
           │  Controlled    │  ← Direct measurement with comparison group
           │  Experiments   │     RCTs, A/B tests, controlled benchmarks
           │  (RCTs, etc.)  │
           ├───────────────┤
           │  Observational │  ← Correlational, no manipulation
           │  Studies       │     Cohort, cross-sectional, case-control
           ├───────────────┤
           │  Case Studies  │  ← Specific documented instances
           │  & Production  │     Engineering postmortems, clinical cases,
           │  Evidence      │     documented implementations at scale
           ├───────────────┤
           │  Expert        │  ← Professional consensus, guidelines,
           │  Consensus     │     position statements, textbooks
           ├───────────────┤
           │  Individual    │  ← Single expert opinion, blog posts,
           │  Expert        │     conference talks, practitioner advice
           │  Opinion       │
           ├───────────────┤
           │  Anecdote &    │  ← "Worked for me", tradition, folklore,
           │  Tradition     │     conventional wisdom without validation
           └───────────────┘
```

**How to use:** When two sources disagree, the one higher on the pyramid generally wins — UNLESS the lower source has a compelling mechanistic argument or the higher source has methodological flaws.

### Domain-Specific Evidence Standards

The pyramid is universal, but what each level LOOKS LIKE varies:

| Domain | Gold standard | Strong evidence | Acceptable | Weak |
|--------|--------------|-----------------|------------|------|
| Medicine/Health | Cochrane reviews, clinical guidelines | RCTs (adequate n, proper blinding) | Large cohort studies | Case reports, expert opinion |
| Exercise Science | Meta-analyses in JSCR/MSSE, NSCA/ACSM position stands | RCTs with trained subjects | Long-term coaching outcomes at scale | Instagram science, gym folklore |
| Nutrition | Systematic reviews in AJCN/JN, EFSA/USDA guidelines | RCTs ≥12 weeks, adequate sample | Large epidemiological studies | Testimonials, fad diet books |
| Software Engineering | RFC/standard + production evidence at scale | Engineering blog with metrics from Tier A company | Well-maintained OSS (≥1k stars, active) | Blog posts without data, hype |
| Finance | Academic papers (JoF, QJE), central bank research | Vanguard/DFA/AQR research with data | Established textbooks (Malkiel, Bogle) | Trading gurus, affiliate content |
| Psychology | APA meta-analyses, Cochrane mental health reviews | Pre-registered RCTs | Replicated observational studies | Pop psychology, single studies |
| Design/Architecture | Building codes, professional standards (AIA/RIBA) | Award-winning documented projects | Expert practitioners with portfolio | Pinterest trends, magazine listicles |
| Cooking | Systematic testing (ATK/Kenji methodology), food science | Replicated technique testing, professional consensus | Michelin-level practitioner methods | "My grandmother always did it this way" |

---

## 2. Reality Constraints Framework

Reality constraints are harder evidence than any study. They come from the fundamental laws governing the domain.

### Constraint Categories

| Category | Examples | Domains where it matters |
|----------|----------|--------------------------|
| **Physics/mechanics** | Gravity, forces, leverage, material strength, heat transfer | Fitness (biomechanics), design (structural), cooking (thermodynamics) |
| **Biology/physiology** | Energy balance, muscle adaptation, hormonal response, circadian rhythm, recovery | Health, fitness, nutrition, sleep, productivity |
| **Cognitive/psychological** | Working memory limits (~4 items), attention span, habit formation, loss aversion | Learning, productivity, UX design, finance |
| **Economic** | Compound interest, opportunity cost, diminishing returns, incentive structures | Finance, business, time management |
| **Spatial/geometric** | Room dimensions, body proportions, ergonomic reach zones | Interior design, workspace, architecture |
| **Temporal** | Recovery time, adaptation rates, learning curves, latency | Training periodization, learning, distributed systems |
| **Safety/risk** | Injury mechanisms, failure modes, toxicity thresholds | Fitness, nutrition, engineering, medicine |

### How to use reality constraints

1. **As hard filters**: Any recommendation that violates a reality constraint is WRONG, regardless of source prestige. A diet claiming to bypass thermodynamics is wrong. An exercise claiming to "spot reduce fat" is wrong. An investment promising guaranteed returns above risk-free rate is wrong.

2. **As signal amplifiers**: When evidence is sparse, reality constraints narrow the solution space. If biomechanics says a movement loads a specific muscle group through full ROM, that's strong evidence even without an RCT.

3. **As BS detectors**: Claims that conflict with known constraints are red flags for the entire source.

---

## 3. Context Sensitivity Framework

### When recommendations are conditional

Most "best practices" have a **validity envelope** — they're best within certain conditions. Recognize when the answer depends on:

| Variable | How it changes the answer |
|----------|--------------------------|
| **Experience level** | Beginner: need simplicity, wide margins. Advanced: need optimization, specificity |
| **Goals** | Different goals = different optima (strength vs. hypertrophy, growth vs. income, aesthetics vs. function) |
| **Constraints** | Budget, time, space, equipment, health conditions narrow the option set |
| **Individual variation** | Genetics, preferences, local conditions, body composition, risk tolerance |
| **Time horizon** | Short-term vs. long-term optimal strategies often differ |
| **Scale** | What works for 1 person may not work for 1000, and vice versa |

### Decision rule

- If the answer is the same regardless of context variables → state it as a universal best practice
- If the answer depends on 1-2 key variables → produce conditional recommendations ("If X, then A. If Y, then B.")
- If the answer depends on many variables → produce a decision framework (matrix or flowchart)
- If critical context variables are unknown → ask the user before recommending

---

## 4. Anti-BS Detection Framework

Don't pattern-match against a blocklist. Reason about WHY something might be epistemically weak.

### The Skepticism Checklist

For any source or claim, ask:

1. **Who benefits?** Follow the money. If the recommender profits from the recommendation, increase skepticism.
2. **What's the sample?** Small n, uncontrolled, self-selected → weak evidence. Large n, controlled, representative → strong.
3. **Where's the comparison?** "X works" means nothing without "compared to what?" A/B thinking is essential.
4. **Is this the complete picture?** Cherry-picked studies, survivorship bias, and publication bias all distort.
5. **Could I be fooled?** Slick presentation, authority signals (white coat, PhD, Forbes feature), emotional appeal → check the actual evidence underneath.
6. **Has this replicated?** Single studies, even large ones, are uncertain. Replication is the gold standard.
7. **Does the mechanism make sense?** A recommendation with a plausible mechanism is stronger than one without.
8. **What would change my mind?** If nothing could change the author's mind, it's ideology, not evidence.

### Universal Discard Rules

Always drop:
- Content farms, SEO listicles, AI-generated summaries
- Marketing disguised as education (affiliate links, sponsored "reviews")
- Influencer/guru content without citations or methodology
- Outdated content (>4 years) unless foundational — and MARKED as such
- Anonymous authors with no verifiable credentials
- Claims that violate known reality constraints without acknowledging the conflict

### Domain-Specific Red Flags

| Domain | Red flags |
|--------|-----------|
| Health/Medicine | Miracle cures, "doctors don't want you to know", single-substance solutions for complex conditions |
| Fitness | "One weird trick", extreme transformations in short time, spot reduction, "muscle confusion" |
| Nutrition | Demonizing single macronutrients, supplement MLMs, fad diets with no long-term data |
| Finance | Guaranteed returns, trading secrets, "passive income" schemes, crypto hype |
| Tech | "X is dead", silver bullet architectures, resume-driven development, framework hype |
| Psychology | Oversimplified personality types, "reprogram your subconscious", NLP claims |
| Design | Trend-only advice without functional reasoning, "rules" without principles behind them |

---

## 5. Domain-Specific Source Guidance

Reference material for identifying authoritative sources per domain. Not exhaustive — use as starting points.

### Technology / Software Engineering

**Tier S:** Official documentation, RFCs (IETF, W3C, ECMA), seminal papers (Lamport, Brewer, Fowler), Google SRE Books, AWS Well-Architected Framework

**Tier A:** Netflix Tech Blog, Uber Engineering, Stripe Blog, Google AI Blog, Cloudflare Blog, Meta Engineering, LinkedIn Engineering, Spotify Engineering, Shopify Engineering

**Tier B:** Pragmatic Engineer, Architecture Notes, InfoQ, ThoughtWorks Technology Radar, ByteByteGo, The New Stack, ACM Queue

**Tier C:** GitHub repos ≥1k stars + active within 6 months, awesome-* lists, CNCF graduated projects

### Health / Medicine

**Tier S:** Cochrane Library, NEJM, Lancet, JAMA, BMJ, WHO/NIH clinical guidelines, Harrison's (textbook)

**Tier A:** Mayo Clinic, Cleveland Clinic, Johns Hopkins, top university medical centers

**Tier B:** UpToDate, established health journalism with medical review

### Fitness / Exercise Science

**Tier S:** NSCA position statements, ACSM guidelines, JSCR, MSSE, SJMSS. Key researchers: Schoenfeld, Helms, Israetel, Nuckols

**Tier A:** Stronger By Science, Renaissance Periodization (research-backed content), NSCA/ACSM certified researchers with publications

**Tier B:** Established evidence-based fitness communicators who cite research, professional S&C coaching organizations

### Nutrition

**Tier S:** Systematic reviews (Examine.com), EFSA scientific opinions, USDA dietary guidelines, AJCN, JN

**Tier A:** Precision Nutrition (evidence-based protocols), registered dietitians with research publications

**Tier B:** Examine.com blog/guides, established nutrition communicators citing primary sources

### Finance / Economics

**Tier S:** Central bank research (Fed, ECB), academic journals (JoF, QJE, AER), foundational works (Graham, Bogle, Malkiel, Damodaran)

**Tier A:** Vanguard Research, AQR/DFA research, CFA Institute, top MBA finance faculty

**Tier B:** Morningstar research, Bogleheads community wisdom, established financial journalists (Zweig, Bernstein)

### Psychology / Cognitive Science

**Tier S:** APA journals, Cochrane mental health reviews, Annual Review of Psychology, foundational researchers (Kahneman, Tversky, Bandura, Dweck)

**Tier A:** University clinical psychology departments, NICE guidelines, APA practice guidelines

**Tier B:** Psychology Today (expert-authored), established authors with research backing (Clear, Newport, Duhigg)

### Design / Architecture

**Tier S:** Building codes, professional standards (AIA, RIBA, ASID), universal design principles (Ron Mace)

**Tier A:** Dezeen, ArchDaily, award-winning firms with documented case studies

**Tier B:** Houzz Pro (technical content), Architectural Digest (when citing principles), design university publications

### Cooking / Food Science

**Tier S:** Harold McGee (On Food and Cooking), Modernist Cuisine, ATK/Cook's Illustrated blind testing, Kenji Lopez-Alt systematic methodology

**Tier A:** ChefSteps, Serious Eats test kitchen, Michelin-starred chefs with published methodology

---

## 6. Synthesis Principles

1. **Triangulate:** A claim is "best practice" when 3+ independent authoritative sources agree AND no reality constraint contradicts it
2. **Evidence hierarchy:** Higher pyramid level wins when sources conflict (with exceptions for methodological flaws)
3. **Date-weight:** Calibrate to domain's rate of change
4. **Scale-contextualize:** Elite ≠ beginner. Netflix ≠ startup. Pro athlete ≠ recreational. Always note the context
5. **Separate evidence from convention:** Research-backed vs. "everyone does it this way" are both potentially valuable, but the reader must know which is which
6. **Honest uncertainty:** Use evidence level markers. "We don't know" is a valid and valuable finding
7. **Concrete examples:** Every principle needs at least one specific application
8. **Conditional recommendations:** When the answer depends on context, say what it depends on — don't pick one context and present it as universal
