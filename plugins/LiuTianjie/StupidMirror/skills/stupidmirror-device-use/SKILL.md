---
name: stupidmirror-device-use
description: Observe and operate real iPhone or Android devices using StupidMirror tools, including reading screens, app navigation, taps, swipes, text entry and real-device UI checks. Use when the user asks to operate a connected phone; connection setup uses stupidmirror-setup.
---

# Operate a device through StupidMirror

Use the StupidMirror MCP tools. Start with `list_devices`; select the intended device and consistently pass `device_id` when multiple devices exist. Call `show_screen` to display the live device inside Codex, then `connect_control` if actions are needed. The app captures in the background. Do not call `start_mirror` unless the user explicitly wants a separate Mac mirror window.

- When the intended target is known, call `tap_text` directly with candidate labels in `queries`; avoid a separate read/find/tap chain. Use `find_any_element` when you need to inspect or disambiguate a target before tapping. These share one local OCR pass and at most one native hierarchy fallback; do not query synonyms separately.
- `observe_screen` defaults to an image plus compact OCR, without a native hierarchy. Keep the image for visual tasks or when the needed information is unclear; for clearly text-only reads, explicitly set `include_image=false`. `observe_screen`, `find_element` and `find_any_element` default to `response_format="compact"`. Keep that format for routine work; do not request full output and then filter it in model context.
- Compact elements retain `id`, text and `source`; `center: [x, y]` is a rounded normalized hint for distinguishing repeated labels. Native elements also retain type and available state flags/values. Use the element `id` and observation `id` (or search `observationID`) as `element_id` and `observation_id` for `tap_element`: it uses the stored full-precision geometry. Reobserve after navigation; do not reuse stale ids or treat OCR text as proof of clickability or toggle state.
- To verify an expected text, use `assert_screen` or a bounded `wait_for` instead of reading the whole screen. A successful tap alone does not prove the destination appeared.
- Request `include_accessibility=true, include_ocr=false` for native switch values, selection, enabled state or semantics absent from OCR. Do not fetch a native tree on every read. Use `response_format="full"` only when raw bounds, confidence precision or parent/child hierarchy are needed for diagnostics; it does not itself enable images or accessibility.
- Keep `include_image=true` (the default) for unlabeled icons, images, maps, canvas content, layout checks or unresolved ambiguity. Inspect the fresh image before coordinate input. If only the image is needed, also pass `include_ocr=false`. Do not take a screenshot automatically after every action.
- Once a field is focused, call `replace_text` to overwrite, `clear_text` to empty, or `type_text` to append. Do not fetch an accessibility tree between focus and input: an iOS snapshot can disturb focus. Verify the resulting text before submission.
- `highlight_elements` and `highlight_clickable_elements` annotate a separately opened Mac mirror without tapping the phone; these native overlays are not currently drawn in the embedded preview.

If an action loses its connection or times out, it may already have executed. Read the current state before deciding what to do next; do not blindly repeat clicks, text entry or submission. Use diagnostics for persistent failures and reuse the app's device connection.

Only carry out the user's requested actions. Drafting text does not authorize sending it, making a purchase or publishing content. Leave authentication secrets and biometric prompts to the user.

When the user sends a screenshot annotation, use its device ID and note. The attached image and numbered regions describe a frozen frame; observe the live device again before an action, and confirm the intended target still matches. Do not blindly replay the stored coordinates. Preview uses WebRTC independently of AI tool calls. `screen_signal`, `screen_frame` and `screen_action` are app-only transport/UI tools.
