---
name: schedule-social
description: "Schedule social media posts. Use when: publishing to Twitter/X, Instagram, LinkedIn, TikTok, YouTube, or Pinterest."
disable-model-invocation: false
argument-hint: "[platform]"
---

# /digital-marketing-pro:schedule-social

## Purpose

Schedule social media posts to one or more platforms with platform-specific formatting, optimized posting times, hashtag strategy, and engagement monitoring setup. Handles multi-platform distribution from a single content brief by generating tailored variations that respect each platform's character limits, media specs, and audience conventions while preserving the core message across all channels.

## Execution gate (MANDATORY — cannot be skipped)

1. Present the full preview — recipients / spend / changes / compliance — as an **Execution Summary** before touching any live system.
2. The user must type `yes` (or an equivalent explicit approval). ANY other input — ambiguous, implied, partial, or absent approval — cancels the run.
3. Never proceed on ambiguous input. Never auto-retry a failed execution; a failure needs human review before any re-run.
4. Record the approval with `python "${CLAUDE_PLUGIN_ROOT}/scripts/approval-manager.py" --brand {slug} --action create-approval --data '{"risk_level":"<tier>","summary":"..."}'` **before** executing, then `python "${CLAUDE_PLUGIN_ROOT}/scripts/approval-manager.py" --brand {slug} --action mark-executed --id {approval_id}` after the platform confirms success.

## Input Required

The user must provide (or will be prompted for):

- **Post content**: Core message text, along with any images, video, carousel assets, or links to include — can be a single unified draft or pre-written per-platform variants
- **Target platforms**: Which platforms to post on — Twitter/X, Instagram (feed, Stories, Reels), LinkedIn (post or article), TikTok, YouTube (Shorts or Community), or Pinterest — must have corresponding MCP servers connected
- **Posting date and time**: Specific date and time per platform with timezone, or "optimal" to use data-driven timing recommendations based on audience engagement patterns
- **Hashtags**: Specific hashtags to use, a topic for auto-suggestion, or "auto" to generate hashtags based on content analysis, trending tags, and brand hashtag strategy
- **Platform-specific variations**: Any per-platform tweaks — different copy length, different images or aspect ratios, different CTAs, tone adjustments, or platform-native features (Instagram polls, LinkedIn document carousels, Twitter/X threads)
- **Link and UTM parameters**: URL to include with UTM tracking parameters (source, medium, campaign, content) for attribution, or auto-generate UTMs based on campaign naming conventions from brand profile
- **Media assets**: Image files or URLs with aspect ratio preferences per platform, video files with duration compliance, or carousel image sets in posting order
- **Engagement instructions**: Whether to set up reply monitoring, comment response guidelines, engagement boost triggers (promote if engagement exceeds threshold), or cross-posting rules
- **Content calendar context**: Optional — campaign name or content pillar this post belongs to, for calendar tracking and thematic consistency across the publishing schedule
- **Accessibility requirements**: Alt text for images, video captions or subtitle files, and any accessibility-specific formatting (plain language, high contrast text overlays)
- **First comment or thread**: Optional — follow-up comment to post immediately after the main post (Instagram first comment for hashtags, Twitter/X thread continuation, LinkedIn engagement prompt)
- **Geo-targeting**: Optional — restrict post visibility to specific regions or languages where supported by the platform (LinkedIn geo-targeting, Facebook location targeting)
- **Cross-promotion references**: Optional — references to related content on other platforms to include in the post (e.g., "Watch the full video on YouTube" or "Read the full article on our blog")
- **Mentions and tags**: Optional — accounts to @mention or tag in the post (partners, collaborators, influencers, featured customers) per platform tagging conventions

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. Also check for guidelines at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Verify connected social MCPs**: Check which social media platform MCP servers are connected and confirm they cover all the user's target platforms. List any missing connections with setup instructions. Verify API permissions include scheduling capability for each platform.
3. **Format content per platform specs**: Adapt the content for each platform's requirements — consult `skills/context-engine/platform-publishing-specs.md` for character limits (Twitter/X: 280, LinkedIn: 3,000, Instagram: 2,200, TikTok: 2,200, Pinterest: 500), image dimensions (1:1, 4:5, 9:16, 16:9), video length caps, carousel slide limits, and link preview behavior. Create distinct variations where content cannot be shared identically across platforms.
4. **Optimize posting times**: Run `python "${CLAUDE_PLUGIN_ROOT}/scripts/posting-time-analyzer.py" --platform {platform} --industry {industry} --audience-type {b2b|b2c|mixed}` to suggest a posting window per platform by day of week and hour. NOTE: this returns a **static industry heuristic (2024-era best-times table)** — it does NOT read the brand's historical engagement data. Treat the output as a starting hypothesis and validate it against the brand's own engagement history before relying on it. Factor in audience timezone distribution.
5. **Analyze and optimize hashtags**: Run `hashtag-analyzer.py` to evaluate proposed hashtags for reach potential, competition level, relevance score, and trending status. Recommend a balanced hashtag mix per platform — branded hashtags, niche community hashtags, and broad reach hashtags — with platform-specific counts (Instagram: 15-20, Twitter/X: 2-3, LinkedIn: 3-5, TikTok: 4-6, Pinterest: 2-5 as keyword tags).
6. **Score content for brand voice**: Run `brand-voice-scorer.py` on each platform variation to verify alignment with brand tone, vocabulary, and messaging guidelines. Flag any variation that falls below the brand's minimum score and suggest specific edits.
7. **Create per-platform variations**: If the user did not provide explicit per-platform copy, generate tailored variations — shorter and punchier for Twitter/X, professional and insight-driven for LinkedIn, visual-first captions with line breaks for Instagram, trend-aware and casual for TikTok, keyword-rich with vertical imagery for Pinterest. Preserve the core message and CTA across all while adapting voice for each platform's native style.
8. **Validate media assets**: Verify all images and videos meet platform requirements — dimensions, aspect ratio, file size limits, video duration, and format (JPEG/PNG for images, MP4 for video). Flag any assets that need resizing or reformatting and suggest optimal crops per platform.
9. **Create approval record**: Create the record via `approval-manager.py --action create-approval` with the risk level inside the `--data` JSON — `{"risk_level":"medium",...}`. There is no `--risk-level` flag; see the Execution gate above for the exact command. Generate a scheduling summary showing each platform's post content, media preview, hashtags, posting time, UTM-tagged links, and brand voice score.
10. **Present scheduling summary**: Display the complete multi-platform schedule for user review — one section per platform showing final copy with character count, media attachments with dimensions, hashtags, posting time with timezone, and any platform-specific notes or warnings. Wait for explicit approval.
11. **Schedule via each platform's MCP**: On approval, submit each post to its target platform through the connected MCP server. Handle platform-specific scheduling APIs, media uploads, hashtag formatting, and link shortening. Confirm the scheduled status for each platform individually.
12. **Verify scheduled status**: After scheduling, query each platform's API to confirm the posts are queued at the correct times with the correct content. Flag any scheduling failures, content truncation, or media upload errors and retry or escalate as needed.
13. **Schedule first comments or threads**: If first-comment content was provided, queue the follow-up comment or thread continuation for immediate posting after the main post goes live on each applicable platform.
14. **Update content calendar**: Log the scheduled posts against the brand's content calendar with campaign name, content pillar, platform, and posting time for cross-channel visibility and duplicate prevention.
15. **Log executions per platform**: Run `execution-tracker.py` for each platform to log the scheduling event with timestamp, platform, scheduled posting time, content summary, hashtags, UTM parameters, and media asset references.

## Output

A structured scheduling confirmation containing:

- **Scheduled post confirmations**: Per-platform confirmation with post ID, scheduled date and time with timezone, and preview link or draft URL where available
- **Platform-specific content**: Final copy for each platform showing character count versus limit, hashtags with position (inline or comment), media attachments with dimensions, and UTM-tagged link
- **Posting times with rationale**: Scheduled time per platform with data-driven justification — historical engagement peak hours, audience timezone alignment, competitive posting window analysis, or user-specified timing
- **Hashtag recommendations**: Final hashtag set per platform with supporting metrics — estimated reach per hashtag, competition level, trending status, and relevance score
- **Brand voice scores**: Per-platform alignment scores with notes on tone adjustments made during variation creation and any remaining recommendations
- **Media spec compliance**: Confirmation that all images and videos meet platform requirements for dimensions, file size, format, aspect ratio, and video duration with any crops or adjustments applied
- **UTM tracking summary**: Complete UTM parameters per platform (source, medium, campaign, content) for attribution tracking in Google Analytics or the brand's analytics platform
- **Cross-platform coordination notes**: Posting sequence rationale if posts are staggered, and any cross-promotion references between platforms (e.g., "Full video on YouTube" link in Twitter/X post)
- **Accessibility compliance**: Alt text applied to all images, caption files attached to videos, and plain-language verification for accessible content across platforms
- **First comment or thread status**: Confirmation of scheduled follow-up comments per platform with content preview and timing (immediate after main post)
- **Content calendar placement**: Campaign name, content pillar, and calendar date for cross-referencing with the brand's publishing schedule
- **Mentions and tags applied**: Confirmation of all @mentions and account tags included per platform with handle verification status
- **Execution log entries**: Timestamped records per platform for audit trail, content calendar synchronization, and cross-channel scheduling coordination

## Agents Used

- **social-media-manager** — Content formatting per platform conventions, posting time optimization, hashtag strategy and analysis, brand voice scoring, platform-specific variation creation, media asset validation, accessibility compliance, first comment scheduling, and engagement monitoring configuration
- **execution-coordinator** — Approval workflow, multi-platform scheduling execution via MCP servers, per-platform status verification, first comment and thread queuing, content calendar update, retry handling for failed schedules, and per-platform execution logging
