# Brief for the score

Give this to a second agent as soon as `timeline.json` exists. Replace the story paragraph.

> You are the composer and sound designer for a {LENGTH}-second film. Work only inside `audio/`.
>
> The film: {STORY IN THREE SENTENCES, WITH THE MORAL}. Tone: {e.g. a tender storybook lullaby, premium
> and restrained}.
>
> The hard rule: everything is code. No samples, no soundfonts, no audio files, no music or speech models,
> no network. Python 3 and numpy only; write your own oscillators, filters, reverb and WAV writer.
>
> Deliver `audio/score.py`, which reads `../timeline.json` (tempo, meter, shot starts and lengths, cue times
> in `events`) and renders `score.wav` (48 kHz stereo, exactly `total_seconds` long) plus stems for music,
> ambience and effects. Every timing comes from the JSON so a re-run follows any change.
>
> Music: {instrumentation, e.g. music box lead, slow warm pad, soft bass from the journey on}. Write a real
> theme of four or eight bars, chord tones on the downbeats. Follow the mood of each shot in the timeline;
> the clearest harmonic moment is at `{TURN EVENT}`.
>
> Ambience and effects from `events`, all subtle: {list}. Footfalls land exactly on each cue time.
>
> Mix to about -16 LUFS integrated with true peak under -1 dBFS, no DC, no clicks, mono compatible.
>
> You cannot listen, so verify in numbers and pictures: print per-section loudness, peak and spectral
> centroid; print the notes per bar with chord names and confirm every strong-beat melody note is a chord
> tone; render a spectrogram with ffmpeg and look at it; read integrated loudness and true peak back from
> `ffmpeg -af ebur128=peak=true`. Vectorize per note, never loop per sample.
