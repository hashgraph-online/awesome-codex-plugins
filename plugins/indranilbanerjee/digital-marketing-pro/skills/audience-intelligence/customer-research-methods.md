# Customer Research Methods — Methodology & Frameworks

A practitioner's guide to understanding customers through quantitative and qualitative research. Covers survey design, interview techniques, Jobs-to-Be-Done methodology, voice-of-customer programs, and synthesis methods — with budget guidance for every stage.

---

## Quantitative Research Methods

### Surveys

| Survey Type | What It Measures | When to Use | Benchmark |
|-------------|-----------------|-------------|-----------|
| **NPS (Net Promoter Score)** | Likelihood to recommend (0-10 scale) | Ongoing relationship health | SaaS: 30-50, eCommerce: 40-60 |
| **CSAT (Customer Satisfaction)** | Satisfaction with specific interaction (1-5 scale) | Post-purchase, post-support, post-onboarding | 75-85% positive |
| **CES (Customer Effort Score)** | Ease of completing a task (1-7 scale) | Post-interaction (support, checkout, setup) | 5.0+ out of 7 |
| **Product-Market Fit (Sean Ellis)** | "How disappointed if you could no longer use this product?" | After 2+ weeks of usage, minimum 40 responses | 40%+ "very disappointed" = PMF |
| **Conjoint Analysis** | Relative value of product features / price tradeoffs | Before pricing changes or new product development | Requires 200+ respondents |

### Analytics-Based Research

| Method | What It Reveals | Tools |
|--------|----------------|-------|
| **Behavioral analytics** | What users actually do (not what they say) | GA4, Mixpanel, Amplitude, Heap |
| **Cohort analysis** | How behavior changes over time by acquisition group | GA4, Mixpanel, custom SQL |
| **Funnel analysis** | Where users drop off in multi-step flows | GA4 funnels, Mixpanel funnels, Hotjar |
| **Session recordings** | Individual user journeys, friction points, confusion | Hotjar, FullStory, Microsoft Clarity |
| **Heatmaps** | Aggregate click, scroll, and attention patterns | Hotjar, Crazy Egg, Microsoft Clarity |
| **Feature usage tracking** | Which features drive retention vs. go unused | Mixpanel, Amplitude, Pendo |

---

## Qualitative Research Methods

### Method Selection Guide

| Method | Best For | Sample Size | Time per Session | Cost |
|--------|----------|-------------|-----------------|------|
| **1:1 Customer Interviews** | Deep understanding of motivations, problems, and decision processes | 8-15 interviews per segment | 30-60 min | Low (just your time) |
| **Focus Groups** | Exploring reactions, language, and group dynamics around concepts | 6-10 participants per group, 2-3 groups minimum | 60-90 min | Medium ($1K-$5K per group with recruitment) |
| **Usability Testing** | Identifying friction in product or website interactions | 5-8 participants per round | 30-45 min | Low-Medium |
| **Ethnographic Observation** | Understanding behavior in natural context (not self-reported) | 5-10 participants | 2-4 hours | Medium-High |
| **Diary Studies** | Capturing behavior and context over days or weeks | 10-20 participants | 1-4 weeks | Medium |
| **Contextual Inquiry** | Watching users perform tasks in their environment while asking questions | 6-12 participants | 60-120 min | Medium |
| **Card Sorting** | Understanding how users categorize and label information | 15-30 participants (open sort), 30+ (closed sort) | 15-30 min | Low |

---

## Survey Design Best Practices

### Question Types and When to Use Each

| Type | Example | Best For | Watch Out For |
|------|---------|----------|---------------|
| **Likert scale (1-5 or 1-7)** | "How satisfied are you with...?" | Measuring attitudes and perceptions | Acquiescence bias (tendency to agree) |
| **Multiple choice** | "Which feature do you use most often?" | Identifying preferences from known options | Leading options, exhaustive list needed |
| **Open-ended** | "What's your biggest challenge with...?" | Discovery, uncovering unknown problems | Low completion rate, analysis-intensive |
| **Matrix / Grid** | Rate 5 features on satisfaction and importance | Comparing multiple items on same dimensions | Respondent fatigue, straightlining |
| **Ranking** | "Rank these 5 features from most to least important" | Forcing tradeoffs (more informative than "rate each") | Maximum 7 items before cognitive overload |
| **Max-Diff** | "Which is most/least important from this set of 4?" | Discriminating between items better than ranking | Requires specialized analysis tools |

### Sample Size Requirements

| Confidence Level | Margin of Error | Population 1K | Population 10K | Population 100K+ |
|-----------------|----------------|---------------|----------------|-------------------|
| 95% | +/- 5% | 278 | 370 | 384 |
| 95% | +/- 3% | 516 | 964 | 1,067 |
| 99% | +/- 5% | 399 | 622 | 663 |

### Bias Avoidance Checklist

- [ ] **No leading questions** — "How great was your experience?" becomes "How would you describe your experience?"
- [ ] **No double-barreled questions** — "How satisfied are you with our pricing and features?" should be two separate questions
- [ ] **Balanced response scales** — Equal number of positive and negative options
- [ ] **No loaded language** — Neutral framing throughout
- [ ] **Randomize option order** — Prevents primacy/recency bias in multiple choice
- [ ] **Include "Not applicable" and "Prefer not to answer"** — Prevents forced false responses
- [ ] **Pilot test with 5-10 people** — Catch confusing questions before launch
- [ ] **Keep under 5 minutes** — Completion rates drop 15-20% for every additional minute beyond 5

### Question Ordering

1. Screening questions first (disqualify non-target respondents early)
2. Broad / easy questions next (build engagement)
3. Core research questions in the middle (respondent is focused)
4. Sensitive or demographic questions last (trust is established)
5. Open-ended questions at the very end (highest effort, lowest energy)

### Incentive Strategy

| Audience | Appropriate Incentive | Amount |
|----------|----------------------|--------|
| B2C customers | Gift card, discount code, sweepstakes entry | $5-$25 per response |
| B2B users | Amazon gift card, charity donation in their name | $25-$100 per response |
| Enterprise decision-makers | Research report access, executive summary | $50-$200 or equivalent value |
| Non-customers | Cash equivalent or universal gift card | $10-$50 per response |

---

## Interview Guide Template

### Warm-Up (5 minutes)
- Tell me about your role and what you're responsible for day-to-day.
- How long have you been in this role / using products like ours?
- What does a typical [relevant workflow] look like for you?

### Jobs-to-Be-Done Exploration (15 minutes)
- When did you first start looking for a solution like [product category]?
- What was happening that made you start looking? (push forces)
- What did you hope the solution would do for you? (pull forces)
- What were you using before? What almost kept you from switching? (habit + anxiety)
- Walk me through the decision process — who was involved, what did you compare?

### Problem Exploration (10 minutes)
- What's the hardest part about [workflow/task]?
- When was the last time you were frustrated by [problem area]? Walk me through what happened.
- How do you work around that problem today?
- What would it look like if that problem didn't exist?

### Solution Evaluation (10 minutes)
- Show me how you currently use [product/feature] for [task].
- What do you wish it did differently?
- If you could wave a magic wand and change one thing, what would it be?
- What would make you recommend this to a colleague?

### Willingness to Pay (5 minutes)
- At what price would this be too expensive to consider? (too expensive)
- At what price would this be so cheap you'd question the quality? (too cheap)
- At what price would it feel expensive but still worth it? (expensive/acceptable)
- At what price would it feel like a great deal? (cheap/acceptable)

### Closing (5 minutes)
- Is there anything I should have asked but didn't?
- Would you be open to a follow-up conversation in the future?
- Can you think of anyone else who'd be good to talk to about this?

---

## Jobs-to-Be-Done (JTBD) Research

### Switch Interview Framework

The switch interview reconstructs the timeline of how a customer moved from their old solution to your product. It reveals the four forces that drive every switching decision.

### The Four Forces of Progress

| Force | Direction | Interview Questions |
|-------|-----------|-------------------|
| **Push** (problems with current solution) | Drives away from status quo | "What was going wrong with your old approach?" "When did it become unacceptable?" |
| **Pull** (attraction of new solution) | Draws toward new solution | "What about [product] made you think it could solve that?" "What outcome were you hoping for?" |
| **Habit** (comfort with current solution) | Resists change | "What did you like about the old way?" "What was hard about leaving?" |
| **Anxiety** (uncertainty about new solution) | Resists change | "What worried you about switching?" "What almost stopped you?" |

### Timeline Mapping

Map the switching journey across these key moments:

1. **First thought** — When did you first realize the old solution wasn't enough?
2. **Passive looking** — When did you start noticing alternatives without actively searching?
3. **Active looking** — What triggered you to start researching and comparing options?
4. **Decision** — What was the final trigger that made you commit?
5. **Purchase** — Walk me through the actual buying/signup experience.
6. **First use** — What happened when you first used the product?
7. **Ongoing use** — How has your usage evolved since then?

---

## Win/Loss Analysis

### Interview Framework — Won Deals

| Area | Questions |
|------|-----------|
| **Trigger** | What was happening that initiated this purchase? |
| **Evaluation** | Who else did you evaluate? How far did they get? |
| **Decision criteria** | What were the top 3 factors in your decision? |
| **Differentiator** | What made you choose us specifically? |
| **Objections** | What concerns did you have? What almost stopped you? |
| **Content influence** | What content, demos, or conversations were most helpful? |
| **Improvement** | What would have made the buying process easier? |

### Interview Framework — Lost Deals

| Area | Questions |
|------|-----------|
| **Trigger** | What problem were you trying to solve? |
| **Evaluation** | Walk me through your evaluation process. |
| **Elimination** | At what point did you remove us from consideration? |
| **Deciding factor** | What specifically caused you to choose [competitor]? |
| **Perception** | What was your impression of our product? Our team? Our pricing? |
| **Reconsideration** | What would have changed your mind? Is there a scenario where you'd reconsider? |

### Pattern Identification Template

```
WIN/LOSS ANALYSIS — [Quarter/Period]

DEALS ANALYZED: [Won: N, Lost: N]

TOP WIN THEMES:
1. [Theme] — mentioned in X of Y winning interviews
2. [Theme] — mentioned in X of Y
3. [Theme] — mentioned in X of Y

TOP LOSS THEMES:
1. [Theme] — mentioned in X of Y losing interviews
2. [Theme] — mentioned in X of Y
3. [Theme] — mentioned in X of Y

COMPETITIVE PATTERNS:
- Lost to [Competitor A]: X times — primary reason: [reason]
- Lost to [Competitor B]: X times — primary reason: [reason]
- Lost to "no decision": X times — primary reason: [reason]

RECOMMENDED ACTIONS:
1. [Action] — addresses [loss theme]
2. [Action] — reinforces [win theme]
3. [Action] — competitive response to [competitor pattern]
```

---

## Voice of Customer (VoC) Programs

### Continuous Feedback Collection Sources

| Source | Type | Mining Method | Insight Quality |
|--------|------|---------------|-----------------|
| **Support tickets** | Reactive complaints | Tag by category, track volume trends | High — real friction |
| **Chat transcripts** | In-moment questions | NLP topic clustering, manual sampling | High — captures confusion |
| **Online reviews** | Public opinion | Sentiment analysis, keyword extraction | Medium-High — self-selected sample |
| **Social mentions** | Unsolicited feedback | Social listening tools (Brandwatch, Sprout) | Medium — noisy but authentic |
| **Sales call recordings** | Prospect objections | Call intelligence (Gong, Chorus) keyword tracking | High — reveals purchase barriers |
| **NPS follow-up responses** | Promoter/detractor reasons | Text analysis of open-ended responses | High — tied to quantitative score |
| **Community forums** | Feature requests, workarounds | Topic tagging, upvote counting | Medium-High — power user bias |
| **App store reviews** | Mobile-specific feedback | Rating trends, keyword extraction | Medium — skews negative |

---

## Research Synthesis

### Affinity Mapping Process

1. **Capture** — Write each observation, quote, or finding on a separate sticky note (digital: Miro, FigJam)
2. **Cluster** — Group similar observations together without pre-defined categories
3. **Label** — Name each cluster with a descriptive theme (use participant language, not internal jargon)
4. **Prioritize** — Rank clusters by frequency (how many participants mentioned it) and severity (how much it impacts behavior)
5. **Synthesize** — Write 3-5 key insight statements in the format: "[User type] needs [need] because [underlying motivation/evidence]"

### From Research to Personas

| Research Input | Persona Element |
|---------------|-----------------|
| Demographic survey data | Age, role, company size, geography |
| JTBD interviews | Goals, motivations, jobs-to-be-done |
| Pain point clustering | Frustrations and challenges |
| Behavioral analytics | Usage patterns, feature preferences |
| Win/loss analysis | Decision criteria, evaluation process |
| Support ticket themes | Common questions and friction points |

### Insight Prioritization Matrix

| Dimension | Weight | Scoring |
|-----------|--------|---------|
| **Frequency** | 30% | How many customers mentioned or demonstrated this? |
| **Severity** | 30% | How significantly does this impact the customer's ability to succeed? |
| **Addressability** | 20% | How feasible is it for us to act on this insight? |
| **Revenue impact** | 20% | Does this affect willingness to pay, retention, or expansion? |

---

## Research Repository Best Practices

### Tagging System

Every insight should be tagged across three dimensions:

1. **Topic** — Feature area, workflow, or product domain
2. **Persona** — Which customer segment this insight applies to
3. **Source** — Interview, survey, analytics, support, review

### Insight Aging

| Age | Status | Action |
|-----|--------|--------|
| < 6 months | Fresh | Use with confidence in current decisions |
| 6–12 months | Current | Valid for strategy, verify details for tactical decisions |
| 12–24 months | Aging | Cross-reference with newer data before relying on it |
| > 24 months | Stale | Re-research before using; market conditions likely changed |

---

## Budget Guide

### Free ($0)

- Google Forms or Typeform free tier for surveys
- Manual customer interviews (use Zoom free tier)
- Google Analytics / Microsoft Clarity for behavioral data
- Review mining (manually read G2, Capterra, app store reviews)
- Support ticket analysis (export and tag manually)

### Starter ($500)

- Survey tool with logic and piping (Typeform Pro, SurveyMonkey)
- $200 in gift card incentives for 10-15 survey respondents
- $300 in gift card incentives for 5-6 customer interviews
- Otter.ai or similar for interview transcription

### Growth ($5,000)

- All of the above, plus:
- Dedicated user research tool (Maze, UserTesting)
- 20-30 moderated interviews with professional transcription
- Panel recruitment for non-customer research (Respondent.io, User Interviews)
- Basic social listening tool (Mention, Brand24)
- Hotjar or similar for session recordings and heatmaps

### Enterprise ($50,000)

- All of the above, plus:
- Full-service research platform (Qualtrics, Medallia)
- Continuous VoC program with automated survey triggers
- Call intelligence platform (Gong, Chorus)
- Professional research agency for complex studies (conjoint, ethnographic)
- Dedicated research repository tool (Dovetail, EnjoyHQ)
- Quarterly competitive win/loss analysis program
