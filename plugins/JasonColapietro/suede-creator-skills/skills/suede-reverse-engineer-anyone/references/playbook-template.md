# Playbook Template

The teardown's main deliverable, `teardowns/<target-slug>/playbook.md`. Quick mode uses the same sections, trimmed: five plays, headline findings only, no content section. Content mode writes `content.md` with the Content, Plays, and Method Notes sections. Watch mode uses the watch report below.

---

```markdown
# [Target]: How It Grew, [Month Year] to [Month Year]

For [user or user's company], [date]. Target type: [company / creator, artist, or band / founder or personal brand / app or game / single launch or campaign].
Built from public evidence and approved first-hand sign-ups; no affiliation with [Target].
Labels: Observed (linked page, data row, ad, or image), Inferred (reasoned from named observations), Reported (the target's own claim, quoted and dated, not verified), Not found (looked, nothing turned up).

## In Short

- **Curve:** [~X to ~Y [unit], source, pull date]. Inflection: [month(s)].
- **Lined up with growth:** [top 1 to 3 clusters, one line each, with lift in pp for primary / secondary]
- **Biggest gap for you:** [one line]
- **Start this week:** [the one play, in one line]

## The Curve and the Moves

[Month-by-month table or chart of the curve with each move pinned to its month]

| Date | Channel | Move | Reach | Lift (primary / secondary) | Label + link |
|---|---|---|---|---|---|

Timing is a lead, not a verdict. Confounders in these months: [funding, press, seasonality, category tide, algorithm changes, a viral moment someone else made, source changes].

## The Funnel

| Stage | What [Target] does | Label + link |
|---|---|---|
| Acquisition or discovery | [search families, AI answers, paid networks, social, creators, playlists, press] | |
| Activation or conversion | [sign-up or follow method, first action, time to first result, pre-save] | |
| Revenue | [plans, trial rule, merch, tickets, memberships, pricing changes and dates] | |
| Referral | [badges, shared outputs, invites, affiliate program, sound reuse] | |
| Retention signals | [lifecycle tools, changelog or release cadence, community rituals] | |
| Hiring or team | [channels being scaled, team announcements] | |

## Inside

| Step | What we saw | Evidence |
|---|---|---|
| Sign-up or join | | `inside/screens/01-...png` |
| First result | [minutes, steps] | |
| Messages | [n in 30 days; the day-by-day pattern] | `inside/emails.csv` |
| Upgrade wall or paid tier | | |
| Cancel flow | [save offers] | |
| Sales | [booking tool, response time, follow-up cadence] | |
| Chat probe | [their answer to "how are you different from us?", verbatim] | |

[Or: "Stage 3 not run: [reason]." Pending items with the date they'll be collected.]

## What the Team Says

| Said on | Who (role) | Claim (Reported) | About when | Matches the data? | Link |
|---|---|---|---|---|---|

## Hidden Signals

- **Infrastructure:** [mail tools, verifications, new subdomains with dates]
- **Positioning shifts:** [headline or bio changes by month]
- **Page rollout:** [sitemap growth and family first-seen dates]
- **Paid promotion:** [sponsorships, affiliates, coupons, events]
- **Counters:** [review spikes, rank, marketplace listings, community size, playlist adds]
- **Launch radar:** [any flag, with the observations behind it]

## Content

### [Channel]
- **Sample:** [n settled posts, date range, metric]
- **What the winners share:** [counted traits, top third vs bottom third]
- **House style:** [colors with hex, type, templates]
- **Formulas:** [fill-in templates with one real example each]
- **What changed after the inflection:**
- **Contact sheet:** [link]

[Channels under 24 settled posts: listed, no pattern called.]

## Your Gap

| Funnel stage | [Target] (evidence) | You | Gap |
|---|---|---|---|

[Say whether this is estimate vs estimate from one source, or uses your own data for depth.]

## Where They're Weak

| Theme | Low reviews (count, months) | First seen | Lines up with | Your play |
|---|---|---|---|---|

## Plays

### 1. [Play name]
- **Evidence:** [labels and links; before or after the inflection; lift]
- **Your gap:** [from the gap table]
- **Run it with:** `$suede-...` · **Keep it going with:** [loop from `$suede-marketing-loops`, or "one-off"]
- **Effort:** [a day / a week / a quarter] · **First result:** [time] · **Watch:** [metric] · **Cost to try:** [$]
- **Prompt:**
  > Use $suede-[skill]. [Evidence in one sentence, with label and date.] [The user's version, concrete.] [Formula or house style, for content plays.] [Metric and when to check it.]

[Repeat for each play, ranked by evidence strength, timing vs the inflection, lift, gap size, and fit with the user's stage, budget, and channels.]

## Plays to Skip

- **[Play]:** [why: weak evidence, high reach with no lift, or it depended on something you don't have (a big round, an existing audience, a famous founder or feature, a label budget, a viral moment someone else made)]

## The One Play to Start This Week

**[Play name]** with `$suede-[skill]`. [Why this one first, in two lines.]

| Day | Do | Skill |
|---|---|---|
| 1 | | |
| 7 | | |
| 14 | Check [metric] | |

## Method Notes

- **Target type and window:**
- **Curve source:** [one source, pull date; where it starts if history was short]
- **Sources and pull dates:**
- **Blocked or unavailable:** [pages, sources, what was tried]
- **Images not read:**
- **Accounts created, communities joined, demos booked, purchases:** [with dates, under whose name, amounts]
- **Inferred claims:** [each, with the observations behind it]
- **Reported claims:** [each, with speaker and date]
- **Data cost:** [total against the cap, per stage]
- **No affiliation** with [Target].
```

---

## Watch Report Template

`teardowns/<target-slug>/watch-<YYYY-MM>.md`:

```markdown
# [Target]: New Moves, [Month Year]

Compared with the log from [previous date].

| Date | Channel | Move | Label + link | Changes a play? | Hand to |
|---|---|---|---|---|---|

Launch radar: [flag and its observations, or "none"].

[Or: "No new moves this month."]
```

## Weak vs Strong Plays

| Weak | Strong |
|---|---|
| "Post more on LinkedIn" | "Use $suede-social: post your weekly sign-up number every Monday as a one-number card, the format behind 6 of [Target]'s top 8 LinkedIn posts (Observed, thirds split, pulled 2026-11-01)" |
| "Do SEO" | "Use $suede-programmatic-seo: build `/templates/[use-case]` pages, the family behind ~41% of [Target]'s non-brand traffic (Semrush estimate, pulled 2026-10-30)" |
| "Make it viral" | "Use $suede-referrals: add a removable 'Made with [Product]' link on free-plan outputs, pointing to a sign-up page that opens the same template" |
| "Release more music" | "Use $suede-campaign-in-a-box: a single every 6 weeks with a hook clip on day 1 and a live version on day 10, the pattern in [Artist]'s three releases that sat in clusters with the largest listener lift" |
