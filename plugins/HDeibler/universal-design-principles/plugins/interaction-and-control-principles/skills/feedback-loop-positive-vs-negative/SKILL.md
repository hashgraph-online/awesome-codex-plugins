---
name: feedback-loop-positive-vs-negative
description: 'Use this skill when designing system architecture or product mechanics that involve feedback loops at a higher level than UI state — recommendation engines, gamification, growth mechanics, engagement systems, or any system where one user action affects subsequent actions in compounding or stabilizing ways. Trigger when designing growth loops, retention features, or system dynamics; when reviewing a feature for unintended consequences; when discussing engagement vs. wellbeing tradeoffs. Sub-aspect of `feedback-loop`; read that first.'
---

# Positive vs. negative feedback loops

The book's distinction between *positive* (amplifying) and *negative* (stabilizing) feedback loops scales beyond UI states to system-level mechanics. Most product UI feedback is negative (stabilizing). But growth, engagement, and recommendation systems often use positive loops — and those carry risks the football-helmet case illustrates.

## Positive feedback loops

A positive loop's response amplifies the original input. More leads to more.

Examples in software:

- **Recommendation engines**: a click teaches the system; the system shows more like it; the user clicks more.
- **Streak counters**: each day of use raises the cost of breaking the streak.
- **Viral growth loops**: each new user can invite others; each invitation creates more users.
- **Network effects**: more users → more value → more users.
- **Engagement bait**: more time spent → more revenue → more reasons to optimize for engagement.

Positive loops are powerful. They produce dramatic growth, viral effects, and addictive engagement. They also produce runaway dynamics if uncoupled from a moderating mechanism.

### When positive loops harm

The book's example: 1950s football. New plastic-with-padding helmets felt safer; players tackled more aggressively; head/neck injuries rose; designers added more padding; aggression rose further. The loop ran unchecked because no moderating mechanism (rules against helmet-first tackling) existed until much later.

Software analogs:

- **Filter bubbles**: recommendation engines that converge users on increasingly narrow content.
- **Engagement-as-metric**: products optimized for time-on-app eventually optimize for hooks at the expense of user welfare.
- **Streak anxiety**: features designed to drive habit can become sources of stress; users feel obligated rather than served.
- **Notification escalation**: each user disengagement is met with more aggressive notifications; users disengage further.

The pattern: the loop's metric and the user's welfare diverge. The system optimizes for the metric; the user suffers.

## Negative feedback loops

A negative loop's response counteracts the original input, returning the system toward equilibrium.

Examples:

- **Auto-save**: every edit triggers save; the system stays in a known-saved state.
- **Form validation**: invalid input → flag → user corrects → equilibrium.
- **Rate limiting**: too many requests → throttle → user adjusts pace → equilibrium.
- **Auto-correct**: typos detected → correction offered → text returns to "intended" state.
- **Thermostatic feedback** in any responsive UI: oscillates around a desired state.

Most product UI is appropriately negative-loop dominant. The user acts; the system stabilizes; the user trusts the system.

## Pairing loops: positive moderated by negative

Healthy systems often pair the two: a positive growth loop moderated by a negative quality loop.

Examples:

- **Recommendation system + diversity injection**: the recommender amplifies similar content; the diversity mechanism injects unfamiliar content to prevent over-narrowing.
- **Engagement metrics + friction**: a product driven by engagement adds explicit "are you done?" prompts to nudge users away when they've spent too long.
- **Viral growth + spam controls**: invitation features paired with rate limits and consent mechanisms.

The discipline: when introducing a positive loop, ask "what's the moderating loop that prevents runaway?" If you don't have an answer, the positive loop will eventually produce harms you didn't predict.

## Designing loops responsibly

A few questions to ask before introducing a positive loop:

1. **What metric does this loop optimize for?**
2. **Does the metric track user welfare, or only platform welfare?**
3. **What's the moderating mechanism?**
4. **What does runaway look like?**
5. **Who is harmed if the loop runs unchecked?**

If the answers reveal harms, redesign the loop or add explicit moderation.

## Worked examples

### Example 1: a recommendation system with diversity

```
[ User clicks article ]
        ↓
[ Recommender notes click ]
        ↓
[ Show more like it ]   ← positive loop
        ↓
[ Track diversity score ] ← moderating loop
        ↓
[ When diversity drops, inject unfamiliar content ]
```

The positive loop drives engagement; the diversity loop prevents narrowing.

### Example 2: a growth loop with consent guardrails

```
[ User signs up ]
        ↓
[ Prompt to invite friends ]   ← positive growth
        ↓
[ Friends sign up ]
        ↓
[ Cap invitations per day ]    ← moderating loop
        ↓
[ Allow opt-out for invitations ]
```

The growth loop drives signups; the cap and opt-out prevent spam.

### Example 3: an engagement system with wellbeing checks

```
[ User opens app ]
        ↓
[ Track session time ]
        ↓
[ After threshold, suggest break ]   ← moderating loop
        ↓
[ User wellbeing prompts ]           ← explicit pause
```

Apps designed for sustainable use rather than maximum engagement build moderating loops in.

## Anti-patterns

- **Pure positive loops in engagement**: gamified streaks with no off-ramp. Users feel trapped.
- **Recommender systems without diversity**: filter bubbles, echo chambers.
- **Growth loops without consent**: viral invitation systems that send messages without user knowledge.
- **Optimization for metrics that don't track user benefit**: time-on-app driven up at the expense of user wellbeing.
- **Loops that amplify already-skewed distributions**: rich-get-richer dynamics in social media (the user with 10,000 followers gets shown to more people; the user with 100 stays invisible).

## Heuristics

1. **The "what's the moderating loop?" check.** For each positive loop in your system, name the negative loop that prevents runaway. If you can't, design one.
2. **The runaway-scenario thought experiment.** Imagine the positive loop running unchecked for a year. What's the worst plausible outcome? Design against it.
3. **The metric-vs-welfare audit.** Does your loop's optimization metric track user welfare? If they diverge, the loop will eventually harm users.
4. **The opt-out check.** Can the user disengage from the loop? If not, you've trapped them.

## Related sub-skills

- **`feedback-loop`** (parent).
- **`feedback-loop-states-and-latency`** — loop implementation at the UI level.
- **`nudge`** (interaction) — small choice-architecture decisions that shape loops.
- **`operant-conditioning`** (interaction) — the psychology behind some positive engagement loops.

## Resources

- **Wiener, N.** *Cybernetics* (1948).
- **Forrester, J. W.** *Industrial Dynamics* (1961); *Urban Dynamics* (1969).
- **Senge, P.** *The Fifth Discipline* (1990) — systems thinking applied to organizations.
- **Center for Humane Technology** — modern advocacy on harm-aware loop design.
