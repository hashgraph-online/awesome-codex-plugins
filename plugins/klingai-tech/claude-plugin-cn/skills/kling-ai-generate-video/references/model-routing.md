# Video entry points and model selection

First follow [capability discovery](../../kling-ai/references/capability-discovery.md). A discovered tool is not proof that any particular model is enabled. Never route by tool count, a static model name, or an earlier account's capabilities.

| Complete live discovery | Routing |
| --- | --- |
| No `omni_ref_video` | Use `text_to_video`, `image_to_video`, or `motion_control` according to intent and available model capabilities. A new model returned on these tools remains eligible. |
| `omni_ref_video` exists | Query its models together with relevant existing video tools, even for pure-text requests. Prefer a compatible V4 model returned by the account, subject to the user's model and capability requirements. |
| No compatible V4 model is returned | If the user permits other models, select a compatible live default. If the user requires V4, stop and report that no eligible pair was returned; do not offer an excluded model. |
| Discovery failed or the requested model/capability is unavailable | Resolve the discovery failure or explain the current limitation. Do not silently use an older model, remove references, or generate to test availability. |

When the user leaves the model open, recommend Kling 4.0 for standard delivery when live discovery returns a compatible pair. Prefer Kling 4.0 Flash when speed or credit savings are prioritized and its live capabilities fit. User-specified available models take precedence. Match the full requested variant using the canonical names and aliases returned for the current account, and use the matched model's name in the recommendation. Use real billing information for budget choices. Do not raise resolution or output count merely because a 4.0 model is available.

## Kling 4.0 and Kling 4.0 Flash

Both variants support text-to-video. Use the current account's live model declarations to confirm the applicable limits, frame roles, and reference slots.

| Model | Image-to-video frame roles | Omni reference inputs | Output |
| --- | --- | --- | --- |
| Kling 4.0 | First, last, and intermediate keyframes | Images, videos, audio, and Elements | 3–30 seconds at 720p, with 1080p and 4K for eligible accounts |
| Kling 4.0 Flash | Single first frame | Images, videos, and Elements | 3–20 seconds at 720p |

The China MCP declares HDR output for `kling-video-v4_0` on `text_to_video`, `image_to_video`, and `omni_ref_video` at 1080p or 4K, subject to live account access. Kling 4.0 Flash currently offers 720p only. Apply the [HDR request rules](../../kling-ai/references/model-parameters.md#hdr-video-output) after selecting a compatible pair.

Both omni-reference variants support smart shot splitting, synchronized sound generation, and retention of source-video audio. Choose at most one of the two sound output options. A separate audio reference requires the selected model to declare an audio input slot.

## Intent and inputs

- Text-only video can use `omni_ref_video` only if the chosen model explicitly permits no media inputs; otherwise use a compatible `text_to_video` model. The word "reference" in the tool name does not make attachments mandatory.
- Image, video, Element, and audio references can use `omni_ref_video` only when the selected model supports each requested type and their combination. Do not treat its general tool description as every model's capability list.
- Keyframes belong to whichever discovered tool/model declares the needed frame inputs. Do not hardcode them to one entry point, invent intermediate frames, or substitute identity references for frame control.
- Motion transfer must use a model that explicitly supports that intent and all required inputs. Existing `motion_control` requests keep the subject image and exactly one motion source.
- Do not move an omni model to `image_to_video` or `text_to_video`; tool/model pairs and their parameter sets are inseparable.
- Required silence is an eligibility condition across these entry points. Exclude a pair without a declared off value or silent-output guarantee before ranking by model preference. An entry named text-to-video is not inherently silent; a compatible text-only omni entry remains eligible without attachments.

After selection, apply [model parameters](../../kling-ai/references/model-parameters.md), including conditional reference caps, Elements, and audio exclusivity. One multi-shot plan remains one task unless separate tasks were explicitly approved. The core Skill's billing, single-submission, and result rules apply to omni reference too.
