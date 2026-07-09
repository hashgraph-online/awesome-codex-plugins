---
name: save-knowledge
description: "Save brand knowledge to memory. Use when: persisting campaign learnings, guidelines, or competitive intel for retrieval."
---

# /digital-marketing-pro:save-knowledge

## Purpose

Save brand knowledge to the persistent memory layer (Pinecone or Qdrant vector database) for semantic retrieval in future sessions. Stores campaign learnings, competitive intelligence, brand guidelines, and performance insights with proper metadata tagging so that valuable knowledge is never lost between sessions. Every stored item is content-hashed for deduplication, tagged with brand context, and indexed for natural language search — turning ad-hoc learnings into durable institutional memory that every agent can draw from. Designed for targeted, intentional knowledge capture — for bulk session syncing, use `/digital-marketing-pro:sync-memory` instead.

## Input Required

The user must provide (or will be prompted for):

- **Content to store**: The knowledge to save — can be plain text typed directly, a reference to content in the current conversation (e.g., "save that email analysis we just did"), structured data from a campaign report or audit, or a URL to external research. Content is stored as-is with optional summarization for the index entry
- **Content type**: One of: `guideline` (brand rules, voice standards, style restrictions), `campaign-learning` (what worked or failed in a campaign with supporting evidence), `competitive-intel` (competitor findings, positioning, pricing, strategy moves), `performance-insight` (metrics, benchmarks, trends, statistical patterns), or `brand-asset` (approved copy, templates, creative references, messaging frameworks)
- **Tags**: Descriptive tags for filtered retrieval — e.g., "email", "q4-2025", "subject-lines", "audience-millennials", "paid-social", "black-friday". If not provided, auto-suggested based on content analysis using brand context, industry taxonomy, and channel detection. Multiple tags encouraged for richer retrieval
- **Source context**: Where this knowledge originated — current session analysis, imported report, campaign retrospective, external research, competitor monitoring, or team input. Used for provenance tracking, credibility weighting during retrieval, and audit trail compliance
- **Priority (optional)**: `high` (surface this knowledge proactively in relevant contexts), `normal` (standard retrieval weight), or `low` (archive-grade, retrieve only on direct queries). Default is `normal`
- **Expiration (optional)**: Date after which this knowledge should be flagged as potentially stale — useful for time-sensitive competitive intel, seasonal campaign data, or pricing information that changes quarterly. No default (knowledge persists indefinitely unless expired)
- **Related entries (optional)**: References to existing stored knowledge this entry connects to — enables knowledge graph linking and richer cross-reference retrieval

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. Also check for guidelines at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Prepare content for storage**: Run `memory-manager.py --action prepare-store` with `content_type`, `tags`, and source context. The script normalizes the content, generates a SHA-256 content hash, structures the metadata payload (brand_slug, content_type, tags, source, timestamp, priority, expiration), and validates that all required fields are present. If tags were not provided, auto-generate them from content analysis.
3. **Check for duplicates**: Compare the content hash against the local index at `~/.claude-marketing/brands/{slug}/memory/`. If a match exists, report the duplicate — show the existing entry's tags, date, and summary — and offer to update its metadata (add new tags, refresh timestamp, change priority) rather than creating a duplicate. If no match, proceed to storage.
4. **Check connected memory services**: Run `memory-manager.py --action get-memory-status` to determine which vector database is connected — Pinecone, Qdrant, or local-only fallback. Verify API connectivity, available storage capacity, and index health. If no vector DB is connected, store locally and recommend persistent storage setup for cross-session access.
5. **Store via vector database MCP**: Send the prepared payload to the connected Pinecone or Qdrant MCP server for embedding and storage. Include all metadata for filtered retrieval. If Supermemory is also connected, sync the entry for cross-session agent access. If Graphiti is connected and related entries were specified, create relationship edges in the knowledge graph.
6. **Update local index**: Run `memory-manager.py --action log-stored` to register the new entry in the local content hash registry with storage ID, vector DB reference, timestamp, and priority. Update sync state so future `/digital-marketing-pro:sync-memory` runs skip this item as already persisted.
7. **Confirm storage**: Present the storage confirmation with all details — what was stored, where it was stored, metadata applied, and example queries that would retrieve this entry.

## Output

A structured storage confirmation containing:

- **Content summary**: Brief description of what was stored, word count, content hash for deduplication reference, and a one-line summary generated from the content for index display
- **Content type**: The classification applied — guideline, campaign-learning, competitive-intel, performance-insight, or brand-asset — with explanation of why this type was selected if auto-detected
- **Tags applied**: All tags attached to the entry — user-provided tags, auto-suggested tags with rationale, and brand-context tags (industry, market, brand slug) added automatically for namespace isolation
- **Storage location**: Which vector database was used (Pinecone, Qdrant, or local-only), namespace or collection name, storage ID, and embedding model used for vectorization
- **Deduplication status**: Whether this was a new entry or an update to an existing entry — with details on what metadata was merged and the original entry's storage date
- **Priority and expiration**: The priority level set (high, normal, low) and expiration date if specified, with a note on how these affect future retrieval ranking
- **Related entries linked**: Any knowledge graph relationships created to existing entries, with bidirectional link confirmation
- **Total stored items**: Running count of total knowledge items stored for this brand, broken down by content type, for memory utilization awareness
- **Retrieval hint**: Two to three example search queries that would surface this entry — so the user knows exactly how to find it later via `/digital-marketing-pro:search-knowledge`

## Agents Used

- **memory-manager** — Content normalization and summarization, SHA-256 hashing for deduplication, duplicate detection against local index with metadata merge option, auto-tag generation from content analysis, metadata structuring with required field validation, vector database payload preparation and embedding, storage execution via Pinecone or Qdrant MCP, knowledge graph relationship creation via Graphiti, local index and sync state update, and retrieval hint generation based on stored content semantics
