# Platform Specs Reference

Character limits, format requirements, and practices for each ad platform.
Google Ads and Performance Max values were checked against Google Ads Help in
October 2026. Meta, LinkedIn, TikTok, and X values are the platforms' long-stable
published limits; confirm them in the ad preview before launch, because
recommended lengths and placements change more often than hard limits.

---

## Google Ads

### Responsive Search Ads (RSAs)

| Element | Character Limit | Required | Notes |
|---------|----------------|----------|-------|
| Headline | 30 chars | 3 minimum, 15 max | Any 3 may be shown together |
| Description | 90 chars | 2 minimum, 4 max | Any 2 may be shown together |
| Display path 1 | 15 chars | Optional | Appears after domain in URL |
| Display path 2 | 15 chars | Optional | Appears after path 1 |
| Final URL | No limit | Required | Landing page URL |

**Combination rules:**
- Google selects up to 3 headlines and 2 descriptions to show
- Headlines appear separated by " | " or stacked
- Any headline can appear in any position unless pinned
- Pinning reduces Google's ability to optimize: use sparingly

**Pinning strategy:**
- Pin your brand name to position 1 if brand guidelines require it
- Pin your strongest CTA to position 2 or 3
- Leave most headlines unpinned for machine learning

**Headline mix recommendation (15 headlines):**
- 3-4 keyword-focused (match search intent)
- 3-4 benefit-focused (what they get)
- 2-3 social proof (numbers, awards, customers)
- 2-3 CTA-focused (action to take)
- 1-2 differentiators (why you over competitors)
- 1 brand name headline

**Description mix recommendation (4 descriptions):**
- 1 benefit + proof point
- 1 feature + outcome
- 1 social proof + CTA
- 1 urgency/offer + CTA (if applicable)

### Performance Max (Google Ads Help, answer 17091269, checked October 2026)

| Element | Limit | Count | Notes |
|---------|-------|-------|-------|
| Headline | 30 chars | 3 to 15 (11+ recommended) | Include at least one of 15 chars or fewer |
| Long headline | 90 chars | 1 to 5 (2+ recommended) | Aim for 30+ chars |
| Description | 90 chars | 2 to 5 (4+ recommended) | |
| Business name | 25 chars | 1 | Must match the domain or the verified legal business name |
| Display path | 15 chars each | up to 2 | |
| Horizontal image 1.91:1 | 1200x628 recommended, 600x314 min | up to 20 | Required |
| Square image 1:1 | 1200x1200 recommended, 300x300 min | up to 20 | Required |
| Vertical image 4:5 | 960x1200 recommended | up to 20 | Optional |
| Square logo 1:1 | 1200x1200 recommended, 128x128 min | up to 5 | Required |
| Video | 10 seconds or longer | up to 15 per orientation | Without your own 16:9, 1:1, and 9:16 videos, Google may auto-generate one |

Image files: JPG or PNG, 5 MB max.

### Display Ads

| Element | Character Limit |
|---------|----------------|
| Headline | 30 chars |
| Long headline | 90 chars |
| Description | 90 chars |
| Business name | 25 chars |

---

## Meta Ads (Facebook & Instagram)

### Single Image / Video / Carousel

| Element | Recommended | Maximum | Notes |
|---------|-------------|---------|-------|
| Primary text | 125 chars | 2,200 chars | Text above image; truncated after ~125 |
| Headline | 40 chars | 255 chars | Below image; truncated after ~40 |
| Description | 30 chars | 255 chars | Below headline; may not show |
| URL display link | 40 chars | N/A | Optional custom display URL |

**Placement-specific notes:**
- **Feed**: All elements show; primary text most visible
- **Stories/Reels**: Primary text overlaid; keep under 72 chars
- **Right column**: Only headline visible; skip description
- **Audience Network**: Varies by publisher

**Best practices:**
- Front-load the hook in primary text (first 125 chars)
- Use line breaks for readability in longer primary text
- Emojis: test, but don't overuse: 1-2 per ad max
- Questions in primary text increase engagement
- Headline should be a clear CTA or value statement

### Lead Ads (Instant Form)

| Element | Limit |
|---------|-------|
| Greeting headline | 60 chars |
| Greeting description | 360 chars |
| Privacy policy text | 200 chars |

---

## LinkedIn Ads

### Single Image Ad

| Element | Recommended | Maximum | Notes |
|---------|-------------|---------|-------|
| Intro text | 150 chars | 600 chars | Above the image; truncated after ~150 |
| Headline | 70 chars | 200 chars | Below the image |
| Description | 100 chars | 300 chars | Only shows on Audience Network |

### Carousel Ad

| Element | Limit |
|---------|-------|
| Intro text | 255 chars |
| Card headline | 45 chars |
| Card count | 2-10 cards |

### Message Ad (InMail)

| Element | Limit |
|---------|-------|
| Subject line | 60 chars |
| Message body | 1,500 chars |
| CTA button | 20 chars |

### Text Ad

| Element | Limit |
|---------|-------|
| Headline | 25 chars |
| Description | 75 chars |

**LinkedIn-specific guidelines:**
- Professional tone, but not boring
- Use job-specific language the audience recognizes
- Statistics and data points perform well
- Avoid consumer-style hype ("Amazing!" "Incredible!")
- First-person testimonials from peers resonate

---

## TikTok Ads

### In-Feed Ads

| Element | Recommended | Maximum | Notes |
|---------|-------------|---------|-------|
| Ad text | 80 chars | 100 chars | Above the video |
| Display name | N/A | 40 chars | Brand name |
| CTA button | Platform options | Predefined | Select from TikTok's options |

### Spark Ads (Boosted Organic)

| Element | Notes |
|---------|-------|
| Caption | Uses original post caption |
| CTA button | Added by advertiser |
| Display name | Original creator's handle |

**TikTok-specific guidelines:**
- Native-looking content usually beats polished ads; test both
- The opening seconds decide the watch
- Use trending sounds only with commercial-use rights (the Commercial Music
  Library for business accounts)
- Text overlay inside safe zones; keep it short
- Vertical 9:16 is the default canvas

---

## Twitter/X Ads

### Promoted Tweets

| Element | Limit | Notes |
|---------|-------|-------|
| Tweet text | 280 chars | Full tweet with image/video |
| Card headline | 70 chars | Website card |
| Card description | 200 chars | Website card |

### Website Cards

| Element | Limit |
|---------|-------|
| Headline | 70 chars |
| Description | 200 chars |

**Twitter/X-specific guidelines:**
- Conversational, casual tone
- Short sentences work best
- One clear message per tweet
- Hashtags: 1-2 max (0 is often better for ads)
- Threads can work for consideration-stage content

---

## Character Counting Tips

- **Spaces count** as characters on all platforms
- **Emojis** count as 1-2 characters depending on platform
- **Special characters** (|, &, etc.) count as 1 character
- **URLs** in body text count against limits
- **Dynamic keyword insertion** (`{KeyWord:default}`) can exceed limits, set safe defaults
- Always verify in the platform's ad preview before launching

---

## Multi-Platform Creative Adaptation

When creating for multiple platforms simultaneously, start with the most restrictive format:

1. **Google Search headlines** (30 chars): forces the tightest messaging
2. **Expand to Meta headlines** (40 chars): add a word or two
3. **Expand to LinkedIn intro text** (150 chars): add context and proof
4. **Expand to Meta primary text** (125+ chars): full hook and value prop

This cascading approach ensures your core message works everywhere, then gets enriched for platforms that allow more space.
