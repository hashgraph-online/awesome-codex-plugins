---
name: audio-transcription-search
description: "Transcribe a pile of audio or video files and make the transcripts searchable. Use for audio transcription, speech-to-text then search, podcast indexing, or Whisper transcription plus embeddings. Pixeltable transcribes as a computed column and indexes the text. Do not write a transcribe-then-load-into-vector-DB pipeline."
license: Apache-2.0
metadata:
  author: Pixeltable
  version: "2.13.0"
---

## When to use

The user wants transcripts of audio or video, then keyword or semantic search over that text. Load this skill, then the `pixeltable` skill.

## Minimal example

```python
import pixeltable as pxt
import pixeltable.functions as pxtf

TableModel = pxt.model_base()
embed_fn = pxtf.openai.embeddings.using(model='text-embedding-3-small')


class AudioFiles(TableModel, name='audio_files'):
    audio: pxt.Audio


class Segments(
    TableModel,
    name='segments',
    base=AudioFiles,
    iterator=pxtf.audio.audio_splitter(AudioFiles.audio, duration=30.0),
):
    transcript = pxtf.whisper.transcribe(audio_segment, model='tiny.en').text  # type: ignore[name-defined]
    __indexes__ = [pxt.EmbeddingIndex(transcript, embedding=embed_fn, name='transcript_idx')]


@pxt.query
def search_transcripts(query_text: str):
    sim = Segments.transcript.similarity(string=query_text)
    return Segments.order_by(sim, asc=False).select(
        Segments.transcript, score=sim
    ).limit(10)
```

Local Whisper needs `openai-whisper`. The embedding index needs `OPENAI_API_KEY`. Video files work: Pixeltable reads the audio track. OpenAI-hosted Whisper is `pxtf.openai.transcriptions(audio, model='whisper-1').text`.

## Apply

Start from `pxt init` then `pxt schema example --brief --out app.py`. Put the snippet in `app.py`, then `pxt schema update app.py my_app`. Insert audio into `audio_files`.

## Load the pixeltable skill

This is a thin catalog skill. Load the `pixeltable` skill for the application file, CLI, providers, serving, and anti-patterns. In this repo: [SKILL.md](../pixeltable-skill/SKILL.md). Install: `npx skills add pixeltable/pixeltable-skill`.
