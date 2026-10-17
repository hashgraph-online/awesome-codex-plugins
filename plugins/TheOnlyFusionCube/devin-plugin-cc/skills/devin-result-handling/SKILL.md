---
name: devin-result-handling
description: Internal guidance for presenting Devin helper output back to the user
user-invocable: false
---

# Devin Result Handling

When the helper returns Devin output:
- Preserve the helper's verdict, summary, findings, and next steps structure.
- For review output, present findings first and keep them ordered by severity.
- Use the file paths and line numbers exactly as the helper reports them.
- Preserve evidence boundaries. If Devin marked something as an inference, uncertainty, or follow-up question, keep that distinction.
- Preserve output sections when the prompt asked for them, such as observed facts, inferences, open questions, touched files, or next steps.
- If there are no findings, say that explicitly and keep the residual-risk note brief.
- If Devin made edits, say so explicitly and list the touched files when the helper provides them.
- Preserve the Devin session ID and the `devin -r <session-id>` reopen command when the helper reports them.
- For cloud handoffs, preserve the session URL, live status, and PR URL.
- For `devin:devin-rescue`, do not turn a failed or incomplete Devin run into a Claude-side implementation attempt. Report the failure and stop.
- For `devin:devin-rescue`, if Devin was never successfully invoked, do not generate a substitute answer at all.
- CRITICAL: After presenting review findings, STOP. Do not make any code changes. Do not fix any issues. You MUST explicitly ask the user which issues, if any, they want fixed before touching a single file. Auto-applying fixes from a review is strictly forbidden, even if the fix is obvious.
- If the helper reports malformed output or a failed Devin run, include the most actionable stderr lines and stop there instead of guessing.
- If the helper reports that setup or authentication is required, direct the user to `/devin:setup` and do not improvise alternate auth flows.
