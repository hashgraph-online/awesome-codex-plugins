# Paperclip CLI reference

Every command and flag below is transcribed from `paperclip --help` and `paperclip <cmd> --help`, and
checked against **0.7.14 and 0.7.15**. Commands marked *(not exercised here)* are documented by the
CLI but were not run while writing this file — verify with `--help` before relying on exact behavior.

`paperclip <command> --help` is authoritative and cheap. Use it.

## Before anything: auth and interactivity

Prefix every invocation, since shell state does not survive between tool calls:

```bash
[ -f .env ] && { set -a; . ./.env; set +a; }; paperclip <command>
```

Without it Paperclip silently falls back to stored OAuth instead of erroring. See
[installation.md](installation.md) for why the guard is mandatory.

**Commands that block on a prompt or a browser** — never run these bare from a tool call:

| Command | Non-interactive form |
|---|---|
| `login`, `setup` | None. Ask the user to run it |
| `uninstall` | None. Ask the user |
| `install` | `printf '1\n\n' \| paperclip install --dir <path>` |
| `fetch` | Works unattended, but acts with the user's browser cookies — explicit request only |

`results` with no arguments is safe: it prints the list rather than prompting.

## Global options

```text
paperclip [OPTIONS] COMMAND [ARGS]...

  --version       Show the version and exit
  --debug         Enable debug logging
  --repo-only     Restrict search/map to the active repo's papers (default: full corpus)
  --repo TEXT     Use this repo for one invocation, without changing sticky state
  --api-key TEXT  API key (alternative to OAuth); also read from PAPERCLIP_API_KEY
  --help
```

Note that `--repo-only` and `--repo` go **before** the subcommand:
`paperclip --repo-only search -s pmc "query"`.

## Two families of commands

`paperclip --help` lists only the account and workspace commands (`login`, `config`, `repo`, `sync`,
`upload`, …). The data commands — `search`, `grep`, `cat`, `map`, `sql` and friends — are dispatched
to the sandboxed virtual shell and do not appear in that listing. They still take `--help`:

```bash
paperclip grep --help
paperclip map --help
```

## Search and discovery

### `search`

```bash
paperclip search -s SOURCE [OPTIONS] "QUERY"
paperclip search "QUERY" /fda/us          # a virtual directory works in place of -s
```

`-s` is required; omitting it prints the source list and exits non-zero.

| Option | Meaning |
|---|---|
| `-n, --limit N` | Number of results |
| `-s, --source S` | Source or comma-separated sources (see search-and-retrieval.md) |
| `-e, --exact` | Exact-phrase matching |
| `--since DATE` | Restrict to documents after a date |
| `--sort relevance\|date` | Result ordering |
| `--author`, `--journal`, `--year` | Metadata filters |
| `--ranking hybrid\|bm25\|vector\|analogical` | Retrieval strategy |
| `--corpus` | Search the whole corpus even with a repo active |

Every search prints a result id (`s_5bcc8044`) that `filter`, `map`, and `results` consume.

### `grep`

```text
grep [OPTIONS] PATTERN [FILE...]

  -i          Ignore case
  -n          Show line numbers
  -c          Count matches only
  -v          Invert match
  -o          Print only the matching part
  -w          Whole words only
  -l          List only filenames with matches
  -h          Suppress filename prefix
  -m NUM      Stop after NUM matches
  -e PATTERN  Explicit pattern; repeat for multi-pattern OR
  -F          Fixed strings (literal, no regex)
  -A NUM      NUM lines after each match
  -B NUM      NUM lines before each match
  -C NUM      NUM lines of context either side
```

Two distinct modes:

```bash
paperclip grep -n "off-target" /papers/PMC12345/content.lines   # within one document
paperclip grep -l "SLC30A8" /papers/                            # across the whole corpus
```

The corpus mode returns matched paragraphs grouped by paper plus a result id, and is **time-bounded**.
On an empty result for a genuinely rare term, retry with `--exhaustive`.

### `scan`

```text
scan [OPTIONS] FILE "pattern1" "pattern2" ...

  -i      Case insensitive
  -C N    Context lines per match (default 5)
```

One request instead of several sequential greps; output is grouped by pattern.

### `lookup`

```text
lookup [OPTIONS] FIELD VALUE

Fields: doi, author, title, abstract, source, date, pmc, pmid, arxiv,
        journal, publisher, type, keywords, category, license, year,
        volume, issue, issn

  -n N      Limit results (default 25)
  --json    Output as JSON  — documented, but observed to return rendered text anyway
```

```bash
paperclip lookup doi 10.1073/pnas.2307796121
paperclip lookup pmc PMC7194329
paperclip lookup author "James Zou" -n 10
```

### `sql`

```bash
paperclip sql "SELECT source, COUNT(*) FROM documents GROUP BY source"
paperclip sql -s proteins "SELECT COUNT(*) FROM uniprot_v.proteins"
```

`SELECT` only. 15 s timeout, 200-row cap. Schemas are in search-and-retrieval.md.

### `filter`

```bash
paperclip filter --from s_abc123 "cardiovascular outcomes"
```

LLM relevance pass over a result set, **overwriting it in place**. If `--require N` cannot be met,
re-run `search` with broader terms for a fresh id rather than filtering again.

## Reading

| Command | Notes |
|---|---|
| `cat [-n] FILE...` | Whole file. `-n` numbers output. The only way to read `meta.json` |
| `head [-n N \| -N] FILE` | First N lines (default 10). `.lines` files only |
| `tail [-n N \| -N] FILE` | Last N lines. `.lines` files only |
| `ls PATH` | Directory listing; on a paper root it also reports the line count |
| `tree PATH` | Recursive listing |
| `wc FILE` | Line/word/character counts |
| `cd PATH` / `pwd` | Exist, but **cwd does not persist between invocations** — use absolute paths |

`head -40 file.lines` and `head -n 40 file.lines` are equivalent.

### `ask-image`

```text
ask-image PATH "question"
ask-image --list

  --fn describe       Describe the figure
  --fn extract-data   Extract data from the figure
```

Figure filenames are publisher-specific, so `ls` the directory before calling this — `--list` needs a
persistent `cd`, which the CLI does not have.

```bash
paperclip ls /papers/PMC10945750/figures/
paperclip ask-image /papers/PMC10945750/figures/pnas.2307796121fig01.jpg "What are the axes and the effect size?"
```

## Analysis

### `map` — LLM reader over a result set

```text
map --from RESULTS_ID [OPTIONS] "query"

  --from ID              Result id from a previous search (required)
  --worker NAME          quick-reader (default) | eligibility-screen | exhaustive-extraction
  --output_schema JSON   Structured output schema
  --claim-schema JSON    JSON Schema for each exhaustive claim
  --repo NAME            Shared repo receiving validated exhaustive claims
  --resume MAP_ID        Continue pending work; never reruns successful papers
  --retry-failed         With --resume, also retry failures
  --cancel MAP_ID        Durably request cancellation
  -n, --limit N          Limit papers processed
  --offset N             Skip the first N papers
  -j, --max-concurrent N Concurrent extraction subagents (default 100, server cap 256)
```

### `reduce` — synthesize map output

```text
reduce --from MAP_ID [OPTIONS] "question"

  --from ID           Map result id (m_* prefix); defaults to the most recent map
  --strategy STR      summarize (default) | table | themes | consensus | bullet_points | extract
  --columns COL,...   Columns for the table strategy
```

### `results`

```bash
paperclip results --list                        # recent result ids with the command that made them
paperclip results s_4a2b61f6                    # view one
paperclip results s_4a2b61f6 --save out.csv     # export to CSV or TXT
```

## Repos — `paperclip repo`, alias `paperclip git`

*(not exercised here)*

| Command | Purpose |
|---|---|
| `repo init <name>` | Create a repo |
| `repo checkout <name>` | Switch branch, else repo; `-` deactivates |
| `repo add <id> ["claim"] [--lines L45-L52] [--json '{...}']` | Add paper, optionally with a claim |
| `repo remove <id>` | Remove a paper |
| `repo commit -m "msg" [--no-verify]` | Snapshot and verify unchecked claims |
| `repo status` | Papers, claims, `[OK]`/`[X]` marks |
| `repo claims` | Claims as JSON, with doc ids and line pins |
| `repo log` | Commit history |
| `repo history` | Command audit trail (searches, maps) |
| `repo branch <name>` | Create and switch to a branch |
| `repo merge <branch>` | Union of papers into the current branch |
| `repo info <name>` | Details for one repo |
| `repo citations` | Citation counts and graph via Semantic Scholar |
| `repo export bibtex\|ris\|csv\|markdown` | Export the active repo |
| `repo` / `repo -n 0` | List 10 most recent repos / all |
| `repos-feature` | Enable or disable the repositories feature |

`paperclip git` mirrors the core subset: `init`, `add`, `commit`, `status`, `log`, `branch`, `merge`,
`switch`.

## Clipboard and workspace

*(not exercised here)*

| Command | Purpose |
|---|---|
| `upload FILES... --into FOLDER` | Persist a generated file into `/clipboard/<folder>/` |
| `cp /papers/<id> /clipboard/<folder>/` | Zero-copy corpus link to a paper |
| `cp ~/local/path /clipboard/` | Copy local PDFs up |
| `mkdir /clipboard/<folder>` | Create a folder |
| `rm /clipboard/<folder> -R` | Soft-delete a folder |
| `sync upload PATH` | Upload a PDF or folder of PDFs |
| `sync add\|run\|list\|remove\|status\|rm\|import` | Registered-folder sync |
| `import SOURCE` | Import PDFs, `.bib`/`.ris`, or a paper's references |
| `library [PAPER_ID]` | Personal library; `--matched`, `--unmatched`, `--rematch`, `--remove`, `-s` |
| `fetch URL_OR_DOI [--into FOLDER]` | Download a paper using your browser cookies |
| `share FOLDER EMAIL [--role viewer\|editor]` | Share a clipboard folder |
| `unshare` | Revoke access |

`import` options: `--doi`, `-n/--limit`, `--min-cites`, `--dry-run`, `--init NAME`, `--add-to-repo`,
`--into /clipboard/<folder>`.

## Account and meta

| Command | Purpose |
|---|---|
| `login` / `logout` | Browser OAuth |
| `setup` | `login` + `install`, for uv installs |
| `install [--dir]` | Write Paperclip skill files into a project |
| `config` | Diagnostics and settings |
| `update` | Upgrade CLI and refresh agent skills |
| `uninstall` | Remove Paperclip from the machine |
| `skill` | Print the full vendor documentation |
| `skills [list\|search\|show\|system]` | Browse bundled domain workflows |

## The sandboxed shell

Data commands execute in a server-side virtual shell (`vsh`), not your local one. An unknown command
returns `vsh: <name>: command not found. Available: ask_image, awk, cat, cd, curl, cut, echo, egrep,
env, export...` — the list is truncated server-side, so that error is the only enumeration available.
Note `curl` appears in it, contradicting the upstream claim that it is blocked; treat the vendor's
allowed/blocked lists as approximate.

`for`/`while` loops and `xargs` are unsupported. Issue several calls instead.

### Pipes and redirection do not work — verified on 0.7.14 and 0.7.15

Upstream documentation says to use `paperclip bash '...'` for pipes and redirection. Neither works in
this version:

```bash
paperclip bash 'grep IC50 /papers/PMC12345/content.lines'
# ERR: vsh: grep IC50 /papers/PMC12345/content.lines: command not found. [exit 126]

paperclip "grep IC50 /papers/PMC12345/content.lines | head -2"
# ERR: vsh: grep: |: Cannot read path: /papers/|   [exit 2]

paperclip "grep nanoparticle /papers/PMC12345/content.lines > /.gxl/hits.txt"
# ERR: vsh: grep: >: Cannot read path: /papers/>   [exit 2]
```

`bash` passes its whole argument as a single command name, and `|` / `>` reach `grep` as literal file
arguments. The SDK's `client.bash()` fails identically — this is server-side, not a CLI quirk.

What does work: quoting an entire command as one argument is equivalent to passing it as separate
arguments, and **your own shell** handles pipes and redirection fine, because the CLI writes to
stdout.

```bash
paperclip "grep -c CRISPR /papers/PMC10945750/content.lines"           # → 62
paperclip grep IC50 /papers/PMC12345/content.lines | head -20          # local pipe
paperclip cat /papers/PMC12345/sections/Abstract.lines > abstract.txt  # local redirect, text
```

### Binary files cannot be retrieved

Text redirects fine. Images do not — every byte that is not valid UTF-8 comes back as `U+FFFD`:

```bash
paperclip cat /papers/PMC10945750/figures/pnas.2307796121fig01.jpg > fig01.jpg
file fig01.jpg          # → data   (not "JPEG image data")
xxd fig01.jpg | head -1 # → efbf bdef bfbd efbf bdef bfbd 0010 4a46  ("....JF")
```

The JPEG SOI/APP0 marker `FF D8 FF E0` arrived as four replacement characters. The file is the right
order of magnitude in size and completely unusable.

No alternative works on 0.7.14 or 0.7.15:

| Attempt | Result |
|---|---|
| `paperclip pull <path>` | `vsh: pull: command not found` — no CLI `pull` |
| `client.pull(path, dest)` (SDK) | Returns `exit_code 0`, `download_url` `None`, writes no file |
| `paperclip cp <figure> <local path>` | `vsh: cp: permission denied` |

Analyze figures in place with `ask-image`, which runs server-side and is unaffected. When the user
genuinely needs the image file, give them the publisher URL from `meta.json`.

### `/.gxl/` is effectively unreadable

`/.gxl/` is described in-band as "Session files (E2B sandbox). Files here persist to GCS." Every
`search`, `grep`, `map`, and `reduce` writes a transcript there, and `ls /.gxl/` lists them:

```text
-rw-r--r--  2349  Jul 28 01:32  reduce_r_36626b45.txt
-rw-r--r--   904  Jul 28 01:32  map_m_4b4632df.txt
-rw-r--r--  1939  Jul 28 01:31  search_s_aaadaa84.txt
```

But reading one fails, so the `Full results: /.gxl/map_<id>.txt` pointer that `map` prints cannot be
followed:

```bash
paperclip cat /.gxl/map_m_4b4632df.txt
# ERR: vsh: cat: /.gxl/map_m_4b4632df.txt: No such file  [exit 1]
```

Each invocation is a new session, and writing there is impossible anyway without redirection. **Use
`paperclip results <id>` or `paperclip results <id> --save out.csv`** to retrieve full output.

### `cd` does not persist

Every invocation resolves relative paths from `/papers/`, whatever a previous `cd` did:

```bash
paperclip cd /.gxl
paperclip pwd                       # → /papers/
paperclip cat map_m_4b4632df.txt    # → Cannot read path: /papers/map_m_4b4632df.txt
paperclip cd /                      # → vsh: cd: /: Permission denied
```

Always pass absolute paths. This also makes `ask-image --list`, which upstream documents as requiring
a `cd` into a paper directory, unusable — list figures with `ls /papers/<id>/figures/` instead.
