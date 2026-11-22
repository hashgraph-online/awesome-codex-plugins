---
name: dawn
description: Compose or edit a local Dawn song in TypeScript, check its score, and render audio or MIDI with an installed Dawn CLI.
---

# Compose with Dawn

Dawn is a TypeScript music SDK and CLI for composing, arranging and rendering
music offline. It is a private preview: use an authorized installation from the
[install guide](https://dawnav.com/install). This skill does not grant access or
install optional models. Check `dawn --version` before starting.
The [agent guide](https://dawnav.com/docs/agents) covers the project workflow.

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

## Taste

Dawn's defaults favour restraint. They hold until the user states a preference;
then theirs wins. Record it (`dawn trace note --kind decision --text "..."`) and
follow it in every later pass.

- Before you arrange or revise, name what the song is and its best part. Keep
  that part in front. Nothing new sits level with it.
- Apply a style request in proportion. A quiet song takes a little of a club
  brief, or none.
- Subtract before you add, and put one idea in front at a time.
- Do not announce an arrival. By default use no riser, roll, impact or sweep
  into a section, and no key lift or pitch glide on the lead; a short fill at
  the end of a phrase is enough, and when the song needs a bigger gesture, use
  it once. An echo that decays sounds confident; a
  stutter that speeds up sounds eager.
- A drop wins by groove and can be leaner than the chorus before it. Reach its
  fullest bar late.
- Do not illustrate the words with sound effects.
- Words come first. Read every sung line on the finished master
  (`dawn vocals recall`) and fix or rewrite a line that does not read.
- Keep the lead dry and centred. Doubles and harmonies sit behind it in a long
  dark room of their own, and a quiet song gains them chorus by chorus.
- For a hazy or dream-pop direction, stack wordless harmony far behind the lead
  (`wobble`, `double`, chorus, a long dark reverb) and step it back under sung
  lines. The haze goes on the voices around the lead, not on the lead.
- When you revise an accepted song, change the smallest part that answers the
  request, keep the earlier version, and compare at matched loudness.

`dawn workflow read original-house references/craft.md` prints the full
reference. `dawn song` follows the same defaults, its house taste. Nothing
announces a section: no riser, noise sweep, roll, stutter, harp run, impact,
feint or key lift unless the prompt or the style asks, and a breakdown stays
dark, though a short fill still closes a full section. The chorus doubles sit
in a far room of their own, behind the lead, and a ballad, lullaby or
interlude sings its first chorus alone. A hazy or dream-pop prompt adds pads
and quiet washes around a lead kept in a short room. `dawn song --list` shows
the taste knobs, and `--taste <knob=value>` changes one for a song:
`--taste announce=once` lets the seed add one arrival signal and a rising
breakdown.

## Notes on a render

To point the user at places in a render, write a score document instead of
naming times in chat. Render the score beside the audio
(`dawn render review.score.json` next to `review.wav`), name it in the
document's head, and draw each stretch in a ` ```dawn ` fence with a mark per
point: `issue bars 18-19 lead: the vowel closes early`. `dawn doc --help` shows
the format. Run `dawn doc check notes.md` until it reports no problems, then
have the user run `dawn doc open notes.md` (it serves until Ctrl+C). They hear
each place from its link, drag across a figure to copy a link to the stretch
they mean, and paste it back. A pasted `#bars=18-19&track=lead` counts bars
from 1 as heard, the last one included.
