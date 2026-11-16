---
name: yaptake
description: Edit a Yaptake video project through its transcript. Use for cutting words or retakes, shortening pauses, fixing captions, arranging clips, changing the output format, or adding on-screen text in Yaptake.
metadata:
  version: "1"
---

# Edit a Yaptake project

Use the local `yaptake` command to inspect and edit a saved Yaptake project.
Each edit is validated by the app's editing core and becomes one undo step.
An open project updates in the app when the command applies an edit.

Yaptake must be installed on an Apple Silicon Mac running macOS 26 or newer.
In the app, **Help → Use with Coding Agents… → Command line** makes the
command available. If it is missing, point to the [download and setup
guide](https://yaptake.com/docs/agents).

Never edit `project.json` directly. The view file below is data for Yaptake
to parse; never execute it as JavaScript or TypeScript.

## Inspect, edit and preview

1. Read the current project, using the path supplied for the task. Create a
   temporary file for this edit:

   ```sh
   yaptake view /absolute/My-video.yaptake --outline
   YAPTAKE_EDIT=$(mktemp "${TMPDIR:-/tmp}/yaptake-edit.XXXXXX")
   yaptake view /absolute/My-video.yaptake > "$YAPTAKE_EDIT"
   ```

2. Edit that separate view file, preserving the IDs and structure described
   below. Keep recorded words, cuts and caption corrections distinct.
3. Validate the file before applying it:

   ```sh
   yaptake edit /absolute/My-video.yaptake --file "$YAPTAKE_EDIT" --dry-run
   ```

4. If validation succeeds, apply the same file:

   ```sh
   yaptake edit /absolute/My-video.yaptake --file "$YAPTAKE_EDIT"
   ```

   A stale revision is refused. Read the view again and redo the edit;
   do not force an older file onto the project.
5. Preview the changed passage, using sentence IDs from the current view:

   ```sh
   yaptake preview /absolute/My-video.yaptake --range s3-s5 --frames 4 --audio
   ```

   The reply names JPEG stills and an AAC snippet in a temporary folder,
   with their times and project revision. Inspect the images and listen to
   the audio to check the cut. Preview does not change the project. Remove
   only the temporary folder returned by this call when it is no longer needed.

Read the view again before making another edit.

## Read the view file

```ts
clip("c1", { name: "Kitchen", sound: true, picture: true, volume: 1 }, [
  say("s1", "Hi everyone, um, welcome back. (1.4s)"),
  say("s2", "~~So the first step.~~"),
]),
```

- Delete words to cut their picture and sound. Delete a `say()` line to cut
  that sentence. Retype words to correct captions; this does not change the
  recorded speech or add speech that was not recorded.
- Remove `~~` around words to restore a cut. Wrap words in `{}` to keep them
  playing while hiding their captions.
- Lower a pause such as `(1.4s)` to shorten it, or delete the pause to remove
  it. Put `|` before a word to start a new caption there.
- Move `say()` lines to reorder speech. Move or remove whole `clip()` blocks
  to arrange clips. Keep each ID attached to the object it identifies.
- A clip's `sound: false` mutes it, `picture: false` hides its video, and
  `volume` ranges from 0 to 1.
- On-screen text times refer to the edited video. If the edit also removes
  footage, a negative text start counts back from the end.

The [editing reference](https://yaptake.com/docs/agent-requests) covers split
clips, overlays, text options and the full view syntax. Use the public
[CLI reference](https://yaptake.com/docs/cli) or `yaptake --help` when a task
needs another command; do not invent fields or options.

## Make a short edit with operations

For a small change, put operation calls in a separate temporary file:

```sh
YAPTAKE_EDIT=$(mktemp "${TMPDIR:-/tmp}/yaptake-ops.XXXXXX")
printf '%s\n' 'cut_fillers()' 'tighten_pauses(0.4)' > "$YAPTAKE_EDIT"
yaptake edit /absolute/My-video.yaptake --ops --file "$YAPTAKE_EDIT" --dry-run &&
yaptake edit /absolute/My-video.yaptake --ops --file "$YAPTAKE_EDIT"
```

All calls in that file become one undo step. Targets use sentence IDs such
as `"s3"`, ranges such as `"s3-s5"`, lists such as `"s2,s7"`, or `"firstN"`,
`"lastN"` and `"all"`. IDs and these relative targets keep the meaning they
had when the edit started, even when an earlier operation removes speech.

`fit_length(seconds, keep?)` cuts toward a maximum duration. Name sentences
that must remain in `keep`; if the target cannot be reached, Yaptake changes
nothing and reports the shortest result it can make. `remove_dead_air()`
requires measured source audio; the outline lists available silent stretches.
`make_rough_reel()` builds from the project library, so inspect that library
and its recording order before using it.

Export only when the task requests it, to a new destination. Exports use the
app's export allowance and never overwrite an existing file. Report an
action-required response instead of changing account settings or retrying
with another identity.

## Use connected MCP tools

When Yaptake's `inspect`, `view`, `edit`, `check`, `apply`, `preview`,
`library`, `search` and `export` tools are available, they address the project
open in the app. A saved project path supplied for the task takes precedence:
use the CLI for that path unless `inspect` confirms the same project is open.
Follow the same loop: read `view`, call `edit` with the
edited `source` and `dryRun: true`, then call `edit` with that same source
and `dryRun: false`. Inspect `preview` to check the result. Use `ops: true`
for operation calls.

`app_not_open` means Yaptake is closed; `no_project` means no project is open.
Explain the response, or use the CLI when the task supplies a saved project
path. Never switch projects based on a guess.

Visual search needs an optional picture model. Report when it is unavailable;
do not start a model download. The [project format
reference](https://yaptake.com/docs/project-format) and [setup
guide](https://yaptake.com/docs/agents) describe the other interfaces.
