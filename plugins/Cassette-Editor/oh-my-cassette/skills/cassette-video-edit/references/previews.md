# Showing the user what changed

Escalate one step per explicit user ask, and never auto-render:

**text digest → contact sheet → full export**

Every settled turn already carries the first level in its envelope, so most turns need nothing
extra from you.

## Timeline digest

The digest is text. When the user asks to see the timeline, reprint `quality.timeline_ctl`
**verbatim in a fenced code block**. It is a mechanical rendering of the project document, so
paraphrasing it silently invents state that nothing verified.

## Contact sheet and storyboard sheet

`cassette_timeline` with `contact_sheet=true` renders a contact sheet.

Terminal hosts save the sheet locally and present a link so the user can inspect it later. For
Claude Code, Codex CLI, and OpenCode, print the returned `contact_sheet_uri` /
`storyboard_sheet_uri` (`file://…`) on its own line — most terminals make it cmd+clickable, which
opens the real pixels in the system image viewer.

Hermes TUI needs its link sentinel. Print a short label such as `Thumbnail (saved locally):`, then
put `MEDIA:<contact_sheet_uri>` on its own line (or `MEDIA:<storyboard_sheet_uri>` for a
storyboard). Use the returned URL-encoded URI, **not** `contact_sheet_path`: raw macOS paths such as
`Library/Application Support` contain spaces and Hermes will leave that `MEDIA:` line as plain
text. This is a local clickable link, not a request to attach or inline-render the image.

Give the local link only; do not duplicate the thumbnail as an inline terminal rendering. On a
remote or SSH host a local `file://` cannot resolve; say the sheet is not viewable there. Do not
offer an editor link as a substitute — it is a bearer capability any signed-in account that sees
it can act on.

Preview files and exports inherit the session's immutable first-ingest +24-hour deadline. The
plugin removes them at that deadline; move an export outside the plugin-managed data directory
before then if the user wants to keep it.

## Plan review

With `CASSETTE_PLAN_REVIEW=user` — the default on MCP hosts, because a person is present in the
chat — a job pauses with an `edit_plan_review` question carrying the plan itself, each storyboard
beat as a readable cell and no raw links. The envelope's `quality` also carries `storyboard` (typed
beat cells) and `storyboard_sheet` (a tiled image of one source frame per planned beat, produced
without rendering the timeline).

Relay the plan verbatim, then answer via `cassette_answer_question` with `approve`,
`revise <feedback>`, or `reject`.

The user may instead decide in an open editor tab, and first answer wins: a
`resume_not_waiting_for_user` error means the tab answered first, so re-check status rather than
retrying the answer. Separately, typing a fresh message in an open editor tab cancels an in-flight
plugin turn because the tab takes over — that is product behaviour, not an error to retry.
