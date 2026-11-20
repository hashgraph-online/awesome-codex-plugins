# Image prompt construction

## Decide whether to edit

- If the user asks to use their prompt as written, preserve it verbatim. Otherwise, check the supplied prompt for the details that matter to this image, such as subject, protected facts, setting, composition, lighting, color, style, and constraints. Leave optional creative details to the model.
- If the prompt is clear, consistent, and already meets the user's requirements, return or submit it verbatim. Apply the same test to a general request to optimize it. Follow an explicit request for a rewrite or a specific change.
- Resolve gaps or conflicts using the request and its references. Ask only if an important requirement remains unclear. If the user clarifies one phrase, replace only that phrase.
- Make the smallest edit that meets the request or fills a material gap. If one sentence is enough, append it and preserve the rest. If the selected model requires prompt reference syntax, make only the necessary binding edits. Clarify before submitting if those edits conflict with a request to preserve the prompt verbatim.

## Recommended order

Use the relevant items when writing a prompt or filling a specific gap.

1. Destination and medium: product photograph, editorial portrait, poster, thumbnail, or marketing still.
2. Subject and protected facts: identity, product structure, exact colors, logo, or copy.
3. Action or visual concept.
4. Environment, time, weather, and mood.
5. Composition: aspect ratio, framing, camera height, focal hierarchy, negative space, and safe areas.
6. Lighting and color.
7. Materials, textures, surface detail, and degree of realism.
8. Constraints: subject count, locked facts, and any requested exclusions.

Translate abstract requests such as "premium," "cinematic," or "high quality" into visible lighting, depth of field, material, color, and composition decisions instead of stacking adjectives.

## Continuous image series

In one prompt, describe what the images share, give each image one beat in sequence, and state what should stay consistent across the series. Set the actual count and resolution through the model's declared settings.

## Multiple references

Assign roles before writing the creative prompt. Identity, product structure, composition, style, and official logo references are not interchangeable. Transfer only the visual traits the user selected from a style reference; do not transfer identity or composition unintentionally.

## Exact text

- Preserve user-provided copy verbatim.
- When the user plans to add text later, leave intentional copy space in the base image.
- For generated text, include the exact copy once with any placement, hierarchy, language, or styling the user specifies. Leave unspecified typography, color, and margins to the model. Keep existing labels unless the user requests a change. Add restrictions on other text only when requested. Check the rendered copy and layout if the image is available for inspection.

## Controlled variants

Keep protected facts identical and change only one dimension at a time: concept, camera distance, composition, mood, color, or expression and action. Do not replace a clear creative decision with a batch of near-duplicates.

Avoid conflicting camera instructions, long repetitive negative lists, and unverified product or brand claims.
