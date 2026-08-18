# Successor Pack Input

Use this only after the user explicitly requests a task handoff or successor
pack. Create `.codex/context-guard/SUCCESSOR_INPUT.json` in the current project:

```json
{
  "schema_version": 1,
  "current_status": "One bounded sentence describing verified current state.",
  "exact_next_action": "One bounded action for the successor.",
  "authorization": {
    "granted": [
      {"text": "Existing permission only.", "source_ids": ["R001"]}
    ],
    "consumed": [
      {"text": "Already used permission or completed external effect.", "source_ids": ["E0001"]}
    ],
    "pending": [],
    "forbidden": [
      {"text": "Existing prohibition only.", "source_ids": ["R001"]}
    ]
  },
  "current_step_reads": [
    {
      "path": "relative/path.py",
      "purpose": "Why the successor needs this body.",
      "read_mode": "lines",
      "line_ranges": [[10, 40]]
    }
  ],
  "audit_only_files": [
    {
      "path": "relative/history.log",
      "purpose": "Historical evidence whose body is not needed normally."
    }
  ]
}
```

Rules:

- Use project-relative regular files only.
- Bind each authorization entry to existing requirement, acceptance, or
  successful evidence IDs. The index is descriptive and grants no new
  permission.
- Put only the files needed for the next step in `current_step_reads`. Use
  `audit_only_files` for historical evidence whose hash is sufficient.
- Do not put secrets, raw customer data, transcript bodies, or private plugin
  paths in the input.
- Run `context-guard rollover` only after saving and checking the input. The
  Hook writes a new directory and refuses to overwrite an existing pack.
- Do not create a successor task until the user separately authorizes it.
