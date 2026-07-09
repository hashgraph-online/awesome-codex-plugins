# Launch Strategy — Product Launch Playbook

> A disciplined launch process turns product releases into measurable growth events. This playbook covers the full lifecycle from planning through post-launch optimization.

---

## Three-Tier Launch Framework

Not every release deserves the same investment. Categorize launches to allocate effort appropriately.

| Dimension | Tier 1: Major Launch | Tier 2: Feature Launch | Tier 3: Minor Update |
|---|---|---|---|
| **Scope** | New product, major rebrand, platform shift | Significant new capability or module | Bug fixes, UI tweaks, incremental improvements |
| **Lead time** | 8-12 weeks | 4-6 weeks | 1-2 weeks |
| **Cross-functional teams** | Product, Marketing, Sales, CS, PR, Leadership | Product, Marketing, Growth | Product, Marketing |
| **External PR** | Press embargo, media outreach, analyst briefing | Blog post, select media pitches | Changelog entry, in-app notification |
| **Customer communication** | Email to full list, webinar, demo event | Email to relevant segments, in-app announcement | In-app tooltip or banner |
| **Sales enablement** | New pitch deck, battle cards, training sessions | Feature one-pager, FAQ document | Internal Slack update |
| **Content assets** | Landing page, video, case study, blog series | Blog post, help docs, short video | Help doc update |
| **Success metrics** | Sign-ups, revenue impact, press coverage, NPS | Feature adoption rate, engagement lift | Bug resolution rate, satisfaction score |
| **Examples** | Figma launching FigJam, Notion launching AI | Slack launching Huddles | Dashboard loading speed improvement |

---

## Product Hunt Launch Guide

### Pre-Launch Preparation (2-4 Weeks Before)

| Task | Details | Timeline |
|---|---|---|
| Research top launches in your category | Study taglines, descriptions, and first comments of successful launches | -4 weeks |
| Recruit a credible Hunter | Find someone with 1,000+ followers on Product Hunt; reach out personally | -3 weeks |
| Build a supporter list | 200+ people who will upvote, comment, and share on launch day | -3 weeks |
| Prepare assets | Thumbnail (240x240), gallery images (5-8 screenshots), video (optional but recommended) | -2 weeks |
| Write tagline and description | Tagline: 60 chars max, clear and punchy. Description: problem → solution → proof | -2 weeks |
| Draft first comment | Founder story, why you built this, what makes it different. Personal and authentic. | -1 week |
| Prepare launch day team | Assign roles: comment responder, social media, supporter coordinator | -1 week |

### Launch Day Execution

- [ ] Launch at 12:01 AM PST (Product Hunt resets daily)
- [ ] Post founder's first comment immediately after listing goes live
- [ ] Send first wave of notifications to supporter list (personal messages, not mass blast)
- [ ] Share on Twitter/X with compelling hook and Product Hunt link
- [ ] Post in relevant communities (Slack groups, Discord, Reddit — check rules first)
- [ ] Respond to every comment within 30 minutes
- [ ] Send second wave of notifications at 9 AM PST (US waking up)
- [ ] Share progress updates on social media throughout the day
- [ ] Send third wave at 12 PM PST if momentum is building
- [ ] Thank supporters publicly in comments and social posts
- [ ] Monitor and respond to questions until midnight PST

### Post-Product Hunt

- [ ] Send thank-you email to all supporters within 24 hours
- [ ] Add "Featured on Product Hunt" badge to website (if applicable)
- [ ] Create blog post summarizing the launch and results
- [ ] Follow up with every lead generated from Product Hunt
- [ ] Analyze traffic and conversion data from launch day

---

## Waitlist Mechanics

### Waitlist Strategy

| Component | Standard Waitlist | Viral Waitlist | VIP Waitlist |
|---|---|---|---|
| Sign-up | Email only | Email + share to move up | Application with qualification criteria |
| Position visibility | Hidden or shown | Shown with "move up" mechanic | Acceptance/rejection notification |
| Incentive to share | None | Higher position for referrals | Early access for qualified applicants |
| Communication | Periodic updates | Real-time position updates | Personalized outreach |
| Best for | Simple interest capture | Pre-launch buzz generation | High-end or limited-capacity products |
| Tools | Mailchimp, ConvertKit | Viral Loops, Waitlist.me, ReferralHero | Typeform + custom CRM workflow |

### Waitlist Email Sequence

| Email | Timing | Content |
|---|---|---|
| Welcome | Immediate | Confirm position, explain what they're getting, set expectations |
| Social proof | Day 3 | "X people joined after you" — create urgency |
| Behind the scenes | Day 7 | Founder story, product preview, build connection |
| Referral nudge | Day 10 | "Move up the list by inviting friends" (for viral waitlists) |
| Sneak peek | Day 14+ | Exclusive preview content, screenshots, or demo |
| Access granted | Launch day | Clear CTA, onboarding instructions, limited-time offer |

---

## Beta Program Design

### Beta Types

| Beta Type | Audience | Duration | Feedback Method |
|---|---|---|---|
| Closed Alpha | Internal team + advisors | 2-4 weeks | Direct Slack/meetings |
| Private Beta | Hand-picked power users (50-200) | 4-8 weeks | In-app feedback widget, weekly surveys |
| Open Beta | Anyone who signs up | 2-4 weeks | Community forum, in-app feedback, analytics |
| Dogfooding | Entire company uses product daily | Ongoing | Internal bug reports, feature requests |

### Beta Feedback Collection

- [ ] In-app feedback button (always visible during beta)
- [ ] Weekly NPS or CSAT micro-survey (1-2 questions)
- [ ] Dedicated Slack or Discord channel for beta participants
- [ ] Bi-weekly user interviews with 5-10 active beta users
- [ ] Session recordings (with consent) via Hotjar, FullStory, or LogRocket
- [ ] Automated bug reporting with screenshot capture
- [ ] Feature request voting board (Canny, Productboard, or similar)
- [ ] Exit survey for users who leave beta early

---

## Pre-Launch Content Sequence

Build momentum in the weeks before launch with a structured content calendar.

| Week | Content Type | Channel | Goal |
|---|---|---|---|
| -6 | Problem-awareness blog post | Blog, LinkedIn, Twitter | Establish the problem you solve |
| -5 | Industry data or original research | Blog, email list | Build authority and attract attention |
| -4 | Founder story / origin narrative | Twitter thread, LinkedIn post | Build personal connection |
| -3 | Teaser video or product preview | Social media, email list | Generate curiosity and anticipation |
| -2 | Early testimonials from beta users | Social media, landing page | Social proof before launch |
| -1 | "Launching next week" countdown | Email list, social media | Convert awareness into intent |
| Launch | Full launch announcement | All channels simultaneously | Maximum coordinated impact |

---

## Launch Day Checklist

### Product Readiness (Complete Before Launch)

- [ ] Core features tested and stable (zero P0/P1 bugs)
- [ ] Onboarding flow tested with 5+ external users
- [ ] Performance benchmarks met (page load <2s, API response <500ms)
- [ ] Error monitoring configured (Sentry, Datadog, or equivalent)
- [ ] Scalability tested for expected traffic (3-5x normal capacity)
- [ ] Security review completed (auth, data handling, API keys)
- [ ] Terms of service and privacy policy published
- [ ] Payment processing tested end-to-end (if applicable)
- [ ] Mobile/responsive experience verified
- [ ] Accessibility basics covered (WCAG 2.1 AA minimum)

### Marketing Assets Ready

- [ ] Landing page live and optimized (hero, features, social proof, CTA)
- [ ] Product demo video produced and uploaded
- [ ] Press kit prepared (logos, screenshots, founder photos, fact sheet)
- [ ] Blog post drafted and scheduled
- [ ] Email announcement drafted for full list
- [ ] Social media posts drafted for all platforms (Twitter, LinkedIn, Facebook, Instagram)
- [ ] Community posts drafted (Reddit, Hacker News, Indie Hackers, relevant Slacks)
- [ ] Help documentation and FAQ published
- [ ] Pricing page live and tested

### Team Coordination

- [ ] All team members briefed on launch timeline and their roles
- [ ] Support team trained on new features and common questions
- [ ] Sales team equipped with updated pitch deck and battle cards
- [ ] War room or dedicated Slack channel created for launch day communication
- [ ] Escalation paths defined (who handles what if something breaks)
- [ ] On-call engineering rotation confirmed for launch window

### Distribution Execution

- [ ] Email blast sent to subscriber list (timed for 10 AM recipient local time)
- [ ] Social media posts published across all platforms
- [ ] Product Hunt listing live (if applicable)
- [ ] Press embargo lifted and pitches sent
- [ ] Partner co-marketing posts coordinated
- [ ] Paid ads activated (if budget allocated for launch amplification)
- [ ] Influencer and advocate outreach completed
- [ ] Community posts published (stagger across platforms to avoid spam flags)
- [ ] Retargeting audiences updated with launch messaging
- [ ] Internal all-hands or Slack announcement to celebrate and mobilize team

### Monitoring and Response

- [ ] Real-time analytics dashboard open (traffic, sign-ups, conversions)
- [ ] Server health monitoring active
- [ ] Social media monitoring active (brand mentions, hashtag tracking)
- [ ] Support queue staffed at 2x normal capacity
- [ ] Bug triage process active with fast-fix deployment capability
- [ ] Hourly check-in cadence established for launch team

---

## Post-Launch Optimization

### First 7 Days

| Day | Focus | Actions |
|---|---|---|
| 1 | Respond and stabilize | Fix critical bugs, answer every comment and email, monitor server load |
| 2 | Analyze first cohort | Review Day 1 sign-up → activation funnel, identify drop-off points |
| 3 | Iterate on onboarding | Fix top 3 friction points in sign-up/activation flow |
| 4 | Amplify what works | Double down on highest-performing channels and messages |
| 5 | Engage early users | Personal outreach to first 50-100 users, collect feedback |
| 6 | Content follow-up | Publish "What we learned from launch" post, share early metrics |
| 7 | Week 1 retrospective | Full team review of metrics, wins, failures, and priorities for Week 2-4 |

### First 30 Days

| Week | Focus Area | Key Actions |
|---|---|---|
| Week 1 | Stabilize and learn | Bug fixes, onboarding optimization, user interviews |
| Week 2 | Optimize conversion | A/B test landing page, improve activation flow, refine messaging |
| Week 3 | Expand reach | Launch on additional channels, activate referral program, begin SEO |
| Week 4 | Retention focus | Analyze Day 7 and Day 14 retention, build engagement loops, plan next release |

---

## Launch Metric Tracking

### Dashboard Metrics

| Metric | Source | Tracking Frequency |
|---|---|---|
| Unique visitors | Google Analytics / Plausible | Hourly on launch day, daily after |
| Sign-ups | Product database | Hourly on launch day, daily after |
| Activation rate | Product analytics (Mixpanel, Amplitude) | Daily |
| Sign-up → Activation time | Product analytics | Daily |
| Channel attribution | UTM parameters, referral data | Daily |
| Revenue (if applicable) | Stripe, payment processor | Daily |
| Support tickets | Help desk (Zendesk, Intercom) | Hourly on launch day |
| NPS / CSAT | Survey tool | Weekly starting Day 7 |
| Social mentions | Brand monitoring (Mention, Brandwatch) | Hourly on launch day |
| Press coverage | Media monitoring | Daily for first 2 weeks |

### Launch Scorecard Template

| KPI | Target | Actual | Status |
|---|---|---|---|
| Day 1 sign-ups | ___ | ___ | On track / Behind / Exceeded |
| Week 1 sign-ups | ___ | ___ | |
| Week 1 activation rate | ___ | ___ | |
| Month 1 sign-ups | ___ | ___ | |
| Month 1 activation rate | ___ | ___ | |
| Month 1 revenue | ___ | ___ | |
| CAC (by channel) | ___ | ___ | |
| Press articles | ___ | ___ | |
| Product Hunt ranking | ___ | ___ | |
| NPS at Day 30 | ___ | ___ | |

---

*A great launch is not a single day. It is a coordinated sequence that builds momentum before, executes with precision during, and compounds results after. Plan the full arc.*
