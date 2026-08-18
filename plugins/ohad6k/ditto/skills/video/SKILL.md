---
name: video
description: Use for video direction, motion and pacing, shot and scene planning, captions, voiceover, trailers, Shorts, and edit critique when the user's Emulo video taste should guide the task. Do not use for unrelated execution, backend work, UI/UX design, or marketing copy alone.
---

# Emulo video

1. Locate `emulo.py` two directories above this skill; fall back to `./emulo.py` only for a direct repo checkout.
2. Store the resolved absolute runtime path as `EMULO_PY`, then run `python "$EMULO_PY" plugin profile-path --domain video`.
3. If it exits nonzero, give its exact recovery or targeted-deepen instruction and stop loading personal context.
4. Read every returned path completely. The first is the core working profile; the second is the video profile. Apply both.
5. Never substitute a generic video or creative persona when the video domain is inactive.
