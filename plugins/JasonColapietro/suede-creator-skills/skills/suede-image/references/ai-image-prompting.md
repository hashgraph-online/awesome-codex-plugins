# AI Image Prompting Guide

How to write effective prompts after a current callable image tool, rights
boundary, and cost ceiling have been verified. Provider and model names change;
do not treat this guide as evidence that a model or capability is available.

---

## Prompt Structure

A strong image prompt follows this formula:

```
[Subject] + [Setting/context] + [Visual style] + [Lighting] + [Composition] + [Technical specs]
```

### Example Prompts by Use Case

**Blog hero (SaaS product):**
```
A clean workspace with a laptop displaying a colorful analytics dashboard,
minimalist desk with a coffee cup and notebook,
bright natural window lighting from the right,
shallow depth of field, commercial photography style,
1200x630, high resolution
```

**Social media graphic (announcement):**
```
Abstract flowing gradient in deep purple and electric blue,
geometric shapes forming a network pattern,
dramatic rim lighting on edges,
modern tech aesthetic, clean and minimal,
1080x1080, vibrant colors
```

**Product lifestyle shot:**
```
A person in a modern office smiling while looking at a tablet,
screen content intentionally out of focus for later compositing,
warm candid photography, natural lighting,
medium shot, shallow depth of field, editorial style
```

**Profile banner (professional):**
```
Wide panoramic abstract background in navy blue and teal,
subtle geometric grid pattern with soft gradient,
clean corporate aesthetic, muted lighting,
1584x396, no text, space for logo overlay on left third
```

**Directory listing (Product Hunt):**
```
A supplied real product screenshot on a clean gradient background,
soft shadow underneath, slight 3D perspective tilt,
modern SaaS product presentation style,
1270x760, bright and professional
```

---

## Style Keywords

### Photorealistic
- "commercial photography"
- "shot on Canon EOS R5"
- "editorial style"
- "natural lighting"
- "shallow depth of field"

### Clean/Corporate
- "clean modern aesthetic"
- "minimal design"
- "professional corporate style"
- "bright and airy"
- "white background"

### Illustrative
- "flat vector illustration"
- "isometric 3D render"
- "hand-drawn sketch style"
- "watercolor illustration"
- "line art"

### Abstract/Brand
- "flowing gradient"
- "geometric pattern"
- "abstract data visualization"
- "particle effects"
- "holographic iridescent"

### Tech/SaaS
- "dark mode UI aesthetic"
- "neon accent lighting"
- "glassmorphism"
- "futuristic minimal"
- "developer-focused"

---

## Lighting Keywords

| Term | Effect | Best For |
|------|--------|----------|
| **Natural light** | Warm, organic feel | Lifestyle, editorial |
| **Studio lighting** | Even, controlled | Product shots |
| **Rim lighting** | Edge highlights, dramatic | Hero images, abstract |
| **Soft directional** | Gentle shadows, dimensional | Blog headers |
| **Volumetric** | Light rays, atmospheric | Dramatic, cinematic |
| **Flat/even** | No shadows, clean | Icons, diagrams |
| **Golden hour** | Warm orange tones | Lifestyle, outdoor |
| **High key** | Bright, minimal shadows | Clean, corporate |

---

## Composition Keywords

| Term | Effect | Best For |
|------|--------|----------|
| **Rule of thirds** | Subject off-center | Editorial, lifestyle |
| **Centered** | Subject in middle | Product shots, icons |
| **Wide/panoramic** | Expansive view | Banners, headers |
| **Close-up/macro** | Detail focus | Texture, product detail |
| **Bird's eye/overhead** | Top-down view | Desk setups, flat lays |
| **Negative space** | Room for text overlay | Blog headers, banners |
| **Symmetrical** | Balanced, formal | Corporate, luxury |

---

## Tool-Specific Research

Before adapting a prompt to a provider:

1. Discover whether an image generator or editor is actually callable in the
   current session.
2. Read its current official documentation for prompt syntax, model availability,
   input types, editing/reference support, output sizes, retention, commercial
   terms, safety restrictions, rate limits, and price.
3. Record the documentation URL and check date.
4. Confirm rights to every uploaded asset and explicit authority for paid use.
5. Run a low-cost test and inspect exact text, brand fidelity, people, hands,
   product UI, cropping, artifacts, and metadata.

OpenAI, Google, Black Forest Labs, Ideogram, Midjourney, Recraft, and self-hosted
diffusion are possible research candidates. Their presence here is not a routing
instruction, recommendation, current model list, or capability claim.

---

## Common Prompt Mistakes

| Mistake | Why It Fails | Fix |
|---------|-------------|-----|
| "A professional image" | No visual detail | Describe subject, setting, style, lighting |
| Long paragraph of text in image | Generated text may be inaccurate | Add exact text deterministically after generation |
| "Make it look good" | Not actionable | Specify style: "commercial photography, bright" |
| Overlong prompts | Important constraints can conflict | Start concise, then add only tested constraints |
| No aspect ratio | Output may not fit placement | Specify the verified placement ratio |
| "Logo in bottom right" | Unreliable placement | Add logos in post-processing |
| "Make it viral" | Not a visual instruction | Describe the aesthetic you want |
| Requesting UI screenshots | AI hallucinates interfaces | Capture real screenshots instead |

---

## Batch Generation Workflow

When you need multiple images with consistent style (e.g., a blog series or social campaign):

1. **Generate a small approved test batch** with different style prompts
2. **Pick the winning style** based on brand fit
3. **Save the exact prompt** as your template
4. **Use a verified reference-input capability** when available and rights-safe
5. **Batch generate** variations only within the approved cost ceiling
6. **Post-process**: add text overlays, logos, crop to platform sizes

---

## Aspect Ratios Quick Reference

These are planning references. Verify current platform specifications, safe zones,
format limits, and the actual site component before production.

| Use Case | Ratio | Pixels | Notes |
|----------|-------|--------|-------|
| Blog hero / OG image | 1.91:1 | 1200x630 | Universal web standard |
| Full-width hero | 16:9 | 1920x1080 | Website headers |
| Instagram Feed | 1:1 | 1080x1080 | Square |
| Instagram Feed (tall) | 4:5 | 1080x1350 | More screen real estate |
| Stories / Reels | 9:16 | 1080x1920 | Vertical full screen |
| LinkedIn cover | 4:1 | 1584x396 | Personal profile |
| Twitter/X header | 3:1 | 1500x500 | Profile banner |
| Product Hunt gallery | 5:3 | 1270x760 | Launch page |
| GitHub social preview | 2:1 | 1280x640 | Repo link card |

---

## Cost Control

- Verify current pricing and calculate the maximum cost before generation.
- Start with the smallest approved test batch and a lower-cost verified mode when
  it still satisfies the evaluation need.
- Use rights-cleared references only when the callable tool supports them.
- Batch similar requests within rate, review, and budget limits.
- Cache reusable approved backgrounds, patterns, and textures.
- Crop, overlay exact text, and adjust color locally when that is cheaper and
  preserves source truth.
