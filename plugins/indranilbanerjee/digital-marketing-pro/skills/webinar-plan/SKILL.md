---
name: webinar-plan
description: "Plan webinars and virtual events. Use when: designing promotion, content, registration, and post-event follow-up."
argument-hint: "[topic]"
---

# /digital-marketing-pro:webinar-plan

## Purpose

Plan a webinar or virtual event from concept to post-event follow-up, including content structure, promotion strategy, registration optimization, engagement tactics, and measurement framework. Produces a complete execution package that a team can implement without further strategic planning.

## Input Required

The user must provide (or will be prompted for):

- **Topic/theme**: Subject matter and angle for the webinar — what specific problem or opportunity will be addressed
- **Target audience**: Who should attend — role, seniority, industry, company size, experience level, and pain points
- **Objectives**: Primary goal — lead generation, education, product demo, thought leadership, customer retention, or partner enablement
- **Preferred platform**: Webinar tool in use or under consideration (Zoom, Teams, Webex, GoToWebinar, Livestorm, StreamYard, etc.)
- **Date/time**: Proposed date and time with timezone (or ask for optimal scheduling recommendation based on audience)
- **Speakers**: Presenters, panelists, or hosts — internal team members and/or external guests with their expertise areas
- **Budget for promotion**: Available spend for driving registrations — paid ads, sponsorships, influencer partnerships, etc.
- **Expected attendance**: Target registration and attendance numbers for goal-setting and promotion planning
- **Content assets available**: Existing slide decks, research reports, demos, or content that can be repurposed for the webinar
- **Follow-up goals**: What should happen after the webinar — sales meetings booked, free trial signups, content downloads, community joins

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. **Also check for guidelines** at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions and relevant category files. Check for custom templates at `~/.claude-marketing/brands/{slug}/templates/`. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Define webinar format**: Select the best format based on objectives, audience preferences, and speaker strengths — presentation, panel discussion, interactive workshop, product demo, AMA, fireside chat, or hybrid format with multiple segments
3. **Create content outline with timing**: Build a minute-by-minute run of show — opening hook, speaker introductions, content segments with transitions, audience interaction points (polls, Q&A breaks), and closing CTA with time allocations for each block
4. **Design registration page copy**: Write headline, subheadline, 3-5 key takeaway bullets, speaker bios with credibility markers, urgency elements (limited spots, countdown), and social proof (past attendee quotes, company logos) optimized for conversion
5. **Build multi-channel promotion plan**: Create a coordinated promotion strategy across email sequences, organic social posts, paid ads (LinkedIn, Meta, Google), partner/speaker cross-promotion, blog/website banners, community outreach, and internal employee advocacy
6. **Create presenter prep materials**: Develop speaker brief with key talking points, slide structure recommendations, audience profile context, brand voice reminders, Q&A preparation, and technical setup/rehearsal checklist
7. **Design attendee engagement strategy**: Plan interactive elements — specific poll questions tied to content, Q&A facilitation approach, chat prompts to spark discussion, breakout room activities (if applicable), live resource sharing, and real-time feedback mechanisms
8. **Plan post-event sequence**: Design the complete follow-up funnel — recording availability timeline, segmented email sequences for attendees vs. no-shows, lead scoring criteria based on engagement, sales handoff process for high-intent leads, and content repurposing plan (blog post, social clips, podcast episode, infographic)
9. **Define success metrics**: Set targets for registrations, show-up rate, engagement rate (poll participation, questions asked, chat activity), leads generated, pipeline influenced, and attendee satisfaction — with industry benchmark comparisons
10. **Create day-of checklist**: Build a comprehensive run-of-day timeline covering tech setup and testing, dry run schedule, backup plans for speaker or tech failures, moderator duties minute-by-minute, recording confirmation, and immediate post-event actions

## Output

A structured webinar execution package containing:

- **Webinar brief**: Format, objectives, audience profile, speakers, platform, date/time, and target metrics summary
- **Content outline with timing**: Minute-by-minute run of show with speaker assignments, transition notes, and engagement cue points
- **Registration page copy**: Headline, description, takeaway bullets, speaker bios, social proof elements, and CTA — ready for implementation
- **3-week promotion calendar**: Day-by-day promotion activities across all channels with content, responsible owners, and spend allocation
- **Email sequences**: Invitation series (2-3 emails with escalating urgency), reminder sequence (1 week, 1 day, 1 hour before), and post-event follow-up (separate tracks for attendees and no-shows)
- **Social promotion posts**: Platform-specific posts for LinkedIn, X/Twitter, Facebook, and Instagram — covering teaser, announcement, countdown, day-of, and post-event phases
- **Presenter guide**: Speaker brief with talking points, brand voice notes, audience context, technical checklist, and rehearsal schedule
- **Engagement plan**: Specific poll questions, timed chat prompts, Q&A facilitation guide, and interactive elements mapped to the content timeline
- **Post-event follow-up sequence**: Recording delivery plan, lead scoring matrix, sales handoff criteria, nurture track design, and content repurposing roadmap
- **Day-of checklist**: Hour-by-hour operational checklist from setup through post-event wrap with contingency plans
- **Success metrics dashboard spec**: KPI definitions, targets, measurement methods, data sources, and industry benchmark comparisons
- **Content repurposing plan**: Specific derivative assets to create from the webinar — blog post, social clips, podcast episode, infographic, email content
- **Budget breakdown**: Promotion spend allocation across channels with expected cost-per-registration estimates

## Agents Used

- **content-creator** — Webinar content outline, registration copy, email sequences, social promotion posts, presenter talking points, engagement prompts
- **email-specialist** — Invitation and follow-up email strategy, send timing optimization, subject line testing, segmentation logic, deliverability checks
- **marketing-strategist** — Promotion strategy, audience targeting, success metrics framework, format selection, post-event lead strategy, ROI projection
