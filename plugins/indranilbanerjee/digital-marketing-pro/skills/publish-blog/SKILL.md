---
name: publish-blog
description: "Publish blog posts. Use when: deploying to WordPress or Webflow with SEO optimization, categories, and scheduling."
disable-model-invocation: true
argument-hint: "[--platform=wordpress|webflow]"
---

# /digital-marketing-pro:publish-blog

## Purpose

Publish a fully optimized blog post to the brand's CMS (WordPress or Webflow) with SEO metadata, categories and tags, featured image, and optional scheduling. Includes pre-publish quality checks for content scoring and brand voice alignment, plus post-publish verification to confirm the live URL is accessible and rendering correctly. Designed to be the final step in a content workflow — taking a draft from ready to live with all optimization gates enforced.

## Input Required

The user must provide (or will be prompted for):

- **Blog content**: The full blog post draft or a rough draft to refine — title, body, any inline images or embeds, and blockquotes or callout boxes
- **Target CMS platform**: Which publishing platform to use — WordPress or Webflow — must have the corresponding MCP server connected
- **Publish date**: Immediate publish or a scheduled date and time with timezone — scheduling uses the platform's native scheduling feature
- **Categories and tags**: Content categories and taxonomy tags for organization and discoverability, or allow auto-suggestion based on content analysis and existing taxonomy
- **Featured image**: Image file path, URL, or description for generation — used as the hero image and social sharing thumbnail (Open Graph and Twitter Card)
- **SEO metadata**: Primary keyword, secondary keywords, meta title (50-60 chars), meta description (150-160 chars) — or request auto-generation based on content analysis and keyword strategy
- **Author attribution**: Author name and bio link if different from the default brand author configured in the CMS
- **Slug preference**: Custom URL slug or auto-generate from the title with keyword optimization and stop-word removal
- **Internal links**: Specific internal pages to link to within the post, or allow auto-detection of linking opportunities based on existing site content
- **Social sharing text**: Custom Open Graph title and description for social previews, or auto-generate from the meta title and description
- **Content format**: Post format — standard article, listicle, how-to guide, case study, or thought leadership — determines schema markup type and structural expectations
- **Excerpt or summary**: A 1-2 sentence excerpt for archive pages, RSS feeds, and social cards, or auto-generate from the opening paragraph
- **Related posts**: Optional — specific posts to link as related content at the end of the article, or auto-detect based on category and topic overlap
- **CTA block**: Optional — custom call-to-action block to append at the end of the post (newsletter signup, product trial, content upgrade, consultation booking)

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. Also check for guidelines at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Verify CMS connection**: Check which CMS MCP server is connected (wordpress or webflow) and confirm it matches the user's target platform. If not connected, instruct the user to configure the MCP server first and provide the relevant setup link.
3. **Score content quality**: Run `content-scorer.py` on the blog draft to evaluate readability (Flesch-Kincaid grade), structure (heading hierarchy, paragraph length, list usage), depth (word count vs topic complexity), and engagement potential. Flag any issues that need fixing before publish.
4. **Score brand voice alignment**: Run `brand-voice-scorer.py` to verify the content matches the brand's tone, vocabulary, and messaging guidelines. Suggest specific edits if the score falls below the brand's minimum threshold defined in profile.json.
5. **Optimize for SEO**: Ensure the primary keyword appears in the title, H1, first 100 words, URL slug, and meta description. Verify meta description is 150-160 characters and meta title is 50-60 characters. Check internal linking opportunities, image alt text, and heading keyword usage. Validate schema markup compatibility for the content type (article, how-to, FAQ).
6. **Format for platform API**: Structure the content payload per the target CMS requirements — consult `platform-publishing-specs.md` for field mappings, HTML formatting, image handling, category/tag taxonomy IDs, featured image upload, Open Graph meta fields, and any platform-specific quirks like WordPress custom fields or Webflow CMS collection structure.
7. **Run compliance check**: Verify content meets regulatory requirements for the brand's target markets — disclosure statements, affiliate link disclaimers, medical or financial disclaimers, and copyright attribution for any third-party content or images referenced.
8. **Create approval record**: Run `approval-manager.py` with risk level set to medium. Generate a pre-publish summary showing title, URL slug, publish time, SEO score, brand voice score, content quality score, categories, tags, featured image preview, and compliance status.
9. **Present pre-publish summary**: Display the complete summary for user review and approval. Highlight any warnings from content scoring, SEO analysis, or compliance checks. Show a side-by-side preview of how the post will appear in search results and social sharing cards. Wait for explicit user confirmation before proceeding.
10. **Execute publish via CMS MCP**: On approval, send the formatted payload to the CMS through the connected MCP server. Handle scheduling if a future publish date was specified. Confirm the API response indicates success.
11. **Verify live URL**: After publish, request the live URL from the CMS API and verify it returns a 200 status. Confirm the title, meta description, featured image, canonical URL, and Open Graph tags are rendering correctly. Check that the page is not blocked by robots.txt or noindex tags.
12. **Validate schema markup**: Confirm the published page includes the correct structured data (Article, HowTo, FAQ, or BreadcrumbList) and that it passes validation for rich snippet eligibility in search results.
13. **Submit to search engines**: If the brand has Google Search Console connected, submit the new URL for indexing to accelerate discovery. Log the submission timestamp.
14. **Log execution and save insight**: Run `execution-tracker.py` to log the publish event with timestamp, platform, URL, scores, and categories. Save an insight about the published content — topic, keywords, performance predictions — for future content strategy reference and gap analysis.

## Output

A structured publish confirmation containing:

- **Published URL**: The live or scheduled URL where the blog post is accessible, with confirmation of correct canonical URL
- **SEO score**: Content SEO score with breakdown — keyword placement, meta title and description quality, internal links count, image alt text coverage, heading structure, and URL slug optimization
- **Brand voice score**: Alignment score with notes on tone, vocabulary, messaging consistency, and any adjustments made during optimization
- **Content quality score**: Readability grade (Flesch-Kincaid), structure assessment (heading hierarchy, paragraph balance), word count, and engagement potential rating
- **Pre-publish checklist results**: Pass/fail status for each quality gate — content score, brand voice, SEO optimization, compliance review, and platform formatting validation
- **Publish details**: Platform, publish status (live or scheduled with date), author, categories, tags, featured image confirmation, canonical URL, and Open Graph preview
- **Social sharing preview**: How the post will appear when shared on Facebook, Twitter/X, and LinkedIn — including Open Graph image, title, and description rendering
- **Compliance status**: Verification of all required disclaimers, disclosures, and attribution included per brand market regulations
- **Schema markup validation**: Structured data type applied, validation status, and rich snippet eligibility for the content format
- **Search engine submission**: Indexing request status via Google Search Console (if connected) with submission timestamp
- **Performance baseline**: Initial metrics snapshot — page load time, Core Web Vitals scores, and crawl status — as a baseline for post-publish performance monitoring
- **Related posts linked**: List of related content linked at the end of the article with titles and URLs for internal traffic flow
- **CTA block confirmation**: The call-to-action block rendered at the end of the post with type, copy, and destination URL
- **Execution log entry**: Timestamped record of the publish action with all metadata for audit trail and performance tracking

## Agents Used

- **content-creator** — Content quality scoring, SEO optimization, brand voice alignment, keyword placement, meta description writing, internal linking recommendations, schema markup guidance, and social sharing text generation
- **execution-coordinator** — Approval workflow, CMS API execution, post-publish verification, live URL validation, execution logging, and insight capture for content strategy
