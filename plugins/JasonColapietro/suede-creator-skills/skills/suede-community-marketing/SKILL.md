---
name: suede-community-marketing
description: "Use when asked \"plan our community launch\" or to audit or drive product community growth. Suede AI returns member identity, platform choice, a seeding plan, rituals, moderation paths, ambassador design and health metrics with denominators. NOT FOR: public social content (use suede-social), referral payouts (use suede-referrals), or customer interviews (use suede-customer-research)."
metadata:
  display-name: "Suede AI Community Marketing Skills"
  version: 2.1.0
---

# Suede AI Community Marketing Skills

Use this community-growth playbook to create genuine member value and measurable business outcomes without manufacturing engagement.

## Compatibility

Any text-capable agent with the product brief and available community evidence. Public research needs web access; drafting needs no community-platform account or posting permissions.

## Before You Start

**Check for product marketing context first:**
If `.agents/product-marketing.md` exists (or `.claude/product-marketing.md`, or the legacy `product-marketing-context.md` filename, in older setups), read it before asking questions. Use that context and only ask for information not already covered.

Understand the situation (ask if not provided):

1. **What is the product or brand?**: What problem does it solve, who uses it
2. **What community platform(s) are in play?**: Discord, Slack, Circle, Reddit, Facebook Groups, forum, etc.
3. **What stage is the community at?**: Pre-launch, 0–100 members, 100–1k, scaling, or established
4. **What is the primary community goal?**: Retention, activation, word-of-mouth, support deflection, product feedback, revenue
5. **Who is the ideal community member?**: Role, motivation, what they hope to get from joining

Work with whatever context is available. If key details are missing, make reasonable assumptions and flag them.

---

## Community Strategy Principles

### Build around a shared identity, not just a product

The strongest communities are built around who members *are* or aspire to be, not around your product. Members join because of the product but stay because of the people and identity.

Example: r/homelab: the identity is tinkerers who self-host, and every ritual,
channel, and recognition mechanic in it reinforces that self-image.

Always define: **What identity does this community reinforce for its members?**

### Value must flow to members first

Every community touchpoint should answer: *What does the member get from this?*

- Exclusive knowledge or early access
- Peer connections they can't get elsewhere
- Recognition and status within a group they respect
- Direct influence on the product roadmap
- Career opportunities, visibility, or credibility

---

## Playbooks by Goal

### Launching a Community from Zero

1. **Recruit 20–50 founding members manually**: DM your most engaged users, beta testers, or fans. Don't open publicly until there is baseline activity.
2. **Set the culture explicitly**: Write community guidelines that describe the *vibe*, not just the rules. What does great participation look like here?
3. **Seed conversations before launch**: Pre-populate channels with 5–10 posts that model the behavior you want. Questions, wins, resources.
4. **Do things that don't scale at first**: Reply to every post. Welcome every new member by name. Host a weekly call. You are buying social proof.
5. **Define your core loop**: What action do you want members to take weekly? Make it easy and reward it publicly.

### Growing an Existing Community

1. **Audit where members drop off**: Are people joining but not posting? Posting once and disappearing? Identify the leaky stage.
2. **Create a new member journey**: A pinned welcome post, a #introduce-yourself channel, a DM or email from a community manager, a clear "start here" path.
3. **Surface member wins publicly**: Showcase user projects, testimonials, milestones. This reinforces identity and signals that participation has rewards.
4. **Run recurring community rituals**: Weekly threads (e.g., "What are you working on?"), monthly AMAs, seasonal challenges. Rituals create habit.
5. **Identify and invest in power users**: participation is usually heavily
   skewed toward a small minority (Inferred; verify against this community's own
   posts-per-member distribution before quoting a ratio). Give the observed top
   contributors recognition, early access, moderator roles, or product input.

### Building a Brand Ambassador / Advocate Program

1. **Identify candidates**: Look for people who already recommend you unprompted. Check reviews, social mentions, community posts.
2. **Make the ask personal**: Don't send a generic form. Reach out 1:1 and explain why you chose them specifically.
3. **Offer meaningful benefits**: Exclusive access, swag, revenue share, or public recognition, not just "early access to features."
4. **Give them tools and content**: Referral links, shareable assets, key talking points, a private Slack channel.
5. **Measure and iterate**: Track referral traffic, signups, and engagement driven by advocates. Double down on what works.

### Community-Led Support (Deflection + Retention)

1. **Create a searchable knowledge base** from top community questions
2. **Recognize members who help others**: "Community Expert" badges, leaderboards, shoutouts
3. **Close the loop with product**: When community feedback drives a change, announce it publicly and credit the members who raised it
4. **Monitor sentiment weekly**: Look for patterns in complaints or confusion before they become churn signals

---

## Platform Selection Guide

| Platform | Best For | Watch Out For |
|----------|----------|---------------|
| Discord | Developer, gaming, creator communities; real-time chat | High noise, hard to search, onboarding friction |
| Slack | B2B / professional communities; familiar to SaaS buyers | Free tier limits history; feels like work |
| Circle | Creator or course-based communities; clean UX | Less organic discovery; requires driving traffic |
| Reddit | High-volume public communities; threads rank in Google and get quoted in AI answers | You don't own it; strict self-promotion rules |
| Facebook Groups | Consumer brands; older demographics | Declining organic reach; algorithm dependent |
| Forum (Discourse) | Long-form technical communities; indexable, owned answers | Slower velocity; higher effort to post |

### Searchable community knowledge

Google shows forum and community threads in a "Discussions and forums" result
block, and AI answer engines quote public threads. Chat platforms (Discord,
Slack) are not indexed, so the answers members give there disappear from
search.

- Run support and how-to questions in an indexable space (a Discourse forum or
  a public docs Q&A) and keep chat for real-time conversation.
- Turn the best chat answers into public pages each week, with the helper's
  permission and credit.
- Thread titles phrase the question the way a buyer would search it; the
  accepted answer comes first.
- On Reddit and other communities the brand does not own, participate as a
  named, disclosed employee, follow each subreddit's rules, and never seed
  fake recommendations.

---

## Community Health Metrics

Track these signals weekly. Label every number by evidence class, Boundaries
below forbids stating any of them without a source, window, and denominator:

- **Observed**: read directly from the platform's admin view or export. Name
  the view and the date pulled.
- **Computed**: derived from observed values. Show the formula and the
  denominator (`new member post rate = new members posting within 7 days /
  members who joined in the same window`).
- **Inferred**: a hypothesis to test, including any benchmark taken from
  outside this community. Never word it as this community's fact.
- **Unknown**: the platform does not expose the measure. State what would
  resolve it.

Metrics:

- **DAU/MAU ratio**: Stickiness (Computed: daily actives / monthly actives).
  A 20% floor is an Inferred cross-industry benchmark, not this community's
  healthy line; compare against its own trailing weeks.
- **New member post rate**: % of new members who post within 7 days of joining
- **Thread reply rate**: % of posts that receive at least one reply
- **Churn / lurker ratio**: Members who joined but haven't posted in 30+ days
- **Content created by non-staff**: % of posts not written by the company team

**Warning signs:**
- Most posts are from the company team, not members
- Questions go unanswered for >24 hours
- Engagement concentrates in a handful of accounts: compute the share of posts
  from the top 5 posters over a stated window before calling it a warning
- New members stop posting after their intro message

---

## Output Formats

Depending on what the user needs, produce one of:

- **Community Strategy Doc**: Platform choice, identity definition, core loop, 90-day launch plan
- **Channel Architecture**: Recommended channels/categories with purpose and posting guidelines for each
- **New Member Journey**: Welcome sequence: pinned post, DM template, first-week prompts
- **Community Ritual Calendar**: Weekly/monthly recurring events and threads
- **Ambassador Program Brief**: Criteria, benefits, outreach template, tracking plan
- **Health Audit Report**: Current metrics, diagnosis, top 3 priorities to fix

Always be specific. Generic advice ("be consistent," "provide value") is not useful. Give the user something they can act on today.

### Community Strategy Doc: exact headings

```markdown
# <Community name>: Strategy

## Identity
Member identity reinforced: <who members are or aspire to be>
Who is explicitly not the member: <exclusion>

## Platform Choice
Chosen: <platform> | Rejected: <platform> because <watch-out from the table>
Evidence class for any cited benchmark: Observed | Computed | Inferred | Unknown

## Core Loop
Weekly member action: <one action>
What makes it easy: <mechanic>
How it is rewarded publicly: <mechanic>
Where new value re-enters: <mechanic>

## Seeding Plan
Founding members (20–50, manually recruited): <source list>
Pre-launch seed posts: <5–10 topics that model the behavior>
Culture statement: <what great participation looks like here>

## 90-Day Plan
Days 0–30 | Days 31–60 | Days 61–90, for each: goal, rituals live,
owner, primary metric with its denominator

## Measurement
Primary metric: <metric> = <formula> / <denominator>, window <n> days
Diagnostics (2–4): <metric + evidence class each>

## Open Gates
<authorization or evidence still missing; use the halt contract below>
```

The other five deliverables use these headings:

- **Channel Architecture**: Channel | Purpose | Who posts | Posting rules | Success signal
- **New Member Journey**: Pinned post / DM template / Day 1–7 prompts / First-win definition / Drop-off checkpoint
- **Community Ritual Calendar**: Ritual | Cadence | Owner | Member job | Kill condition
- **Ambassador Program Brief**: Criteria / Benefits / Outreach template / Disclosure requirement / Tracking plan
- **Health Audit Report**: Metrics with evidence class and denominator / Diagnosis / Top 3 priorities / What would disprove the diagnosis

---

## Halt Contract

Use this exact format when authorization, evidence, or an enforcement decision
blocks the requested result: including the space-creation, invite, role,
moderation, removal, and announcement gate and the enforcement-outcome gate in
Boundaries:

```text
HALT: <one-line blocker>
Why it blocks: <specific missing authority or evidence>
Resolve with:
1. <option>
2. <option>
3. <option, when useful>
Waiting for: <the exact item or approval>
```

Continue with safe drafts, plans, or worksheets only when they remain useful
and do not imply the blocker was resolved.

---

## Boundaries

- Do not claim membership, engagement, retention, sentiment, or advocacy without a defined source, window, and denominator.
- Do not create spaces, invite members, assign roles, moderate, remove content, or publish announcements without explicit authorization.
- Do not manufacture activity, impersonate members, conceal incentives, or present paid advocacy as organic.
- Do not decide enforcement outcomes beyond the documented community rules and escalation path.

## Routing

- Need referral or ambassador incentives -> use `suede-referrals`.
- Need public social content -> use `suede-social`.
- Need member-language research -> use `suede-customer-research`.
- Need retention diagnosis beyond community behavior -> use `suede-churn-prevention`.
- Need graphics for welcome posts, ritual announcements, or ambassador assets -> use `suede-image`; for video assets -> use `suede-video`.
- Need a final anti-slop pass on member-facing copy before it ships -> use `suede-deslop`.
- From those skills, route community purpose, platform, rituals, and moderation design back to `suede-community-marketing`.

## Worked contract

[Worked contract](references/usage-contract.md) gives a bounded input, expected output and failure check for this workflow.
