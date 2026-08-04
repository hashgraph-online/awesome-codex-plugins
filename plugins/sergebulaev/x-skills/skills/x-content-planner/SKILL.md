---
name: x-content-planner
description: Generate a weekly X (Twitter) content plan from a theme, audience, and content pillars. Produces per-day recommendations (single tweet vs thread, X hook formula, angle, posting time, primary goal), a single-to-thread mix, daily reply and quote-tweet targets, and a goal-mix balance check across replies, reposts, likes, and bookmarks. Use when the user wants to plan a week of X content instead of ad-hoc posting. Not for drafting one tweet (use x-post-writer) or one thread (use x-thread-builder).
---

# X Content Planner

Produce a weekly X plan built around a pillar discipline and the faster cadence
X allows. Unlike LinkedIn, X rewards posting multiple times a day, so the plan
mixes single tweets, threads, and reply/quote-tweet targets.

## When to use

- User asks "plan my week on X" or "what should I post this week"
- User wants to escape ad-hoc posting and establish a rhythm
- Before a launch week (the plan aligns a product pillar)

## Input

- **Theme** (optional): e.g. "shipping our AI agent in public"
- **Audience description:** e.g. "indie builders, AI engineers, early founders"
- **Pillar mix** (optional): defaults to 40% Build-in-Public / 30% Insight /
  20% Engagement / 10% Promotion
- **Posting cadence** (optional): defaults to 2 posts/day on weekdays
- **Voice samples** (optional): past tweets for voice calibration

## Output

A markdown plan with:

### 7-day calendar

| Day | Slot | Type | Pillar | Formula | 1-line angle | Goal | Time |
|---|---|---|---|---|---|---|---|
| Mon | AM | single | Insight | X1 One-Liner Contrarian | "speed is a revenue line item" | reposts | 9:30 AM |
| Mon | PM | reply block | Engagement | R-templates | 5 builder threads | replies | 2:00 PM |
| Tue | AM | thread | Build-in-Public | X10 How-I Teardown | "how we cut deploy 40m to 6m" | bookmarks | 10:00 AM |
| Tue | PM | single | Insight | X2 Data-Point | "1.3s page = 2.4x conversion" | bookmarks | 1:30 PM |
| Wed | AM | thread | Insight | X7 Listicle-Thread | "9 landing-page mistakes" | bookmarks | 9:30 AM |
| Thu | AM | single | Build-in-Public | X3 Confession | "the metric we hid for a month" | replies | 10:00 AM |
| Fri | AM | single | Engagement | X6 Relatable | "friday deploy energy" | likes | 9:00 AM |

(The skill fills real angles from the theme. Weekends are optional and skew to
story threads or relatable singles.)

### Daily reply and quote-tweet targets

For each day:
- **5-10 accounts to engage** (names or archetypes: "peer builders at 2-20k",
  "AI founders shipping in public", "the creators whose threads you bookmark")
- **Template to apply** (R1 answer, R2 concede-sharpen, R3 extend, R5 value-add quote)
- **Target:** 5-10 substantive replies per day. On X, replies on other people's
  posts drive more profile visits and follows than your own posts early on.

### Weekly balance check

- [ ] Single-to-thread mix roughly 60/40 (singles for cadence, threads for depth)
- [ ] At least 1 build-in-public post (real number from your work)
- [ ] At least 1 bookmark-bait post (list, framework, or how-to)
- [ ] At least 1 engagement/reply-heavy day
- [ ] No pillar over 60% of the week's posts
- [ ] No formula repeated more than twice in the week
- [ ] Goal mix spread (see below): not every post chases the same signal

## Goal mix (balance the week)

Every formula earns a primary signal. A week that is all bookmark-bait or all
reply-bait reads as engineered. Spread the goals:

| Goal | Formulas | Weekly target |
|---|---|---|
| Replies | X3, X9, X1 | at least 1 |
| Reposts | X1, X4, X8 | at least 1 |
| Likes | X6, X8 | at least 1 |
| Bookmarks | X2, X5, X7, X10 | at least 2 (bookmarks are the underrated lever) |

## Rules

- **2-4 posts/day is fine on X.** It moves faster than LinkedIn and does not
  punish frequency the same way. Quality still gates: do not pad to hit a count.
- **Single-to-thread mix ~60/40.** Singles keep you present daily; threads earn
  the bookmarks and follows.
- **Replies are a content type, not an afterthought.** Block reply time daily;
  early growth on X comes more from replies than from posts.
- **Weekday mornings (9-11 AM local) and a 1-3 PM bump** are the primary windows;
  8-11 PM works for the dev/build crowd.
- **Promotion pillar max 1-2 posts/week.** Overuse kills trust.
- **One formula per slot, varied across the week.** Do not stack three X7 threads.

## Formula -> pillar mapping

| Pillar | Preferred formulas |
|---|---|
| Build-in-Public | X3 Confession, X10 How-I Teardown, X8 Story Thread |
| Insight | X1 Contrarian, X2 Data-Point, X7 Listicle-Thread, X9 Curiosity-Gap |
| Engagement | X6 Relatable, X4 Quote-Tweet, reply templates |
| Promotion | X10 (results that imply the product), X2 (your own data) |

## Steps

1. Gather inputs. Ask for theme, audience, pillar preferences if not provided.
2. Validate the pillar mix sums to 100%; warn if any pillar is over 60%.
3. For each day and slot, pick: type (single/thread/reply block), pillar,
   formula (do not over-repeat), angle, posting time (audience timezone), goal.
4. Add daily reply/quote-tweet targets with a suggested template.
5. Run the weekly balance check and the goal-mix check; flag anything missing.
6. Return as markdown, plus optional JSON for import.

## Example

See `references/example-week.md` for a filled-in 7-day plan.

## Files

- `SKILL.md` - this file
- `references/example-week.md` - worked 7-day plan
- `references/pillars-framework.md` - the X pillar discipline explained

## Related skills

- `x-post-writer` - draft each single tweet from the plan
- `x-thread-builder` - draft each thread from the plan
- `x-reply-drafter` - execute the daily reply targets
- `x-hook-extractor` - study competitors' posts while planning
