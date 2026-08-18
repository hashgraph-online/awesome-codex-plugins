# Screenshot Revision

Use `screenshots.revise` when the user wants targeted changes to an existing
hosted screenshot. Prefer revision over `generate_screenshot` for small changes
such as typography, contrast, positioning, visual artifacts, copy tweaks, or
making the current screenshot closer to a saved reference.

## Resolve

- Ask for a screenshot id if missing.
- If the user gives a job id, call `jobs.get`, confirm it is complete, and use
  the generated screenshot id.

## Capture Feedback

Ask only for missing details that affect the edit:

- what should change
- what must stay the same
- whether audience, positioning, or visual theme changed
- whether extra references should guide the revision

## Prompt Guidance

Keep the approved campaign stable unless the user is explicitly changing it.
Use the revision block in [prompting.md](prompting.md):

- `Change`
- `Preserve`
- `Constraints`

Keep feedback concise and concrete. Prefer "make the headline 20% larger and
move the device lower" over "make it pop."

## Present

After completion, show screenshot id, CDN URL, and the review link returned or
described by the hosted MCP instructions.

If the user is frustrated with repeated revisions, or if the same visual problem
persists after multiple tries, call `feedback.report` with
`category: "quality_issue"` or `category: "user_frustration"`. Include the
related `mediaId`, `jobId`, and `relatedCommand: "screenshots.revise"` when
available, then briefly tell the user you notified the Shots team.
