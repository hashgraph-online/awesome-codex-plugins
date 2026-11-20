---
name: pw-doctor
description: Diagnose the Prewalk installation, presets, hook manifest, state directory, and Codex model-routing capability.
---

# Prewalk Doctor

Inspect the live `spawn_agent` schema, then pass exactly the fields it exposes:

Use the absolute helper path resolved from this installed skill, with the shell
working directory set to the user's project. On Windows use `python`.
Pass the actual session ID; do not change directories to the plugin.

```text
python <absolute-plugin-path>/hooks/_arm.py doctor <session-id> --schema-fields=<comma-separated live field names>
```

Omit absent fields and do not call the tool. A missing model argument means
spawn handoff cannot honor presets with
`require_model_routing=true`; recommend the manual model + `pw-resume` fallback.
Also report a missing or mismatched `CODEX_THREAD_ID`. Native session binding
requires Codex CLI 0.146.0 or newer; after upgrading, restart the Codex thread.

Schema support proves request fields, not lifecycle delivery. For an existing
pending collaboration route, `_pw.py observe <session_id>` checks the runtime's
read-only parent/child journal evidence without spawning or accepting a manual
completion claim. Missing journals or ambiguous identities retain the route.
