---
name: exa-web-search
description: Use the Exa MCP server for internet search and full-page retrieval. Use whenever the user asks to search, browse, look up, verify, research, find sources, find current or latest online information, discover papers or repositories, compare web sources, or read and summarize a URL whose content was not provided. Prefer Exa by default for general web research. Do not use it for local filesystem or codebase search, or when the user explicitly requests a different tool or a specialized connected source is the direct system of record.
---

# Exa Web Search

Use Exa as the first web-search tool for matching requests.

## Workflow

1. Call `mcp__exa__web_search_exa` before drafting an answer that depends on online information.
2. Write a natural-language query describing the ideal source. Include dates, domains, or source types when they materially narrow the task.
3. Request enough results to compare sources; use 5-10 for broad research and fewer for a targeted lookup.
4. Call `mcp__exa__web_fetch_exa` on the best URLs when search excerpts do not contain enough context, when exact attribution matters, or when the user asks to read a specific page.
5. For time-sensitive or consequential claims, compare multiple independent or primary sources. Prefer official documentation, original papers, first-party announcements, and source repositories.
6. Cite the final source URLs close to the claims they support. Distinguish source statements from inference.

## Boundaries

- Honor explicit user constraints about tools, domains, dates, languages, and source types.
- Use `rg` or repository tools for local files instead of Exa.
- Prefer a dedicated connected system when it is the authoritative source, such as Zotero for the user's library, Figma for a design file, or OpenAI Developer Docs for OpenAI product documentation.
- If Exa is unavailable or returns inadequate results, state that briefly and use another available web-search tool so the task still completes.
