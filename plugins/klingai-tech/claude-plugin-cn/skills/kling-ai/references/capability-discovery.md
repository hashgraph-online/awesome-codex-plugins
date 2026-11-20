# Account-scoped capability discovery

Read this before choosing a model for generation or a model recommendation. Status, credit, and library queries do not need model discovery.

## Discover candidates

1. Read the current connection's complete `tools/list`, following all pagination. Only discovered tools are candidates. A failed discovery is not an empty list and must not trigger a fallback to old capabilities.
2. If the live `who_am_i` schema declares `tools`, pass a nonempty set of relevant generation tools; otherwise read the full response. Do not invent model or field filters. For V4 discovery, include all discovered generation tools that support the requested output type and intent.
3. Treat `who_am_i.availableModels` and each tool's `models` as the authority for this account. Match requested canonical names or declared aliases within that set. A tool's existence, examples, membership tier, or `defaultModel` alone does not establish model access; the default must also belong to its model set.
4. If a requested model is missing from the filtered response, check the remaining discovered generation tools before concluding it was not returned. A model available only for another output type is not a candidate for this request. Explain that mismatch without claiming an account permission failure or changing the requested media type.
5. Fix one tool/model pair, then read [model parameters](model-parameters.md). Never move a model or its arguments to a different tool.

## Video candidates

For text-driven video, query `text_to_video`; for image-driven video or keyframes, query `image_to_video`. When `omni_ref_video` exists, include it in the same capability query in both cases. For example, a pure-text request queries `["text_to_video", "omni_ref_video"]` when both exist and the filter is supported. Do not exclude omni reference because there are no attachments: the selected model's required inputs determine whether text-only generation is valid.

Host tool-name search must discover these candidates, not just the legacy entry point. Search results for `text_to_video` alone are not a complete tool inventory. Motion transfer must retain its subject-image and motion-source requirements. See [video model routing](../../kling-ai-generate-video/references/model-routing.md) before choosing a video model.

## Selection and visibility

- A user-specified available model takes precedence if it satisfies all required capabilities. Recommend V4 for video only when the user permits it and the current account returns an eligible tool/model pair. Match V4 or V4 Flash using live canonical names and declared aliases. Prefer full-quality V4 for normal delivery and V4 Flash when the user prioritizes drafts, speed, or credit savings, subject to live capabilities.
- If no compatible V4 model is returned and the user permits other models, choose a compatible live model, preferring the tool's available default. If the user requires V4, report the unmet requirement and stop. For images, follow the [image model selection rules](../../kling-ai-generate-image/SKILL.md#mode-rules).
- In user-facing recommendations, identify the selected model by its returned name. Do not describe it as "the latest model" or "最新模型", or recommend models absent from the current account response.
- Required references, duration, sound, speed, and budget take precedence over version preferences. Do not silently drop requirements, increase output count, or lower specifications to make a model fit.
- Reuse one successful discovery response during the same generation preparation. Refresh after reconnecting, switching account/endpoint, changed entitlements, a capability notification, or a rejected model/argument; query additional tools when the candidate set changes.
- A filtered response says nothing about unqueried tools. If full discovery still does not return a requested model, report only that the current connection did not return it. If the user says it is enabled, follow [capability troubleshooting](troubleshooting.md#model-capability-mismatch); do not guess a model identifier or probe access by generating.
- Model capability comes from `who_am_i`; request encoding comes from the tool's `inputSchema`. Tool examples cannot expand model capabilities. Refresh inconsistent or incomplete definitions; if no valid request satisfies both, stop before submission.
