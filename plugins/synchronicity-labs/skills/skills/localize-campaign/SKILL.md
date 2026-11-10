---
name: localize-campaign
description: Localize a whole video campaign into several languages and markets with sync. labs (sync.so). Plans the video × language matrix, maps markets to languages, pilots one video so names and terms are right before spending on the rest, dubs and lip-syncs every version, and delivers consistently named files plus a review sheet per market. Use for several source videos across languages or markets, such as "make these ads in Spanish, German and Japanese", launching a campaign or a course in new markets, international or multi-market rollouts. Not for one video into a few languages (translate-and-dub), new speech in the same language (lipsync, batch-lipsync), or subtitles only.
license: MIT
compatibility: Needs the sync. MCP server or a SYNC_API_KEY. See references/connect.md.
---

# Localize a campaign

[sync. labs](https://sync.so) | [Campaign localization guide](https://sync.so/docs/plugins-and-extensions/agent-skills/localize-campaign)

Delivers every video in every target language as a dubbed, lip-synced MP4 with a predictable name, plus a sheet the regional teams can review from.

If no sync. tools are available, follow [references/connect.md](references/connect.md) first. Without the MCP tools, each version is one `POST /v2/generate` with `dubParams`, as in [references/api.md](references/api.md).

## 1. Plan the matrix

1. **Videos.** List each source video with its name, length and where it comes from (a file, URL or social link).
2. **Markets to languages.** Turn markets into languages and confirm them with the user. Germany, Austria and Switzerland are all German; Brazil is Portuguese; most of LATAM is Spanish. Call `dubbing_get-options` and check that every language is supported, naming the closest option for any that isn't. Don't guess regional variants the options don't list.
3. **The matrix.** Show it as a table: one row per video, one column per language, and the total number of versions.
4. **Files.** Agree a naming pattern up front, by default `<campaign>_<video>_<lang>.mp4`, for example `spring24_hero-30s_de.mp4`.

## 2. Check what dubbing won't change

Before spending anything, tell the user what stays the same, so nobody is surprised in review:

- Text on screen, burned-in captions, logos and end cards stay in the source language.
- Music and sound effects carry over. Very loud music under the voice can lower the dub's quality.
- Brand names, product names and slogans can be translated or mispronounced. Ask which must stay untranslated.
- The lips can only be matched where a speaker is on screen. Voiceover-only shots still get the dubbed audio.

## 3. Quote, then pilot

1. **Project and inputs.** Call `projects_create` once for the campaign, with a new UUID `id`, the campaign name and `defaultWorkflow: "translate_and_dub"`. Save the returned `id` as `projectId`. Pass it wherever a tool asks for `projectId`, and add `projectIntent: "explicit"` only on tools that take that field. Save each source video into it once, as in [references/media-input.md](references/media-input.md).
2. **Quote.** Call `generations_estimate-cost` with `workflow: "translate-and-dub"`, `model: "sync-3"` and each video's length as `duration`. Multiply by the number of languages, and show the per-video, per-language and total cost, using the returned breakdown. If it reports external provider charges as excluded, say they're extra. Wait for approval of the total.
3. **Pilot.** Run one version first, usually the most important video in the most important language. Use `dubbing_create` with `videoAssetId`, `targetLang`, `sourceLang: "auto"`, `model: "sync-3"`, the `projectId` with `projectIntent: "explicit"`, and a new `idempotencyKey`. Wait for it with `generations_get` and `wait: true`. Ask the user, or a speaker of that language, to check names, terms and tone. Fix anything you can before the rest.

## 4. Run the rest

- Give every version its own `idempotencyKey`, written into the matrix before any call, such as `<campaign>-<video>-<lang>`, and reuse it on every retry. Track each version's generation `id` and status in the matrix as you go, so an interrupted run resumes instead of paying twice.
- **With `jobs_create-many` listed (any paid plan).** The approved total already covers them, so start the remaining versions together without asking again: one item per version, each exactly the `dubbing_create` arguments the pilot used (`videoAssetId`, `targetLang`, `sourceLang`, `model`, the `projectId` with `projectIntent: "explicit"`) plus that version's `idempotencyKey`. Save a new UUID for the set in the matrix, then call `jobs_create-many` with `tool: "dubbing_create"`, that UUID as `idempotencyKey` and the items, at most 50 per call. Record each started version's `id`, then follow them with `jobs_get-many` and `wait: true`, calling again while some are still running. When the response has `remaining`, send it again exactly as returned once running versions finish; if the tool refuses a single remaining item, send that version with `dubbing_create` and the same key. A failed item with a 5xx or no status may still have started, so send it again with the same keys; fix any other failed version first.
- **Without it,** read `generationLimits.concurrency` from `account_get-context` and keep that many `dubbing_create` calls in flight at most. On `concurrency_limit_reached`, wait `error.retryAfterMs` milliseconds and retry the identical request with the same key.
- If one version fails, record why and carry on with the others.

## 5. Deliver

- Give a results table: video, language, status, and the exact `outputMediaUrl`.
- In a coding agent, download each file into `./<campaign>/<lang>/` using the agreed names.
- Write `review.csv` with one row per version: file, language, the market it's for, status, and empty `approved` and `notes` columns for the regional reviewers.
- Offer to redo only the versions reviewers reject. Never resubmit a version just to check progress.
