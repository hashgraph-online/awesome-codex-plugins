---
name: extract-audio
description: Get the sound out of a video or recording - save it as MP3, M4A, WAV or FLAC, cut a part, make it evenly loud, or prepare a 16 kHz mono WAV for transcription - and pull embedded subtitles out as SRT. Use when the user asks to extract audio, rip the soundtrack, turn a video into a podcast or MP3, get audio for transcription, or save the subtitles of a video.
---

# Audio (and subtitles) from video

Keep the original file. Name results after it (`meeting.mp4` → `meeting.mp3`) and do not overwrite anything.

## 1. Look first

```sh
ffprobe -v error -show_entries stream=index,codec_type,codec_name:stream_tags=language,title -of compact "$IN"
```

This lists the audio and subtitle tracks. If there are several audio tracks (languages, commentary), ask which one; select it with `-map 0:a:N`.

## 2. With ffmpeg

| Goal                                   | Command                                                                                     |
| -------------------------------------- | ------------------------------------------------------------------------------------------- |
| MP3, good quality                      | `ffmpeg -i in.mp4 -vn -c:a libmp3lame -q:a 2 out.mp3`                                       |
| M4A without re-encoding (AAC source)   | `ffmpeg -i in.mp4 -vn -c:a copy out.m4a` (if it fails, the track is not AAC: encode to MP3) |
| WAV for editing                        | `ffmpeg -i in.mp4 -vn -c:a pcm_s16le out.wav`                                               |
| FLAC (lossless, smaller than WAV)      | `ffmpeg -i in.mkv -vn -c:a flac out.flac`                                                   |
| Only a part (from 1:30, 2 minutes)     | `ffmpeg -ss 00:01:30 -t 120 -i in.mp4 -vn -c:a libmp3lame -q:a 2 part.mp3`                  |
| Evenly loud (podcasts, talks)          | `ffmpeg -i in.mp4 -vn -af loudnorm=I=-16:TP=-1.5:LRA=11 -c:a libmp3lame -q:a 2 out.mp3`     |
| For transcription (Whisper and others) | `ffmpeg -i in.mp4 -vn -ac 1 -ar 16000 -c:a pcm_s16le speech.wav`                            |
| Second audio track                     | add `-map 0:a:1` before the output name                                                     |

## 3. Subtitles

| Goal                        | Command                                               |
| --------------------------- | ----------------------------------------------------- |
| First subtitle track to SRT | `ffmpeg -i in.mkv -map 0:s:0 out.srt`                 |
| A given language            | `ffmpeg -i in.mkv -map 0:s:m:language:eng out.en.srt` |
| SRT ↔ VTT                   | `ffmpeg -i in.srt out.vtt`                            |

Only text subtitles (SubRip, ASS, mov_text, WebVTT) convert to SRT. Picture-based ones (PGS on Blu-ray, DVD subtitles) need OCR; say so instead of producing an empty file. Videos without subtitle tracks have nothing to extract: offer transcription of `speech.wav` instead.

## 4. Without ffmpeg

With the Converter Studio MCP tools, `convert` the video with `to: "mp3"`, `"m4a"`, `"wav"` or `"flac"`; subtitle files convert with `to: "srt"` or `"vtt"`. Taking only the sound is priced by the recording's length and costs far less than converting the video itself (which is also priced by its frame size and the format made). Without either, https://converter.studio does it in the browser.

## Report

Give the output's length, format and size, and which track was used. For subtitles, say how many lines came out and the language.
