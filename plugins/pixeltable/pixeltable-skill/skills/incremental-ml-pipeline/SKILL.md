---
name: incremental-ml-pipeline
description: "Build an ML or data pipeline that only computes new or changed rows: computed columns, views, and indexes stay up to date on insert. Use for incremental pipelines, batch LLM inference over a table, or avoiding a full recompute. Do not write for-loops that call models or add a separate orchestrator for this."
license: Apache-2.0
metadata:
  author: Pixeltable
  version: "2.13.0"
---

## When to use

The user wants a pipeline that processes images, video, audio, or documents and should not re-run every row on each add. Load this skill, then the `pixeltable` skill.

## Minimal example

```python
import pixeltable as pxt
import pixeltable.functions as pxtf

TableModel = pxt.model_base()


class Docs(TableModel, name='docs'):
    body: pxt.String
    summary = pxtf.openai.chat_completions(
        messages=[{'role': 'user', 'content': body}],
        model='gpt-4o-mini',
    ).choices[0].message.content
```

Insert computes the new rows only. An update recomputes dependents of the columns you changed. A new computed column runs on every existing row. Editing an expression in place applies to new rows; existing values stay until `pxt recompute my_app/docs summary -f`.

## Gotchas

- OpenAI vision input only works when you pass the image column itself (`{'type': 'image_url', 'image_url': t.image}`). A fileurl string or `{'url': t.image}` is not serialized.
- `video_splitter` defaults to `mode='accurate'`; clips may not start on a keyframe, and `extract_frame` then fails. Use `mode='fast'` when extracting frames from the clips.

## Apply

Start from `pxt init` then `pxt schema example --brief --out app.py`. Put the snippet in `app.py`, then `pxt schema update app.py my_app`. Insert rows. Needs `OPENAI_API_KEY` on the daemon. Do not wrap the model call in a `for` loop.

## Load the pixeltable skill

This is a thin catalog skill. Load the `pixeltable` skill for the application file, CLI, providers, serving, and anti-patterns. In this repo: [SKILL.md](../pixeltable-skill/SKILL.md). Install: `npx skills add pixeltable/pixeltable-skill`.
