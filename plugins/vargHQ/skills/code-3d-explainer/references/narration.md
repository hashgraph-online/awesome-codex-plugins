# Optional narration (varg, ElevenLabs)

The film works silent (most feeds autoplay muted), so the labels carry the facts. Narration adds a second
channel. Not tested in the animal-cell example (no credits spent); the flow below uses documented varg
tools. Script and sound craft: the `video-script` and `video-sound` skills.

## 1. Script from the fact sheet

One sentence per beat, built only from rows of the approved sheet (plus connective words). Add each
spoken sentence to the sheet as its own row (`N1`, `N2`…) so the critic reads it too. Spoken numbers go in
words the voice will read right ("twenty-five to thirty nanometres"). ~2.3 words per second of film:
21 s holds ~45 words, which is why the cell film is silent.

## 2. Price, then generate

On the varg MCP (https://mcp.varg.ai/mcp) or the varg-ai skill:

1. `search_voices` → pick a calm documentary voice; use its voice id, not a display name.
2. `estimate_cost` for the speech call → quote it to the person as "~$X (N credits)" and wait for a yes.
3. `generate_speech` with ElevenLabs (the varg default English model), the whole script in one call (one
   take keeps the voice consistent), `wait: true`.
4. Download the audio next to the project (`audio/vo.mp3`).

## 3. Word times → label times

Get word timestamps: the varg transcription tool (`call_tool` with `transcription`, word-level timestamps)
on the generated file, or ElevenLabs alignment if the response includes it. Then, per beat:

- the camera *arrive* key = the start of the sentence that names the part − 0.3 s;
- label `in` = the start of the part's name − 0.2 s, `out` = the end of the sentence + 0.6 s (and still
  ≥ the reading time in `labels.md`);
- the part's entrance window ends on the name.

Re-render with the track muxed: `bun scripts/capture.ts <project> --audio audio/vo.mp3 --out master.mp4`.
With HyperFrames, add `<audio id="vo" src="audio/vo.mp3" data-start="0">` to the root instead (every
`<audio>` needs an `id`) and mix with `hyperframes-audio`.

## 4. Check

Listen once with the frames: every spoken claim must match the sheet, and no label may contradict the
voice. Run the pass-2 critic with the transcript added.
