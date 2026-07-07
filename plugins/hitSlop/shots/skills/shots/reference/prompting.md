# Screenshot Prompting

Send a complete plain-text prompt to `generate_screenshot` in the `prompt`
field. Use markdown-style sections when they help, but do not force a template.
The server appends dimensions, platform constraints, and reference metadata.

Each `generate_screenshot` call creates one App Store screenshot. Write the
prompt as a creative brief for the image model, not as structured data.

## Contract

Every prompt should answer the relevant parts of this list:

- What app and campaign is this for?
- Who is the target user?
- What single job should this panel do?
- What should be visible: real UI, object hero, collage, feature grid, proof,
  human story, or full-bleed scene?
- Which references control product truth, and which references control style?
- What text should appear, or should there be no readable text?
- What must be avoided?

Use visual facts over praise words. Avoid vague terms like `stunning`,
`beautiful`, `masterpiece`, `innovative`, and `seamless`.

## Detail Bar

The prompt can be markdown, but it should not be thin. A good natural-language
prompt carries the same detail the old JSON structure tried to force:

- exact visible copy, including capitalization and line breaks when important
- panel role and audience
- composition by region: top, center, lower third, background, overlays
- subject scale, crop, rotation, and layering
- back-to-front layer stack or clear canvas regions for dense modern comps
- typography style, hierarchy, color, and text footprint
- real UI state: screen name, selected tab, controls, data, cards, buttons
- material, lighting direction, texture, highlights, shadows, and palette
- viewpoint, crop, scale, gaze, pose, and object interactions when people or
  realistic objects appear
- reference usage: what each image controls and what it must not control
- negative constraints specific to the concept

Do not make the prompt longer by filling a template. Make it longer only when
the detail helps the model render the intended screenshot.

These examples intentionally mirror the runtime BAML screenshot examples at a
conceptual level, but the plugin docs are not mechanically imported into BAML.
Keep both aligned when adding new screenshot styles.

## Proven Prompt Tactics

Pick the structure that fits the screenshot. These are useful tactics, not
templates:

- Natural creative brief: best when the concept is open-ended and taste matters.
- Back-to-front layer stack: best for dense collages, object heroes, stickers,
  cards, shadows, and overlapping UI.
- Wireframe plus copy lock: best when exact visible text and panel structure
  matter.
- Approximate coordinate map: useful when recreating a specific composition,
  but keep it loose enough for the image model to render naturally.
- Whitespace/crop-control brief: best when the model tends to overfill the
  canvas or cover important UI.
- Compact priority brief: acceptable when it clarifies hierarchy, but write it
  as plain text inside the `prompt` string. Do not send a structured object as
  the prompt value.

For high-fidelity recreations, combine two tactics: for example, a short
creative brief plus `COPY LOCK`, or a layer stack plus a priority order. For
looser ideation, use fewer sections and let the model explore.

## Prompt Shape

Use only the sections the concept needs:

```text
Create one App Store screenshot for "AppName".

Campaign job:
Audience:
Core promise:

Visible text:
Composition:
Visual direction:
Product/UI details:
Reference usage:
Avoid:
```

If the best screenshot is text-free or no-device, say that directly. Do not add
a headline, subtitle, device, or UI panel just because other examples use one.

## Text Rendering

- Put exact visible copy in quotes.
- Render exact copy once, with no extra characters.
- Specify font style, weight, size, color, placement, contrast, and hierarchy.
- Spell unusual brand names letter-by-letter when needed.
- Use short headline text; small text and dense layouts are less reliable.
- Make headline text much larger than supporting text.
- Keep critical text in the top two-thirds unless the reference intentionally
  uses another layout.
- If no text belongs, write: `No readable overlay text anywhere.`

## Photorealism And Material Detail

For photorealistic scenes, objects, or people, say "photorealistic" directly.
Then describe the image like a real capture:

- viewpoint and crop: close-up, eye-level, top-down, three-quarter, full body
- lighting: soft daylight from left, rim light, overhead studio highlight,
  golden hour, low-key dark studio
- real texture: skin pores, fabric weave, worn edges, ceramic glaze, metal
  reflections, paper grain, mesh perforations
- shadows and highlights: contact shadows, ambient occlusion, specular glints,
  soft falloff, dark recesses
- imperfections: tiny scuffs, wrinkles, uneven fibers, natural variation

For people, specify body framing, scale, gaze, pose, and object interaction:
"full body visible, feet included", "looking down at the open book", "hands
naturally gripping the handlebars", or "child-sized relative to the table".

For wide, cinematic, low-light, rain, neon, or atmospheric scenes, add extra
scale, color, and environment detail so the model does not trade realism for
mood.

## Device And Product Content

Use real app references to describe product UI. Be specific about layout, data,
states, and controls.

Good:

- `Alarm setup screen with dark background, yellow accent switch, Ringtones tab
  selected, category chips for Bright, Noisy, and Energetic, a list of sounds,
  and a floating volume slider card.`
- `Photo feedback chat with three gray message bubbles, a small image preview,
  mint "Fixed" card, bottom AI edit input, and two black action chips.`
- `3D room planner screen with a sofa selected, green bounding box, material
  swatches, vertical tool rail, bottom category tabs, and a yellow chair object
  placed in AR.`

Bad:

- `Shows the app`
- `A clean dashboard with some cards`

If no real UI reference or detailed screen description exists, stop and ask for
one before generating.

## Reference Usage

Call out exactly what each reference should do:

```text
Reference image usage:
- Reference 1: real app UI layout, visible controls, and product accuracy.
- Reference 2: existing English campaign style, palette, typography, device treatment, and background rhythm.
- Reference 3: app icon color and brand symbol language.
- Gallery inspiration: style and composition only; do not copy its UI, claims, or branding.
```

Never say only "use references." The generation model needs to know which image
controls product accuracy and which image controls style.

## Screenshot Types

### Text-Free Object Hero

Use this when the reference is mostly visual or the user asks for a targeted
material/color transformation.

```text
Create one App Store screenshot for "ALTER EGO".

Campaign job: hero atmosphere, pure visual recognition.
Audience: adults interested in psychology, philosophy, literature, and identity.

Use the gallery inspiration as a near-exact composition reference: a full-bleed,
straight-on vintage broadcast microphone on a pure black background, with the
same crop, bottom control strip, waveform panel, red record button, and blue
home button.

Apply the user change: make every metal surface of the microphone metallic pink.
Use brushed rose-gold base tones, hot pink specular highlights, and deep
magenta shadows inside the mesh perforations. Preserve the dome shape, dot mesh
pattern, horizontal band, lightning emblem, side knobs, yoke arms, stand post,
studio lighting, and bottom UI controls.

Composition details: the microphone body should dominate roughly the top 85% of
the portrait canvas, centered and straight-on, with the stand post cropped by
the dark control strip. Keep the pure black background flat and clean. Preserve
the small circular emblem on the band, the knurled texture on the knobs, the
soft overhead highlight on the dome, and the falloff into darker side shadows.

No readable overlay text anywhere. No app name, tagline, badge, device frame,
headline, subtitle, or extra UI. The result should feel like the same image
re-shot with the microphone made from pink metal.
```

### Chaotic Social Collage

Use this for social, photo, dating, AI feedback, youth culture, or anything that
should feel loud, conversational, and shareable.

For this style, the prompts that work best are specific but not bureaucratic:
state the target visual bar, quote the exact large text, then describe the
composition as a back-to-front layer stack. Every sticker, card, heart, chat
bubble, avatar, and photo label should either prove the product or sharpen the
emotional joke. Avoid asking for "lots of fun elements" without assigning each
one a job.

```text
Create one App Store screenshot for "Picky".

Campaign job: make users instantly understand that the app helps choose the best
photo before posting.
Visible text: "GUESSING" as the biggest word in hot pink bubble lettering;
"WHICH PHOTO TO POST" below in black; bottom sticker label "Let AI Analyze +
Friends vote".

Composition: no traditional phone frame. Make the panel a layered collage with
a clear back-to-front stack: bright sky/flash background with soft cloud blur;
cropped red stoplight at the top reading "STOP"; huge glossy hot-pink headline;
large hand holding three printed selfie photos; extra tilted photo cards peeking
from the bottom edge; tiny gray file-name labels like IMG_1992.JPG; small avatar
circles overlapping the bottom label; and glassy heart stickers in the
foreground.

Visual direction: glossy Gen-Z collage, oversized type, pink-and-black contrast,
cutout photography, glassy pink/purple hearts, sticker shadows, tab-pill UI,
soft glow, and playful imperfections. The layout should feel like a polished
campaign comp, not a rough moodboard. It can be crowded, but every sticker,
photo, avatar, and label should point back to the photo-choice concept and stay
readable at thumbnail size.

Product/UI details: include a small bottom sticker card with avatar stack and
the words "Let AI Analyze + Friends vote". The plus icon can be a small glossy
rounded-square button between the headline lines. Do not show a generic phone
dashboard; the proof is the photo cards and social voting language.

Avoid generic dashboard UI, fake App Store chrome, unreadable tiny body copy,
random stickers unrelated to photo feedback, recognizable third-party
photography, creator likenesses, and any beauty claim that implies guaranteed
results.
```

### Commerce Deal Collage

Use this for shopping, marketplace, drops, coupons, resale, wishlists, and deal
apps where the screenshot needs to feel like a polished campaign poster and
still prove real product value.

```text
Create one App Store screenshot for "Golden Hour".

Campaign job: make shoppers feel that premium deals are personalized, urgent,
and curated just for them.
Audience: fashion shoppers who respond to limited-time drops, strong visual
merchandising, and simple savings proof.

COPY LOCK
Use this exact visible text where it appears:
"TOP BRANDS PICKED FOR YOU"
"GOLDEN HOUR 00:27:07"
"You've got just 1 hour to grab what you love - after that, it's gone. Fresh deals drop tomorrow!"
"Items" "27"
"Total Savings" "$2145"
"-60%" "MARA" "Linen Dress" "$29" "$72" "BUY NOW"
"-70%" "COAST" "Card Holder Wallet" "$59" "$198" "BUY NOW"

Composition: full-bleed warm peach background with a huge rounded cream poster
card nearly filling the canvas. At the top, set the headline in three stacked
lines of heavy black uppercase type. Under it, place one central white rounded
shopping UI panel with the countdown row, body copy, stats row, and two product
cards. Surround the UI with realistic fashion cutouts: white sneakers upper
left, black sunglasses upper right, orange heart sticker on the right edge,
black wallet mid-right, leopard boot lower left, denim jeans and orange sneaker
across the bottom, and an olive handbag lower right.

LAYER STACK
Back: peach background and cream poster card with white stroke.
Middle: headline, then the clean white deal panel.
Front: product cutouts and sticker accents, each casting soft editorial shadows
onto the card. Crop the foreground products at the canvas edges for depth
without covering product names, prices, or buttons.

Visual direction: polished fashion flash-sale collage, premium e-commerce UI,
cream/peach/orange palette, realistic product photography, soft shadows,
rounded surfaces, and clear thumbnail-first hierarchy. The panel should feel
like a high-end shopping campaign, not a generic marketplace grid.

Avoid: phone hardware, App Store badges, install buttons, extra product cards,
invented brand partnerships, unreadable tiny claims, clutter that competes with
the headline, or product cutouts that hide the deal UI.
```

### Bold Utility / Mascot

Use this for practical apps that need one urgent promise: alarms, reminders,
budgeting, receipts, routines, task managers.

```text
Create one App Store screenshot for "SuperAlarm".

Campaign job: hero promise for heavy sleepers.
Visible text: "Don't oversleep again" in huge rounded black letters. Small brand
mark "SuperAlarm" at top. Bottom proof line "Made by HEAVY SLEEPERS" and rating
"4.7" only if supplied by the app record.

Composition: bright yellow full-bleed background with a large rounded white card
shape filling most of the panel. A black iPhone alarm screen sits tilted in the
lower half, showing 07:00, SuperAlarm, a yellow Snooze button, and a dark Turn
off slider. A cheerful sun mascot peeks from behind the phone and a
pillow/blanket illustration sits behind it.

Visual direction: high-contrast black/yellow system, chunky friendly typography,
simple mascot shapes, practical UI proof, energetic morning tone.

Reference usage: use the real alarm reference for the exact dark screen style,
yellow controls, and mascot proportions. Use the poster reference for the
rounded card shape and headline scale.

Avoid thin typography, muted colors, generic productivity dashboard cards,
extra feature lists, invented ratings, and tiny alarm settings text.
```

### Feature Grid

Use this when the app has many modes or actions and the screenshot needs to
communicate variety fast.

```text
Create one App Store screenshot for "SuperAlarm".

Campaign job: show why alarms are hard to dismiss.
Visible text: "Solve tasks to stop the Alarm" in huge rounded black text.

Composition: bright yellow background. Arrange eight black rounded task tiles
in a clean grid: Math, Push-up, Walk, Face ID, Object scan, QR/Barcode Scan,
Shake, and Memory. Each tile has a bold simple icon or mini illustration in
purple, teal, orange, or yellow.

Visual direction: playful but utilitarian, strong contrast, big touch-target
tiles, simple shadows, no device frame. Make the grid feel like a product
feature screen and a poster at the same time.

Layout details: leave a large top text block, then place the grid below it with
consistent tile spacing and slight tile rotation only if it keeps the grid
readable. Use thick rounded typography and high-contrast labels inside each
tile. The icons should feel like actual task modes, not random decorative art.

Avoid adding a phone unless the approved concept asks for one, and do not add
more than the eight task tiles.
```

### Editorial Media Collage

Use this for books, music, film, culture, journaling, or social discovery.

```text
Create one App Store screenshot for "Tome".

Campaign job: make the app feel like a refined home for readers and bookish
community.
Visible text: "blog about Books, find Reading Buddies on TOME" with "Books" and
"Buddies" huge in elegant white serif type, "blog about" and "find" in italic,
and "Reading" handwritten in hot pink.

Composition: black full-bleed editorial poster. At the top, cropped book covers
overlap like a shelf and are partially cut off by the top edge. Along the
bottom, circular reader avatars overlap the edge in a community row. Keep
strong negative space around the typography so the panel reads like a magazine
ad, not a dashboard.

Visual direction: magazine spread, literary, high contrast, serif display type,
small handwritten pink accent, tasteful book-cover collage, premium social
reading mood.

Reference usage: book covers and avatars are style/content proof; do not copy
another app's branding. Preserve the editorial type contrast: huge serif words,
small italic connective words, one handwritten pink accent.

Avoid generic e-reader UI, fake bestseller claims, stock book mockups, and
clutter that weakens the large type.
```

### Notebook / Hand-Drawn Brand Panel

Use this when the app has a parent, school, journaling, calendar, kids, or
personal organization angle and the brand can support a warm hand-made style.

```text
Create one App Store screenshot for "Peggy".

Campaign job: instantly explain that Peggy filters school chaos for parents.
Visible text: "Let Peggy filter school stuff" in large mixed blue and navy type.
Small supporting words clustered to the right of "stuff": "emails", "RSVPs",
"forms", and "deadlines".

Composition: full panel looks like lined notebook paper with a red margin line,
blue ruled lines, small doodled paper airplanes, and a simple hand-drawn parent
character near the top. Place the headline across the middle with the Peggy P
logo as a rounded-square inline mark between "Let" and "Peggy". At the bottom,
show a cropped calendar strip with two real-feeling school events such as
"Piano Lessons" and "Tennis Club Meetup"; keep the events secondary.

Visual direction: friendly school-paper texture, dark navy ink illustration,
soft blue brand type, hand-drawn warmth mixed with clean app-store readability.
It should feel like a parent's messy school inbox has been made simple.

Avoid polished corporate stock imagery, generic email inbox UI, fake badges,
and too many tiny event details.
```

### Calm Product Workflow

Use this for home design, planning, travel, health, finance, or any app where
trust and product clarity matter.

```text
Create one App Store screenshot for "RoomPlan".

Campaign job: show that users can customize a real space.
Visible text: "Customize furniture" in large dark blue rounded sans-serif at
the top.

Composition: soft sky-blue panel with an iPhone centered below the headline.
The phone screen shows an AR room scene with a yellow chair selected, a bright
green 3D bounding box around it, and bottom circular controls for settings,
confirm, and delete. A pill-shaped callout overlaps the phone bottom reading
"600+ items to choose". Keep everything clean, airy, and easy to scan.

Visual direction: calm pastel product demo, soft rounded panel edges, realistic
interior photo, clear AR selection lines, subtle shadows, trustworthy design
tool feel.

Product/UI details: keep the phone screen dominated by the room camera view, not
menus. The selected chair should be visibly inside the green box. Bottom
controls should be large circular buttons, with the checkmark in the center. If
material swatches appear, keep them as a small floating palette, not a crowded
catalog.

Avoid exaggerated 3D fantasy furniture, messy room clutter, tiny unreadable
menus, and unsupported proof.
```

### Founder Or Testimonial Panel

Use this only when the user supplies the founder story, quote, customer story,
or proof.

```text
Create one App Store screenshot for "Peggy".

Campaign job: build trust through a human founder story.
Visible text: "Made with love by a Dad of 3" at the top. Show a founder-style
signature "Nick Gidwani, Founder of Peggy" and the quote "I made this app for
my family, and for parents everywhere, to simplify their lives!"

Composition: friendly blue background. Center a paper-like hand-drawn family
card with scalloped white edges, a simple parent-and-kids sketch, soft shadow,
and playful handwritten labels. Place the founder name and title under the card,
then the quote near the lower third with generous margins.

Visual direction: warm, personal, school-family utility, hand-drawn illustration
mixed with polished app-store typography. This should feel sincere and human,
not like a corporate testimonial ad.

Reference usage: use the supplied founder/family story exactly; do not invent a
new quote, founder name, job title, or family details. Match the blue background
and casual marker-like drawing style from the reference.

Avoid stock-photo business imagery, fake review stars, fake press logos, or any
quote not supplied by the user.
```

## Visual Defaults

- One promise per panel.
- Device should not stretch to fill the canvas.
- Use real UI as the proof, not generic decorative UI.
- Backgrounds should support the promise without overpowering the subject.
- Breakout elements must relate to actual UI or the app's value.
- Do not request fake App Store chrome, badges, gutters, borders, dividers, or
  rounded screenshot frames.

## Platform Notes

- iPhone: use iPhone 15 Pro or iPhone 16 Pro frames only when the concept
  needs a phone. Device usually works best at roughly 55-65% canvas width.
- iPad: wider layouts need larger typography and often work better in landscape.
- Android: use Pixel or Samsung framing when a phone is needed; do not mention
  iOS-only UI like Dynamic Island.
- Watch: keep copy extremely short and prioritize big, high-contrast iconography.

## Revision Block

For revisions, append a short block to preserve what already works:

```text
REVISION INSTRUCTIONS

Change:
- {exact requested change}

Preserve:
- positioning, panel role, crop safety
- theme, palette, and typography unless explicitly changed
- unchanged device UI and approved copy

Constraints:
- keep everything else stable
```
