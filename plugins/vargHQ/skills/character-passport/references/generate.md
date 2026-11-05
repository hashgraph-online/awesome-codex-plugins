# Generating the cast and using it in shots

A chain of approved stills: passport → sheet → expressions and prop sheet → one still per shot → video from the
approved still. Nothing moves before its still is approved. Prices are varg prices on 2026-11-03; quote dollars
first, credits in brackets.

| Step | Model | Price | Why |
| --- | --- | --- | --- |
| Sheets, expressions, prop sheet | `nano_banana_2_1` (≤10 reference images) | $0.05 (5 credits) | Holds identity across panels and edits; cheapest. All 22 test images: $1.10 |
| Photoreal hero face | `seedream_5_pro` | ~$0.07 | Best skin texture in earlier varg tests |
| Labelled sheet for a client | `gpt_image_2_5` | ~$0.24 | Clean text; keep a text-free twin for models |
| Sheets and shots, ChatGPT users | `gpt_image_2_6` with `image_size` set, sheet as Image 1 | $0.06-0.07 | Face 0.72 vs 0.66 for Nano Banana with the sheet; ages faces, invents signs, mirrors side details: [gpt-image.md](gpt-image.md) |
| Shot stills | `nano_banana_2_1`, sheet as Image 1 | $0.05 | 8 of 8 shots kept the face, no grid leak |
| Voice test lines | `gemini_3_8_flash_tts` with the voice line as `style_instructions` | $0.01 a take | Accent, pace and habit written in words; measured with `voice_check.py` |
| Voice, final | `eleven_v4` with a chosen voice id + audio tags (`[sighs]`, `[whispers]`) | ~$0.008 per character | Most expressive; voice names can 404 on v4, raw ElevenLabs voice ids work |
| Video from an approved still | `kling_v4` image-to-video | ~$0.83 per 5 s at 720p | Most faithful to the start frame |
| Video from references | `seedance_2_5`, face close-up `@image1` + full-body front `@image2` | ~$2 per 5 s with audio | Steadiest face when no start frame fits |
| 20+ shots, a mascot | `minimax_h3_lora` or Higgsfield Soul ID | training cost | References stop holding over long series |

Per-model reference fields, route pinning, exclusion lines and drift fixes: varg-character-design
`references/downstream.md`. Per-shot prompting: varg-video-prompting.

## Reference order in a shot prompt

1. Name each image's job first: "Image 1 is Vesna's sheet: identity only. Image 2 is the umbrella sheet: the object
   only. Image 3 is the bus-stop master: the location only."
2. Add a winner rule: "Where Image 3 and Image 1 differ in light or setting, Image 3 wins; Image 1 only defines the
   person."
3. Then the shot, the passport, the prop passports and the look block (`scripts/prompt.py build`).
4. Video models get panels, not the board: `scripts/crop_sheet.py`. A small face inside a busy sheet is what video
   models drift towards.

## Image-to-video prompts

The start frame already carries the look and the costume. Write only what changes: the cause, the action in
seconds, the tells, the camera. Put the prop's ```motion block in when the prop moves (`prompt.py --video`). One
camera move, one action per shot. See `acting.md` for the acting line.

## Voice before picture

Generate and approve the voice before any talking shot, then lip-sync to it or pass it as an audio reference.
Seedance 2.5 re-voices an `@audio1` line in a similar voice with its own timing (varg run, 2026-10-15); if the
exact take matters, mute the model's audio and retime the clip to the approved track.

## Takes

Make 2-4 takes per shot and pick with the passport checklist (each detail visible and right / wrong / not in
frame), not by taste. Re-anchor every shot on the original sheet; never chain from a drifted shot.
