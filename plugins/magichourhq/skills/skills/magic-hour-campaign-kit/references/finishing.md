# From generated media to a finished ad

Use Magic Hour for appearance and motion. Use the available compositor for exact text, logos, coordinates, timing, and export. Do not promise a composition tool is part of the MCP: inspect available tools first. If none is available, deliver the accepted media and an explicit unfinished layout brief.

## Choose the next operation

| Remaining problem | Next operation | Acceptance check |
| --- | --- | --- |
| Product identity, setting, or lighting is wrong | AI Image Editor, starting from the approved original | Compare label, cap, geometry, material, and colors before animation |
| Approved still needs motion | Image to video; describe motion rather than redesigning the scene | Watch the full clip for identity drift and copy-area intrusion |
| Headline, CTA, logo, or exact placement is missing | Compose with original brand assets and editable text | Exact spelling, no clipping, requested coordinates and contrast |
| Wrong canvas shape but source is acceptable | Contain the source within a designed layout, or crop only if all requirements survive | No stretched product or hidden required content |
| Source is too small for its intended display size | Obtain an adequately detailed source within budget, or disclose the limitation | Judge at actual delivery size; upscaling dimensions alone is not proof |

Do not regenerate an accepted product merely to change a headline. Do not repair a wrong label by covering it with an unrelated overlay; obtain a faithful source or report the failure.

## Establish the export contract

Read the actual destination/template requirements: canvas size, duration, file type/codec, size limit, copy and platform-overlay regions, and audio. Distinguish a web hero loop, a catalog image, and an ad; they have different acceptance criteria. Use exact user copy and original logos. Never invent a discount, performance claim, testimonial, or destination URL.

For a contained source, calculate scale as `min(panel_width/source_width, panel_height/source_height)`. Cap at 1 when avoiding enlargement. Center the resulting dimensions within the panel or use the requested alignment. Use even dimensions where the encoder requires them. If the user needs a full-bleed result, a contained panel is a proposed layout change, not fulfillment of that requirement.

Reserve fixed copy regions outside the moving picture when motion could cross the text. Fit text by measuring/rendering it; reduce size or deliberately wrap within the user's hierarchy. Do not silently rewrite supplied copy to fit. Preserve required watermarks and disclose them.

## Assemble and inspect

Use the user's existing editor/compositor. For a simple local export, FFmpeg can pad, overlay and draw exact text without another generation. Put user copy in UTF-8 text files and use `drawtext=textfile=…:expansion=none`; never splice arbitrary copy into a shell command or filter expression. Use a font the user has rights to use, and retain its name/path in the handoff without publishing the font file.

Decide audio explicitly: retain, mute, or replace with an authorized track. Check the actual source streams. A shorter music track must not accidentally truncate the picture; a silent sample must not be presented as an audio demonstration. Verify synchronization and endings when audio is included.

If source motion is shorter than the requested duration, generate enough motion within authorization, or use a deliberate hold/loop only when it meets the brief. A six-second export with one second of motion is not six seconds of generated motion. Inspect loop seams and disclose holds; never hide them with the export duration.

Render, then decode the exported file and inspect the full playback where available. Also inspect beginning, transition/hold boundary, and final frame. Verify actual dimensions, duration, frame rate, codec, audio streams, text, logo, product identity, clipping, and platform-overlay regions. A successful encode does not establish visual quality or platform acceptance.

Deliver the final media, a poster if useful, editable text/layout sources, and source project IDs. State unresolved requirements. The [public AURORA example](https://github.com/magichourhq/skills/tree/main/examples/aurora-finished) contains an executed FFmpeg recipe and its limitations; it is one square layout, not a universal platform template.
