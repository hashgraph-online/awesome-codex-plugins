# UTM Tracking — Naming Conventions & Governance

## UTM Parameter Definitions

| Parameter | Required | Purpose | Example |
|-----------|----------|---------|---------|
| `utm_source` | Yes | Where the traffic comes from | google, facebook, linkedin, newsletter |
| `utm_medium` | Yes | How the traffic arrives | cpc, social, email, referral, organic |
| `utm_campaign` | Yes | Which campaign | 2025-q2-product-launch |
| `utm_term` | Optional | Paid keyword (search ads) | project-management-software |
| `utm_content` | Optional | Which creative/variation | hero-image-v2, cta-blue |

---

## Naming Convention Rules

1. **Always lowercase**: `facebook` not `Facebook`
2. **Hyphens for spaces**: `product-launch` not `product_launch` or `product launch`
3. **No special characters**: Only a-z, 0-9, and hyphens
4. **Consistent terminology**: Use the standardized source/medium values below
5. **Date format**: YYYY-QN or YYYY-MM (e.g., `2025-q2` or `2025-06`)
6. **Descriptive but concise**: Enough to identify, not a full sentence

---

## Standardized Source/Medium Values

### Sources (utm_source)

| Value | Use For |
|-------|---------|
| `google` | Google Ads, organic |
| `facebook` | Facebook/Meta organic and paid |
| `instagram` | Instagram organic and paid |
| `linkedin` | LinkedIn organic and paid |
| `twitter` | Twitter/X |
| `tiktok` | TikTok organic and paid |
| `youtube` | YouTube |
| `pinterest` | Pinterest |
| `bing` | Microsoft/Bing Ads |
| `email` | Email campaigns (your ESP) |
| `newsletter` | Newsletter specifically |
| `partner-[name]` | Co-marketing partner |
| `influencer-[name]` | Influencer campaigns |
| `podcast-[name]` | Podcast sponsorship |
| `qr` | QR code scans |
| `direct-mail` | Physical direct mail |
| `event-[name]` | In-person events |

### Mediums (utm_medium)

| Value | Use For |
|-------|---------|
| `cpc` | Paid search (cost per click) |
| `paid-social` | Paid social media ads |
| `social` | Organic social media |
| `email` | Email marketing |
| `referral` | Partner/affiliate referral |
| `display` | Display/banner advertising |
| `video` | Video advertising (YouTube, CTV) |
| `affiliate` | Affiliate marketing |
| `influencer` | Influencer partnerships |
| `organic` | Organic search (not typically tagged) |
| `pr` | Press/media coverage |
| `podcast` | Podcast advertising |
| `sms` | SMS/text message marketing |
| `push` | Push notification |
| `direct-mail` | Physical mail |
| `qr` | QR code |

---

## Campaign Naming Format

```
utm_campaign = [year]-[quarter]-[type]-[audience]-[description]
```

**Examples**:
- `2025-q2-launch-enterprise-ai-features`
- `2025-q3-promo-all-summer-sale`
- `2025-q1-abm-target-accounts-nurture`
- `2025-evergreen-retargeting-website-visitors`

---

## UTM Content Tag Patterns

Use `utm_content` to differentiate:

| Pattern | Example | Use Case |
|---------|---------|----------|
| `[format]-[variant]` | `carousel-v2` | Ad format testing |
| `[position]-[cta]` | `hero-signup` | Email link position |
| `[audience]-[message]` | `cfo-roi-focus` | Audience-message testing |
| `[creative-id]` | `creative-2025-0142` | Linking to creative asset tracking |

---

## Common UTM Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| Inconsistent capitalization | `Facebook` and `facebook` appear as separate sources | Always use lowercase |
| Spaces in parameters | Breaks URL encoding | Use hyphens |
| No UTM on email links | Cannot track email-driven traffic | Tag every email link |
| UTM on internal links | Overwrites the original source attribution | NEVER use UTMs on internal site links |
| Different mediums for same channel | `social`, `social-media`, `organic-social` all different | Standardize to the list above |
| No campaign naming convention | Impossible to aggregate campaigns | Follow naming format |
| Not shortening URLs | Ugly, untrustworthy links in visible placements | Use URL shortener for visible links |

---

## UTM for Offline-to-Online

| Offline Channel | UTM Implementation |
|----------------|-------------------|
| Direct mail | Short URL or QR code with UTMs baked in |
| Print ad | Vanity URL redirecting to UTM-tagged page |
| Event booth | QR code on signage → UTM-tagged landing page |
| Business card | QR code → UTM-tagged URL |
| TV/Radio | Vanity URL (`brand.com/tv`) redirecting with UTMs |
| Billboard | Short URL or QR → UTM-tagged page |

---

## Governance Rules

1. **Single owner**: One person/team owns the UTM taxonomy document
2. **Centralized tracker**: Maintain a spreadsheet of all active UTM parameters
3. **No freelancing**: All team members use standardized values from this document
4. **URL builder tool**: Use a shared UTM builder that enforces naming rules
5. **Quarterly audit**: Review analytics for non-standard UTM values and clean up
6. **New value requests**: Adding a new source/medium value requires updating the standard
