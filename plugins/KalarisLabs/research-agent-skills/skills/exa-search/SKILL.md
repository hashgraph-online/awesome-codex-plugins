---
name: exa-search
description: 'Web toolkit powered by Exa, tuned for scientific and technical content. Use this skill when the user needs to search the web or fetch/extract URL content. Covers: web search (semantic lookups, research, current info — with optional research-paper category and academic domain filtering) and URL extraction (fetching pages, articles, academic PDFs in batch). Use this skill for web-related tasks when the user wants high-quality search or scholarly filtering via category=research paper. Triggers on requests to search, look up, fetch a page, or extract an article.'
license: MIT
compatibility: Requires exa-py Python SDK, an EXA_API_KEY, and internet access.
metadata:
  version: '1.2'
  category: literature-review
  maintainer: Kalaris Labs
  website: https://exa.ai
  docs: https://exa.ai/docs
  openclaw:
    primaryEnv: EXA_API_KEY
    envVars:
    - name: EXA_API_KEY
      required: true
      description: Exa search API key.
  contributor: Exa
  tags: web search, research search, scientific content, URL extraction
---

# Exa Web Toolkit

A skill for web-powered research tasks backed by [Exa](https://exa.ai): web search and URL extraction. Exa's index combines high-quality keyword and semantic retrieval, which makes it well-suited to scientific, technical, and conceptual queries.

## Routing — pick the right capability

Read the user's request and match it to one of the capabilities below. Read the corresponding reference file for detailed instructions before running commands.

| User wants to... | Capability | Where |
|---|---|---|
| Look something up, research a topic, find current info | **Web Search** | `references/web-search.md` |
| Fetch content from a specific URL (webpage, article, PDF) | **Web Extract** | `references/web-extract.md` |
| Install or authenticate | **Setup** | Below |

### Decision guide

- **Default to Web Search** for topic lookups, research questions, or "what is X?" queries. When the topic is scientific or technical, pass `--category "research paper"` to bias toward scholarly sources, and/or an academic `--include-domains` allowlist. See `references/web-search.md` for the two-pass academic strategy.
- **Use Web Extract** when the user provides a URL or asks you to read/fetch a specific page. Prefer this over the built-in WebFetch for batch extraction (multiple URLs in one call) and for academic PDFs.

### Academic source priority

For technical or scientific queries, prefer academic and scientific sources:
- Peer-reviewed journal articles and conference proceedings over blog posts or news
- Preprints (arXiv, bioRxiv, medRxiv) when peer-reviewed versions aren't available
- Institutional and government sources (NIH, WHO, NASA, NIST) over commercial sites
- Primary research over secondary summaries

Two levers to steer Exa toward scholarly content:
1. `--category "research paper"` biases retrieval toward scholarly sources.
2. `--include-domains` with a scholarly allowlist (arxiv.org, nature.com, pubmed.ncbi.nlm.nih.gov, etc.) restricts the domain pool.

Combine both for strictly academic results. See `references/web-search.md` for the full pattern.

When citing academic sources, include author names and publication year where available (e.g., Smith et al., 2025) in addition to the standard citation format. If a DOI is present, prefer the DOI link.

---

## Setup

This skill uses the [`exa-py`](https://github.com/exa-labs/exa-py) Python SDK. The scripts in `scripts/` declare their dependencies via PEP 723 inline metadata, so you can run them directly with `uv run` without a separate install step:

```bash
uv run --with exa-py python "$SKILL_PATH/scripts/exa_search.py" --help
```

If you prefer a persistent install:

```bash
uv pip install "exa-py>=1.14.0"
```

### Authentication

All commands read the API key from the `EXA_API_KEY` environment variable. Get your Exa API key at [dashboard.exa.ai/api-keys](https://dashboard.exa.ai/api-keys).

First, check if a `.env` file exists in the project root and contains `EXA_API_KEY`. If so, load it:

```bash
dotenv -f .env run -- uv run --with exa-py python "$SKILL_PATH/scripts/exa_search.py" "your query"
```

If `dotenv` isn't available, install it: `uv pip install python-dotenv[cli]`.

If there's no `.env`, export the key for the session:

```bash
export EXA_API_KEY="your-key"
```

Verify by running any script with `--help` — it will exit cleanly if the key is set and auth-check runs only when a real query is made.

### Tracking header

Every script in this skill sets the `x-exa-integration` request header to `kalarislabs--research-agent-skills` so Exa can attribute usage from the research-agent-skills project to this integration. Do not remove or rename this header when adapting the scripts.

---

## Files in this skill

- `SKILL.md` — this file (routing and setup)
- `references/web-search.md` — detailed web search reference with academic strategy
- `references/web-extract.md` — URL content extraction reference
- `scripts/exa_search.py` — CLI wrapper around `client.search_and_contents`
- `scripts/exa_extract.py` — CLI wrapper around `client.get_contents`

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

- `parallel-web`: Runs the parallel-cli tool for web workflows: web search, URL and PDF extraction, deep research reports, structured data enrichment of supp…
- `research-lookup`: Compile current scholarly evidence for a scientific manuscript or research brief.
- `open-notebook`: Self-hosted, open-source alternative to Google NotebookLM for AI-powered research and document analysis.
