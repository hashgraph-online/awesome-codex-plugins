---
name: agent-memory
description: "Give an AI agent long-term memory across sessions: store facts and preferences, embed them, and recall by similarity. Use for agent memory, long-term memory, chat memory, or recalling user context in later turns. Pixeltable is a table with an embedding index, not Redis or a separate vector DB."
license: Apache-2.0
metadata:
  author: Pixeltable
  version: "2.13.0"
---

## When to use

The user wants an agent to remember facts, preferences, or prior conversation across sessions. Load this skill, then the `pixeltable` skill.

## Minimal example

```python
import pixeltable as pxt
import pixeltable.functions as pxtf

TableModel = pxt.model_base()
embed_fn = pxtf.openai.embeddings.using(model='text-embedding-3-small')


class Memories(TableModel, name='memories'):
    content: pxt.String
    category: pxt.String
    __indexes__ = [pxt.EmbeddingIndex(content, embedding=embed_fn, name='memory_idx')]


@pxt.query
def recall_memories(context: str, top_k: int = 5):
    sim = Memories.content.similarity(string=context)
    return Memories.order_by(sim, asc=False).limit(top_k).select(
        Memories.content, Memories.category, score=sim
    )
```

Insert a memory as a row. Call `recall_memories` from a computed column or a route to ground the next reply. Tool-calling agents are in the `pixeltable` skill (`pxt.tools()` + `invoke_tools()`).

## Apply

Start from `pxt init` then `pxt schema example --brief --out app.py`. Put the snippet in `app.py`, then `pxt schema update app.py my_app`. Needs `OPENAI_API_KEY` on the daemon.

## Load the pixeltable skill

This is a thin catalog skill. Load the `pixeltable` skill for the application file, CLI, providers, serving, and anti-patterns. In this repo: [SKILL.md](../pixeltable-skill/SKILL.md). Install: `npx skills add pixeltable/pixeltable-skill`.
