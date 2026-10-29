# Agentic editing practices

How the editing agents that work well cut footage, collected from their repos and docs (2026-10). Each practice links the project or article it comes from.

## 1. Let the model read the video, not watch it

Give the agent a word-level transcript of every take plus on-demand filmstrip and waveform images at decision points. Dumping every frame costs millions of tokens of noise; a 12 KB transcript and a few images are enough to cut with word precision.

Source: https://github.com/browser-use/video-use

## 2. Write an edit decision list, then render

Have the agent express the cut as data (sources, in and out points, the reason for each range, grade, overlays, subtitles) and let plain ffmpeg do the encoding. The EDL can be reviewed, diffed and re-rendered without redoing the reasoning.

Source: https://github.com/browser-use/video-use/blob/main/SKILL.md

## 3. Never cut inside a word; pad the edges

Snap every cut to word boundaries from the transcript and pad each edge by roughly 30-200 ms to absorb ASR timestamp drift. Tighter padding suits fast montage, looser padding suits documentary.

Source: https://github.com/browser-use/video-use/blob/main/SKILL.md

## 4. Pick cut points by silence length

Gaps of 400 ms or more are the cleanest cut points, 150-400 ms gaps need a visual check, and anything under 150 ms is unsafe. Extend past laughs and reactions, which are often the beat itself.

Source: https://github.com/browser-use/video-use/blob/main/SKILL.md

## 5. Fade audio for 30 ms at every cut

Hard audio cuts pop. A 30 ms fade-in and fade-out at each segment boundary removes clicks without being audible as a fade.

Source: https://github.com/browser-use/video-use/blob/main/SKILL.md

## 6. Burn subtitles last, on the output timeline

Apply captions after all overlays so nothing covers them, and compute their times on the edited timeline (word start minus segment start plus segment offset), not on the source.

Source: https://github.com/browser-use/video-use/blob/main/SKILL.md

## 7. Leave a margin around silence cuts

Fully removing every silent frame makes speech feel breathless. Keep a small margin (auto-editor defaults to 0.2 s before and after) and adjust it to the pace you want.

Source: https://github.com/WyattBlue/auto-editor

## 8. Make a proxy before anything else

Transcode heavy HEVC or 4K sources to a 1080p H.264 proxy with hardware decode first, so transcription, analysis and preview renders take seconds. Render the final from the originals.

Source: https://github.com/louisedesadeleer/cut-video

## 9. Use forced alignment for tight boundaries

Whisper is fine for the words but its timestamps drift, especially on retakes. Forced alignment (for example Montreal Forced Aligner or WhisperX) snaps words to the audio at 10-20 ms precision, which is what clean cuts need.

Source: https://github.com/louisedesadeleer/cut-video

## 10. Render with trim+concat, then re-transcribe

Extract each kept segment and concatenate rather than using a single select filter, which can misalign audio. Then transcribe the output again and scan for clipped words or surviving stutters before shipping.

Source: https://github.com/louisedesadeleer/cut-video

## 11. Agree on the plan before touching the cut

Show candidates or a plain-English strategy first: scored segments with hooks and reasons, then let the person pick and adjust timecodes. Only render what was approved.

Source: https://github.com/AgriciDaniel/claude-shorts

## 12. Self-check every cut boundary, with a cap

After rendering, inspect each cut (about 1.5 s either side) for visual jumps, audio spikes and hidden captions, confirm duration with ffprobe and measure loudness. Fix and re-render, but stop after about three passes and report what is left.

Source: https://github.com/browser-use/video-use/blob/main/SKILL.md

## 13. Score with a reviewer agent and loop back

A separate reviewer that scores adherence to the brief, pacing and visual quality can send feedback to the director when a threshold is missed. Save every iteration so you can compare versions.

Source: https://github.com/poseljacob/agentic-video-editor

## 14. Judge versions pairwise, not with absolute scores

Model judges are unreliable at absolute scores but reliable at saying which of two edits is better. Compare each new version against the previous one, swap the order and require it to win both times.

Source: https://github.com/YeJe-cpu/SeeCut

## 15. Keep an editable timeline as the source of truth

Store transcripts, subtitle layers, voice-overs and graphics in one editable project and treat MP4 and SRT as exports. Fixing one wrong line then doesn't mean starting over.

Source: https://github.com/JimLiu/baocut

## 16. Validate the edit spec before rendering

When the edit is JSON, check it against the schema and let a person review it in an editor before spending render credits. The same spec then works from chat, CLI or API.

Source: https://shotstack.io/docs/guide/agents/mcp-server/

## 17. Fix the transcript before rendering captions

Create the project without auto-rendering, correct names and misheard words in the transcript, then export. Fixing captions after the render costs another render.

Source: https://docs.submagic.co/guides/edit-transcript-before-rendering

## 18. Hand off to a real NLE for finishing

Export the agent's cut as an interchange timeline (OTIO, FCPXML, EDL, AAF) so an editor can finish it in Resolve, Premiere or Final Cut instead of receiving a flat MP4.

Source: https://github.com/AcademySoftwareFoundation/OpenTimelineIO

## 19. Measure loudness the agent cannot hear

Agents can't listen, so give them numbers: dialogue around -16 to -14 LUFS, music 18-20 dB under speech and true peak below about -1.5 dBTP, checked with ffmpeg's ebur128 filter.

Source: https://github.com/calesthio/OpenMontage/blob/main/skills/creative/sound-design.md

## 20. Tune scene detection with a stats pass

Run PySceneDetect once to write a stats CSV, read the content values and set the threshold from that; use the content detector for hard cuts and the threshold detector for fades to black.

Source: https://github.com/calesthio/OpenMontage/blob/main/skills/creative/scene-detect-usage.md

## 21. Keep captions inside the vertical safe zone

For 9:16 output, keep captions and key text inside a central safe area (about 900x1400 px of 1080x1920) and off the speaker's face, so platform UI and faces never cover them.

Source: https://github.com/calesthio/OpenMontage/blob/main/skills/creative/short-form.md
