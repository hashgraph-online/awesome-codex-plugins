# Narration timing and reusable assembly

Read this for multi-scene explainers, localization or tight duration targets.

1. Divide narration at complete ideas, not arbitrary character counts. Keep each TTS request within the live limit. Reuse the same voice and record its exact selection.
2. Measure each returned file. Include intended pauses and a short final tail; a requested duration is not evidence of actual speech duration.
3. Map each beat to its visual and source. Keep this in the existing script or timeline, not a separate synchronized state system.
4. For a clip shorter than the beat, choose a supported longer generation, an intentional still hold, a relevant cutaway or locally composed motion. Do not stretch a face/lip-sync clip or slow speech unpredictably to fill a slot.
5. For narration that exceeds a hard limit, first shorten the wording without losing the claim. Regenerate only that audio segment within budget. Do not cut the last word or accelerate the entire narration until it barely fits.
6. Assemble using the available editor/compositor. Match frame rate, dimensions, audio sample rate and pixel format; verify the exported file rather than relying on timeline settings.

Use restrained transitions with consistent durations. Account for overlap when calculating final length. Avoid changing an accepted identity because a transition made the composition inconvenient.

Captions must match the spoken audio, including numbers and names. A script-derived caption is only a draft until its wording and timing have been checked against the recording. Keep captions as editable SRT/VTT when requested; a burned-in export alone makes localization unnecessarily expensive.

For localization, adapt meaning and on-screen layout together. Translated speech rarely has the same duration. Re-measure it, retime the existing visual sequence and inspect text expansion before generating replacement visuals. Keep original narration and an uncaptioned master.

For source-based explainers, link each substantive claim to the supplied document or verified source. Do not narrate uncertain claims as established facts or depict an illustrative simulation as real footage. A source credit at the end does not repair an unsupported claim in the middle.
