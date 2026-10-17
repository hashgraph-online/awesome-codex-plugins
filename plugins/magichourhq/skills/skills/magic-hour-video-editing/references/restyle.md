# Restyle a performance without confusing the tools

Use `ai_video_editor_create_video` for an instruction such as changing a room or rendering style. Use `video_to_video_create_video` when the requested result is a supported stylized reinterpretation of the source footage. Neither is a lossless editor or an exact motion-transfer guarantee.

For Video-to-Video, read the current art styles and compatible models/versions. Set `assets.video_source: file`, `video_file_path` and the source interval. `fps_resolution: FULL` requests the input frame rate; `HALF` requests half. Choosing HALF can reduce motion detail; it is not equivalent to a smooth full-rate result. Probe the actual export.

Select `style.prompt_type` deliberately: `default` uses the style's prompt and ignores your custom text; `custom` uses the supplied prompt; `append_default` combines it with the style default. Do not pass a careful preservation prompt under `default` and claim it was applied. The schema notes that v1 may still add its style LoRA prompt. A version description is routing guidance, not proof of fidelity for this clip.

Start with a representative interval containing the hardest turn, object contact or cut. Inspect the first frame, facial details, hands, edges and action across the complete interval. Compare against the original at the same time points. Style changes can shift gestures or redraw objects even when attractive.

In the [published Ink/v2 example](https://github.com/magichourhq/skills/tree/main/examples/scene-remixes), the custom request produced a glossy colored treatment and changed facial details. A supported style name did not establish the intended look. The case retains that miss and a separate Video Editor repair attempt; use the actual outputs to assess the route, not the enum's name.

Use `/v1/video-to-video` and the ordinary upload/create-once/wait/download lifecycle from the parent skill. Preserve the clean source and original soundtrack. If an edit breaks identity or timing, return to that source; do not feed an unaccepted restyle into another generative pass. Assemble captions and crop only after picture review.
