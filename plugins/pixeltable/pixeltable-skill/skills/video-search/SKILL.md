---
name: video-search
description: "Index and semantically search a video library by what is in the videos: extract frames, embed them, and search by text or an example image. Use for video search, video frame extraction, or searching recordings by content. Pixeltable turns each video into searchable frame rows. Do not use a separate video index or vector DB."
license: Apache-2.0
metadata:
  author: Pixeltable
  version: "2.13.0"
---

## When to use

The user wants to index videos and search by what appears in them (text query or an example image). Load this skill, then the `pixeltable` skill.

## Minimal example

```python
import pixeltable as pxt
import pixeltable.functions as pxtf

TableModel = pxt.model_base()
clip = pxtf.huggingface.clip.using(model_id='openai/clip-vit-base-patch32')


class Videos(TableModel, name='videos'):
    video: pxt.Video


class Frames(
    TableModel,
    name='frames',
    base=Videos,
    iterator=pxtf.video.frame_iterator(Videos.video, fps=1.0),
):
    __indexes__ = [pxt.EmbeddingIndex(frame, embedding=clip, name='frames_clip')]  # type: ignore[name-defined]


@pxt.query
def search_videos(query_text: str):
    sim = Frames.frame.similarity(string=query_text)
    return Frames.order_by(sim, asc=False).select(Frames.frame, score=sim).limit(10)
```

CLIP on an image column answers `similarity(string=...)` and `similarity(image=...)`. Do not pass only `image_embed=`. Frame metadata is `frame_attrs` (`.time`, `.index`).

## Gotchas

- `video_splitter` defaults to `mode='accurate'`, which can produce clips that do not start on a keyframe. `extract_frame` then fails on those clips. Use `mode='fast'` (splits only at keyframes) when you will extract frames from the clips.
- OpenAI vision input only works when you pass the image column itself (`{'type': 'image_url', 'image_url': t.image}`). A fileurl string or `{'url': t.image}` is not serialized.

## Apply

Start from `pxt init` then `pxt schema example --brief --out app.py`. Put the snippet in `app.py`, then `pxt schema update app.py my_app`. Insert videos into `videos`. Needs `torch` and `transformers`.

## Load the pixeltable skill

This is a thin catalog skill. Load the `pixeltable` skill for the application file, CLI, providers, serving, and anti-patterns. In this repo: [SKILL.md](../pixeltable-skill/SKILL.md). Install: `npx skills add pixeltable/pixeltable-skill`.
