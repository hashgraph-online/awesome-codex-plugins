---
name: batch-lipsync
description: Lip-sync many videos at once with sync. labs (sync.so), from a CSV, spreadsheet, folder or list. Pairs each video or avatar with its own audio or script, quotes the whole run once, starts the rows together within the plan's concurrency limit, resumes safely without paying twice, and collects every output. Use for bulk or batch lipsync of supplied audio or scripts, personalized video at scale (one video per lead, customer or recipient name), ad and creative variants, many voiceovers onto one presenter, or any "do this for each row" lipsync job. Not for one video (lipsync), translating videos into other languages (translate-and-dub for one video, localize-campaign for several).
license: MIT
compatibility: Needs the sync. MCP server or a SYNC_API_KEY. The bundled script needs a SYNC_API_KEY and Python 3.9+.
---

# Lipsync many videos

[sync. labs](https://sync.so) | [Batch lipsync guide](https://sync.so/docs/plugins-and-extensions/agent-skills/batch-lipsync)

Delivers one MP4 per row of the user's list, plus a results table that maps each row to its output.

If no sync. tools are available and there's no `SYNC_API_KEY`, follow [references/connect.md](references/connect.md) first.

## 1. Build the manifest

Turn whatever the user gave you (a CSV, a spreadsheet, a folder of files, "this video with each of these 30 audio files") into a CSV in the working directory, one row per output video:

| Column | Meaning |
| --- | --- |
| `id` | A unique, stable row name, such as `lead-042` or `es-ad1`. It names the output and keys retries. |
| `video` | A local path, `https://` URL or sync. asset ID. Use `image` instead for a still picture (sync-3). |
| `audio` | A local path, URL or asset ID. Leave it empty when the row uses `script`. |
| `script`, `voice_id` | The words and a voice from `voices_list` (or `GET /v2/voices`), when there's no audio. |
| `sync_mode` | Optional: `bounce`, `loop`, `cut_off`, `silence` or `remap`. |

Show the user the row count and a few sample rows, and fix gaps before spending anything: missing files, rows with neither audio nor script, duplicate IDs. Columns the run doesn't use stay local. Scripts, media, file names and the row IDs (used as output names) are sent to sync., so use plain row IDs like `lead-042` rather than names or emails.

## 2. Quote the whole run

Sum one estimate per row: `generations_estimate-cost` with `model: "sync-3"` and each row's `audioDuration` or `script` (plus `videoDuration` and `syncMode` for `cut_off` or `silence`), or `python3 scripts/sync_batch.py estimate manifest.csv`. Show the total, the row count and the most expensive rows, and wait for approval of the total. That one approval covers every row: don't ask again per row or per chunk. Script rows are approximate and exclude speech synthesis. If some rows can't be priced, show the known subtotal and which rows are missing; don't present it as the total.

Offer a **pilot**: run the first one or two rows, let the user check them, then run the rest. A mistake in a shared input, such as a wrong voice or a badly framed avatar, then costs two generations instead of two hundred.

## 3. Run it

Pick the route, in this order of preference:

- **The bundled script (preferred with a `SYNC_API_KEY` and a shell).** `python3 scripts/sync_batch.py run manifest.csv --out ./lipsync-out` uploads each local file once, creates one generation per row with a stable idempotency key, keeps to the plan's concurrency limit, waits, and downloads each result. Re-running the same command resumes: finished rows are skipped, submitted rows are polled instead of resubmitted, and a row whose inputs changed after submission is refused until it gets a new ID. Progress and output URLs are saved to `manifest.csv.state.json` and `results.csv`.
- **MCP `jobs_create-many`, for any run of 2 or more rows, when the tool is listed.** It starts every row through the same API path, plan limits and billing as one `lipsync_create` per row, keeps within the plan's concurrency, and waits out busy refusals for you.
  1. Make one item per row: exactly the arguments `lipsync_create` takes for that row (`videoUrl` or `videoAssetId`, `audioUrl` or `audioAssetId`, or `script` and `voiceId`, `model: "sync-3"`, and `options.sync_mode` when set), plus the row's own `idempotencyKey`, `<run-name>-<row id>`. To keep the run in one project, call `projects_create` once and pass its `projectId` with `projectIntent: "explicit"` in every item. Otherwise each item gets a new project.
  2. Write a new UUID for the set into the manifest, then call `jobs_create-many` with `tool: "lipsync_create"`, that UUID as `idempotencyKey`, and the items. Send at most 50 items per call, each chunk with its own saved set key. After an unclear response, send the identical call again: the keys make that safe.
  3. Each item comes back started, failed or not started. Record each started row's job `id` in the manifest. Pass the returned `jobs` to `jobs_get-many` (up to 50 per call) with `wait: true`, call it again while some are still running, and record each row's `outputMediaUrl` from its `result`.
  4. When the response has `remaining`, the account stayed at its limit. Once `jobs_get-many` shows jobs finishing, send `remaining` again exactly as returned (the same tool, set key and items) until every row has started. If the tool refuses a single remaining item, send that row with `lipsync_create` and the same `idempotencyKey`.
  5. A failed item with a 5xx or no status may still have started: send it again with the same keys. Fix any other failed row before sending it again.
- **MCP tools, one generation per row**, when `jobs_create-many` isn't listed, or for a one-row pilot. Call `account_get-context` and read `generationLimits.concurrency`. Keep that many `lipsync_create` calls in flight at most, each with its own `idempotencyKey` (use `<run-name>-<row id>`, saved in the manifest before the call) and a new `projectCreationKey`, or one shared project from `projects_create`. On `concurrency_limit_reached`, wait `error.retryAfterMs` milliseconds and retry the identical request with the same key. Poll each with `generations_get` and record the `outputMediaUrl` in the manifest as you go.

## 4. Deliver

Report how many rows completed and failed, list each failure with its reason, and give the results table (`id`, status, output URL or local file). Offer to retry only the failed rows. Rows that failed on bad input need a fixed input, not a retry.

## Rules

- One paid generation per row. Poll saved generation IDs for progress, and start another attempt only after a confirmed failure and the user's OK to retry.
- Keep each row's idempotency key stable across retries and reruns, and never derive it from the time or a random value created inside a retry loop.
- Assume the user has the rights to their own media, and don't ask about consent on routine requests. Decline only when the request is to make a real, identifiable person, such as a politician or celebrity, appear to say something they didn't say, in order to deceive.
- For one recording personalized with each recipient's name in the presenter's own voice, make one dialogue-edit preview per recipient with the edit-dialogue skill, then render every approved preview with `jobs_create-many` and `tool: "dialogue-videos_create"`, on any paid plan.
