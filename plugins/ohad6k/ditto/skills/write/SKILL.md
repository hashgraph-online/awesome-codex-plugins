---
name: write
description: Use for marketing, social, replies, product copy, launch copy, and writing in the user's voice when their Emulo writing profile should guide the task. Do not use for unrelated execution or UI/UX design alone.
---

# Emulo write

1. Locate `emulo.py` two directories above this skill; fall back to `./emulo.py` only for a direct repo checkout.
2. Store the resolved absolute runtime path as `EMULO_PY`, then run `python "$EMULO_PY" plugin profile-path --domain write`.
3. If it exits nonzero, give its exact recovery or targeted-deepen instruction and stop loading personal context.
4. Read every returned path completely. The first is the core working profile; the second is the writing profile. Apply both.
5. Pick the register from context; never ask. A writing profile with register sections (`## Voice laws`, `## Casual register`, `## Professional register`) loads voice laws always, plus exactly one register:
   - An explicit audience statement from the user ("for my boss", "make it formal") always wins.
   - Otherwise infer from what is in the task: a pasted thread with a manager, client, or customer, a formal email, documentation, or official product copy selects professional; a community reply, social post, chat banter, or a builder-to-builder thread selects casual; a pasted conversation selects the register matching that thread's own audience and tone.
   - State the pick in one short line ("using professional register") so it is correctable, then write; never block on register confirmation.
   - If the picked register has no section in the profile, load the voice laws only and never substitute the other register; say so in the same line ("professional register not mined yet, using voice laws only") and suggest `run emulo and deepen write` to mine it.
   - A flat profile without register sections applies in full, unchanged.
6. Never imitate a generic voice when the writing domain is inactive.
