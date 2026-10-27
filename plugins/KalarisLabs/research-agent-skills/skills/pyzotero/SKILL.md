---
name: pyzotero
description: 'Reads and writes Zotero libraries from Python with pyzotero 1.13.0 and the Zotero Web API v3: items, collections, tags, attachments, saved searches, full-text content, and BibTeX, CSL-JSON, and bibliography export. Also covers the pyzotero CLI and MCP server for a local Zotero 7. Use when fetching or searching library items programmatically; when creating, updating, or deleting references, collections, or tags; when uploading PDF attachments or downloading files; when exporting citations as BibTeX or CSL-JSON; when building research automation around a Zotero user or group library. Not for formatting citations in a manuscript or verifying references against external databases.'
license: MIT
compatibility: Requires Python 3.10+ and pyzotero 1.13+. Web API access needs a Zotero API key. Optional CLI and MCP extras require Zotero 7 with local API access enabled.
allowed-tools: Read Write Edit Bash
metadata:
  version: '1.2'
  category: literature-review
  maintainer: Kalaris Labs
  openclaw:
    primaryEnv: ZOTERO_API_KEY
    envVars:
    - name: ZOTERO_API_KEY
      required: true
      description: Zotero API key.
    - name: ZOTERO_LIBRARY_ID
      required: true
      description: Zotero library id.
    - name: ZOTERO_LIBRARY_TYPE
      required: false
      description: 'Zotero library type: ''user'' or ''group'' (default ''user'').'
  tags: Zotero, reference management, citations, BibTeX, literature
---

# Pyzotero

Pyzotero is a Python wrapper for the [Zotero API v3](https://www.zotero.org/support/dev/web_api/v3/start). Use it to programmatically manage Zotero libraries: read items and collections, create and update references, upload attachments, manage tags, and export citations.

**Current upstream:** pyzotero 1.13.0 (PyPI, May 2026). Docs: [pyzotero.readthedocs.io](https://pyzotero.readthedocs.io/en/latest/).

## Authentication Setup

**Required credentials** — get from https://www.zotero.org/settings/keys:
- **User ID**: shown as "Your userID for use in API calls"
- **API Key**: create at https://www.zotero.org/settings/keys/new
- **Library ID**: for group libraries, the integer after `/groups/` in the group URL

Store credentials in environment variables or a `.env` file:
```
ZOTERO_LIBRARY_ID=your_user_id
ZOTERO_API_KEY=your_api_key
ZOTERO_LIBRARY_TYPE=user  # or "group"
```

See [references/authentication.md](references/authentication.md) for full setup details.

## Installation

```bash
uv add pyzotero              # Web API client
uv add "pyzotero[cli]"       # + local CLI (Zotero 7)
uv add "pyzotero[mcp]"       # + MCP server for LLM clients (Zotero 7)
```

## Quick Start

```python
import os
from pyzotero import Zotero

zot = Zotero(
    library_id=os.environ['ZOTERO_LIBRARY_ID'],
    library_type=os.environ.get('ZOTERO_LIBRARY_TYPE', 'user'),
    api_key=os.environ['ZOTERO_API_KEY'],
)

# Retrieve top-level items (returns 100 by default)
items = zot.top(limit=10)
for item in items:
    print(item['data']['title'], item['data']['itemType'])

# Search by keyword
results = zot.items(q='machine learning', limit=20)

# Retrieve all items (use everything() for complete results)
all_items = zot.everything(zot.items())
```

## Core Concepts

- A `Zotero` instance is bound to a single library (user or group). All methods operate on that library.
- Item data lives in `item['data']`. Access fields like `item['data']['title']`, `item['data']['creators']`.
- Pyzotero returns 100 items by default (API default is 25). Use `zot.everything(zot.items())` to get all items.
- Write methods return `True` on success or raise a `ZoteroError`.

## Reference Files

| File | Contents |
|------|----------|
| [references/authentication.md](references/authentication.md) | Credentials, library types, local mode |
| [references/read-api.md](references/read-api.md) | Retrieving items, collections, tags, groups |
| [references/search-params.md](references/search-params.md) | Filtering, sorting, search parameters |
| [references/write-api.md](references/write-api.md) | Creating, updating, deleting items |
| [references/collections.md](references/collections.md) | Collection CRUD operations |
| [references/tags.md](references/tags.md) | Tag access and management |
| [references/files-attachments.md](references/files-attachments.md) | File download and attachment uploads |
| [references/exports.md](references/exports.md) | BibTeX, CSL-JSON, bibliography export |
| [references/pagination.md](references/pagination.md) | follow(), everything(), generators |
| [references/full-text.md](references/full-text.md) | Full-text content indexing and access |
| [references/saved-searches.md](references/saved-searches.md) | Saved search management |
| [references/cli.md](references/cli.md) | Command-line interface (local Zotero 7) |
| [references/mcp.md](references/mcp.md) | MCP server for LLM clients (local Zotero 7) |
| [references/error-handling.md](references/error-handling.md) | Errors and exception handling |

## Common Patterns

### Fetch and modify an item
```python
item = zot.item('ITEMKEY')
item['data']['title'] = 'New Title'
zot.update_item(item)
```

### Create an item from a template
```python
template = zot.item_template('journalArticle')
template['title'] = 'My Paper'
template['creators'][0] = {'creatorType': 'author', 'firstName': 'Jane', 'lastName': 'Doe'}
zot.create_items([template])
```

### Export as BibTeX
```python
zot.add_parameters(format='bibtex')
bibtex = zot.top(limit=50)
# bibtex is a bibtexparser BibDatabase object
print(bibtex.entries)
```

### Local mode (read-only, no API key needed)
```python
zot = Zotero(library_id='123456', library_type='user', local=True)
items = zot.items()
```

### Local Zotero 7 (CLI or MCP, no API key)

For searching a locally running Zotero desktop app (including full-text PDF search), use the CLI or MCP server instead of the Web API. Both require Zotero 7 with local API access enabled. See [references/cli.md](references/cli.md) and [references/mcp.md](references/mcp.md).

## Agent operating procedure

1. **Check the environment.** Confirm the research question, databases, date range and inclusion criteria.
2. **Pin down the inputs.** Confirm formats, identifiers and parameters from the data or the user. Ask rather than guess any value that changes the result.
3. **Run a small version first.** Run the search on one database with a narrow query and check that the results are relevant.
4. **Execute the full task** using the instructions and references above.
5. **Validate the result.** Every reference is retrieved from a real record with a resolvable identifier; counts and search strings are recorded.
6. **Report.** State what was run (versions, commands, parameters), what was checked, and what is still uncertain.

| If this happens | Do this |
|---|---|
| An API rate-limits or returns errors | Back off and retry, reduce the batch size, or switch database, and report the gap. |
| A function, flag or endpoint in these instructions is missing in the installed version | Check the installed version's own documentation (`help()`, `--help`, official docs), adapt, and tell the user. Never invent an API. |
| A required input, identifier or parameter is ambiguous | Ask the user, or state the assumption explicitly before running. |

**Integrity rules**

- Never fabricate results, parameters, identifiers, citations or statistics. If something cannot be run or verified, say so plainly.
- Never summarize a paper you have not retrieved; never cite from memory.
- Treat version-specific details here as possibly outdated: confirm them against the official documentation for the installed version.
- Ask before actions that cost money, consume shared GPUs or cloud quota, touch personal or patient data, or cannot be undone.

## Related skills

- `reference-manager-interop`: Move and sync reference libraries between Zotero, Mendeley, EndNote, JabRef, Paperpile and writing tools (LaTeX/BibTeX, Word, Google Docs,…
- `citation-management`: Searches OpenAlex, PubMed, and Google Scholar, extracts metadata from DOIs, PMIDs, PMCIDs, arXiv IDs, and URLs via CrossRef, PubMed, and ar…
- `literature-review`: Runs systematic literature reviews by searching PubMed, arXiv, bioRxiv, and Semantic Scholar (plus web search via parallel-cli), screening…
