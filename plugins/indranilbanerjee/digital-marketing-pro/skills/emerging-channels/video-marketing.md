# Video Marketing — Format & Distribution Guide

> Video is the dominant content format across every major platform. This guide covers format specifications, production tiers, SEO optimization, distribution strategy, and repurposing workflows to maximize the ROI of every video asset you produce.

---

## Format-by-Platform Guide

### Platform Specifications

| Platform | Format | Aspect Ratio | Max Length | Ideal Length | Resolution |
|----------|--------|-------------|------------|-------------|------------|
| **YouTube (long-form)** | Horizontal | 16:9 | 12 hours | 8-15 min (most topics) | 1920x1080 (min), 3840x2160 (ideal) |
| **YouTube Shorts** | Vertical | 9:16 | 3 min | 30-60 sec | 1080x1920 |
| **TikTok** | Vertical | 9:16 | 10 min | 15-60 sec (sweet spot: 21-34 sec) | 1080x1920 |
| **Instagram Reels** | Vertical | 9:16 | 15 min | 15-30 sec (discovery), 60-90 sec (engagement) | 1080x1920 |
| **Instagram Feed Video** | Square or Vertical | 1:1 or 4:5 | 60 min | 30-60 sec | 1080x1080 or 1080x1350 |
| **Instagram Stories** | Vertical | 9:16 | 60 sec/story | 15 sec per story | 1080x1920 |
| **LinkedIn Video** | Horizontal or Square | 16:9 or 1:1 | 10 min (native) | 1-3 min | 1920x1080 or 1080x1080 |
| **Twitter/X Video** | Horizontal or Square | 16:9 or 1:1 | 2 min 20 sec | 30-60 sec | 1920x1080 or 1080x1080 |
| **Facebook Video** | Horizontal or Square | 16:9 or 1:1 | 240 min | 1-3 min (feed), 3-5 min (Watch) | 1920x1080 |
| **Pinterest Video Pins** | Vertical | 2:3 or 9:16 | 15 min | 15-30 sec | 1000x1500 or 1080x1920 |

### Platform-Specific Content Strategy

| Platform | Content That Performs | Tone | Hook Window |
|----------|---------------------|------|-------------|
| **YouTube** | Tutorials, reviews, deep dives, vlogs, interviews | Educational, thorough, personality-driven | 5 seconds |
| **YouTube Shorts** | Quick tips, reactions, behind-scenes, teasers | Punchy, immediate, pattern-interrupt | 1 second |
| **TikTok** | Trends, demonstrations, storytelling, humor, raw/authentic | Authentic, unpolished, entertaining | 0.5-1 second |
| **Instagram Reels** | Aesthetic demos, transformations, tips, trending audio | Polished but relatable, aspirational | 1 second |
| **LinkedIn** | Thought leadership, case studies, industry insights, career advice | Professional, value-first, no fluff | 3 seconds |
| **Twitter/X** | Hot takes, commentary, clip highlights, news reactions | Opinionated, concise, conversational | 2 seconds |

---

## Production Tiers

### Tier 1 — Phone Production ($0-500)

| Element | Specification |
|---------|-------------- |
| Camera | Smartphone (iPhone 13+ or equivalent Android) |
| Audio | Lavalier mic ($15-30) or wireless mic system ($50-100) |
| Lighting | Natural window light or single ring light ($20-50) |
| Tripod | Phone tripod or mini tripod ($15-30) |
| Editing | CapCut (free), InShot, or built-in phone editor |
| Best for | TikTok, Reels, Stories, YouTube Shorts, social clips |
| Quality level | Authentic, relatable — audiences expect lower production on short-form |

### Tier 2 — Semi-Professional ($500-5,000)

| Element | Specification |
|---------|-------------- |
| Camera | Mirrorless camera (Sony ZV-E10, Canon EOS R50) or high-end webcam (Sony ZV-1) |
| Audio | Shotgun mic (Rode VideoMic) or USB condenser (Blue Yeti, Elgato Wave) |
| Lighting | 2-3 point lighting setup (key, fill, backlight) — Elgato, Neewer, or Aputure |
| Tripod | Full-size tripod + fluid head for smooth movements |
| Editing | DaVinci Resolve (free), Adobe Premiere Pro, Final Cut Pro |
| Teleprompter | Optional — PromptSmart, Teleprompter Premium app |
| Best for | YouTube long-form, LinkedIn, website hero videos, product demos |
| Quality level | Professional, clean — suitable for brand channels and B2B content |

### Tier 3 — Full Production ($5,000-50,000+)

| Element | Specification |
|---------|-------------- |
| Camera | Cinema camera (Blackmagic, RED, Sony FX series) or high-end mirrorless |
| Audio | Professional boom mic, wireless lavs, dedicated audio recorder |
| Lighting | Full studio lighting rig with modifiers, gels, professional grip |
| Set design | Purpose-built set or location scouting + art direction |
| Crew | Director, DP, audio engineer, gaffer, production assistant |
| Editing | Full post-production: color grading, sound design, motion graphics, VFX |
| Best for | Brand campaigns, TV/CTV ads, product launches, company overview videos |
| Quality level | Broadcast/cinematic — premium brand positioning |

---

## Video SEO Checklist

### YouTube SEO (Primary Video Search Engine)

| Element | Best Practice | Impact |
|---------|--------------|--------|
| **Title** | Front-load primary keyword, under 60 characters, compelling hook | High |
| **Description** | First 2 sentences = keyword-rich summary; full description 200-500 words with keywords, timestamps, links | High |
| **Tags** | 5-10 relevant tags: primary keyword, variations, broad category | Medium |
| **Thumbnail** | Custom, high-contrast, face + text, 1280x720px, <2MB | Very High (affects CTR) |
| **Captions/Subtitles** | Upload accurate SRT file (do not rely on auto-captions) | High (SEO + accessibility) |
| **Chapters/Timestamps** | Add timestamps in description (00:00 format) | High (engagement + SERP features) |
| **Cards & End Screens** | Link to related videos, playlists, subscribe prompt | Medium (retention + channel growth) |
| **Playlist inclusion** | Add every video to at least one relevant playlist | Medium (session time) |
| **Hashtags** | 3-5 hashtags in description (#keyword) | Low-Medium |
| **Pinned comment** | Add a keyword-rich pinned comment with CTA | Low |

### Video Schema Markup

```json
{
  "@context": "https://schema.org",
  "@type": "VideoObject",
  "name": "How to Build a Social Media Strategy in 2025",
  "description": "Step-by-step guide to creating a social media strategy...",
  "thumbnailUrl": "https://example.com/thumbnails/social-strategy.jpg",
  "uploadDate": "2025-03-15",
  "duration": "PT12M30S",
  "contentUrl": "https://example.com/videos/social-strategy.mp4",
  "embedUrl": "https://www.youtube.com/embed/xxxxx",
  "interactionStatistic": {
    "@type": "InteractionCounter",
    "interactionType": "https://schema.org/WatchAction",
    "userInteractionCount": 15000
  }
}
```

### Cross-Platform Video SEO

| Platform | SEO Factor | Optimization |
|----------|-----------|-------------|
| YouTube | Search + recommendation algorithm | Keywords in title, description, tags; high CTR thumbnail; watch time |
| TikTok | Discovery algorithm | Trending sounds, hashtags, first-second hook, completion rate |
| Instagram | Explore + Reels algorithm | Trending audio, hashtags (3-5), high engagement in first 30 min |
| LinkedIn | Feed algorithm | Native upload (not YouTube link), captions, first 3 lines compelling |
| Google Search | Video SERP features | VideoObject schema, YouTube hosting, keyword-optimized title |

---

## Thumbnail Design Guide

### Thumbnail Best Practices

| Element | Best Practice |
|---------|--------------|
| **Dimensions** | 1280x720px (16:9), under 2MB |
| **Face** | Include an expressive human face (thumbnails with faces get 38% more clicks) |
| **Text** | 3-5 words max, large bold font, contrasting color |
| **Contrast** | High contrast between subject and background |
| **Branding** | Consistent brand elements (color palette, logo placement, font) |
| **Emotion** | Convey an emotion: surprise, excitement, curiosity, urgency |
| **Avoid** | Clickbait that doesn't match content (kills retention and trust) |
| **Test** | View thumbnail at phone size (the most common viewing context) |

### Thumbnail A/B Testing

YouTube now offers native thumbnail A/B testing. Use it to:
1. Test face vs. no face
2. Test different text overlays
3. Test different color schemes
4. Test different expressions/emotions
5. Run for minimum 7 days or 10,000 impressions before drawing conclusions

---

## Distribution Strategy

### Multi-Platform Distribution Workflow

| Step | Action | Timeline |
|------|--------|----------|
| 1 | Publish full-length video on YouTube | Day 0 |
| 2 | Upload native version to LinkedIn and Facebook | Day 0 (same day) |
| 3 | Post 3-5 short clips as Reels, TikToks, Shorts | Days 1-5 (stagger daily) |
| 4 | Share on Twitter/X with native upload or clip | Day 0-1 |
| 5 | Embed video in related blog post on website | Day 0-1 |
| 6 | Include in email newsletter | Next newsletter send |
| 7 | Pin best-performing clip to social profiles | Ongoing |
| 8 | Add to relevant YouTube playlist | Day 0 |

### Paid Distribution

| Platform | Ad Format | Best For | Typical CPV |
|----------|-----------|----------|-------------|
| YouTube Ads | In-stream (skippable/non-skip), Discovery, Shorts | Awareness, consideration | $0.02-0.10 |
| TikTok Ads | In-feed, TopView, Spark Ads | Gen Z/Millennial awareness | $0.02-0.08 |
| Meta (IG/FB) | In-feed video, Reels ads, Stories ads | Broad awareness, retargeting | $0.01-0.05 |
| LinkedIn Ads | Sponsored video, document ads | B2B awareness, thought leadership | $0.08-0.20 |
| Connected TV | Streaming ads (Roku, Hulu, YouTube CTV) | Mass awareness, brand campaigns | $0.02-0.04 (CPM $20-40) |

---

## Performance Metrics

### Core Video KPIs

| Metric | Definition | Benchmark | Platform |
|--------|-----------|-----------|----------|
| **View count** | Total views (definitions vary by platform) | Growing per video | All |
| **Watch time** | Total minutes watched | YouTube: prioritize total watch hours | YouTube |
| **Average view duration** | Mean time watched per view | >50% of video length | YouTube, Facebook |
| **Completion rate** | % who watched to the end | Short-form: >60%; Long-form: >40% | TikTok, Reels, YouTube |
| **Click-through rate** | Impressions → clicks (thumbnail CTR) | YouTube: >5% | YouTube |
| **Engagement rate** | (Likes + comments + shares + saves) / views | >3% | All social |
| **Subscriber/follower growth** | New subscribers per video | Positive per video | All |
| **Traffic source** | Where views came from (search, suggested, external) | Diversified | YouTube |
| **Conversion rate** | Views → desired action (link click, purchase, signup) | Varies by funnel stage | All |

### Platform-Specific Success Signals

| Platform | Algorithm Rewards | Optimize For |
|----------|------------------|-------------|
| YouTube | Watch time, CTR, session time | Longer watch duration, high CTR thumbnails, end screens to next video |
| TikTok | Completion rate, rewatches, shares | Short + rewatchable, loop-friendly endings, share-worthy content |
| Instagram Reels | Saves, shares, completion rate | Save-worthy tips, share-worthy humor, satisfying completions |
| LinkedIn | Dwell time, comments, native video | Conversation-starting content, text hooks in first line |

---

## Repurposing Workflow — Long-Form to Multi-Platform

### The Content Waterfall

```
Long-Form Video (8-15 min, YouTube)
│
├─→ 3-5 Short Clips (30-60 sec) → TikTok, Reels, Shorts
│
├─→ Audiogram (60-90 sec, waveform visual) → Twitter/X, LinkedIn
│
├─→ Key Frames / Screenshots → Quote graphics for Instagram, LinkedIn
│
├─→ Transcript → Blog post (SEO) + Newsletter excerpt
│
├─→ Audio Extract → Podcast feed (if applicable)
│
├─→ Key Insights → Twitter/X thread (5-8 tweets)
│
└─→ Slide Deck → LinkedIn document post / SlideShare
```

### Clip Selection Criteria

When choosing which moments to extract as short-form clips:

| Criteria | Why |
|----------|-----|
| **Self-contained insight** | Clip must make sense without context from the full video |
| **Strong hook** | First 1-2 seconds grab attention |
| **Emotional reaction** | Surprise, humor, strong opinion, controversial take |
| **Actionable tip** | Viewers can implement something immediately |
| **Visual demonstration** | Something being shown, not just discussed |
| **Natural ending** | Clip has a satisfying conclusion (not mid-sentence cutoff) |

### Editing Workflow for Repurposing

| Step | Tool | Time Estimate |
|------|------|--------------|
| 1. Record long-form video | Camera + audio setup | 30-60 min |
| 2. Edit long-form version | Premiere Pro, Final Cut, DaVinci Resolve | 2-4 hours |
| 3. Auto-transcribe | Descript, Otter.ai, Premiere auto-transcribe | 5 minutes |
| 4. Identify clip-worthy moments | Review transcript, mark timestamps | 30 minutes |
| 5. Export vertical clips (9:16) | Premiere Pro auto-reframe or CapCut | 30-60 min |
| 6. Add captions to clips | CapCut auto-captions, Descript, Zubtitle | 15-30 min |
| 7. Create audiograms | Headliner, Descript | 15 min |
| 8. Pull quote screenshots | Canva template | 15 min |
| 9. Edit transcript into blog post | Manual editing | 30-60 min |
| 10. Schedule across platforms | Buffer, Hootsuite, Later, or native scheduling | 15 min |

**Total time to produce 10+ content pieces from one video: 5-8 hours**

---

## Video Content Calendar Template

| Week | Long-Form (YouTube) | Short-Form (TikTok/Reels/Shorts) | LinkedIn | Twitter/X |
|------|--------------------|---------------------------------|----------|-----------|
| 1 | Tutorial: "How to {{topic}}" | 3 clips from tutorial + 2 trending/reactive | 1 native video (insight from tutorial) | 2 clips + 1 thread |
| 2 | Interview/podcast episode | 3 clips from interview + 2 trending | 1 thought leadership video | 2 clips + 1 thread |
| 3 | List/review: "Top 5 {{tools}}" | 3 clips from list + 2 trending | 1 case study video | 2 clips + 1 thread |
| 4 | Behind-the-scenes / vlog | 3 clips from BTS + 2 trending | 1 industry commentary | 2 clips + 1 thread |

**Monthly output from this calendar: 4 long-form + 20 short-form + 4 LinkedIn + 12 Twitter = 40 video pieces**

---

> **The best video strategy is not about producing more — it is about producing once and distributing everywhere.** One well-planned long-form video becomes a week of multi-platform content. Invest in the production. Multiply through repurposing. Measure relentlessly.
