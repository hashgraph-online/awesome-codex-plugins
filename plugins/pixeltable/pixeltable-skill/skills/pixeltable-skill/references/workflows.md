# FastAPIRouter

`from pixeltable.serving import FastAPIRouter`. One application file declares `TableModel` classes and routers. Start from `pxt service example --out app.py`. Apply tables with `pxt schema update`. Start HTTP with `pxt service update`.

```python
# app.py
import pixeltable as pxt
import pixeltable.functions as pxtf
from pixeltable.functions.huggingface import sentence_transformer
from pixeltable.serving import FastAPIRouter

TableModel = pxt.model_base()
embed_fn = sentence_transformer.using(model_id='intfloat/multilingual-e5-large-instruct')


class Docs(TableModel, name='docs'):
    document: pxt.Document
    timestamp: pxt.Timestamp
    uuid = pxt.Column(value=pxtf.uuid.uuid7(), primary_key=True)


class Chunks(
    TableModel,
    name='chunks',
    base=Docs,
    iterator=pxtf.document.document_splitter(
        Docs.document, separators='page, sentence', metadata='title,heading,page'
    ),
):
    __indexes__ = [pxt.EmbeddingIndex(text, embedding=embed_fn, name='chunks_embed')]  # type: ignore[name-defined]
    # Needs sentence-transformers + torch, and spaCy if separators include 'sentence'.


ingest = FastAPIRouter(name='ingest', prefix='/api', tags=['data'])
ingest.add_insert_route(
    Docs, path='/upload', uploadfile_inputs=[Docs.document], inputs=[Docs.timestamp],
    outputs=[Docs.document], background=True,
)
ingest.add_delete_route(Docs, path='/delete')

@pxt.query
def list_docs():
    return Docs.select(Docs.document, Docs.timestamp).order_by(Docs.timestamp, asc=False)

@pxt.query
def search_docs(query_text: str):
    sim = Chunks.text.similarity(string=query_text)
    return Chunks.where(sim > 0.3).order_by(sim, asc=False).select(
        text=Chunks.text, score=sim).limit(20)

ingest.add_query_route(path='/list', query=list_docs, method='get')
ingest.add_query_route(path='/search', query=search_docs, method='post')
```

```bash
pxt init
pxt schema update app.py my_app
pxt service update app.py my_app
```

After apply: `t = pxt.get_table('my_app.docs')`.

Already have FastAPI: after schema update, bind the catalog, then include the router. Call `pxt.get_table()` inside custom handlers.

```python
ingest.bind('my_app')
app.include_router(ingest)
```

The other way round also works: define the `fastapi.FastAPI` object in `app.py` and `include_router()` every router the file declares. `pxt service update` then serves that one application, named after the module, with the models bound at `TARGET` before it starts. Without a `FastAPI` object, each router is its own service on its own port.

- `add_insert_route`: POST from model columns. `uploadfile_inputs` for files. Persists the row. A file column is `uploadfile_inputs` or `inputs`, not both.
- `add_compute_route`: same request shape as insert, but `Table.compute()`: no row stored
- `add_update_route`: POST matches the row by primary key, so the request body carries the key (`id`) even though `inputs` does not list it. No `match_columns`
- `add_query_route`: wraps `@pxt.query`. Default `{ "rows": [...] }`. `one_row=True` returns the object (0 rows is a 404, more than one is a 409). `return_fileresponse=True` returns the one media column as a file (implies one-row)
- `add_delete_route`: POST delete by primary key, or by a nonempty `match_columns=` list
- Indexes on the model (`__indexes__`)

Media columns in JSON are URLs under `{prefix}/_pxt/media/...` (this file: `/api/_pxt/media/...`). Use that URL in a browser or `<img>` / `<video>`. Do not base64 the bytes. `return_fileresponse=True` streams the file instead of a URL.

`background=True` returns `{ "id", "job_url" }`. Poll `job_url` (`{prefix}/_pxt/jobs/{id}`). Status is `pending` | `done` | `error`, not `succeeded`. Mutually exclusive with `return_fileresponse`.

No HTTP: apply, then insert from Python. [Self-hosting](https://docs.pixeltable.com/howto/deployment/overview).

[cli.md](cli.md) | [core-api.md](core-api.md#serving)
