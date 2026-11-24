---
case: note-N4
description: Use when the user has chosen between options that matter later (an architecture, a library), and the decision and its reasons should outlive the chat.
---

# Recording the decision

Shapes: note.

```sh
stickypane answers cache-way
stickypane note write adr-cache --open <<'EOF'
---
title: Decision: versioned cache keys
---
**Context.** Prices must be fresh within a minute of an edit.
**Options.** Delete the key on write; bump a version in the key.
**Decided.** Bump a version: chosen by the user in [[cache-way]].
**Because.** No slow first read; old keys expire on their own.
EOF
```

Write "Decided" only after the user chose, with a link to the form that
holds the answer. Until then the note lists the options and nothing else.

Done when: the decision names the user's answer and links the form.
