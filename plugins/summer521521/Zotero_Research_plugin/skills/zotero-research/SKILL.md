---
name: zotero-research
description: Use when the user wants to search, browse, read, summarize, cite, annotate, or manage their Zotero library through Zotero MCP. Triggers include Zotero, 文献库, 查文献, 读论文, PDF 注释, citation key, BibTeX, 标签, 集合, and adding or updating Zotero items.
metadata:
  short-description: Search and manage Zotero via MCP
---

# Zotero Research

Use this skill when working with the user's Zotero library through the `zotero` MCP server.

## Defaults

- Use local Zotero first. If a database path is needed, read it from `ZOTERO_DB_PATH`; do not assume a hard-coded machine path.
- Semantic search uses the default local embedding model from `zotero-mcp` (`all-MiniLM-L6-v2`) unless the current MCP configuration explicitly exposes OpenAI or Gemini embeddings.
- Prefer read-only exploration unless the user explicitly asks to add, update, tag, create collections, or merge items.
- Write operations are allowed when requested clearly. For destructive or hard-to-reverse operations, especially duplicate merging, show a dry-run/preview first.

## llm-for-zotero Compatibility

- The user's Zotero desktop may have `llm-for-zotero` installed: https://github.com/yilewang/llm-for-zotero.
- Treat `llm-for-zotero` as a Zotero-side PDF reader and library assistant. It is not exposed as a Codex marketplace plugin or as the `zotero` MCP server.
- Treat this personal `zotero-research-tools` plugin as the Codex-facing layer: it exposes the `zotero` MCP server, reads Zotero metadata/full text/notes/annotations/tags/collections, and routes research tasks.
- Use `llm-for-zotero` output only after it is saved into Zotero notes/annotations, the MinerU Markdown cache, file-based notes, or pasted by the user. Do not assume Codex can operate the add-on UI directly through MCP.
- As of `llm-for-zotero` v3.8.13, the add-on advertises stronger chat-history search, source-grounded citation rendering, Codex trace display, Markdown/Mermaid/SVG rendering, and smarter MinerU cloud polling. Treat these as Zotero-side UI/output helpers; they do not make the add-on UI directly callable from the `zotero` MCP server.
- Keep data paths distinct:
  - `ZOTERO_DB_PATH` is only the optional Zotero MCP database path and should point to `zotero.sqlite`.
  - The MinerU cache belongs under Zotero's data directory as `llm-for-zotero-mineru`, not under `ZOTERO_DB_PATH` and not necessarily under the user's Obsidian folder.
- Main conflict checks:
  - If `ZOTERO_DB_PATH` points outside the resolved Zotero data directory, Codex and `llm-for-zotero` may be reading different libraries.
  - If MinerU cache files are absent, prefer Zotero MCP full text/notes first and do not report stale cache counts.
  - Do not add a separate marketplace entry for `llm-for-zotero`; this repo should expose only `zotero-research-tools` for Codex-side work.
- Quick local status entry from this repo root:

```powershell
.\plugins\zotero-research-tools\scripts\start-zotero-mcp.ps1 -Status
```

## Official Zotero Plugin Routing

- The user has installed the official Codex Zotero plugin. Treat it as a separate managed plugin, not as code to merge into this personal plugin.
- If official Zotero app tools are available in the current session, prefer them for broad paper discovery, citation lookup, citation insertion, and simple bibliography workflows.
- Prefer this personal `zotero-research-tools` plugin for local Zotero MCP operations, local library metadata, notes, annotations, tags, collections, write operations, and any workflow that depends on the user's local Zotero database.
- Prefer the MinerU `full.md` cache for deep paper reading, evidence extraction, methods/results checking, and figure/table-aware summaries.
- If both official Zotero and this personal plugin can answer a request, use official Zotero for citation-facing output and this personal plugin for local evidence reading and synthesis.
- If the user says the official Zotero plugin is installed but its tools are not exposed in the current session, say so clearly and fall back to this personal plugin.
- Do not combine the official plugin and this plugin into one local bundle. Keep this plugin as a local augmentation and routing layer around Zotero MCP, `llm-for-zotero`, and MinerU output.

## MinerU Markdown Cache

- `llm-for-zotero` can parse PDFs with MinerU and save enhanced Markdown plus extracted images in Zotero's data directory.
- Do not assume the cache is in the Obsidian notes folder. The configured Obsidian folder may be empty even when MinerU output exists.
- Resolve Zotero's actual data directory first:
  - Inspect Zotero `prefs.js` under the active profile, usually `%APPDATA%\Zotero\Zotero\Profiles\*\prefs.js`.
  - If `extensions.zotero.useDataDir` is `true`, use `extensions.zotero.dataDir`.
  - Otherwise fall back to Zotero's default data directory.
- MinerU cache layout:
  - `<Zotero data directory>\llm-for-zotero-mineru\<numeric item or attachment id>\full.md`
  - `<Zotero data directory>\llm-for-zotero-mineru\<numeric item or attachment id>\manifest.json`
  - `<Zotero data directory>\llm-for-zotero-mineru\<numeric item or attachment id>\images\`
- Prefer `full.md` for paper-content questions when it exists; it is usually richer than generic PDF text extraction and keeps figure/table references.
- Use `manifest.json`, the first Markdown heading, or Zotero MCP metadata to map numeric cache folders back to human-readable paper titles.
- Legacy cache names may exist as `_content.md` inside the numeric folder or `<id>.md` directly under the MinerU cache directory, but `full.md` is the current primary file.
- Current machine snapshot from 2026-04-23: 57 `full.md` files were found under the MinerU cache. Treat this as a stale-prone snapshot and verify live before reporting counts.

## Search Flow

1. Start broad with recent items, collections, tags, or keyword search:
   - `zotero_get_recent`
   - `zotero_get_collections`
   - `zotero_get_tags`
   - `zotero_search_items`
   - `zotero_advanced_search`
2. Use `zotero_semantic_search` for concept-level questions, literature discovery, or when the user's query is a topic rather than an exact title/author.
3. After identifying candidates, read details with:
   - `zotero_get_item_metadata`
   - `zotero_get_item_fulltext`
   - `zotero_get_item_children`
   - `zotero_get_annotations`
   - `zotero_get_notes`
4. When the user references a citation key, use `zotero_search_by_citation_key` before fuzzy search.

## Zotero MCP v0.4.1 Notes

Recent `zotero-mcp-server` releases are published on PyPI even when GitHub release pages lag. v0.4.x keeps the `zotero-mcp serve` command, adds a standalone `zotero-cli`, optional install extras (`semantic`, `pdf`, `scite`, `all`), relation tools, Scite citation/retraction tools, configurable transports, and database maintenance commands such as `zotero-mcp update-db` and `zotero-mcp db-status`.

Recent MCP tools may include collection-scoped search, item relationship lookup, note create/update/delete, PDF area annotation support, local image/PDF attachment support, PDF outline extraction, Scite enrichment, and direct relation add/remove. Use these capabilities only when the exposed MCP tool list in the current Codex session actually includes them; otherwise fall back to metadata/full-text/annotation reads and report the limitation.

Current upstream checked: `zotero-mcp-server` v0.4.1. Useful compatibility fixes include local fulltext extraction from `.zotero-ft-cache` and Zotero storage when filenames drift, UTF-8 handling for Windows PDF extraction, annotation text extraction, Better BibTeX citation-key lookup, group-library URL normalization, HTTP/1.1 local API transport for Zotero 7+, and non-PDF fulltext extraction from text-like attachments.

Be careful with write semantics in v0.4.1 and newer: `zotero_update_item.collections` replaces collection membership instead of adding to it. Preview the target collection keys before using it on existing items.

For note edits, prefer an explicit preview first and keep item keys or collection keys in the response so changes are traceable.

## Answering Style

- Answer in Chinese unless the user asks otherwise.
- Cite the Zotero item key, title, authors, and year/date when reporting findings.
- Distinguish metadata, full text, notes, and annotations when conclusions depend on them.
- If full text or annotations are unavailable, say that clearly and fall back to metadata/abstract.
- For multi-paper comparisons, keep a compact table first, then a short synthesis.

## Write Operations

Allowed when the user clearly requests them:

- Add items: `zotero_add_by_doi`, `zotero_add_by_url`, `zotero_add_from_file`
- Organize items: `zotero_create_collection`, `zotero_manage_collections`, `zotero_batch_update_tags`
- Edit metadata: `zotero_update_item`
- Related items: `zotero_add_item_relation`, `zotero_remove_item_relation`
- Duplicates: run `zotero_find_duplicates` first; only call `zotero_merge_duplicates` after the user confirms the preview.

## Maintenance

- If semantic search returns no results, check `zotero_get_search_database_status` and consider `zotero_update_search_database`.
- If shell access is more efficient than MCP schemas, use `zotero-cli` for quick search/get/tag/database checks after confirming it is installed on PATH.
- If local connection fails, ask the user to open Zotero and enable local API communication in Zotero preferences.
- If search quality is weak, rebuild the semantic database with full-text indexing (`zotero-mcp update-db --fulltext`, or `--force-rebuild` after changing embedding models) before changing embedding providers.
