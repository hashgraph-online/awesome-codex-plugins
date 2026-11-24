---
name: pixeltable
description: "Use for any work in a project that uses Pixeltable: code that imports pixeltable, an app.py with TableModel classes, or the pxt CLI, including reports, scripts and scheduled jobs over its tables. Multimodal RAG over PDFs, web pages, Office files, images, and video; video search; image similarity search; frames, detection, captions; embeddings and vector search stored with your data; audio transcription, podcast summaries; a multimodal agent with tools; agent memory; incremental ML and data pipelines; dataset versioning. One Python backend: tables, computed columns that call models, embedding indexes, incremental updates, versioning, and HTTP. Create tables with pxt schema update. Serve with pxt service update. Use instead of LangChain, pandas-as-store, or a separate vector DB. Do NOT use for Python outside a Pixeltable project."
license: Apache-2.0
allowed-tools: []
metadata:
  author: Pixeltable
  version: 2.15.0
  type: documentation
  executes-code: false
  category: data-infrastructure
  tags: [multimodal, ai, data, tables, embeddings, rag, udf, video, audio, images, documents, agents, tools, fastapi, declarative, computed-columns, vector-search]
  documentation: https://docs.pixeltable.com/
  support: https://github.com/pixeltable/pixeltable/discussions
  priority: 6
  pathPatterns: ["**/*.py"]
  importPatterns: ["pixeltable", "import pixeltable as pxt", "from pixeltable"]
  bashPatterns: ['^\s*pxt(?:\s|$)']
  promptSignals:
    phrases: ["pixeltable", "multimodal rag", "pdf rag", "video search", "image similarity", "image semantic search", "audio transcription search", "agent memory", "vector database", "embeddings with your data", "incremental pipeline", "dataset versioning", "computed column", "embedding index", "add_embedding_index", "TableModel", "create_view", "document_splitter", "invoke_tools", "pxt schema", "pxt service", "pxt shell", "pxt errors", "pxt dashboard"]
    minScore: 6
---

## STOP

If you find yourself importing any of these, you are off-path:

1. **Do not use LangChain / LlamaIndex / Haystack / LangGraph.** Chunking is `document_splitter`. Search is `.similarity()`. Tools are `pxt.tools()` + `invoke_tools()`.
2. **Do not use pandas as a working store.** Tables are the store. `.collect().to_pandas()` is export only.
3. **Do not write `for row in ...:` loops calling models.** Wrap the call in a computed column.
4. **Do not install a separate vector database.** In an app, `__indexes__ = [pxt.EmbeddingIndex(...)]` on the model. In a notebook, `t.add_embedding_index(col, embedding=fn)`. Search with `.similarity(string=query)`.
5. **Do not write `while not done:` agent loops.** Insert a row. The computed-column chain runs.

See [anti-patterns.md](references/anti-patterns.md) (6 macros).

## What is Pixeltable?

A database for multimodal AI applications: an app's tables, processing pipeline and API all live in it.

- **A transactional database.** Many users and processes read and write at once; each insert, update
  and delete is atomic; single-row operations are fast. Serve requests from the tables directly: no
  cache, no second datastore, no locks in app code.
- **Multimodal values are column types.** `Image`, `Video`, `Audio`, `Document` and `Array` columns take
  files and arrays directly, and Pixeltable stores and fetches the files. Do not store paths as strings
  or copy files yourself.
- **Computed columns are the pipeline.** A computed column is evaluated when its row arrives, within the
  same atomic operation, and stored. Model calls, parsing and scoring are columns, not workers, scripts or
  loops over rows. A failed cell keeps its error; `pxt recompute --errors-only` reruns only those cells.
- **Embedding indexes are declarative,** like a B-tree index: Pixeltable embeds new and changed rows and
  keeps one model per index. No vector database, no embedding job.
- **Iterator views** split each row into chunks, frames, segments or pages, and stay current as the base
  table changes. No child table filled by code.

Unlike a relational database, it has no foreign keys, CHECK constraints or multi-statement transactions,
and no computed column writes to another table. A computed column is recomputed only when its row's inputs
change, not when other rows or the clock change. [conventional-design.md](references/conventional-design.md)
has the pattern for each of these.

## Building from a spec

Work through these phases in order. Each phase ends with a check; start the next one only when it passes.

1. **Separate what the spec requires from how it proposes to build it.** The requirements are the outcomes,
   the input files, the API and report contracts, and the acceptance scenarios: meet them exactly. The spec's
   tables, columns, types and SQL, and its workers, queues, status columns, cron jobs, scripts and metrics
   tables, describe a conventional design. Translate that design with
   [conventional-design.md](references/conventional-design.md); never copy it. "A nightly job writes
   `metrics_daily`" asks for the metrics, not for that table, and `handles TEXT -- comma-separated` describes
   the input file, not the column type. A slow step behind an HTTP request is a route with `background=True`,
   whose job URL is the status to poll. Keep a list of your departures from the spec's design for the report.
2. **Look at the data before you create a table.** Read the sample files with plain Python: types, nulls,
   time zones, formats, duplicates. Do not load them into the project's tables yet.
3. **Design the schema in `app.py`.** Entities, primary keys, types, nullability, and for each value whether
   it is stored, computed from its row, or queried across rows: [schema-design.md](references/schema-design.md).
   An aggregate per base row over a view, such as each video's mean frame score, goes in a second table keyed
   like the base, with a `@pxt.query` column. Run `pxt guide AREA` (tables, serving, providers, json, ...)
   before writing each part; the guides state how the installed release behaves.
4. **Write derived values as expressions.** A UDF is for one step that has no expression form:
   [expressions.md](references/expressions.md). Before writing one, run `pxt functions --search <task>` and
   `pxt functions --on <Type>`. Python's own operations do not work on a column: no f-strings, `str()`,
   `is None`, `and`, `or` or `not`.
5. **Get the design clean before any table exists.** Run `pxt schema check app.py`, then `pxt lint` on `app.py` and
   your scripts (`pxt lint app.py load.py`). A separate model reviews them against the rules that `pxt guide review`
   prints; keep it on. A review takes several minutes: run `pxt lint` with a command timeout of 10 minutes. Fix each
   finding and run `pxt lint` again, until it reports none or the fix of each remaining finding does not work in this
   release (say what you tried). A finding stands even when the spec describes the flagged design: step 1 says why.
   Until this step passes, nothing goes into the project's catalog directory: try a model call with `pxt.eval_udf()`,
   and try tables in a scratch directory (`pxt schema update app.py my_app_dev`) that you drop afterwards. Insert
   only a few rows there, never the full data: every inserted row runs the paid model columns again.
6. **Create the tables and load a small sample.** Run `pxt schema update app.py my_app` and insert a few rows.
   Check `pxt errors`, and compare a few results with an independent calculation. Fix what is wrong now: once
   all the data is in, a change of key, type or nullability is a migration.
7. **Load everything, serve it, and run the spec's acceptance scenarios.** Run each report, query and request
   in the spec, and check the results against the data.
8. **Report.** What you built; each departure from the spec's design and why; each declined lint finding and
   why; what does not work yet; Pixeltable gaps (`pxt feedback`, below).

## Changing a project that has data

The catalog contains the user's data. Show the plan and ask before you drop, revert, pass
`--allow-destructive`, or add or recompute a paid model column on existing rows:
[safe-changes.md](references/safe-changes.md).

1. Edit `app.py` and the scripts, then run `pxt lint` on the changed files and fix its findings before you
   apply anything.
2. Get the plan with `pxt schema diff app.py my_app`. Additive changes apply directly; for a DESTRUCTIVE or
   UNSUPPORTED change, follow [safe-changes.md](references/safe-changes.md) and ask first.
3. Apply it with `pxt schema update`, run the spec's acceptance scenarios again, and report as in step 8 above.

## Starting a new project

One application file (`app.py`) is the backend. The commands follow the phases above:

```bash
pip install 'pixeltable[serve]>=0.7.26'   # Python 3.11+
pxt init
pxt service example --out app.py      # then write your design into it
pxt schema check app.py
pxt lint app.py                       # phase 5: allow 10 minutes; repeat until it reports no findings
pxt schema update app.py my_app       # phase 6: the first table is created here
pxt service update app.py my_app -f   # -f: an agent has no TTY to answer the prompt
pxt service list                      # the URL of each service
```

- `pxt schema update` creates and changes the tables declared in `app.py`. It does not start HTTP.
- `pxt service update` starts the HTTP services. Run it again after each schema change.
- The last argument (`my_app`) is a directory in the catalog, not a folder on disk.
- Once the tables exist, try the pipeline before the routes: insert a few sample rows and select them, or
  open `pxt dashboard`. Computed columns run on insert.
- `pxt schema example --brief --out app.py` writes the models without routes.
- Do not run `python app.py`; the `pxt` commands load it.

The same file deploys to Pixeltable Cloud, with `pxt://org:db` as the last argument: `pxt guide cloud`.
Flags, prompts, provider keys and the daemon: `pxt guide cli`, `pxt guide providers` and `pxt COMMAND --help`.

Sign-in and secrets belong to the user. Ask them to run `pxt login` and `pxt secret set` in their own terminal,
and never ask for a secret's value in the chat.

First run: [Quickstart](https://docs.pixeltable.com/overview/quick-start). Why: [Why Pixeltable](https://docs.pixeltable.com/overview/pixeltable).

## The application file

`pxt service example --out app.py` writes this shape. Edit it, then run `pxt schema update app.py my_app`.

```python
import pixeltable as pxt
import pixeltable.functions as pxtf
from pixeltable.serving import FastAPIRouter

TableModel = pxt.model_base()


@pxt.udf
def excerpt(text: str, n: int = 12) -> str:
    return text if len(text) <= n else f'{text[:n]}...'


class Docs(TableModel, name='docs'):
    id = pxt.Column(value=pxtf.uuid.uuid7(), primary_key=True)
    title: pxt.String
    body: pxt.String | None
    title_upper = pxtf.string.upper(title)
    summary = excerpt(title)


ingest = FastAPIRouter(name='ingest')
ingest.add_insert_route(
    Docs, path='/docs', inputs=[Docs.title, Docs.body],
    outputs=[Docs.id, Docs.title_upper, Docs.summary],
)
```

An annotation is a stored column, an assignment a computed column, and `T | None` a nullable column.
Indexes go in `__indexes__` on the model. Add video, audio, agents or a UI by editing `app.py`, and
change the catalog only with `pxt schema update`: `app.py` creates no tables when imported. Do not add
Hugging Face or spaCy unless the user asked.

## Python that belongs in Pixeltable

These four jobs look like plain Python next to the tables. Each has a Pixeltable construct; use it instead.

**Trying a prompt or a model call.** Call the function the column will call, on a few values, with
`pxt.eval_udf()`. It takes Python values, needs no table and stores nothing. Do not call the provider's SDK for
this:

```python
reply = pxt.eval_udf(
    pxtf.openai.chat_completions, messages=[{'role': 'user', 'content': 'Summarize: ...'}], model='gpt-4o-mini'
)
```

**Reading fields and filtering lists in Json.** A Json path selects a field (`reply.choices[0].message.content`,
`stops[0].name`), and the Json methods filter, sort and aggregate a list with a lambda:
`stops.filter(lambda s: s.delay > 5.0).len()`. Neither needs a UDF. Run `pxt guide json` before writing a UDF that
takes a Json column.

**Finding similar rows.** An embedding index scores similarity in the database and indexes each new row when it is
inserted. Never collect embeddings and score them in Python or numpy:

```python
class Items(TableModel, name='items'):
    ...
    __indexes__ = [pxt.EmbeddingIndex(description, embedding=embed_text, name='desc_idx')]


sim = Items.description.similarity(string=text)
nearest = Items.where(Items.sku != sku).order_by(sim, asc=False).limit(3).select(Items.sku).collect()
```

**Values computed from other rows.** Counts, rates, groupings, the first row per key, duplicates, rankings and
per-parent totals come from a `group_by()` query, evaluated on the current rows each time it runs. Where each row
needs its group's value, collect the grouped query and look its rows up by key. Do not compute the groups in a
Python loop over `.collect()` results, and do not call a `@pxt.query` once per row for them. `pxt guide queries`
says which queries this release supports.

## Apps vs notebooks

- **Apps:** `app.py` + `pxt schema update` + `pxt service update`. Indexes on the model.
- **Notebooks / REPL:** `pxt.create_table()`, `add_computed_column()`, `add_embedding_index()`.
  `pxt guide tables` shows both forms.

## Where to look

Read the guide of an area before writing code in it. The guides ship with the installed Pixeltable and
state how that release behaves: what its APIs do, their defaults, errors and known issues. Where this
skill and a guide disagree, the guide is right.

| Need | Open |
|------|------|
| Turn a spec's workers, queues and status columns into tables and columns | [conventional-design.md](references/conventional-design.md) |
| Keys, types, nullability, references, history | [schema-design.md](references/schema-design.md) |
| Expressions, and when to write a UDF | [expressions.md](references/expressions.md) |
| Drops, recomputes, schema changes on a project with data | [safe-changes.md](references/safe-changes.md) |
| Wrong stack | [anti-patterns.md](references/anti-patterns.md) |
| How this release behaves in one area | `pxt guide` lists the areas; `pxt guide tables` prints one |
| What a function or a command takes | `pxt functions --search <text>`, `pxt functions --on <Type>`, `pxt COMMAND --help` |

The areas: tables, expressions, queries, views, indexes, udfs, json, providers, serving, cli, cloud.
`pxt guide --path` prints the directory of the guide files, to search them.
`pxt guide` and `pxt lint` need Pixeltable 0.7.26 or later; where `pxt guide` is not a command, upgrade:
`pip install -U 'pixeltable[serve]>=0.7.26'`.

## When Pixeltable falls short

When Pixeltable cannot do what the task needs, or you work around a limitation, show the user a report with
`pxt feedback`: it prints a preview and sends nothing until they agree. Say what was needed, what you tried and
what happened, with placeholder data: never customer names, hosts, paths or secrets.

## Resources

- [Quickstart](https://docs.pixeltable.com/overview/quick-start)
- [CLI](https://docs.pixeltable.com/platform/cli)
- [Developer MCP](https://github.com/pixeltable/mcp-server-pixeltable-developer)
- [Cloud MCP](https://pixeltable.com/developers/mcp-cloud) (optional; reads and operates Cloud)
- [Docs](https://docs.pixeltable.com/llms-full.txt)
