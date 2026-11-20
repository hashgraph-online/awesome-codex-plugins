# Image prompt construction

## Decide whether to edit

- Honor a request to use the prompt verbatim. When the user supplies a prompt, check the subject, protected facts, scene, composition, lighting, style, and constraints that matter for the requested use. Leave discretionary details to the model.
- If the prompt is clear, consistent, and already meets the request, return or submit it verbatim. Apply the same check to a general request to optimize it.
- Resolve consequential gaps, ambiguities, or conflicts using the user's request and references. If a key detail remains unclear, ask before finalizing the prompt. Apply the answer only where it resolves the ambiguity.
- Change only the text needed to resolve the issue or make the requested edit. If one sentence is enough, append it to the original. For model-specific reference syntax, adjust only the required references.

## Recommended order

Use the relevant items below when writing a new prompt or filling a gap.

1. Destination and medium: product photograph, editorial portrait, poster, thumbnail, or marketing still.
2. Subject and protected facts: identity, product structure, exact colors, logo, or copy.
3. Action or visual concept.
4. Environment, time, weather, and mood.
5. Composition: aspect ratio, framing, camera height, focal hierarchy, negative space, and safe areas.
6. Lighting and color.
7. Materials, textures, surface detail, and degree of realism.
8. Applicable constraints such as subject count, locked facts, text restrictions, and watermark requirements.

Translate abstract requests such as "premium," "cinematic," or "high quality" into visible lighting, depth of field, material, color, and composition decisions instead of stacking adjectives.

## Continuous image series

State what stays consistent across the set, such as the subject's appearance, outfit, location, and lighting. Then describe each image in narrative order with one distinct action or composition per image. Ask for separate images in one generation and describe shared references once.

## Multiple references

Assign roles before writing the creative prompt. Identity, product structure, composition, style, and official logo references are not interchangeable. Transfer only the visual traits the user selected from a style reference; do not transfer identity or composition unintentionally.

## Exact text

- Preserve user-provided copy verbatim.
- If the user chooses to add the text in post-production, reserve space for it in the base image.
- For generated text, include the exact copy and any placement, hierarchy, or language the user specifies. Leave unspecified typography, color, and margins to the model. If the user asks to add a single headline, add that headline and preserve existing labels. Restrict other text only when the user asks. Check spelling and legibility when inspecting the result.

## Controlled variants

Keep protected facts identical and change only one dimension at a time: concept, camera distance, composition, mood, color, or expression and action. Do not replace a clear creative decision with a batch of near-duplicates.

Avoid conflicting camera instructions, long repetitive negative lists, and unverified product or brand claims.
