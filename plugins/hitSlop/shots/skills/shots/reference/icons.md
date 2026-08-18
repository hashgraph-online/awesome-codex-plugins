# App Icon Generation

Use the two-step hosted icon flow:

1. `generate_icon_moodboard` creates a 2048x2048 moodboard with about 20 numbered
   concepts. Cost: 5 generation credits.
2. `generate_icon` creates one 1024x1024 source artwork icon per call. Cost: 3
   generation credits.

Ask before spending credits. Present the moodboard and let the user pick concept
numbers before generating finals.

Icon candidate commands use media-derived access. Use `icons.get`,
`icons.set_current`, and `icons.delete` with the icon `mediaId`; do not pass an
`appId` for those candidate-specific operations.

## Prompt Contract

The MCP tools use structured arguments, but the creative prompt itself should be
plain text. Do not send JSON-shaped image prompts. Put the art direction in
`creative_direction` as a natural-language creative brief, and use the dedicated
tool fields (`style`, `symbol`, `background`, `styles`) only to make the request
easier to scan.

Good icon briefs read like this:

```text
Create one 1024x1024 full-bleed square app icon source artwork for "AppName".

Icon job: communicate the app's core promise at thumbnail size.
Focal symbol: one clear object or abstract mark.
Visual direction: material, palette, lighting, and mood.
Background: full-bleed color/texture/gradient to every edge.
Avoid: no text, no rounded mask, no preview tile, no outer frame.
```

Keep the brief concise for simple icons. Add material, lighting, and texture
detail when the icon depends on a 3D, glossy, glass, metallic, clay, or
photorealistic treatment.

## Required Direction

Before the moodboard, lock:

- app name and category
- core promise
- audience
- brand colors or mood
- current icon or visual references, if available
- 3-6 style families to explore

For final icons, ask for or infer:

- chosen moodboard concept number
- symbol or object
- background treatment
- style notes to preserve
- material and lighting details, if dimensional

## Source Artwork Rules

Prompt for square, full-bleed, upload-ready source artwork:

- 1024x1024 PNG final output
- full color and texture to every edge
- no rounded-corner mask
- no App Store preview tile
- no outer background or presentation card
- no text, letters, labels, watermark, badge, or fake notification
- no black corner voids
- one strong focal point
- readable silhouette at small App Store sizes

Apple and Xcode apply rounded masks later. The generated source should be a full
square asset.

## GPT Image 2 Guidance

- For 3D/glossy icons, name the material: glass, metal, clay, soft plastic,
  enamel, velvet, paper, ceramic, liquid, or another concrete surface.
- Specify lighting direction and behavior: soft top-left key light, rim light,
  specular highlights, contact shadows, ambient occlusion, reflected color.
- For flat or geometric icons, ask for clean vector-like shapes, strong
  silhouette, balanced negative space, minimal strokes, and crisp contrast.
- For character or mascot icons, keep the body simple and avoid tiny facial
  features. The character should read clearly as a thumbnail.
- For photorealistic object icons, say "photorealistic" and describe real
  texture, imperfections, shadows, crop, and camera angle.
- Avoid unsupported claims, ratings, awards, press badges, follower counts, and
  third-party logos.

## Moodboard Plan

Use a small planning table before the moodboard:

```markdown
| Direction | Symbol | Style | Why it fits |
| --- | --- | --- | --- |
| 1 |  |  |  |
| 2 |  |  |  |
| 3 |  |  |  |
```

Good directions:

- one clear symbol or visual metaphor
- recognizable at small size
- distinct silhouette
- tied to the app's actual value
- fits the app's category norms without disappearing into them

Avoid:

- generic gradients with no symbol
- complex scenes
- tiny UI screenshots inside the icon
- multiple unrelated objects
- unsupported mascots or brand claims
- text or letter marks unless the user explicitly asks for a brand-mark concept

## Style Families

- Character/mascot: education, kids, habit, playful consumer apps
- Dimensional 3D: finance, productivity, creator tools, premium utilities
- Minimal geometric: developer tools, B2B, infrastructure, focused utilities
- Glass/translucent: creative tools, cameras, social apps, premium utilities
- Editorial/luxury: fashion, beauty, lifestyle, premium services
- Soft wellness: meditation, family, journaling, health
- Kinetic sport: fitness, events, action apps
- Photorealistic object: food, home, craft, audio, camera, or physical-product apps

## Example Moodboard Request

Use tool fields, not a JSON prompt object:

```text
Tool: generate_icon_moodboard
appId: APP_ID
styles:
- calm warm utility
- minimal geometric
- soft dimensional
creative_direction:
Explore app icon concepts for a calm meal-planning app. The icon should
communicate dinner clarity, household warmth, and practical organization without
using text. Favor one strong symbol per concept: plate, pantry shelf, calendar
tab, grocery basket, or abstract dinner-table geometry. Use warm olive, soft
cream, muted gold, and charcoal accents. Every concept should be full-bleed,
readable at small size, and free of rounded masks or preview tiles.
```

## Example Final Icon Requests

Cute mascot:

```text
Tool: generate_icon
appId: APP_ID
style: friendly rounded mascot from moodboard concept 7
symbol: simple owl head holding one small flashcard
background: bright warm blue full-bleed background with subtle radial depth
creative_direction:
Create one upload-ready 1024x1024 square app icon source artwork. Keep the owl
large, centered, and readable as a thumbnail. Use soft clay-like 3D material,
rounded forms, tiny beak, simple eyes, and a single flashcard shape. No text, no
letters on the card, no rounded mask, no border, no preview tile.
```

Premium dimensional:

```text
Tool: generate_icon
appId: APP_ID
style: premium dimensional 3D from moodboard concept 3
symbol: abstract upward bar chart folded into a shield
background: deep navy full-bleed background with soft teal rim light
creative_direction:
Create a confident finance icon with one polished focal symbol. The shield and
bar-chart form should feel like brushed graphite and teal glass, with a soft
top-left key light, subtle edge highlights, contact shadow, and strong silhouette.
No text, no numbers, no outer frame, no rounded-corner preview.
```

Minimal geometric:

```text
Tool: generate_icon
appId: APP_ID
style: minimal geometric from moodboard concept 12
symbol: interlocking brackets forming a lightning bolt
background: full-bleed charcoal square with one electric green accent
creative_direction:
Create a developer-tool icon with crisp vector-like geometry, high contrast, and
balanced negative space. Use two bracket shapes that interlock into a lightning
bolt. Keep strokes thick enough for thumbnail readability. No text, no border,
no preview tile, no decorative code fragments.
```

Glass/translucent:

```text
Tool: generate_icon
appId: APP_ID
style: translucent glass object from moodboard concept 5
symbol: layered camera aperture inside a rounded glass prism
background: full-bleed midnight indigo with cyan and magenta light falloff
creative_direction:
Create one premium creative-tool icon. The focal object is a translucent glass
aperture prism with believable refraction, rim highlights, soft caustic glow,
and a clear silhouette against the dark background. No text, no camera UI, no
rounded mask, no App Store tile preview.
```

Editorial luxury:

```text
Tool: generate_icon
appId: APP_ID
style: editorial luxury from moodboard concept 9
symbol: single satin ribbon folded into a bookmark shape
background: full-bleed deep burgundy with subtle paper grain
creative_direction:
Create one tasteful lifestyle icon with a satin ribbon bookmark as the only
focal symbol. Use warm directional light, soft fabric sheen, realistic fold
shadows, and a restrained burgundy, champagne, and ink palette. Keep it elegant
and sparse. No text, no monogram, no badge, no border, no rounded preview.
```

Photorealistic object:

```text
Tool: generate_icon
appId: APP_ID
style: photorealistic object icon from moodboard concept 14
symbol: small ceramic espresso cup seen from a three-quarter top angle
background: full-bleed matte sage with soft morning shadow
creative_direction:
Create a photorealistic 1024x1024 app icon source artwork. The espresso cup
should be large, centered, tactile, and simple enough to read at small size.
Show ceramic texture, tiny rim highlights, warm coffee surface, realistic contact
shadow, and natural imperfections. No text, no saucer clutter, no rounded mask,
no preview tile.
```
