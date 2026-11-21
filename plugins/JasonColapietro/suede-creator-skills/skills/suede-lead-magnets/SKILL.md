---
name: suede-lead-magnets
description: "Suede AI Lead Magnet Skills. lead-magnet strategy for useful downloads, gated resources, delivery, and qualified capture. Use when asked \"design a lead magnet\" or to choose formats, gating, an indexable companion page, and a measurement plan. NOT FOR: interactive tools (suede-free-tools), nurture flows (suede-emails), or production copy (suede-copy)."
metadata:
  display-name: "Suede AI Lead Magnet Skills"
  version: 2.1.0
---

# Suede AI Lead Magnet Skills

## Compatibility

Works with supplied product context and audience evidence. File access is useful for existing assets; live research requires browsing. Email delivery and form deployment are separate authorized actions.

For a concrete input, expected output, recovery path, and validation check, read
[the worked contract](references/worked-contract.md). Use it to check the handoff
before treating the task as complete.

Design lead magnets as useful, rights-clear assets with an honest value exchange and a measurable path to product value. Choose the format, depth, gating, delivery, and follow-up based on audience need and qualification, not on maximizing raw email capture.

## Before Planning

**Check for product marketing context first:**
If `.agents/product-marketing.md` exists (or `.claude/product-marketing.md`, or the legacy `product-marketing-context.md` filename, in older setups), read it before asking questions. Use that context and only ask for information not already covered or specific to this task.

Gather this context (ask if not provided):

### 1. Business Context
- What does the company do?
- Who is the ideal customer?
- What problems does your product solve?

### 2. Current Lead Generation
- How do you currently capture leads?
- What lead magnets or offers do you have?
- What's your current conversion rate on email capture?
- Where does the audience spend time online?
- What's the most common question prospects ask before buying?

### 3. Content Assets
- What existing content could be repurposed? (blog posts, guides, data)
- What expertise can you package?
- What templates or tools do you use internally?

### 4. Goals
- Primary goal: email list growth, lead quality, product education?
- Target audience stage: awareness, consideration, or decision?
- Timeline and resource constraints?

---

## Lead Magnet Principles

### 1. Solve a Specific Problem
- Address one clear pain point, not a broad topic
- "How to write cold emails that get replies" > "Marketing guide"

### 2. Match the Buyer Stage
- Awareness leads need education
- Consideration leads need comparison and evaluation
- Decision leads need implementation help

### 3. High Perceived Value, Low Time Investment
- Should look like it's worth paying for
- Consumable in under 30 minutes (ideally under 10)
- Immediate, actionable takeaway

### 4. Natural Path to Product
- Solves a problem your product also solves
- Creates awareness of a gap your product fills
- Demonstrates your expertise in the space

### 5. Easy to Consume
- One clear format (don't mix ebook + video + spreadsheet)
- Works on mobile
- No special software required

### Defaults to Refuse
Named cliches this skill does not produce, whatever the brief says:
- The 40-page "Ultimate Guide to [Category]" nobody finishes.
- The "10 Tips" PDF that restates the blog post it gates.
- The checklist whose items are all "consider X" rather than a decidable action.
- The template that is a blank document with headings.

---

## Lead Magnet Types

| Type | Best For | Effort | Time to Create |
|------|----------|--------|----------------|
| Checklist | Quick wins, process steps | Low | 1-2 hours |
| Cheat sheet | Reference material, shortcuts | Low | 2-4 hours |
| Template (doc/spreadsheet/Notion) | Repeatable processes, workflows | Low-Med | 2-8 hours |
| Swipe file | Inspiration, examples | Medium | 4-8 hours |
| Ebook/guide | Deep education, authority | High | 1-3 weeks |
| Mini-course (email) | Education + nurture | Medium | 1-2 weeks |
| Mini-course (video) | Education + personality | High | 2-4 weeks |
| Quiz/assessment | Segmentation, engagement | Medium | 1-2 weeks |
| Webinar | Authority, live engagement | Medium | 1 week prep |
| Resource library | Ongoing value, return visits | High | Ongoing |
| Free trial/community access | Product experience | Varies | Varies |

**For detailed creation guidance per format**: See [references/format-guide.md](references/format-guide.md)

---

## Matching Lead Magnets to Buyer Stage

### Awareness Stage
Goal: Educate on the problem. Attract people who don't know you yet.

| Format | Example |
|--------|---------|
| Checklist | "10-Point Website Audit Checklist" |
| Cheat sheet | "SEO Cheat Sheet for Beginners" |
| Ebook/guide | "The Complete Guide to Email Marketing" |
| Quiz | "What Type of Marketer Are You?" |

### Consideration Stage
Goal: Help evaluate solutions. Build trust and demonstrate expertise.

| Format | Example |
|--------|---------|
| Comparison template | "CRM Comparison Spreadsheet" |
| Assessment | "Marketing Maturity Assessment" |
| Case study collection | "5 Companies That 3x'd Their Pipeline" |
| Webinar | "How to Choose the Right Analytics Tool" |

### Decision Stage
Goal: Help implement. Remove friction to purchase.

| Format | Example |
|--------|---------|
| Template | "Ready-to-Use Sales Email Templates" |
| Free trial | "14-Day Free Trial" |
| Implementation guide | "Migration Checklist: Switch in 30 Minutes" |
| ROI calculator | "Calculate Your Savings" (route to `suede-free-tools`) |

---

## Gating Strategy

### Gating Options

| Approach | When to Use | Trade-off |
|----------|-------------|-----------|
| **Full gate** | High-value content, bottom-funnel | Max capture, lower reach |
| **Partial gate** | Preview + full version | Balance of reach and capture |
| **Ungated + optional** | Top-funnel education, original data | Max reach, links, and citations; lower capture |
| **Content upgrade** | Blog post + bonus | Contextual, high-intent |

### What to Ask For

- **Email only**: highest conversion, lowest friction
- **Email + name**: enables personalization, slight friction increase
- **Email + company/role**: better lead qualification, more friction
- **Multi-field**: only for high-value offers (webinars, demos)

Rule of thumb: Ask for the minimum needed. Every extra field reduces conversion by 5-10%.

### How to Frame the Exchange

- Make the value obvious: "Get the full 25-page guide free"
- Show a preview: table of contents, first page, sample results
- Add social proof only when it is real: "Downloaded by [verified count] [role]"
- Reduce risk: "No spam. Unsubscribe anytime."

**For form optimization**: route to `suede-site-alchemy`.
**For popup implementation**: route to `suede-site-alchemy`.

---

## Search, Links, and AI Citations

A PDF behind a form is invisible to search engines and AI answer engines. The
strongest lead magnets do double duty: an indexable page earns traffic, links,
and citations, and the gated asset converts the readers who want more.

- **Publish the substance, gate the convenience.** Put the core findings,
  checklist items, or framework on an HTML page that ranks. Gate the editable
  template, the full dataset, the spreadsheet, or the bonus that saves time.
- **Original data is the link asset.** A survey, benchmark, or analysis of the
  user's own anonymized product data gives other writers and AI answers a
  number to cite. Publish the method, sample size, and date beside the
  findings. Never invent or pad a dataset.
- **Answer-first page structure.** Open with the headline finding in two or
  three sentences, use question headings, and add a short FAQ that a buyer
  would actually ask.
- **Structured data.** `Article` JSON-LD for the page; `Dataset` when the data
  is downloadable. If crawlers see content that users must sign up to read,
  mark it with paywalled-content structured data (`isAccessibleForFree: false`
  plus `hasPart` with the gated section's CSS selector) so Google does not
  treat the gate as cloaking.
- **Attribution-ready.** Name the author, date the data, and give the chart a
  plain-language caption, so a journalist or an AI engine can quote it with the
  brand name attached.

Route keyword and topic choice to `suede-content-strategy`, technical checks to
`suede-seo-audit`, and AI answer visibility to `suede-ai-seo`. Suede AI runs
this as a managed service at https://suedeai.agency.

---

## Landing Page & Delivery

### Landing Page Structure

1. **Headline**: Clear benefit: what they'll get and why it matters
2. **Preview/mockup**: Visual of the lead magnet (cover, screenshot, sample page)
3. **What's inside**: 3-5 bullet points of key takeaways
4. **Social proof**: Download count, testimonials, logos
5. **Form**: Minimal fields, clear CTA button
6. **FAQ**: Address hesitations (Is it really free? What format?)

**For landing page optimization**: route to `suede-site-alchemy`.

### Delivery Methods

| Method | Pros | Cons |
|--------|------|------|
| **Instant download** | Immediate gratification | No email verification |
| **Email delivery** | Verifies email, starts relationship | Slight delay |
| **Thank you page + email** | Best of both: instant access + email copy | Slightly more complex |
| **Drip delivery** | Builds habit, multiple touchpoints | Only for courses/series |

### Thank You Page Optimization

Don't waste the thank you page. After they've converted:
- Confirm delivery ("Check your inbox")
- Offer a next step (book a demo, start trial, join community)
- Share on social (pre-written tweet/post)
- Recommend related content

---

## Promotion & Distribution

### Blog CTAs & Content Upgrades

- Create post-specific content upgrades (bonus checklist for a how-to post)
- Content upgrades convert 2-5x better than generic sidebar CTAs

### Exit-Intent & Popups

- Trigger on exit intent or scroll depth
- Match the popup offer to the page content
- Route popup implementation to `suede-site-alchemy`.

### Social Media

- Route social strategy and post production to `suede-social`.

### Paid Promotion

- Facebook/Instagram lead ads for top-funnel lead magnets
- Google Ads for high-intent lead magnets (templates, tools)
- LinkedIn for B2B lead magnets
- Retarget blog visitors with lead magnet ads
- Use `suede-ads` for campaign strategy

### Partner Co-Promotion

- Route partner cross-promotion, guest webinars, and bundled resource collections to `suede-co-marketing`.

---

## Measuring Success

### Key Metrics

| Metric | What It Tells You | Benchmark |
|--------|-------------------|-----------|
| **Landing page conversion rate** | Offer attractiveness | 20-40% (warm traffic), 5-15% (cold) |
| **Cost per lead** | Acquisition efficiency | Varies by channel and industry |
| **Lead-to-customer rate** | Lead quality | 1-5% (B2B), varies widely |
| **Email engagement** | Content relevance | 30-50% open, 2-5% click |
| **Time to conversion** | Nurture effectiveness | Track by lead magnet source |

Benchmarks are industry ranges for calibration only: never assert them as this asset's expected or achieved result.

**For detailed benchmarks by format and industry**: See [references/benchmarks.md](references/benchmarks.md)

### A/B Testing Ideas

- **Headline**: Benefit-focused vs. curiosity-driven
- **Format**: Checklist vs. guide on same topic
- **Gate level**: Full gate vs. partial preview
- **Form fields**: Email-only vs. email + name
- **CTA copy**: "Download Free Guide" vs. "Get Your Copy"
- **Delivery**: Instant download vs. email delivery

### Lead Quality Signals

The lead magnet passes the quality check when at least 3 of these 4 hold:
- Higher-than-average email engagement
- Leads progress to trial/demo at expected rates
- Low unsubscribe rate after delivery
- Leads match ICP demographics

---

## Output Format

When creating a lead magnet strategy, provide:

### 1. Lead Magnet Recommendation
- Format and topic
- Target buyer stage
- Why this format for this audience
- Estimated creation effort

### 2. Content Outline
- Key sections/components
- Length and scope
- What makes it unique or valuable
- Every third-party asset the magnet embeds (stock imagery, quoted data or charts,
  borrowed templates, screenshots of other products), named individually with its
  license or the gap stated. An unresolved gap blocks production of that asset.

### 3. Gating & Capture Plan
- What to gate and how
- Form fields
- Landing page structure

### 4. Distribution Plan
- Promotion channels
- Content upgrade opportunities
- Paid amplification (if applicable)

### 5. Measurement Plan
- KPIs and targets
- What to A/B test first

---

## Boundaries

- Do not claim conversion, demand, originality, or audience fit without evidence.
- Do not publish assets, create forms, collect contacts, start campaigns, or change consent settings without explicit authorization.
- Do not gate material the user must provide freely for legal, safety, account, or support reasons.
- Do not decide privacy, licensing, compliance, or retention policy for captured data.

## Routing

- Use `suede-free-tools` for calculators, graders, quizzes, and generators.
- Use `suede-copy` for asset and landing-page copy and `suede-emails` for post-capture nurture.
- Use `suede-content-strategy` for topic selection and `suede-analytics` for measurement.
- Use `suede-ads` or `suede-social` for distribution and `suede-co-marketing` for partner promotion.
- Use `suede-site-alchemy` for landing pages, forms, and popup implementation.
- Use `suede-ab-testing` to design and evaluate the tests in A/B Testing Ideas.
