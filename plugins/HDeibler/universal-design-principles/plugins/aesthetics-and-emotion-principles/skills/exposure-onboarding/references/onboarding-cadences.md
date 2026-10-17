# Onboarding cadences

Patterns for first-week onboarding designed to maximize exposure and build familiarity.

## Pattern: daily-habit cadence

Designed for products that benefit from daily use (meditation, journaling, exercise tracking, language learning).

**Day 1:** complete onboarding; immediate value experience (a 5-minute session, a short lesson, an initial entry).

**Day 2:** notification at the same time as Day 1; encourage return; deliver another small valuable experience.

**Day 3:** continued notification; vary the content slightly to maintain interest.

**Day 4–5:** reinforce the building habit with a small celebration ("You're on a 4-day streak!").

**Day 6–7:** maintain the cadence; introduce a new feature or deeper capability now that the user is engaged.

**Week 2 onward:** reduce notification cadence to maintenance level; the habit is forming.

This cadence works because daily exposure builds familiarity quickly and the daily ritual integrates the product into users' routines.

## Pattern: weekly-rhythm cadence

Designed for products that don't need daily use but benefit from weekly check-ins (analytics, financial summaries, content roundups, project updates).

**Day 1:** complete onboarding; deliver immediate value; tell users about the weekly cadence ("You'll get a summary every Monday").

**Day 8:** first weekly summary email/notification with personalized content from the past week.

**Day 15, 22, 29:** continued weekly summaries; refine based on what users engage with.

**Month 2 onward:** weekly cadence maintained; users have integrated the product into their weekly routine.

This pattern works for products where daily use would be overkill but weekly engagement is valuable.

## Pattern: trigger-driven re-engagement

Designed for products users come to when something specific happens (event-based products, on-demand services).

**Day 1:** complete onboarding; user knows what triggers will bring them back.

**When trigger occurs:** the product reaches out (notification, email) at the moment of relevance.

**Between triggers:** minimal contact; let the product wait for the next trigger.

This pattern works for products where the value is real but irregular. The exposure effect builds through the relevant moments rather than through daily ritual.

## Pattern: progressive-feature-disclosure cadence

Designed for products with depth that needs gradual introduction.

**Day 1:** complete onboarding; the user sees the simple-mode interface; completes a basic task.

**Day 2–3:** notifications introduce one new feature each, related to what the user has been doing.

**Day 4–7:** continued feature introductions; each tied to a real use case.

**Week 2:** by now, the user has been exposed to most of the product's capabilities; depth becomes available without overwhelming.

This pattern works for products that span novice and expert use. The early exposure is to the simple side; depth is introduced as familiarity builds.

## Pattern: social-driven re-engagement

Designed for products where other users are part of the value (social networks, collaboration tools, marketplaces).

**Day 1:** complete onboarding; connect to other users (invite friends, join groups, find collaborators).

**Day 2 onward:** notifications driven by other users' activity (someone replied, your team made progress, a new item appeared).

**Long-term:** the social connections become the return mechanism; the product is a venue for ongoing interaction.

This pattern is powerful but requires that other users actually exist and are active. Cold-start problems are real.

## Components of effective cadences

**Notifications:** the primary mechanism for bringing users back. Calibrate frequency carefully; over-notification is the most common failure.

**Email:** lower-frequency than notifications but valuable for richer content and specific engagement.

**In-product cues:** badges, streaks, progress indicators that give users a reason to return.

**Calendar / time-based:** scheduled events users can plan around (a weekly meeting, a daily session).

**External integration:** widgets on the home screen, watch faces, browser extensions that surface relevant content ambient.

## Calibrating notification frequency

Too few notifications: users forget the product exists; the exposure effect doesn't operate.

Too many notifications: users get annoyed; uninstall the app or disable notifications; the effect reverses.

The right level depends on:

- **Product type.** Daily-use products tolerate daily notifications. Occasional-use products need fewer.
- **Notification value.** A notification that brings something specific and valuable can be daily. A generic "come back" can be at most weekly.
- **User preferences.** Different users want different frequencies. Provide controls.
- **Time of day.** Notifications at appropriate moments (not in the middle of the night) maintain goodwill.

A starting heuristic: send the minimum number of notifications that achieves the engagement goal. Add more only if measurement shows users want them.

## Friction reduction for return

Each step of friction reduces return rate. The hierarchy:

**Highest friction (worst):** "Open browser, navigate to URL, log in, click around to find relevant content."

**Lower:** "Open the app, navigate to the relevant section."

**Even lower:** "Open the app to a homepage that shows what's new."

**Lower still:** "Tap a notification that opens directly to the relevant content."

**Lowest (best):** "See the relevant content surface ambient (widget, watch face, dashboard at-a-glance)."

For each return path your users take, find ways to move down the friction ladder. Each step improves return rate.

## Anti-patterns

**The "ghost town" cadence.** No re-engagement at all. Users complete onboarding and never come back unless they remember on their own.

**The "spammer" cadence.** Many notifications per day. Initial engagement spike, then mass uninstall.

**The "irrelevant" cadence.** Notifications that don't match user interests. Users disable notifications; you've lost the channel.

**The "fake urgency" cadence.** "Come back!! You're missing out!!" Users see through the artificial urgency and disengage.

**The "no value at the destination" cadence.** Notifications that drive users back to a product that doesn't deliver something new. Users feel tricked.

**The "rigid schedule" cadence.** Same notification at the same time every day regardless of context. Becomes background noise; loses effectiveness.

## Measuring success

Track metrics that reflect the exposure effect's operation:

- **First-week return rate.** What % of users return at least N times in the first week?
- **Habit formation rate.** What % of users have established a return pattern (daily, weekly, etc.) by day 30?
- **Long-term retention.** What % of users active at day 30 are still active at day 90 / 180 / 365?

If first-week return rate is low, the early exposure isn't happening. If habit formation rate is low, the product isn't sticking. If long-term retention is low despite habit formation, the product isn't continuing to deliver value.

Each metric points to a different problem; treat accordingly.

## Cross-reference

For redesign-related exposure issues, see `exposure-redesign-risk`. For the parent principle, see `exposure-effect`.
