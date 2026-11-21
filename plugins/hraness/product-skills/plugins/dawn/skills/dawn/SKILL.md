---
name: dawn
description: Compose or edit a local Dawn song in TypeScript, check its score, and render audio or MIDI with an installed Dawn CLI.
---

# Compose with Dawn

Dawn is a TypeScript music SDK and CLI for composing, arranging and rendering
music offline. It is a private preview: use an authorized installation from the
[install guide](https://dawnav.com/install). This skill does not grant access or
install optional models. Check `dawn --version` before starting.

Work in the song folder the user names. Read its `AGENTS.md`, `song.ts`, relevant
track files and `.dawn/sdk/v1.ts`. Import builders from `"dawn"`; the project maps
that name to its own SDK. Keep the user's musical choices and unrelated parts.

For a new song, create an empty folder and run `dawn init`. The supplied
[Morning study](examples/morning-study.ts) is an original eight-bar score with
synthesized instruments. Copy it to `song.ts` in that new project, or write a
score for the user's brief using the local SDK. Keep samples beside their tracks
when the user chooses to use them.

After each meaningful edit, run:

```sh
dawn check --json && dawn render review.wav --measure && dawn render review.mid
```

These commands check the source and write a WAV and MIDI file in the project.
Choose unused output names so an earlier review stays available. Inspect the
diagnostics and measurements, then listen when audio playback is available.
Report technical checks and listening separately; creating a file does not show
that the arrangement sounds right.

`dawn check` may refresh the project's compatible SDK and Dawn-owned agent notes.
When it reports a migration or runtime update, inspect `dawn changes --json` and
`dawn migrate --json` before applying one. Preserve the project's existing files
and follow the corrective command rather than rewriting its format by hand.

Songs are executable TypeScript. Review unfamiliar source before running it.
Keep substantial edits recoverable with a copy or commit. Publish a song or set up
an optional provider only when the user requests it; local rendering needs neither.

Use the [agent guide](https://dawnav.com/docs/agents) for the complete edit loop,
the [SDK guide](https://dawnav.com/docs/sdk) for builders and the
[CLI reference](https://dawnav.com/docs/cli) for exports and diagnostics.
