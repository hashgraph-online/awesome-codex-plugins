# From a conventional design to Pixeltable

Specs and design docs are written for a database plus application code: a worker processes uploads, a
status column tracks progress, a nightly job fills a metrics table. Built literally, that design uses
Pixeltable as a plain database with Python around it, and loses Pixeltable's advantages: incremental
computation, stored intermediate results, retries of only what failed, and lineage. Translate each
piece before writing code, and tell the user which pieces you translated.

## Translating a piece the table does not list

Ask what the piece does, and use the construct for that job:

- It computes a value from one row's data, such as a model call, a parse or a validation: a computed column.
- Its value depends on other rows, another table or the current time: a query, evaluated when it is read
  ([schema-design.md](schema-design.md#5-stored-computed-or-queried)). Do not store the value and refresh it with a
  job: the stored copy is stale between runs.
- It brings in new data on a schedule: the system scheduler runs a script that inserts the data, and the computed
  columns do the rest.
- It creates rows in another table: a route that inserts into the second table after the first insert, or a second
  table keyed like the first.
- It answers requests: a route over a table or a `@pxt.query`.

The table lists common cases of these rules.

| The spec asks for | Build |
|-------------------|-------|
| A worker or job queue that processes each upload, and a status to poll | An insert route with `background=True`. It answers at once with a `job_url`, and that URL is the status to poll: pending, then done with the route's outputs, or error (`pxt guide serving`). The computed columns are the pipeline. No jobs table, no status column, no thread. |
| A status such as `uploaded -> processing -> done / failed` | Derive it: the row exists, its stored computed columns have values, or `col.errortype != None`. Serve it from a `@pxt.query` through `add_query_route`. |
| Retry failed items, N times | `insert(..., on_error='ignore')` keeps the row and records the error in `col.errortype` / `col.errormsg`. `pxt recompute PATH COL --errors-only` reruns only the failed cells and their dependents; cells that succeeded are never redone. |
| A transform step that writes a cleaned table | Computed columns on the same table. |
| Split each item into chunks, frames, pages or segments, written to a child table | An iterator view (`pxt guide views` lists the iterators). |
| A metrics, stats or summary table refreshed by a job | A `@pxt.query` with `group_by` and aggregates, served by `add_query_route`. Regenerating the report means running the query. |
| A per-parent total written back onto the parent row | A query that groups the view by the parent's key; look the totals up by key when reading the parents. |
| Cron, nightly, "after each export" | Pixeltable has no scheduler. The system scheduler (cron, CI) runs a script that inserts the new data or calls a route, and the columns do the rest. Never a sleep loop or a thread in the service. |
| A cache in front of model calls (Redis) | Stored computed columns are the cache. |
| A vector database, an embedding job | `__indexes__ = [pxt.EmbeddingIndex(...)]` on the model. |
| A history array or a log appended by code | An append-only events table ([schema-design.md](schema-design.md#7-history)). |
| An endpoint that computes something from stored rows | `add_query_route` over a `@pxt.query`. A custom FastAPI handler only for what routes cannot express, and then a `def` handler, never `async def`. |
| An upload handler that saves the file and inserts it | `add_insert_route(..., uploadfile_inputs=[...])`, which puts the upload in Pixeltable's media store. |
| After processing, create rows in another table (extracted memories, assignments fanned out to stations) | No computed column writes to another table. Use a decorator route (`@router.insert_route(...)`): Pixeltable runs the insert, then calls your function with the new row's `outputs`, and the function inserts into the second table. With `background=True` both run in one job. Say in your report that this step is not declarative. |
| Look up another table while computing a column | A value that should follow the other table: look it up at query time. A value fixed when the row arrives: a column that calls a `@pxt.query` over the other table, computed on insert. It keeps its value when that table changes; `pxt recompute` refreshes it. Never a UDF that reads the table: `pxt.get_table()` inside a UDF fails on insert. |
| Flag near-duplicates of earlier uploads | A view over the uploads table with a column that calls a `@pxt.query`. The query searches the base table's embedding index for an earlier row above a similarity threshold, once per row, on insert: [the similarity-column pattern](#the-similarity-column-pattern). Never a loop that compares rows in Python and writes flags back. |
| Classify each item against a set of labels (zero-shot) | A labels table with an embedding index, and a column that calls a `@pxt.query` returning the most similar label: [the similarity-column pattern](#the-similarity-column-pattern). Never label embeddings kept in a file. |
| Combine per-frame (or per-chunk) results into one per-video result | A base-table column cannot aggregate its own view. Keep the per-frame work in a view, and put the aggregate in a second table keyed like the base: [the aggregate-table pattern](#the-aggregate-table-pattern) below. Never write the aggregate back onto the base row with `update()`, and never fold the pipeline into one UDF that loops over frames. |

## Signs that the design is still conventional

- A Python loop over `.collect()` results that computes something and writes it back with `update()`.
- A `status` column that only code changes.
- `threading`, `while True`, `time.sleep` or a FastAPI `lifespan` hook in the application file.
- A second datastore: SQLite, Redis, JSON files, pandas DataFrames kept between requests.
- More hand-written FastAPI handlers than `add_*_route` calls.
- A UDF that loads a model, shells out to ffmpeg, or loops over frames or chunks.

## The aggregate-table pattern

A result that combines many view rows (one video from its frames, one summary from its chunks) lives in
a second table, keyed like the base. Its computed column is a `@pxt.query` that aggregates the view, and a
decorator route inserts the key into it after the base insert:

```python
# ruff: noqa: F821
import pydantic

import pixeltable as pxt
from pixeltable.functions.video import frame_iterator, make_video
from pixeltable.serving import FastAPIRouter

TableModel = pxt.model_base()


class Videos(TableModel, name='videos'):
    video_id = pxt.Column(type=pxt.String, primary_key=True)
    video: pxt.Video


class Frames(TableModel, name='frames', base=Videos, iterator=frame_iterator(Videos.video, fps=2.0)):
    small = frame.resize((160, 90))  # type: ignore[name-defined]


@pxt.query
def reassemble(video_id: str) -> pxt.Query:
    return Frames.where(Frames.video_id == video_id).select(make_video(Frames.pos, Frames.small, fps=2))


class Reassembled(TableModel, name='reassembled'):
    video_id = pxt.Column(type=pxt.String, primary_key=True)
    video = reassemble(video_id)  # a Video column; its file goes into the media store


class Added(pydantic.BaseModel):
    video_id: str


api = FastAPIRouter(name='api')


@api.insert_route(
    Videos, path='/videos', inputs=['video_id'], uploadfile_inputs=['video'], outputs=['video_id'], background=True
)
def add_reassembled(*, video_id: str) -> Added:
    Reassembled.insert([{'video_id': video_id}])
    return Added(video_id=video_id)
```

- `video` is a Video column, because `reassemble()` returns one value per call (`pxt guide queries`).
- Nothing tracks the dependency across tables. After any change to a base row or its frames, recompute
  the aggregate row: with `t = pxt.get_table('my_app/reassembled')`, run
  `t.recompute_columns('video', where=t.video_id == vid)`.
- The two inserts are not one transaction: a failed second insert leaves the first in place.

## The similarity-column pattern

A value that comes from a similarity search, such as the label set's best match for an image or an earlier copy of
the same photo, is a column that calls a `@pxt.query`. `similarity()` takes the query's parameter as its value, and
the column runs the search once, when its row is inserted:

```python
import pixeltable as pxt
import pixeltable.functions as pxtf

TableModel = pxt.model_base()
clip = pxtf.huggingface.clip.using(model_id='openai/clip-vit-base-patch32')


class Labels(TableModel, name='labels'):
    name = pxt.Column(type=pxt.String, primary_key=True)
    __indexes__ = [pxt.EmbeddingIndex(name, embedding=clip, name='labels_clip')]


@pxt.query
def best_label(img: pxt.Image) -> pxt.Query:
    sim = Labels.name.similarity(image=img)
    return Labels.order_by(sim, asc=False).limit(1).select(Labels.name)


class Images(TableModel, name='images'):
    upload_no = pxt.Column(type=pxt.Int, primary_key=True)
    image: pxt.Image
    suggested_label = best_label(image)
    __indexes__ = [pxt.EmbeddingIndex(image, embedding=clip, name='images_clip')]


@pxt.query
def earlier_copy(img: pxt.Image, upload_no: int) -> pxt.Query:
    sim = Images.image.similarity(image=img)
    return Images.where((Images.upload_no < upload_no) & (sim > 0.9)).order_by(sim, asc=False).limit(1).select(
        Images.upload_no
    )


class Duplicates(TableModel, name='duplicates', base=Images):
    copy_of = earlier_copy(Images.image, Images.upload_no)
```

- `copy_of` is in a view because a model's own columns cannot call a query over that model.
- The threshold comes from the data: resized copies of the same photo scored 0.94 to 0.95 against the original
  with this model, and the closest different photo 0.77. Check a few pairs before choosing one.
- The search sees the rows of earlier inserts, not the other rows of the same insert: two copies uploaded in one
  batch are not flagged.
- A stored result keeps its value when the queried table changes. After a change to the labels, recompute
  `suggested_label`: `pxt recompute my_app/images suggested_label`.
