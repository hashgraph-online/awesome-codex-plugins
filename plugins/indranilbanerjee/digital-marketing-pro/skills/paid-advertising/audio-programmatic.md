# Audio Programmatic Advertising — Streaming, Podcasts & Digital Audio

## Audio Advertising Ecosystem

### Platform Landscape

| Platform | Users / Reach | Ad Model | Unique Advantage | Self-Serve |
|---|---|---|---|---|
| **Spotify Ad Studio** | 600M+ users, 220M+ ad-supported | Self-serve + managed | Mood/activity targeting, playlist context, companion display | Yes ($250 min) |
| **Pandora / SiriusXM Media** | 50M+ ad-supported listeners | Managed + programmatic | Largest audio ad network in US, Music Genome targeting | Limited (SXM Media portal) |
| **iHeartRadio** | 150M+ monthly users | Managed + programmatic | Broadcast radio + streaming combo, local targeting strength | Managed only |
| **Amazon Music / Alexa** | 100M+ users | Amazon DSP | Shopping intent integration, Alexa voice CTA | Via Amazon DSP |
| **YouTube Music** | 80M+ music subscribers + ad-tier | Google Ads / DV360 | Google audience data, cross-platform with YouTube video | Yes (via Google Ads) |
| **Deezer** | 16M+ users (strong in EU/LATAM) | Programmatic + direct | European reach, editorial playlist sponsorship | Managed only |

### Podcast Ad Networks

| Network | Scale | Model | Strength |
|---|---|---|---|
| **Spotify Audience Network** | 250M+ podcast listeners | Programmatic + direct | Cross-show audience targeting, Spotify first-party data |
| **Megaphone** (Spotify-owned) | 60K+ shows, largest podcast ad server | Dynamic ad insertion (DAI) | Programmatic marketplace, enterprise podcast hosting |
| **iHeart Podcast Network** | 400M+ monthly downloads | Host-read + DAI | Massive show catalog, celebrity/influencer hosts |
| **Acast** | 100K+ shows, global | Marketplace + programmatic | Global reach, conversational targeting, self-serve |
| **SiriusXM Podcast Network** | Stitcher + AdsWizz stack | Programmatic + host-read | Premium inventory, advanced measurement |
| **Podscribe** | Attribution platform | Measurement + marketplace | Pixel attribution, cross-show measurement |
| **Podcorn** | Micro-influencer podcasts | Marketplace (host-read) | Direct relationships with niche shows |

### Buying Model Comparison

```
Decision Tree: How to Buy Audio Ads

├── Budget < $1K/month → Spotify Ad Studio (self-serve)
├── Budget $1K–$10K/month → Spotify Ad Studio + Acast marketplace
├── Budget $10K–$50K/month → Managed via SXM Media or iHeart + programmatic
├── Budget $50K+/month → Full programmatic (DSP) + direct podcast sponsorships
└── Podcast-only strategy → Megaphone/SAN (programmatic) + Podcorn (host-read)
```

---

## Ad Formats

### Streaming Audio Formats

| Format | Duration | Experience | CPM Range | Best For |
|---|---|---|---|---|
| **Audio Spot** | 15s, 30s, 60s | Sound-only during music breaks | $5–$15 | Core format — awareness, consideration |
| **Companion Display** | Shown during audio ad | Visual banner alongside audio playback | +$2–$5 incremental | Drive clicks, show product, reinforce brand |
| **Video Takeover** | 15–30s | Full-screen video during streaming break (mobile) | $15–$30 | Product demos, visual branding, app installs |
| **Sponsored Playlist** | Ongoing | Brand logo + messaging on curated playlist | $10K–$50K flat | Lifestyle association, sustained awareness |
| **Sponsored Session** | 30 minutes | User gets ad-free session in exchange for watching video ad | $20–$40 | High-value impressions, positive brand association |
| **Homepage Takeover** | 24 hours | Featured placement on app home screen | $50K+ flat | Tentpole launches, maximum reach |

### Podcast Ad Formats

| Format | Delivery | Trust Factor | CPM Range | Best For |
|---|---|---|---|---|
| **Host-Read** | Recorded by podcast host | Highest (2–3x engagement vs pre-produced) | $25–$50 | Brand trust, direct response, niche audiences |
| **Pre-Produced (DAI)** | Dynamically inserted, brand-recorded | Moderate | $15–$30 | Scale, consistency, A/B testing |
| **Baked-In** | Permanent in episode recording | High (feels organic) | $30–$60 (flat per episode) | Evergreen campaigns, long-tail exposure |
| **Pre-Roll** | Before episode content (15–30s) | Lower (easy to skip) | $15–$25 | Short awareness messages, lower budgets |
| **Mid-Roll** | During episode content (30–60s) | Highest attention | $25–$50 | Primary placement — highest recall |
| **Post-Roll** | After episode content (15–30s) | Lowest (audience drops off) | $10–$18 | Lowest CPM, CTA-heavy messages |

### Format Selection Matrix

| Goal | Streaming Format | Podcast Format | Reasoning |
|---|---|---|---|
| Brand awareness | Audio Spot (30s) + Companion | Host-Read Mid-Roll | Sound + visual reinforcement; host trust |
| Direct response / CTA | Audio Spot (15s) + Companion | Host-Read Mid-Roll with promo code | Short hook + clickable companion; trackable code |
| Product launch | Sponsored Session + Video Takeover | Branded series sponsorship | Premium attention; deep storytelling |
| Local / SMB | Audio Spot (15s) on Spotify | Niche local podcasts via Podcorn | Geo-targeting; local audience alignment |
| eCommerce | Audio Spot (30s) + Companion | Host-Read with vanity URL | Audio drives awareness, companion drives click |

---

## Targeting Capabilities

### Streaming Audio Targeting

| Targeting Type | Spotify | Pandora | Amazon Music | Description |
|---|---|---|---|---|
| **Demographics** | Age, gender, location | Age, gender, location, income | Age, gender, location | Standard demo targeting |
| **Genre / Playlist** | 1,000+ genre segments | Music Genome categories | Genre-based | Target by listening taste |
| **Mood / Activity** | Workout, focus, party, chill, commute | Mood stations | Limited | Context-based targeting |
| **Real-Time Context** | Platform (mobile/desktop/smart speaker), time of day | Platform, device | Device, Alexa context | Reach users in specific moments |
| **Listening Behavior** | Podcast listeners, playlist followers, heavy streamers | Station loyalty, skip rate | Purchase behavior overlay | Behavioral segments |
| **First-Party Data** | CRM list match (email) | CRM match | Amazon customer match | Retarget existing customers |
| **Lookalike** | Expand from CRM seed | Expand from segments | Amazon Lookalike | Find similar listeners |
| **Retargeting** | Ad exposure retargeting | Cross-platform retargeting | Amazon retargeting pixel | Sequential messaging |

### Podcast Targeting

| Method | How It Works | Precision | Scale |
|---|---|---|---|
| **Show-level** | Select specific podcast titles | Highest (you pick the show) | Lowest |
| **Category / Genre** | Target podcast categories (business, comedy, true crime) | Medium | High |
| **Audience Segment** | Cross-show audience targeting based on listener behavior | Medium-high | High |
| **Contextual** | Target by episode topic / transcript analysis | Medium | Medium |
| **Demographic** | Age, gender, location of listeners (survey + inferred) | Medium | High |
| **Sequential** | Listener hears Ad A → frequency cap → Ad B follows | High | Medium |

### Sequential Messaging Strategy

```
Sequence Example (3-Touch Audio Campaign):

Touch 1 (Week 1): 30s awareness spot — introduce brand + problem statement
    ↓ (frequency cap: 3x/week)
Touch 2 (Week 2): 15s consideration spot — social proof + differentiator
    ↓ (frequency cap: 2x/week)
Touch 3 (Week 3): 15s conversion spot — offer + clear CTA
    ↓
Retarget on display/social: Listeners who completed sequence → visual ads
```

---

## Creative Production

### Script Templates

**15-Second Spot (Hook → Value → CTA):**
```
[0-3s]  Hook: Attention-grabbing question or statement
[3-10s] Value: One clear benefit or differentiator
[10-15s] CTA: Simple, memorable action (URL, promo code, or "search for [brand]")
```

**30-Second Spot (Hook → Problem → Solution → CTA):**
```
[0-5s]   Hook: Relatable scenario or surprising fact
[5-15s]  Problem: Articulate the pain point
[15-25s] Solution: How your product/service solves it
[25-30s] CTA: Clear next step with tracking mechanism
```

**60-Second Spot (Story Arc):**
```
[0-10s]  Setup: Character or scenario introduction
[10-25s] Conflict: Problem or challenge they face
[25-45s] Resolution: How the product helps, with specifics
[45-55s] Social Proof: Stat, testimonial, or credibility marker
[55-60s] CTA: Memorable, repeatable action
```

### Audio Production Specs

| Specification | Requirement |
|---|---|
| **File format** | WAV (production) or MP3 320kbps (delivery) |
| **Sample rate** | 44.1 kHz |
| **Bit depth** | 16-bit minimum |
| **Loudness** | -16 LUFS (integrated), -1 dBTP (true peak) |
| **Background music** | -20 dB below voice, royalty-free or licensed |
| **Voice-over** | Clear enunciation, conversational tone, no room echo |
| **Duration** | Exact to spec (15.0s, 30.0s, or 60.0s — no tolerance) |

### Dynamic Audio Creative

Dynamic audio personalizes the ad in real time based on listener data:

| Variable | Source | Example |
|---|---|---|
| **Weather** | Listener's current weather | "Rainy day in Seattle? Perfect time to..." |
| **Location** | Geo-IP / device location | "Hey Chicago, your nearest store is on Michigan Ave" |
| **Time of Day** | Device clock | "Good morning — start your day with..." |
| **Day of Week** | Calendar | "Happy Friday — this weekend, try..." |
| **Listener Name** | CRM data match (Spotify) | "Hey Sarah, we made this playlist for you" |

**Production:** Requires modular recording — record base script + all variable inserts separately with matching tone, pace, and room acoustics.

---

## Measurement & Attribution

### Core Metrics

| Metric | Definition | Benchmark (Streaming) | Benchmark (Podcast) |
|---|---|---|---|
| **Listen-Through Rate (LTR)** | % who hear the full ad | 90%+ (15s), 80%+ (30s) | 95%+ (host-read), 85%+ (DAI) |
| **Completion Rate** | % who hear to the end | 85%+ (15s), 75%+ (30s) | 90%+ (mid-roll) |
| **Frequency** | Avg times a listener hears the ad | 3–5x/week optimal | 2–3x per listener per show |
| **Reach** | Unique listeners exposed | Varies by budget | Varies by show size |
| **CPM** | Cost per 1,000 impressions | $5–$15 (streaming) | $15–$50 (podcast) |
| **CPCV** | Cost per completed view/listen | $0.01–$0.03 | $0.02–$0.06 |
| **Brand Lift** | Awareness/consideration/intent change | 5–15% lift (average) | 10–25% lift (host-read) |

### Podcast Attribution Methods

| Method | How It Works | Accuracy | Ease |
|---|---|---|---|
| **Vanity URL** | brand.com/podcastname | Medium (some type direct) | Easy |
| **Promo Code** | Unique code per show/campaign | High (direct match) | Easy |
| **Pixel Attribution** | Podsights, Chartable, Podscribe pixel on site | High (impression-to-conversion) | Medium |
| **Post-Listen Survey** | "How did you hear about us?" | Low (recall bias) | Easy |
| **Branded Search Lift** | Monitor branded search volume during campaign | Medium (correlation) | Medium |
| **Household Graph** | Match podcast device to conversion device | High | Hard (requires partner) |

### Brand Lift Studies

Available through Spotify Brand Lift and Nielsen for campaigns with sufficient spend (typically $25K+):
- **Ad Recall:** "Do you remember hearing an ad for [brand]?" — Benchmark: 15–30% lift
- **Awareness:** "Have you heard of [brand]?" — Benchmark: 5–15% lift
- **Consideration:** "Would you consider [brand]?" — Benchmark: 3–10% lift
- **Purchase Intent:** "How likely are you to purchase from [brand]?" — Benchmark: 2–8% lift

---

## Cross-Channel Integration

### Audio in the Media Mix

| Strategy | How It Works | Expected Impact |
|---|---|---|
| **Audio → Display/Social Retarget** | Listeners who heard audio ad → retarget with visual creative | 20–40% higher display CTR from audio-primed audiences |
| **Audio + Video Sequential** | Audio ad (awareness) → Video ad (consideration) → Display (conversion) | Full-funnel coverage across contexts |
| **Audio + Search** | Audio drives branded search → capture with branded search ads | 15–25% branded search volume lift during audio flights |
| **Podcast + Email** | Podcast sponsor → drive to email signup → nurture sequence | High-quality leads from trusted host endorsement |
| **Streaming + CTV** | Audio ads during music → CTV ads during streaming video | Multi-format reach within same household |

### Frequency Capping Across Audio

- Spotify: Platform-level frequency caps (set in Ad Studio or via DSP)
- Podcast: Frequency is per-show; cross-show frequency requires programmatic buying via SAN or DSP
- Cross-platform: Use DSP (The Trade Desk, DV360) to manage frequency across streaming + podcast + CTV
- Recommended total audio frequency: 5–8 impressions per listener per week across all audio channels

---

## Audio Creative Best Practices

### What Works

- **Conversational tone** outperforms corporate/announcer voice by 20–30% in recall
- **Sound logos / mnemonics** (Intel bong, Netflix "ta-dum") build long-term brand recognition — invest in a 2–3 second audio signature
- **First 3 seconds must hook** — no "This ad is brought to you by..." openings (listeners tune out)
- **Personalization** (dynamic weather, location, time) increases recall 30%+ vs generic
- **Repetition of brand name** — mention brand name 2–3 times in a 30s spot (beginning and end minimum)
- **One message per spot** — do not try to cover multiple features or offers
- **CTA clarity** — simple, repeatable action ("visit brand dot com slash podcast" or "search for Brand in the app store")

### What Fails

- Starting with "Hey listeners" or generic greetings — feels like an interruption
- Sound effects louder than voice — jarring in headphone environments
- Multiple CTAs (visit website AND download app AND use promo code) — pick one
- Overly produced spots that sound nothing like the surrounding content
- 60-second spots without a compelling story — 30 seconds is the safe default
- Background music that competes with voice — keep it at -20 dB minimum

### Podcast Host-Read Guidelines

When briefing podcast hosts for host-read ads:
- [ ] Provide 3–5 key talking points, not a rigid script — hosts need to sound natural
- [ ] Include brand pronunciation guide and any terms to avoid
- [ ] Specify the one CTA (vanity URL or promo code)
- [ ] Share a 1-page brand brief with tone, audience, and key differentiator
- [ ] Allow hosts to use their own language and personal anecdotes
- [ ] Review and approve reads before air, or accept that baked-in reads cannot be edited
- [ ] Set clear FTC disclosure expectations ("This episode is sponsored by...")

> **Key principle:** Audio advertising succeeds when it respects the listener's environment. People listen to audio during personal, often intimate moments — commuting, working out, cooking, falling asleep. Ads that match the tone and context of these moments feel like natural companions rather than interruptions. The best audio ads sound like they belong.
