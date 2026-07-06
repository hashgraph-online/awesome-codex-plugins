# Review Management Platforms — Strategy & Operations Reference

A comprehensive guide to managing online reviews across platforms. Covers review generation, response frameworks by rating, monitoring tools, fake review detection, platform-specific policies, and the legal landscape of review management.

---

## Major Review Platforms by Industry

| Platform | Primary Industries | Monthly Active Users | Review Impact |
|----------|-------------------|---------------------|---------------|
| **Google Business Profile** | All (universal) | 1B+ | Dominant for local search; directly influences local pack ranking |
| **Yelp** | Restaurants, home services, local retail | 178M+ | Strong for service businesses; recommendation filter is aggressive |
| **TripAdvisor** | Hotels, restaurants, attractions, tours | 460M+ | Primary for hospitality and travel; ranking algorithm heavily weights recency |
| **Healthgrades** | Healthcare (doctors, dentists, hospitals) | 50M+ | Leading healthcare review site; patients trust peer reviews over credentials |
| **Avvo** | Legal (attorneys, law firms) | 12M+ | Dominant in legal; Avvo rating combines reviews + profile completeness |
| **G2** | SaaS, enterprise software | 80M+ | Primary B2B review site; influences procurement decisions |
| **Capterra** | SaaS, business software | 100M+ | Gartner-owned; strong for SMB software comparison shopping |
| **Trustpilot** | eCommerce, online services | 50M+ | European-origin, growing globally; open platform with TrustScore |
| **BBB (Better Business Bureau)** | All (credibility-focused) | 120M+ | Trust signal for older demographics; accreditation carries weight |
| **Facebook** | Local businesses, restaurants, retail | 3B+ | Recommendations (not star ratings); integrated with social discovery |
| **Amazon** | eCommerce, consumer products | 300M+ | Verified purchase reviews dominate product purchase decisions |
| **Glassdoor** | Employer brand (all industries) | 55M+ | Employee reviews affect recruiting and indirectly affect customer perception |

### Industry-Specific Priority Matrix

| Industry | Tier 1 (Must-Have) | Tier 2 (Important) | Tier 3 (Nice-to-Have) |
|----------|-------------------|--------------------|-----------------------|
| **Restaurant** | Google, Yelp, TripAdvisor | Facebook, OpenTable | Zomato, Foursquare |
| **Hotel/Hospitality** | Google, TripAdvisor, Booking.com | Expedia, Yelp | Facebook, Hotels.com |
| **Healthcare** | Google, Healthgrades, Zocdoc | Vitals, WebMD | Yelp, Facebook |
| **Legal** | Google, Avvo, Lawyers.com | Justia, FindLaw | Yelp, BBB |
| **SaaS** | G2, Capterra, Google | Trustpilot, TrustRadius | Product Hunt, GetApp |
| **eCommerce** | Google, Trustpilot, Amazon | Facebook, BBB | Sitejabber, ResellerRatings |
| **Home Services** | Google, Yelp, HomeAdvisor | Angi, BBB | Facebook, Thumbtack |
| **Automotive** | Google, DealerRater, Cars.com | Edmunds, CarGurus | Yelp, Facebook |

---

## Review Generation Strategies

### Timing by Business Type

| Business Type | Optimal Request Timing | Rationale |
|--------------|----------------------|-----------|
| **Services (completed)** | 1-3 days after service delivery | Experience is fresh; satisfaction is confirmed |
| **Restaurants** | Same day or next morning | Dining experience memory fades quickly |
| **Physical products** | 7-14 days after delivery | Customer has had time to use and evaluate |
| **SaaS / Software** | 30-60 days after onboarding (or after first success milestone) | Need enough usage to form a genuine opinion |
| **Healthcare** | 1-2 days after appointment | Compliance-sensitive; must be careful with messaging |
| **Hotels** | Day after checkout | Experience is complete and fresh |

### Request Channels

| Channel | Response Rate | Best For | Tips |
|---------|--------------|----------|------|
| **Email (post-purchase)** | 5-15% | eCommerce, SaaS, professional services | Personalize with order details; single CTA; mobile-optimized |
| **SMS** | 15-25% | Local services, restaurants, healthcare | Keep to 160 characters; direct link; time within business hours |
| **In-person ask** | 30-50% | Retail, restaurants, services | Train staff to ask after positive interaction; provide card with QR code |
| **QR code (physical)** | 5-10% | Retail stores, restaurants, offices | Place at point of sale, on receipts, on table tents |
| **In-app prompt** | 10-20% | SaaS, mobile apps | Trigger after success moment (not randomly); allow dismissal |
| **Post-support follow-up** | 10-20% | Any business with support | Only request after positive resolution (CSAT 4-5) |

### Review Landing Page Design

Create a branded review page that simplifies the process:

1. **Thank the customer** — One sentence acknowledging their business
2. **Show platform options** — Display 2-3 platform icons with direct review links
3. **Prioritize your target platform** — Make Google (or your priority platform) the largest/first button
4. **Pre-fill where possible** — Some platforms allow URL parameters for star pre-selection (use cautiously — review gating is prohibited)
5. **Mobile-optimize** — 70%+ of review requests are opened on mobile

---

## Response Framework by Rating

### 5-Star Reviews

**Strategy:** Reinforce the positive, reference specifics, invite return engagement.

```
Hi [Name], thank you so much for the kind words! We're thrilled to
hear that [specific thing they mentioned — e.g., "Sarah made your
experience seamless"]. [That's exactly what we aim for / We'll pass
along the compliment to the team]. We'd love to see you again —
[relevant invitation, e.g., "our spring collection launches next
month"]. Thank you for your support!
```

**Timing:** Within 48 hours. **Tone:** Warm, specific, brief.

### 4-Star Reviews

**Strategy:** Thank sincerely, acknowledge the suggestion or gap, signal improvement.

```
Thank you for the thoughtful review, [Name]. We're glad
[specific positive they mentioned] met your expectations. We
appreciate your note about [specific suggestion or concern] —
that's exactly the kind of feedback that helps us improve.
[We're already working on X / We've shared this with our team].
Hope to earn that 5th star next time!
```

**Timing:** Within 48 hours. **Tone:** Appreciative, action-oriented.

### 3-Star Reviews

**Strategy:** Thank for honesty, address specific concerns, offer a path to resolution.

```
Hi [Name], thank you for taking the time to share your experience.
We're glad [positive aspect they mentioned], but we understand that
[specific concern] fell short of what you expected. That's not the
standard we hold ourselves to. [Specific action: "We've spoken with
our team about X" / "We've adjusted our process for Y"]. If you're
open to it, we'd love the chance to make it right — please reach
out to [contact method].
```

**Timing:** Within 24 hours. **Tone:** Empathetic, solution-focused, not defensive.

### 2-Star Reviews

**Strategy:** Empathize, take responsibility, move to private conversation, offer specific resolution.

```
[Name], we're sorry to hear about your experience with
[specific issue]. That's not acceptable, and we take this
seriously. I'd like to personally look into what happened
and make this right. Could you reach out to me directly at
[email/phone]? I want to understand the full situation and
find a solution for you. — [Name, Title]
```

**Timing:** Within 12-24 hours. **Tone:** Personal, accountable, urgent.

### 1-Star Reviews

**Strategy:** Empathize immediately, no excuses, investigate, escalate internally, offer direct contact.

```
[Name], I'm truly sorry for this experience. This does not
reflect who we are or the standard we set for ourselves. I
want to investigate this personally and make it right. Please
contact me directly at [email] or [phone] — I'll prioritize
your case. We owe you better than this. — [Name, Title]
```

**Timing:** Within 6-12 hours. **Tone:** Empathetic, personal, executive-level when warranted.

### Response Rules (All Ratings)

- Never copy/paste the same response across reviews — each response must be unique
- Never argue with a reviewer publicly
- Never offer compensation publicly (do it privately)
- Never ask a reviewer to change or remove their review
- Always respond from a named person when possible (not "The Team")
- Keep responses under 150 words for positive reviews, under 200 words for negative
- Never reveal private customer details in a public response

---

## Review Monitoring Tools

| Tool | Starting Price | Platforms Monitored | Key Strength |
|------|---------------|--------------------| -------------|
| **Google Alerts** | Free | Web mentions (not review-specific) | Free baseline monitoring; limited to web search results |
| **BrightLocal** | $39/mo | Google, Facebook, Yelp, 80+ sites | Best for local SEO agencies managing multiple locations |
| **ReviewTrackers** | Custom | 100+ review sites | Enterprise-grade analytics; sentiment trending |
| **Birdeye** | $299/mo | 200+ sites; includes messaging | All-in-one: monitoring + generation + messaging |
| **Podium** | $399/mo | Google, Facebook + messaging | Strong SMS review request automation |
| **Reputation.com** | Custom | 100+ sites | Enterprise; multi-location management at scale |
| **Yext** | $199/mo | 200+ directories + review sites | Listings management + review monitoring combined |

### Tool Selection Criteria

| Business Type | Recommended Tool Tier |
|--------------|----------------------|
| Single location, bootstrap budget | Google Alerts (free) + manual monitoring |
| Single location, growth budget | BrightLocal or Podium |
| Multi-location (5-50 locations) | Birdeye or ReviewTrackers |
| Enterprise (50+ locations) | Reputation.com or Yext |
| SaaS / B2B | G2 + Capterra dashboards (free) + BrightLocal for web reviews |

---

## Review Aggregation & Schema Markup

### Aggregate Rating Schema

Add structured data to your website to display star ratings in search results:

```json
{
  "@context": "https://schema.org",
  "@type": "LocalBusiness",
  "name": "Business Name",
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.7",
    "reviewCount": "312",
    "bestRating": "5",
    "worstRating": "1"
  }
}
```

**Important:** Google requires that aggregate ratings come from genuine first-party reviews collected on your site — not scraped from third-party platforms. Misrepresenting review sources violates Google's structured data guidelines and can result in manual action.

---

## Fake Review Detection

### Red Flag Patterns

| Pattern | Description | Detection Method |
|---------|-------------|-----------------|
| **Cluster timing** | Multiple 5-star reviews within hours or days | Plot review dates; look for unnatural clusters |
| **Generic language** | Vague praise with no specific details ("Great place! Highly recommend!") | Manual read; NLP analysis for specificity score |
| **No photos or profile history** | Reviewers with new accounts, no profile photo, no other reviews | Click through to reviewer profile |
| **One-review accounts** | Reviewer has only ever left one review (this one) | Profile audit; common with purchased reviews |
| **Copied text** | Same or near-identical text across multiple reviews | Search unique phrases from reviews; plagiarism detection |
| **Reviewer location mismatch** | Reviewer is from a different country/region than the business | Check reviewer profile location vs. business location |
| **Sudden rating shift** | Average rating jumps dramatically in a short period | Monitor rating trends over time |
| **Competitor attack** | Sudden cluster of 1-star reviews with similar language | Analyze timing, language patterns, and reviewer profiles |

### What to Do About Fake Reviews

| Situation | Action |
|-----------|--------|
| Fake positive reviews on your profile (not yours) | Remove if you can; report to platform; never solicit fake reviews |
| Fake negative reviews (competitor attack) | Document evidence; report to platform with specific policy violations cited; respond professionally and publicly |
| Fake reviews on competitor profiles | Do nothing — focus on earning genuine reviews; never report competitor reviews unless they violate platform policies |

---

## Platform-Specific Policies

### Google Business Profile

- **Prohibited:** Review gating (routing positive to Google, negative to private feedback), fake reviews, reviews from employees, incentivized reviews (offering discounts for reviews)
- **Allowed:** Asking all customers for reviews (without filtering by sentiment), providing a direct link, reminding customers
- **Removal process:** Flag review > select violation > Google reviews (takes 3-14 days; no guarantee of removal)
- **Impact on ranking:** Review quantity, quality, and recency are confirmed local ranking factors

### Yelp

- **Prohibited:** Asking for reviews on Yelp (Yelp's official policy discourages solicitation), offering incentives, review kiosks
- **Recommendation filter:** Yelp's algorithm filters reviews it deems unreliable into a "not currently recommended" section; this is opaque and cannot be appealed
- **Strategy:** Focus on great service; display Yelp badge but don't explicitly ask for Yelp reviews; respond to all reviews promptly

### Amazon

- **Prohibited:** Incentivized reviews (except Vine program), reviews from family/friends, manipulating reviews with refunds or discounts
- **Verified purchase badge:** Reviews from verified purchases carry significantly more weight in ranking
- **Vine program:** Amazon's official program where trusted reviewers receive free products in exchange for honest reviews

### Trustpilot

- **Open platform:** Anyone can leave a review, even without a purchase (business can flag for verification)
- **Invitation-only option:** Businesses can close their profile to only accept reviews from invited customers
- **Transparency reports:** Trustpilot publishes reports on fake review activity

---

## Review Analytics

### Sentiment Analysis Framework

Track these metrics monthly across all platforms:

| Metric | Formula | Benchmark |
|--------|---------|-----------|
| **Overall sentiment score** | (Positive reviews - Negative reviews) / Total reviews | > 0.70 |
| **Rating trend** | Average rating this month vs. prior 3-month average | Stable or improving |
| **Review velocity** | New reviews per month | Growing month-over-month |
| **Response rate** | Reviews responded to / Total reviews | > 90% for negative, > 50% for positive |
| **Response time** | Median time from review posting to response | < 24 hours negative, < 48 hours positive |

### Keyword Extraction Categories

Analyze review text to identify recurring themes:

| Category | Example Keywords | Action |
|----------|-----------------|--------|
| **Product quality** | "quality", "durable", "broke", "cheap", "excellent" | Product team feedback |
| **Service experience** | "friendly", "rude", "helpful", "waited", "ignored" | Staff training |
| **Pricing** | "expensive", "worth it", "overpriced", "great value", "deal" | Pricing strategy |
| **Speed / timeliness** | "fast", "slow", "on time", "delayed", "quick" | Operations optimization |
| **Cleanliness / environment** | "clean", "dirty", "ambiance", "comfortable", "run-down" | Facilities management |
| **Specific staff** | Individual names mentioned positively or negatively | Recognition or coaching |

### Competitor Review Comparison

| Metric | Your Business | Competitor A | Competitor B | Competitor C |
|--------|--------------|--------------|--------------|--------------|
| Google rating | ___ | ___ | ___ | ___ |
| Google review count | ___ | ___ | ___ | ___ |
| Yelp rating | ___ | ___ | ___ | ___ |
| Top positive theme | ___ | ___ | ___ | ___ |
| Top negative theme | ___ | ___ | ___ | ___ |
| Response rate | ___ | ___ | ___ | ___ |
| Review velocity (monthly) | ___ | ___ | ___ | ___ |

---

## Legal Considerations

### Review Solicitation Laws

- **FTC Act Section 5:** Prohibits unfair or deceptive acts; fake or undisclosed incentivized reviews violate this
- **Consumer Review Fairness Act (2016):** Businesses cannot use contract clauses to prevent customers from leaving honest reviews; non-disparagement clauses in consumer contracts are void
- **State laws:** California, New York, and other states have additional consumer review protection statutes

### Review Gating Prohibition

- **What it is:** Asking customers for their rating first, then directing happy customers to leave a public review while routing unhappy customers to a private feedback form
- **Why it's prohibited:** Google, Yelp, and FTC consider this deceptive; it artificially inflates public ratings
- **The correct approach:** Ask all customers for a review on the same platform with the same process, regardless of expected sentiment

### Defamation and False Reviews

- **A review is protected speech if:** It states an opinion, is based on actual experience, and does not contain provably false statements of fact
- **A review may be defamatory if:** It contains provably false factual claims that damage the business, and was made with knowledge of falsity or reckless disregard for truth
- **Practical advice:** Pursuing defamation claims against reviewers almost always generates negative publicity (the "Streisand effect"); exhaust platform dispute processes before considering legal action

### FTC Endorsement Guidelines (Updated 2023)

- Reviews from employees, family, or affiliates must disclose the relationship
- Incentivized reviews must disclose the incentive (and many platforms prohibit them entirely)
- Businesses are liable for employee review solicitation practices even if not directly authorized
- Penalties: Up to $50,120 per violation (adjusted annually for inflation)
