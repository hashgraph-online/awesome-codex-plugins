---
name: sw-learner
description: Reconstruct a complete consent-ready FeedbackSubmission from the entire current SolidWorks task, including corrected build instructions, every final code artifact, reproducible errors and fixes, lessons, and eligible images. Use throughout SolidWorks work for tracking and invoke at the end through sw-session-reporter; do not use for non-SolidWorks conversations.
---

# SolidWorks Learner

Track the session from the first SolidWorks message. When invoked, reread the
entire Codex task and rebuild the complete current payload, not a delta. Keep
only corrected final versions.

Never show the raw payload, base64 images, or full submission JSON to the user.

## 1. Confirm relevance and session

If no SolidWorks modeling, API calls, CAD code, design decisions, or debugging
occurred, return an internal skip result and stop.

Read `.sw-learner-state.json` in the CAD working directory and require a
non-empty fixed `sessionId`. If it is missing, resolve the plugin root and run
`scripts/sw_session.py start` once, then keep that UUID for the rest of the
task.

## 2. Resolve the part

Use quoted `curl` and the configured `SW_KB_HOST` default to query:

```text
GET /api/parts?q={encoded-part-identifier}&pageSize=20
```

Record the best exact or close `partId`; use `null` when none exists. Preserve
the known `partNumber`.

## 3. Collect eligible images

Find images referenced by generated code (`SaveBMP`, `ExportBMP`, `SaveAs`, or
paths ending in `.png`, `.jpg`, `.jpeg`, `.bmp`, `.tiff`, `.tif`, `.gif`) and
images actually shown in the task. Include only existing readable files under
10 MB. Deduplicate by filename and encode bytes as base64.

Use MIME types `image/png`, `image/jpeg`, `image/bmp`, `image/tiff`, or
`image/gif`. Convert Windows paths to accessible host paths when working through
WSL.

## 4. Build FeedbackSubmission

Follow `../../schemas/feedback-submission.schema.json`. Always include:

- `issues`: a two-to-five sentence narrative of what was built, the approach,
  mistakes fixed, validation, and final state;
- `sessionId`: the fixed ID for this Codex task;
- `partId`: the matched UUID or `null` when useful.

Add arrays only when they contain at least one item. Omit empty arrays entirely.

### Instructions

Include exact ordered build steps with the SolidWorks version, material, final
feature order, real parameter values, API calls, validation, and exports. Skip
generic steps that add no reusable knowledge.

### Macros

Include every code artifact written in the task: Python, VBA, or SWAPI. Store
the full verbatim final working source, never a summary or truncated excerpt.
Required macro fields are `name`, `language`, and `code`. Add description,
`swFeaturesUsed`, parameters, template flag, version, and part ID when known.

### Known errors

Include only concrete failures with the exact return value or error, affected
SolidWorks method, and a resolution that actually worked. Exclude typos,
immediately-fixed syntax mistakes, vague symptoms, and non-SolidWorks issues.

Use severity `critical` for total failure, `high` for plausible but wrong
output, `medium` for a caught and repaired failure, and `low` for minor
inconvenience.

### Lessons

Include non-obvious lessons demonstrated in this task, from successes and
failures. Every lesson needs `category`, `title`, `whatHappened`, `rootCause`,
`prevention`, and `severity`. Make `prevention` a concrete rule, never merely
`be careful`.

## 5. Validate and persist privately

Write the payload to `.sw-feedback-payload.json` in the CAD working directory
only when persistence is needed across the consent turn. Ensure it is ignored
by version control. Validate it with:

```text
python <plugin-root>/scripts/validate_feedback.py .sw-feedback-payload.json
python <plugin-root>/scripts/sw_session.py mark-payload --part-id <uuid-or-null> --part-number <value>
```

Increment `payloadVersion` on every rebuild. Replace earlier payload content;
do not accumulate stale or broken code versions.
