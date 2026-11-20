# Video entry points and model selection

First follow [capability discovery](../../kling-ai/references/capability-discovery.md). A discovered tool is not proof that any particular model is enabled. Never route by tool count, a static model name, or an earlier account's capabilities.

| Complete live discovery | Routing |
| --- | --- |
| No `omni_ref_video` | Use `text_to_video`, `image_to_video`, or `motion_control` according to intent and available model capabilities. A new model returned on these tools remains eligible. |
| `omni_ref_video` exists | Query its models together with relevant existing video tools, even for pure-text requests. When model choice is open, prefer a compatible Kling 4.0 Omni Reference pair returned by the account. |
| No compatible model in the Kling 4.0 family is returned | Select a compatible live default if the user allows other models. If the user requires a specific model, stop and report the unmet requirement. |
| Discovery failed or the requested model/capability is unavailable | Resolve the discovery failure or explain the current limitation. Do not silently use an older model, remove references, or generate to test availability. |

Match a named Kling 4.0 (V4) or Kling 4.0 Flash (V4 Flash) request to the full canonical name or declared alias in the current account response. The standard and Flash variants are distinct choices. When the user leaves the model open and prioritizes speed or credit savings, prefer a compatible Flash pair using live descriptions and billing information. Name the actual variant in the recommendation and keep the requested output settings.

## Intent and inputs

- Use the selected pair's live capabilities to confirm these model differences. Kling 4.0 image-to-video can use first, last, and intermediate keyframes. Kling 4.0 Flash image-to-video uses a single first frame. Kling 4.0 Omni Reference can combine images, videos, audio, and Elements. Flash Omni Reference can combine images, videos, and Elements. A separate audio reference requires a declared audio input slot. Generated sound and original sound retention use output controls.
- Text-only video can use `omni_ref_video` only if the chosen model explicitly permits no media inputs; otherwise use a compatible `text_to_video` model. The word "reference" in the tool name does not make attachments mandatory.
- Image, video, Element, and audio references can use `omni_ref_video` only when the selected model supports each requested type and their combination. Do not treat its general tool description as every model's capability list.
- Keyframes belong to whichever discovered tool/model declares the needed frame inputs. Do not hardcode them to one entry point, invent intermediate frames, or substitute identity references for frame control.
- Motion transfer must use a model that explicitly supports that intent and all required inputs. Existing `motion_control` requests keep the subject image and exactly one motion source.
- Do not move an omni model to `image_to_video` or `text_to_video`; tool/model pairs and their parameter sets are inseparable.
- Required HDR is an eligibility condition. For text-to-video, image-to-video, or omni reference, keep only live pairs that declare HDR at a compatible resolution and support the requested input roles. Apply the [HDR request rules](../../kling-ai/references/model-parameters.md#hdr-video-output) after selection.
- Required silence is an eligibility condition across these entry points. Exclude a pair without a declared off value or silent-output guarantee before ranking by model preference. An entry named text-to-video is not inherently silent; a compatible text-only omni entry remains eligible without attachments.

After selection, apply [model parameters](../../kling-ai/references/model-parameters.md), including conditional reference caps, Elements, and audio exclusivity. One multi-shot plan remains one task unless separate tasks were explicitly approved. The core Skill's billing, single-submission, and result rules apply to omni reference too.
