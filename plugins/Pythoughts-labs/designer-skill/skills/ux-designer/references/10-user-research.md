# User Research Methods

User research is the systematic study of target users to understand their behaviors, needs, and motivations. It informs design decisions with evidence rather than assumptions.

---

## Why User Research?

### Benefits

- **Reduce risk** - Validate ideas before building
- **Save resources** - Avoid building unwanted features
- **Improve usability** - Design for real user needs
- **Increase satisfaction** - Create products people love
- **Drive conversion** - Remove friction in user journeys

### Key Statistics (2025)

| Method | Popularity |
|--------|------------|
| User interviews | 86% |
| Usability testing | 84% |
| Surveys | 77% |
| Concept testing | 64% |

---

## Research Categories

### Qualitative vs. Quantitative

| Qualitative | Quantitative |
|-------------|--------------|
| "Why" and "How" | "What" and "How many" |
| Deep understanding | Statistical significance |
| Small sample sizes | Large sample sizes |
| Exploratory | Measurable |
| Interviews, observations | Surveys, analytics |

### Generative vs. Evaluative

| Generative (Discovery) | Evaluative (Validation) |
|------------------------|------------------------|
| What should we build? | Does this work? |
| Early-stage exploration | Testing solutions |
| Understand problems | Measure effectiveness |
| Interviews, field studies | Usability tests, A/B tests |

---

## Core Research Methods

### 1. User Interviews

One-on-one conversations to understand user experiences, needs, and pain points.

**When to use:**
- Early discovery phase
- Understanding context of use
- Exploring new problem spaces
- Deep-diving into specific topics

**Best Practices:**

```
Preparation:
- Define clear research questions
- Write a discussion guide
- Recruit representative participants (5-8)
- Plan for 45-60 minute sessions

During:
- Ask open-ended questions
- Follow up with "why" and "how"
- Avoid leading questions
- Listen more than you talk
- Take notes or record (with permission)

Question Examples:
✓ "Tell me about the last time you..."
✓ "Walk me through how you..."
✓ "What was the hardest part about..."
✓ "Why did you choose that approach?"

✗ "Do you like feature X?" (leading)
✗ "Would you use this?" (hypothetical)
✗ "Isn't this confusing?" (leading)
```

### 2. Usability Testing

Observing users as they attempt to complete tasks with your product.

**When to use:**
- Validating design decisions
- Identifying usability issues
- Comparing design alternatives
- Before and after redesigns

**Types:**

| Type | Description | Sample Size |
|------|-------------|-------------|
| Moderated | Facilitator guides the session | 5-8 |
| Unmoderated | Participant completes alone | 10-20+ |
| Remote | Via video conferencing | Any |
| In-person | Same physical location | 5-8 |

**Best Practices:**

```
Task Design:
- Realistic scenarios
- Specific, measurable goals
- Avoid hints in wording
- Test critical paths

Metrics:
- Task success rate
- Time on task
- Error rate
- Satisfaction rating (SUS, NPS)
- Qualitative observations

Running the Test:
- "Think aloud" protocol
- Don't help unless stuck
- Note where users struggle
- Ask follow-up questions after tasks
```

### 3. Surveys

Collecting structured data from many users.

**When to use:**
- Measuring satisfaction (NPS, CSAT)
- Validating findings at scale
- Prioritizing features
- Segmenting users
- Benchmarking over time

**Best Practices:**

```
Question Design:
- One concept per question
- Avoid leading language
- Include "I don't know" option
- Mix question types

Question Types:
- Multiple choice (easy to analyze)
- Rating scales (1-5 or 1-7)
- Open-ended (qualitative insights)
- Matrix questions (use sparingly)

Keep It Short:
- 5-10 minutes maximum
- Front-load important questions
- Make it mobile-friendly
- Show progress indicator
```

**Tools:** Typeform, Google Forms, SurveyMonkey, Qualtrics

### 4. Card Sorting

Understanding how users categorize and label information.

**When to use:**
- Designing navigation
- Organizing content
- Creating taxonomies
- Validating IA decisions

**Types:**

| Type | Description | Use |
|------|-------------|-----|
| Open | Users create their own categories | Discovery |
| Closed | Users sort into predefined categories | Validation |
| Hybrid | Mix of open and closed | Refinement |

**Tools:** OptimalSort, Maze, Miro

### 5. Tree Testing

Validating whether users can find items in your information architecture.

**When to use:**
- Testing navigation structure
- Validating IA changes
- Before/after IA redesigns

**Process:**

```
1. Create text-only sitemap (tree)
2. Write tasks: "Find where to return an item"
3. Users navigate the tree to find the target
4. Measure:
   - Success rate
   - Directness (first click correct)
   - Time to complete
```

**Tools:** Treejack, UXtweak

### 6. Analytics Review

Analyzing behavioral data to understand what users do.

**When to use:**
- Always (continuous)
- Identifying problem areas
- Measuring feature adoption
- Understanding user flows

**Key Metrics:**

```
Engagement:
- Page views, sessions
- Time on page
- Bounce rate
- Feature usage

Conversion:
- Conversion rate
- Drop-off points
- Funnel completion

User Behavior:
- Click patterns (heatmaps)
- Scroll depth
- Search queries
- Error rates
```

**Tools:** Google Analytics, Mixpanel, Amplitude, Hotjar, FullStory

### 7. A/B Testing

Comparing two or more versions to see which performs better.

**When to use:**
- Optimizing specific metrics
- Validating design changes
- Testing copy variations
- Resolving design debates

**Requirements:**

```
- Sufficient traffic/users
- Clear hypothesis
- Single variable testing (ideally)
- Statistical significance threshold
- Adequate test duration
```

**Tools:** Optimizely, VWO, Google Optimize (deprecated), LaunchDarkly

---

## Research Planning

### Research Questions

```
Good research questions:
- Specific and focused
- Answerable through research
- Actionable outcomes

Examples:
✓ "What prevents users from completing checkout?"
✓ "How do users currently track their expenses?"
✓ "Which onboarding flow leads to higher activation?"

Not:
✗ "Is our product good?"
✗ "What do users want?"
✗ "Should we build feature X?"
```

### Participant Recruitment

**Sample Sizes:**

| Method | Typical Sample |
|--------|---------------|
| Interviews | 5-12 |
| Usability testing | 5-8 per round |
| Card sorting | 15-30 |
| Surveys | 100+ for quantitative |
| A/B tests | Varies (statistical power) |

**Recruitment Sources:**
- Existing user base
- Recruitment platforms (UserTesting, Respondent.io)
- Social media
- Intercept surveys
- Panel providers

**Screening:**
- Demographics
- Relevant experience
- Product usage
- Technical requirements

---

## Remote vs. In-Person Research

### Remote Research

**Advantages:**
- Global reach
- Lower cost
- More convenient
- Larger sample sizes
- Natural environment

**Challenges:**
- Technical issues
- Harder to build rapport
- Less contextual observation
- Distractions

**Tools:** Zoom, UserTesting, Lookback, Maze

### In-Person Research

**Advantages:**
- Deeper rapport
- Full context observation
- Non-verbal cues visible
- Better for complex tasks
- Prototype testing

**Challenges:**
- Geographic limitations
- Higher cost
- Scheduling difficulties
- Lab environment effect

---

## Research Analysis

### Affinity Mapping

Grouping observations to find patterns.

```
1. Write each observation on a sticky note
2. Group similar observations
3. Name the groups
4. Identify themes and patterns
5. Prioritize findings
```

**Tools:** Miro, FigJam, physical sticky notes

### Thematic Analysis

```
1. Familiarize with data
2. Generate initial codes
3. Search for themes
4. Review themes
5. Define and name themes
6. Report findings
```

### Quantitative Analysis

```
Basic:
- Descriptive statistics
- Task success rates
- Comparison of means

Advanced:
- Statistical significance testing
- Regression analysis
- Cohort analysis
```

---

## Presenting Research Findings

### Research Report Structure

```
1. Executive Summary
   - Key findings
   - Recommendations

2. Research Overview
   - Goals
   - Methods
   - Participants

3. Detailed Findings
   - Organized by theme
   - Evidence and quotes
   - Severity ratings

4. Recommendations
   - Prioritized actions
   - Design implications
   - Next steps
```

### Making Findings Actionable

```
Instead of:
"Users were confused by the checkout flow"

Say:
"5 of 8 users couldn't find the promo code field.
Recommendation: Move promo code input above the order summary.
Impact: Could recover ~15% of abandoned carts."
```

---

## 2026 Trends

### AI in Research

- **Transcription:** Otter.ai, Dovetail
- **Analysis:** Pattern recognition in qualitative data
- **Synthesis:** Summarizing findings across studies
- **Moderation:** AI-assisted interview guides

54% of researchers are experimenting with AI tools (2025 State of User Research)

### Continuous Research

Moving from project-based to always-on research:
- Regular user touchpoints
- Embedded research in product teams
- Research repositories (Dovetail, Notion)
- Democratized research

### Research Operations (ResOps)

- Standardized processes
- Participant panels
- Tool management
- Knowledge management
- Research training

---

## Ethical Considerations

### Informed Consent

```
Participants must know:
- Purpose of research
- How data will be used
- Their right to withdraw
- Recording/privacy details
- Compensation details
```

### Privacy

```
- Anonymize data when possible
- Secure data storage
- Clear data retention policies
- GDPR/CCPA compliance
- Limit data access
```

### Inclusive Research

```
- Recruit diverse participants
- Accommodate disabilities
- Consider cultural contexts
- Avoid biased questions
- Provide fair compensation
```

---

## Tools Overview

| Category | Tools |
|----------|-------|
| Interviews | Zoom, UserInterviews.com |
| Usability | UserTesting, Maze, Lookback |
| Surveys | Typeform, SurveyMonkey |
| Analytics | Mixpanel, Amplitude, Hotjar |
| Card Sorting | OptimalSort, Maze |
| Repository | Dovetail, Condens, Notion |
| Prototyping | Figma, ProtoPie |

---

## Sources

- [User Interviews - State of User Research 2025](https://www.userinterviews.com/state-of-user-research-report)
- [Nielsen Norman Group - Research Methods](https://www.nngroup.com/articles/which-ux-research-methods/)
- Portigal, S. (2013). "Interviewing Users"
- Kuniavsky, M. (2012). "Observing the User Experience"
- [Maze - UX Research Methods](https://maze.co/guides/ux-research/)
