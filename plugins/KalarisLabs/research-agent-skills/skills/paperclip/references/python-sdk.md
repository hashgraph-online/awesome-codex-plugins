# The `gxl_paperclip` Python SDK

A typed client over the same server the CLI talks to. Reach for it when Paperclip work belongs inside
a script, notebook, or service — batch retrieval, joining results against your own data, streaming map
progress into a UI. For interactive one-off queries the CLI is faster.

Signatures below were read from the installed package with `inspect` on **0.7.14** and re-checked on
**0.7.15**; `search`, `health`, `papers.head`, `results.list`, and `execute` were executed live. Repo,
library, and map calls are transcribed from their signatures and not exercised here.

## Installing

The curl installer bundles the SDK inside its private tree at `~/.paperclip/lib/`, which is **not** on
your `sys.path`. For real use, install it into the environment you control:

```bash
uv pip install https://paperclip.gxl.ai/paperclip.whl
# or
uv add https://paperclip.gxl.ai/paperclip.whl
```

Install from the full URL, not by name: `gxl-paperclip` is not on PyPI, and the `paperclip` package
that is on PyPI is unrelated software. The wheel URL is unversioned, so a rebuild of your environment
can pick up a newer SDK — check `gxl_paperclip.__version__` if behavior shifts.

Verify:

```python
import gxl_paperclip
print(gxl_paperclip.__version__)   # 0.7.15 at time of writing
```

If you only need a quick script on a machine that has the CLI, you can borrow the bundled copy — but
it is tied to the installer's layout and will break if that changes:

```python
import sys
sys.path.insert(0, "/Users/you/.paperclip/lib")
from gxl_paperclip import PaperclipClient
```

## Connecting

```python
from gxl_paperclip import PaperclipClient

client = PaperclipClient.from_env()
```

`from_env()` picks up `PAPERCLIP_API_KEY`, falling back to the OAuth credentials `paperclip login`
wrote to `~/.paperclip/credentials.json`. Optional keyword arguments: `base_url`, `timeout`
(default 120.0), `user_agent`, `session`.

Explicit auth strategies are available when the environment is not enough:

```python
from gxl_paperclip import PaperclipClient, APIKeyAuth, BearerAuth, FileCredentialsAuth

client = PaperclipClient(APIKeyAuth("gxl_..."), timeout=300.0)
```

Check the connection:

```python
status = client.health()
# HealthStatus(reachable=True, output='Health:  healthy\nInit:    True', exit_code=0, elapsed_ms=15)
```

## `ExecuteResult`

Almost every call returns one:

| Field | Meaning |
|---|---|
| `output` | Rendered text, as the CLI would print it |
| `exit_code` | 0 on success |
| `elapsed_ms` | Server-side latency |
| `result_id` | `s_*` id to pass to `map_`/`reduce`/`results` |
| `result_data` | Structured payload when the command produces one |
| `download_url`, `download_filename` | Set for commands that produce a file |
| `cwd` | Virtual working directory after the call |
| `raw` | Unparsed server response |

**`output` from `search` carries ANSI colour codes.** Strip them before parsing or logging:

```python
import re
ANSI = re.compile(r"\x1b\[[0-9;]*m")
clean = ANSI.sub("", result.output)
```

`papers.*` output is plain text and needs no stripping.

## Search and retrieval

```python
result = client.search("CRISPR delivery", limit=5, source="pmc")
print(result.result_id)      # s_5e9cc4f4
```

```python
client.search(
    query,
    limit=None, source=None, exact=False, since=None, sort=None,
    author=None, journal=None, year=None, type=None, category=None,
    mode=None, min_embedding_similarity=None, min_bm25_score=None,
    all=False, timeout=None,
)
```

`source` is the SDK's equivalent of `-s` and behaves the same way — pass it. `mode` corresponds to
`--ranking`. `min_embedding_similarity` and `min_bm25_score` are score floors with no CLI equivalent,
useful for suppressing weak tail matches in a batch job.

```python
client.lookup("doi", "10.1073/pnas.2307796121", limit=None)
client.sql("SELECT source, COUNT(*) FROM documents GROUP BY source")
client.sql("SELECT COUNT(*) FROM uniprot_v.proteins", source="proteins")
```

## Reading documents — `client.papers`

```python
client.papers.ls("/papers/PMC10945750/")
client.papers.cat("/papers/PMC10945750/meta.json")
client.papers.head("/papers/PMC10945750/content.lines", lines=40)
client.papers.tail("/papers/PMC10945750/content.lines", lines=20)
client.papers.grep("lipid nanoparticle", "/papers/PMC10945750/content.lines",
                   ignore_case=True, extended=False)
client.papers.scan("/papers/PMC10945750/content.lines", ["IC50", "EC50", "dose"])
```

`head` returns text with the `L<n>:` prefixes intact, so line numbers for citations come straight out:

```python
out = client.papers.head("/papers/PMC10945750/content.lines", lines=3).output
# 'L1: Targeted nonviral delivery of genome editors in vivo\nL2: Proceedings of the National...'
```

Reading metadata as a dict:

```python
import json
meta = json.loads(client.papers.cat("/papers/PMC10945750/meta.json").output)
meta["doi"], meta["journal"], meta["pub_year"]
```

## map and reduce

`map_` **streams** — it returns an iterator of events rather than a single result:

```python
from gxl_paperclip import MapProgressEvent, MapResultEvent

for event in client.map_("What delivery vector and efficiency were reported?",
                         from_results="s_abc123"):
    if isinstance(event, MapProgressEvent):
        print("progress:", event)
    elif isinstance(event, MapResultEvent):
        print("result:", event)
```

```python
client.reduce(
    "Compare vector, cell type, and efficiency",
    from_map="m_def456",
    strategy="table",                       # summarize | table | themes | consensus | bullet_points | extract
    columns=["paper", "vector", "efficiency"],
)
```

Give `map_` a generous `timeout`, or set one on the client — an LLM reader over ten papers routinely
exceeds the 120 s default.

## Results

```python
for row in client.results.list(limit=10):
    print(row.result_id, row.command, row.created_at)
    # s_5e9cc4f4 search 2026-07-28T01:05:31.651263+00:00

data = client.results.get("s_5e9cc4f4")     # ResultData: result_id, output, command, latency_ms, ...
```

## Figures, files, and arbitrary commands

Resolve the filename from `papers.ls` first — figures are named by the publisher, not `fig1.jpg`:

```python
client.papers.ls("/papers/PMC10945750/figures/")
# pnas.2307796121fig01.gif  pnas.2307796121fig01.jpg

fig = "/papers/PMC10945750/figures/pnas.2307796121fig01.jpg"
client.ask_image(fig, "What is on each axis?")
client.ask_image(fig, fn="extract-data")

# pull() does NOT work for binaries in 0.7.14–0.7.15: returns exit_code 0 with download_url None
# and writes no file. There is no working route to a local image — use ask_image server-side.
client.pull(fig, "fig01.jpg")

client.upload_document("analysis.json", data_bytes,
                       folder_path="analyses/my-topic",
                       content_type="application/json")
```

Anything the SDK does not wrap is reachable through the escape hatches:

```python
client.execute("search", ["-s", "pmc", "CRISPR delivery", "-n", "5"])

for event in client.stream("map", ["--from", "s_abc123", "question"]):
    ...
```

**`client.bash()` does not work in 0.7.14–0.7.15.** It passes the whole script as a single command
name, so even a plain command fails, and pipes and redirection fail with it:

```python
r = client.bash("grep -c CRISPR /papers/PMC10945750/content.lines")
r.output
# 'ERR: vsh: grep -c CRISPR /papers/PMC10945750/content.lines: command not found. ... [exit 126]'
```

Use `execute()` with an argument list instead, and do any piping in Python:

```python
client.execute("grep", ["-c", "CRISPR", "/papers/PMC10945750/content.lines"])
```

## `exit_code` does not report sandbox failures

The call above returned `exit_code == 0` while the sandbox reported `[exit 126]` inside `output`. The
`ExecuteResult.exit_code` field describes the HTTP-level command dispatch, not the command that ran
inside `vsh`. Check the output too:

```python
r = client.execute("cat", ["/papers/PMC99999999/meta.json"])
failed = r.exit_code != 0 or r.output.lstrip().startswith("ERR:")
```

The CLI does surface the real status — `paperclip search -s pmc "x"` with a bad key exits 1 — so shell
callers can rely on `$?` where SDK callers cannot.

## Repos and library

`client.repos` and `client.library` are lower-level than the CLI: they take repo ids and entry ids
rather than names, so resolve the name first.

```python
repo = client.repos.get_repo_by_name("my-review")
client.repos.create_repo("my-review", "Delivery vectors")
client.repos.add_papers(repo["id"], [{"document_id": "PMC10945750"}])
client.repos.annotate_paper(repo["id"], entry_id, "Claim text", lines="L45-L52")
client.repos.commit(repo["id"], "Initial citations")
client.repos.get_status(repo["id"])
client.repos.create_branch(repo["id"], "safety")
client.repos.merge_branches(repo["id"], "safety", "main")
bibtex = client.repos.export(repo["id"], "bibtex")        # returns bytes
```

```python
client.library.list_papers(page=1, per_page=50, search="fine-tuning")
client.library.upload_pdfs([("paper.pdf", pdf_bytes)])
job = client.library.poll_import_job(job_id, timeout_s=900)
client.library.delete_paper(paper_id)
```

The same rule as the CLI applies: repositories are opt-in. Do not create one unless the user asked.

## Errors

All inherit from `PaperclipError`:

```python
from gxl_paperclip import (
    PaperclipError, AuthError, RateLimitError, NotFoundError,
    ServerError, RequestTimeoutError, NetworkError,
)

try:
    result = client.search("query", source="pmc", limit=5)
except AuthError:
    ...            # missing or expired credentials — re-login, or check PAPERCLIP_API_KEY
except RateLimitError:
    ...            # back off and retry
except RequestTimeoutError:
    ...            # raise the timeout, especially around map_
except PaperclipError:
    ...            # anything else
```

`exit_code` is separate from exceptions: a call can return successfully with a non-zero `exit_code`
(for example a corpus `grep` that matched nothing). Check both.

## Batch pattern

```python
import json, re
from gxl_paperclip import PaperclipClient

ANSI = re.compile(r"\x1b\[[0-9;]*m")
client = PaperclipClient.from_env(timeout=300.0)

hits = client.search(
    "lipid nanoparticle mRNA delivery to hematopoietic stem cells",
    source="pmc", limit=10,
)

rows = []
for doc_id in extract_ids(ANSI.sub("", hits.output)):        # your parser
    meta = json.loads(client.papers.cat(f"/papers/{doc_id}/meta.json").output)
    ic50 = client.papers.grep("IC50", f"/papers/{doc_id}/content.lines", ignore_case=True)
    rows.append({
        "id": doc_id,
        "title": meta["title"],
        "doi": meta.get("doi"),
        "year": meta.get("pub_year"),
        "ic50_lines": ic50.output,
    })
```

Prefer `result_data` over parsing `output` where the server populates it — the rendered text is a UI
surface and its formatting is not a stable contract.
