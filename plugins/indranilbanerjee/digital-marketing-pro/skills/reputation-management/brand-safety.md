# Brand Safety — 4-Layer Protection Framework

> Protecting your brand from appearing alongside harmful, inappropriate, or off-brand content. One misplacement can undo years of brand building. This framework provides four layers of defense so that never happens.

---

## The 4-Layer Protection Model

```
Layer 4: Owned Content Safety        ← What you publish
Layer 3: Partner Safety               ← Who you associate with
Layer 2: Platform Safety              ← Where your ads appear
Layer 1: Content Adjacency            ← What appears next to your ads
```

Each layer addresses a different attack surface. Robust brand safety requires all four.

---

## Layer 1 — Content Adjacency

Content adjacency is the most common brand safety risk: your ad appearing next to objectionable content on publisher sites, YouTube videos, or social feeds.

### GARM Brand Safety Categories (Industry Standard)

| Category | Risk Level | Examples | Default Action |
|----------|-----------|----------|----------------|
| Adult & Explicit Sexual Content | High | Pornography, graphic sexual content | Block |
| Arms & Ammunition | High | Weapons sales, tactical gear | Block (most brands) |
| Crime & Harmful Acts | High | Violence promotion, illegal activity tutorials | Block |
| Death, Injury & Military Conflict | High | Graphic war footage, accident videos | Block |
| Online Piracy | High | Torrent sites, illegal streaming | Block |
| Hate Speech & Discrimination | High | Extremist content, slurs | Block |
| Obscenity & Profanity | Medium | Casual profanity in entertainment | Case-by-case |
| Illegal Drugs / Tobacco / Alcohol | Medium | Drug culture content, vaping promotion | Industry-dependent |
| Spam / Malware | High | Click farms, malicious sites | Block |
| Terrorism | High | Extremist propaganda | Block |
| Sensitive Social Issues | Medium | Political debates, social justice | Case-by-case |
| Misinformation | High | Fake news, conspiracy theories | Block |

### Keyword Exclusion Lists

**Universal Block List (apply to all campaigns):**
```
tragedy, shooting, terrorist, bomb, assault, murder, scandal,
arrest, abuse, trafficking, extremist, conspiracy, hoax,
pornography, explicit, hate crime, mass shooting, genocide,
drug overdose, suicide, self-harm
```

**News-Sensitive Block List (activate during breaking events):**
```
breaking news, developing story, crisis, emergency, disaster,
casualties, victims, manhunt, evacuation
```

**Political Block List (for brands avoiding political adjacency):**
```
election, candidate name, party name, impeach, ballot,
partisan, left-wing, right-wing, propaganda
```

> **Important:** Overly aggressive keyword blocking can tank reach. Review block lists quarterly and monitor impression loss vs. safety trade-off.

---

## Layer 2 — Platform Safety

### Google Ads — Brand Safety Settings

| Setting | Location | Recommendation |
|---------|----------|----------------|
| Content exclusions | Campaign → Settings → Content exclusions | Exclude: DL-MA, Live streaming (unless relevant), Parked domains |
| Topic exclusions | Campaign → Content → Topics (Exclusions) | Exclude sensitive topics per GARM categories |
| Placement exclusions | Campaign → Content → Placements (Exclusions) | Maintain exclusion list of 500+ sites (update monthly) |
| Inventory type | Campaign → Settings → Inventory type | Use "Limited inventory" for maximum safety |
| Brand suitability | Google Ads → Tools → Brand suitability | Enable and configure content labels |

### Meta (Facebook / Instagram) — Brand Safety Settings

| Setting | Location | Recommendation |
|---------|----------|----------------|
| Inventory filter | Business Settings → Brand Safety → Inventory Filter | Full inventory (broadest), Standard (recommended), Limited (strictest) |
| Block lists | Business Settings → Brand Safety → Block Lists | Upload publisher block list (CSV) |
| Content type exclusions | Ad Set → Placements → Brand Safety | Exclude in-stream for sensitive brands |
| Publisher allow lists | Business Settings → Brand Safety → Publisher Lists | Use for premium-only placement strategies |

### YouTube — Brand Safety Settings

| Setting | Location | Recommendation |
|---------|----------|----------------|
| Content suitability | Google Ads → Inventory type | "Limited inventory" excludes most risk |
| Channel exclusions | Placements → Exclusions | Exclude specific channels flagged by monitoring |
| Topic exclusions | Content → Topics → Exclusions | Mirror GARM exclusions |
| Lineups | Google Ads → YouTube lineups | Use curated lineups for premium inventory |

### Programmatic (DV360, TTD, Xandr)

| Setting | Recommendation |
|---------|----------------|
| Pre-bid filtering | Enable IAS or DV pre-bid segments |
| Domain allow/block lists | Maintain curated allow list (preferred) or comprehensive block list |
| App allow/block lists | Block app categories: casual games, utility, VPN |
| Supply path optimization | Prefer direct-sold inventory, authorized resellers only (ads.txt verified) |
| Deal-based buying | Use PMPs and PG deals for highest safety |

---

## Layer 3 — Partner Safety

### Influencer Brand Safety Checklist

Before engaging any influencer or creator:

- [ ] Audit last 12 months of content for controversial statements
- [ ] Check for past brand safety incidents (search: "[name] controversy")
- [ ] Review follower demographics (bot checks, audience quality)
- [ ] Search for association with extremist groups or figures
- [ ] Verify they haven't promoted competing or conflicting brands recently
- [ ] Include morality/brand safety clause in contract
- [ ] Require content approval before publishing
- [ ] Set up real-time monitoring during campaign window

### Partner / Sponsorship Safety

| Evaluation Criteria | Risk Question | Action if Flagged |
|---------------------|--------------|-------------------|
| Event sponsorship | Has this event had safety incidents before? | Enhanced due diligence, exit clause in contract |
| Co-branding | Does partner brand align with our values? | Brand values alignment assessment |
| Affiliate programs | Are affiliates placing ads on safe inventory? | Require affiliates to use your approved placement lists |
| Reseller / distributor | Are they selling in authorized channels? | MAP enforcement, channel monitoring |

---

## Layer 4 — Owned Content Safety

### Pre-Publication Content Review

| Content Type | Review Process | Reviewers |
|-------------|---------------|-----------|
| Blog posts | Sensitivity read + legal review (if claims made) | Editor + Legal |
| Social posts | Brand voice check + cultural sensitivity review | Social Lead + Diversity advocate |
| Email campaigns | Compliance check (CAN-SPAM, GDPR) + tone review | Email Lead + Legal |
| Video content | Full script review + final cut review | Creative Director + Legal |
| User-generated content | Moderation before amplification | Community Manager |
| AI-generated content | Fact-check + hallucination review + bias check | Subject matter expert |

### Cultural Sensitivity Calendar

Maintain awareness of dates/events where brand messaging must be adjusted:

| Period | Consideration |
|--------|--------------|
| Religious holidays (all faiths) | Avoid tone-deaf promotions |
| National tragedies / anniversaries | Pause promotional messaging |
| Political election seasons | Avoid anything interpretable as partisan |
| Cultural awareness months | Participate authentically or not at all |
| International campaigns | Local cultural review for every market |

---

## Brand Safety Vendor Evaluation

| Vendor | Strengths | Best For | Integration |
|--------|-----------|----------|-------------|
| **IAS (Integral Ad Science)** | Strong pre-bid, contextual targeting, industry benchmarks | Programmatic-heavy advertisers | DV360, TTD, Xandr, Meta, YouTube |
| **DoubleVerify (DV)** | Comprehensive coverage, attention metrics, custom categories | Enterprise brands needing granular control | All major DSPs, social platforms |
| **MOAT (Oracle)** | Viewability + brand safety combined, competitive analytics | Viewability-focused campaigns | Oracle ecosystem, major DSPs |
| **Zefr** | YouTube-specific brand suitability, video-level targeting | YouTube-heavy advertisers | YouTube, connected TV |
| **Channel Factory** | YouTube optimization, performance + safety balance | Performance marketers on YouTube | YouTube |

### Vendor Selection Criteria

| Criteria | Weight | Questions to Ask |
|----------|--------|-----------------|
| Coverage | 25% | Which platforms/exchanges are covered? |
| Accuracy | 25% | What is the false positive/negative rate? |
| Granularity | 20% | Can I create custom brand safety categories? |
| Reporting | 15% | Real-time dashboards? Post-campaign analysis? |
| Cost | 15% | CPM surcharge? Flat fee? Tiered pricing? |

---

## Brand Safety Audit Checklist (Quarterly)

- [ ] Review and update keyword exclusion lists
- [ ] Audit placement reports for all active campaigns (flag any misplacements)
- [ ] Update publisher block/allow lists based on last quarter's data
- [ ] Review influencer roster for any new controversies
- [ ] Test brand safety vendor accuracy (sample audit of 100 placements)
- [ ] Update GARM category settings if brand positioning has shifted
- [ ] Review programmatic supply paths (ads.txt/sellers.json compliance)
- [ ] Conduct cultural sensitivity calendar review for next quarter
- [ ] Check AI-generated content outputs for bias or hallucination patterns
- [ ] Brief creative and media teams on any new brand safety policies

---

## Crisis-Triggered Brand Safety Protocols

When a crisis occurs (see `crisis-communication.md`), immediately activate:

| Action | Timeline | Owner |
|--------|----------|-------|
| Pause all programmatic campaigns | Within 15 minutes | Media team |
| Pause social ad campaigns | Within 15 minutes | Social team |
| Review scheduled organic posts for tone-appropriateness | Within 30 minutes | Content team |
| Add crisis-specific keywords to block lists | Within 1 hour | Media team |
| Notify brand safety vendor of elevated risk | Within 1 hour | Media team |
| Resume campaigns only after explicit approval from crisis commander | When cleared | Incident Commander |

---

> **Brand safety is not a set-and-forget configuration.** It requires continuous monitoring, quarterly audits, and rapid adaptation when the environment shifts. The cost of one brand safety failure always exceeds the cost of prevention.
