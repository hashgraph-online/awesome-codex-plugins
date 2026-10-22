# Content engine — per-deliverable draft checklists, follow-ups, and dispatch rules

Read this when you are drafting a specific content type and want the minimum component list for it, when offering next steps after a draft, or when producing several formats from one brief in parallel. It supplements `SKILL.md`; the brand-context, gate, humanize, and disclosure rules there are authoritative. For depth on a format, the per-topic reference files beside this one (`ad-copy.md`, `email-sequences.md`, `social-content.md`, `landing-pages.md`, `video-scripting.md`, `case-studies.md`, `seo-content.md`) go further.

## Supported content types (ask if not given)

Blog post or article · ad copy (specify platform) · email (single, newsletter, or sequence) · social post (specify platform) · landing page copy · video script (long-form, short-form, explainer) · press release · case study · content calendar.

Also gather: topic, target audience (role, industry, pain points, buying stage), 2-4 key messages, and optionally a tone override, length target, primary keyword, call to action, and campaign context.

## Minimum components by type

### Blog post / article
- 2-3 headline options with the SEO keyword in the primary
- Hook introduction (question, statistic, bold statement, or story)
- 3-5 sections with descriptive subheadings using related keywords
- Supporting evidence, examples, and data references
- Conclusion with a clear call to action
- SEO: meta title, meta description, internal linking suggestions, keyword placement

### Ad copy
- Platform-specific format and constraints (character limits, headline count, description count)
- 3-5 headline variations
- 2-3 description variations
- Display URL suggestions
- Call-to-action options
- Ad extensions recommendations
- Compliance notes for regulated industries

### Email
- 2-3 subject line options with open-rate considerations
- Preview text
- Body copy with clear hierarchy and scannable formatting
- Primary CTA with button text
- Personalization token recommendations
- Deliverability notes (spam trigger words, link density, image-to-text ratio)

### Social media post
- Platform-native format and length
- Hook in the first line (scroll-stopping opener)
- Hashtag strategy (platform-appropriate count)
- Call to action or engagement prompt
- Image/video specifications and recommendations
- Optimal posting time suggestions

### Landing page
- Headline and subheadline
- Hero section copy
- 3-4 benefit-driven value propositions
- Social proof placement (testimonials, logos, statistics)
- Primary and secondary CTAs
- FAQ section
- SEO: meta title, meta description

### Video script
- Platform-specific structure (long-form 3-10 min, short-form 15-90s, explainer)
- Hook within the first 3 seconds
- Scene descriptions with timestamps
- Dialogue and on-screen text
- B-roll suggestions
- Music and tone recommendations
- End card with CTA

### Press release
- Headline following press release conventions
- Dateline and lead paragraph (who, what, when, where, why)
- Supporting quotes (placeholder guidance)
- Boilerplate and media contact placeholders

### Case study
- Result-focused title
- Customer overview (industry, size, challenge)
- Challenge → Solution → Results structure
- Metrics and data points (prompt the user for specifics; never invent them)
- Customer quote placeholders
- Call to action

## Quality checks after drafting

Evaluate automatically: brand voice consistency (matches profile settings); compliance (restricted terms, required disclaimers, regulatory language); legal flags (unsubstantiated claims, superlatives without evidence, comparative claims); SEO alignment (keyword usage, meta tags, heading structure); readability appropriate for the target audience.

## After drafting

Ask: "Would you like me to:
- Revise any section or adjust the tone?
- Create variations for A/B testing? (`/digital-marketing-pro:prompt-test`)
- Evaluate quality with the full scoring framework? (`/digital-marketing-pro:eval-content`)
- Adapt this content for other channels? (`/digital-marketing-pro:content-repurpose`)
- Create an email sequence from this content? (`/digital-marketing-pro:email-sequence`)
- Generate social media posts to promote this? (`/digital-marketing-pro:social-strategy`)"

## Execution discipline — parallel dispatch

When `/digital-marketing-pro:content-engine` is invoked to produce **multiple content formats from a single brief** (e.g. "draft a launch blog post + 3 social posts + email teaser + ad copy"), dispatch the per-format generations in **one message with parallel `Task` calls**. Each format reads the same brief, applies the same brand voice, but produces an independent draft — there is no cross-dependency between, say, the LinkedIn post and the email teaser.

Sequence the steps that DO have dependencies:
1. SME calibration + brief refinement (sequential — single pass)
2. **Per-format drafting in parallel** (multiple `Task` calls in one message — one per format)
3. `/digital-marketing-pro:check` quality gate on each draft (parallel by file)
4. Aggregation + handoff (sequential)

Single-format requests can skip parallelization — there's nothing to parallelize.
