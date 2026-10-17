---
name: cassette-video-edit
description: Edit, trim, cut, caption, subtitle, reframe, combine, add background music to, or export video, audio, and image files through Cassette. Use this skill whenever the user asks to change, preview, or render a media file in the project — even if they never say "Cassette" or name a tool — for example "trim the intro off demo.mp4", "add subtitles to this clip", "make me a 30-second cut with music", "why is there dead air at the start". Drives the local Oh My Cassette stdio MCP tools in Codex or Claude as one multi-turn conversation with the Cassette agent, with per-turn timeline previews, guided questions, and rendering only on explicit export.
version: 2.1.0
license: MIT
metadata:
  tags: [cassette, video, codex, claude, hermes, opencode, mcp, media-editing]
  category: media
---

# Oh My Cassette local workflow

Cassette edits the media; you carry the messages. The `cassette` MCP server is a local stdio child
process that opens no port and talks directly to the separate Cassette backend. Do not start or
depend on the separate FastAPI web-demo server for this workflow — that is a different adapter.
This is the canonical workflow for every supported MCP host, including Codex, Claude Code, Hermes,
and OpenCode.

Two details live outside this file to keep it short. Read them when they apply:

- `references/auth.md` — any `auth_*` error, or the user is not signed in on this machine.
- `references/music.md` — any Jamendo/BGM request or `jamendo_*` error.
- `references/previews.md` — showing a timeline, contact sheet, or storyboard, and the plan-review
  pause.

## Courier doctrine

You are a courier between the user and the Cassette agent, not an editor or a brief writer.

- Pass the user's editing words to `cassette_run_job` as `message` VERBATIM. Never rewrite,
  optimize, summarize, translate, or expand them. The agent is the creative brain and it reads the
  session's uploaded media itself, so a "helpfully" rewritten instruction only throws away detail
  the user chose and the agent could have used.
- Relay the agent's questions and plans back verbatim too. You add exactly three things: the
  timeline delta, the version numbers, and any validated artifact path.
- Do not call `cassette_make_prompt`. It is a legacy brief builder, kept only so the tool-name set
  stays stable.
- Do not interrupt an edit to ask about model selection, optimization, or BGM. A fresh session uses
  GPT-5.6 Luna with `xhigh` thinking. Open the model picker only when the user explicitly invokes
  the host's `cassette-model` command/skill or asks in natural language to view or change it.

## Safety and identity

- Only files inside the active host project roots or explicitly configured media roots are
  ingestible. On `source_path_not_allowed`, ask the user to move the file into the project or to
  rerun the private setup command with `--allowed-root`. Do not go hunting for a path that works.
- Keep the returned `session_id` and `job_id`. Sessions are isolated by default; hand one to
  another host only when the user deliberately asks for a Codex or Claude handoff.
- Use only paths and resource links returned in `artifacts`. Never invent an export path or ask the
  MCP runtime to expose another local file.

## The editing loop

One session is one continuous conversation on one persistent agent thread. The agent remembers
every previous turn, so a follow-up like "make that title bigger" needs no context restating.

1. Call `cassette_ingest_media` once per source asset. Omit `session_id` on the first call so the
   runtime generates one, then reuse the returned value everywhere.
2. Call `cassette_list_assets` and confirm the intended files are present.
3. Before the first edit, call `cassette_config(session_id)`. If its source is `default`, present
   the returned choices and save the user's selection (including an accepted default).
4. For each editing request, call `cassette_run_job` with the user's verbatim `message` and the same
   `session_id`.
5. Relay what comes back (see routing below), then wait for the user's next instruction.
6. Pass `export=true` only on a turn where the user expresses finish or export intent.

If the user explicitly asks for background music, `cassette_match_exact_bgm` takes a concrete
title/artist and `jamendo_music_matcher` handles a configured mood/genre. Never switch providers
automatically. `cassette_match_bgm` remains available only when the user explicitly asks for the
legacy Free To Use provider. Read `references/music.md` before handling music.

### One turn, end to end

```
User:  trim the dead air off the front of demo.mp4 and add a title card

You:   cassette_run_job(session_id="s_41k",
                        message="trim the dead air off the front of demo.mp4 and add a title card")
       → phase="succeeded"
         timeline_delta="v6→v9: trimmed 3.2s from head; added title card 0.0–2.5s"
         quality.timeline_ctl=<digest>, artifacts=[contact sheet]

       "v6→v9: trimmed 3.2s off the head and added a 2.5s title card. Nothing is rendered
        yet — want to see the contact sheet, or should I export?"

User:  export it

You:   cassette_run_job(session_id="s_41k", message="export it", export=true)
       → phase="review_required"
       cassette_review_completion(job_id="j_88", decision="export",
                                  reason="user asked to export; trim and title card both landed")
       → phase="exported", artifacts=[…/exports/j_88/demo_cut.mp4]
```

Note what did not happen: no status polling, no rewriting of the user's words, and no rendering
until the user asked for it.

## Routing on typed state

Treat the structured `phase` and `next_action` fields as authoritative. Do not decide routing,
progress, or completion from keywords in prose.

`cassette_run_job` **is** the wait. It returns when the turn is settled, streaming MCP progress
notifications when the host supports them, and answers with a terminal phase. Make exactly one
call per user turn, then return control to the user. Never start a second corrective, retry, or
"finish the plan" call until the user sends another message.

| phase | what it means | what you do |
|---|---|---|
| `succeeded` | edit committed, **nothing rendered** | relay `data.job.timeline_delta` + the digest, continue the conversation |
| `needs_user` | the agent asked a question | relay it, then `cassette_answer_question(job_id, response)` |
| `review_required` | export turn awaiting judgement | evaluate the result, then **in the same assistant turn** call `cassette_review_completion(job_id, decision, reason)` — only `decision=export` renders |
| `exported` | the render finished | present the validated `artifacts` and their resource links |
| `failed` / `cancelled` / `timed_out` | terminal error | report the structured error and its runtime-derived next action |
| `running` / `exporting` | the call detached (`wait=false`) or was interrupted | see recovery below |

### Where the per-turn data lives

The envelope itself is thin — `ok`, `phase`, `next_action`, `session_id`, `job_id`, `artifacts`,
`data`. Everything describing the turn hangs off `data.job`:

| what you want | where it is |
|---|---|
| what changed this turn | `data.job.timeline_delta` |
| the agent's plan checkpoints | `data.job.plan_progress` |
| the text digest of the timeline | `data.job.quality.timeline_ctl` |
| the contact sheet, when one exists | `data.job.quality.contact_sheet_uri` |
| measurements of the rendered file | `data.job.quality.export_qc` (on `exported` only) |
| resource links and export paths | `artifacts[]` — top level, **not** under `data` |

Reading `timeline_delta` or `quality` off the top of the envelope yields nothing at all, which
looks exactly like a turn that produced no preview. The digest is there on every settled turn; the
contact sheet is best-effort and is simply absent when a sheet could not be built from the current
frames, so check before offering to show one.

`cassette_timeline` answers in its own shape — `data.ctl` plus `data.version`, `data.clip_count`,
and `data.duration_sec` — not under `data.job`. Same digest, different path from the run envelope.

`cassette_review_completion` takes `reason` as a **required** argument alongside `job_id` and
`decision` (plus an optional `summary`) — omitting it fails the call with `validation_error`
before anything renders. Write the judgement you actually made, in one line: it is the record of
why this edit was considered finished, and it is the only place that judgement is captured.

On `exported`, the runtime has already measured the finished file into `quality.export_qc`
(duration, fps, resolution, audio span, `black_segments`, and `audio_levels` with
`mean_dbfs`/`peak_dbfs`). Read those numbers instead of probing the export yourself, and raise them
with the user only when a field contradicts what they asked for.

An explicit user export request is already authorization to export. If that export turn returns
`review_required`, inspect the attached timeline and resolve the gate in the same assistant turn.
Do **not** ask the user to confirm export again merely because the Cassette agent's prose says it
cannot render or lacks rendering capability: that prose is precisely why the typed supervisor
review gate exists. Ask only when the timeline reveals a real defect or the requested result is
genuinely ambiguous. Never start a second `cassette_run_job` to get past this gate.

A `thread_busy` error means a run is already live on this session's thread, often started from an
open editor tab. Wait and retry rather than starting a second job.

On hosts that support MCP elicitation, the runtime may collect a `needs_user` answer itself and
return the already-resumed result. Trust the returned phase and do not answer twice.

### Recovery, not polling

`cassette_job_status` re-attaches to a job whose call did not return — the host restarted, the call
was cancelled, or the turn was deliberately started with `wait=false`. Call it **once**, act on the
phase it reports, and stop. A settled turn never needs it.

`job_id` is the durable handle for that recovery: jobs persist private thread and interrupt
metadata on disk, so a paused turn resumes after a supported MCP host restarts.

A long edit does not need managing. Hosts that background long tool calls (Claude Code moves any
call past two minutes into a background task) keep the session usable while the turn runs and
deliver the result when it lands.

## Timeline grounding

- Every user-visible statement about project state comes from `cassette_timeline` or the envelope's
  `timeline_delta`, never from memory. Name the version: "v42→v43: trimmed the intro to 4.0s."
- Prefer relaying `timeline_delta` and `plan_progress` over re-describing the whole timeline.
- The runtime hands out no editor deep link, and you must not construct or offer one. That URL is a
  bearer capability: the backend binds no owner to a session, so any signed-in account that sees it
  can open the project and run edits on the thread. Previews go through the digest, the contact
  sheet, and the export instead.
- Route essentially everything through `cassette_run_job`. `cassette_edit` is an opt-in fast lane
  for small named changes (trim, retime, text, delete, undo) that stays **disabled unless the
  operator sets `CASSETTE_DIRECT_EDIT=1`** — no shipping host config sets it, so assume it is off
  and reach for it only once a `cassette_edit` call has actually succeeded in this session or the
  user says they enabled it. When you do use it, read `cassette_timeline` first and pass
  `expected_version` from that read; a `stale_timeline` error means re-read and retry.

## Model, thinking level, and updates

- `cassette_config(session_id)` shows the current choice and the available options; adding
  `model=…` / `thinking_level=…` changes them. It accepts a product id (`openai/gpt-5.6-luna`) or a
  label ("GPT-5.6 Luna").
- The selectable models are GPT-5.6 Luna and GPT-5.4 Mini. Thinking levels are `off`, `minimal`,
  `low`, `medium`, `high`, and `xhigh`. The default is GPT-5.6 Luna with `xhigh` thinking. The
  preference persists for the session and applies from the next turn, the same semantics as
  switching model between turns in the web editor. Never ask automatically; change it only when
  the user asks, and confirm in one line.
- The MCP `instructions` carry an `UPDATE AVAILABLE:` line when a newer Oh My Cassette release
  exists. Mention it once per session with both version numbers and offer the command it names. Run
  that command only after the user explicitly agrees, and never re-offer in the same session — it
  replaces the plugin on disk, so tell the user the new version applies after the host reloads
  (`/reload-plugins` in Claude Code, a new task in Codex). Never fabricate a version or an update
  command; if the line is absent, the install is current and the subject does not come up.

## Cancellation and handoff

- Call `cassette_cancel_job` only when the user asks to stop the edit.
- For a deliberate host handoff, provide the exact `session_id` and active `job_id`; the receiving
  host should begin with `cassette_job_status` rather than re-ingesting or starting a duplicate job.
- Exported files remain under the shared Oh My Cassette data directory. Prefer the returned resource
  link or file URI over relocating the artifact.
