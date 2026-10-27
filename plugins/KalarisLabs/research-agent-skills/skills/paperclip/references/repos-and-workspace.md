# Paper repositories, clipboard, and the personal library

Three separate stores, easy to confuse:

| Store | Holds | Command family |
|---|---|---|
| **Repo** | Paper membership + verifiable *claims* | `repo` / `git` |
| **Clipboard** (`/clipboard/`) | Uploaded PDFs, corpus links, and files you generated | `upload`, `cp`, `sync`, `mkdir`, `rm` |
| **Library** | Every paper you imported, matched or not | `library`, `import` |

A repo does **not** copy papers into the clipboard, and `repo commit` does **not** save files. To
persist an artifact you produced, use `paperclip upload`.

Examples omit the auth prefix. Every real invocation needs it:
`[ -f .env ] && { set -a; . ./.env; set +a; }; paperclip <command>`.

Commands here are transcribed from `--help` at 0.7.14–0.7.15 and were not executed while writing this
file. Verify with `--help` before a long run.

## Repositories are opt-in

**Do not create, add to, or commit a repo on your own initiative.** The default for every query —
simple lookup or full synthesis — is to read the lines and cite them directly. Repos exist for when
the user explicitly asks to track a collection, build a systematic review, or verify claims.

If a command prints a leftover `[repo: <name>]` banner from earlier work, ignore it. Appending
unrelated papers to someone's existing repo is a silent corruption of their work. If the active repo
does not match the current request, either start a new one or run `paperclip repo checkout -` to
deactivate.

For a systematic review or a quantitative meta-analysis, load
`paperclip skills show paperclip-meta-analysis` **before** creating the repo. That workflow requires
structured, line-pinned JSON claims and deterministic compile/QA steps; free-text claims are valid in
general repos but are not poolable effect estimates.

## Repo basics

`paperclip git` and `paperclip repo` are the same feature. `git` exposes the core subset
(`init`, `add`, `commit`, `status`, `log`, `branch`, `merge`, `switch`); `repo` adds `checkout`,
`remove`, `claims`, `history`, `citations`, `export`, and `info`.

```bash
paperclip repo init my-review          # create and activate
paperclip repo                         # list 10 most recent repos
paperclip repo -n 0                    # list all
paperclip repo info my-review
paperclip repo checkout other-repo     # switch branch first, else repo
paperclip repo checkout -              # deactivate
```

The active repo is sticky across commands. Two ways to scope one invocation instead:

```bash
paperclip --repo other-repo search -s pmc "query"    # use this repo, don't change sticky state
paperclip --repo-only search -s pmc "query"          # search only the repo's papers
paperclip search -s pmc "query" --corpus             # full corpus despite an active repo
```

By default `search` covers the whole corpus even with a repo active — the repo is used for tagging.

## Claims

```bash
paperclip repo add PMC10945750 "LNP delivery achieved 70% editing in hepatocytes" --lines L45-L52
paperclip repo add bio_456 "Off-target rate below 0.1%"
paperclip repo add PMC123                             # membership only, never verified
paperclip repo add PMC123 --json '{"type":"effect_size","value":0.42,"ci":[0.31,0.55]}' --lines L88
```

- `--lines` pins the claim to specific lines, which makes verification faster and more accurate.
  Supply it whenever you know where the claim came from.
- **Each `add` with a claim creates a new entry.** Call `add` repeatedly with the same paper id to
  attach several claims.
- To correct a claim: `paperclip repo remove <id>`, then re-add the corrected text.
- `--json` stores a caller-defined structured claim without making the repo domain-specific.

```bash
paperclip repo claims       # all claims as JSON, with doc ids and line pins
```

## Commit and verification

```bash
paperclip repo commit -m "Initial citations"
paperclip repo commit -m "Snapshot" --no-verify
paperclip repo status
paperclip repo log
paperclip repo history        # audit trail of searches, maps, and other commands
```

- `commit` **always succeeds** — it is a metadata snapshot that also verifies unchecked claims in
  parallel against full text.
- Each claim comes back `[OK]` (supported) or `[X]` (not supported). `[X]` is advisory and does not
  block the commit.
- Already-verified claims are not re-checked on later commits.

**Run `repo status` before writing your final response, and cite only `[OK]` claims.** For each `[X]`:
revise the claim to match what the paper actually says, find a different source, or drop it.

## Full workflow

```bash
# 1. Create
paperclip repo init my-review

# 2. Find and read
paperclip search -s pmc "topic A" -n 10
paperclip map --from s_xxx "What was the main finding and the sample size?"

# 3. Add the claims you intend to cite
paperclip repo add PMC123 "Key finding X" --lines L45-L52
paperclip repo add bio_456 "Key finding Y"

# 4. Commit — verifies every claim against full text
paperclip repo commit -m "Initial citations"

# 5. Inspect
paperclip repo status
#   [OK] PMC123   claim: Key finding X
#   [X]  bio_456  claim: Key finding Y — paper says Z instead

# 6. Repair
paperclip repo remove bio_456
paperclip repo add bio_456 "Key finding Z" --lines L80
paperclip repo commit -m "Fix bio_456 claim"

# 7. Confirm all [OK], then write
paperclip repo status
```

## Branches

Repos start on `main`. Branch to explore a side question without polluting the main line of evidence.

```bash
paperclip repo branch safety-concerns          # create and switch; forks current papers
paperclip repo add PMC789 "Drug X causes hepatotoxicity in 12%" --lines L200-L210
paperclip repo commit -m "safety claims"

paperclip repo checkout main                   # main is unaffected
paperclip repo merge safety-concerns           # union of papers
```

`repo checkout <name>` tries a branch within the current repo first, then falls back to switching
repo. Merge takes the union of papers.

## Export and citation graph

```bash
paperclip repo export bibtex   > review.bib
paperclip repo export ris      > review.ris
paperclip repo export markdown > review.md
paperclip repo export csv      > review.csv
paperclip repo citations                        # counts and graph via Semantic Scholar
```

`repos-feature` enables or disables the repositories feature entirely.

## Clipboard — `/clipboard/`

Your personal document space, searchable with the same tools as the corpus.

```bash
paperclip mkdir /clipboard/my-review
paperclip cp /papers/PMC10945750 /clipboard/my-review/   # zero-copy corpus link
paperclip cp ~/local/papers/ /clipboard/                 # upload local PDFs
paperclip ls /clipboard/
paperclip ls /clipboard/my-review
paperclip head -40 /clipboard/my-review/<id>/content.lines
paperclip search "deep learning" -s clipboard
paperclip rm /clipboard/my-review/<id>                   # remove one document
paperclip rm /clipboard/my-review -R                     # soft-delete a folder
```

Corpus links are symbolic — reading `content.lines` on a linked paper proxies to the original, so
nothing is duplicated and line numbers stay stable.

Documented limits: PDF only, 20 MB per file, 10,000 documents, 50 GB per user.

### Saving files you generated

```bash
paperclip upload analysis.json --into analyses/my-topic
paperclip upload index.html render_qa.json --into analyses/my-topic
```

This is the **only** way to persist a generated file. `repo commit` records claim metadata and stores
nothing else. JSON, HTML, CSV, MD, and PDF are all accepted.

### Syncing local folders

```bash
paperclip sync upload ~/my_papers/       # one-shot upload of a file or folder
paperclip sync add ~/my_papers/          # register a folder for ongoing sync
paperclip sync run                       # upload new/modified PDFs
paperclip sync list
paperclip sync status
paperclip sync remove ~/my_papers/       # unregister; remote documents stay
paperclip sync rm my_papers              # delete from the clipboard
paperclip sync rm --all
paperclip sync import refs.bib
```

### Sharing

```bash
paperclip share my_papers colleague@example.com
paperclip share my_papers colleague@example.com --role editor
paperclip unshare my_papers colleague@example.com
```

Sharing sends the user's documents to another person. Confirm the folder and the recipient with the
user before running it.

## Importing

`import` covers three different jobs. The third one surprises people.

```bash
# PDFs → your personal library
paperclip import paper.pdf
paperclip import ~/papers/                       # recursive
paperclip import ~/papers/ --dry-run

# Bibliographies → library, or corpus links in a clipboard folder
paperclip import refs.bib
paperclip import refs.ris --dry-run
paperclip import refs.bib --into /clipboard/thesis-refs
paperclip import refs.bib --init my-review       # create a repo from the file
paperclip import refs.bib --add-to-repo          # also add to the active repo

# A paper's REFERENCES via Semantic Scholar — not the paper itself
paperclip import PMC11282385
paperclip import PMC11282385 --min-cites 50
paperclip import PMC11282385 --dry-run
```

**`paperclip import <paper-id>` imports that paper's bibliography, not the paper.** To save a paper
you found, use `paperclip cp /papers/<id> /clipboard/<folder>/`.

Options: `--doi`, `-n/--limit`, `--min-cites`, `--dry-run`, `--init NAME`, `--add-to-repo`, `--into`.

Run `--dry-run` first on anything larger than a handful of references.

## Library

```bash
paperclip library                      # everything imported
paperclip library PMC11166971          # one paper's details
paperclip library --matched            # corpus-linked only  (✓)
paperclip library --unmatched          # bib-metadata-only    (○)
paperclip library --rematch            # retry matching unmatched entries
paperclip library -s "fine-tuning"     # keyword search over title, authors, journal
paperclip library --remove PMC123456
```

Unmatched entries keep their title, authors, year, DOI, and journal, so they remain searchable and
exportable even though there is no full text behind them. `--rematch` is worth re-running after the
corpus updates.

## Fetching a paper Paperclip does not have

```bash
paperclip fetch https://www.nature.com/articles/s41586-023-05724-2
paperclip fetch 10.1038/s41586-023-05724-2
paperclip fetch https://arxiv.org/abs/2301.00001 --into /clipboard/my-review/
```

Downloads using **your browser cookies** and adds the result to your clipboard, so it can reach
paywalled content your institution licenses. It acts with the user's credentials against a publisher's
site — only run it when the user asked for that specific paper.
