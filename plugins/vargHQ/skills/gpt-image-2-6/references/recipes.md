# GPT Image 2.6 recipes: text-heavy layouts

Eight text-heavy layouts from a study of 83 X posts about GPT Image 2.5 and 2.6 (collected 2026-11-04);
the most saved were the editorial travel print (2,218 bookmarks), the storyboard (2,202) and the
character sheet (1,336). Each recipe has the settings, a prompt template and our example made
on varg with `gpt_image_2_6` on 2026-11-04/05. A community prompt is quoted word for word only where
its author published it; a non-English prompt is shown in the original with an English translation.
Fill the `[BRACKETS]`. The "photos" in the photo recipes are stand-in photos we made with the same
model, not real photographs.

Calls: see section 6 of [../SKILL.md](../SKILL.md). For a recipe marked "edit", pass the photo in `files`;
`gpt_image_2_6` then routes to the edit model by itself (+1 credit per reference).

---

## 1. Infographic (field-guide page)

**Settings:** text-to-image, `aspect_ratio: "4:3"`, `quality: "high"`, `reasoning_effort: "high"`.
**Our example:** a Red Fox page,
https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_99da5c60e85b.png

Prompt by @iamsofiaijaz (https://x.com/iamsofiaijaz/status/2113510238846672945), written for GPT Image 2.5:

```
A professional educational infographic for a [Subject], designed in a modern "Terrestrial Life" series style. The layout features a large, realistic 3D central illustration of the [Subject] with anatomical labels like "Compound Eyes," "Thorax," and "Abdomen" using thin pointer lines. The color palette is clean with soft beige and muted tones. The composition includes multiple data modules: a "Quick Profile" sidebar, a "Top 5 Amazing Facts" list, a "Size Comparison" chart against a human silhouette, and a "Knowledge Score" star rating system. Include a "Detail Focus" section on the right with four square macro-photography close-ups of life stages or specific features. The bottom features "Habitat" and "Diet" icons, a "Conservation Status" slider, and a small "Did You Know?" footer. High resolution, crisp typography, clean vector lines, and a professional scientific journal aesthetic.
```

Notes:
- The anatomical labels in the template are an insect's. Swap them for your subject's parts (the fox
  page uses "Keen Ears", "Whiskers", "Bushy Tail").
- The model writes the facts itself. Check every fact and number before you publish, or give it the
  facts: add `Use exactly these facts: "…", "…"` to the prompt.

## 2. Product launch poster

**Settings:** text-to-image, `aspect_ratio: "3:4"`, `quality: "high"`, `reasoning_effort: "medium"`.
**Our example:** SUMMIT ROAST (a fictional brand),
https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_143c5129c4b7.png

Prompt by varg (written for this skill; OpenAI says Flare "improves layout quality for posters, product
imagery, and other professional visuals"):

```
Product launch poster, 3:4 vertical. Headline at the top in a tall condensed sans serif: "[BRAND]".
Subhead under it in a light serif: "[ONE LINE, UP TO 8 WORDS]".
Hero: [PRODUCT, with its label text "[LABEL TEXT]"] standing on [SURFACE], [LIGHT, e.g. one soft key
light from the upper left], [BACKGROUND COLOUR OR GRADIENT].
Price badge: a round [COLOUR] badge with "[PRICE]" and "[UNIT]" in it.
Bottom row: three line icons, each with a short caption: "[FEATURE 1]", "[FEATURE 2]", "[FEATURE 3]".
Footer in small spaced capitals: "[FOOTER LINE]".
Spell every quoted word exactly. No other text, no logos except the brand name.
```

What the example shows: brand "SUMMIT ROAST", subhead "Single-origin. Roasted at 2,400 m.", a kraft
coffee bag on a dark stone with beans, a navy background, badge "$18" / "340 g", features "Bright
citrus", "Cocoa finish", "Ethically sourced", footer "SHIPS EVERY MONDAY".

## 3. Photo → editorial travel print

**Settings:** edit (`files: [photo]`), `aspect_ratio: "3:4"` (varg has no 4:5 preset; for 4:5 pass
`image_size: {"width": 1088, "height": 1360}`), `quality: "high"`.
**Our example:** stand-in photo
https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_de945fe48c84.png → print "LISBON,
Rainy Morning Ride" https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_c1beb16c718f.png

Prompt by @Naiknelofar788 (https://x.com/Naiknelofar788/status/2101161664892829838), written for GPT
Image 2.5:

```
A sophisticated minimalist lifestyle art poster featuring [PERSON / SUBJECT / MOMENT] as the central focus, transformed from a real-life photograph into a refined hand-drawn editorial illustration. Preserve the subject's recognizable pose, silhouette, clothing, hairstyle, and key visual details while simplifying the scene into an elegant artistic composition.

Use a limited vintage color palette inspired by the original environment, with warm muted tones printed on an ivory/off-white paper background. Combine delicate ink outlines, loose sketchwork, fine hatching, subtle halftone texture, faded print imperfections, and soft watercolor-like washes.

Reduce the surrounding environment into a few recognizable contextual elements—[CAFÉ / BAR / STREET / LANDMARK / OBJECTS]—using simplified linework and layered shapes rather than detailed realism. Add subtle abstract circles, geometric forms, atmospheric marks, tiny decorative elements, or silhouettes to create visual depth.

Include small minimalist typography on one side: [CITY / LOCATION], [SUBJECT / MOMENT], and optional coordinates, date, or short descriptor, designed like a premium collectible travel/lifestyle print.

Generous negative space, elegant editorial composition, vintage screen-print aesthetic, hand-crafted illustration, sophisticated travel-magazine design, muted heritage colors, subtle paper grain, artistic but recognizable, no photorealistic background, no excessive details, 4:5 vertical composition.
```

Notes: our print added coordinates under the title (the template allows them). They matched Lisbon, but
check yours before you print.

## 4. Photo → Baroque gallery poster

**Settings:** edit (`files: [photo]`), `aspect_ratio: "3:4"`, `quality: "high"`, `reasoning_effort: "medium"`.
**Our example:** stand-in photo of an alpine village
https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_17855ee4e472.png → framed poster
"ALPINE SERENITY" https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_d55052e95ef9.png

Prompt by @Goodmanprotocol (https://x.com/Goodmanprotocol/status/2118193088128745875), written for GPT
Image 2.6:

```
PREMIUM BAROQUE FRAMED ARTWORK - PHOTOREALISTIC GALLERY POSTER

Use the uploaded image as the sole visual reference. Create a seamless 3:4 vertical fine-art poster.

TOP SECTION (75%): Display the original scene as a beautiful painting inside an ornate antique gold Baroque frame, mounted on a subtly textured plaster wall. Preserve the original scene and its defining details. Select 1–3 prominent elements already present in the image and extend them beyond the frame in realistic 3D, with natural depth, perspective and cast shadows. Do not introduce any new objects, flowers, plants or decorative elements that are not present in the source image. Choose a muted wall color derived from the original image's palette. Match the lighting, atmosphere and time of day of the original scene. Photorealistic rendering with a sophisticated fine-art gallery aesthetic.

BOTTOM SECTION (25%): Continue the same plaster wall and lighting seamlessly. Place a small, clean thumbnail of the original unedited image slightly left of center, without a white border and with a subtle natural shadow. Beside it, add a refined 2–3-word ALL-CAPS serif title and a single-line italic subtitle inspired by the original scene. Keep the typography minimal, elegant and clearly contrasted against the wall. 

COMPOSITION & QUALITY: The entire poster must appear as one continuous image. No divider lines, white bands, gaps, separate panels or outer borders. Ensure seamless transitions, balanced spacing, realistic materials, sophisticated typography and premium editorial art direction. Preserve the original subject's identity and visual character without altering the source scene.
```

Notes: in our example nothing broke out of the frame in 3D. If you want that effect, name the element
("the wooden bridge comes out of the frame").

## 5. Landmark postcard

**Settings:** text-to-image, `aspect_ratio: "16:9"` (came back 1088×608), `quality: "high"`.
**Our example:** a suspension bridge in fog over a bay,
https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_4671ad66f76a.png

Prompt by @Maercihh (https://x.com/Maercihh/status/2117592215602233781), written for GPT Image 2.5:

```
A wide horizontal landscape hand-painted illustration of [LANDMARK NAME] in [CITY/COUNTRY] with strong emphasis on negative space and quiet composition. 

The image features a warm off-white cream paper background that occupies 40-50% of the total canvas, creating generous blank margins and breathing room. 

The [LANDMARK NAME] is positioned slightly off-center as a calm visual anchor, depicted through simplified [KEY ARCHITECTURAL FEATURES - e.g., "towering structures", "iconic silhouette", "distinctive archways"] with loose, expressive brush strokes. The landmark is suggested through minimal rhythmic marks and abstract color blocks in deep teal, cobalt blue, and forest green, rather than drawing every architectural detail precisely.

The composition is sparse and uncluttered: only a few carefully placed elements including 2-3 tiny human figures [DOING TYPICAL ACTIVITY - e.g., "walking", "taking photos", "sitting"] rendered as simple silhouettes in coral red and mustard yellow, one small [CONTEXTUAL ELEMENT - e.g., "cafe table", "bench", "street vendor cart"] with minimal shapes, two or three [NATURAL ELEMENTS - e.g., "potted plants", "trees", "flowers"] in emerald green, and subtle [CULTURAL/ARCHITECTURAL HINTS - e.g., "traditional roof lines", "modern glass panels", "historic columns"].

Large areas of the warm paper background remain completely untouched, especially around the edges and between elements.

The style combines mid-century travel poster aesthetics with contemporary [REGIONAL] editorial illustration: elegant, minimal, warm, cultured, and slightly nostalgic.

The texture shows loose hand-painted gouache and pastel marks with dry brush strokes, pastel smudges, wax-crayon edges, uneven color patches, imperfect handmade edges, and visible gaps between colored areas.

Colors are layered, dry, and tactile with a restrained palette of deep teal, sky blue, coral red, salmon pink, mustard yellow, ochre, terracotta, and small near-black accents, but used sparingly so each color can breathe against the paper.

The overall mood is quiet, spacious, relaxed, refined, like a sophisticated [CITY] cultural postcard or handmade art print suitable for premium lifestyle merchandise.

The landmark remains recognizable through its essential identity—[DEFINING CHARACTERISTICS]—but the drawing stays airy, calm, poetic, and softly abstract.

Strong sense of pause, breath, and refined emptiness with confident use of blank space.

No crowded composition, no full-bleed busy background, no photorealism, no glossy digital rendering, no clean vector art, no 3D rendering, no text, no signage, no logos, no readable text.
```

Notes: in our example the cream paper fills the sky, but the water runs to the frame edges. The prompt
says "no text" on purpose: add a caption in your layout tool afterwards.

## 6. Character turnaround sheet

**Settings:** with a reference photo: edit (`files: [character]`); without one, text-to-image with a
written description in place of "image1". `aspect_ratio: "16:9"`, `quality: "high"`, `reasoning_effort: "high"`.
**Our example:** "Mara", https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_92817f364ac7.png

Prompt by @EvoLinkAi (https://x.com/EvoLinkAi/status/2107667147019194394, the prompt for
https://x.com/EvoLinkAi/status/2107436379575840895), written for GPT Image 2.5:

```
image1 as the primary character reference. Create a polished production-ready character reference sheet and turnaround board for the same person in image1. Preserve her facial identity, hairstyle, hair color, body proportions, and overall appearance across every panel.

Show full-body front view, 3/4 view, side profile, and back view in a clean horizontal lineup. Add a large hero portrait, neutral and surprised expression studies, close-ups of the eyes, lips, makeup, hair texture, wardrobe details, and a coordinated color palette.

The character wears a warm orange short-sleeve collared dress with white sneakers. Use a warm cream background, soft studio lighting, refined editorial art-direction, subtle vintage 1990s American diner influence, clean grid layout, thin brown borders, organized annotation panels, cinematic character design presentation, highly consistent face and costume details, realistic photography mixed with premium concept-art styling.

Include minimal clean labels such as FRONT, 3/4 VIEW, SIDE VIEW, BACK VIEW, HERO PORTRAIT, EXPRESSIONS, HAIR DETAIL, and COLOR PALETTE. Wide landscape composition, high resolution, professional film pre-production character bible.
```

Notes: swap the wardrobe sentence for your character's clothes. Use a photo only of a person who agreed
to it. For a sheet that later feeds video models, see `varg-character-design` and `character-passport`.

## 7. Storyboard sheet

**Settings:** text-to-image, `aspect_ratio: "16:9"`, `quality: "high"`, `reasoning_effort: "high"`.
**Our example:** "THE LAST LIGHT", six panels,
https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_d505f9aceadb.png

Idea by @EHuanglu (https://x.com/EHuanglu/status/2098411370815643837: GPT Image turns an idea into a
storyboard, then a video model animates it; the author's prompts are on a third-party site, so they are
not quoted here). Prompt by varg:

```
Storyboard sheet, 16:9, on white paper. Title at the top: "[TITLE] – STORYBOARD".
Six panels in a 3×2 grid. Each panel has a label in its top-left corner with its number and shot
type, and one handwritten caption line under it:
1. "WIDE" – [what we see]. Caption: "[caption]"
2. "CLOSE-UP" – [what we see]. Caption: "[caption]"
3. "LOW ANGLE" – [what we see]. Caption: "[caption]"
4. "TRACKING" – [what we see]. Caption: "[caption]"
5. "POV" – [what we see]. Caption: "[caption]"
6. "FINAL" – [what we see]. Caption: "[caption]"
Style: pencil and grey wash; [ONE ACCENT COLOUR] only on [THE HERO OBJECT]. The same [HERO OBJECT]
design in every panel. Spell every quoted word exactly; no other text.
```

What the example shows: a paper boat in a flooded city at night; captions "Boat sails through flooded
city.", "Boat rides the waves.", "Lighthouse rises ahead.", "Camera follows the boat.", "Boat's POV toward
the lighthouse.", "Boat reaches the lighthouse."; orange accent on the boat.

Notes: crop single panels out of the sheet and use them as start frames for a video model (see
`kling-4-prompting` for stills as key frames).

## 8. Low-res → clean upscale

**Settings:** edit (`files: [small image]`), `image_size` set to the size you want (we asked for
`{"width": 1536, "height": 864}`), `quality: "high"`.
**Our example:** a 272×152 noisy JPEG
https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_f395c2486a58.jpg → clean 1536×864
https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_39f3af099f61.png

Prompt by @k_matsumaru (https://x.com/k_matsumaru/status/2097506834659893340), written for GPT Image 2.5.
Original (Japanese):

```
この低解像度の画像を高解像度化してください。

一切のアーティファクトの生成を許可しません。元の画像の画風、色の塗り、構図を完全に維持したまま、ノイズが生まれている箇所などを徹底的に潰し鮮明な画像にしてください。
```

English translation:

```
Please upscale this low-resolution image to high resolution.

No artifacts of any kind are allowed. Keep the original image's art style, colouring and composition
exactly as they are, thoroughly remove every place where noise has appeared, and make the image sharp.
```

Notes: the author uses it to rebuild a clean reference from a frame grabbed out of a generated video. It
redraws, so small details can change; for a faithful photo upscale use `topaz` or `clarity_upscaler`
(varg-ai models list).
