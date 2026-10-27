---
name: cassette-video-edit
license: MIT
description: Edit, trim, cut, caption, retime, combine, or export video, audio, and image files through Cassette. Use this skill whenever the user asks to change, preview, or render media in the project, even if they never say "Cassette" or name a tool, for example "trim the intro off demo.mp4", "add subtitles to this clip", "make a 30-second cut", "put a title on it", "export the video". Drives the tools of the `cassette` MCP server (oh-my-cassette), which relays a running conversation with the Cassette editing agent.
---

# Oh My Cassette

The `cassette` MCP server is a local bridge to the Cassette video editor. Its editing tools come
from the Cassette MCP service and change as Cassette evolves, so this skill deliberately names none
of them. **The server's instructions and each tool's description are the source of truth**: read
them, and when they disagree with anything you remember, they win.

## Rules that hold for every version

1. **Follow the server.** Which tool to call, in what order, and how to route on a result are in the
   server instructions and the tool descriptions. Route on typed fields such as `status`, never on
   prose.
2. **Relay the user's words.** When a tool takes the user's editing request, pass it exactly as the
   user wrote it: no rewriting, summarizing, translating, or expanding. The Cassette agent reads the
   project media itself.
3. **Ground every claim in a tool result.** What is on the timeline, which version it is, and where
   the editor link points come from the latest result, not from memory.
4. **Render only when asked.** Export or render only when the user asks to export, render, download,
   or finish.
5. **Say where the media goes.** When the user has not asked for Cassette by name in this
   conversation, tell them before the first upload that the files they named go to the Cassette
   service for editing, and go on once they agree.

## Local files

- Pass file paths as the user gave them, absolute or relative to the workspace. The bridge prepares
  and uploads them and hands Cassette references in their place.
- Only files the user named or that sit in the workspace. Never search the filesystem for media.
- Files outside the workspace are refused unless the user adds their directory to
  `CASSETTE_ALLOWED_ROOTS`. Only video, audio, and image files upload.
- Video is transcoded on this machine with ffmpeg before it uploads, and audio or images Cassette
  does not take as they are get converted. Long footage can take minutes.
- Exported files are downloaded into `cassette-exports/` in the workspace. Use the local path the
  result gives you; never invent one.

## Long waits

Long work never fails just for taking long. A tool waits a bounded time and then returns a normal,
non-error result that says the work is still going:

- **`status: "preparing"`** comes from the bridge: the local files are still being prepared or
  uploaded, and that work continues in the background. Tell the user the progress it reports, then
  call the same tool again with exactly the same arguments to keep waiting; it picks up the same
  work instead of starting over. Never keep calling for longer than the user is willing to wait:
  ask before you continue a long wait.
- **`running`, `processing` and similar statuses** come from Cassette. How to continue (usually the
  same tool with the id the result returns) is in the server instructions and the tool description.
- Cancelling a call only stops waiting; the work goes on. Stop the work itself only when the user
  asks, with the tool the server provides for that.

## When the bridge itself reports a problem

Errors whose code starts with `bridge.` come from the local bridge, not from Cassette. Any other
error code is Cassette's own: follow its message and the tool description.

| Code | What to do |
| --- | --- |
| `bridge.backend_unreachable` | A tool that names its request in an argument has already been sent again by the bridge while the call's wait lasted. If the message says the connection broke during the call, the work may still be running: call the same tool again with the same arguments to pick it up. If it says Cassette did not take the call, retry after `retry_after_seconds` when the error gives it. Otherwise call `cassette_bridge_status` once, tell the user the service is not reachable and at which URL, and retry only after it reports connected. |
| `bridge.rate_limited` | Cassette is taking too many requests and did not run the call. Wait `retry_after_seconds` (from the error), then call the same tool again with the same arguments; do not retry sooner. |
| `bridge.forbidden` | This account or grant cannot access Cassette. Ask the user to check that they signed in with the account of their projects. Do not repeatedly trigger login. |
| `bridge.auth_unavailable` | Online authentication or secure credential storage is unavailable. Tell the user to restore the connection or unlock the system keyring, then retry. |
| `bridge.unauthorized` | The service refused the token. Tell the user to run `oh-my-cassette login`. The browser handles email verification and consent. Restart the MCP host only if it cannot refresh tools. Do not repeatedly trigger login. |
| `bridge.upgrade_required` | Tell the user to update the oh-my-cassette version their MCP host runs (the message links the steps: bump the `oh-my-cassette==` pin, or update the plugin). Do not retry. |
| `bridge.protocol_unsupported` | The service at that URL is too old for this plugin (it does not speak MCP 2026-07-28). Tell the user the Cassette service must be updated. Do not retry. |
| `bridge.file_not_found` | Ask the user for the correct path. |
| `bridge.file_outside_workspace` | Ask the user to copy the file into the workspace, or to add its directory to `CASSETTE_ALLOWED_ROOTS`. When the message says the host started the bridge in a folder too wide to read from (the whole disk or the home folder), ask them to set `CASSETTE_WORKSPACE` to the project folder. |
| `bridge.file_type_rejected` | Tell the user which types this tool accepts (the message lists them). |
| `bridge.file_too_large` | Tell the user about the size limit (`CASSETTE_MAX_UPLOAD_MB`). |
| `bridge.ffmpeg_unavailable` | Video needs ffmpeg on this machine. Relay the install hint from the message, or ask the user to set `CASSETTE_FFMPEG` and `CASSETTE_FFPROBE`. Do not retry until it is installed. |
| `bridge.prepare_failed` | ffmpeg could not read or convert the file. Tell the user which file failed and what the message says; do not retry the same file unchanged. |
| `bridge.upload_failed` | Retry once, then report it. |
| `bridge.invalid_argument` | Fix the arguments: file parameters take a path or a list of paths. |
| `bridge.contract_violation` | A Cassette service bug. Report it to the user as is; do not retry. |

A failed export download (`bridge.download_failed`) does not fail the call: the result says so and
keeps the original URL, which you can give the user.

## When only `cassette_bridge_status` is listed

The service is offline, refused the token, or needs a newer plugin. Call `cassette_bridge_status`
once and tell the user what it reports (URL, `error_code` and reason). Do not poll it. When the
service comes back, its tools appear by themselves; if this host does not refresh tool lists, ask
the user to restart the MCP server.
