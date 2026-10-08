---
name: magic-hour-text-to-video
description: Turn an idea into a short Magic Hour video when no exact identity or starting frame is required. Use for original surreal scenes, visual jokes, atmosphere or concept exploration; use Image-to-Video for an approved person, character or composition.
license: MIT
metadata:
  author: magichourhq
  version: "1.0.0"
---

# Magic Hour text to video

Translate the idea into one clear visual event. Accept “make an elevator open onto the moon”; choose the framing, pacing and model within the user's existing budget. Preserve requested creative choices. Deliver the video, with any unmet requirement made explicit.

## Decide whether a reference is necessary

Use `text_to_video_create_video` for an original scene whose exact cast and appearance can vary. If the user provides their face, a recurring character or a required starting composition, use that reference through AI Image Editor when needed, then Image-to-Video. An optional imagined character is not a reason to force a paid image step. Honor an explicit Text-to-Video request while explaining any identity limit that matters.

## Direct a visible event

Define the setup, the change and the payoff. For a short clip, choose one event that a viewer can understand without explanatory copy. Establish the subject immediately; reserve enough time to see the result. Give physical direction and timing instead of piling up adjectives.

Examples of structures, not measured viral formats:

| Intent               | Shot direction                                                                                    |
| -------------------- | ------------------------------------------------------------------------------------------------- |
| Impossible reveal    | Familiar closed door → it opens onto an unexpected world → hold long enough to read the reveal    |
| Visual joke          | Establish an ordinary action → one clear physical contradiction → visible reaction or consequence |
| Cinematic atmosphere | One focal subject, one camera move and restrained environmental motion; no unnecessary plot       |

Write subject/action → setting → framing/camera → timing/end state → essential constraints. Match the proposed action to the supported duration. Multiple unrelated events in five seconds can lose the payoff; use separately directed shots and an available compositor when the brief needs them. Avoid arbitrary fixed shot counts or slowing the whole video to hide missing action.

Example: “Locked camera inside a steel elevator. Its doors open during the first two seconds onto a lunar landscape with Earth above the horizon. Hold the impossible view for the remaining three seconds. Realistic cold light, straight door geometry, no people, text or cuts.”

## Generate, review, repair

Use the creation MCP at `https://mcp.magichour.ai/`; [setup](https://github.com/magichourhq/magic-hour-mcp/blob/main/user.md). Read current model, duration, resolution, audio and aspect support. API users should consult the [live schema](https://docs.magichour.ai/api-reference/openapi.json) for `/v1/text-to-video`. Set audio intentionally; an audio toggle does not guarantee exact dialogue, music rights or synchronized sound.

Submit one job within the existing spending authority, retain its ID, then use `wait_for_video_project`. Resume that ID after a wait timeout; never repeat an ambiguous create request. Download using the exact returned URL and verify actual dimensions, duration and streams.

Review the complete event: does the setup read, does the requested action happen, is the payoff visible, does geometry survive, and are cuts or sounds intentional? Judge physical interactions and timing, not just attractive still frames. Do not call a requested loop seamless without comparing the join.

Treat exclusions as requirements to verify. In the [actual moon-elevator run](https://github.com/magichourhq/skills/tree/main/examples/midnight-remix), the reveal worked but the output added numerals and camera movement despite explicit constraints. Check lettering and the last frame; attractive scenery alone did not pass that brief.

For an absent action, simplify the beat or provide clearer timing before changing everything at once. For wrong appearance, use an accepted still and Image-to-Video on the next authorized attempt. Preserve successful takes; do not repeatedly regenerate an accepted scene merely to change captions or export shape.

Deliver the finished file, the prompt and accepted settings in the project, and material limitations. For a series requiring the same cast, retain a usable frame as a reference for later scenes. Do not claim a text seed alone locks identity.
