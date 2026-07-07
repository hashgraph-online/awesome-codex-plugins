# Screenshot Inspiration Reference

This page provides complete visual direction examples from successful Shots campaigns. Use these as templates when planning screenshot sets — complete with palette specs, compositional patterns, headline formulas, and proven style families.

## How to Use This Reference

**Important:** These examples are reference patterns to adapt, not templates to copy verbatim.

- **Adapt colors:** Change palette hex codes to match your app's brand
- **Rewrite headlines:** Adjust to reflect your app's specific value proposition
- **Show real UI:** Device screens must show YOUR app's actual interface (never copy example UI)
- **Customize patterns:** Use compositional patterns as starting points, not rigid rules
- **Make it yours:** Draw inspiration from style families, but customize for your app's personality

The goal is to understand proven patterns and apply them creatively to your specific app and audience.

For public App Store inspiration, use `gallery.ensure_app` or
`gallery.get_app`, then pass the chosen `galleryInspirationScreenshotId` to
`generate_screenshot`. Treat gallery screenshots as style references only:
composition, color, typography, pacing, and tone. Never copy another app's UI,
claims, brand, or product state.

If the user asks for inspiration behavior Shots does not support, or repeatedly
tries to work around gallery limits, call `feedback.report` with
`category: "unsupported_workflow"` or `category: "feature_request"` and briefly
tell the user you notified the Shots team.

## Prompt Format

Write screenshot prompts as complete plain text. The server automatically
appends dimensions, constraints, and reference metadata. Use only the sections
the concept needs, and do not force device/headline fields when the reference is
visual-first or text-free.

**Example 1: Detailed Prompt**
```text
Create one 1264x2736 App Store screenshot for "Pulse: Fitness Tracking".

Campaign goal: Drive downloads by showcasing immersive, data-rich workout tracking.
Audience: Data-driven fitness enthusiasts aged 22-42 who want real-time performance insights.

Visual direction: Dark cinematic gradient with vivid neon-athletic accents.
Palette: primary #0A0A0F, secondary #1C1C2E, accent #FF3B5C, text #FFFFFF.
Mood: Premium, energetic, precise.

Panel content:
- Headline: "Your Workout, Fully Alive."
- Subtitle: "Real-time heart rate zones. Every rep counted."
- Device: iPhone 16 Pro, black titanium frame, 10° left tilt
- Screen shows: Live workout dashboard with large radial 5-zone heart rate arc, 164 BPM center, stats row below, ECG waveform
- Layout: Device centered-right, headline left third
- Background: Deep gradient (#0A0A0F to #1C1C2E) with vivid red radial glow behind device
- Breakout: ECG waveform bleeds from device edge into background with fade
```

**Example 2: Concise Prompt**
```text
Create a 1264x2736 screenshot for dating app "Spark".

Hero panel with headline "Real Connections, Zero Games" on dark navy (#0A1828) background. iPhone 15 Pro centered showing match feed with profile cards. Warm coral accent color (#FF6B5A). Three floating profile cards burst from device right side at slight angles with drop shadows. Clean premium aesthetic.
```

## Visual Style Families

### 1. Clean Premium (Dating)
**App:** Pull — AI Dating App Photos
**Palette:**
- Primary: `#0F1416` (near-black)
- Secondary: `#1A2328` (dark charcoal)
- Accent: `#119DA4` (teal)
- Text: `#FFFFFF` (white)

**Motifs:**
- Teal gradient orbs
- Subtle grain texture
- Dark premium canvas with soft teal lighting accents
- iPhone 15 Pro device with real app UI on screen

**Mood:** Dark, confident, aspirational

**Typography:**
- Headlines: Large, bold, sans-serif, white (#FFFFFF), high-contrast, readable at thumbnail size
- Subtitles: Smaller, regular weight, light gray (#CCCCCC)

**Example Headline:** "2 Selfies In. 50+ Photos Out."
**Example Subtitle:** "No photographer. No plastic skin."

**Layout Pattern:**
- Headline at top 20%, centered
- iPhone 15 Pro device below with slight 3D tilt (~5° clockwise)
- Dark charcoal background with soft teal radial glow behind device
- Breakout elements: 4-5 AI-generated photos bursting from the device side at varying sizes with rotation and drop shadows

**When to Use:** Apps targeting confidence, premium positioning, or transformation outcomes. Works for dating, professional development, personal brand.

---

### 2. Maximal Social Pop (Photo / Feedback)
**App pattern:** Picky-style photo choice, AI feedback, friend voting, social confidence

**Palette:**
- Primary: bright sky blue / white flash lighting
- Secondary: glossy hot pink and magenta shadows
- Accent: mint green, purple glass, black UI pills
- Text: black or white, very high contrast

**Motifs:**
- Oversized bubble or condensed display headlines
- Cropped stop signs, traffic lights, or other "decision" symbols
- Hand-held printed photo cards, tilted stacks, filename labels
- Glassy pink/purple hearts, cloud mist, sparkle highlights
- Floating chat bubbles, segmented controls, avatar rows, voting chips
- Product-proof stickers such as score badges, "Fixed" cards, or AI edit bars

**Mood:** Loud, glossy, young, social, conversational, premium chaos

**Prompting Pattern:**
Describe the composition as a back-to-front layer stack: background, large text,
hero photo/phone object, UI proof overlays, foreground stickers. Every sticker,
heart, avatar, chat bubble, and label needs a product or emotional job. This
style works best when the prompt is specific about layer order and text
hierarchy rather than simply asking for "lots of fun elements."

**Example Headlines:**
- "STOP GUESSING"
- "KNOW YOUR BEST SHOT BEFORE YOU POST"
- "GET FLOODED WITH REAL VOTES"
- "CHAT YOUR WAY TO FIRE"

**When to Use:** Social, photo/video, dating, AI feedback, creator tools, youth
culture, friend-voting flows, and apps where conversation or social proof is the
product.

---

### 3. Editorial Warm-Luxury (Fashion)
**App:** Closet — AI Wardrobe Organizer
**Palette:**
- Primary: `#C9A97A` (warm gold)
- Secondary: `#F5EFE6` (cream)
- Accent: `#D4614A` (terracotta)
- Text: `#1C1410` (near-black)
- Subtitle: `#7A6A5A` (warm brown)

**Motifs:**
- Floating outfit cards with soft drop shadows
- Warm cream and terracotta background washes
- Editorial photography of styled flat-lays and lifestyle moments
- Thin gold hairline dividers and label tags
- Scattered clothing item thumbnails in rounded cards
- AI sparkle (✦) as recurring accent mark

**Mood:** Aspirational, warm, premium, effortlessly chic

**Typography:**
- Headlines: Large bold serif-meets-modern-sans hybrid — 36–42pt, near-black #1C1410, tight tracking, two lines max
- Subtitles: 16–18pt medium-weight sans-serif, muted warm brown #7A6A5A, 1.4 line height, max 2 lines

**Example Headlines:**
- "Your Wardrobe, Always Ready."
- "Outfits That Style Themselves."
- "Discover Looks You'll Actually Wear."

**Layout Patterns:**
- Device centered-left, headline large and bold top-right, floating cards overlapping device
- Full-bleed editorial split: lifestyle photo bleeds across left 45%, device center-right overlapping photo
- Device centered with slight lean, cascading stack of floating cards in staggered arc

**Backgrounds:**
- Warm linen-textured cream with soft terracotta gradient washes
- Editorial lifestyle photography blurred at 20% with gold hairline rules
- Bold warm terracotta-to-blush diagonal gradients with linen texture overlay

**When to Use:** Fashion, lifestyle, curation, personal style. Any app where visual abundance, taste, and aspirational identity matter. Every panel should feel like it could be torn from Vogue or Who What Wear.

---

### 4. Dark Cinematic (Fitness)
**App:** Pulse — Fitness Tracking
**Palette:**
- Primary: `#0A0A0F` (near-black)
- Secondary: `#1C1C2E` (dark charcoal)
- Accent: `#FF3B5C` (vibrant red)
- Text: `#FFFFFF` (white)
- Subtitle: `#A0A8C0` (muted blue-white)

**Motifs:**
- Glowing concentric activity rings
- Pulse / ECG waveform line as recurring graphic element
- Radial heart-rate zone arcs in gradient color (blue → green → yellow → orange → red)
- Soft bloom/glow halos behind key data points
- Thin grid lines suggesting precision and measurement

**Mood:** Premium, energetic, precise

**Typography:**
- Headlines: SF Pro Display heavy/black weight, 52–60pt, pure white (#FFFFFF), left-aligned, 2 lines max, tight leading
- Subtitles: SF Pro Text regular, 22–26pt, muted blue-white (#A0A8C0), left-aligned, max 1 line

**Example Headlines:**
- "Your Workout, Fully Alive."
- "Know Exactly How Hard to Push."
- "Wake Up Ready to Crush It."

**Layout Patterns:**
- Device centered-right, headline and subtitle stacked left third, UI elements bleeding into background
- Device slightly left of center, headline stacked right third, large ghost UI element as background motif
- Device centered, recovery score visually dominant, ghost circle behind device

**Backgrounds:**
- Deep vertical gradients (#0A0A0F to #1C1C2E) with vivid radial glow blooms (red, blue, green) behind device
- Glow colors rotate per panel: warm red energy, cool blue precision, vital green readiness

**Breakout Elements:**
- ECG waveform bleeds from device edge into background with fade
- Zone bars extend beyond device frame with matching glow
- Large ghost UI elements (rings, arcs) behind device at 8–15% opacity

**When to Use:** Health, fitness, productivity, data visualization. Apps where precision, performance, and real-time feedback are core. All panels share same background gradient system; only glow color shifts.

---

## Complete Campaign Examples

### Closet (Fashion) — 3-Panel Progression

**Panel 1: Hero — Establish Core Value**
- **Headline:** "Your Wardrobe, Always Ready."
- **Subtitle:** "Every piece you own, organized beautifully in one place."
- **Role:** First impression — communicate beauty + organization instantly
- **Device Screen:** Masonry-grid wardrobe view, 12 clothing items in rounded cards, warm amber category pills
- **Layout:** Device centered-left, headline top-right, floating outfit card overlapping device
- **Background:** Warm linen cream with terracotta gradient in upper right, subtle fabric texture overlay

**Panel 2: Feature — Strongest Differentiator**
- **Headline:** "Outfits That Style Themselves."
- **Subtitle:** "AI suggests what to wear — based on your actual closet."
- **Role:** Maximum revision impact — AI outfit suggestion with editorial drama
- **Device Screen:** AI Outfit Suggestion screen with '✦ AI Style Pick' header, styled outfit flat-lay, item tags, 'Why this works' copy
- **Layout:** Full-bleed split — lifestyle photo left 45%, device center-right overlapping, headline spans full width
- **Background:** Rich lifestyle editorial photo left (blurred 20%), soft cream right with radial gold glow, gold hairline separator
- **Breakout:** Large floating AI suggestion card with 3-item outfit strip, 'AI Pick' terracotta pill, gold sparkle glyphs

**Panel 3: Discovery — Differentiation from Competitors**
- **Headline:** "Discover Looks You'll Actually Wear."
- **Subtitle:** "New outfit ideas, built from pieces you already own."
- **Role:** Joy of finding new combinations — energy and inspiration
- **Device Screen:** Discover feed with Pinterest-style cards: 'The Quiet Luxury Edit', 'Weekend Off-Duty', 'Golden Hour Dinner'
- **Layout:** Device centered with right lean, headline top-left, cascading stack of 3 floating cards in staggered arc
- **Background:** Bold warm terracotta-to-blush diagonal gradient with linen texture, large circular gold glow behind device
- **Breakout:** Three outfit cards cascade left of device with rotation (–8°, 0°, +6°), progressive shadows, gold '✦ New' badge

**Campaign Insight:** Progression moves from organization → AI intelligence → discovery. Each panel escalates visual energy: calm cream → editorial split → bold gradient. Floating cards create abundance and depth. AI sparkle (✦) recurs as brand signature.

---

### Pulse (Fitness) — 3-Panel Progression

**Panel 1: Hero — Live Workout Energy**
- **Headline:** "Your Workout, Fully Alive."
- **Subtitle:** "Real-time heart rate zones. Every rep counted."
- **Role:** Premium all-in-one fitness dashboard
- **Device Screen:** Live workout with large radial 5-zone heart rate arc, '164 BPM' center, stats row below, ECG waveform
- **Layout:** Device centered-right, headline left third, ECG waveform bleeding into background
- **Background:** Deep gradient with vivid red radial glow bloom — heat and intensity
- **Glow:** `#FF3B5C` red

**Panel 2: Feature — Zone Intelligence**
- **Headline:** "Know Exactly How Hard to Push."
- **Subtitle:** "5-zone training. Smarter effort, faster results."
- **Role:** Heart-rate zone breakdown — differentiator from Strava/Apple Fitness
- **Device Screen:** Post-workout zone breakdown with 5 horizontal stacked bars, time/percentage per zone, peak zone card
- **Layout:** Device slightly left, headline right third, large ghost ring arc behind device (semi-transparent)
- **Background:** Deep gradient with electric-blue radial glow — precision mood
- **Glow:** `#3B82F6` blue
- **Breakout:** Zone 5 bar extends beyond device frame with red glow

**Panel 3: Recovery — Morning Readiness**
- **Headline:** "Wake Up Ready to Crush It."
- **Subtitle:** "Daily recovery score so you always train smart."
- **Role:** Recovery and readiness — key differentiator vs Strava, nod to Whoop users
- **Device Screen:** Morning recovery dashboard with large '82' recovery score in green ring, 'READY TO TRAIN' badge, HRV/HR/Sleep cards, 7-day sparkline
- **Layout:** Device centered, headline above-left, recovery score dominant, ghost circle in background
- **Background:** Deep gradient with emerald radial glow — vitality and readiness
- **Glow:** `#22C55E` green
- **Breakout:** Large ghost circle (400pt) behind device at 8% opacity, matching recovery ring

**Campaign Insight:** All panels share `#0A0A0F` to `#1C1C2E` gradient base. Only the glow color shifts: red (energy) → blue (precision) → green (readiness). This creates visual consistency while emotionally differentiating each panel. Consistent left-leaning 8–12° device tilt. UI elements bleed into backgrounds for immersion.

---

## Headline Formula Bank

### Before/After Transformations

| Weak | Strong | Pattern |
|------|--------|---------|
| "Organize Your Wardrobe" | "Your Wardrobe, Always Ready." | Outcome > Action |
| "AI Outfit Suggestions" | "Outfits That Style Themselves." | Benefit > Feature |
| "Track Your Workouts" | "Your Workout, Fully Alive." | Experience > Function |
| "Improve Your Photos" | "2 Selfies In. 50+ Photos Out." | Concrete Ratio > Vague Promise |
| "Smart Recovery Tracking" | "Wake Up Ready to Crush It." | Emotional Outcome > Technical Feature |

### Proven Patterns

**1. Outcome-First (Not Feature-First)**
- ✅ "Land With A Plan" (travel itinerary)
- ✅ "Know They Are Safe" (pet tracking)
- ✅ "Find Your People Tonight" (social planning)
- ❌ "AI Travel Planning"
- ❌ "Pet Location Tracker"
- ❌ "Event Discovery App"

**2. Concrete Specificity**
- ✅ "2 Selfies In. 50+ Photos Out."
- ✅ "5-zone training. Smarter effort, faster results."
- ❌ "Better photos with less effort"
- ❌ "Advanced training features"

**3. Emotional Payload**
- ✅ "Wake Up Ready to Crush It."
- ✅ "Discover Looks You'll Actually Wear."
- ✅ "Your Workout, Fully Alive."
- ❌ "Morning Recovery Dashboard"
- ❌ "Outfit Discovery Feature"
- ❌ "Live Workout Stats"

**4. Two-Line Structure**
- Line 1: Bold promise or outcome (4–6 words)
- Line 2: Clarifying detail or mechanism (4–8 words)
- Examples:
  - "Outfits That / Style Themselves."
  - "Your Wardrobe, / Always Ready."
  - "Know Exactly / How Hard to Push."

**5. Reader as Subject**
- ✅ "Your Wardrobe, Always Ready"
- ✅ "Your Workout, Fully Alive"
- ❌ "Closet Organizes Your Clothes"
- ❌ "Pulse Tracks Your Fitness"

---

## Icon Moodboard Approach

### Contact Sheet Format

Icon moodboards generate as a **2048x2048 contact sheet** with ~20 numbered concepts arranged in a grid. Each concept is a small icon preview (~180–220px square) with a number label.

**Purpose:** Brainstorming step before finals. User picks favorites by number, then you generate individual 1024x1024 finals.

**Cost:** 5 generation credits

### Variety Requirements

Successful moodboards include:

1. **Symbol Variety**
   - Abstract geometric marks
   - Literal objects that represent the app
   - Mascot or character concepts when appropriate
   - Hybrid object + abstract background concepts

2. **Background Variety**
   - Solid full-bleed color
   - Radial, linear, or angular gradients
   - Subtle texture or material fields
   - High-contrast light/dark variants

3. **Style Variety**
   - Flat/minimal
   - Dimensional 3D with shadows and highlights
   - Glass or translucent objects
   - Clay/soft mascot forms
   - Photorealistic object icons

4. **Color Range**
   - Brand colors if specified
   - Adjacent hues
   - Bold contrasts
   - Monochrome variations

### Example Prompt Structure

Use `generate_icon_moodboard` tool fields, but keep `creative_direction` as a
plain-text brief rather than JSON-shaped image instructions:

```text
Generate an icon moodboard for [App Name], a [category] app that [core function].

Symbol exploration: include [primary symbol], [secondary symbol], and abstract
representations of [core concept]. Avoid text or letter marks unless the user
explicitly wants brand-mark exploration.

Background directions: try full-bleed [brand color], gradients in [color range],
and subtle textured options.

Style mix: include flat minimalist options, dimensional/3D treatments, glass or
translucent forms, and one photorealistic object direction when it fits.

Audience: [target user] who values [key attributes].
```

### After Moodboard Review

Once the user selects favorites (e.g., "I like #7, #12, and #19"), generate
individual finals with `generate_icon` using specific direction:

```text
style: dimensional gradient with soft shadows, inspired by moodboard #7
symbol: stylized wave arc
background: radial gradient from teal to deep blue
creative_direction: one upload-ready 1024x1024 full-bleed square app icon
source artwork; no text, no rounded mask, no preview tile
```

---

## Compositional Patterns

### Device Placement

**Centered-Right:**
- Headline and subtitle stack in left third
- Device in right two-thirds with slight tilt
- Leaves room for text hierarchy
- Example: Pulse Panel 1

**Centered-Left:**
- Headline and subtitle in right third
- Device in left two-thirds
- Breakout elements can fan right
- Example: Closet Panel 1

**Center with Lean:**
- Device centered with 3–5° tilt
- Headline spans top
- Breakout elements cascade to one side
- Example: Closet Panel 3

**Full-Bleed Split:**
- Background photo bleeds left 45%
- Device center-right overlaps photo
- Headline spans full width at top
- Creates editorial magazine effect
- Example: Closet Panel 2

### Breakout Element Strategies

**Fan/Burst:**
- 4–5 elements radiating from device edge
- Varying sizes and rotation
- Progressive drop shadows
- Creates "many outputs" narrative
- Example: Pull hero (2 selfies → 50+ photos)

**Cascading Stack:**
- 3 cards in staggered arc
- Each rotated slightly (–8°, 0°, +6°)
- Layered with progressive shadows
- Suggests depth and abundance
- Example: Closet Panel 3 (Discover feed)

**Bleed Continuity:**
- UI element extends from device into background
- Fades to transparent at edges
- Creates immersion
- Example: Pulse Panel 1 (ECG waveform)

**Floating Feature Card:**
- Large card breaks dramatically above/beside device
- Shows mini UI preview or detail
- Label badge with accent color
- Prominent warm drop shadow
- Example: Closet Panel 2 (AI suggestion card)

### Background Depth Techniques

**Radial Glow Bloom:**
- Soft gradient glow behind device
- Accent color at center fading to transparent
- Creates focal depth and mood
- Match glow color to panel theme (red = energy, blue = precision, green = readiness)

**Ghost UI Elements:**
- Large semi-transparent version of key UI element
- Sits behind device at 8–15% opacity
- Reinforces visual theme without competing
- Example: Pulse Panel 2 (ghost zone ring), Pulse Panel 3 (ghost recovery circle)

**Texture Overlays:**
- Subtle fabric/linen texture at 6–8% opacity
- Adds tactile warmth without noise
- Works for warm/luxury styles
- Example: Closet backgrounds

**Editorial Photography:**
- Full-bleed lifestyle photo blurred at 20%
- Occupies 40–50% of panel
- Thin hairline rule separates from UI zone
- Adds aspiration and context
- Example: Closet Panel 2

### Typography Hierarchy

**Large Bold Headlines:**
- 36–60pt depending on style family
- Pure white or near-black for maximum contrast
- 2 lines max, tight leading
- Left-aligned or centered per layout
- Must be readable at 60px thumbnail width

**Supporting Subtitles:**
- 16–26pt, regular or medium weight
- Muted color (warm brown for warm palettes, blue-white for dark palettes)
- 1–2 lines max
- Sits 12–16pt below headline
- Provides clarifying detail without competing

**Text Placement:**
- Keep all text 80px+ from edges
- Never overlay text on busy backgrounds without scrim
- Prioritize readability over decoration

---

## Quick Reference: When to Use Each Style Family

| Style Family | Best For | Avoid For |
|--------------|----------|-----------|
| **Clean Premium** | Apps about transformation, confidence, premium positioning, measurable outcomes | Playful apps, kids apps, community-first products |
| **Editorial Warm-Luxury** | Fashion, lifestyle, curation, taste-making, visual abundance, aspiration | Technical tools, data apps, sports/fitness, enterprise |
| **Dark Cinematic** | Fitness, health, productivity, data visualization, performance tracking, real-time feedback | Kids, casual games, cozy/warm products, beginner-friendly tools |

---

## Prompting Tips

Write prompts as complete plain text. Use markdown-style sections when they help
the brief scan, but do not force every screenshot into the same structure.

1. **Use complete palette specs with hex codes** — don't say "warm colors," say `#C9A97A` and `#F5EFE6`
2. **Specify exact device model and tilt** — "iPhone 16 Pro, natural titanium frame, 3° left tilt"
3. **Name the style family** — "Editorial warm-luxury" or "Dark cinematic gradient"
4. **Include motif list** — recurring visual elements that create brand signature
5. **Quote text verbatim** — headlines and subtitles should render >95% accurate
6. **Describe device screen UI in detail** — never say "app UI" or "placeholder screen"
7. **Specify breakout elements precisely** — how many, where placed, rotation degrees, shadow type
8. **Include background composition** — gradient directions, texture overlays, glow positions, opacity percentages
