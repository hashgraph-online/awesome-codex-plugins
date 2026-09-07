---
name: cassette-model
description: Show or change the Cassette editing model and thinking level for the current media session. Invoke only when the user explicitly asks for the model picker, wants to inspect the current Cassette model, or requests a model/thinking change.
version: 1.0.0
license: MIT
metadata:
  tags: [cassette, model, thinking, mcp]
  category: media
---

# Cassette model picker

This is an explicit settings action. Never invoke it automatically during media ingestion or before
an edit. A fresh Cassette session already uses GPT-5.6 Luna with `xhigh` thinking.

1. Reuse the active Cassette `session_id` from the current conversation. If no Cassette media
   session exists yet, tell the user to add media first; do not invent an id or create an edit.
2. Call `cassette_config` with only `session_id` to read the current selection and static options.
3. If the invocation already names a valid model and/or thinking level, call `cassette_config` with
   those values and confirm the saved choice in one line.
4. Otherwise show the model and thinking choices as two compact numbered lists and wait for the
   user's selections. Then call `cassette_config` with the selected model label and thinking value.
5. Explain that the setting is scoped to this Cassette session and applies from the next edit turn.

Selectable models are GPT-5.6 Luna and GPT-5.4 Mini. Thinking values are `off`, `minimal`, `low`,
`medium`, `high`, and `xhigh` (display `xhigh` as “Extra High”).
