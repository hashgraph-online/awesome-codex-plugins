# Generative AI Tools for Ad Creative

Reference for using AI image generators, video generators, voice models, and code-based video tools to produce ad visuals at scale. Tools are described by capability class, not by brand: pick whichever model in the class is available, licensed, and current in the session.

## Availability and Execution Gate

Capability classes, price bands, limits, request shapes, and commands in this
reference are examples, not proof that a tool is installed, connected,
authorized, licensed for the asset, or still current. Before using any route:

1. Inspect the tools and runtimes actually available in the current session.
2. Verify the chosen provider's current official documentation, pricing, output
   rights, consent requirements, and exact model or package version.
3. Confirm credentials and the intended account without exposing secrets.
4. Treat installs, paid generation, uploads, voice cloning, and publication as
   separately authorized actions.
5. If no tool in the needed class or runtime is available, return the
   provider-neutral prompt, storyboard, or render specification instead of
   inventing a call.

---

## When to Use Generative Tools

| Need | Tool Category | Best Fit (capability class) |
|------|---------------|----------|
| Static ad images (banners, social) | Image generation | Premium image model with editing, open-weight multi-reference image model, typography-specialist image model |
| Ad images with text overlays | Image generation (text-capable) | Typography-specialist image model, premium image model with strong text rendering |
| Short video ads (6-30 sec) | Video generation | Native-audio video model, controllable video model, low-cost high-volume video model |
| Video ads with voiceover | Video gen + voice | Native-audio video model, or silent controllable video model + premium voice model |
| Voiceover tracks for ads | Voice generation | Premium voice model, low-cost TTS API, low-latency TTS model |
| Multi-language ad versions | Voice generation | Premium voice model, large-library multilingual voice platform |
| Brand voice cloning | Voice generation | Premium voice model with cloning, enterprise on-premise cloning platform |
| Product mockups and variations | Image generation + references | Open-weight multi-reference image model |
| Templated video ads at scale | Code-based video | Remotion, Hyperframes |
| Personalized video (name, data) | Code-based video | Remotion, Hyperframes |
| Brand-consistent variations | Image gen + style refs | Multi-reference image model, typography-specialist model with style references |

---

## Image Generation

### Premium image model with native editing

A general-purpose, high-quality image model offered through a large provider's multimodal API, usually the same API used for text generation.

**Best for:** High-quality ad images, product visuals, text rendering
**Access:** The provider's hosted API or cloud console
**Pricing band:** ~$0.04/image (fast tier) to ~$0.24/image (4K premium tier)

**Strengths:**
- Strong text rendering in images (logos, headlines)
- Native image editing (modify existing images with prompts)
- Available through the same API used for text generation
- Supports both generation and editing in one model

**Ad creative use cases:**
- Generate social media ad images from text descriptions
- Create product mockup variations
- Edit existing ad images (swap backgrounds, change colors)
- Generate images with headline text baked in

**Request shape (illustrative; use the provider's documented endpoint and fields):**
```bash
# Generic multimodal image-generation request
curl -X POST "$IMAGE_API_URL" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $IMAGE_API_KEY" \
  -d '{
    "prompt": "Create a clean, modern social media ad image for a project management tool. Show a laptop with a kanban board interface. Bright, professional, 16:9 ratio.",
    "output": ["image"]
  }'
```

---

### Open-weight multi-reference image model

An image model family with open weights for self-hosting plus hosted API access through model-hosting marketplaces and the developer's own API.

**Best for:** Photorealistic images, brand-consistent variations, multi-reference generation
**Access:** Hosted model marketplaces, the developer's API, or self-hosted weights
**Pricing band:** ~$0.01-0.06/image depending on tier and resolution

**Tier variants:**
| Tier | Speed | Quality | Cost | Best For |
|-------|-------|---------|------|----------|
| Pro | ~6 sec | Highest | ~$0.015/MP | Final production assets |
| Flex | ~22 sec | High + editing | ~$0.06/MP | Iterative editing |
| Dev (open weight) | ~2.5 sec | Good | ~$0.012/MP | Rapid prototyping |
| Small/fast | Fastest | Good | Lowest | High-volume batch generation |

**Strengths:**
- Multi-image reference (up to ~8 images) for consistent identity across ads
- Product consistency: same product in different contexts
- Style transfer from reference images
- Open-weight tier for self-hosting

**Ad creative use cases:**
- Generate 50+ ad variations with consistent product/person identity
- Create product-in-context images (your SaaS on different devices)
- Style-match to existing brand assets using reference images
- Rapid A/B test image variations

---

### Typography-specialist image model

An image model specialized in typography and text rendering within images.

**Best for:** Ad banners with text, branded graphics, social ad images with headlines
**Access:** The developer's API or an inference aggregator
**Pricing band:** ~$0.06/image (API), lower on subscription

**Strengths:**
- Best-in-class text rendering (roughly 90% legible-text accuracy vs ~30% for general tools)
- Style reference system (upload a few reference images)
- Large preset style library for consistent brand aesthetics
- Strong at logos and branded typography

**Ad creative use cases:**
- Generate ad banners with headline text directly in the image
- Create social media graphics with branded text overlays
- Produce multiple design variations with consistent typography
- Generate promotional materials without needing a designer for each iteration

---

### Other Image Tool Classes

| Class | Best For | API Status | Notes |
|------|----------|------------|-------|
| **Chat-integrated image model** | General image generation | Official API | Built into a chat assistant, good text rendering |
| **Artistic community model** | Artistic, high-aesthetic images | Often no official public API | Chat-app based; unofficial APIs exist but risk account bans |
| **Open-source diffusion model** | Self-hosted, customizable | Open source | Best for teams with GPU infrastructure |

---

## Video Generation

### Native-audio video model (vertical-first)

A large provider's video model, available through its multimodal API and cloud platform.

**Best for:** High-quality video ads with native audio, vertical video for social
**Access:** The provider's hosted API or cloud platform
**Pricing band:** ~$0.15/sec (fast tier), ~$0.40/sec (standard tier)

**Capabilities:**
- Up to ~60 seconds at 1080p
- Native audio generation (dialogue, sound effects, ambient)
- Vertical 9:16 output for Stories/Reels/Shorts
- Upscale to 4K
- Text-to-video and image-to-video

**Ad creative use cases:**
- Generate short video ads (15-30 sec) from text descriptions
- Create vertical video ads for TikTok, Reels, Shorts
- Produce product demos with voiceover
- Generate multiple video variations from the same prompt with different styles

---

### Long-form cinematic video model

Video generation with simultaneous audio-visual generation and camera controls, often reached through third-party inference APIs.

**Best for:** Cinematic video ads, longer-form content, audio-synced video
**Access:** The developer's API or third-party inference aggregators
**Pricing band:** ~$0.09/sec (third-party)

**Capabilities:**
- Up to ~3 minutes at 1080p/30-48fps
- Simultaneous audio-visual generation
- Text-to-video and image-to-video
- Motion and camera controls

**Ad creative use cases:**
- Longer product explainer videos
- Cinematic brand videos with synchronized audio
- Animate product images into video ads

---

### Controllable video model (silent output)

A video generation and editing platform with strong controllability.

**Best for:** Controlled video generation, style-consistent content, editing existing footage
**Access:** The platform's developer API

**Capabilities:**
- Character/scene consistency across shots
- Motion brush and camera controls
- Image-to-video with reference images
- Video-to-video style transfer
- Silent output: pair with a voice model for narration

**Ad creative use cases:**
- Generate video ads with consistent characters/products across scenes
- Style-transfer existing footage to match brand aesthetics
- Extend or remix existing video content

---

### Dialogue-focused video model

A video model with synchronized audio tuned for speech.

**Best for:** High-fidelity video with dialogue and sound
**Access:** The provider's hosted API
**Pricing band:** ~$0.10-0.50/sec depending on resolution and tier

**Capabilities:**
- Up to ~60 seconds with synchronized audio
- Dialogue, sound effects, and ambient audio
- Fast and quality tiers
- Text-to-video and image-to-video

**Ad creative use cases:**
- Video testimonials and talking-head style ads
- Product demo videos with narration
- Narrative brand videos

---

### Low-cost high-volume video model

A video model with simultaneous audio-visual generation and multimodal reference inputs, offered through an official cloud plus several third-party inference APIs.

**Best for:** Fast, affordable video ads with native audio, multimodal reference inputs
**Access:** Official cloud API and third-party inference aggregators; often a widely compatible API format
**Pricing band:** ~$0.10-0.80/min depending on resolution (estimated 10-100x cheaper per clip than premium dialogue models)

**Capabilities:**
- Up to ~20 seconds at up to 2K resolution
- Simultaneous audio-visual generation
- Text-to-video and image-to-video
- Many reference files (up to ~12) for multimodal input

**Ad creative use cases:**
- High-volume short video ad production at low cost
- Video ads with synchronized voiceover and sound effects in one pass
- Multi-reference generation (feed product images, brand assets, style references)
- Rapid iteration on video ad concepts

---

### All-in-one cinematic video studio

A full-stack, web-based video creation platform with cinematic camera presets.

**Best for:** Social video ads, cinematic style, mobile-first content
**Access:** Web app

**Capabilities:**
- 50+ preset camera movements (zooms, pans, FPV drone shots)
- Image-to-video animation
- Built-in editing, transitions, and keyframing
- All-in-one workflow: image gen, animation, editing

**Ad creative use cases:**
- Social media video ads with cinematic feel
- Animate product images into dynamic video
- Create multiple video variations with different camera styles
- Quick-turn video content for social campaigns

---

### Video Tool Comparison

| Class | Max Length | Audio | Resolution | API | Best For |
|------|-----------|-------|------------|-----|----------|
| **Native-audio video model** | ~60 sec | Native | 1080p/4K | Official | Vertical social video |
| **Long-form cinematic model** | ~3 min | Native | 1080p | Third-party | Longer cinematic |
| **Controllable video model** | ~10 sec | No | 1080p | Official | Controlled, consistent |
| **Dialogue-focused model** | ~60 sec | Native | 1080p | Official | Dialogue-heavy |
| **Low-cost high-volume model** | ~20 sec | Native | 2K | Official + third-party | Affordable high-volume |
| **All-in-one video studio** | Varies | Yes | 1080p | Web-based | Social, mobile-first |

---

## Voice & Audio Generation

For layering realistic voiceovers onto video ads, adding narration to product demos, or generating audio for code-rendered videos. These tools turn ad scripts into natural-sounding voice tracks.

### When to Use Voice Tools

Many video models now include native audio. Use a standalone voice model when you need:

- **Voiceover on silent video**: add a voice track to silent AI-generated clips or code-rendered templates
- **Brand voice consistency**: Clone a specific voice for all ads
- **Multi-language versions**: Same ad script in 20+ languages
- **Script iteration**: Re-record voiceover without reshooting video
- **Precise control**: Exact timing, emotion, and pacing

---

### Premium voice model

The highest-realism class of voice generation and voice cloning.

**Best for:** Most natural-sounding voiceovers, brand voice cloning, multilingual
**Access:** REST API with streaming support
**Pricing band:** ~$0.12-0.30 per 1,000 characters depending on plan; low monthly entry plans

**Capabilities:**
- ~29+ languages with natural accent and intonation
- Voice cloning from short audio clips (instant) or longer recordings (professional)
- Emotion and style control
- Streaming for real-time generation
- Voice library with hundreds of pre-built voices

**Ad creative use cases:**
- Generate voiceover tracks for video ads
- Clone your brand spokesperson's voice (with documented consent) for all ad variations
- Produce the same ad in 10+ languages from one script
- A/B test different voice styles (authoritative vs. friendly vs. urgent)

**Request shape (illustrative; use the provider's documented endpoint and fields):**
```bash
curl -X POST "$VOICE_API_URL/text-to-speech/{voice_id}" \
  -H "Authorization: Bearer $VOICE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Stop wasting hours on manual reporting. Try DataFlow free for 14 days.",
    "model": "<multilingual-voice-model>",
    "voice_settings": {"stability": 0.5, "similarity": 0.75}
  }' --output voiceover.mp3
```

---

### Low-cost TTS API

Simple, affordable text-to-speech bundled into a general AI platform's API.

**Best for:** Quick voiceovers, cost-effective at scale, simple integration
**Access:** The same SDK used for the platform's text models
**Pricing band:** ~$15-30 per million characters; ~$0.015/min on the smallest tier

**Capabilities:**
- A small set of built-in voices (no custom cloning)
- Multiple languages
- Real-time streaming
- HD quality option

**Ad creative use cases:**
- Fast, cheap voiceover for draft/test ad versions
- High-volume narration at low cost
- Prototype ad audio before investing in a premium voice

---

### Low-latency TTS model

Ultra-low-latency voice generation built for real-time applications.

**Best for:** Real-time voice, lowest latency, emotional expressiveness
**Access:** REST + WebSocket streaming
**Pricing band:** Low monthly entry plans; pay-as-you-go from ~$0.03/min

**Capabilities:**
- ~40ms time-to-first-audio
- 15+ languages
- Nonverbal expressiveness: laughter, breathing, emotional inflections
- Streaming API for real-time generation

**Ad creative use cases:**
- Real-time ad preview during creative iteration
- Interactive demo videos with dynamic narration
- Ads requiring natural laughter, sighs, or emotional reactions

---

### Open-source local voice studio

Free, local-first voice synthesis desktop studios built on open-weight TTS models. The open-source alternative to premium voice models.

**Best for:** Free voice cloning, local/private generation, zero-cost batch production
**Access:** A local REST API (for example `http://localhost:8000`)
**Pricing:** Free (permissive open-source license). Runs entirely on your machine.

**Capabilities:**
- Voice cloning from short audio samples via an open-weight TTS model
- Multi-language support (varies by model)
- Multi-track timeline editor for composing conversations
- Faster inference on Apple Silicon with Metal acceleration
- Local REST API for programmatic generation
- No cloud dependency: all processing on-device

**Ad creative use cases:**
- Free voice cloning (with documented consent) for a brand spokesperson across all ad variations
- Batch generate voiceovers without per-character costs
- Private/local generation when ad content is sensitive or pre-launch
- Prototype voice variations before committing to a paid service

**Request shape (illustrative):**
```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"text": "Stop wasting hours on manual reporting.", "profile_id": "abc123", "language": "en"}'
```

Install only from the project's official release or source, after the user authorizes the exact install.

---

### Other Voice Tool Classes

| Class | Best For | Differentiator |
|------|----------|---------------|
| **Large-library voice platform** | Large voice library, low latency | 900+ voices, <300ms latency |
| **Enterprise cloning platform** | Enterprise voice cloning | On-premise deployment, real-time speech-to-speech |
| **Actor-licensed voice platform** | Ethical, commercial-safe voices | Voices from compensated actors, safe for commercial use |
| **Budget expressive voice API** | Budget-friendly, emotion control | Roughly 50-70% cheaper than premium voice models, emotion tags |
| **Browser voice studio** | Non-technical teams | Browser-based studio, 200+ voices |
| **Hyperscaler cloud TTS** | Cloud ecosystem, scale, cost | 200+ neural voices, 40+ languages, SSML control, enterprise SLAs |

---

### Voice Tool Comparison

| Class | Quality | Cloning | Languages | Latency | Price/1K chars |
|------|---------|---------|-----------|---------|----------------|
| **Premium voice model** | Best | Yes (instant + pro) | 29+ | ~200ms | $0.12-0.30 |
| **Low-cost TTS API** | Good | No | 13+ | ~300ms | $0.015-0.030 |
| **Low-latency TTS model** | Very good | No | 15+ | ~40ms | ~$0.03/min |
| **Large-library voice platform** | Very good | Yes | 140+ | <300ms | ~$0.10-0.20 |
| **Budget expressive voice API** | Good | Yes | 13+ | ~200ms | ~$0.05-0.10 |
| **Actor-licensed voice platform** | Very good | No (actor voices) | English | ~300ms | Custom pricing |
| **Open-source local voice studio** | Good | Yes (local) | 2+ | Local | Free (open source) |

### Voice Tool Options by Need

These are options to evaluate, not rankings. Run a short script through two or
three tools and judge by ear, then check each vendor's current pricing and
language list.

```
Need voiceover for ads?
├── Clone a specific brand voice (with consent) → options include premium voice model, enterprise on-premise cloning platform, budget expressive voice API, large-library platform
├── Multilingual (same ad, many languages) → options include large-library voice platform, premium voice model
├── Free / open source / local → options include open-source local voice studio
├── Cheap and fast → options include low-cost TTS API
├── Actor-compensated voice licensing → options include actor-licensed voice platform
└── Real-time / interactive → options include low-latency TTS model
```

### Workflow: Voice + Video

```
1. Write the ad script with `suede-ad-creative`
2. Generate voiceover with a premium voice model or low-cost TTS API
3. Generate or render video:
   a. Silent video (AI-generated or code-rendered) → layer voice track
   b. Or use a native-audio video model (skip separate VO)
4. Combine with ffmpeg if layering separately:
   ffmpeg -i video.mp4 -i voiceover.mp3 -c:v copy -c:a aac output.mp4
5. Generate variations (different scripts, voices, or languages)
```

---

## Code-Based Video

For templated, data-driven video ads, render video from code instead of
prompts. AI video generators produce a different clip each time; code-based
frameworks render deterministic, brand-exact video from templates and data. Two
common options are **Remotion** (React components) and **Hyperframes** (HTML
files). For how they differ and how to pick, use `suede-video`. For licensing
and current features, check each project's own docs
([remotion.dev](https://www.remotion.dev/docs),
[hyperframes.heygen.com](https://hyperframes.heygen.com/introduction)).
Remotion is source-available rather than open source, so read its license
before commercial use.

**Best for:** Templated ad variations, personalized video, brand-consistent production

### Why Code-Based Video for Ads

| AI Video Generators | Code-based video |
|---------------------|----------|
| Unique output each time | Deterministic, pixel-perfect |
| Prompt-based, less control | Full code control over every frame |
| Hard to match brand exactly | Exact brand colors, fonts, spacing |
| One-at-a-time generation | Batch render hundreds from data |
| No dynamic data insertion | Personalize with names, prices, stats |

### Ad Creative Use Cases

**1. Dynamic product ads**
Feed a JSON array of products and render a unique video ad for each. Example in Remotion (the same template works as an HTML composition in Hyperframes):
```tsx
// Simplified Remotion component for product ads
export const ProductAd: React.FC<{
  productName: string;
  price: string;
  imageUrl: string;
  tagline: string;
}> = ({productName, price, imageUrl, tagline}) => {
  return (
    <AbsoluteFill style={{backgroundColor: '#fff'}}>
      <Img src={imageUrl} style={{width: 400, height: 400}} />
      <h1>{productName}</h1>
      <p>{tagline}</p>
      <div className="price">{price}</div>
      <div className="cta">Shop Now</div>
    </AbsoluteFill>
  );
};
```

**2. A/B test video variations**
Render the same template with different headlines, CTAs, or color schemes:
```tsx
const variations = [
  {headline: "Save 50% Today", cta: "Get the Deal", theme: "urgent"},
  {headline: "Join 10K+ Teams", cta: "Start Free", theme: "social-proof"},
  {headline: "Built for Speed", cta: "Try It Now", theme: "benefit"},
];
// Render all variations programmatically
```

**3. Personalized outreach videos**
Generate videos addressing prospects by name for cold outreach or sales.

**4. Social ad batch production**
Render the same content across different aspect ratios:
- 1:1 for feed
- 9:16 for Stories/Reels
- 16:9 for YouTube

### Code-Based Workflow for Ad Creative

```
1. Design the template (or have an AI agent write it)
2. Define data schema (products, headlines, CTAs, images)
3. Feed data array into template
4. Batch render all variations
5. Upload to ad platform
```

### Conditional Local Examples

Run these examples only when Node.js and Remotion are already available or the
user has authorized the exact install, current official documentation confirms
the commands, and the project path and output are understood. Otherwise return
the React composition plan and render specification without executing. These
are Remotion commands; for Hyperframes setup, use `suede-video`.

```bash
# Create a new Remotion project
npx create-video@latest

# Render a single video
npx remotion render src/index.ts MyComposition out/video.mp4

# Batch render from data
npx remotion render src/index.ts MyComposition --props='{"data": [...]}'
```

---

## Choosing the Right Tool

### Options by Need

Start from the approach (code-based or AI generation), then pick a tool. The
classes listed are options to evaluate, not rankings. Models change quickly, so
run the same brief through two or three and compare the output, and check
current versions and pricing on each vendor's site.

```
Need video ads?
├── Templated, data-driven (same structure, different data)
│   └── Code-based video (Remotion, Hyperframes; see suede-video)
├── Unique creative from prompts (exploratory)
│   ├── Dialogue/voiceover in the clip → options include dialogue-focused, native-audio, long-form cinematic, or low-cost high-volume models
│   ├── Consistency across scenes → options include controllable video models
│   ├── Native vertical (9:16) output → options include native-audio video models
│   ├── High volume at low cost → options include low-cost high-volume video models
│   └── Cinematic camera work → options include all-in-one video studios, long-form cinematic models
└── Both → AI generation for hero creative, code-based video for variations

Need image ads?
├── Text/headlines in the image → options include typography-specialist models, premium image models with strong text rendering
├── Product consistency across variations → options include multi-reference image models
├── Quick iterations on existing images → options include premium image models with native editing
├── Polished final assets → options include multi-reference Pro tiers, artistic community models
└── High volume at low cost → options include small/fast open-weight tiers, fast tiers of premium image models
```

### Cost Comparison for 100 Ad Variations

Rough order-of-magnitude estimates for comparing approaches, not quotes. Prices
change often; verify on each vendor's pricing page before budgeting.

| Approach | Tool Class | Approximate Cost |
|----------|------|-----------------|
| 100 static images | Premium image model | ~$4-24 |
| 100 static images | Open-weight Dev tier | ~$1-2 |
| 100 static images | Typography-specialist API | ~$6 |
| 100 × 15-sec videos | Native-audio video model, fast tier | ~$225 |
| 100 × 15-sec videos | Code-based video (templated) | Render compute only (self-hosted); check license terms |
| 10 hero videos + 90 templated | Video model + code-based video | ~$22 + render time |

### Workflow for Scaled Ad Production

1. **Generate hero creative** with AI image and video models: high-quality, exploratory
2. **Build templates** in code (Remotion or Hyperframes) based on winning creative patterns
3. **Batch produce variations** from data (products, headlines, CTAs)
4. **Iterate**: use AI tools for new angles, code-based templates for scale

This hybrid approach gives you the creative exploration of AI generators and the consistency and scale of code-based rendering.

---

## Platform-Specific Image Specs

When generating images for ads, request the correct dimensions:

| Platform | Placement | Aspect Ratio | Recommended Size |
|----------|-----------|-------------|-----------------|
| Meta Feed | Single image | 1:1 | 1080x1080 |
| Meta Stories/Reels | Vertical | 9:16 | 1080x1920 |
| Meta Carousel | Square | 1:1 | 1080x1080 |
| Google Display | Landscape | 1.91:1 | 1200x628 |
| Google Display | Square | 1:1 | 1200x1200 |
| LinkedIn Feed | Landscape | 1.91:1 | 1200x627 |
| LinkedIn Feed | Square | 1:1 | 1200x1200 |
| TikTok Feed | Vertical | 9:16 | 1080x1920 |
| Twitter/X Feed | Landscape | 16:9 | 1200x675 |
| Twitter/X Card | Landscape | 1.91:1 | 800x418 |

Include these dimensions in your generation prompts to avoid needing to crop or resize.
