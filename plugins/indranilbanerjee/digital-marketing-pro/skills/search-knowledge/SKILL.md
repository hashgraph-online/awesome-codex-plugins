---
name: search-knowledge
description: "Search stored brand knowledge. Use when: recalling past learnings, voice guidelines, or competitor insights via semantic search."
---

# /digital-marketing-pro:search-knowledge

## Purpose

Semantic search across all stored brand knowledge in the vector database and knowledge graph. Answers questions like "What worked for email in Q4?", "What are our brand voice guidelines?", "Show me learnings about audience X", or "What did we learn about competitor Y's pricing?" Returns relevant entries ranked by similarity with full provenance context, so agents and users can make decisions informed by everything the brand has ever learned — not just what they remember from the current session. Searches all connected memory layers simultaneously: vector DB for semantic similarity, knowledge graph for entity relationships, and local index for un-synced recent entries.

## Input Required

The user must provide (or will be prompted for):

- **Search query**: Natural language question or topic — e.g., "What email subject line patterns drove the highest open rates?", "What are our compliance restrictions for the EU market?", "Show me everything we know about competitor X", or "What campaign strategies worked for audience millennials in Q4?" The query is embedded and matched semantically, so exact wording does not need to match stored content
- **Content type filter (optional)**: Narrow results to a specific type — `guideline`, `campaign-learning`, `competitive-intel`, `performance-insight`, or `brand-asset`. Omit to search all types. Multiple types can be specified as a comma-separated list
- **Date range filter (optional)**: Restrict results to a time window — e.g., "last 90 days", "Q4 2025", "2025-01-01 to 2025-06-30", or "this year". Useful for recency-sensitive queries where older knowledge may be stale or superseded
- **Max results (optional)**: Number of results to return — default 10, maximum 50. Use higher limits for comprehensive research queries and knowledge audits, lower limits for quick factual lookups
- **Tags filter (optional)**: Further narrow by specific tags — e.g., "email", "paid-social", "audience-millennials", "black-friday". Combines with content type and date range as AND filters for precise retrieval
- **Priority filter (optional)**: Filter by knowledge priority — `high` for proactively surfaced insights, `normal` for standard entries, or `all` (default). Use `high` when you need only the most impactful learnings
- **Include expired (optional)**: Whether to include knowledge entries past their expiration date — default `false`. Set to `true` for historical research where stale knowledge still has archival value
- **Search mode (optional)**: `semantic` (default — natural language similarity), `exact` (keyword match for precise terms like campaign names or metric values), or `hybrid` (combines both with weighted scoring)

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. Also check for guidelines at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Check connected memory services**: Run `memory-manager.py --action get-memory-status` to determine which storage layers are available — Pinecone, Qdrant, Graphiti knowledge graph, Supermemory cross-session store, and local index. Build a search plan that queries all connected layers in parallel for fastest results.
3. **Execute vector search**: If Pinecone or Qdrant is connected, query the vector database MCP with the user's search query, applying content type, date range, tag, and priority filters as metadata constraints. Request top-N results ranked by cosine similarity with full metadata payloads returned.
4. **Execute graph search**: If Graphiti is connected, also query the temporal knowledge graph for entity relationships and causal chains relevant to the query — e.g., "which campaigns influenced audience growth", "what strategy replaced our old approach", or "how has competitor X's positioning evolved". Graph results provide relationship and temporal context that vector search alone cannot capture.
5. **Search local index**: Run `memory-manager.py --action search-local` to check the local memory index for any entries not yet synced to the vector database. This catches recent session knowledge that was stored locally via `/digital-marketing-pro:save-knowledge` but not yet pushed to persistent storage via `/digital-marketing-pro:sync-memory`.
6. **Merge and rank results**: Combine results from all queried layers (vector DB, knowledge graph, local index), deduplicate by content hash, and rank by composite relevance. Weight vector similarity scores, graph relationship strength, recency, and priority level. Translate raw similarity scores into human-readable relevance categories (highly relevant, related, tangentially related).
7. **Present results with context**: Display ranked results with full provenance — content summary, content type, tags, source, date stored, relevance category, priority, and related entries. For graph results, include entity relationships and temporal context. Suggest follow-up queries based on patterns in the results.

## Output

A structured search response containing:

- **Query interpretation**: How the natural language query was parsed — key concepts extracted, filters applied (content type, date range, tags, priority), search mode used, and which memory layers were queried
- **Results list**: Ranked entries with: relevance category (highly relevant, related, tangentially related), content summary, content type, tags, source attribution, date stored, priority level, storage layer (vector DB, graph, local), and expiration status if applicable
- **Graph relationships (if applicable)**: Entity relationships discovered — campaign connections, causal chains, temporal sequences, strategy evolution paths, and competitor relationship maps that add structural context beyond keyword matching
- **Cross-references**: Links between results — e.g., a campaign learning that connects to a performance insight and a competitive intel entry, showing the full picture across knowledge types
- **Knowledge gaps**: Areas where the query suggests knowledge should exist but no entries were found — with specific recommendations to fill those gaps via `/digital-marketing-pro:save-knowledge` or data collection
- **Follow-up suggestions**: Refined or expanded queries the user could run to explore related knowledge — based on tags, entities, and content types found in the current results
- **Result count by layer**: Breakdown of how many results came from each memory layer (vector DB, knowledge graph, local index) for transparency on search coverage and sync status
- **Search performance**: Query execution time per layer and total, to help diagnose slow searches or connectivity issues with external memory services

## Agents Used

- **memory-manager** — Query parsing with concept extraction and filter construction, multi-layer parallel search execution (vector DB via MCP, knowledge graph via Graphiti, local index via file system), result deduplication by content hash, cross-layer result merging with composite relevance ranking, similarity score translation to human-readable categories, relationship context extraction from graph results, knowledge gap detection based on query coverage analysis, and follow-up query generation from result pattern analysis
