---
name: troubleshoot
description: Diagnose and recover sync. labs (sync.so) work that failed, stalled, was rejected or errored, then resume it safely without paying twice. Covers sign-in and missing tools, rejected inputs, plan, credit and concurrency limits, stuck or slow jobs, lost responses after a timeout, dubbing provider errors and poor lipsync quality, and can report the problem to the sync. team. Use for "my lipsync failed", "why was this rejected", "it's been processing forever", "I got a 429 or 402", "the sync tools disappeared", or any sync. error message. Not for first-time setup (setup) or writing integration code (sync-api).
license: MIT
compatibility: Works best with the sync. MCP server connected. See references/connect.md.
---

# Troubleshoot sync. work

Finds out what actually happened, says it plainly, and resumes the work without starting a second paid job.

## 1. Gather the facts

Collect what's known before guessing: the tool or request that failed, the exact error text and code, and any generation, batch, project, asset or job ID. Then read the current state:

- A generation: `generations_get` with its `id`. Note `status`, `error` and `errorCode`.
- No ID: `generations_list` with a small `limit`, or `batches_list` for batches, to find it.
- The account: `account_get-context` for plan limits and concurrency, `account_get-usage` for credits.

Never ask for the user's API key or password, and don't paste signed media links into anything public.

## 2. Find the cause

| What you see | What it means | What to do |
| --- | --- | --- |
| Sign-in error, or the sync. tools are missing | The MCP connection is signed out, or the client hasn't loaded it | Reconnect with [references/connect.md](references/connect.md). Signing in in a browser tab doesn't sign in the agent's connection. A tool that's missing here may only exist in another client, such as Studio tools in ChatGPT. |
| `PENDING` or `PROCESSING` for a while | Normal for long or busy jobs. Dubbing and batches take longer than plain lipsync. | Keep polling the same ID. Pending isn't failed, and a second create won't make it faster. |
| A timeout or lost response after a create | The job may or may not have started | Look for it with `generations_list` (or `batches_list`), or retry the identical request with the same idempotency key, which returns the original if it exists. For a `jobs_create-many` set, send the identical call again with the same set `idempotencyKey` and items. Never switch to a new key to "recover". |
| `concurrency_limit_reached` | The plan's limit on simultaneous jobs is reached | Wait `error.retryAfterMs` (or for a running job to finish), then retry the same request. More creates won't clear it. |
| `insufficient_credits`, `free_tier_generations_exhausted`, `generation_plan_duration_exceeded`, `plan_feature_unavailable` | A plan or balance limit | Quote the message and point to https://sync.so/billing/subscription. Don't retry, and don't switch accounts to get around it. |
| A 4xx about the input (format, resolution, face, length, speaker) | sync. refused the media or settings | Explain which input and why, and fix only that. Don't quietly change the model, speaker, language or trim. [references/media-input.md](references/media-input.md) has the input checklist. |
| `import_in_progress` | A social-link import is still running | Wait `retryAfterMs`, then repeat the identical call. |
| `FAILED` with a voice-provider error during dubbing | Often the user's own ElevenLabs key, if they connected one to sync. | Check that key's credits and validity. Removing it from sync. falls back to sync.'s own. |
| `COMPLETED`, but the lipsync looks wrong | Usually the source: a turned or covered face, several faces, music under the voice, low resolution | Go through the input checklist. If an older model was used, suggest `sync-3`. A new attempt is a new paid generation, so quote it first. |
| The result is there but the link or download failed | The output exists | Recover the link with `generations_get`. Don't generate again. |

Failed generations aren't charged.

## 3. Resume

Say what the cause was, what you did, and what happens next. Resume the original workflow from where it stopped, reusing the same project, assets and keys. Leave anything you couldn't confirm as unknown, and don't promise a finish time you can't back up.

## 4. Report it

If `feedback_send` is available and the problem was a confusing error, a bug, a missing capability or a workaround, send one report per problem after you've dealt with it. Use the matching `kind`, a short `message` with the exact error text and what would have helped, and the `tool`, `errorCode` and `generationId` or `jobId` when known. Leave out secrets, signed links, personal data and the user's media. The report doesn't retry or fix the job.
