# Positive vs. negative loops: system-dynamics reference

A reference complementing `feedback-loop-positive-vs-negative` with system-dynamics vocabulary and case studies.

## System-dynamics vocabulary

From Forrester's *Industrial Dynamics* and the broader system-dynamics tradition:

- **Stock**: a quantity that accumulates over time (users, money, inventory, attention).
- **Flow**: the rate at which a stock changes (sign-ups per day, churn per month).
- **Reinforcing loop** (positive): one variable's change amplifies the next variable in the loop.
- **Balancing loop** (negative): one variable's change is counteracted by another.
- **Delay**: time between an action and its visible effect; delays cause oscillation in feedback loops.

## The football-helmet case in detail

The book's example illustrates a *runaway positive loop*:

```
[ Better helmets ] →+ [ Players feel safer ]
                          ↓+
                     [ More aggressive tackling ]
                          ↓+
                     [ More head/neck injuries ]
                          ↓+
                     [ Designers add more padding ]
                          ↓+
                     [ Better helmets ] (loop closes)
```

No balancing mechanism (rules against helmet-first tackling) existed; the loop ran unchecked for decades. Eventually moderating mechanisms were added (rule changes, public-health awareness, technique training).

The pattern recurs: a well-intentioned design intervention triggers behavior changes that defeat the original goal.

## Software cases

### Filter bubbles

```
[ User clicks recommendation ] →+ [ Recommender boosts similar content ]
                                       ↓+
                                  [ User sees more similar content ]
                                       ↓+
                                  [ User clicks more similar content ]
```

Without a diversity-injection balancing loop, the user's content world narrows.

### Engagement-as-metric

```
[ Optimize for time-on-app ] →+ [ Add hooks: notifications, streaks, autoplay ]
                                       ↓+
                                  [ Users spend more time ]
                                       ↓+
                                  [ Metric improves ]
                                       ↓+
                                  [ More resources to optimize for engagement ]
```

The metric improves; user wellbeing may decline. Without a wellbeing-tracking balancing loop, the optimization continues past the user's interest.

### Spam invitation systems

```
[ User signs up ] →+ [ Prompted to invite contacts ]
                          ↓+
                     [ Contacts receive invitation ]
                          ↓+
                     [ Some sign up ]
                          ↓+
                     [ More invitations sent ]
```

Some early-2010s products produced viral growth through aggressive invitation prompts; the loops worked but generated spam complaints, regulatory attention, and user resentment. Modern equivalents add explicit consent and rate limits.

## Healthy patterns: paired loops

Sustainable systems pair positive and negative loops:

### Recommendation + diversity

A positive loop amplifies similar content; a balancing loop injects unfamiliar content periodically. Spotify's "Discover Weekly" and similar features explicitly balance the recommender's tendency to converge.

### Growth + quality

A positive growth loop drives signups; a balancing quality loop (onboarding requirements, fraud detection, paid conversion) maintains user quality.

### Engagement + wellbeing

Apple's Screen Time and Android's Digital Wellbeing add explicit moderating loops to the engagement-driven mobile environment. Whether they're enough is debated, but the design move is right: when a system has strong positive engagement loops, build moderating loops in.

## Diagnostic questions

For any system with a positive feedback loop:

1. **What's the loop optimizing for?**
2. **Whose interest does that metric serve?**
3. **What's the balancing loop?**
4. **What does runaway look like at 1 year? 5 years?**
5. **Who is harmed if runaway happens?**

If answers reveal harms or have no balancing mechanism, redesign.

## Resources

- **Wiener, N.** *Cybernetics* (1948).
- **Forrester, J. W.** *Industrial Dynamics* (1961).
- **Senge, P.** *The Fifth Discipline* (1990) — popularized system-dynamics thinking for management.
- **Meadows, D.** *Thinking in Systems* (2008) — accessible introduction.
- **Center for Humane Technology** (humanetech.com) — modern advocacy on feedback-loop design and harm.
- **Doctorow, C.** writings on enshittification — runaway positive loops in platform economics.
