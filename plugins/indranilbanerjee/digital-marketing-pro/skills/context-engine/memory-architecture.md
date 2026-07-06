# Memory Architecture — Persistent Brand Knowledge System

How the Digital Marketing Pro plugin stores, retrieves, and learns from marketing knowledge across sessions.

---

## Overview

The plugin uses a **5-layer memory architecture**. Each layer serves a different purpose, persistence level, and query pattern. Layers are additive — the plugin works with just Layer 1, and each additional layer adds capabilities.

| Layer | Name | Persistence | Setup | Best For |
|---|---|---|---|---|
| 1 | Session Context | Permanent (insights.json) + per-session (auto-memory) | Zero config | Brand profile, campaign tracker, session continuity |
| 2 | Brand RAG | Permanent, cloud-hosted | Pinecone or Qdrant API key | Historical campaign learnings, semantic search |
| 3 | Temporal Knowledge Graph | Permanent, cloud-hosted | Graphiti API key | Understanding how audiences, campaigns, and markets evolve over time |
| 4 | Universal Agent Memory | Permanent, cloud-hosted | Supermemory API key | Cross-agent knowledge sharing, institutional learning |
| 5 | Knowledge Base | Permanent, human-editable | Notion or Google Drive credentials | Team documentation, style guides, SOPs |

---

## Layer 1: Session Context (Always Available)

**Source:** Claude Code auto-memory at `~/.claude/projects/` + `insights.json` at `~/.claude-marketing/brands/{slug}/insights.json`

**Persistence:** Per-session (auto-memory survives across sessions, insights.json is permanent)

**What's stored:**
- Session summaries and conversation context
- Campaign tracker data (campaigns, performance snapshots, insights, violations)
- Brand profile (identity, voice, audiences, competitors, goals)
- Active brand state (`_active-brand.json`)

**Query pattern:** Automatic — loaded at session start via the `SessionStart` hook. No manual retrieval needed.

**Setup:** Zero config. Works out of the box with `setup.py` and `campaign-tracker.py`.

**Limitations:**
- No semantic search — linear scan only
- Limited to approximately 200 insights per brand (older entries are pruned)
- No cross-brand querying (each brand's data is isolated)
- No relationship or temporal awareness between data points

---

## Layer 2: Brand RAG (Vector Database)

**Services:** Pinecone (`@pinecone-database/mcp`) or Qdrant (`mcp-server-qdrant`)

**Persistence:** Permanent, cloud-hosted (Pinecone) or self-hosted (Qdrant)

**What's stored:**
- Brand guidelines and voice documentation
- Campaign archives (plans, results, post-mortems)
- Performance history and trend data
- Competitive intelligence reports
- Content templates and high-performing examples
- Audience research and persona documents

**Metadata per entry:**

| Field | Type | Example |
|---|---|---|
| `brand_slug` | string | `"acme-corp"` |
| `content_type` | enum | `guideline`, `campaign-learning`, `competitive-intel`, `performance-insight`, `brand-asset` |
| `tags` | string[] | `["email", "developer-audience", "q3-2026"]` |
| `source` | string | `"campaign-tracker"`, `"manual-upload"`, `"performance-report"` |
| `created_at` | ISO 8601 | `"2026-01-15T14:30:00Z"` |
| `content_hash` | SHA-256 | Used for deduplication — skip store if hash matches existing entry |

**Query pattern:** Semantic similarity search — natural language queries retrieve the most relevant stored knowledge.

Examples:
- "What email strategies worked for developer audiences?"
- "Show me competitive intelligence about Acme's pricing"
- "What blog formats drove the most organic traffic last quarter?"

**Setup:** Set `PINECONE_API_KEY` in `.env` (Pinecone free tier: 1 index, 100K vectors) or `QDRANT_URL` + `QDRANT_API_KEY` for self-hosted.

**Storage via:**
```bash
python memory-manager.py --brand {slug} --action prepare-store --type campaign-learning --data '{"content": "...", "tags": [...]}'
```
The script prepares the payload, then the MCP store call writes it to the vector database.

---

## Layer 3: Temporal Knowledge Graph (Graphiti/Zep)

**Service:** Zep Graphiti (`graphiti-mcp`)

**Persistence:** Permanent, cloud-hosted

**What's stored:** Entity-relationship-temporal data — facts about marketing entities and how they relate to each other over time.

**Entity types:**

| Entity | Examples |
|---|---|
| Brand | Acme Corp, BetaWidget |
| Campaign | Q3 Email Blast, Black Friday 2026 |
| Audience | Developer Persona, Enterprise Buyer |
| Competitor | RivalCo, AlternateTech |
| Channel | Email, LinkedIn, Google Ads |
| Message | Value Prop A, Discount Offer |
| Product | Pro Plan, Starter Kit |
| Market | North America SaaS, APAC Enterprise |

**Relationship types:**

| Relationship | Pattern | Example |
|---|---|---|
| `targeted` | Campaign → Audience | "Q3 Email Blast targeted Developer Persona from Jan–Mar 2026" |
| `outperformed` | Campaign → Campaign | "Black Friday 2026 outperformed Black Friday 2025 by 35% ROAS" |
| `shifted` | Audience property change | "Developer Persona shifted from email-preferred to Slack-preferred in Q2 2026" |
| `correlated` | Channel → Channel | "LinkedIn engagement correlated with Google Ads conversion lift (r=0.72)" |
| `influenced` | Message → Conversion | "Value Prop A influenced 45% of Q3 enterprise conversions" |

**Temporal dimension:** Every relationship has a time range. This enables queries like "What was true in Q1 vs. Q3?" and tracking how strategies, audiences, and markets evolve.

**Query pattern:** Graph traversal with time filters.

Examples:
- "What campaigns targeted developers in Q3 and what were the results?"
- "How has our enterprise audience's channel preference changed over the last 12 months?"
- "Which messages correlated with the highest conversion rates in APAC?"

**Setup:** Set `GRAPHITI_API_KEY` in `.env`.

**Storage via:**
```bash
python memory-manager.py --brand {slug} --action prepare-graph --entity-type campaign --data '{"name": "...", "relationships": [...]}'
```

---

## Layer 4: Universal Agent Memory (Supermemory)

**Service:** Supermemory (`@supermemoryai/supermemory-mcp`)

**Persistence:** Permanent, cloud-hosted

**What's stored:** Cross-session agent learnings — every agent's discoveries, preferences, and patterns. This is the institutional knowledge layer.

**Examples of stored memories:**
- "The email-specialist learned that Acme's audience prefers Tuesday 10 AM sends over Thursday sends (23% higher open rate)"
- "The media-buyer found that video ads outperform image ads 2:1 for this brand on Meta"
- "The seo-specialist discovered that long-form guides (2,500+ words) rank 3x better than short posts for Acme's keywords"
- "The content-creator learned to avoid passive voice — brand manager flagged it twice in review"

**Auto-deduplication:** Supermemory automatically merges similar memories, preventing redundant entries from accumulating.

**Query pattern:** Natural language — any agent can query what other agents have learned.

Examples:
- "What has any agent learned about email for this brand?"
- "What patterns has the media-buyer observed about video ad performance?"
- "Are there any known issues with this brand's LinkedIn content?"

**Setup:** Set `SUPERMEMORY_API_KEY` in `.env`.

**Shared across:** All 25 agents. When one agent learns something, every other agent can retrieve it.

---

## Layer 5: Knowledge Base (Notion/Google Drive)

**Services:** Notion (`@notionhq/mcp-server`) or Google Drive (`mcp-google-drive`)

**Persistence:** Permanent, human-editable

**What's stored:**
- Team documentation and onboarding materials
- Brand style guides (the original source documents)
- Campaign briefs and creative briefs
- Standard operating procedures
- Creative assets and design references
- Meeting notes and decision logs

**Query pattern:** Structured search by page/folder + text search within documents.

Examples:
- "Find the brand style guide in the Acme workspace"
- "What does the Q3 campaign brief say about target audience?"
- "Pull the latest meeting notes on budget allocation"

**Setup:** Set `NOTION_API_KEY` in `.env` or `GOOGLE_APPLICATION_CREDENTIALS` for Google Drive.

**Best for:** Human-maintained knowledge that changes infrequently. This layer is the source of truth for documents that teams collaboratively edit — the plugin reads from it but does not write to it without explicit instruction.

---

## Decision Tree: Which Layer to Use

| Need | Layer | Reasoning |
|---|---|---|
| "What's our brand voice?" | Layer 1 (profile.json) or Layer 5 (Notion) | Always check the profile first; Notion for the full style guide |
| "What worked for email last quarter?" | Layer 2 (Vector DB) | Semantic search over campaign learnings and performance data |
| "How has our audience changed over time?" | Layer 3 (Knowledge Graph) | Temporal graph query across entity relationships |
| "What did the media-buyer learn about video ads?" | Layer 4 (Supermemory) | Cross-agent memory query |
| "Where's the brand style guide PDF?" | Layer 5 (Notion/Drive) | Document retrieval from human-maintained knowledge base |
| "Quick session context — what are we working on?" | Layer 1 (auto-memory) | Loaded automatically at session start |
| "What competitors have shifted strategy recently?" | Layer 3 (Knowledge Graph) | Temporal queries on competitor entities |
| "Has anyone on the team documented this workflow?" | Layer 5 (Notion/Drive) | SOP and documentation search |

---

## Minimum Viable Setup

Start simple and add layers as needs grow:

| Stage | Layers | Cost | Capabilities |
|---|---|---|---|
| **Getting Started** | Layer 1 only | Free | Brand profile, campaign tracking, session memory |
| **Adding RAG** | Layer 1 + Layer 2 | Free (Pinecone free tier: 1 index, 100K vectors) | + Semantic search over campaign history |
| **Cross-Session Learning** | Layer 1 + Layer 2 + Layer 4 | Supermemory plan | + Persistent agent learnings across sessions |
| **Full Intelligence** | All 5 layers | Multiple subscriptions | + Temporal analysis, team docs, complete memory system |

**Recommendation:** Most users should start with Layers 1 + 2. Add Layer 4 when you want agents to remember lessons across sessions. Layers 3 and 5 are for advanced users managing complex multi-brand portfolios or large teams.

---

## Sync Operations

The `/digital-marketing-pro:sync-memory` command synchronizes local data with remote memory layers.

**How it works:**
1. Reads `insights.json` for the active brand
2. Diffs against `_last_sync.json` to identify new or updated entries since the last sync
3. Prepares new items with metadata (content_type, tags, content_hash)
4. Stores via MCP calls to the configured memory layers (Layer 2, 3, and/or 4)
5. Updates `_last_sync.json` with the current sync timestamp and entry hashes

**Sync state file:** `~/.claude-marketing/brands/{slug}/_last_sync.json`

```json
{
  "last_sync_at": "2026-02-10T09:00:00Z",
  "synced_layers": [2, 4],
  "entries_synced": 47,
  "entry_hashes": ["a1b2c3...", "d4e5f6..."]
}
```

**Recommended cadence:** Run `/digital-marketing-pro:sync-memory` after every major campaign review, quarterly business review, or when switching between brands after significant work. Minimum recommended frequency: weekly for active brands.

**Conflict resolution:** Remote memory is append-only. The `content_hash` field prevents duplicate entries. If local data is updated (e.g., an insight is revised), the sync creates a new entry with an `updated_from` reference to the original hash.
