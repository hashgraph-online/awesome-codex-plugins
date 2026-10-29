---
name: image-similarity-search
description: "Semantic search over an image collection: CLIP embeddings, find similar images, and search images by text. Use for image semantic search, image similarity search, or visual search. Embeddings stay with the image rows. Do not install a separate vector DB."
license: Apache-2.0
metadata:
  author: Pixeltable
  version: "2.13.0"
---

## When to use

The user wants similar-image search, text-to-image search, or CLIP embeddings over a photo library. Load this skill, then the `pixeltable` skill.

## Minimal example

```python
import pixeltable as pxt
import pixeltable.functions as pxtf

TableModel = pxt.model_base()
clip = pxtf.huggingface.clip.using(model_id='openai/clip-vit-base-patch32')


class Images(TableModel, name='images'):
    image: pxt.Image
    __indexes__ = [pxt.EmbeddingIndex(image, embedding=clip, name='images_clip')]


@pxt.query
def search_images(query_text: str):
    sim = Images.image.similarity(string=query_text)
    return Images.order_by(sim, asc=False).select(Images.image, score=sim).limit(10)
```

Query with an example image using `similarity(image=query_img)` instead of `string=`. `embedding=clip` covers both modalities. Do not pass only `image_embed=` if you will query with text.

## Gotchas

- OpenAI vision input only works when you pass the image column itself (`{'type': 'image_url', 'image_url': t.image}`). A fileurl string or `{'url': t.image}` is not serialized.

## Apply

Start from `pxt init` then `pxt schema example --brief --out app.py`. Put the snippet in `app.py`, then `pxt schema update app.py my_app`. Insert images into `images`. Needs `torch` and `transformers`.

## Load the pixeltable skill

This is a thin catalog skill. Load the `pixeltable` skill for the application file, CLI, providers, serving, and anti-patterns. In this repo: [SKILL.md](../pixeltable-skill/SKILL.md). Install: `npx skills add pixeltable/pixeltable-skill`.
