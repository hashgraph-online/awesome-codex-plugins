---
name: social-strategy
description: "Build social media strategy. Use when: defining content pillars, posting cadence, engagement tactics, or growth plans."
argument-hint: "[platform or objective]"
---

# /digital-marketing-pro:social-strategy

## Purpose

Build a comprehensive, platform-specific social media strategy that defines content pillars, posting cadence, engagement playbook, community management approach, and growth tactics tailored to each platform's algorithm and audience behavior.

## Input Required

The user must provide (or will be prompted for):

- **Platforms**: Which social platforms to strategize for (Instagram, TikTok, LinkedIn, X, YouTube, Facebook, Pinterest, Threads)
- **Current state**: Existing follower counts, engagement rates, content performance (if available)
- **Goals**: Growth, engagement, traffic, leads, community building, thought leadership
- **Resources**: Team size, content creation capacity, tools in use
- **Audience**: Target audience per platform (or use brand personas)
- **Competitors**: Social accounts to benchmark against (optional)

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. **Also check for guidelines** at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions and relevant category files. Check for custom templates at `~/.claude-marketing/brands/{slug}/templates/`. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. Audit current social presence: content mix, posting frequency, engagement patterns, follower quality
3. Define 3-5 content pillars aligned with brand expertise and audience interests
4. Set platform-specific posting cadence based on algorithm best practices and team capacity
5. Design content mix ratios per platform: educational, entertaining, promotional, community, trending
6. Build engagement playbook: comment strategy, DM workflows, UGC encouragement, community rituals
7. Define growth tactics per platform: hashtag strategy, collaboration, paid boost criteria, cross-promotion
8. Create content format recommendations per platform (carousels, reels, stories, threads, lives)
9. Set KPIs per platform with realistic growth benchmarks
10. Build a 30-day quick-start action plan

## Output

A structured social media strategy containing:

- Platform-by-platform strategy with rationale for prioritization
- Content pillar framework with example topics per pillar
- Posting cadence calendar with optimal times per platform
- Content format recommendations with performance benchmarks
- Engagement playbook with response templates and escalation rules
- Growth tactics roadmap per platform
- Community management guidelines
- KPI targets and measurement framework per platform
- 30-day quick-start action plan with specific daily/weekly tasks

## Agents Used

- **content-creator** — Content strategy, pillar development, format recommendations, engagement tactics
- **social-media-manager** — Platform-native strategy, algorithm optimization, hashtag strategy, posting time optimization, community management
